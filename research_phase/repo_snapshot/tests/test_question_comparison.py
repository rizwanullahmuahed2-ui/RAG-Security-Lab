import pytest
from src.evaluation.question_comparison import REPEATED, repeated_poison_pool, answer_at_level
from src.vectorstore.exact_store import ExactVectorStore


def test_repeat_counts_are_nested_without_forging_sources(tiny_poison_pool):
    low = repeated_poison_pool(tiny_poison_pool, "TQ-1", 10)
    high = repeated_poison_pool(tiny_poison_pool, "TQ-1", 50)
    assert len(low) == 10 and len(high) == 50
    assert set(low.poison_id) < set(high.poison_id)
    assert high.poisoned_text.nunique() == 1
    assert set(high.trust_level) == {"untrusted"}
    assert set(high.target_question_id) == {"TQ-1"}
    assert len(repeated_poison_pool(tiny_poison_pool, "TQ-1", 0)) == 0
    with pytest.raises(ValueError, match="assigned attack"):
        repeated_poison_pool(tiny_poison_pool, "TQ-4", 10)


def test_repeated_attack_retrieval_and_filtering(tiny_chunks, tiny_poison_pool, tiny_questions,
        offline_config, embedder, llm, reranker, source_filter):
    store = ExactVectorStore()
    # Query exactly matches the controlled payload, so poison is the nearest vector.
    question = tiny_questions.iloc[0].to_dict()
    question["question"] = tiny_poison_pool.iloc[0].poisoned_text
    args = dict(chunks=tiny_chunks, poisons=tiny_poison_pool, question=question, custom_query="",
        seed=42, mode=REPEATED, config=offline_config, embedder=embedder, llm=llm,
        reranker=reranker, source_filter=source_filter, store=store)
    result = answer_at_level(**args, count=20, defense="none")
    assert result["target_copies_injected"] == 20
    assert result["target_copies_retrieved"] == offline_config.retrieval.top_k
    filtered = answer_at_level(**args, count=50, defense="source_filtering")
    assert filtered["target_copies_injected"] == 50
    assert filtered["poison_retrieved"] == 0
    assert not store._collections  # temporary indexes are released
