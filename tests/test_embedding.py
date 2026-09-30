"""Embedding-layer tests (spec section 31): output dimensions."""
from __future__ import annotations

import numpy as np

from src.embeddings.embedding_service import HashingEmbeddingService


def test_encode_returns_correct_shape():
    embedder = HashingEmbeddingService(dimension=128)
    vectors = embedder.encode(["Kabul is the capital.", "Herat is a province."])
    assert vectors.shape == (2, 128)
    assert vectors.dtype == np.float32


def test_encode_empty_batch_returns_empty_array():
    embedder = HashingEmbeddingService(dimension=128)
    vectors = embedder.encode([])
    assert vectors.shape == (0, 128)


def test_encode_is_deterministic():
    embedder = HashingEmbeddingService(dimension=128)
    v1 = embedder.encode_one("Kabul is the capital of Afghanistan.")
    v2 = embedder.encode_one("Kabul is the capital of Afghanistan.")
    np.testing.assert_array_equal(v1, v2)


def test_encode_normalizes_to_unit_length():
    embedder = HashingEmbeddingService(dimension=128)
    vec = embedder.encode_one("some non-empty text with several distinct tokens")
    assert abs(np.linalg.norm(vec) - 1.0) < 1e-5


def test_similar_texts_score_higher_than_dissimilar():
    embedder = HashingEmbeddingService(dimension=256)
    query = embedder.encode_one("What is the capital of Afghanistan?")
    similar = embedder.encode_one("Kabul is the capital of Afghanistan.")
    dissimilar = embedder.encode_one("The Ministry of Higher Education oversees universities.")
    assert float(query @ similar) > float(query @ dissimilar)
