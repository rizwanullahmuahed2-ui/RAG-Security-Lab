"""Robust CSV loaders for documents, chunks, questions, and poisoned passages.

Per spec section 7: validate required columns, missing/duplicate IDs, empty
text, and missing Ground Truth. Raise clear errors instead of silently
skipping invalid records — a silently-dropped row is exactly the kind of
thing that would quietly invalidate a security experiment.
"""
from __future__ import annotations

import pandas as pd

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


class DataValidationError(ValueError):
    """Raised when an input CSV fails schema or integrity validation."""


DOCUMENT_FIELDS = [
    "document_id", "title", "category", "subcategory", "source", "source_url",
    "publication_date", "data_year", "last_verified", "language", "text",
    "trust_level", "verification_status", "notes",
]

CHUNK_FIELDS = [
    "chunk_id", "document_id", "title", "category", "chunk_index", "text",
    "source", "source_url", "trust_level", "verification_status",
]

QUESTION_FIELDS = [
    "question_id", "question", "ground_truth", "relevant_document_id",
    "relevant_chunk_id", "category", "question_type", "source", "source_url",
    "data_year", "targeted_for_attack", "attack_id",
]

POISON_FIELDS = [
    "poison_id", "attack_id", "target_question_id", "target_query",
    "correct_answer", "attacker_false_information", "poisoned_text",
    "attack_type", "source_status", "trust_level", "verification_status",
]


