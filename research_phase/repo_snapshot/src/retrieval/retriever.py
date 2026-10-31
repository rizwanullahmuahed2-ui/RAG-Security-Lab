"""Vector retrieval; the versioned offline backend adds lexical sentence ranking.

Offline ranking scans all eligible texts, scores content-word coverage and
proximity, and uses vector similarity to break ties. Metadata filtering still
precedes selection. No question IDs, ground-truth values or attack labels are
available to the scorer. Neural embedding backends retain vector ranking.
"""
from __future__ import annotations

import dataclasses
from typing import Any

from src.embeddings.embedding_service import EmbeddingService
from src.vectorstore.chroma_store import ChromaVectorStore
from src.retrieval.lexical import sentences, sentence_score, content_weights


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
    source_url: str = ""

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
            source_url=hit.get("source_url", ""),
        )


class Retriever:
    def __init__(self, embedder: EmbeddingService, store: ChromaVectorStore, collection_name: str):
        self._embedder = embedder
        self._store = store
        self._collection_name = collection_name

    def retrieve(self, query: str, top_k: int, where: dict | None = None) -> list[RetrievedChunk]:
        query_vec = self._embedder.encode_one(query)
        lexical = self._embedder.backend_name.startswith('hashing-lexical-v2:')
        # Offline corpora are small: score every eligible passage, so hashing
        # collisions cannot exclude evidence before lexical relation matching.
        pool_k = max(top_k, self._store.count(self._collection_name)) if lexical else top_k
        hits = self._store.query(self._collection_name, query_vec, pool_k, where=where)
        if lexical:
            weights=content_weights([hit['text'] for hit in hits])
            def score(hit):
                best=max((sentence_score(query, s, weights) for s in sentences(hit['text'])),default=(0.,0.,0.))
                return (*best, hit['similarity_score'])
            hits.sort(key=score,reverse=True)
            hits=hits[:top_k]
            for rank,hit in enumerate(hits,1):hit['rank']=rank
        return [RetrievedChunk.from_hit(h) for h in hits]
