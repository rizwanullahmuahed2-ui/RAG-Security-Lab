"""Reranking defense (spec section 22).

Same fallback pattern as the embedding layer: a real cross-encoder model
(`CrossEncoderReranker`) needs a model download; `LexicalOverlapReranker` is
a deterministic, dependency-light fallback (scikit-learn TF-IDF + cosine
similarity, computed on the fly with no network access) used automatically
if the cross-encoder can't be loaded, so the reranking-defense experiment
can still run end-to-end offline.

Both record original rank/similarity alongside the reranked
rank/score, per spec: "The reranker must record: original rank, reranked
rank, original similarity, reranking score."
"""
from __future__ import annotations

import abc
import dataclasses

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from src.retrieval.retriever import RetrievedChunk
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


@dataclasses.dataclass
class RerankedChunk:
    chunk_id: str
    document_id: str
    text: str
    title: str
    source: str
    trust_level: str
    verification_status: str
    original_rank: int
    original_similarity: float
    reranked_rank: int
    rerank_score: float
    source_url: str = ""


class Reranker(abc.ABC):
    @property
    @abc.abstractmethod
    def backend_name(self) -> str: ...

    @abc.abstractmethod
    def rerank(self, query: str, candidates: list[RetrievedChunk], top_k: int) -> list[RerankedChunk]: ...


class CrossEncoderReranker(Reranker):
    def __init__(self, model_name: str):
        from sentence_transformers import CrossEncoder  # deferred import
        self._model_name = model_name
        self._model = CrossEncoder(model_name)

    @property
    def backend_name(self) -> str:
        return f"cross_encoder:{self._model_name}"

    def rerank(self, query: str, candidates: list[RetrievedChunk], top_k: int) -> list[RerankedChunk]:
        if not candidates:
            return []
        pairs = [(query, c.text) for c in candidates]
        scores = self._model.predict(pairs)
        order = sorted(range(len(candidates)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [
            RerankedChunk(
                chunk_id=candidates[i].chunk_id, document_id=candidates[i].document_id,
                text=candidates[i].text, title=candidates[i].title, source=candidates[i].source,
                trust_level=candidates[i].trust_level, verification_status=candidates[i].verification_status,
                original_rank=candidates[i].rank, original_similarity=candidates[i].similarity_score,
                reranked_rank=new_rank, rerank_score=float(scores[i]),
                source_url=candidates[i].source_url,
            )
            for new_rank, i in enumerate(order, start=1)
        ]


class LexicalOverlapReranker(Reranker):
    """Deterministic, offline fallback: TF-IDF cosine similarity between the
    query and each candidate's text, fit fresh on (query + candidates) each
    call — no pretrained model, no network access."""

    @property
    def backend_name(self) -> str:
        return "lexical_overlap_tfidf"

    def rerank(self, query: str, candidates: list[RetrievedChunk], top_k: int) -> list[RerankedChunk]:
        if not candidates:
            return []
        corpus = [query] + [c.text for c in candidates]
        vectorizer = TfidfVectorizer(stop_words="english")
        try:
            matrix = vectorizer.fit_transform(corpus)
            query_vec, doc_vecs = matrix[0:1], matrix[1:]
            scores = cosine_similarity(query_vec, doc_vecs)[0]
        except ValueError as exc:
            if "empty vocabulary" not in str(exc):
                raise
            scores = np.zeros(len(candidates))
        order = sorted(range(len(candidates)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [
            RerankedChunk(
                chunk_id=candidates[i].chunk_id, document_id=candidates[i].document_id,
                text=candidates[i].text, title=candidates[i].title, source=candidates[i].source,
                trust_level=candidates[i].trust_level, verification_status=candidates[i].verification_status,
                original_rank=candidates[i].rank, original_similarity=candidates[i].similarity_score,
                reranked_rank=new_rank, rerank_score=float(scores[i]),
                source_url=candidates[i].source_url,
            )
            for new_rank, i in enumerate(order, start=1)
        ]


def get_reranker(config) -> Reranker:
    if config.reranking.backend == "cross_encoder":
        try:
            reranker = CrossEncoderReranker(config.reranking.model)
            logger.info("Reranking backend: %s", reranker.backend_name)
            return reranker
        except Exception as exc:  # noqa: BLE001 - any load failure -> fallback
            if not getattr(config, "allow_fallback", False):
                raise RuntimeError("Reranker model could not load; fallback is disabled") from exc
            logger.warning(
                "Could not load cross-encoder model '%s' (%s: %s). Falling back to '%s'. "
                "Results with the fallback reranker are NOT equivalent to a real "
                "cross-encoder run and should not be reported as the primary result.",
                config.reranking.model, type(exc).__name__, exc, config.reranking.fallback_backend,
            )
    if config.reranking.backend != "lexical_overlap" and not (
        config.reranking.backend == "cross_encoder" and config.reranking.fallback_backend == "lexical_overlap"
    ):
        raise ValueError("Unknown or disabled reranker backend/fallback")
    reranker = LexicalOverlapReranker()
    logger.info("Reranking backend: %s", reranker.backend_name)
    return reranker