def _require_columns(df: pd.DataFrame, required: list[str], name: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise DataValidationError(
            f"{name}: missing required column(s) {missing}. "
            f"Found columns: {list(df.columns)}. "
            f"Fix the CSV or update the schema mapping in src/data/loaders.py "
            f"rather than hardcoding a different column name downstream."
        )


def _require_unique_ids(df: pd.DataFrame, id_col: str, name: str) -> None:
    if (df[id_col] != df[id_col].str.strip()).any():
        raise DataValidationError(f"{name}: {id_col} contains surrounding whitespace")
    dupes = df[df[id_col].duplicated(keep=False)][id_col].unique().tolist()
    if dupes:
        raise DataValidationError(f"{name}: duplicate {id_col} value(s): {dupes}")
    if df[id_col].isna().any() or (df[id_col].astype(str).str.strip() == "").any():
        raise DataValidationError(f"{name}: found missing/empty {id_col} value(s)")


def _require_nonempty(df: pd.DataFrame, col: str, name: str) -> None:
    bad = df[df[col].isna() | (df[col].astype(str).str.strip() == "")]
    if len(bad) > 0:
        raise DataValidationError(
            f"{name}: {len(bad)} row(s) have empty '{col}': "
            f"{bad.index.tolist()[:10]}{'...' if len(bad) > 10 else ''}"
        )


def load_documents(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    _require_columns(df, DOCUMENT_FIELDS, "documents.csv")
    _require_unique_ids(df, "document_id", "documents.csv")
    _require_nonempty(df, "text", "documents.csv")
    _require_nonempty(df, "source", "documents.csv")
    if df.empty:
        raise DataValidationError("documents.csv: dataset must not be empty")
    bad_trust = set(df["trust_level"]) - {"high", "medium", "low"}
    if bad_trust:
        raise DataValidationError(f"documents.csv: invalid trust_level value(s): {bad_trust}")
    bad_verif = set(df["verification_status"]) - {"verified", "unverified"}
    if bad_verif:
        raise DataValidationError(f"documents.csv: invalid verification_status value(s): {bad_verif}")
    logger.info("Loaded %d documents from %s", len(df), path)
    return df


def load_chunks(path: str, valid_document_ids: set[str] | None = None) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    _require_columns(df, CHUNK_FIELDS, "chunks.csv")
    _require_unique_ids(df, "chunk_id", "chunks.csv")
    _require_nonempty(df, "text", "chunks.csv")
    if valid_document_ids is not None:
        orphans = set(df["document_id"]) - valid_document_ids
        if orphans:
            raise DataValidationError(
                f"chunks.csv: chunk(s) reference unknown document_id(s): {orphans}"
            )
    logger.info("Loaded %d chunks from %s", len(df), path)
    return df


def load_questions(path: str, valid_chunk_ids: set[str] | None = None) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    _require_columns(df, QUESTION_FIELDS, "questions.csv")
    _require_unique_ids(df, "question_id", "questions.csv")
    _require_nonempty(df, "question", "questions.csv")
    _require_nonempty(df, "ground_truth", "questions.csv")  # missing Ground Truth check
    values = df["targeted_for_attack"].astype(str).str.strip().str.lower()
    if not values.isin({"true", "false", "1", "0", "yes", "no"}).all():
        raise DataValidationError("questions.csv: invalid targeted_for_attack boolean")
    df["targeted_for_attack"] = values.isin(
        {"true", "1", "yes"}
    )
    targeted = df[df["targeted_for_attack"]]
    bad_targets = targeted[targeted["attack_id"].str.strip() == ""]
    if len(bad_targets) > 0:
        raise DataValidationError(
            f"questions.csv: {len(bad_targets)} question(s) marked targeted_for_attack=True "
            f"but have no attack_id: {bad_targets['question_id'].tolist()}"
        )
    if valid_chunk_ids is not None:
        orphans = set(df["relevant_chunk_id"]) - valid_chunk_ids
        if orphans:
            raise DataValidationError(
                f"questions.csv: question(s) reference unknown relevant_chunk_id(s): {orphans}"
            )
    logger.info("Loaded %d questions (%d targeted) from %s", len(df), len(targeted), path)
    return df


def load_poisoned_passages(path: str, valid_question_ids: set[str] | None = None) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    _require_columns(df, POISON_FIELDS, "poisoned_passages.csv")
    _require_unique_ids(df, "poison_id", "poisoned_passages.csv")
    _require_nonempty(df, "poisoned_text", "poisoned_passages.csv")
    for column in ("attack_id", "target_question_id", "target_query", "correct_answer", "attacker_false_information"):
        _require_nonempty(df, column, "poisoned_passages.csv")
    _require_unique_ids(df, "attack_id", "poisoned_passages.csv")
    if set(df["verification_status"]) - {"unverified"}:
        raise DataValidationError("poisoned_passages.csv: verification_status must be unverified")
    bad_type = set(df["attack_type"]) - {"targeted_adversarial_passage_injection"}
    if bad_type:
        raise DataValidationError(f"poisoned_passages.csv: unexpected attack_type value(s): {bad_type}")
    bad_status = set(df["source_status"]) - {"attacker_generated"}
    if bad_status:
        raise DataValidationError(f"poisoned_passages.csv: unexpected source_status value(s): {bad_status}")
    bad_trust = set(df["trust_level"]) - {"untrusted"}
    if bad_trust:
        raise DataValidationError(
            f"poisoned_passages.csv: expected all poisoned records to be trust_level='untrusted', "
            f"found: {bad_trust}"
        )
    if valid_question_ids is not None:
        orphans = set(df["target_question_id"]) - valid_question_ids
        if orphans:
            raise DataValidationError(
                f"poisoned_passages.csv: poison(s) reference unknown target_question_id(s): {orphans}"
            )
    logger.info("Loaded %d poisoned passages from %s", len(df), path)
    return df


def load_all(paths) -> dict[str, pd.DataFrame]:
    """Load + cross-validate all four input tables together.

    `paths` is a src.config.config.PathsConfig (or anything with the same
    attribute names).
    """
    documents = load_documents(paths.documents_csv)
    chunks = load_chunks(paths.chunks_csv, valid_document_ids=set(documents["document_id"]))
    questions = load_questions(paths.questions_csv, valid_chunk_ids=set(chunks["chunk_id"]))
    poisoned = load_poisoned_passages(
        paths.poisoned_passages_csv, valid_question_ids=set(questions["question_id"])
    )
    validate_relationships(documents, chunks, questions, poisoned)
    return {
        "documents": documents,
        "chunks": chunks,
        "questions": questions,
        "poisoned_passages": poisoned,
    }


def validate_relationships(documents, chunks, questions, poisoned) -> None:
    """Reject contradictory provenance and attack labels before any experiment."""
    if chunks.empty or questions.empty:
        raise DataValidationError("chunks and questions must not be empty")
    docs = documents.set_index("document_id")
    chunk_index = chunks.set_index("chunk_id")
    question_index = questions.set_index("question_id")
    for chunk in chunks.itertuples(index=False):
        doc = docs.loc[chunk.document_id]
        for field in ("trust_level", "verification_status", "source", "source_url"):
            if getattr(chunk, field) != doc[field]:
                raise DataValidationError(f"{chunk.chunk_id}: chunk {field} differs from document provenance")
    for question in questions.itertuples(index=False):
        if question.relevant_document_id != chunk_index.loc[question.relevant_chunk_id, "document_id"]:
            raise DataValidationError(f"{question.question_id}: relevant document/chunk mismatch")
    for poison in poisoned.itertuples(index=False):
        question = question_index.loc[poison.target_question_id]
        if not question.targeted_for_attack or question.attack_id != poison.attack_id:
            raise DataValidationError(f"{poison.poison_id}: attack/target linkage mismatch")
        if question.ground_truth.strip() != poison.correct_answer.strip() or question.question.strip() != poison.target_query.strip():
            raise DataValidationError(f"{poison.poison_id}: target query or ground truth mismatch")
        if poison.correct_answer.casefold().strip() == poison.attacker_false_information.casefold().strip():
            raise DataValidationError(f"{poison.poison_id}: false claim equals ground truth")
    missing = set(questions.loc[questions.targeted_for_attack, "attack_id"]) - set(poisoned.attack_id)
    if missing:
        raise DataValidationError(f"Targeted questions missing poisons: {sorted(missing)}")
    if set(chunks.chunk_id) & set(poisoned.poison_id):
        raise DataValidationError("Poison IDs collide with clean chunk IDs")
