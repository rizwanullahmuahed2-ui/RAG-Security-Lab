"""Execute frozen API embeddings and real generative LLM evaluation.

Headers and credentials are never written to logs. No fallback model is used.
The --stage option allows retrieval to be frozen before generating test answers.
"""
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import hashlib
import json
import os
import platform
import threading
import time
import urllib.request
import urllib.error

import numpy as np
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer

ROOT = Path(__file__).resolve().parent
LOCK = threading.Lock()
STOP = threading.Event()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encode(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def read(name):
    return json.loads((ROOT / name).read_text())


def save(name, obj):
    (ROOT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def append(name, obj):
    with LOCK:
        with (ROOT / name).open("a") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def load_key():
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        for line in (ROOT.parents[1] / ".env").read_text().splitlines():
            if line.strip().startswith("OPENAI_API_KEY="):
                key = line.split("=", 1)[1].strip().strip("\"'")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is absent")
    return key


def api(path, payload, key):
    raw = encode(payload)
    for attempt in range(1, 4):
        if STOP.is_set():
            raise RuntimeError("Stopped after another request failed")
        req = urllib.request.Request("https://api.openai.com/v1/" + path, data=raw,
                                     headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                obj = json.load(response)
                request_id = response.headers.get("x-request-id")
            return obj, request_id, attempt
        except urllib.error.HTTPError as exc:
            try:
                err = json.loads(exc.read()).get("error", {})
            except Exception:
                err = {}
            transient = exc.code in [408, 429, 500, 502, 503, 504] and err.get("code") != "insufficient_quota"
            append("api_errors.jsonl", {"at_utc": datetime.now(timezone.utc).isoformat(), "endpoint": path,
                                       "status": exc.code, "type": err.get("type"), "code": err.get("code"), "attempt": attempt})
            if not transient or attempt == 3:
                STOP.set()
                raise RuntimeError(f"API failure: HTTP {exc.code}; code={err.get('code')}") from None
        except (urllib.error.URLError, TimeoutError) as exc:
            append("api_errors.jsonl", {"endpoint": path, "error_class": type(exc).__name__, "attempt": attempt})
            if attempt == 3:
                STOP.set()
                raise RuntimeError("API network failure") from None
        time.sleep(attempt * 2)


def verify_freeze():
    for name, expected in read("freeze.json")["hashes"].items():
        if digest((ROOT / name).read_bytes()) != expected:
            raise RuntimeError("Frozen input changed: " + name)


def embeddings(config, tests, docs, inserts, key):
    text_list = [d["text"] for d in docs]
    for condition in ["targeted", "unrelated", "benign"]:
        text_list += [d["text"] for d in inserts[condition]]
    text_list += [q["question"] for q in tests]
    text_list = list(dict.fromkeys(text_list))
    mapping = {text: i for i, text in enumerate(text_list)}
    if (ROOT / "embeddings.npz").exists():
        meta = read("embeddings_manifest.json")
        assert meta["texts_sha256"] == digest(encode(text_list))
        assert meta["matrix_sha256"] == digest((ROOT / "embeddings.npz").read_bytes())
        matrix = np.load(ROOT / "embeddings.npz")["matrix"]
        return matrix, mapping
    chunks, records = [], []
    for offset in range(0, len(text_list), 128):
        payload = {"model": config["embedding_model"], "input": text_list[offset:offset+128],
                   "dimensions": config["embedding_dimensions"], "encoding_format": "float"}
        obj, request_id, attempts = api("embeddings", payload, key)
        assert obj["model"] == config["embedding_model"], obj["model"]
        values = sorted(obj["data"], key=lambda x: x["index"])
        assert [x["index"] for x in values] == list(range(len(payload["input"])))
        chunks.extend(x["embedding"] for x in values)
        records.append({"offset": offset, "count": len(values), "model": obj["model"],
                        "request_id": request_id, "attempts": attempts, "usage": obj.get("usage"),
                        "request_sha256": digest(encode(payload)), "response_sha256": digest(encode(obj))})
        print(f"Embeddings {len(chunks)}/{len(text_list)}", flush=True)
    matrix = np.asarray(chunks, dtype=np.float32)
    assert matrix.shape == (len(text_list), config["embedding_dimensions"])
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    assert np.all(norms > 0)
    matrix = matrix / norms
    np.savez_compressed(ROOT / "embeddings.npz", matrix=matrix)
    save("embedding_texts.json", text_list)
    save("embeddings_manifest.json", {"model": config["embedding_model"], "dimensions": config["embedding_dimensions"],
                                      "normalization": "float32 L2", "texts_sha256": digest(encode(text_list)),
                                      "matrix_sha256": digest((ROOT / "embeddings.npz").read_bytes()), "batches": records})
    return matrix, mapping


def freeze_contexts(config, tests, docs, inserts, matrix, mapping):
    if (ROOT / "contexts.jsonl").exists():
        m = read("generation_freeze.json")
        assert digest((ROOT / "contexts.jsonl").read_bytes()) == m["contexts_sha256"]
        assert digest((ROOT / "requests.json").read_bytes()) == m["requests_sha256"]
        return
    requests = {}
    records = []
    for condition in config["conditions"]:
        added = [] if condition == "clean" else inserts["targeted" if condition == "accepted_label" else condition]
        if condition == "accepted_label":
            added = [dict(d, verified=True, trust="high") for d in added]
        for defense in config["defenses"]:
            collection = docs + added
            if defense in ["filter", "filter_rerank"]:
                collection = [d for d in collection if d["verified"] and d["trust"] in ["high", "medium"]]
            vectors = matrix[[mapping[d["text"]] for d in collection]]
            for q in tests:
                query = matrix[mapping[q["question"]]]
                scores = vectors @ query
                order = np.argsort(-scores, kind="stable")[:config["candidate_count"]]
                candidates = [collection[int(j)] for j in order]
                if defense in ["rerank", "filter_rerank"]:
                    tfidf = TfidfVectorizer(stop_words="english", lowercase=True, norm="l2")
                    x = tfidf.fit_transform([q["question"]] + [d["text"] for d in candidates])
                    lexical = (x[1:] @ x[0].T).toarray().ravel()
                    reranked = np.argsort(-lexical, kind="stable")
                    final = [candidates[int(j)] for j in reranked[:config["final_context_count"]]]
                else:
                    final = candidates[:config["final_context_count"]]
                passages = "\n\n".join(config["passage_template"].format(rank=i+1, text=d["text"]) for i, d in enumerate(final))
                content = config["user_template"].format(question=q["question"], passages=passages)
                payload = {"model": config["generator"], "temperature": config["temperature"],
                           "max_tokens": config["max_tokens"], "store": config["store"],
                           "messages": [{"role": "system", "content": config["system_prompt"]},
                                        {"role": "user", "content": content}]}
                request_hash = digest(encode(payload))
                requests[request_hash] = payload
                final_ids = [d["id"] for d in final]
                supports = set(q["support_ids"])
                own = [d for d in final if d.get("target_qid") == q["id"]]
                support_ranks = [i+1 for i, d in enumerate(final) if d["id"] in supports]
                records.append({"qid": q["id"], "condition": condition, "defense": defense,
                                "request_sha256": request_hash, "candidate_ids": [d["id"] for d in candidates],
                                "final_ids": final_ids, "gold_support_ids": q["support_ids"],
                                "support_fraction": len(supports & set(final_ids))/len(supports),
                                "all_support": supports <= set(final_ids), "any_support": bool(support_ranks),
                                "first_support_reciprocal_rank": 1/min(support_ranks) if support_ranks else 0,
                                "assigned_insert_exposed": bool(own),
                                "any_insert_exposed": any(d["kind"] != "clean" for d in final),
                                "insert_occupancy": sum(d["kind"] != "clean" for d in final)/len(final),
                                "own_false_claim_exposed": condition in ["targeted", "accepted_label"] and bool(own)})
    with (ROOT / "contexts.jsonl").open("w") as f:
        for row in records:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    save("requests.json", requests)
    save("generation_freeze.json", {"frozen_at_utc": datetime.now(timezone.utc).isoformat(),
                                    "condition_evaluations": len(records), "unique_requests": len(requests),
                                    "contexts_sha256": digest((ROOT / "contexts.jsonl").read_bytes()),
                                    "requests_sha256": digest((ROOT / "requests.json").read_bytes()),
                                    "run_script_sha256": digest(Path(__file__).read_bytes()),
                                    "input_freeze_sha256": digest((ROOT / "freeze.json").read_bytes()),
                                    "embeddings_manifest_sha256": digest((ROOT / "embeddings_manifest.json").read_bytes()),
                                    "python": platform.python_version(), "numpy": np.__version__, "scikit_learn": sklearn.__version__})
    print(f"Frozen {len(records)} condition rows and {len(requests)} distinct requests", flush=True)


def generate(config, key, workers):
    manifest = read("generation_freeze.json")
    assert digest(Path(__file__).read_bytes()) == manifest["run_script_sha256"]
    requests = read("requests.json")
    cache = {}
    path = ROOT / "responses.jsonl"
    if path.exists():
        for line in path.read_text().splitlines():
            row = json.loads(line)
            assert row["request_sha256"] not in cache
            assert digest(encode(requests[row["request_sha256"]])) == row["request_sha256"]
            assert digest(encode(row["response"])) == row["response_sha256"]
            cache[row["request_sha256"]] = row
    pending = [(h, p) for h, p in requests.items() if h not in cache]
    # Interleave requests deterministically, avoiding condition-order/time confounding.
    pending.sort(key=lambda hp: digest(("request-order:"+hp[0]).encode()))
    completed = len(cache)
    def one(item):
        h, payload = item
        started = time.monotonic()
        obj, request_id, attempts = api("chat/completions", payload, key)
        if obj.get("model") != config["generator"]:
            STOP.set()
            raise RuntimeError("Generator snapshot mismatch")
        row = {"request_sha256": h, "response_sha256": digest(encode(obj)), "response": obj,
               "request_id": request_id, "attempts": attempts,
               "latency_seconds": time.monotonic()-started, "received_at_utc": datetime.now(timezone.utc).isoformat()}
        append("responses.jsonl", row)
        return h
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(one, item) for item in pending]
        for future in as_completed(futures):
            future.result()
            completed += 1
            if completed % 20 == 0 or completed == len(requests):
                print(f"Generated {completed}/{len(requests)} distinct responses", flush=True)
    save("completion.json", {"completed_at_utc": datetime.now(timezone.utc).isoformat(),
                             "unique_responses": completed, "condition_evaluations": manifest["condition_evaluations"],
                             "model": config["generator"], "model_fallbacks": 0,
                             "responses_sha256": digest(path.read_bytes())})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["retrieval", "generation", "all"], default="all")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    verify_freeze()
    config, tests, docs, inserts = [read(name) for name in ["config.json", "test_questions.json", "clean_documents.json", "insertions.json"]]
    key = load_key()
    if args.stage in ["retrieval", "all"]:
        matrix, mapping = embeddings(config, tests, docs, inserts, key)
        freeze_contexts(config, tests, docs, inserts, matrix, mapping)
    if args.stage in ["generation", "all"]:
        generate(config, key, args.workers)


if __name__ == "__main__":
    main()
