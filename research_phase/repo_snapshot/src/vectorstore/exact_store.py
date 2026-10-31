"""Deterministic cosine search for benchmark-sized corpora.

Unlike an approximate ANN index, every eligible vector is scored and ties are
broken by chunk ID. Query cost is linear in corpus size; use Chroma for larger KBs.
"""
from __future__ import annotations
from typing import Any
import numpy as np


class ExactVectorStore:
    def __init__(self):
        self._collections: dict[str, dict[str, dict]] = {}

    def create_collection(self, name: str):
        return self._collections.setdefault(name, {})

    def delete_collection(self, name: str):
        self._collections.pop(name, None)

    def reset_collection(self, name: str):
        self._collections[name] = {}
        return self._collections[name]

    def add_documents(self, collection_name: str, ids: list[str], embeddings: np.ndarray,
                      documents: list[str], metadatas: list[dict[str, Any]]):
        if not (len(ids) == len(embeddings) == len(documents) == len(metadatas)):
            raise ValueError("IDs, vectors, documents and metadata must have equal lengths")
        collection = self.create_collection(collection_name)
        if len(set(ids)) != len(ids) or set(ids) & set(collection):
            raise ValueError("Duplicate vector IDs")
        vectors = np.asarray(embeddings, dtype=np.float64)
        if vectors.ndim != 2 or not np.isfinite(vectors).all():
            raise ValueError("Embeddings must be a finite 2D array")
        if collection and len(next(iter(collection.values()))["vector"]) != vectors.shape[1]:
            raise ValueError("Embedding dimension mismatch")
        for cid, vector, document, metadata in zip(ids, vectors, documents, metadatas):
            norm = np.linalg.norm(vector)
            collection[cid] = {"vector": vector / norm if norm else vector.copy(),
                               "text": document, "metadata": dict(metadata)}

    @staticmethod
    def _matches(metadata: dict, where: dict | None) -> bool:
        if where is None:
            return True
        if "$and" in where:
            return all(ExactVectorStore._matches(metadata, predicate) for predicate in where["$and"])
        for key, value in where.items():
            if not isinstance(value, dict) or set(value) != {"$in"}:
                raise ValueError("Exact store supports conjunctions of metadata $in predicates")
            if metadata.get(key) not in value["$in"]:
                return False
        return True

    def query(self, collection_name: str, query_embedding: np.ndarray, top_k: int, where=None):
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        query = np.asarray(query_embedding, dtype=np.float64)
        if query.ndim != 1 or not np.isfinite(query).all():
            raise ValueError("Query must be a finite vector")
        norm = np.linalg.norm(query)
        if norm:
            query = query / norm
        eligible = [(cid, row) for cid, row in self.create_collection(collection_name).items()
                    if self._matches(row["metadata"], where)]
        if not eligible:
            return []
        # Per-vector dot products avoid backend-dependent matrix scheduling/tie drift.
        scored = [(float(np.dot(query, row["vector"])), cid, row) for cid, row in eligible]
        scored.sort(key=lambda entry: (-round(entry[0], 12), entry[1]))
        return [{**row["metadata"], "chunk_id": cid, "text": row["text"],
                 "similarity_score": score, "rank": rank}
                for rank, (score, cid, row) in enumerate(scored[:top_k], 1)]

    def get_documents(self, collection_name: str, ids: list[str]):
        collection = self.create_collection(collection_name)
        return [{**collection[cid]["metadata"], "chunk_id": cid, "text": collection[cid]["text"]}
                for cid in ids if cid in collection]

    def count(self, collection_name: str):
        return len(self.create_collection(collection_name))


def get_vector_store(config):
    if config.vector_db.backend == "exact":
        return ExactVectorStore()
    if config.vector_db.backend == "chroma":
        from src.vectorstore.chroma_store import ChromaVectorStore
        return ChromaVectorStore()
    raise ValueError("Unknown vector database backend")
