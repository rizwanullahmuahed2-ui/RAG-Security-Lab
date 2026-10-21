"""End-to-end test (spec section 32): the complete pipeline —

    Document -> Chunk -> Embed -> ChromaDB -> Retrieve -> Inject Poison
    -> Retrieve Again -> Generate Answer -> Evaluate

— on the tiny 10-document / 4-question / 3-poison fixture set, entirely
offline (hashing embedder + lexical-overlap reranker + extractive LLM
stub). This is the smallest possible run that still exercises every
pipeline stage for real.
"""
from __future__ import annotations

import pytest

from src.attacks.poison_generator import create_poisoned_kb
from src.defenses.source_filter import SourceFilter
from src.evaluation.evaluator import run_condition
from src.vectorstore.indexer import index_chunks
from src.vectorstore.exact_store import ExactVectorStore


def test_clean_retrieval_finds_the_right_chunk(tiny_chunks, embedder, store):
    index_chunks(tiny_chunks, embedder, store, collection_name="e2e-clean")
    query_vec = embedder.encode_one("In what year was Da Afghanistan Bank established?")
    hits = store.query("e2e-clean", query_vec, top_k=3)
    assert hits[0]["chunk_id"] == "CHK-DOC-5"  # the Da Afghanistan Bank chunk


def test_poisoned_kb_can_surface_the_poison_at_retrieval(tiny_chunks, tiny_poison_pool, embedder, store):
    combined, injected = create_poisoned_kb(tiny_chunks, tiny_poison_pool, poison_count=3, random_seed=42)
    index_chunks(combined, embedder, store, collection_name="e2e-poisoned")
    assert store.count("e2e-poisoned") == len(tiny_chunks) + 3

    query_vec = embedder.encode_one("What is the capital of Afghanistan?")
    hits = store.query("e2e-poisoned", query_vec, top_k=5)
    hit_ids = [h["chunk_id"] for h in hits]
    # Both the legitimate chunk and the poisoned passage targeting this
    # exact question should be retrievable candidates.
    assert "CHK-DOC-1" in hit_ids
    assert "TPOI-1" in hit_ids


def test_full_condition_run_produces_one_record_per_question(
    tiny_chunks, tiny_poison_pool, tiny_questions, embedder, store, reranker, llm, offline_config,
):
    source_filter = SourceFilter(
        allowed_trust_levels=offline_config.filtering.allowed_trust_levels,
        allowed_verification_statuses=offline_config.filtering.allowed_verification_statuses,
    )
    records = run_condition(
        clean_chunks=tiny_chunks, poison_pool=tiny_poison_pool, questions=tiny_questions,
        embedder=embedder, store=store, reranker=reranker, source_filter=source_filter,
        llm=llm, config=offline_config, poison_count=3,
        apply_reranking=False, apply_filtering=False, collection_name="e2e-full",
    )
    assert len(records) == len(tiny_questions)
    for r in records:
        # offline_config uses toy poisoning levels [0,1,2,3], not the real
        # {0,5,10,20} labels, so an unmapped count falls back to "KB-<n>".
        assert r["condition"] == "KB-3"
        assert isinstance(r["poison_retrieved"], bool)
        assert isinstance(r["attack_success"], bool)
        # attack_success can only be True for targeted questions.
        if not r["targeted_for_attack"]:
            assert r["attack_success"] is False


def test_source_filtering_removes_poison_before_generation(
    tiny_chunks, tiny_poison_pool, tiny_questions, embedder, store, reranker, llm, offline_config,
):
    source_filter = SourceFilter(allowed_trust_levels=["high", "medium"], allowed_verification_statuses=["verified"])
    records = run_condition(
        clean_chunks=tiny_chunks, poison_pool=tiny_poison_pool, questions=tiny_questions,
        embedder=embedder, store=store, reranker=reranker, source_filter=source_filter,
        llm=llm, config=offline_config, poison_count=3,
        apply_reranking=True, apply_filtering=True, collection_name="e2e-filtered",
    )
    # With filtering applied, no poisoned chunk (all trust_level="untrusted")
    # should ever appear in the final retrieved set.
    assert all(r["poison_retrieved"] is False for r in records)
    assert all(r["attack_success"] is False for r in records)


@pytest.mark.parametrize("apply_reranking", [False, True])
def test_evidence_keeps_source_urls_through_generation(
        tiny_chunks, tiny_poison_pool, tiny_questions, embedder, reranker,
        llm, source_filter, offline_config, apply_reranking):
    """Exports must retain source links for clean evidence and none for poison."""
    chunks = tiny_chunks.assign(source_url=lambda frame: "https://example.org/" + frame.document_id)
    records = run_condition(
        clean_chunks=chunks, poison_pool=tiny_poison_pool, questions=tiny_questions,
        embedder=embedder, store=ExactVectorStore(), reranker=reranker,
        source_filter=source_filter, llm=llm, config=offline_config, poison_count=3,
        apply_reranking=apply_reranking, apply_filtering=False, collection_name="e2e-provenance",
    )
    evidence = [passage for record in records for passage in record["evidence"]]
    expected = dict(zip(chunks.chunk_id, chunks.source_url))
    expected.update(dict.fromkeys(tiny_poison_pool.poison_id, ""))
    assert any(passage["source_url"] for passage in evidence)
    assert any(passage["chunk_id"] in set(tiny_poison_pool.poison_id) for passage in evidence)
    assert all(passage["source_url"] == expected[passage["chunk_id"]] for passage in evidence)
