"""Runs the full experiment grid: every poisoning level x every defense
configuration, evaluated over every question (spec sections 24, 26, 28).

Configurations A-D map onto (poison_count, apply_reranking, apply_filtering):
    A. Clean RAG                                -> count=0,  rerank=F, filter=F
    B. Poisoned RAG                             -> count>0,  rerank=F, filter=F
    C. Poisoned RAG + Reranking                 -> count>0,  rerank=T, filter=F
    D. Poisoned RAG + Reranking + Filtering     -> count>0,  rerank=T, filter=T

The same three defense variants (none / reranking / reranking+filtering) are
ALSO run at poison_count=0, which is what makes the "does the defense cost
you accuracy on clean data" trade-off question (section 18) answerable —
without that, Figure 4 (Defense Method vs Clean-data Accuracy) would have
nothing to plot.
"""
from __future__ import annotations

from typing import Any
from time import perf_counter

import pandas as pd

from src.attacks.poison_generator import create_poisoned_kb
from src.defenses.reranker import Reranker
from src.defenses.source_filter import SourceFilter
from src.embeddings.embedding_service import EmbeddingService
from src.evaluation import metrics
from src.generation.llm_interface import LLMInterface
from src.generation.rag_pipeline import RagPipeline
from src.retrieval.retriever import Retriever
from src.vectorstore.chroma_store import ChromaVectorStore
from src.vectorstore.indexer import index_chunks
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

_LEVEL_LABEL = {0: "Clean", 5: "Low", 10: "Medium", 20: "High"}
DEFENSE_VARIANTS = [
    ("none", False, False),
    ("reranking", True, False),
    ("source_filtering", False, True),
    ("reranking+source_filtering", True, True),
]


def build_attack_lookup(poison_pool: pd.DataFrame) -> dict[str, str]:
    return dict(zip(poison_pool["attack_id"], poison_pool["attacker_false_information"]))


def run_condition(
    clean_chunks: pd.DataFrame,
    poison_pool: pd.DataFrame,
    questions: pd.DataFrame,
    embedder: EmbeddingService,
    store: ChromaVectorStore,
    reranker: Reranker,
    source_filter: SourceFilter,
    llm: LLMInterface,
    config,
    poison_count: int,
    apply_reranking: bool,
    apply_filtering: bool,
    collection_name: str,
) -> list[dict[str, Any]]:
    combined_chunks, injected_subset = create_poisoned_kb(
        clean_chunks, poison_pool, poison_count, config.poisoning.random_seed
    )
    index_chunks(combined_chunks, embedder, store, collection_name, reset=True)
    poison_ids_in_kb: set[str] = set(injected_subset["poison_id"]) if len(injected_subset) else set()
    target_poison_ids = injected_subset.groupby("target_question_id")["poison_id"].agg(set).to_dict()

    retriever = Retriever(embedder, store, collection_name)
    pipeline = RagPipeline(
        retriever=retriever, llm=llm,
        system_prompt=config.llm_system_prompt, temperature=config.llm_temperature,
        max_tokens=config.llm_max_tokens, candidate_k=config.retrieval.candidate_k,
        top_k=config.retrieval.top_k, reranker=reranker, source_filter=source_filter,
        rerank_k=config.reranking.final_k,
    )
    attack_lookup = build_attack_lookup(poison_pool)

    parts = []
    if apply_reranking:
        parts.append("reranking")
    if apply_filtering:
        parts.append("source_filtering")
    defense_method = "+".join(parts) if parts else "none"
    defense_enabled = bool(parts)
    condition_label = f"KB-{_LEVEL_LABEL.get(poison_count, poison_count)}"

    records: list[dict[str, Any]] = []
    for q in questions.itertuples(index=False):
        started = perf_counter()
        result = pipeline.answer(q.question, apply_filtering=apply_filtering, apply_reranking=apply_reranking)
        retrieved_ids = [d["chunk_id"] for d in result.retrieved_documents]
        retrieved_scores = [
            d["rerank_score"] if d["rerank_score"] is not None else d["original_similarity"]
            for d in result.retrieved_documents
        ]
        poison_hits = [cid for cid in retrieved_ids if cid in poison_ids_in_kb]
        poison_retrieved = len(poison_hits) > 0
        poison_rank = (retrieved_ids.index(poison_hits[0]) + 1) if poison_hits else None
        correct_chunk_retrieved = q.relevant_chunk_id in retrieved_ids
        targeted = str(q.targeted_for_attack).strip().lower() in {"true", "1", "yes"}
        matching_ids = target_poison_ids.get(q.question_id, set())
        target_hits = matching_ids & set(retrieved_ids)
        verdict = metrics.score_targeted_answer(result.answer, q.ground_truth,
                    attack_lookup.get(q.attack_id, ""), targeted, bool(target_hits))
        f1 = metrics.f1_score(result.answer, q.ground_truth)

        # Attack success per spec section 21: poison retrieved AND the
        # answer reflects the attacker's intended false information —
        # NOT the same as "poison retrieved" and NOT the same as "wrong answer".
        records.append({
            "experiment_id": f"EXP-{condition_label}-{defense_method.replace('+', '_')}-{q.question_id}",
            "question_id": q.question_id,
            "condition": condition_label,
            "top_k": config.reranking.final_k if apply_reranking else config.retrieval.top_k,
            "poison_count": poison_count,
            "poison_fraction": poison_count / len(combined_chunks),
            "seed": config.poisoning.random_seed,
            "split": getattr(q, "split", "unspecified"),
            "family_id": getattr(q, "family_id", q.relevant_document_id),
            "question": q.question,
            "attack_id": q.attack_id,
            "attack_injected": bool(matching_ids),
            "target_poison_retrieved": bool(target_hits),
            "latency_ms": round((perf_counter() - started) * 1000, 3),
            "embedding_backend": embedder.backend_name,
            "reranker_backend": reranker.backend_name if apply_reranking else "disabled",
            "llm_backend": llm.backend_name,
            "evidence": result.retrieved_documents,
            "retrieved_chunk_ids": retrieved_ids,
            "retrieved_scores": [round(s, 4) for s in retrieved_scores],
            "poison_retrieved": poison_retrieved,
            "poison_rank": poison_rank,
            "poison_count_retrieved": len(poison_hits),
            "correct_chunk_retrieved": correct_chunk_retrieved,
            "generated_answer": result.answer,
            "ground_truth": q.ground_truth,
            **verdict,
            "f1": round(f1, 4),
            "defense_enabled": defense_enabled,
            "defense_method": defense_method,
            "relevant_chunk_id": q.relevant_chunk_id,
            "category": q.category,
            "targeted_for_attack": targeted,
        })
    logger.info(
        "Condition %s / defense=%s: %d questions evaluated (%d poisoned passages in KB)",
        condition_label, defense_method, len(records), poison_count,
    )
    return records


