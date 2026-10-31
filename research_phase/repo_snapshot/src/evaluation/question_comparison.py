"""Interactive dose tests, separate from the fixed benchmark attack distribution."""
from __future__ import annotations
from uuid import uuid4
import pandas as pd
from src.attacks.poison_generator import create_poisoned_kb
from src.evaluation.metrics import score_targeted_answer
from src.generation.rag_pipeline import RagPipeline
from src.retrieval.retriever import Retriever
from src.vectorstore.indexer import index_chunks

SPREAD = "Benchmark: attacks across different questions"
REPEATED = "Stress test: repeat attack on this question"
TARGETED = "Targeted test: attack the selected question"


def repeated_poison_pool(pool: pd.DataFrame, question_id: str, count: int) -> pd.DataFrame:
    """Exact copies measure saturation, not independent corroborating sources."""
    if type(count) is not int or count < 0:
        raise ValueError("Repeat count must be a nonnegative integer")
    matches = pool.loc[pool.target_question_id == question_id]
    if len(matches) != 1:
        raise ValueError("Choose a benchmark question with exactly one assigned attack")
    original = matches.iloc[0].to_dict()
    rows = [{**original, "poison_id": f"REPEAT-{original['poison_id']}-{i:04d}",
             "source_status": "attacker_generated", "trust_level": "untrusted",
             "verification_status": "unverified"} for i in range(1, count + 1)]
    return pd.DataFrame(rows, columns=pool.columns)


def answer_at_level(*, chunks, poisons, question, custom_query, count, seed, mode, defense,
                    config, embedder, llm, reranker, source_filter, store):
    """Return a real pipeline answer and measured exposure. Never alter the answer."""
    if mode not in (SPREAD, REPEATED, TARGETED):
        raise ValueError("Unknown poisoning mode")
    if mode in (REPEATED, TARGETED) and custom_query.strip():
        raise ValueError("Repeated-attack mode requires the selected benchmark question, not a custom query")
    if defense not in {"none", "reranking", "source_filtering", "reranking+source_filtering"}:
        raise ValueError("Unknown defense")
    qid = question["question_id"]
    pool = repeated_poison_pool(poisons, qid, count) if mode in (REPEATED, TARGETED) else poisons
    combined, injected = create_poisoned_kb(chunks, pool, count, seed)
    collection = f"interactive_{uuid4().hex}"
    try:
        index_chunks(combined, embedder, store, collection)
        pipeline = RagPipeline(Retriever(embedder, store, collection), llm,
            config.llm_system_prompt, config.llm_temperature, config.llm_max_tokens,
            config.retrieval.candidate_k, config.retrieval.top_k, reranker, source_filter,
            rerank_k=config.reranking.final_k)
        result = pipeline.answer(custom_query.strip() or question["question"],
            apply_filtering="source_filtering" in defense, apply_reranking="reranking" in defense)
    finally:
        store.delete_collection(collection)
    hits = {row["chunk_id"] for row in result.retrieved_documents}
    poison_ids = set(injected.poison_id)
    target_ids = set(injected.loc[injected.target_question_id == qid, "poison_id"])
    assigned = poisons.loc[poisons.target_question_id == qid]
    false_info = assigned.iloc[0].attacker_false_information if len(assigned) else ""
    targeted = mode == TARGETED or str(question["targeted_for_attack"]).lower() in {"true", "1", "yes"}
    verdict = None if custom_query.strip() else score_targeted_answer(result.answer, question["ground_truth"],
        false_info, targeted, bool(hits & target_ids))
    return dict(result=result, verdict=verdict, gold=question["ground_truth"], poison_ids=poison_ids,
        target_injected=bool(target_ids), target_retrieved=bool(hits & target_ids),
        false_info=false_info, attack_targeted=targeted,
        target_copies_injected=len(target_ids), target_copies_retrieved=len(hits & target_ids),
        poison_retrieved=len(hits & poison_ids), count=count, seed=seed, mode=mode, defense=defense,
        caption=f"{count} passages · {defense} · seed {seed} · {mode}",
        backends=f"{embedder.backend_name} / {reranker.backend_name} / {llm.backend_name}")


def comparison_row(saved):
    verdict = saved["verdict"] or {}
    return {"Injected passages": saved["count"], "Copies attacking this question": saved["target_copies_injected"],
            "Target copies in context": saved["target_copies_retrieved"],
            "All poisons in context": saved["poison_retrieved"],
            "Context passages": len(saved["result"].retrieved_documents),
            "Answer match": verdict.get("answer_correct"), "Attack success": verdict.get("attack_success"),
            "Defense": saved['defense'],
            "Poison share of context (%)": round(100 * saved['poison_retrieved'] / max(1,len(saved['result'].retrieved_documents)),1),
            "Answer": saved["result"].answer}
