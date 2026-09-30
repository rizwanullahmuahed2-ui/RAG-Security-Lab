"""Filtering-defense tests (spec section 31): untrusted records excluded per policy."""
from __future__ import annotations

from src.defenses.source_filter import SourceFilter
from src.retrieval.retriever import RetrievedChunk


def _chunk(cid: str, trust: str, verif: str) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=cid, document_id="DOC-X", text="text", title="t", source="s",
        similarity_score=0.9, rank=1, trust_level=trust, verification_status=verif,
    )


def test_allows_high_trust_verified():
    f = SourceFilter(allowed_trust_levels=["high", "medium"], allowed_verification_statuses=["verified"])
    assert f.is_allowed("high", "verified") is True


def test_excludes_untrusted_unverified():
    f = SourceFilter(allowed_trust_levels=["high", "medium"], allowed_verification_statuses=["verified"])
    assert f.is_allowed("untrusted", "unverified") is False


def test_excludes_low_trust_even_if_verified():
    f = SourceFilter(allowed_trust_levels=["high", "medium"], allowed_verification_statuses=["verified"])
    assert f.is_allowed("low", "verified") is False


def test_filter_chunks_removes_only_disallowed_entries():
    f = SourceFilter(allowed_trust_levels=["high", "medium"], allowed_verification_statuses=["verified"])
    candidates = [
        _chunk("good-1", "high", "verified"),
        _chunk("poison-1", "untrusted", "unverified"),
        _chunk("good-2", "medium", "verified"),
        _chunk("poison-2", "untrusted", "unverified"),
    ]
    kept = f.filter_chunks(candidates)
    assert [c.chunk_id for c in kept] == ["good-1", "good-2"]


def test_filter_chunks_on_empty_list():
    f = SourceFilter(allowed_trust_levels=["high"], allowed_verification_statuses=["verified"])
    assert f.filter_chunks([]) == []
