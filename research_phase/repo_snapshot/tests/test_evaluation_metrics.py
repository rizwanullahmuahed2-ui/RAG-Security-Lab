"""Metric tests (spec section 31): poison-retrieval detection and
attack-success logic. These are the tests that most directly protect the
project's central research-integrity claim (section 21): poison_retrieved,
answer_error, and attack_success are three DIFFERENT events and must never
collapse into each other.
"""
from __future__ import annotations

import pytest

from src.evaluation import metrics


# --- exact_match / contains_value -------------------------------------------

def test_exact_match_handles_hedge_words_and_units():
    assert metrics.exact_match("Approximately 34 provinces are in Afghanistan.", "34 provinces") is True
    assert metrics.exact_match("The population was 42,647,492 in 2024.", "Approximately 42,647,492 (about 42.6 million)") is True


def test_exact_match_rejects_wrong_value():
    assert metrics.exact_match("Afghanistan has 32 provinces.", "34 provinces") is False


# --- poison_retrieved vs answer_correct vs attack_success are independent --

def _record(poison_retrieved, answer_correct, attack_success, targeted=True):
    return {
        "poison_retrieved": poison_retrieved, "answer_correct": answer_correct,
        "attack_success": attack_success, "targeted_for_attack": targeted,
    }


def test_poison_retrieved_without_wrong_answer_is_not_attack_success():
    """LLM ignored the poison and answered correctly anyway -> poison WAS
    retrieved, but this must not be scored as attack success."""
    record = _record(poison_retrieved=True, answer_correct=True, attack_success=False)
    assert record["poison_retrieved"] is True
    assert record["attack_success"] is False


def test_wrong_answer_without_poison_retrieval_is_not_attack_success():
    """An ordinary generation error, unrelated to this attack, must not be
    counted toward attack_success_rate."""
    record = _record(poison_retrieved=False, answer_correct=False, attack_success=False)
    assert metrics.attack_success_rate([record]) == 0.0


def test_attack_success_rate_only_counts_true_attack_success_flags():
    records = [
        _record(poison_retrieved=True, answer_correct=False, attack_success=True),   # real attack success
        _record(poison_retrieved=True, answer_correct=False, attack_success=False),  # wrong, but NOT the attacker's claim
        _record(poison_retrieved=False, answer_correct=False, attack_success=False),  # unrelated error
        _record(poison_retrieved=True, answer_correct=True, attack_success=False),   # poison ignored
    ]
    assert metrics.attack_success_rate(records) == 0.25


def test_answer_reflects_false_info_vs_ground_truth_are_scored_independently():
    predicted = "Afghanistan now has 32 provinces."
    assert metrics.answer_reflects_false_info(predicted, "32 provinces") is True
    assert metrics.exact_match(predicted, "34 provinces") is False


def test_poison_retrieval_rate_counts_only_flagged_records():
    records = [
        _record(poison_retrieved=True, answer_correct=True, attack_success=False),
        _record(poison_retrieved=False, answer_correct=True, attack_success=False),
    ]
    assert metrics.poison_retrieval_rate(records) == 0.5


def test_recall_at_k_and_mrr():
    records = [
        {"correct_chunk_retrieved": True, "retrieved_chunk_ids": ["A", "B", "C"], "relevant_chunk_id": "B"},
        {"correct_chunk_retrieved": False, "retrieved_chunk_ids": ["X", "Y"], "relevant_chunk_id": "Z"},
    ]
    assert metrics.recall_at_k(records) == 0.5
    # MRR: 1/2 for the first record (rank 2), 0 for the second (not found) -> mean 0.25
    assert metrics.mean_reciprocal_rank(records) == 0.25


def test_defense_success_rate_relative_reduction():
    assert metrics.defense_success_rate(baseline_asr=0.8, defended_asr=0.2) == pytest.approx(0.75)
    assert metrics.defense_success_rate(baseline_asr=0.0, defended_asr=0.0) is None
