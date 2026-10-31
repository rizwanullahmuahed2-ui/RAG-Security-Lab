"""The saved source snapshots must reproduce the committed dataset bytes."""
import os
from pathlib import Path
import shutil

from scripts import build_dataset


ROOT = Path(__file__).resolve().parents[1]


def test_offline_rebuild_uses_canonical_bytes_on_every_platform(tmp_path, monkeypatch):
    """Rebuild outside the checkout, including a simulated Windows newline default."""
    for directory in ("legacy", "sources"):
        shutil.copytree(ROOT / "data" / directory, tmp_path / "data" / directory)
    (tmp_path / "data" / "raw").mkdir()
    shutil.copy2(ROOT / "config.yaml", tmp_path / "config.yaml")
    monkeypatch.setattr(build_dataset, "ROOT", tmp_path)
    for line_separator in ("\n", "\r\n"):
        monkeypatch.setattr(os, "linesep", line_separator)
        manifest = build_dataset.build()
        for filename in manifest["files"]:
            generated = (tmp_path / "data" / "raw" / filename).read_bytes()
            assert generated == (ROOT / "data" / "raw" / filename).read_bytes()
        assert (tmp_path / "data" / "dataset_manifest.json").read_bytes() == (
            ROOT / "data" / "dataset_manifest.json").read_bytes()
        assert (tmp_path / "documents.csv").read_bytes() == (ROOT / "documents.csv").read_bytes()
