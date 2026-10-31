"""Verify published evidence offline without changing repository files.

Uses only Python's standard library. No network or provider client is imported.
The historical checker writes a receipt, so it is executed in a temporary mirror
whose output receipt is never linked to the published receipt.
"""
from pathlib import Path
import hashlib
import json
import runpy
import shutil
import tempfile

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
REPOSITORY = PROJECT.parent

def filehash(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()

def link_or_copy(source, destination):
    try:
        destination.symlink_to(source, target_is_directory=source.is_dir())
    except (OSError, NotImplementedError):
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)

def main():
    manifest = json.loads((HERE / 'PUBLICATION_MANIFEST.json').read_text())
    mismatches = [name for name, expected in manifest['files_sha256'].items()
                  if not (REPOSITORY / name).is_file()
                  or filehash(REPOSITORY / name) != expected]
    if mismatches:
        raise SystemExit('Publication file missing or changed: ' + ', '.join(mismatches[:10]))
    selection_path = PROJECT / 'assistant_review/selection_freeze.json'
    selection = json.loads(selection_path.read_text())
    assert filehash(selection_path) == (selection_path.with_name(selection_path.name + '.sha256')).read_text().strip()
    assert all(filehash(PROJECT / name) == expected for name, expected in selection['source_hashes'].items())
    notes_path = PROJECT / 'assistant_review/AI_STAGE1_NOTES.json'
    lock = json.loads((PROJECT / 'assistant_review/AI_PASS1_LOCK.json').read_text())
    assert filehash(notes_path) == lock['ai_notes_sha256']
    notes = json.loads(notes_path.read_text())['records']
    assert len(notes) == 72 and {r['case_id'] for r in notes} == {r['case_id'] for r in selection['selection']}
    author = json.loads((PROJECT / 'manual_review/author_reported_findings.json').read_text())
    assert author['number_of_reviewed_responses'] == 72 and sum(author['main_sample_findings'].values()) == 64
    original_receipt = PROJECT / 'protocol/POSTRUN_QA.json'
    before_receipt = filehash(original_receipt)
    with tempfile.TemporaryDirectory(prefix='rag-evidence-check-') as directory:
        temporary = Path(directory)
        project = temporary / 'rag_security_revision_v2'
        project.mkdir()
        for child in PROJECT.iterdir():
            if child.name in {'.venv', '__pycache__', '.git'}:
                continue
            if child.name == 'protocol':
                protocol = project / 'protocol'
                protocol.mkdir()
                for item in child.iterdir():
                    if item.name == 'POSTRUN_QA.json':
                        continue
                    if item.name == 'verify_saved_study_c_independently.py':
                        # A real copy is essential: the checker resolves __file__.
                        shutil.copy2(item, protocol / item.name)
                    else:
                        link_or_copy(item, protocol / item.name)
            else:
                link_or_copy(child, project / child.name)
        for name in ('revision', 'research_phase', 'implementation_plan', 'final_submission'):
            link_or_copy(REPOSITORY / name, temporary / name)
        runpy.run_path(str(project / 'protocol/verify_saved_study_c_independently.py'),
                       run_name='__main__')
        result = json.loads((project / 'protocol/POSTRUN_QA.json').read_text())
        assert result['status'] == 'passed'
        assert result['response_count'] == 2559
        assert result['condition_rows_all_rounds'] == 5208
        assert result['baseline_files_unchanged'] == 244
    assert filehash(original_receipt) == before_receipt, 'Published receipt changed'
    print(json.dumps({'publication_files_verified': len(manifest['files_sha256']),
                      'saved_response_count': 2559, 'condition_rows': 5208,
                      'historical_baseline_files_unchanged': 244,
                      'semantic_case_selection_and_note_integrity_verified': 72,
                      'published_files_modified': 0, 'new_api_calls': 0,
                      'verification': 'passed'}, indent=2))

if __name__ == '__main__':
    main()
