"""Deterministic chunking.

The shipped chunks.csv was already chunked by hand to this same target
(~400 tokens, ~75 overlap) when the dataset was built. This module exists
so that (a) the chunking logic is testable and deterministic per section 9,
and (b) growing the corpus later (more raw documents) can be re-chunked
automatically with the exact same, auditable algorithm — rather than by
hand — using the values from config.yaml.

"Tokens" here means whitespace-split words, which keeps the module
dependency-free (no tokenizer download needed) while still being a
reasonable, deterministic proxy for the ~400-token target described in the
dataset spec.
"""
from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class Chunk:
    chunk_index: int
    text: str


def chunk_text(text: str, chunk_size_tokens: int, chunk_overlap_tokens: int) -> list[Chunk]:
    """Split `text` into overlapping chunks of ~chunk_size_tokens words.

    Deterministic: same input + same config always produces the same
    output, which section 9 explicitly requires (attack and defense metrics
    would be meaningless if chunk boundaries moved between runs).
    """
    if chunk_size_tokens <= 0 or chunk_overlap_tokens < 0:
        raise ValueError("chunk size must be positive and overlap nonnegative")
    if chunk_overlap_tokens >= chunk_size_tokens:
        raise ValueError("chunk_overlap_tokens must be smaller than chunk_size_tokens")

    words = text.split()
    if not words:
        return []

    step = chunk_size_tokens - chunk_overlap_tokens
    chunks: list[Chunk] = []
    start = 0
    index = 1
    while start < len(words):
        window = words[start : start + chunk_size_tokens]
        chunks.append(Chunk(chunk_index=index, text=" ".join(window)))
        if start + chunk_size_tokens >= len(words):
            break
        start += step
        index += 1
    return chunks
