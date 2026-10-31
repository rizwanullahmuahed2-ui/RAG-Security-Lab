"""Stage a portable public research snapshot without API calls or a Git push.

Run after the current manuscript/report exports are stable. Existing repository
files outside the five evidence directories are not edited or removed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
WORKSPACE = WORK.parent
ROOTS = ('rag_security_revision_v2', 'revision', 'research_phase',
         'implementation_plan', 'final_submission')
SKIP_COMPONENTS = {'.env', '.env.local', '.venv', '.git', '__pycache__',
                   'human_review_app'}
PRIVATE_PROTOCOL = {'model_access_check.json', 'model_access_latest.json',
                    'model_access_checks.jsonl', 'human_review_coordination.json',
                    'implementation_decisions.json'}
GENERATED_NAMES = {'PUBLICATION_MANIFEST.json', 'verify_evidence.py',
                   'requirements-reanalysis.txt'}

VERIFY_SCRIPT = r'''"""Verify published evidence offline without changing repository files.

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
'''

REQUIREMENTS = '''# Optional full saved-output reanalysis. Use Python 3.12.14 for the frozen runner.
numpy==2.3.5
scipy==1.17.0
scikit-learn==1.8.0
matplotlib==3.10.8
pyarrow==26.0.0
'''


def sha(path: Path) -> str:
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def eligible(path: Path, baseline_paths: set[str]) -> bool:
    relative = path.relative_to(WORKSPACE)
    if not path.is_file() or any(part in SKIP_COMPONENTS for part in relative.parts):
        return False
    if path.name.startswith('.env') or path.suffix in {'.pyc', '.zip', '.tmp'}:
        return False
    # Historical evidence is kept byte-for-byte for the 244-file comparison.
    if str(relative) in baseline_paths:
        return True
    if path.name == 'build_stdout.json' or path.name in GENERATED_NAMES:
        return False
    if path.parent == HERE and path.name in {'RELEASE_MANIFEST.json', 'LATEST_DELIVERY.json', 'build_release.py'}:
        return False
    if path.is_relative_to(HERE / 'qa'):
        return False
    if path.parent == WORK / 'protocol' and path.name in PRIVATE_PROTOCOL:
        return False
    parts = relative.parts
    if parts[:2] == ('rag_security_revision_v2', 'evaluation'):
        if 'coordinator_only' in parts:
            return False
        if 'human_review_packet' in parts:
            return path.name in {'REVIEW_STATUS.json', 'Stage1_Reviewer_1_BLINDED.csv'}
        if 'study_c_review' in parts:
            return path.name in {'REVIEW_STATUS.json', 'Stage1_Reviewer_1_BLINDED.csv'}
    return True


def assert_no_credential(path: Path) -> None:
    if path.stat().st_size >= 100 * 1024 * 1024:
        raise RuntimeError('File exceeds the normal GitHub file limit: ' + str(path))
    data = path.read_bytes()
    patterns = [rb'\bsk-(?:proj-|svcacct-|ant-)[A-Za-z0-9_-]{24,}',
                rb'\bgh[pousr]_[A-Za-z0-9]{30,}',
                rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']
    if any(re.search(pattern, data) for pattern in patterns):
        raise RuntimeError('Credential-like material detected; file not staged: ' + str(path))


def stage(destination: Path) -> dict:
    destination = destination.resolve()
    if destination == WORKSPACE or not (destination / '.git').exists():
        raise ValueError('Destination must be an existing isolated Git clone')
    baseline = json.loads((WORK / 'baseline/prior_files_sha256.json').read_text())['files']
    baseline_paths = set(baseline)
    files = []
    for name in ROOTS:
        for path in sorted((WORKSPACE / name).rglob('*')):
            if eligible(path, baseline_paths):
                assert_no_credential(path)
                relative = path.relative_to(WORKSPACE)
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
                files.append(target)
    release = destination / 'rag_security_revision_v2/release'
    generated = {release / 'verify_evidence.py': VERIFY_SCRIPT,
                 release / 'requirements-reanalysis.txt': REQUIREMENTS}
    for path, text in generated.items():
        path.write_text(text)
        files.append(path)
    # The separately authored guide is already copied with the source directory.
    assert (release / 'GITHUB_EVIDENCE_README_FA.md').is_file()
    for relative, expected in baseline.items():
        assert sha(destination / relative) == expected, relative
    manifest = {
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Public saved-evidence snapshot; no new inference or human labels created',
        'default_verification_command': 'python rag_security_revision_v2/release/verify_evidence.py',
        'saved_provider_responses': 2559,
        'condition_rows': 5208,
        'historical_baseline_files': 244,
        'current_review_scope': 'See current article and author-reported manual findings; archived optional review-protocol definitions are retained only to preserve frozen input hashes.',
        'files_sha256': {str(path.relative_to(destination)): sha(path) for path in sorted(set(files))},
    }
    manifest_path = release / 'PUBLICATION_MANIFEST.json'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    largest = sorted(files, key=lambda path: path.stat().st_size, reverse=True)[:5]
    return {'destination': str(destination), 'copied_files': len(files),
            'total_bytes': sum(path.stat().st_size for path in files),
            'baseline_files_verified': len(baseline),
            'largest_files': [{'path': str(path.relative_to(destination)), 'bytes': path.stat().st_size}
                              for path in largest],
            'manifest': str(manifest_path), 'new_api_calls': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, default=WORKSPACE / 'rag_security_delivery_repo')
    args = parser.parse_args()
    print(json.dumps(stage(args.destination), ensure_ascii=False, indent=2))
