"""Vector store tests (spec section 31): insertion and retrieval."""
from __future__ import annotations

from src.vectorstore.chroma_store import ChromaVectorStore
from src.vectorstore.indexer import index_chunks


def test_insert_and_retrieve(tiny_chunks, embedder, store):
    index_chunks(tiny_chunks, embedder, store, collection_name="tst1")
    assert store.count("tst1") == len(tiny_chunks)

    query_vec = embedder.encode_one("What is the capital of Afghanistan?")
    hits = store.query("tst1", query_vec, top_k=3)
    assert len(hits) == 3
    # The Kabul/capital chunk should be the top hit for a capital-city query.
    assert hits[0]["chunk_id"] == "CHK-DOC-1"
    # Ranks are 1-indexed and increasing.
    assert [h["rank"] for h in hits] == [1, 2, 3]


def test_query_on_empty_collection_returns_no_hits(embedder, store):
    store.create_collection("empty")
    query_vec = embedder.encode_one("anything")
    assert store.query("empty", query_vec, top_k=5) == []


def test_reset_collection_clears_previous_contents(tiny_chunks, embedder, store):
    index_chunks(tiny_chunks, embedder, store, collection_name="tst2")
    assert store.count("tst2") == len(tiny_chunks)
    index_chunks(tiny_chunks.iloc[:2], embedder, store, collection_name="tst2", reset=True)
    assert store.count("tst2") == 2


def test_get_documents_returns_metadata(tiny_chunks, embedder, store):
    index_chunks(tiny_chunks, embedder, store, collection_name="tst3")
    docs = store.get_documents("tst3", ["CHK-DOC-1"])
    assert len(docs) == 1
    assert docs[0]["trust_level"] == "high"
    assert docs[0]["verification_status"] == "verified"
