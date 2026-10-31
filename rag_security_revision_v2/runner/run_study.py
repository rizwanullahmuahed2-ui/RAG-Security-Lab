"""Versioned, fail-closed RAG experiment runner. No network without --execute-api.

Design inputs are frozen before embedding calls; vectors, contexts and exact
completion payloads are frozen before any completion call. A provider invocation
is keyed by (round_id, payload_sha256), never by condition or by payload alone.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import threading
import time
import urllib.error
import urllib.request

import numpy as np
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer


def now():
    return datetime.now(timezone.utc).isoformat()


def encode(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def read_jsonl(path):
    path = Path(path)
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


class ExperimentError(RuntimeError):
    pass


class PermanentAPIError(ExperimentError):
    pass


class LiveTransport:
    """Lazy credential loading; bodies and authorization headers are never logged."""
    def __init__(self, env_path=Path('/workspace/.env')):
        self.env_path = Path(env_path)
        self._key = None

    def _load_key(self):
        if self._key is None:
            # The explicitly configured file takes precedence over a stale
            # inherited environment variable after a user updates the file.
            key = ''
            if self.env_path.is_file():
                for line in self.env_path.read_text().splitlines():
                    if line.strip().startswith('OPENAI_API_KEY='):
                        key = line.split('=', 1)[1].strip().strip("\"'")
                        break
            else:
                key = os.environ.get('OPENAI_API_KEY', '').strip()
            if not key:
                raise PermanentAPIError('OPENAI_API_KEY is unavailable; no request sent')
            self._key = key
        return self._key

    def __call__(self, endpoint, payload):
        request = urllib.request.Request(
            'https://api.openai.com/v1/' + endpoint, data=encode(payload),
            headers={'Authorization': 'Bearer ' + self._load_key(), 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.load(response), response.headers.get('x-request-id')
        except urllib.error.HTTPError as error:
            try:
                code = json.loads(error.read()).get('error', {}).get('code')
            except Exception:
                code = None
            # Only predefined status/code information escapes the transport.
            if error.code in {408, 429, 500, 502, 503, 504} and code != 'insufficient_quota':
                raise ConnectionError('Transient HTTP ' + str(error.code)) from None
            raise PermanentAPIError('Permanent API HTTP ' + str(error.code)) from None
        except (urllib.error.URLError, TimeoutError):
            raise ConnectionError('Provider network/timeout error') from None


class StudyRunner:
    DATA_NAMES = ('config.json', 'test_questions.json', 'clean_documents.json', 'insertions.json')

    def __init__(self, data_root, run_root, *, transport=None, execute_api=False):
        self.data_root = Path(data_root).resolve()
        self.run_root = Path(run_root).resolve()
        self.run_root.mkdir(parents=True, exist_ok=True)
        self.source_root = Path(__file__).resolve().parent
        self.transport = transport
        self.execute_api = execute_api
        self.lock = threading.RLock()
        self.stop = threading.Event()

    def data(self, name):
        return read_json(self.data_root / name)

    def run(self, name):
        return read_json(self.run_root / name)

    def append(self, name, value):
        with self.lock:
            with (self.run_root / name).open('a') as handle:
                handle.write(json.dumps(value, ensure_ascii=False) + '\n')

    def _seal(self, name, manifest):
        path = self.run_root / name
        if path.exists():
            raise ExperimentError('Refusing to replace an existing freeze: ' + name)
        write_json(path, manifest)
        (self.run_root / (name + '.sha256')).write_text(digest(path.read_bytes()) + '\n')

    def _manifest(self, name):
        path = self.run_root / name
        seal = self.run_root / (name + '.sha256')
        if not path.is_file() or not seal.is_file() or digest(path.read_bytes()) != seal.read_text().strip():
            raise ExperimentError('Freeze manifest missing or changed: ' + name)
        return read_json(path)

    def _hash_paths(self, paths, root):
        return {str(path.relative_to(root)): digest(path.read_bytes()) for path in paths}

    def verify_design(self):
        manifest = self._manifest('design_freeze.json')
        for group, root in [('data_hashes', self.data_root), ('source_hashes', self.source_root),
                            ('run_hashes', self.run_root)]:
            for name, expected in manifest[group].items():
                path = root / name
                if not path.is_file() or digest(path.read_bytes()) != expected:
                    raise ExperimentError('Frozen ' + group + ' input changed: ' + name)
        for name, expected in manifest.get('external_hashes', {}).items():
            path = Path(name) if Path(name).is_absolute() else (self.data_root / name).resolve()
            if not path.is_file() or digest(path.read_bytes()) != expected:
                raise ExperimentError('Frozen supporting input changed: ' + name)
        if (manifest['python'] != platform.python_version() or manifest['numpy'] != np.__version__
                or manifest['scikit_learn'] != sklearn.__version__):
            raise ExperimentError('Runtime dependency versions differ from the frozen design')
        return manifest

    def verify_generation(self):
        self.verify_design()
        manifest = self._manifest('generation_freeze.json')
        for name, expected in manifest['run_hashes'].items():
            path = self.run_root / name
            if not path.is_file() or digest(path.read_bytes()) != expected:
                raise ExperimentError('Frozen generation input changed: ' + name)
        requests = self.run('requests.json')
        if any(digest(encode(payload)) != key for key, payload in requests.items()):
            raise ExperimentError('Payload key does not match its exact request')
        return requests

    def _validate_inputs(self, config, tests, docs, inserts):
        if int(config.get('rounds', 3)) < 1:
            raise ExperimentError('rounds must be positive')
        qids = [q['id'] for q in tests]
        doc_ids = [d['id'] for d in docs]
        if len(set(qids)) != len(qids) or len(set(doc_ids)) != len(doc_ids):
            raise ExperimentError('Duplicate question or clean-document IDs')
        if not tests or not docs or not all(q['support_ids'] and set(q['support_ids']) <= set(doc_ids) for q in tests):
            raise ExperimentError('Missing question support')
        if any(not d['verified'] or d['trust'] not in {'high', 'medium'} or d['kind'] != 'clean' for d in docs):
            raise ExperimentError('Core clean collection must be accepted by the fixed gate')
        for condition in ['targeted', 'unrelated', 'benign']:
            rows = inserts[condition]
            if len(rows) != len(tests) or {d['target_qid'] for d in rows} != set(qids):
                raise ExperimentError('Need one insertion per target in ' + condition)
            if any(d['verified'] or d['trust'] in {'high', 'medium'} for d in rows):
                raise ExperimentError('Base insertions must have rejected labels')
            insertion_ids = [d['id'] for d in rows]
            if len(insertion_ids) != len(set(insertion_ids)) or set(insertion_ids) & set(doc_ids):
                raise ExperimentError('Insertion IDs collide with clean IDs or duplicate within a condition')
            if any(d.get('kind') != condition for d in rows):
                raise ExperimentError('Insertion kind does not match its corpus condition')
        required = ['max_usd', 'input_per_million', 'output_per_million', 'embedding_per_million']
        if any(not math.isfinite(float(config.get('budget', {}).get(key, -1)))
               or float(config.get('budget', {}).get(key, -1)) < 0 for key in required):
            raise ExperimentError('Explicit nonnegative money ceiling and unit rates are required')
        if int(config.get('max_attempts', 3)) not in {1, 2, 3}:
            raise ExperimentError('max_attempts must be 1, 2 or 3')

    def design(self):
        if (self.run_root / 'design_freeze.json').exists():
            self.verify_design()
            return self.run('design_freeze.json')
        config, tests, docs, inserts = [self.data(name) for name in self.DATA_NAMES]
        self._validate_inputs(config, tests, docs, inserts)
        optional = self.data_root / 'controlled_contexts.json'
        if config.get('modules', {}).get('controlled', optional.exists()) and not optional.exists():
            raise ExperimentError('Controlled module enabled but controlled_contexts.json is absent')
        if config.get('modules', {}).get('controlled', False):
            self._validate_controlled(self.data('controlled_contexts.json'), tests)
        texts = list(dict.fromkeys([d['text'] for d in docs]
                    + [d['text'] for c in ['targeted', 'unrelated', 'benign'] for d in inserts[c]]
                    + [q['question'] for q in tests]))
        batch_size = int(config.get('embedding_batch_size', 128))
        if not 1 <= batch_size <= 2048:
            raise ExperimentError('Invalid embedding batch size')
        batches = []
        for offset in range(0, len(texts), batch_size):
            payload = {'model': config['embedding_model'], 'input': texts[offset:offset+batch_size],
                       'dimensions': int(config['embedding_dimensions']), 'encoding_format': 'float'}
            batches.append({'offset': offset, 'payload': payload, 'request_sha256': digest(encode(payload))})
        write_json(self.run_root / 'embedding_texts.json', texts)
        write_json(self.run_root / 'embedding_requests.json', batches)
        paths = [self.data_root / name for name in self.DATA_NAMES]
        if optional.exists():
            paths.append(optional)
        external = {}
        for name in config.get('freeze_extra_files', config.get('additional_frozen_files', [])):
            path = (self.data_root / name).resolve()
            if not path.is_file() or path.name.startswith('.env'):
                raise ExperimentError('Invalid additional frozen path')
            if not path.is_relative_to(self.data_root.parent) and not path.is_relative_to(Path('/workspace')):
                raise ExperimentError('Additional frozen file must be within the data root or workspace')
            if path.is_relative_to(self.data_root):
                paths.append(path)
            else:
                external[os.path.relpath(path, self.data_root)] = digest(path.read_bytes())
        manifest = {'phase': 'design_before_embeddings', 'frozen_at_utc': now(),
                    'data_hashes': self._hash_paths(paths, self.data_root),
                    'source_hashes': self._hash_paths(sorted(self.source_root.glob('*.py')), self.source_root),
                    'run_hashes': self._hash_paths([self.run_root / 'embedding_texts.json',
                                                  self.run_root / 'embedding_requests.json'], self.run_root),
                    'external_hashes': external,
                    'python': platform.python_version(), 'numpy': np.__version__,
                    'scikit_learn': sklearn.__version__, 'embedding_texts': len(texts),
                    'embedding_batches': len(batches),
                    'trust_boundary': 'Local file integrity checks; no hostile-owner authenticity guarantee'}
        self._seal('design_freeze.json', manifest)
        return manifest

    def _estimate(self, endpoint, payload, config):
        # Byte fallback is intentionally conservative for byte-level tokenizers;
        # the JSON bytes include a generous allowance for chat framing.
        input_upper = len(encode(payload)) + 512
        rates = config['budget']
        if endpoint == 'embeddings':
            output_upper = 0
            reserve = input_upper * float(rates['embedding_per_million']) / 1e6
        else:
            output_upper = int(payload['max_tokens'])
            reserve = (input_upper * float(rates['input_per_million'])
                       + output_upper * float(rates['output_per_million'])) / 1e6
        return reserve, input_upper, output_upper

    def _committed_cost(self):
        reservations, settled = {}, {}
        for entry in read_jsonl(self.run_root / 'cost_ledger.jsonl'):
            if entry['event'] == 'reserve':
                reservations[entry['attempt_id']] = float(entry['reserved_usd'])
            elif entry['event'] == 'settle':
                settled[entry['attempt_id']] = float(entry['actual_usd'])
        return sum(settled.get(key, value) for key, value in reservations.items())

    def _actual_cost(self, endpoint, response, config):
        usage, rates = response.get('usage', {}), config['budget']
        if endpoint == 'embeddings':
            return int(usage.get('total_tokens', usage.get('prompt_tokens', 0))) * float(rates['embedding_per_million']) / 1e6
        return (int(usage.get('prompt_tokens', 0)) * float(rates['input_per_million'])
                + int(usage.get('completion_tokens', 0)) * float(rates['output_per_million'])) / 1e6

    def _call(self, endpoint, payload, *, expected_hash, round_id=None):
        config = self.data('config.json')
        if self.transport is None:
            if not self.execute_api:
                raise ExperimentError('API execution disabled; pass --execute-api to perform live requests')
            self.transport = LiveTransport()
        max_attempts = int(config.get('max_attempts', 3))
        previous_attempts = sum(entry['event'] == 'reserve' and entry.get('endpoint') == endpoint
                                and entry.get('request_sha256') == expected_hash and entry.get('round_id') == round_id
                                for entry in read_jsonl(self.run_root / 'cost_ledger.jsonl'))
        if previous_attempts >= max_attempts:
            raise ExperimentError('Attempt allowance exhausted across resumes; no request sent')
        for attempt in range(previous_attempts + 1, max_attempts + 1):
            with self.lock:
                if self.stop.is_set():
                    raise ExperimentError('Run stopped after a fatal request error')
                if endpoint == 'embeddings':
                    self.verify_design()
                    frozen = {r['request_sha256']: r['payload'] for r in self.run('embedding_requests.json')}
                else:
                    frozen = self.verify_generation()
                if expected_hash not in frozen or digest(encode(payload)) != expected_hash or frozen[expected_hash] != payload:
                    raise ExperimentError('Pending request does not match frozen request')
                reserve, input_upper, output_upper = self._estimate(endpoint, payload, config)
                if self._committed_cost() + reserve > float(config['budget']['max_usd']) + 1e-12:
                    self.stop.set()
                    raise ExperimentError('Recorded money ceiling would be exceeded; no request sent')
                attempt_id = f'{endpoint}:{round_id}:{expected_hash}:{time.time_ns()}'
                self.append('cost_ledger.jsonl', {'event': 'reserve', 'attempt_id': attempt_id,
                            'at_utc': now(), 'endpoint': endpoint, 'round_id': round_id,
                            'request_sha256': expected_hash, 'attempt': attempt,
                            'input_token_upper': input_upper, 'output_token_upper': output_upper,
                            'reserved_usd': reserve})
            started = time.monotonic()
            response, request_id = None, None
            try:
                response, request_id = self.transport(endpoint, payload)
                if not isinstance(response, dict):
                    raise PermanentAPIError('Provider response is not a JSON object')
                expected_model = config['embedding_model'] if endpoint == 'embeddings' else config['generator']
                if response.get('model') != expected_model:
                    raise PermanentAPIError('Returned model does not match frozen model')
                usage = response.get('usage')
                if not isinstance(usage, dict) or ('total_tokens' not in usage and 'prompt_tokens' not in usage):
                    raise PermanentAPIError('Token usage absent; unable to account for response')
                required_usage = ['total_tokens'] if endpoint == 'embeddings' else ['prompt_tokens', 'completion_tokens']
                if any(not isinstance(usage.get(name), int) or usage[name] < 0 for name in required_usage):
                    raise PermanentAPIError('Required nonnegative token usage fields are absent')
                if endpoint == 'chat/completions':
                    choices = response.get('choices')
                    if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
                        raise PermanentAPIError('Expected one well-formed completion choice')
                    message = choices[0].get('message')
                    if not isinstance(message, dict) or not isinstance(message.get('content'), (str, type(None))):
                        raise PermanentAPIError('Malformed completion message')
                    if not isinstance(choices[0].get('finish_reason'), str):
                        raise PermanentAPIError('Completion finish reason is absent')
                actual = self._actual_cost(endpoint, response, config)
                self.append('cost_ledger.jsonl', {'event': 'settle', 'attempt_id': attempt_id,
                            'at_utc': now(), 'endpoint': endpoint, 'actual_usd': actual, 'usage': usage})
                if actual > reserve + 1e-12:
                    raise PermanentAPIError('Actual charge exceeded conservative reservation; halt for review')
                return response, request_id, attempt, time.monotonic() - started
            except PermanentAPIError:
                self.stop.set()
                if response is not None:
                    self.append('rejected_provider_responses.jsonl', {'at_utc': now(), 'endpoint': endpoint,
                                'request_sha256': expected_hash, 'round_id': round_id, 'attempt': attempt,
                                'request_id': request_id, 'response': response, 'response_sha256': digest(encode(response))})
                self.append('api_errors.jsonl', {'at_utc': now(), 'endpoint': endpoint,
                            'request_sha256': expected_hash, 'round_id': round_id,
                            'attempt': attempt, 'error_class': 'PermanentAPIError'})
                raise
            except (ConnectionError, TimeoutError, json.JSONDecodeError):
                self.append('api_errors.jsonl', {'at_utc': now(), 'endpoint': endpoint,
                            'request_sha256': expected_hash, 'round_id': round_id,
                            'attempt': attempt, 'error_class': 'TransientNetworkError',
                            'reservation_retained_for_unknown_charge': True})
                if attempt == max_attempts:
                    self.stop.set()
                    raise ExperimentError('Request failed after bounded transient retries') from None
                time.sleep(min(2 * attempt, 10))
            except Exception as error:
                self.stop.set()
                self.append('api_errors.jsonl', {'at_utc': now(), 'endpoint': endpoint,
                            'request_sha256': expected_hash, 'round_id': round_id,
                            'attempt': attempt, 'error_class': type(error).__name__,
                            'reservation_retained_for_unknown_charge': True})
                raise ExperimentError('Unexpected transport/response failure; stopped for review') from None

    def embeddings(self):
        self.verify_design()
        config = self.data('config.json')
        requests = self.run('embedding_requests.json')
        cache = {}
        for row in read_jsonl(self.run_root / 'embedding_responses.jsonl'):
            key = row['request_sha256']
            if key in cache or digest(encode(row['response'])) != row['response_sha256']:
                raise ExperimentError('Embedding response cache changed or duplicated')
            cache[key] = row
        expected = {r['request_sha256']: r for r in requests}
        if not set(cache) <= set(expected):
            raise ExperimentError('Unexpected embedding response in cache')
        chunks = []
        for item in requests:
            key = item['request_sha256']
            if key not in cache:
                response, request_id, attempts, latency = self._call('embeddings', item['payload'], expected_hash=key)
                row = {'request_sha256': key, 'response_sha256': digest(encode(response)), 'response': response,
                       'request_id': request_id, 'attempts': attempts, 'latency_seconds': latency, 'received_at_utc': now()}
                self.append('embedding_responses.jsonl', row)
                cache[key] = row
            response = cache[key]['response']
            if response['model'] != config['embedding_model']:
                raise ExperimentError('Cached embedding model mismatch')
            values = sorted(response['data'], key=lambda value: value['index'])
            if [row['index'] for row in values] != list(range(len(item['payload']['input']))):
                raise ExperimentError('Embedding batch indices do not match request')
            chunks.extend(row['embedding'] for row in values)
        matrix = np.asarray(chunks, dtype=np.float32)
        texts = self.run('embedding_texts.json')
        if matrix.shape != (len(texts), int(config['embedding_dimensions'])) or not np.isfinite(matrix).all():
            raise ExperimentError('Invalid embedding matrix dimensions or values')
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        if not np.all(norms > 0):
            raise ExperimentError('Zero-length embedding')
        normalized = matrix / norms
        path = self.run_root / 'embeddings.npz'
        if path.exists():
            old = np.load(path)['matrix']
            if old.shape != normalized.shape or not np.array_equal(old, normalized):
                raise ExperimentError('Existing normalized embedding artifact differs from response reconstruction')
        else:
            np.savez_compressed(path, matrix=normalized)
        manifest = {'model': config['embedding_model'], 'dimensions': int(config['embedding_dimensions']),
                    'normalization': 'float32 L2', 'texts_sha256': digest(encode(texts)),
                    'matrix_sha256': digest(path.read_bytes()),
                    'raw_responses_sha256': digest((self.run_root / 'embedding_responses.jsonl').read_bytes()),
                    'unique_texts': len(texts), 'batches': len(requests)}
        destination = self.run_root / 'embeddings_manifest.json'
        if destination.exists() and read_json(destination) != manifest:
            raise ExperimentError('Embedding manifest changed')
        if not destination.exists():
            write_json(destination, manifest)
        return normalized, {text: i for i, text in enumerate(texts)}

    def _payload(self, config, question, documents):
        passages = '\n\n'.join(config['passage_template'].format(rank=i+1, text=doc['text']) for i, doc in enumerate(documents))
        return {'model': config['generator'], 'temperature': config['temperature'], 'max_tokens': config['max_tokens'],
                'store': config['store'], 'messages': [
                    {'role': 'system', 'content': config['system_prompt']},
                    {'role': 'user', 'content': config['user_template'].format(question=question['question'], passages=passages)}]}

    def _record(self, config, question, condition, defense, candidates, final, *, module='core', copies=1):
        payload = self._payload(config, question, final)
        supports, ids = set(question['support_ids']), [d['id'] for d in final]
        own = [d for d in final if d.get('target_qid') == question['id']]
        ranks = [i+1 for i, doc in enumerate(final) if doc['id'] in supports]
        row = {'qid': question['id'], 'module': module, 'copies_per_target': 0 if condition == 'clean' else copies, 'condition': condition,
               'defense': defense, 'request_sha256': digest(encode(payload)),
               'candidate_ids': [d['id'] for d in candidates], 'final_ids': ids,
               'gold_support_ids': question['support_ids'], 'support_fraction': len(supports & set(ids))/len(supports),
               'all_support': supports <= set(ids), 'any_support': bool(ranks),
               'first_support_reciprocal_rank': 1/min(ranks) if ranks else 0,
               'assigned_insert_exposed': bool(own),
               'any_insert_exposed': any(d['kind'] != 'clean' for d in final),
               'insert_occupancy': sum(d['kind'] != 'clean' for d in final)/len(final),
               'own_false_claim_exposed': condition in ['targeted', 'accepted_label'] and bool(own),
               'final_documents': final}
        return row, payload

    def contexts(self):
        self.verify_design()
        if (self.run_root / 'generation_freeze.json').exists():
            self.verify_generation()
            return self.run('generation_freeze.json')
        config, tests, docs, inserts = [self.data(name) for name in self.DATA_NAMES]
        matrix = np.load(self.run_root / 'embeddings.npz')['matrix']
        texts = self.run('embedding_texts.json')
        embedding_manifest = self.run('embeddings_manifest.json')
        if digest((self.run_root / 'embeddings.npz').read_bytes()) != embedding_manifest['matrix_sha256']:
            raise ExperimentError('Normalized vectors changed before context construction')
        if digest((self.run_root / 'embedding_responses.jsonl').read_bytes()) != embedding_manifest['raw_responses_sha256']:
            raise ExperimentError('Raw embedding response archive changed')
        mapping = {text: index for index, text in enumerate(texts)}
        request_map, records = {}, []
        modules = config.get('modules', {'core': True, 'controlled': False, 'doses': []})
        scenarios = []
        if modules.get('core', True):
            scenarios += [(condition, defense, 1, 'core') for condition in config['conditions'] for defense in config['defenses']]
        scenarios += [('targeted', defense, int(copies), 'dose') for copies in modules.get('doses', [])
                      for defense in ['none', 'rerank']]
        if any(copies < 2 for _, _, copies, module in scenarios if module == 'dose'):
            raise ExperimentError('Additional dose values must be greater than one')
        for condition, defense, copies, module in scenarios:
            added = [] if condition == 'clean' else inserts['targeted' if condition == 'accepted_label' else condition]
            if condition == 'accepted_label':
                added = [dict(doc, verified=True, trust='high') for doc in added]
            if copies > 1:
                added = [dict(doc, id=doc['id'] + f'__copy{copy+1}') for doc in added for copy in range(copies)]
            collection = docs + added
            if len({doc['id'] for doc in collection}) != len(collection):
                raise ExperimentError('Corpus IDs collide after constructing a dose condition')
            if defense in ['filter', 'filter_rerank']:
                collection = [d for d in collection if d['verified'] and d['trust'] in {'high', 'medium'}]
            vectors = matrix[[mapping[d['text']] for d in collection]]
            for question in tests:
                scores = vectors @ matrix[mapping[question['question']]]
                order = np.argsort(-scores, kind='stable')[:int(config['candidate_count'])]
                candidates = [collection[int(index)] for index in order]
                if defense in ['rerank', 'filter_rerank']:
                    tfidf = TfidfVectorizer(stop_words='english', lowercase=True, norm='l2')
                    values = tfidf.fit_transform([question['question']] + [doc['text'] for doc in candidates])
                    lexical = (values[1:] @ values[0].T).toarray().ravel()
                    reranked = np.argsort(-lexical, kind='stable')
                    final = [candidates[int(index)] for index in reranked[:int(config['final_context_count'])]]
                else:
                    final = candidates[:int(config['final_context_count'])]
                row, payload = self._record(config, question, condition, defense, candidates, final, module=module, copies=copies)
                records.append(row)
                request_map[row['request_sha256']] = payload
        if modules.get('controlled', False):
            controlled = self.data('controlled_contexts.json')
            self._validate_controlled(controlled, tests)
            by_id = {q['id']: q for q in tests}
            for item in controlled:
                final = item['documents']
                row, payload = self._record(config, by_id[item['qid']], item['condition'], 'none', final, final,
                                            module='controlled', copies=0 if item['condition'] == 'clean' else 1)
                records.append(row)
                request_map[row['request_sha256']] = payload
        with (self.run_root / 'contexts.jsonl').open('w') as handle:
            for row in records:
                handle.write(json.dumps(row, ensure_ascii=False) + '\n')
        write_json(self.run_root / 'requests.json', request_map)
        rounds = int(config.get('rounds', 3))
        census = {'context_rows_per_round': len(records), 'rounds': rounds,
                  'condition_evaluations': len(records)*rounds, 'unique_payloads': len(request_map),
                  'logical_generation_calls': len(request_map)*rounds,
                  'max_transport_attempts': len(request_map)*rounds*int(config.get('max_attempts', 3)),
                  'successful_output_tokens_max': len(request_map)*rounds*int(config['max_tokens']),
                  'input_token_byte_upper_all_rounds': sum(len(encode(p))+512 for p in request_map.values())*rounds,
                  'primary_unit': 'Question/shared-fact group; condition rows and rounds are not independent questions'}
        write_json(self.run_root / 'request_census.json', census)
        names = ['design_freeze.json', 'design_freeze.json.sha256', 'embedding_texts.json',
                 'embedding_requests.json', 'embedding_responses.jsonl', 'embeddings.npz',
                 'embeddings_manifest.json', 'contexts.jsonl', 'requests.json', 'request_census.json']
        manifest = {'phase': 'generation_before_completions', 'frozen_at_utc': now(),
                    'run_hashes': self._hash_paths([self.run_root/name for name in names], self.run_root),
                    'census': census, 'python': platform.python_version(),
                    'numpy': np.__version__, 'scikit_learn': sklearn.__version__}
        self._seal('generation_freeze.json', manifest)
        return manifest

    def _validate_controlled(self, rows, tests):
        questions = {q['id']: q for q in tests}
        canonical = {doc['id']: doc for doc in self.data('clean_documents.json')}
        insertions = self.data('insertions.json')
        expected_insertions = {condition: {doc['target_qid']: doc for doc in insertions[condition]}
                               for condition in ['targeted', 'unrelated', 'benign']}
        if not rows:
            raise ExperimentError('Controlled module contains no eligible cases')
        grouped = {}
        for row in rows:
            if row['qid'] not in questions or len(row['documents']) != 5:
                raise ExperimentError('Invalid controlled question or context length')
            grouped.setdefault(row['qid'], {})
            if row['condition'] in grouped[row['qid']]:
                raise ExperimentError('Duplicate controlled arm')
            grouped[row['qid']][row['condition']] = row['documents']
        for qid, arms in grouped.items():
            if set(arms) != {'clean', 'targeted', 'unrelated', 'benign'}:
                raise ExperimentError('Each controlled question requires four arms')
            changing = [i for i in range(5) if len({d[i]['text'] for d in arms.values()}) > 1]
            if len(changing) != 1:
                raise ExperimentError('Controlled arms must differ at exactly one fixed position')
            slot = changing[0]
            if any(doc[slot]['id'] in set(questions[qid]['support_ids']) for doc in arms.values()):
                raise ExperimentError('Controlled replacement slot must not be a required support')
            for i in range(5):
                if i != slot and len({encode(d[i]) for d in arms.values()}) != 1:
                    raise ExperimentError('Controlled fixed documents differ across arms')
                if i != slot:
                    fixed = arms['clean'][i]
                    if fixed['id'] not in canonical or encode(fixed) != encode(canonical[fixed['id']]):
                        raise ExperimentError('Controlled fixed evidence differs from canonical clean document')
            if len({len(d[slot]['text'].split()) for d in arms.values()}) != 1:
                raise ExperimentError('Controlled replacement slot word lengths must match')
            for condition, final in arms.items():
                if len({doc['id'] for doc in final}) != 5:
                    raise ExperimentError('Controlled context contains duplicate document IDs')
                if not set(questions[qid]['support_ids']) <= {doc['id'] for doc in final}:
                    raise ExperimentError('Controlled context removed a required support')
                if condition != 'clean':
                    expected = expected_insertions[condition][qid]
                    if any(final[slot].get(field) != expected.get(field)
                           for field in ['text', 'kind', 'target_qid', 'verified', 'trust']):
                        raise ExperimentError('Controlled insertion differs from its paired core insertion')
                elif (final[slot].get('kind') != 'clean' or not final[slot].get('verified')
                      or final[slot].get('trust') not in {'high', 'medium'}):
                    raise ExperimentError('Controlled clean filler must have accepted clean labels')

    def _response_cache(self, requests, rounds):
        cache = {}
        for row in read_jsonl(self.run_root / 'responses.jsonl'):
            key = (int(row['round_id']), row['request_sha256'])
            if key in cache or key[0] not in range(1, rounds+1) or key[1] not in requests:
                raise ExperimentError('Unexpected or duplicate generation cache key')
            if digest(encode(row['response'])) != row['response_sha256']:
                raise ExperimentError('Generation response hash mismatch')
            if row['response'].get('model') != self.data('config.json')['generator']:
                raise ExperimentError('Cached completion model mismatch')
            cache[key] = row
        return cache

    def retrieval_stress(self):
        """Label-error sensitivity only. Produces no generator or embedding call."""
        self.verify_design()
        if (self.run_root / 'generation_freeze.json').exists():
            self.verify_generation()
        config, tests, docs = [self.data(name) for name in self.DATA_NAMES[:3]]
        manifest = self.run('embeddings_manifest.json')
        if digest((self.run_root / 'embeddings.npz').read_bytes()) != manifest['matrix_sha256']:
            raise ExperimentError('Vectors changed before retrieval-only stress')
        matrix = np.load(self.run_root / 'embeddings.npz')['matrix']
        mapping = {text: i for i, text in enumerate(self.run('embedding_texts.json'))}
        records = []
        for question in tests:
            supports = set(question['support_ids'])
            selected_support = sorted(supports)[0]
            non_support = sorted(d['id'] for d in docs if d['id'] not in supports)
            if not non_support:
                raise ExperimentError('Stress control requires an accepted clean non-support document')
            selected_distractor = non_support[0]
            for condition, rejected in [('all_accepted', None), ('support_rejected', selected_support),
                                        ('distractor_rejected', selected_distractor)]:
                variant = [dict(d, verified=False, trust='untrusted') if d['id'] == rejected else dict(d) for d in docs]
                for defense in ['none', 'filter']:
                    collection = variant if defense == 'none' else [d for d in variant if d['verified'] and d['trust'] in {'high','medium'}]
                    vectors = matrix[[mapping[d['text']] for d in collection]]
                    order = np.argsort(-(vectors @ matrix[mapping[question['question']]]), kind='stable')[:int(config['candidate_count'])]
                    candidates = [collection[int(i)] for i in order]
                    final = candidates[:int(config['final_context_count'])]
                    final_ids = [d['id'] for d in final]
                    records.append({'qid': question['id'], 'condition': condition, 'defense': defense,
                                    'rejected_id': rejected, 'selected_support_id': selected_support,
                                    'selected_distractor_id': selected_distractor,
                                    'candidate_ids': [d['id'] for d in candidates], 'final_ids': final_ids,
                                    'gold_support_ids': question['support_ids'],
                                    'all_support': supports <= set(final_ids),
                                    'support_fraction': len(supports & set(final_ids))/len(supports)})
        path = self.run_root / 'retrieval_label_stress.jsonl'
        path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in records))
        grouped = []
        for condition in ['all_accepted', 'support_rejected', 'distractor_rejected']:
            for defense in ['none', 'filter']:
                group = [r for r in records if r['condition'] == condition and r['defense'] == defense]
                grouped.append({'condition': condition, 'defense': defense, 'n': len(group),
                                'all_support_count': sum(r['all_support'] for r in group),
                                'all_support_rate': sum(r['all_support'] for r in group)/len(group),
                                'mean_support_fraction': sum(r['support_fraction'] for r in group)/len(group)})
        summary = {'at_utc': now(), 'rows': len(records), 'question_count': len(tests), 'generation_calls': 0,
                   'embedding_calls': 0, 'summary': grouped, 'records_sha256': digest(path.read_bytes()),
                   'selection_rule': 'Lowest sorted required support ID and lowest sorted clean non-support ID, selected separately for each question',
                   'scope': 'Sensitivity to hypothetical supplied-label errors. Measures annotated-support coverage, not factual answer utility, equivalent evidence, or operational authorization security.'}
        write_json(self.run_root / 'retrieval_label_stress_summary.json', summary)
        return summary

    def generate(self, workers=1):
        # Mandatory even with a completely empty response cache.
        requests = self.verify_generation()
        config = self.data('config.json')
        rounds = int(config.get('rounds', 3))
        cache = self._response_cache(requests, rounds)
        completed = len(cache)
        for round_id in range(1, rounds+1):
            pending = [key for key in requests if (round_id, key) not in cache]
            pending.sort(key=lambda key: digest(f'round-order:{round_id}:{key}'.encode()))

            def one(key):
                # Obtain the payload from freshly verified frozen bytes, not a stale memory object.
                payload = self.verify_generation()[key]
                response, request_id, attempts, latency = self._call('chat/completions', payload,
                                                  expected_hash=key, round_id=round_id)
                choices = response.get('choices')
                if not isinstance(choices, list) or len(choices) != 1:
                    self.stop.set()
                    raise PermanentAPIError('Expected one completion choice')
                finish = choices[0].get('finish_reason')
                row = {'round_id': round_id, 'request_sha256': key,
                       'response_sha256': digest(encode(response)), 'response': response,
                       'request_id': request_id, 'attempts': attempts, 'latency_seconds': latency,
                       'received_at_utc': now(), 'finish_reason': finish,
                       'status': 'complete' if finish == 'stop' else 'truncated' if finish == 'length' else 'needs_review'}
                self.append('responses.jsonl', row)
                return (round_id, key), row

            with ThreadPoolExecutor(max_workers=max(1, int(workers))) as pool:
                futures = [pool.submit(one, key) for key in pending]
                for future in as_completed(futures):
                    key, row = future.result()
                    cache[key] = row
                    completed += 1
                    if completed % 25 == 0 or completed == len(requests)*rounds:
                        print(f'Generation progress: {completed}/{len(requests)*rounds}', flush=True)
        self.verify_generation()
        rows = list(cache.values())
        completion = {'completed_at_utc': now(), 'model': config['generator'], 'rounds': rounds,
                      'unique_payloads': len(requests), 'fresh_provider_successes': len(rows),
                      'condition_evaluations': self.run('request_census.json')['condition_evaluations'],
                      'normal_stop': sum(row['status'] == 'complete' for row in rows),
                      'truncations': sum(row['status'] == 'truncated' for row in rows),
                      'other_finish_reasons': sum(row['status'] == 'needs_review' for row in rows),
                      'responses_sha256': digest((self.run_root / 'responses.jsonl').read_bytes()),
                      'cost_committed_usd': self._committed_cost(), 'model_fallbacks': 0,
                      'note': 'Fresh calls do not guarantee independent provider samples; within-round payload reuse is explicit.'}
        write_json(self.run_root / 'completion.json', completion)
        return completion


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--run-root', type=Path, required=True)
    parser.add_argument('--stage', choices=['design', 'embeddings', 'contexts', 'stress', 'generation', 'all'], default='design')
    parser.add_argument('--execute-api', action='store_true')
    parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args()
    runner = StudyRunner(args.data_root, args.run_root, execute_api=args.execute_api)
    if args.stage in ['design', 'all']:
        print(json.dumps(runner.design(), ensure_ascii=False))
    if args.stage in ['embeddings', 'all']:
        runner.embeddings()
    if args.stage in ['contexts', 'all']:
        print(json.dumps(runner.contexts(), ensure_ascii=False))
    if args.stage == 'stress' or (args.stage == 'all' and runner.data('config.json').get('modules', {}).get('label_stress', True)):
        print(json.dumps(runner.retrieval_stress(), ensure_ascii=False))
    if args.stage in ['generation', 'all']:
        print(json.dumps(runner.generate(args.workers), ensure_ascii=False))


if __name__ == '__main__':
    main()
