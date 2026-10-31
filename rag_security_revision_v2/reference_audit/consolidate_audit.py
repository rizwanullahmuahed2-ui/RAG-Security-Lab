"""Join the two assistant source audits without changing archived annotations."""
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
BASE = WORK.parent / 'revision' / 'experiment'


def save(name, value):
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    questions = json.loads((BASE / 'test_questions.json').read_text())
    records = []
    source_files = {}
    for name in ['B_first32.json', 'B_last32.json']:
        path = ROOT / name
        source_files[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        records += json.loads(path.read_text())['records']
    by_qid = {row['qid']: row for row in records}
    assert len(records) == len(by_qid) == len(questions) == 64
    joined = []
    for index, question in enumerate(questions):
        row = dict(by_qid[question['id']])
        assert row['gold'] == question['answer']
        assert row['designated_false'] == question['false_answer']
        row['index_zero_based'] = index
        row['eligible_source_aligned_exact_relation'] = (
            row['gold_status'] == 'accepted'
            and row['false_status'] == 'contradicted_by_exact_source')
        row['numeric_surface_named_entity'] = question['id'] == '5a7653d25542992db9473765'
        row['eligible_source_aligned_quantitative_sensitivity'] = (
            row['eligible_source_aligned_exact_relation'] and not row['numeric_surface_named_entity'])
        row['human_validation_status'] = 'required_pending_actual_independent_reviewers'
        row['original_annotation_changed'] = False
        joined.append(row)
    summary = {
        'scope': 'Retrospective assistant source/snapshot audit; no human validation or universal external truth verification',
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'n_questions': len(joined),
        'gold_status_counts': dict(Counter(row['gold_status'] for row in joined)),
        'false_status_counts': dict(Counter(row['false_status'] for row in joined)),
        'source_aligned_exact_relation_cases': sum(row['eligible_source_aligned_exact_relation'] for row in joined),
        'source_aligned_quantitative_sensitivity_cases': sum(row['eligible_source_aligned_quantitative_sensitivity'] for row in joined),
        'human_judgments_completed': 0,
        'archived_annotations_and_outputs_changed': False,
        'warning': 'Accepted means consistency with the specified source-defined relation, not independently established factual truth. The sensitivity subset is selected retrospectively from reference audit criteria, not a new untouched test.',
        'source_audits_sha256': source_files,
    }
    save('B_reference_cards_v2.json', {'summary': summary, 'records': joined})
    save('B_reference_audit_summary.json', summary)
    columns = ['index_zero_based', 'qid', 'gold', 'designated_false', 'gold_status', 'false_status',
               'numeric_surface_named_entity', 'eligible_source_aligned_exact_relation',
               'eligible_source_aligned_quantitative_sensitivity', 'reason', 'human_validation_status']
    with (ROOT / 'B_reference_audit_index.csv').open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows({key: row.get(key, '') for key in columns} for row in joined)

    rows = list(csv.DictReader((BASE / 'scored_results.csv').open()))
    sets = {
        'all_64_archived_cases': set(by_qid),
        'source_aligned_exact_relation_retrospective': {r['qid'] for r in joined if r['eligible_source_aligned_exact_relation']},
        'source_aligned_quantitative_retrospective': {r['qid'] for r in joined if r['eligible_source_aligned_quantitative_sensitivity']},
    }
    sensitivity = []
    for name, ids in sets.items():
        grouped = defaultdict(list)
        for row in rows:
            if row['qid'] in ids:
                grouped[(row['condition'], row['defense'])].append(row)
        for (condition, defense), selected in grouped.items():
            assert len(selected) == len(ids)
            out = {'subset': name, 'condition': condition, 'defense': defense, 'n': len(selected)}
            for field in ['numeric_gold_only', 'numeric_false_only', 'all_support', 'assigned_insert_exposed']:
                out[field + '_count'] = sum(
                    int(str(row[field]).strip().lower() in {'true', '1', '1.0'})
                    for row in selected)
            sensitivity.append(out)
    with (ROOT / 'B_retrospective_source_sensitivity.csv').open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(sensitivity[0]))
        writer.writeheader(); writer.writerows(sensitivity)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
