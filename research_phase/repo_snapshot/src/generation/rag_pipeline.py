"""End-to-end RAG pipeline (spec section 13).

    Question -> Query Embedding -> Vector Retrieval -> [Source Filtering]
             -> [Reranking] -> Context Construction -> LLM -> Final Answer

Filtering is applied to the retrieval candidate pool BEFORE reranking
(Configuration D = C + filtering: filtering narrows the candidate set,
then reranking orders what's left). Returns the full retrieved-evidence
list alongside the answer — spec section 13 is explicit that the security
evaluation needs the evidence, not just the final answer text.
"""
from __future__ import annotations

import dataclasses
from typing import Any

from src.defenses.reranker import Reranker, RerankedChunk
from src.defenses.source_filter import SourceFilter
from src.generation.llm_interface import LLMInterface
from src.retrieval.retriever import Retriever, RetrievedChunk


@dataclasses.dataclass
class RagResult:
    query: str
    retrieved_documents: list[dict[str, Any]]
    context: str
    answer: str


def _build_context(chunks: list[RetrievedChunk] | list[RerankedChunk]) -> str:
    return "\n\n".join(c.text for c in chunks)


def _to_dict(c: RetrievedChunk | RerankedChunk) -> dict[str, Any]:
    if isinstance(c, RerankedChunk):
        return {
            "chunk_id": c.chunk_id, "document_id": c.document_id, "title": c.title,
            "text": c.text,
            "source": c.source, "source_url": c.source_url, "trust_level": c.trust_level,
            "verification_status": c.verification_status,
            "original_rank": c.original_rank, "original_similarity": c.original_similarity,
            "reranked_rank": c.reranked_rank, "rerank_score": c.rerank_score,
        }
    return {
        "chunk_id": c.chunk_id, "document_id": c.document_id, "title": c.title,
        "text": c.text,
        "source": c.source, "source_url": c.source_url, "trust_level": c.trust_level,
        "verification_status": c.verification_status,
        "original_rank": c.rank, "original_similarity": c.similarity_score,
        "reranked_rank": None, "rerank_score": None,
    }


class RagPipeline:
    def __init__(
        self,
        retriever: Retriever,
        llm: LLMInterface,
        system_prompt: str,
        temperature: float,
        max_tokens: int,
        candidate_k: int,
        top_k: int,
        reranker: Reranker | None = None,
        source_filter: SourceFilter | None = None,
        rerank_k: int | None = None,
    ):
        self._retriever = retriever
        self._llm = llm
        self._system_prompt = system_prompt
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._candidate_k = candidate_k
        self._top_k = top_k
        self._reranker = reranker
        self._source_filter = source_filter
        self._rerank_k = rerank_k if rerank_k is not None else top_k

    def answer(self, query: str, apply_filtering: bool = False, apply_reranking: bool = False) -> RagResult:
        if not query.strip():
            raise ValueError("Question must not be empty")
        if apply_filtering and self._source_filter is None:
            raise ValueError("Filtering requested without a source filter")
        if apply_reranking and self._reranker is None:
            raise ValueError("Reranking requested without a reranker")
        # Filter at retrieval time so untrusted documents cannot exhaust the candidate pool.
        where = self._source_filter.where_clause() if apply_filtering else None
        candidates: list[RetrievedChunk] = self._retriever.retrieve(query, self._candidate_k, where=where)

        if apply_filtering and self._source_filter is not None:
            candidates = self._source_filter.filter_chunks(candidates)

        if apply_reranking and self._reranker is not None:
            final_chunks: list[Any] = self._reranker.rerank(query, candidates, self._rerank_k)
        else:
            final_chunks = candidates[: self._top_k]

        context = _build_context(final_chunks)
        answer = self._llm.generate(
            query=query, context=context, system_prompt=self._system_prompt,
            temperature=self._temperature, max_tokens=self._max_tokens,
        )
        return RagResult(
            query=query,
            retrieved_documents=[_to_dict(c) for c in final_chunks],
            context=context,
            answer=answer,
        )
