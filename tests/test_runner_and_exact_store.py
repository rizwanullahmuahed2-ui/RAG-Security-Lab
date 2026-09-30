"""Reproducibility, artifact isolation, and exact-search contract tests."""
from dataclasses import fields
import json
import numpy as np
import pytest

from src.vectorstore.exact_store import ExactVectorStore
from src.vectorstore.indexer import index_chunks
from src.evaluation.runner import execute


def test_exact_ties_stable_under_insertion_order():
    store = ExactVectorStore()
    vectors = np.asarray([[1., 0.], [1., 0.], [0., 1.]])
    store.add_documents("one", ["b", "a", "c"], vectors, ["b", "a", "c"], [{}, {}, {}])
    store.add_documents("two", ["c", "a", "b"], vectors[::-1], ["c", "a", "b"], [{}, {}, {}])
    for name in ("one", "two"):
        assert [r["chunk_id"] for r in store.query(name, np.array([1., 0.]), 3)] == ["a", "b", "c"]


def test_exact_zero_vectors_and_metadata_filter():
    store = ExactVectorStore()
    store.add_documents("x", ["clean", "poison"], np.array([[0., 0.], [1., 0.]]), ["a", "b"],
                        [{"trust_level": "high"}, {"trust_level": "untrusted"}])
    hits = store.query("x", np.array([1., 0.]), 5, {"trust_level": {"$in": ["high"]}})
    assert len(hits) == 1 and hits[0]["similarity_score"] == 0
    assert store.query("x", np.array([1., 0.]), 5, {"trust_level": {"$in": ["missing"]}}) == []


def test_exact_rejects_bad_inputs():
    store = ExactVectorStore()
    with pytest.raises(ValueError, match="finite"):
        store.add_documents("x", ["a"], np.array([[np.nan]]), ["a"], [{}])
    with pytest.raises(ValueError, match="Duplicate"):
        store.add_documents("x", ["a", "a"], np.ones((2, 1)), ["a", "a"], [{}, {}])
    with pytest.raises(ValueError, match="positive"):
        store.query("x", np.array([1.]), 0)


def test_exact_retrieval_correct_support(tiny_chunks, embedder):
    store = ExactVectorStore()
    index_chunks(tiny_chunks, embedder, store, "test")
    hits = store.query("test", embedder.encode_one("In what year was Da Afghanistan Bank established?"), 3)
    assert hits[0]["chunk_id"] == "CHK-DOC-5"


def test_runner_isolates_success_and_failure(tmp_path, monkeypatch, offline_config,
        tiny_documents, tiny_chunks, tiny_questions, tiny_poison_pool):
    config = offline_config
    config.project_root = tmp_path
    for name, frame in [("documents", tiny_documents), ("chunks", tiny_chunks),
                         ("questions", tiny_questions), ("poisoned_passages", tiny_poison_pool)]:
        path = tmp_path / f"{name}.csv"
        frame.to_csv(path, index=False)
        setattr(config.paths, f"{name}_csv", str(path))
    monkeypatch.setattr("src.evaluation.runner.generate_all_figures", lambda *a: None)
    first, first_summary = execute(config, experiment="clean", seeds=[17, 42])
    second, _ = execute(config, experiment="clean", seeds=[17])
    assert first != second
    assert first_summary.answer_accuracy.nunique() == 1
    assert first_summary.recall_at_k.nunique() == 1
    manifest = json.loads((first / "manifest.json").read_text())
    assert manifest["status"] == "completed" and manifest["n_records"] == 8
    assert manifest["actual_backends"]["vector_store"] == "exact"
    latest = (tmp_path / "results/latest.json").read_text()

    def fail(*args):
        raise RuntimeError("synthetic model initialization failure")
    monkeypatch.setattr("src.evaluation.runner.get_embedding_service", fail)
    with pytest.raises(RuntimeError, match="synthetic"):
        execute(config, experiment="clean")
    assert (tmp_path / "results/latest.json").read_text() == latest
    statuses = [json.loads(p.read_text())["status"] for p in (tmp_path / "results/runs").glob("*/manifest.json")]
    assert sorted(statuses) == ["completed", "completed", "failed"]


def test_fallback_disabled_by_default(monkeypatch, offline_config):
    from src.embeddings.embedding_service import get_embedding_service
    offline_config.embedding_backend = "sentence_transformers"
    def fail(*args):
        raise OSError("offline")
    monkeypatch.setattr("src.embeddings.embedding_service.SentenceTransformerEmbeddingService", fail)
    with pytest.raises(RuntimeError, match="fallback is disabled"):
        get_embedding_service(offline_config)
    offline_config.allow_fallback = True
    assert get_embedding_service(offline_config).backend_name.startswith("hashing")
