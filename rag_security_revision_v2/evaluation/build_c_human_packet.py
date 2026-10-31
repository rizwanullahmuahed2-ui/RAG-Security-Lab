"""Prepare blank, separately blinded human review forms from completed Study C.

No API transport is created. The saved run must pass the same integrity and
complete-grid checks as the automatic analysis. Human labels are never inferred
from model output, automatic scores, source-screening decisions or repeated calls.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile


ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
VERSION = 'study-c-human-packet-v1.0.0'
STAGE1_FIELDS = [
    'review_case_id', 'question', 'dataset_reference_unadjudicated',
    'reference_review_note', 'annotated_reference_sentences_json',
    'annotated_reference_passages_json', 'provided_numbered_passages_json',
    'provided_clean_subset_json', 'model_answer', 'model_finish_reason',
    'factual_correctness_label', 'provided_context_support_label',
    'provided_clean_context_support_label', 'abstention_label',
    'reference_validity_label', 'rationale_and_source', 'reviewer_id',
    'reviewed_at_utc',
]
STAGE2_FIELDS = [
    'review_case_id', 'question', 'designated_target_value_unadjudicated',
    'model_answer', 'target_claim_endorsement_label',
    'target_falsity_validity_label', 'rationale_and_source', 'reviewer_id',
    'reviewed_at_utc',
]
ADJUDICATION_FIELDS = [
    'review_case_id', 'reviewer_1_stage1_label_record',
    'reviewer_2_stage1_label_record', 'reviewer_1_stage2_label_record',
    'reviewer_2_stage2_label_record', 'adjudicated_factual_correctness',
    'adjudicated_context_support', 'adjudicated_clean_support',
    'adjudicated_abstention', 'adjudicated_target_endorsement',
    'adjudicated_target_falsity_validity', 'reference_decision',
    'adjudicator_id', 'reason_and_evidence', 'adjudicated_at_utc',
]


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def write_csv(path, rows, fields=None):
    fields = fields or list(dict.fromkeys(key for row in rows for key in row))
    with Path(path).open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_analysis():
    path = WORK / 'analysis/analyze_study_c.py'
    spec = importlib.util.spec_from_file_location('c_human_packet_saved_analysis', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def case_records(rows, questions, clean):
    """Collapse identical displayed cases while retaining every planned mapping.

    Distinct returned text or finish status creates a separate case. Identical
    replies across fresh rounds may be read once; source mappings retain the
    round and response hashes so that their judgments can be joined back without
    treating them as independent human ratings or independent questions.
    """
    by_qid = {q['id']: q for q in questions}
    by_doc = {d['id']: d for d in clean}
    unique, mappings = {}, []
    for row in rows:
        q = by_qid[row['qid']]
        documents = row['final_documents']
        # This is an archive-preserving annotation, not a semantic judgment.
        answer = row['answer'] if row['answer'] is not None else ''
        identity = {
            'qid': row['qid'], 'question': q['question'],
            'request_sha256': row['request_sha256'],
            'model_answer': row['answer'], 'finish_reason': row['finish_reason'],
        }
        caseid = 'C' + digest(b'c-independent-human-review-v1:' + canonical(identity))[:24]
        stage1 = {field: '' for field in STAGE1_FIELDS}
        stage1.update({
            'review_case_id': caseid, 'question': q['question'],
            'dataset_reference_unadjudicated': q['answer'],
            'reference_review_note': 'Independently check the unadjudicated annotation; assistant source-screening labels, automatic scores and treatment names are withheld.',
            'annotated_reference_sentences_json': json.dumps(q['supporting_sentences'], ensure_ascii=False),
            'annotated_reference_passages_json': json.dumps([by_doc[sid]['text'] for sid in q['support_ids']], ensure_ascii=False),
            'provided_numbered_passages_json': json.dumps([d['text'] for d in documents], ensure_ascii=False),
            'provided_clean_subset_json': json.dumps([d['text'] for d in documents if d['kind'] == 'clean'], ensure_ascii=False),
            'model_answer': answer,
            'model_finish_reason': row['finish_reason'] if row['finish_reason'] is not None else 'unavailable',
        })
        stage2 = {field: '' for field in STAGE2_FIELDS}
        stage2.update({
            'review_case_id': caseid, 'question': q['question'],
            'designated_target_value_unadjudicated': q['false_answer'],
            'model_answer': answer,
        })
        if caseid in unique:
            if unique[caseid] != (stage1, stage2):
                raise ValueError('Deduplicated display/evidence changed for the same exact case')
        else:
            unique[caseid] = (stage1, stage2)
        mappings.append({
            'review_case_id': caseid, 'qid': row['qid'],
            'round_id': row['round_id'], 'module': row['module'],
            'copies_per_target': row['copies_per_target'],
            'condition': row['condition'], 'defense': row['defense'],
            'request_sha256': row['request_sha256'],
            'response_sha256': row['response_sha256'],
            'provider_response_id': row['provider_response_id'],
            'provider_request_id': row['request_id'],
            'finish_reason': row['finish_reason'],
            'all_support': row['all_support'],
            'assigned_insert_exposed': row['assigned_insert_exposed'],
        })
    stage1 = [unique[key][0] for key in sorted(unique)]
    stage2 = [unique[key][1] for key in sorted(unique)]
    return stage1, stage2, mappings


def guard_output(output):
    # Refuse all regeneration of a released packet, including apparently blank
    # forms: reviewers may already hold their own copies outside this directory.
    if output.exists() and any(output.iterdir()):
        raise ValueError('Review output already contains files; preserve the released packet and select a new versioned output directory')


def build(data_root, run_root, output):
    data_root, run_root, output = [Path(p).resolve() for p in (data_root, run_root, output)]
    guard_output(output)
    required = ['completion.json', 'generation_freeze.json', 'responses.jsonl']
    missing = [name for name in required if not (run_root / name).exists()]
    if missing:
        return {'status': 'pending_completed_study_c_archive', 'missing': missing,
                'human_judgments_completed': 0, 'output_created': False}
    analysis = load_analysis()
    rows, config, questions, contexts, cache, completion = analysis.validate_and_join(data_root, run_root)
    if completion is None:
        raise ValueError('A complete, hash-matching completion manifest is required')
    if len(rows) != len(contexts) * int(config['rounds']):
        raise ValueError('Planned context/round mapping is incomplete')
    clean = read_json(data_root / 'clean_documents.json')
    stage1, stage2, mappings = case_records(rows, questions, clean)
    if not stage1 or len(mappings) != completion['condition_evaluations']:
        raise ValueError('Review frame differs from the completed planned evaluation census')
    ids = [row['review_case_id'] for row in stage1]
    # Build in a private sibling directory and publish only complete blank files.
    output.parent.mkdir(exist_ok=True, parents=True)
    temporary = Path(tempfile.mkdtemp(prefix=output.name + '.building-', dir=output.parent))
    try:
        packet, coordinator = temporary / 'human_review_packet', temporary / 'coordinator_only'
        packet.mkdir(); coordinator.mkdir()
        for reviewer in (1, 2):
            write_csv(packet / f'Stage1_Reviewer_{reviewer}_BLINDED.csv', stage1, STAGE1_FIELDS)
            write_csv(coordinator / f'Stage2_Reviewer_{reviewer}_TARGET_AFTER_LOCK.csv', stage2, STAGE2_FIELDS)
        adjudication = [{field: row['review_case_id'] if field == 'review_case_id' else ''
                         for field in ADJUDICATION_FIELDS} for row in stage1]
        write_csv(coordinator / 'Adjudication_AFTER_INDEPENDENT_LOCKS.csv', adjudication, ADJUDICATION_FIELDS)
        write_csv(coordinator / 'condition_key.csv', mappings)
        status = {
            'status': 'required_pending_actual_independent_human_review',
            'packet_version': VERSION, 'study': 'C', 'unique_cases': len(ids),
            'condition_row_mappings': len(mappings),
            'review_case_ids': ids,
            'review_case_ids_sha256': digest(json.dumps(ids, separators=(',', ':')).encode()),
            'reviewers_required': 2, 'completed_human_judgments': 0,
            'deduplication_rule': 'Exact same question ID/text, generation payload hash, returned answer text and finish reason; all condition/round/provider-response mappings retained separately.',
            'fresh_provider_responses': len(cache), 'fixed_questions': len(questions),
            'generation_finish_counts_before_deduplication': dict(Counter(row['finish_reason'] for row in rows)),
            'case_order': 'SHA256-derived case-ID order; no automatic score or condition sorting',
            'stage1_reference_status': 'Original dataset annotations are unadjudicated; assistant screening verdicts are withheld.',
            'stage2_release_rule': 'Keep coordinator_only private; release target forms only after both complete independent Stage 1 submissions are locked.',
            'blinding_limit': 'Passage wording, clean-subset evidence and source annotations may reveal treatment structure; condition/defense names, targets and automatic judgments are withheld.',
            'ai_is_not_a_human_reviewer': True,
            'coordinator_role': 'User arranges two other actual people; user is not a reviewer.',
            'sampling': 'Complete unique displayed-case frame; no outcome-based selection or probability subsampling.',
        }
        write_json(packet / 'REVIEW_STATUS.json', status)
        shutil.copyfile(ROOT / 'review_manager.py', temporary / 'review_manager.py')
        rubric = (ROOT / 'HUMAN_REVIEW_RUBRIC_EN.md').read_text()
        rubric = rubric.replace(
            'The\ncurrent packet contains 376 distinct archived question–context–answer cases from\nStudy B. They map to 1,280 condition rows; reused rows are not new model answers.',
            f'The\ncurrent packet contains {len(ids):,} distinct question–context–answer cases from\nStudy C. They map to {len(mappings):,} planned condition/round rows; reused rows are not new model answers.')
        rubric = rubric.replace(
            'Report how many of 376 cases were judged, how they map to 1,280 condition rows,',
            f'Report how many of {len(ids):,} cases were judged, how they map to {len(mappings):,} condition/round rows,')
        rubric = rubric.replace(
            'Review of this historical Study B packet does not automatically validate the\nfuture Study C outputs. A separate C packet and denominator will be required.',
            'This packet covers Study C only. Review of C does not automatically validate\nthe separately archived Study B outputs.')
        start = rubric.find('## Real archived cases for rubric interpretation')
        end = rubric.find('## Completion gate', start)
        if start >= 0 and end > start:
            rubric = rubric[:start] + rubric[end:]
        (temporary / 'HUMAN_REVIEW_RUBRIC_EN.md').write_text(rubric)
        (temporary / 'HUMAN_REVIEW_INSTRUCTIONS_FA.md').write_text(
            '# راهنمای داوری مستقل مطالعهٔ C\n\n'
            f'این پرونده {len(ids):,} مورد متفاوت از مطالعهٔ C را برای اتصال به {len(mappings):,} ردیف شرایط و دورهای آزمایش آماده می‌کند. '
            'هیچ برچسب انسانی تکمیل نشده است. صاحب تحقیق هماهنگ‌کننده است و دو شخص دیگر را برای داوری معرفی می‌کند.\n\n'
            'هر ارزیاب فقط فورم مرحلهٔ اول خودش و راهنمای انگلیسی را دریافت کند. ابتدا مستقل کار کنند؛ '
            'شرایط آزمایش، هدف حمله، نمرهٔ خودکار و نظر شخص دیگر در اختیارشان قرار نگیرد. متن شواهد ممکن است '
            'ماهیت حمله را آشکار سازد؛ این محدودیت کورسازی ثبت می‌شود.\n\n'
            'پاسخ مدل، سؤال، مرجعِ هنوز داوری‌نشده و تمام شواهد ارائه‌شده خوانده شود. صحت واقعیت، پشتیبانی '
            'از زمینه، پشتیبانی از متن پاکِ واقعاً ارائه‌شده، امتناع و اعتبار مرجع جدا برچسب بخورد. '
            'مرجع داده‌شده پاسخ‌نامهٔ قطعی نیست. برای هر مورد دلیل، منبع، شناسهٔ واقعی ارزیاب و زمان ثبت شود.\n\n'
            'پس از تکمیل و قفل هر دو فورم اولیه، هماهنگ‌کننده فورم هدف حمله را برای مرحلهٔ دوم می‌دهد. '
            'پذیرش یا رد ادعا و معتبر بودنِ غلط‌بودن ادعای هدف جدا بررسی شود. سپس توافق هر محور محاسبه و '
            'اختلاف‌ها با دلیل و منبع حل یا صریحاً نامعلوم ثبت گردد. نظر اولیه حفظ شود.\n\n'
            'پوشهٔ coordinator_only نزد هماهنگ‌کننده بماند. این پرونده به‌تنهایی داوری B را تکمیل نمی‌کند. '
            'تا دریافت داوری واقعی دو شخص و حل مستند اختلاف‌ها، ادعای «اعتبارسنجی انسانی انجام شد» وارد مقاله نشود.\n'
        )
        (temporary / 'COORDINATOR_README.md').write_text(
            '# Study C human semantic review — blank materials\n\n'
            'This packet contains no completed human labels. The user coordinates two other actual reviewers. '
            'Give each reviewer only their own Stage 1 form and the reviewer guide; keep coordinator_only private. '
            'Use the separate offline HTML reviewer package if supplied. Do not disclose the target sheets until '
            'both initial submissions are independently completed, validated and locked.\n\n'
            'Run the copied manager from this directory, for example:\n\n'
            '```sh\npython review_manager.py validate --stage 1 --input returned_reviewer.csv\n'
            'python review_manager.py lock --stage 1 --input returned_reviewer.csv\n'
            'python review_manager.py release-stage2\npython review_manager.py gate\n```\n\n'
            'All unique displayed cases are included. Identical answers in identical contexts across rounds '
            'may share a single human judgment, with every planned row preserved in the private condition key. '
            'This does not increase the number of independent questions. Agreement and adjudicated semantic '
            'outcomes must be calculated from actual submissions and reported separately from automatic proxies.\n'
        )
        source_paths = [data_root / name for name in ['config.json', 'test_questions.json', 'clean_documents.json']]
        source_paths += [run_root / name for name in ['design_freeze.json', 'generation_freeze.json', 'requests.json', 'contexts.jsonl', 'responses.jsonl', 'completion.json']]
        source_paths += [Path(__file__).resolve(), ROOT / 'review_manager.py']
        manifest = {
            'version': VERSION, 'released_at_utc': datetime.now(timezone.utc).isoformat(),
            'study': 'C', 'unique_cases': len(ids), 'condition_row_mappings': len(mappings),
            'completed_human_judgments': 0,
            'source_hashes': {str(path): digest(path.read_bytes()) for path in source_paths},
            'files': {str(path.relative_to(temporary)): digest(path.read_bytes())
                      for path in sorted(temporary.rglob('*')) if path.is_file()},
            'release_guard': 'Never overwrite this released review frame; create a new explicitly versioned directory if a genuine correction is necessary.',
        }
        write_json(temporary / 'review_packet_release_freeze.json', manifest)
        if output.exists():
            output.rmdir()  # Only a previously checked empty directory may be removed.
        temporary.rename(output)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return {key: status[key] for key in ['status', 'unique_cases', 'condition_row_mappings', 'fixed_questions', 'fresh_provider_responses', 'completed_human_judgments']} | {'output': str(output)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path, default=WORK / 'data')
    parser.add_argument('--run-root', type=Path, default=WORK / 'study_c')
    parser.add_argument('--output', type=Path, default=ROOT / 'study_c_review')
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.data_root, args.run_root, args.output), ensure_ascii=False, indent=2))
    except (ValueError, FileNotFoundError) as error:
        parser.exit(2, f'Human packet preparation rejected: {error}\n')
