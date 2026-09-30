"""Document/source filtering defense (spec section 23).

Deliberately NOT a learned poison detector — a simple, transparent
metadata policy, exactly as the spec asks for: "Do not pretend this is a
sophisticated AI-based poison detector. The experiment is specifically
testing whether this simple metadata-based defense can reduce attack
impact."

Known limitation (worth stating explicitly, not hiding): this policy
trusts the `trust_level` / `verification_status` metadata fields as given.
In this dataset that's a safe assumption, because poisoned records are
constructed with trust_level='untrusted' by the data pipeline itself,
not self-declared by an adversary who controls the vector store. A more
adaptive real-world attacker who could write directly to a KB record's
metadata (rather than just its text) could try to mark their own passage
"trusted" and evade this filter — that failure mode is out of scope for
this simple defense and should be called out in the writeup, not glossed
over.
"""
from __future__ import annotations

from src.retrieval.retriever import RetrievedChunk
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


class SourceFilter:
    def __init__(self, allowed_trust_levels: list[str], allowed_verification_statuses: list[str]):
        self._allowed_trust = set(allowed_trust_levels)
        self._allowed_verification = set(allowed_verification_statuses)

    def is_allowed(self, trust_level: str, verification_status: str) -> bool:
        return trust_level in self._allowed_trust and verification_status in self._allowed_verification

    def where_clause(self) -> dict:
        return {"$and": [
            {"trust_level": {"$in": sorted(self._allowed_trust)}},
            {"verification_status": {"$in": sorted(self._allowed_verification)}},
        ]}

    def filter_chunks(self, candidates: list[RetrievedChunk]) -> list[RetrievedChunk]:
        return [c for c in candidates if self.is_allowed(c.trust_level, c.verification_status)]


def get_source_filter(config) -> SourceFilter:
    return SourceFilter(
        allowed_trust_levels=config.filtering.allowed_trust_levels,
        allowed_verification_statuses=config.filtering.allowed_verification_statuses,
    )
