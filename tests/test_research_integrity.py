"""Regression tests for failures that change the validity of research results."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest

from src.attacks.poison_generator import create_poisoned_kb, select_poison_subset
from src.config.config import load_config
from src.data.loaders import DataValidationError, load_all, load_questions, validate_relationships
from src.evaluation import metrics
from src.evaluation.evaluator import run_condition, summarize
from src.evaluation.io import load_records, save_records
from src.generation.rag_pipeline import RagPipeline, RagResult
from src.retrieval.retriever import Retriever, RetrievedChunk
from src.vectorstore.chroma_store import ChromaVectorStore
from src.vectorstore.indexer import index_chunks

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("prediction,value", [("134 provinces", "34 provinces"), ("3.4", "4"),
    ("34%", "34"), ("-34", "34"), ("Kabulistan", "Kabul"), ("12.345", "12.34")])
def test_numeric_and_word_boundaries(prediction, value):
    assert not metrics.contains_value(prediction, value)


@pytest.mark.parametrize("prediction,value", [("It was 34.", "34"), ("42,647,492.00 people", "42647492.00"),
    ("The figure is 34%.", "34%"), ("کابل", "کابل")])
def test_numeric_punctuation_and_unicode(prediction, value):
    assert metrics.contains_value(prediction, value)


def test_mixed_answer_requires_review():
    verdict = metrics.score_targeted_answer("Kabul and Kandahar.", "Kabul", "Kandahar", True, True)
    assert verdict["ambiguous_answer"]
    assert not verdict["answer_correct"] and not verdict["attack_success"]


def test_seedless_generator_reproducible_between_processes():
    code = ("from src.attacks.poison_generator import generate_poison; "
            "print(generate_poison('What is the capital?', 'Kabul', 'Herat', 'P', 'A', 'Q')['poisoned_text'])")
    outputs = [subprocess.check_output([sys.executable, "-c", code], cwd=ROOT,
               env={**os.environ, "PYTHONHASHSEED": seed}, text=True) for seed in ("1", "99")]
    assert outputs[0] == outputs[1]


def test_nested_budgets(tiny_poison_pool):
    low = select_poison_subset(tiny_poison_pool, 1, 42)
    high = select_poison_subset(tiny_poison_pool, 2, 42)
    assert set(low.poison_id) <= set(high.poison_id)
    with pytest.raises(ValueError):
        select_poison_subset(tiny_poison_pool, -1, 42)


def test_poison_id_collision(tiny_chunks, tiny_poison_pool):
    tiny_poison_pool.loc[0, "poison_id"] = tiny_chunks.iloc[0].chunk_id
    with pytest.raises(ValueError, match="collide"):
        create_poisoned_kb(tiny_chunks, tiny_poison_pool, 3, 42)


def test_boolean_typo_rejected(tiny_questions, tmp_path):
    tiny_questions.loc[0, "targeted_for_attack"] = "treu"
    path = tmp_path / "questions.csv"
    tiny_questions.to_csv(path, index=False)
    with pytest.raises(DataValidationError, match="boolean"):
        load_questions(path)


def test_provenance_mismatch_rejected(tiny_documents, tiny_chunks, tiny_questions, tiny_poison_pool):
    tiny_chunks.loc[0, "trust_level"] = "medium"
    with pytest.raises(DataValidationError, match="provenance"):
        validate_relationships(tiny_documents, tiny_chunks, tiny_questions, tiny_poison_pool)


def test_config_paths_independent_of_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = load_config(ROOT / "config.yaml")
    data = load_all(config.paths)
    assert len(data["documents"]) == 224
    assert Path(config.paths.documents_csv).is_absolute()


def test_all_documents_indexed_and_splits_do_not_leak():
    data = load_all(load_config(ROOT / "config.yaml").paths)
    assert set(data["documents"].document_id) == set(data["chunks"].document_id)
    questions = data["questions"]
    assert questions.groupby("family_id").split.nunique().max() == 1
    assert questions.groupby("relevant_document_id").split.nunique().max() == 1
    assert not data["documents"].text.duplicated().any()


def test_source_snapshots_match_manifest():
    from src.evaluation.runner import sha256
    manifest = json.loads((ROOT / "data/dataset_manifest.json").read_text())
    for filename, digest in manifest["files"].items():
        assert sha256(ROOT / "data/raw" / filename) == digest


def test_store_instances_do_not_share_collections(tiny_chunks, embedder):
    first, second = ChromaVectorStore(), ChromaVectorStore()
    index_chunks(tiny_chunks, embedder, first, "same-name")
    assert first.count("same-name") == len(tiny_chunks)
    assert second.count("same-name") == 0


def test_filtering_prevents_candidate_starvation(tiny_chunks, tiny_poison_pool, embedder, store, source_filter, llm):
    combined, _ = create_poisoned_kb(tiny_chunks, tiny_poison_pool, 3, 42)
    index_chunks(combined, embedder, store, "filter-starvation")
    query = tiny_poison_pool.iloc[0].poisoned_text
    pipeline = RagPipeline(Retriever(embedder, store, "filter-starvation"), llm, "", 0, 100, 1, 1,
                           source_filter=source_filter)
    result = pipeline.answer(query, apply_filtering=True)
    assert len(result.retrieved_documents) == 1
    assert result.retrieved_documents[0]["trust_level"] == "high"


def test_reranker_empty_vocabulary(reranker):
    chunk = RetrievedChunk("id", "doc", "the and or", "", "", 1.0, 1, "high", "verified")
    assert reranker.rerank("the", [chunk], 1)[0].rerank_score == 0


def test_unrelated_poison_cannot_get_attack_credit(monkeypatch, tiny_chunks, tiny_poison_pool,
        tiny_questions, embedder, store, reranker, source_filter, llm, offline_config):
    def answer(*args, **kwargs):
        return RagResult("q", [{"chunk_id": "TPOI-2", "rerank_score": None, "original_similarity": .9}], "", "Kandahar")
    monkeypatch.setattr(RagPipeline, "answer", answer)
    offline_config.poisoning.random_seed = next(seed for seed in range(20)
        if select_poison_subset(tiny_poison_pool, 1, seed).iloc[0].poison_id == "TPOI-2")
    records = run_condition(tiny_chunks, tiny_poison_pool, tiny_questions,
        embedder, store, reranker, source_filter, llm, offline_config, 1, False, False, "unrelated-poison")
    q1 = records[0]
    assert q1["poison_retrieved"] and q1["false_claim_match"]
    assert not q1["attack_success"] and not q1["attack_injected"]
    assert not records[3]["targeted_for_attack"]  # literal 'False' must not become truthy


def test_result_roundtrip_and_injected_denominator(tmp_path, tiny_chunks, tiny_poison_pool,
        tiny_questions, embedder, store, reranker, source_filter, llm, offline_config):
    records = run_condition(tiny_chunks, tiny_poison_pool, tiny_questions,
        embedder, store, reranker, source_filter, llm, offline_config, 1, False, False, "roundtrip")
    path = tmp_path / "results.csv"
    save_records(records, path)
    assert load_records(path) == records
    summary = summarize(records).iloc[0]
    assert summary.n_attacked == 1 and summary.n_targeted == 3
    assert summary.n_questions == 4
    assert summary.n_poisoned_answers == sum(r["attack_success"] for r in records)


def test_wilson_empty_and_all_success():
    assert metrics.wilson_interval(0, 0) == (None, None)
    lo, hi = metrics.wilson_interval(10, 10)
    assert 0 < lo < hi <= 1


@pytest.mark.parametrize("size,overlap", [(0, 0), (-1, 0), (4, -1), (4, 4)])
def test_invalid_chunk_parameters(size, overlap):
    from src.preprocessing.chunking import chunk_text
    with pytest.raises(ValueError):
        chunk_text("some text", size, overlap)


def test_invalid_config_rejected(offline_config):
    offline_config.retrieval.candidate_k = 1
    with pytest.raises(ValueError, match="candidate_k"):
        offline_config.validate()


def test_unknown_reranker_does_not_fallback(offline_config):
    from src.defenses.reranker import get_reranker
    offline_config.reranking.backend = "typo"
    with pytest.raises(ValueError):
        get_reranker(offline_config)
