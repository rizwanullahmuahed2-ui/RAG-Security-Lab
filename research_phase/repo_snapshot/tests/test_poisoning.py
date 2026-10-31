"""Poisoning tests (spec section 31): clean data must remain unchanged."""
from __future__ import annotations

import pandas as pd

from src.attacks.poison_generator import create_poisoned_kb, generate_poison, select_poison_subset


def test_create_poisoned_kb_does_not_mutate_clean_chunks(tiny_chunks, tiny_poison_pool):
    original = tiny_chunks.copy(deep=True)
    combined, injected = create_poisoned_kb(tiny_chunks, tiny_poison_pool, poison_count=2, random_seed=42)

    # The input DataFrame object itself must be untouched.
    pd.testing.assert_frame_equal(tiny_chunks, original)
    # Every original clean row must still be present, unmodified, in the combined KB.
    for _, row in tiny_chunks.iterrows():
        match = combined[combined["chunk_id"] == row["chunk_id"]]
        assert len(match) == 1
        assert match.iloc[0]["text"] == row["text"]


def test_create_poisoned_kb_adds_exactly_the_requested_count(tiny_chunks, tiny_poison_pool):
    combined, injected = create_poisoned_kb(tiny_chunks, tiny_poison_pool, poison_count=2, random_seed=42)
    assert len(injected) == 2
    assert len(combined) == len(tiny_chunks) + 2


def test_create_poisoned_kb_zero_count_matches_clean_exactly(tiny_chunks, tiny_poison_pool):
    combined, injected = create_poisoned_kb(tiny_chunks, tiny_poison_pool, poison_count=0, random_seed=42)
    assert len(injected) == 0
    assert len(combined) == len(tiny_chunks)


def test_select_poison_subset_is_reproducible(tiny_poison_pool):
    a = select_poison_subset(tiny_poison_pool, count=2, random_seed=42)
    b = select_poison_subset(tiny_poison_pool, count=2, random_seed=42)
    assert list(a["poison_id"]) == list(b["poison_id"])


def test_poisoned_records_never_contain_ground_truth_as_the_stated_answer():
    record = generate_poison(
        target_query="How many provinces does Afghanistan have?",
        correct_answer="34 provinces",
        attacker_false_information="30 provinces",
        poison_id="POI-TEST", attack_id="ATK-TEST", target_question_id="Q-TEST", seed=1,
    )
    assert "34" not in record["poisoned_text"]
    assert "30 provinces" in record["poisoned_text"]
    assert record["trust_level"] == "untrusted"
    assert record["verification_status"] == "unverified"
    assert record["source_status"] == "attacker_generated"


def test_generate_poison_is_deterministic_for_a_fixed_seed():
    kwargs = dict(
        target_query="What is the capital of Afghanistan?", correct_answer="Kabul",
        attacker_false_information="Kandahar", poison_id="POI-X", attack_id="ATK-X",
        target_question_id="Q-X", seed=7,
    )
    assert generate_poison(**kwargs)["poisoned_text"] == generate_poison(**kwargs)["poisoned_text"]
