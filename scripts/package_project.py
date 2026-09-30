"""Build a portable ZIP containing source, datasets, tests, and the latest completed run."""
from pathlib import Path
import json
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]


def package():
    files = set()
    for pattern in ("*.py", "*.md", "*.yaml", "requirements*.txt", "documents.csv", ".gitignore"):
        files.update(ROOT.glob(pattern))
    for folder in ("src", "tests", "scripts", "data", ".github"):
        files.update(p for p in (ROOT / folder).rglob("*") if p.is_file()
                     and not {"__pycache__", "chroma", "chroma_test"}.intersection(p.parts))
    latest = ROOT / "results/latest.json"
    if latest.exists():
        run_id = json.loads(latest.read_text())["run_id"]
        run = ROOT / "results/runs" / run_id
        if run.parent.resolve() != (ROOT / "results/runs").resolve():
            raise ValueError("Invalid latest run ID")
        if json.loads((run / "manifest.json").read_text())["status"] != "completed":
            raise ValueError("Latest run is not completed")
        files.add(latest)
        files.update(p for p in run.rglob("*") if p.is_file())
    destination = ROOT / "deliverables/RAG-Security-Lab.zip"
    destination.parent.mkdir(exist_ok=True)
    with ZipFile(destination, "w", ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(files):
            archive.write(path, Path("RAG-Security-Lab") / path.relative_to(ROOT))
    with ZipFile(destination) as archive:
        corrupt = archive.testzip()
        if corrupt:
            raise RuntimeError(f"Corrupt ZIP entry: {corrupt}")
    print(f"Packaged {len(files)} files: {destination} ({destination.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    package()
