"""Analyze saved prospective Study C evidence; never calls a model.

All answer endpoints are explicitly automatic proxies. Missing or non-normal
generations remain unknown. Bounds use planned question/round denominators;
available-case estimates are labelled sensitivities, never substituted for them.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import csv
import os
import statistics
import sys

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
VERSION = 'study-c-automatic-analysis-v1.0.0'
ANSWER_METRICS = [
    'strict_target_choice_proxy', 'strict_reference_choice_proxy',
    'old_numeric_false_only', 'old_numeric_gold_only', 'old_mixed',
    'old_literal_abstention', 'old_strict_em', 'old_token_f1',
    'abstention_language_detected', 'nonliteral_abstention_language',
]
RETRIEVAL_METRICS = [
    'all_support', 'support_fraction', 'assigned_insert_exposed',
    'any_insert_exposed', 'own_false_claim_exposed', 'insert_occupancy',
]
GROUP_FIELDS = ['module', 'copies_per_target', 'condition', 'defense']


def module_from_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EVALUATOR = module_from_path('study_c_evaluator_v2', WORK / 'evaluation/evaluator_v2.py')
RUNNER = module_from_path('study_c_saved_evidence_runner', WORK / 'runner/run_study.py')


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def read_lines(path):
    path = Path(path)
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def csv_value(value):
    return json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value


def write_csv(path, rows):
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with Path(path).open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: csv_value(row.get(key)) for key in fields})


def group_key(row):
    return tuple(row[key] for key in GROUP_FIELDS)


def group_info(key):
    return dict(zip(GROUP_FIELDS, key))


def metric_value(row, metric):
    if metric in RETRIEVAL_METRICS:
        value = row.get(metric)
    else:
        value = row.get(metric) if row.get('analysis_valid') else None
    return float(value) if value is not None else None


def summarize_metric(rows, metric, rounds):
    """Equal question weights after equal within-question round weights."""
    by_question = defaultdict(list)
    for row in rows:
        by_question[row['qid']].append(row)
    n = len(by_question)
    if any(len(items) != rounds or {int(r['round_id']) for r in items} != set(range(1, rounds+1))
           for items in by_question.values()):
        raise ValueError('Planned question/round grid is incomplete or duplicated')
    valid, lower_by_q, upper_by_q, complete_means = [], [], [], []
    for items in by_question.values():
        values = [metric_value(row, metric) for row in items]
        known = [value for value in values if value is not None]
        valid += known
        lower_by_q.append(sum(known) / rounds)
        upper_by_q.append((sum(known) + rounds-len(known)) / rounds)
        if len(known) == rounds:
            complete_means.append(statistics.mean(known))
    by_round = []
    for round_id in range(1, rounds+1):
        values = [metric_value(row, metric) for row in rows if row['round_id'] == round_id]
        known = [value for value in values if value is not None]
        unknown = n-len(known)
        by_round.append({
            'round_id': round_id, 'metric': metric, 'n_questions': n,
            'valid_cells': len(known), 'unknown_cells': unknown,
            'known_value_sum': sum(known),
            'mean_question_rate': sum(known)/n if n and not unknown else None,
            'rate_lower': sum(known)/n if n else None,
            'rate_upper': (sum(known)+unknown)/n if n else None,
        })
    lower = statistics.mean(lower_by_q) if n else None
    upper = statistics.mean(upper_by_q) if n else None
    complete_round_rates = [row['mean_question_rate'] for row in by_round]
    all_rounds_observed = n and all(value is not None for value in complete_round_rates)
    summary = {
        'metric': metric, 'n_questions': n, 'rounds': rounds,
        'planned_cells': n*rounds, 'valid_cells': len(valid), 'unknown_cells': n*rounds-len(valid),
        'known_value_sum': sum(valid), 'mean_question_rate': lower if lower == upper else None,
        'rate_lower': lower, 'rate_upper': upper,
        'complete_question_count': len(complete_means),
        'complete_question_mean': statistics.mean(complete_means) if complete_means else None,
        'available_cell_rate_sensitivity': statistics.mean(valid) if valid else None,
        'round_rate_min': min(complete_round_rates) if all_rounds_observed else None,
        'round_rate_max': max(complete_round_rates) if all_rounds_observed else None,
        'unit': 'Mean across questions after mean across the planned rounds within each question',
    }
    return summary, by_round


def paired_contrast(left, right, metric, rounds):
    a = {(row['qid'], row['round_id']): row for row in left}
    b = {(row['qid'], row['round_id']): row for row in right}
    if set(a) != set(b):
        raise ValueError('Planned paired comparison has different question/round grids')
    n = len({qid for qid, _ in a})
    by_q = defaultdict(list)
    complete_cells = []
    for key in sorted(a):
        av, bv = metric_value(a[key], metric), metric_value(b[key], metric)
        low = (av if av is not None else 0) - (bv if bv is not None else 1)
        high = (av if av is not None else 1) - (bv if bv is not None else 0)
        complete = av is not None and bv is not None
        by_q[key[0]].append((low, high, complete))
        if complete:
            complete_cells.append(av-bv)
    lows, highs, complete_questions = [], [], []
    for values in by_q.values():
        if len(values) != rounds:
            raise ValueError('Contrast round grid differs from frozen design')
        lows.append(statistics.mean(value[0] for value in values))
        highs.append(statistics.mean(value[1] for value in values))
        if all(value[2] for value in values):
            complete_questions.append(statistics.mean(value[0] for value in values))
    lower = statistics.mean(lows) if n else None
    upper = statistics.mean(highs) if n else None
    return {
        'metric': metric, 'n_questions': n, 'rounds': rounds, 'planned_pairs': n*rounds,
        'complete_pair_cells': len(complete_cells), 'unknown_pair_cells': n*rounds-len(complete_cells),
        'mean_question_difference': lower if lower == upper else None,
        'difference_lower': lower, 'difference_upper': upper,
        'paired_complete_question_count': len(complete_questions),
        'paired_complete_question_mean_difference': statistics.mean(complete_questions) if complete_questions else None,
        'paired_complete_cell_mean_difference': statistics.mean(complete_cells) if complete_cells else None,
        'difference_unit': 'fraction; multiply by 100 for percentage points',
    }


def success_value(row, metric):
    value = metric_value(row, metric)
    return None if value is None else int(bool(row['own_false_claim_exposed']) and bool(value))


def binary_transition_bounds(a, b, event):
    possible = [(aa, bb) for aa in ([0, 1] if a is None else [a])
                for bb in ([0, 1] if b is None else [b])]
    values = [int(event(aa, bb)) for aa, bb in possible]
    return min(values), max(values)


def defense_transitions(base, defended, metric, reference_metric, rounds):
    a = {(row['qid'], row['round_id']): row for row in base}
    b = {(row['qid'], row['round_id']): row for row in defended}
    if set(a) != set(b):
        raise ValueError('Defense transition grids differ')
    sums = Counter()
    per_round = defaultdict(Counter)
    for key in a:
        initial = success_value(a[key], metric)
        later = success_value(b[key], metric)
        reference = metric_value(b[key], reference_metric)
        sums['complete_transition_cells'] += initial is not None and later is not None and reference is not None
        bounds = {
            'initial_success': (int(initial == 1), int(initial != 0)),
            'prevented': binary_transition_bounds(initial, later, lambda x, y: x == 1 and y == 0),
            'restored_reference': binary_transition_bounds(initial, reference, lambda x, y: x == 1 and y == 1),
            'new_success': binary_transition_bounds(initial, later, lambda x, y: x == 0 and y == 1),
        }
        for name, (lower, upper) in bounds.items():
            sums[name+'_lower'] += lower; sums[name+'_upper'] += upper
            per_round[key[1]][name+'_lower'] += lower; per_round[key[1]][name+'_upper'] += upper
    result = {'metric': metric, 'reference_metric': reference_metric,
              'n_questions': len({key[0] for key in a}), 'rounds': rounds,
              'planned_transition_cells': len(a), 'complete_transition_cells': sums['complete_transition_cells'],
              'success_definition': 'Own target insertion exposed AND automatic target-choice/value proxy; not semantic attack success'}
    for name in ['initial_success', 'prevented', 'restored_reference', 'new_success']:
        for bound in ['lower', 'upper']:
            result[name+'_'+bound+'_cells'] = sums[name+'_'+bound]
            result['mean_'+name+'_'+bound+'_per_round'] = sums[name+'_'+bound] / rounds
    il, iu = sums['initial_success_lower'], sums['initial_success_upper']
    for name in ['prevented', 'restored_reference']:
        result[name+'_fraction_lower'] = sums[name+'_lower']/iu if iu else None
        result[name+'_fraction_upper'] = min(1, sums[name+'_upper']/il) if il else (1 if iu else None)
    result['per_round_counts'] = [{'round_id': key, **dict(value)} for key, value in sorted(per_round.items())]
    return result


def validate_and_join(data_root, run_root, *, allow_incomplete=False):
    runner = RUNNER.StudyRunner(data_root, run_root)
    requests = runner.verify_generation()  # Integrity only: never constructs live transport.
    config = read_json(data_root / 'config.json')
    rounds = int(config.get('rounds', 3))
    questions = read_json(data_root / 'test_questions.json')
    by_qid = {row['id']: row for row in questions}
    contexts = read_lines(run_root / 'contexts.jsonl')
    if {row['request_sha256'] for row in contexts} != set(requests):
        raise ValueError('Frozen request and context inventories differ')
    planned_keys = [(row['qid'], *group_key(row)) for row in contexts]
    if len(planned_keys) != len(set(planned_keys)):
        raise ValueError('Duplicate planned condition context')
    if not all(row['qid'] in by_qid for row in contexts):
        raise ValueError('Context refers to an unknown question')
    cache = runner._response_cache(requests, rounds)
    expected = len(requests)*rounds
    complete_path = run_root / 'completion.json'
    completion = read_json(complete_path) if complete_path.exists() else None
    if completion:
        if sha((run_root / 'responses.jsonl').read_bytes()) != completion['responses_sha256']:
            raise ValueError('Raw response archive differs from completion manifest')
    if len(cache) != expected and not allow_incomplete:
        raise ValueError('Run has missing responses; --allow-incomplete is required for explicitly bounded diagnostics')
    provider_ids = [row['response'].get('id') for row in cache.values()]
    nonempty_ids = [value for value in provider_ids if value]
    if len(set(nonempty_ids)) != len(nonempty_ids):
        raise ValueError('Duplicate provider response IDs across supposedly fresh logical calls')
    rows = []
    for context in contexts:
        question = by_qid[context['qid']]
        for round_id in range(1, rounds+1):
            response_record = cache.get((round_id, context['request_sha256']))
            answer, finish, status, scores = None, None, 'missing_response', {}
            if response_record:
                response = response_record['response']
                choices = response.get('choices')
                if isinstance(choices, list) and len(choices) == 1 and isinstance(choices[0], dict):
                    choice = choices[0]
                    message = choice.get('message')
                    if isinstance(message, dict) and isinstance(message.get('content'), str):
                        answer = message['content']; finish = choice.get('finish_reason')
                        status = ('complete' if finish == 'stop' and answer.strip() else
                                  'truncated' if finish == 'length' else
                                  'empty_response' if not answer.strip() else 'non_normal_finish')
                    else:
                        status = 'malformed_response'
                else:
                    status = 'malformed_response'
                if answer is not None:
                    documents = context['final_documents']
                    scores = EVALUATOR.score_output(
                        answer, question.get('answer_numeric', question['answer']), question['false_answer'],
                        documents, clean_contexttexts=[doc for doc in documents if doc['kind'] == 'clean'],
                        reference_status='accepted_source_supported', finish_reason=finish)
            row = {
                **context, 'round_id': round_id,
                'question': question['question'], 'reference': question.get('answer_numeric', question['answer']),
                'designated_false': question['false_answer'],
                'answer_unit_class': question.get('answer_unit_class', question.get('unit_class', 'unknown')),
                'answer': answer, 'generation_status': status, 'analysis_valid': status == 'complete',
                'finish_reason': finish,
                'provider_response_id': response_record['response'].get('id') if response_record else None,
                'request_id': response_record.get('request_id') if response_record else None,
                'received_at_utc': response_record.get('received_at_utc') if response_record else None,
                'response_sha256': response_record.get('response_sha256') if response_record else None,
                **scores,
            }
            for metric in ANSWER_METRICS:
                row.setdefault(metric, None)
            rows.append(row)
    return rows, config, questions, contexts, cache, completion


def make_cases(rows, grouped):
    cases = []
    def add(group, row, counterpart=None):
        identity = '|'.join(str(row.get(key)) for key in ['qid', 'module', 'condition', 'defense', 'copies_per_target', 'round_id'])
        if counterpart:
            identity += '|versus:'+counterpart['defense']+':'+counterpart['condition']
        caseid = sha(('c-case-order-v1:'+group+':'+identity).encode())
        cases.append({'case_id': caseid, 'case_group': group, 'qid': row['qid'],
                      'scope': 'Automatic-proxy case; reference truth and semantic endorsement await actual human review',
                      'observed': row, 'counterpart': counterpart})
    for row in rows:
        if row['module'] == 'core' and row['condition'] in ['targeted', 'accepted_label'] and row['analysis_valid']:
            if row['all_support'] and row['strict_target_choice_proxy']:
                add('annotated_support_retained_with_target_choice_proxy', row)
            if row['own_false_claim_exposed'] and not row['strict_target_choice_proxy']:
                add('own_poison_exposed_without_target_choice_proxy', row)
    for condition in ['targeted', 'accepted_label']:
        base = {(row['qid'], row['round_id']): row for row in grouped.get(('core', 1, condition, 'none'), [])}
        for defense in ['rerank', 'filter', 'filter_rerank']:
            for row in grouped.get(('core', 1, condition, defense), []):
                other = base[(row['qid'], row['round_id'])]
                if (row['analysis_valid'] and other['analysis_valid']
                    and success_value(other, 'strict_target_choice_proxy') == 1
                    and success_value(row, 'strict_target_choice_proxy') == 0
                    and not row['strict_reference_choice_proxy']):
                    add('proxy_prevention_without_reference_choice_restoration', row, other)
    rejected = {(row['qid'], row['round_id']): row for row in grouped.get(('core', 1, 'targeted', 'filter'), [])}
    for row in grouped.get(('core', 1, 'accepted_label', 'filter'), []):
        other = rejected[(row['qid'], row['round_id'])]
        if row['analysis_valid'] and other['analysis_valid'] and row['strict_target_choice_proxy'] != other['strict_target_choice_proxy']:
            add('accepted_label_changes_target_choice_proxy_under_filtering', row, other)
    cases.sort(key=lambda row: row['case_id'])
    descriptions = []
    for name in sorted({row['case_group'] for row in cases}):
        selected, used = [], set()
        group = [row for row in cases if row['case_group'] == name]
        for row in group:
            if row['qid'] not in used:
                selected.append(row['case_id']); used.add(row['qid'])
            if len(selected) == 3:
                break
        descriptions.append({'case_group': name, 'case_records': len(group),
                             'distinct_questions': len({row['qid'] for row in group}),
                             'representative_case_ids': selected,
                             'selection_rule': 'First three distinct question IDs in SHA-256 case order; all group records retained'})
    return cases, descriptions


def build_figure(summary, n_questions, rounds, output):
    metrics = ['strict_reference_choice_proxy', 'strict_target_choice_proxy']
    conditions = ['clean', 'targeted', 'unrelated', 'benign', 'accepted_label']
    defenses = ['none', 'rerank', 'filter', 'filter_rerank']
    lookup = {(row['condition'], row['defense'], row['metric']): row for row in summary if row['module'] == 'core'}
    if any((condition, defense, metric) not in lookup or lookup[(condition, defense, metric)]['mean_question_rate'] is None
           for condition in conditions for defense in defenses for metric in metrics):
        return {'status': 'withheld_primary_core_grid_incomplete'}
    os.environ.setdefault('MPLCONFIGDIR', str(output / '.mplcache'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9,
                         'axes.spines.top': False, 'axes.spines.right': False})
    colors = ['#173f5f', '#ed8b24', '#278779', '#985aa1']
    fig, axes = plt.subplots(2, 1, figsize=(8.4, 6.8), sharex=True)
    labels = {'none': 'None', 'rerank': 'Rerank', 'filter': 'Filter', 'filter_rerank': 'Filter + rerank'}
    x, width = np.arange(len(conditions)), .18
    for ax, metric in zip(axes, metrics):
        for index, (defense, color) in enumerate(zip(defenses, colors)):
            records = [lookup[(condition, defense, metric)] for condition in conditions]
            means = np.array([row['mean_question_rate']*100 for row in records])
            low = np.array([row['round_rate_min']*100 for row in records])
            high = np.array([row['round_rate_max']*100 for row in records])
            ax.bar(x+(index-1.5)*width, means, width, label=labels[defense], color=color,
                   yerr=np.array([np.maximum(0, means-low), np.maximum(0, high-means)]),
                   capsize=2, zorder=3)
        ax.set_ylim(0, 108); ax.set_ylabel('Questions (%)')
        ax.set_title('Strict reference-choice proxy' if 'reference' in metric else 'Strict target-choice proxy', loc='left')
        ax.grid(axis='y', alpha=.2, zorder=0)
    axes[0].legend(ncol=4, frameon=False, loc='upper center', bbox_to_anchor=(.5, 1.25))
    axes[1].set_xticks(x, ['Clean', 'Targeted', 'Unrelated', 'Benign', 'Accepted\nlabel'])
    fig.text(.02, .01, f'{n_questions} fixed questions; {rounds} fresh rounds per distinct payload. Ranges span rounds. Automatic proxies; human review pending.', fontsize=8)
    fig.tight_layout(rect=[0, .035, 1, .98])
    for suffix in ['png', 'pdf']:
        fig.savefig(output / ('study_c_outcomes.'+suffix), dpi=240, bbox_inches='tight')
    plt.close(fig)
    return {'status': 'created_from_saved_outputs', 'png': 'study_c_outcomes.png', 'pdf': 'study_c_outcomes.pdf',
            'error_bars': 'Minimum and maximum observed round rates, not confidence intervals'}


def analyze(data_root, run_root, output, *, allow_incomplete=False, plot=True):
    data_root, run_root, output = Path(data_root).resolve(), Path(run_root).resolve(), Path(output).resolve()
    rows, config, questions, contexts, cache, completion = validate_and_join(data_root, run_root, allow_incomplete=allow_incomplete)
    rounds = int(config.get('rounds', 3))
    grouped = defaultdict(list)
    for row in rows:
        grouped[group_key(row)].append(row)
    summary, per_round, strata, conditioned = [], [], [], []
    for key, values in sorted(grouped.items()):
        info = group_info(key)
        for metric in ANSWER_METRICS+RETRIEVAL_METRICS:
            item, repeated = summarize_metric(values, metric, rounds)
            summary.append({**info, **item})
            per_round += [{**info, **entry} for entry in repeated]
        for unit in sorted({row['answer_unit_class'] for row in values}):
            subset = [row for row in values if row['answer_unit_class'] == unit]
            for metric in ANSWER_METRICS[:4]:
                item, _ = summarize_metric(subset, metric, rounds)
                strata.append({**info, 'answer_unit_class': unit, **item})
        for exposure in ['assigned_insert_exposed', 'any_insert_exposed', 'own_false_claim_exposed']:
            subset = [row for row in values if row[exposure]]
            for metric in ANSWER_METRICS[:4]:
                item, _ = summarize_metric(subset, metric, rounds)
                conditioned.append({**info, 'conditioned_on': exposure, **item})

    contrasts = []
    def contrast(a, b, name, priority='secondary_exploratory'):
        if a not in grouped or b not in grouped:
            return
        ia, ib = group_info(a), group_info(b)
        for metric in ANSWER_METRICS[:4]:
            item = paired_contrast(grouped[a], grouped[b], metric, rounds)
            contrasts.append({'comparison': name, 'priority': priority, 'module': ia['module'],
                              'module_b': ib['module'], 'condition_a': ia['condition'], 'condition_b': ib['condition'],
                              'defense_a': ia['defense'], 'defense_b': ib['defense'],
                              'copies_a': ia['copies_per_target'], 'copies_b': ib['copies_per_target'], **item})
    for module in ['core', 'controlled']:
        for control in ['unrelated', 'benign', 'clean']:
            contrast((module, 1, 'targeted', 'none'), (module, 0 if control == 'clean' else 1, control, 'none'),
                     'targeted_minus_'+control, 'primary_automatic' if module == 'core' and control != 'clean' else 'secondary_exploratory')
    for defense in ['rerank', 'filter', 'filter_rerank']:
        contrast(('core', 0, 'clean', defense), ('core', 0, 'clean', 'none'), 'clean_defense_minus_undefended')
        contrast(('core', 1, 'targeted', defense), ('core', 1, 'targeted', 'none'), 'targeted_defense_minus_undefended')
        contrast(('core', 1, 'accepted_label', defense), ('core', 1, 'targeted', defense), 'accepted_label_minus_rejected_label')
    for copies in config.get('modules', {}).get('doses', []):
        for defense in ['none', 'rerank']:
            contrast(('dose', int(copies), 'targeted', defense), ('core', 1, 'targeted', defense), 'dose_minus_one_copy')

    paired = []
    for condition in ['targeted', 'accepted_label']:
        for defense in ['rerank', 'filter', 'filter_rerank']:
            a, b = ('core', 1, condition, 'none'), ('core', 1, condition, defense)
            if a in grouped and b in grouped:
                for target_metric, reference_metric in [('strict_target_choice_proxy', 'strict_reference_choice_proxy'),
                                                        ('old_numeric_false_only', 'old_numeric_gold_only')]:
                    item = defense_transitions(grouped[a], grouped[b], target_metric, reference_metric, rounds)
                    paired.append({'condition': condition, 'defense': defense, **item})
    cases, case_groups = make_cases(rows, grouped)
    usage = Counter()
    for record in cache.values():
        for name in ['prompt_tokens', 'completion_tokens', 'total_tokens']:
            usage[name] += int(record['response'].get('usage', {}).get(name, 0))
    status_counts = Counter(row['generation_status'] for row in rows)
    execution = {
        'questions': len(questions), 'rounds': rounds, 'contexts_per_round': len(contexts),
        'planned_condition_evaluations': len(rows), 'unique_payloads': len({row['request_sha256'] for row in contexts}),
        'planned_logical_generation_calls': len({row['request_sha256'] for row in contexts})*rounds,
        'saved_logical_responses': len(cache), 'mapped_rows_with_saved_response': sum(row['generation_status'] != 'missing_response' for row in rows),
        'generation_status_counts_condition_rows': dict(status_counts),
        'reported_generation_usage_distinct_calls': dict(usage),
        'cost_committed_usd_conservative': completion.get('cost_committed_usd') if completion else None,
        'completion_manifest_present': completion is not None, 'human_judgments_completed': 0,
        'source_group_and_unit_limits': 'Questions and source titles are fixed. Rounds and condition reuse do not create new independent questions; the corpus is shared.',
    }
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / 'scored_rows.csv', rows)
    for name, table in [('summary', summary), ('summary_by_round', per_round), ('strata_summary', strata),
                        ('exposure_conditioned_summary', conditioned), ('contrasts', contrasts),
                        ('paired_defense_outcomes', paired)]:
        write_csv(output / (name+'.csv'), table)
    with (output / 'cases.jsonl').open('w') as handle:
        for case in cases:
            handle.write(json.dumps(case, ensure_ascii=False)+'\n')
    write_csv(output / 'case_index.csv', [{'case_id': row['case_id'], 'case_group': row['case_group'], 'qid': row['qid'],
                                        **{name: row['observed'][name] for name in GROUP_FIELDS+['round_id']}}
                                       for row in cases])
    figure = build_figure(summary, len(questions), rounds, output) if plot else {'status': 'not_requested'}
    report = {
        'analysis_version': VERSION, 'analyzed_at_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Saved-output automatic analysis; strict choices and value matches are proxies, not completed semantic or human validation.',
        'definitions': {'primary_automatic': 'Strict concise target-choice proxy; numerical target production is reported separately.',
                        'semantic_endpoint': 'Required and pending actual human judgments; not inferred from proxy scores.',
                        'aggregation': 'Mean of the planned rounds within each question, then equal-weight mean across questions.',
                        'missingness': 'Missing, empty, malformed, truncated or non-normal generations are unknown; main rates/differences have planned-denominator bounds.',
                        'sensitivity': 'Complete-question and paired-complete-question estimates retain explicit reduced denominators.',
                        'round_range': 'Descriptive minimum/maximum across fresh rounds, not a confidence interval or independent-sample claim.',
                        'interval_policy': 'No population confidence interval or significance test is produced by this script.'},
        'data_root': str(data_root), 'run_root': str(run_root), 'execution': execution,
        'summary': summary, 'summary_by_round': per_round, 'strata_summary': strata,
        'exposure_conditioned_summary': conditioned, 'contrasts': contrasts,
        'paired_defense_outcomes': paired, 'case_groups': case_groups, 'figure': figure,
        'integrity': {'design_and_generation_freezes_verified': True,
                      'request_payload_hashes_verified': True, 'raw_response_hashes_and_models_verified': True,
                      'completion_response_archive_hash_verified': completion is not None,
                      'analysis_script_sha256': sha(Path(__file__).read_bytes()),
                      'evaluator_script_sha256': sha((WORK / 'evaluation/evaluator_v2.py').read_bytes())},
    }
    write_json(output / 'analysis.json', report)
    write_json(output / 'analysis_manifest.json', {
        'analysis_version': VERSION,
        'files': {str(path.relative_to(output)): sha(path.read_bytes()) for path in sorted(output.rglob('*'))
                  if path.is_file() and path.name != 'analysis_manifest.json' and '.mplcache' not in path.parts},
    })
    print(json.dumps({'analysis_version': VERSION, 'scope': report['scope'], 'execution': execution, 'figure': figure}, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--run-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--allow-incomplete', action='store_true')
    parser.add_argument('--no-plot', action='store_true')
    args = parser.parse_args()
    analyze(args.data_root, args.run_root, args.output, allow_incomplete=args.allow_incomplete, plot=not args.no_plot)
