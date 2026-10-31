"""Data loader tests (spec section 31): required fields and ID integrity."""
from __future__ import annotations

import pandas as pd
import pytest

from src.data.loaders import (
    DataValidationError, load_chunks, load_documents, load_poisoned_passages, load_questions,
)


def _write(df: pd.DataFrame, path) -> str:
    df.to_csv(path, index=False)
    return str(path)


def test_load_documents_happy_path(tiny_documents, tmp_path):
    path = _write(tiny_documents, tmp_path / "documents.csv")
    df = load_documents(path)
    assert len(df) == len(tiny_documents)


def test_load_documents_rejects_missing_column(tiny_documents, tmp_path):
    bad = tiny_documents.drop(columns=["trust_level"])
    path = _write(bad, tmp_path / "documents.csv")
    with pytest.raises(DataValidationError, match="missing required column"):
        load_documents(path)


def test_load_documents_rejects_duplicate_id(tiny_documents, tmp_path):
    bad = pd.concat([tiny_documents, tiny_documents.iloc[[0]]], ignore_index=True)
    path = _write(bad, tmp_path / "documents.csv")
    with pytest.raises(DataValidationError, match="duplicate"):
        load_documents(path)


def test_load_documents_rejects_empty_text(tiny_documents, tmp_path):
    bad = tiny_documents.copy()
    bad.loc[0, "text"] = ""
    path = _write(bad, tmp_path / "documents.csv")
    with pytest.raises(DataValidationError, match="empty 'text'"):
        load_documents(path)


def test_load_documents_rejects_invalid_trust_level(tiny_documents, tmp_path):
    bad = tiny_documents.copy()
    bad.loc[0, "trust_level"] = "super-trusted"  # not one of high/medium/low
    path = _write(bad, tmp_path / "documents.csv")
    with pytest.raises(DataValidationError, match="invalid trust_level"):
        load_documents(path)


def test_load_chunks_rejects_orphan_document_id(tiny_documents, tiny_chunks, tmp_path):
    bad = tiny_chunks.copy()
    bad.loc[0, "document_id"] = "DOC-DOES-NOT-EXIST"
    path = _write(bad, tmp_path / "chunks.csv")
    with pytest.raises(DataValidationError, match="unknown document_id"):
        load_chunks(path, valid_document_ids=set(tiny_documents["document_id"]))


def test_load_questions_rejects_missing_ground_truth(tiny_questions, tmp_path):
    bad = tiny_questions.copy()
    bad.loc[0, "ground_truth"] = ""
    path = _write(bad, tmp_path / "questions.csv")
    with pytest.raises(DataValidationError, match="empty 'ground_truth'"):
        load_questions(path)


def test_load_questions_rejects_targeted_without_attack_id(tiny_questions, tmp_path):
    bad = tiny_questions.copy()
    bad.loc[0, "attack_id"] = ""  # row 0 has targeted_for_attack=True
    path = _write(bad, tmp_path / "questions.csv")
    with pytest.raises(DataValidationError, match="no attack_id"):
        load_questions(path)


def test_load_poisoned_passages_rejects_orphan_target_question(tiny_poison_pool, tiny_questions, tmp_path):
    bad = tiny_poison_pool.copy()
    bad.loc[0, "target_question_id"] = "TQ-DOES-NOT-EXIST"
    path = _write(bad, tmp_path / "poisoned_passages.csv")
    with pytest.raises(DataValidationError, match="unknown target_question_id"):
        load_poisoned_passages(path, valid_question_ids=set(tiny_questions["question_id"]))


def test_load_poisoned_passages_rejects_wrong_trust_level(tiny_poison_pool, tmp_path):
    bad = tiny_poison_pool.copy()
    bad.loc[0, "trust_level"] = "high"  # poisoned records must be 'untrusted'
    path = _write(bad, tmp_path / "poisoned_passages.csv")
    with pytest.raises(DataValidationError, match="trust_level"):
        load_poisoned_passages(path)
