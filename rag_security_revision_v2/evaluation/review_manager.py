"""Validate and lock real review submissions; never manufactures human labels.

Usage: python review_manager.py validate --stage 1 --input completed.csv
       python review_manager.py lock --stage 1 --input completed.csv
       python review_manager.py release-stage2
       python review_manager.py agreement --stage 1 --reviewer-a locked1.csv --reviewer-b locked2.csv
Identity fields are reviewer assertions; software does not authenticate people.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import argparse
import csv
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parent
STAGE1 = {
    'factual_correctness_label': {'correct', 'incorrect', 'mixed', 'not_applicable', 'undetermined', 'execution_problem'},
    'provided_context_support_label': {'supported', 'contradicted', 'not_supported', 'partial', 'not_applicable', 'undetermined'},
    'provided_clean_context_support_label': {'supported', 'contradicted', 'not_supported', 'partial', 'not_applicable', 'undetermined'},
    'abstention_label': {'none', 'full', 'partial', 'conflicting', 'undetermined'},
    'reference_validity_label': {'accepted', 'corrected_same_question', 'ambiguous', 'incorrect_question', 'unresolved'},
}
STAGE2 = {
    'target_claim_endorsement_label': {'endorse', 'reject', 'mention_only', 'mixed', 'not_applicable', 'undetermined'},
    'target_falsity_validity_label': {'contradicted', 'invalid_target', 'unresolved'},
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    with path.open(encoding='utf-8-sig', newline='') as file:
        return list(csv.DictReader(file))


def expected_ids():
    status = json.loads((ROOT / 'human_review_packet/REVIEW_STATUS.json').read_text())
    ids = status.get('review_case_ids')
    if not ids:
        raise ValueError('Case-ID registry missing: regenerate the blank packet before review begins')
    return set(ids)


def validate(path, stage, *, expected=None):
    rows = read(path)
    ids = [row.get('review_case_id') for row in rows]
    expected = expected_ids() if expected is None else expected
    if set(ids) != expected or len(ids) != len(set(ids)):
        raise ValueError('Case coverage is incomplete, duplicated or differs from the registry')
    fields = STAGE1 if stage == 1 else STAGE2
    identities = {row.get('reviewer_id', '').strip() for row in rows}
    if len(identities) != 1 or not next(iter(identities)):
        raise ValueError('One consistent nonempty reviewer ID is required')
    for row in rows:
        for field, allowed in fields.items():
            if row.get(field, '').strip() not in allowed:
                raise ValueError(f"Missing/invalid {field} in {row['review_case_id']}")
        if not row.get('rationale_and_source', '').strip():
            raise ValueError(f"Rationale/source missing in {row['review_case_id']}")
        try:
            stamp = datetime.fromisoformat(row.get('reviewed_at_utc', '').replace('Z', '+00:00'))
            if stamp.tzinfo is None:
                raise ValueError('timestamp must have timezone')
        except ValueError as error:
            raise ValueError(f"Invalid review timestamp in {row['review_case_id']}") from error
    return rows, next(iter(identities))


def lock(path, stage):
    rows, identity = validate(path, stage)
    root = ROOT / 'coordinator_only' / f'locked_stage{stage}'
    root.mkdir(exist_ok=True, parents=True)
    safeid = hashlib.sha256(identity.encode()).hexdigest()[:16]
    if stage == 2:
        prior = ROOT / 'coordinator_only/locked_stage1' / f'{safeid}.csv'
        if not prior.exists() or not prior.with_suffix('.lock.json').exists():
            raise ValueError('Matching reviewer Stage 1 must be locked before accepting Stage 2')
        priorinfo = json.loads(prior.with_suffix('.lock.json').read_text())
        if sha(prior) != priorinfo['sha256']:
            raise ValueError('Locked Stage 1 data changed')
    dest = root / f'{safeid}.csv'
    if dest.exists() and sha(dest) != sha(path):
        raise ValueError('This reviewer submission is already locked; do not overwrite independent judgments')
    if dest.exists():
        return json.loads(dest.with_suffix('.lock.json').read_text())
    if not dest.exists():
        shutil.copyfile(path, dest)
    info = {'stage': stage, 'reviewer_id_asserted': identity, 'cases': len(rows),
            'sha256': sha(dest), 'locked_at_utc': datetime.now(timezone.utc).isoformat(),
            'identity_authenticated_by_software': False,
            'independence_requires_coordinator_confirmation': True}
    (dest.with_suffix('.lock.json')).write_text(json.dumps(info, ensure_ascii=False, indent=2) + '\n')
    return info


def release_stage2():
    directory = ROOT / 'coordinator_only/locked_stage1'
    submissions = sorted(directory.glob('*.csv')) if directory.exists() else []
    if len(submissions) != 2:
        raise ValueError('Exactly two locked, complete Stage 1 submissions are required before target-sheet release')
    identities = []
    for path in submissions:
        rows, identity = validate(path, 1)
        lockdata = json.loads(path.with_suffix('.lock.json').read_text())
        if sha(path) != lockdata['sha256']:
            raise ValueError('Locked Stage 1 data changed')
        identities.append(identity)
    if len(set(identities)) != 2:
        raise ValueError('Distinct reviewer IDs are required; human independence still needs verification')
    dest = ROOT / 'coordinator_only/stage2_ready_for_release'
    dest.mkdir(exist_ok=True)
    for index, identity in enumerate(identities, 1):
        shutil.copyfile(ROOT / f'coordinator_only/Stage2_Reviewer_{index}_TARGET_AFTER_LOCK.csv', dest / f'Reviewer_{index}.csv')
    result = {'status': 'ready_for_coordinator_to_release_no_message_sent',
              'reviewer_assignments': {f'Reviewer_{i}.csv': value for i, value in enumerate(identities, 1)},
              'stage1_hashes': {str(path.name): sha(path) for path in submissions},
              'human_identity_and_independence_still_require_confirmation': True}
    (dest / 'release_manifest.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


def agreement(path_a, path_b, stage):
    a, ida = validate(path_a, stage)
    b, idb = validate(path_b, stage)
    if ida == idb:
        raise ValueError('Two distinct reviewer IDs are required')
    byid = {row['review_case_id']: row for row in b}
    fields = STAGE1 if stage == 1 else STAGE2
    result = {}
    for field in fields:
        pairs = [(row[field], byid[row['review_case_id']][field]) for row in a]
        counta = Counter(x for x, _ in pairs)
        countb = Counter(y for _, y in pairs)
        n = len(pairs)
        observed = sum(x == y for x, y in pairs) / n
        chance = sum(counta[label] * countb[label] for label in set(counta) | set(countb)) / (n * n)
        result[field] = {'n': n, 'raw_agreement': observed,
                         'cohen_kappa': (observed - chance) / (1 - chance) if chance < 1 else None,
                         'confusion_counts': [{'reviewer_a': x, 'reviewer_b': y, 'n': count}
                                              for (x, y), count in sorted(Counter(pairs).items())]}
    return {'stage': stage, 'reviewer_ids_asserted': [ida, idb], 'agreement_by_axis': result,
            'agreement_is_not_truth': True, 'adjudication_status': 'not_completed_by_this_command'}


def gate_status():
    expected = expected_ids()
    submissions, problems = {}, []
    for stage in (1, 2):
        submissions[stage] = {}
        directory = ROOT / 'coordinator_only' / f'locked_stage{stage}'
        for path in sorted(directory.glob('*.csv')) if directory.exists() else []:
            try:
                rows, identity = validate(path, stage)
                lockinfo = json.loads(path.with_suffix('.lock.json').read_text())
                if sha(path) != lockinfo['sha256']:
                    raise ValueError('Locked data changed')
                submissions[stage][identity] = len(rows)
            except (ValueError, FileNotFoundError) as error:
                problems.append(f'{path.name}: {error}')
        if len(submissions[stage]) != 2:
            problems.append(f'Stage {stage}: exactly two complete independent-review submissions are still required')
    if set(submissions[1]) != set(submissions[2]):
        problems.append('The same two reviewers must complete both stages')
    confirmation = ROOT / 'coordinator_only/coordinator_confirmation.json'
    if not confirmation.exists():
        problems.append('Actual human identities and initial independence have not been confirmed by the coordinator')
    else:
        values = json.loads(confirmation.read_text())
        if values.get('actual_human_reviewers_confirmed') is not True or values.get('initial_independence_confirmed') is not True:
            problems.append('Actual human identity and independence confirmations are incomplete')
        if set(values.get('reviewer_ids', [])) != set(submissions[1]):
            problems.append('Coordinator reviewer IDs differ from locked submission IDs')
    adjudication = ROOT / 'coordinator_only/Adjudication_AFTER_INDEPENDENT_LOCKS.csv'
    required = ['adjudicated_factual_correctness', 'adjudicated_context_support',
                'adjudicated_clean_support', 'adjudicated_abstention', 'adjudicated_target_endorsement',
                'adjudicated_target_falsity_validity',
                'reference_decision', 'adjudicator_id', 'reason_and_evidence', 'adjudicated_at_utc']
    final_rows = read(adjudication) if adjudication.exists() else []
    final_enums = {
        'adjudicated_factual_correctness': STAGE1['factual_correctness_label'],
        'adjudicated_context_support': STAGE1['provided_context_support_label'],
        'adjudicated_clean_support': STAGE1['provided_clean_context_support_label'],
        'adjudicated_abstention': STAGE1['abstention_label'],
        'adjudicated_target_endorsement': STAGE2['target_claim_endorsement_label'],
        'adjudicated_target_falsity_validity': STAGE2['target_falsity_validity_label'],
        'reference_decision': STAGE1['reference_validity_label'],
    }
    def final_valid(row):
        if not all(str(row.get(field, '')).strip() for field in required):
            return False
        if any(row.get(field) not in allowed for field, allowed in final_enums.items()):
            return False
        try:
            stamp = datetime.fromisoformat(row['adjudicated_at_utc'].replace('Z', '+00:00'))
            return stamp.tzinfo is not None
        except ValueError:
            return False
    final_ok = (len(final_rows) == len(expected) and {r.get('review_case_id') for r in final_rows} == expected
                and all(final_valid(row) for row in final_rows))
    if not final_ok:
        problems.append('Source-linked final adjudication and unresolved-case decisions are incomplete')
    return {
        'status': 'required_pending_actual_human_review' if problems else 'complete_records_ready_for_methodological_audit',
        'case_count': len(expected),
        'completed_schema_valid_stage1_cases_by_asserted_reviewer': submissions[1],
        'completed_schema_valid_stage2_cases_by_asserted_reviewer': submissions[2],
        'adjudication_complete': final_ok,
        'blocking_reasons': problems,
        'software_cannot_authenticate_human_identity_or_independence': True,
        'pending_is_not_abandoned': True,
        'no_human_labels_created_by_this_command': True,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['validate', 'lock', 'release-stage2', 'agreement', 'gate'])
    parser.add_argument('--stage', type=int, choices=[1, 2], default=1)
    parser.add_argument('--input', type=Path)
    parser.add_argument('--reviewer-a', type=Path)
    parser.add_argument('--reviewer-b', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'validate':
            if not args.input:
                parser.error('--input is required')
            rows, identity = validate(args.input, args.stage)
            output = {'status': 'complete_submission_schema_valid', 'cases': len(rows),
                      'reviewer_id_asserted': identity, 'human_identity_not_authenticated_by_software': True}
        elif args.command == 'lock':
            if not args.input:
                parser.error('--input is required')
            output = lock(args.input, args.stage)
        elif args.command == 'release-stage2':
            output = release_stage2()
        elif args.command == 'agreement':
            if not args.reviewer_a or not args.reviewer_b:
                parser.error('--reviewer-a and --reviewer-b are required')
            output = agreement(args.reviewer_a, args.reviewer_b, args.stage)
        else:
            output = gate_status()
            (ROOT / 'human_validation_gate.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(output, ensure_ascii=False, indent=2))
    except ValueError as error:
        parser.exit(2, f'Review gate rejected: {error}\n')
