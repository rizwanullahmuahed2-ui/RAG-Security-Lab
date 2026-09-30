"""Thin, explicit wrapper over ChromaDB (spec section 11).

Design choice: we ALWAYS pass precomputed embedding vectors to Chroma
ourselves (`collection.add(embeddings=...)` / `collection.query(query_embeddings=...)`)
rather than handing Chroma raw text and letting it call its own default
embedding function. This keeps the embedding backend fully under our
control (see src/embeddings/embedding_service.py) and means ChromaDB itself
never needs network access, regardless of which embedding backend is
active.
"""
from __future__ import annotations

from typing import Any

import chromadb
import numpy as np
from uuid import uuid4
from chromadb.errors import NotFoundError

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


class ChromaVectorStore:
    def __init__(self, persist_directory: str | None = None):
        """`persist_directory=None` uses an ephemeral in-memory client
        (used by tests and the minimal prototype so repeated runs don't
        accumulate stale on-disk state)."""
        if persist_directory:
            self._client = chromadb.PersistentClient(path=persist_directory)
        else:
            self._client = chromadb.EphemeralClient()
        self._namespace = "" if persist_directory else f"session_{uuid4().hex}_"

    def create_collection(self, name: str):
        return self._client.get_or_create_collection(name=self._namespace + name, metadata={"hnsw:space": "cosine"}, embedding_function=None)

    def delete_collection(self, name: str) -> None:
        try:
            self._client.delete_collection(name=self._namespace + name)
        except NotFoundError:
            pass

    def reset_collection(self, name: str):
        self.delete_collection(name)
        return self.create_collection(name)

    def add_documents(
        self,
        collection_name: str,
        ids: list[str],
        embeddings: np.ndarray,
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        if not ids:
            return
        collection = self.create_collection(collection_name)
        batch_size = self._client.get_max_batch_size()
        for start in range(0, len(ids), batch_size):
            end = start + batch_size
            collection.add(ids=ids[start:end], embeddings=embeddings[start:end].tolist(),
                           documents=documents[start:end], metadatas=metadatas[start:end])
        logger.info("Added %d records to collection '%s'", len(ids), collection_name)

    def query(
        self, collection_name: str, query_embedding: np.ndarray, top_k: int, where: dict | None = None
    ) -> list[dict[str, Any]]:
        collection = self.create_collection(collection_name)
        count = collection.count()
        if count == 0:
            return []
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        result = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"],
            where=where,
        )
        hits: list[dict[str, Any]] = []
        for rank, (chunk_id, doc, meta, distance) in enumerate(
            zip(result["ids"][0], result["documents"][0], result["metadatas"][0], result["distances"][0]),
            start=1,
        ):
            # Chroma's "cosine" space returns a distance in [0, 2]; convert to a
            # similarity score in roughly [-1, 1] (1 = identical) for readability.
            similarity = 1.0 - distance
            hits.append({
                "chunk_id": chunk_id,
                "text": doc,
                "similarity_score": similarity,
                "rank": rank,
                **meta,
            })
        return hits

    def get_documents(self, collection_name: str, ids: list[str]) -> list[dict[str, Any]]:
        collection = self.create_collection(collection_name)
        result = collection.get(ids=ids, include=["documents", "metadatas"])
        return [
            {"chunk_id": cid, "text": doc, **meta}
            for cid, doc, meta in zip(result["ids"], result["documents"], result["metadatas"])
        ]

    def count(self, collection_name: str) -> int:
        return self.create_collection(collection_name).count()