def run_all_experiments(
    documents: pd.DataFrame,
    clean_chunks: pd.DataFrame,
    poison_pool: pd.DataFrame,
    questions: pd.DataFrame,
    embedder: EmbeddingService,
    store: ChromaVectorStore,
    reranker: Reranker,
    source_filter: SourceFilter,
    llm: LLMInterface,
    config,
) -> list[dict[str, Any]]:
    del documents  # not directly needed here; kept for a consistent call signature
    all_records: list[dict[str, Any]] = []
    for count in config.poisoning.counts:
        for _defense_name, rerank_flag, filter_flag in DEFENSE_VARIANTS:
            collection_name = (
                config.vector_db.clean_collection if count == 0
                else f"{config.vector_db.poisoned_collection_prefix}_{count}"
            )
            all_records.extend(run_condition(
                clean_chunks=clean_chunks, poison_pool=poison_pool, questions=questions,
                embedder=embedder, store=store, reranker=reranker, source_filter=source_filter,
                llm=llm, config=config, poison_count=count,
                apply_reranking=rerank_flag, apply_filtering=filter_flag,
                collection_name=collection_name,
            ))
    return all_records


def summarize(records: list[dict[str, Any]]) -> pd.DataFrame:
    """One row per (condition, defense_method) with the section-25 metrics."""
    df = pd.DataFrame(records)
    if df.empty:
        return pd.DataFrame()
    rows = []
    group_columns = ["condition", "defense_method"] + (["seed"] if "seed" in df else [])
    for group_key, group in df.groupby(group_columns, sort=False):
        condition, defense_method = group_key[:2]
        group_records = group.to_dict("records")
        targeted = [r for r in group_records if r["targeted_for_attack"]]
        exposed = [r for r in targeted if r.get("attack_injected", False)]
        accuracy_ci = metrics.wilson_interval(sum(r["answer_correct"] for r in group_records), len(group_records))
        asr_ci = metrics.wilson_interval(sum(r["attack_success"] for r in exposed), len(exposed))
        rows.append({
            "condition": condition,
            "defense_method": defense_method,
            "n_questions": len(group_records),
            "n_targeted": len(targeted),
            "seed": group_records[0].get("seed", 42),
            "poison_count": group_records[0].get("poison_count", 0),
            "n_attacked": len(exposed),
            "n_poisoned_answers": sum(r["attack_success"] for r in targeted),
            "attack_success_rate_injected": metrics.attack_success_rate(exposed) if exposed else None,
            "injected_asr_ci_low": asr_ci[0], "injected_asr_ci_high": asr_ci[1],
            "accuracy_ci_low": accuracy_ci[0], "accuracy_ci_high": accuracy_ci[1],
            "ambiguous_answers": sum(r.get("ambiguous_answer", False) for r in group_records),
            "strict_exact_match": sum(r.get("strict_exact_match", False) for r in group_records) / len(group_records),
            "mean_latency_ms": group["latency_ms"].mean() if "latency_ms" in group else None,
            "recall_at_k": round(metrics.recall_at_k(group_records), 4),
            "mrr": round(metrics.mean_reciprocal_rank(group_records), 4),
            "poison_retrieval_rate": round(metrics.poison_retrieval_rate(targeted), 4) if targeted else None,
            "answer_accuracy": round(metrics.answer_accuracy(group_records), 4),
            "mean_f1": round(metrics.mean_f1(group_records), 4),
            "attack_success_rate": round(metrics.attack_success_rate(targeted), 4) if targeted else None,
        })
    return pd.DataFrame(rows)
