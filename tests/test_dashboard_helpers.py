"""Guard state, provenance and recovery behavior at the dashboard boundary."""
import json

import pandas as pd
import pytest

from src.generation.rag_pipeline import RagResult
from src.ui.dashboard import (
    answer_export, completed_runs, evidence_table, filter_rows,
    parse_selection_seeds, safe_source_url,
)


@pytest.mark.parametrize("value", ["", "42 42", "1 -1", "4294967296", "42,17", "one"])
def test_invalid_seed_input_rejected_before_running(value):
    with pytest.raises(ValueError):
        parse_selection_seeds(value)


def test_seed_order_and_boundaries_preserved():
    assert parse_selection_seeds("  17 42\n91 0 4294967295 ") == [17, 42, 91, 0, 4294967295]


def test_search_uses_literal_text_and_keeps_original_indices():
    frame = pd.DataFrame({"question": ["GDP (US$)", "Population"], "id": [1, 2]}, index=[7, 12])
    assert filter_rows(frame, " (us$) ").index.tolist() == [7]
    assert filter_rows(frame, "[").empty
    assert filter_rows(frame, "  ").equals(frame)


def test_saved_run_discovery_skips_corrupt_and_incomplete_runs(tmp_path):
    for name, manifest in (("good", '{"status":"completed"}'), ("bad-json", "{"),
                           ("partial", '{"status":"completed"}'), ("failed", '{"status":"failed"}'),
                           ("bad-shape", '[]')):
        folder = tmp_path / name
        folder.mkdir()
        (folder / "manifest.json").write_text(manifest)
    for name in ("summary_metrics.csv", "results.csv"):
        (tmp_path / "good" / name).write_text("field\nvalue\n")
    runs, skipped = completed_runs(tmp_path)
    assert [path.parent.name for path, _ in runs] == ["good"]
    assert set(skipped) == {"bad-json", "partial", "bad-shape"}


@pytest.mark.parametrize("value", ["javascript:alert(1)", "file:///etc/passwd", "//example.org", "https://", "http://[", None])
def test_untrusted_evidence_links_only_allow_web_urls(value):
    assert safe_source_url(value) is None


def test_evidence_export_contains_exact_context_and_attribution():
    evidence = [{"chunk_id": "P-1", "source": "Injected", "trust_level": "untrusted",
                 "verification_status": "unverified", "text": "An injected claim."}]
    saved = dict(result=RagResult("A question?", evidence, "An injected claim.", "A claim."),
                 selection_key=("Q1", "", 1, "none", 42, "targeted"), count=1, mode="targeted",
                 defense="none", seed=42, backends="hashing / extractive", gold="Truth",
                 verdict={"attack_success": True}, poison_ids={"P-1"},
                 target_copies_injected=1, target_copies_retrieved=1)
    exported = json.loads(answer_export(saved, {"setting": "value"}, {"input": "hash"}))
    assert exported["result"]["retrieved_documents"] == evidence
    assert exported["result"]["context"] == "An injected claim."
    assert exported["dataset_sha256"] == {"input": "hash"}
    assert exported["injected_poison_ids"] == ["P-1"]
    assert evidence_table(saved).iloc[0]["Evidence"] == "Injected poison"
    assert safe_source_url("https://example.org/source") == "https://example.org/source"
    saved["verdict"] = None
    assert json.loads(answer_export(saved, {}, {}))["ground_truth"] is None
