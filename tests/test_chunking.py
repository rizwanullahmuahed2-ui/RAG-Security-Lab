"""Chunking tests (spec section 31): deterministic output."""
from __future__ import annotations

import pytest

from src.preprocessing.chunking import chunk_text


def test_chunking_is_deterministic():
    text = " ".join(f"word{i}" for i in range(1000))
    run1 = chunk_text(text, chunk_size_tokens=400, chunk_overlap_tokens=75)
    run2 = chunk_text(text, chunk_size_tokens=400, chunk_overlap_tokens=75)
    assert run1 == run2


def test_chunking_respects_overlap():
    text = " ".join(f"word{i}" for i in range(1000))
    chunks = chunk_text(text, chunk_size_tokens=400, chunk_overlap_tokens=75)
    assert len(chunks) >= 2
    first_words = chunks[0].text.split()
    second_words = chunks[1].text.split()
    # The last 75 words of chunk 1 should equal the first 75 words of chunk 2.
    assert first_words[-75:] == second_words[:75]


def test_chunking_short_text_produces_one_chunk():
    text = "Kabul is the capital of Afghanistan."
    chunks = chunk_text(text, chunk_size_tokens=400, chunk_overlap_tokens=75)
    assert len(chunks) == 1
    assert chunks[0].text == text


def test_chunking_empty_text_produces_no_chunks():
    assert chunk_text("", chunk_size_tokens=400, chunk_overlap_tokens=75) == []


def test_chunking_rejects_overlap_ge_size():
    with pytest.raises(ValueError):
        chunk_text("some text", chunk_size_tokens=100, chunk_overlap_tokens=100)
