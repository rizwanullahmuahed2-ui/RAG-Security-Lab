"""Validate plan coverage, arithmetic and preservation of existing evidence."""
from pathlib import Path
import csv
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from pypdf import PdfReader
from docx import Document

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent


def read_json(name):
    return json.loads((ROOT / name).read_text())


def main():
    baseline = read_json('baseline_files_sha256.json')['files']
    changes = []
    for name, expected in baseline.items():
        path = WORKSPACE / name
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        if actual != expected:
            changes.append(name)
    assert not changes, changes

    mapping = read_json('requirements_work_package_map.json')
    original = json.loads((WORKSPACE / 'research_phase/gap_matrix.json').read_text())
    rows = mapping['requirements']
    assert len(rows) == 67
    assert len({row['requirement_id'] for row in rows}) == 67
    assert {row['requirement_id'] for row in rows} == {row['id'] for row in original['requirements']}
    source = {row['id']: row for row in original['requirements']}
    for row in rows:
        assert row['expert_force'] == source[row['requirement_id']]['force']
        assert row['research_status'] == source[row['requirement_id']]['status']
        assert row['primary_work_package'] in {f'P{i}' for i in range(9)}
        assert row['plan_status'] == 'planned_only_no_implementation'
    with (ROOT / 'Implementation_Tracker_FA.csv').open(encoding='utf-8-sig', newline='') as file:
        assert len(list(csv.DictReader(file))) == 67

    blueprint = read_json('Experiment_Blueprint.json')
    assert blueprint['status'] == 'proposed_unexecuted_not_a_frozen_protocol'
    n, rounds = 64, 3
    assert blueprint['core']['rows'] == n * 5 * 4 * rounds == 3840
    assert blueprint['core']['max_logical_generation_calls'] == n * 8 * rounds == 1536
    assert blueprint['controlled_exposure']['generation_calls_max'] == n * 4 * rounds == 768
    assert blueprint['optional_fixed_target_dose']['extra_rows'] == n * 2 * 2 * rounds == 768
    budget = blueprint['budget']
    assert budget['main_condition_rows'] == 3840 + 768 == 4608
    assert budget['main_logical_generation_calls_max'] == 1536 + 768 == 2304
    assert budget['with_dose_condition_rows'] == 4608 + 768 == 5376
    assert budget['with_dose_logical_generation_calls_max'] == 2304 + 768 == 3072
    assert budget['main_successful_output_tokens_max'] == 2304 * 64
    assert budget['with_dose_successful_output_tokens_max'] == 3072 * 64
    assert budget['with_dose_transport_attempts_max'] == 3072 * 3
    assert blueprint['generation']['across_round_response_reuse'] is False

    pdf_path = ROOT / 'Implementation_Plan_FA.pdf'
    document = PdfReader(pdf_path)
    bounds = ROOT / 'plan_text_bounds.html'
    subprocess.run(['pdftotext', '-bbox-layout', str(pdf_path), str(bounds)], check=True)
    namespace = {'x': 'http://www.w3.org/1999/xhtml'}
    pages = ET.parse(bounds).getroot().findall('.//x:page', namespace)
    assert len(pages) == len(document.pages)
    outside, replacement = [], 0
    for index, page in enumerate(pages):
        width, height = float(page.attrib['width']), float(page.attrib['height'])
        for word in page.findall('.//x:word', namespace):
            replacement += (word.text or '').count('\ufffd')
            left, top, right, bottom = [float(word.attrib[key]) for key in ['xMin','yMin','xMax','yMax']]
            if left < -1 or top < -1 or right > width + 1 or bottom > height + 1:
                outside.append({'page': index + 1, 'word': word.text})
    assert replacement == 0
    assert not outside, outside
    word_document = Document(ROOT / 'Implementation_Plan_FA.docx')
    assert len(word_document.tables) == 3

    quality = {
        'checked_at_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Implementation plan only; no manuscript revision, experimental execution or API inference',
        'work_packages': 9,
        'review_requirements_mapped': 67,
        'expert_force_and_research_status_preserved': True,
        'baseline_files_checked': len(baseline),
        'baseline_files_unchanged': not changes,
        'pdf_pages': len(document.pages),
        'docx_tables': len(word_document.tables),
        'pdf_replacement_glyphs': replacement,
        'pdf_words_outside_page': outside,
        'pdf_text_validation_engine': 'Poppler pdftotext bbox-layout; pypdf page count',
        'budget_arithmetic_checked': True,
        'new_generation_calls': 0,
        'new_embedding_calls': 0,
        'completed_human_judgments': 0,
        'new_protocol_frozen': False,
        'visual_review': 'Pending final visual inspection',
    }
    (ROOT / 'PLAN_QUALITY_CHECKS.json').write_text(json.dumps(quality, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(quality, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
