"""Baseline similarity-based retriever (spec section 12)."""
from __future__ import annotations

import dataclasses
from typing import Any

from src.embeddings.embedding_service import EmbeddingService
from src.vectorstore.chroma_store import ChromaVectorStore


@dataclasses.dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    text: str
    title: str
    source: str
    similarity_score: float
    rank: int
    trust_level: str
    verification_status: str

    @classmethod
    def from_hit(cls, hit: dict[str, Any]) -> "RetrievedChunk":
        return cls(
            chunk_id=hit["chunk_id"],
            document_id=hit.get("document_id", ""),
            text=hit["text"],
            title=hit.get("title", ""),
            source=hit.get("source", ""),
            similarity_score=hit["similarity_score"],
            rank=hit["rank"],
            trust_level=hit.get("trust_level", ""),
            verification_status=hit.get("verification_status", ""),
        )


class Retriever:
    def __init__(self, embedder: EmbeddingService, store: ChromaVectorStore, collection_name: str):
        self._embedder = embedder
        self._store = store
        self._collection_name = collection_name

    def retrieve(self, query: str, top_k: int, where: dict | None = None) -> list[RetrievedChunk]:
        query_vec = self._embedder.encode_one(query)
        hits = self._store.query(self._collection_name, query_vec, top_k, where=where)
        return [RetrievedChunk.from_hit(h) for h in hits]
