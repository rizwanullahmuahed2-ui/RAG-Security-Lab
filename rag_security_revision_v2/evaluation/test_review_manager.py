"""Submission-gate tests with explicitly synthetic, temporary case records."""
import csv
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import review_manager as manager


class ReviewGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'human_review_packet').mkdir()
        (self.root / 'coordinator_only').mkdir()
        (self.root / 'human_review_packet/REVIEW_STATUS.json').write_text(json.dumps({'review_case_ids': ['synthetic-case']}))
        self.patcher = patch.object(manager, 'ROOT', self.root)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop(); self.temp.cleanup()

    def write(self, path, row):
        with path.open('w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=list(row))
            writer.writeheader(); writer.writerow(row)

    def submission(self, stage, identity):
        fields = manager.STAGE1 if stage == 1 else manager.STAGE2
        row = {'review_case_id': 'synthetic-case', 'reviewer_id': identity,
               'rationale_and_source': 'Synthetic fixture only; no human judgment.',
               'reviewed_at_utc': '2026-10-26T00:00:00+00:00'}
        row.update({key: sorted(values)[0] for key, values in fields.items()})
        path = self.root / f'fixture-{identity}-stage{stage}.csv'
        self.write(path, row)
        return path

    def test_blank_forms_cannot_be_counted_as_review(self):
        path = self.root / 'blank.csv'
        self.write(path, {'review_case_id': 'synthetic-case', 'reviewer_id': ''})
        with self.assertRaisesRegex(ValueError, 'nonempty reviewer ID'):
            manager.validate(path, 1)
        self.assertFalse(manager.gate_status()['adjudication_complete'])

    def test_target_sheet_cannot_release_before_two_locked_initial_reviews(self):
        manager.lock(self.submission(1, 'synthetic-person-a'), 1)
        with self.assertRaisesRegex(ValueError, 'Exactly two'):
            manager.release_stage2()

    def test_invalid_consensus_labels_do_not_open_completion_gate(self):
        for identity in ['synthetic-person-a', 'synthetic-person-b']:
            manager.lock(self.submission(1, identity), 1)
            manager.lock(self.submission(2, identity), 2)
        (self.root / 'coordinator_only/coordinator_confirmation.json').write_text(json.dumps({
            'actual_human_reviewers_confirmed': True, 'initial_independence_confirmed': True,
            'reviewer_ids': ['synthetic-person-a', 'synthetic-person-b']}))
        row = {'review_case_id': 'synthetic-case',
               'adjudicated_factual_correctness': 'not-a-valid-label',
               'adjudicated_context_support': 'supported', 'adjudicated_clean_support': 'supported',
               'adjudicated_abstention': 'none', 'adjudicated_target_endorsement': 'reject',
               'adjudicated_target_falsity_validity': 'contradicted', 'reference_decision': 'accepted',
               'adjudicator_id': 'synthetic-person-a', 'reason_and_evidence': 'Synthetic test only.',
               'adjudicated_at_utc': '2026-10-26T00:00:00+00:00'}
        self.write(self.root / 'coordinator_only/Adjudication_AFTER_INDEPENDENT_LOCKS.csv', row)
        result = manager.gate_status()
        self.assertFalse(result['adjudication_complete'])
        self.assertEqual(result['status'], 'required_pending_actual_human_review')


if __name__ == '__main__':
    unittest.main(verbosity=2)
