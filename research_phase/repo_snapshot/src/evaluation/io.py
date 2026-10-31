"""Converts in-memory evaluation records (with real list/bool/int fields)
to and from the flat CSV shape used by evaluation_results.csv and the
per-experiment raw result files in results/raw/.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json

import pandas as pd

RESULT_COLUMNS = [
    "experiment_id", "question_id", "condition", "top_k", "retrieved_chunk_ids",
    "retrieved_scores", "poison_retrieved", "poison_rank", "poison_count_retrieved",
    "correct_chunk_retrieved", "generated_answer", "ground_truth", "answer_correct",
    "f1", "attack_success", "defense_enabled", "defense_method",
    "relevant_chunk_id", "category", "targeted_for_attack",
]

EXTRA_COLUMNS = ["poison_count", "poison_fraction", "seed", "split", "family_id", "question", "attack_id",
                 "attack_injected", "target_poison_retrieved", "latency_ms", "embedding_backend",
                 "reranker_backend", "llm_backend", "evidence", "strict_exact_match", "false_claim_match", "ambiguous_answer"]


def records_to_dataframe(records: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for r in records:
        row = dict(r)
        row["retrieved_chunk_ids"] = "|".join(r["retrieved_chunk_ids"])
        row["retrieved_scores"] = "|".join(str(s) for s in r["retrieved_scores"])
        row["poison_rank"] = "" if r["poison_rank"] is None else r["poison_rank"]
        if "evidence" in row:
            row["evidence"] = json.dumps(row["evidence"], ensure_ascii=False)
        rows.append(row)
    df = pd.DataFrame(rows)
    for col in RESULT_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[RESULT_COLUMNS + [c for c in EXTRA_COLUMNS if c in df]]


def save_records(records: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    records_to_dataframe(records).to_csv(path, index=False)


def load_records(path: Path) -> list[dict[str, Any]]:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    records = []
    for row in df.to_dict("records"):
        row["retrieved_chunk_ids"] = row["retrieved_chunk_ids"].split("|") if row["retrieved_chunk_ids"] else []
        row["retrieved_scores"] = (
            [float(s) for s in row["retrieved_scores"].split("|")] if row["retrieved_scores"] else []
        )
        row["poison_rank"] = int(row["poison_rank"]) if row["poison_rank"] not in ("", None) else None
        row["top_k"] = int(row["top_k"])
        row["poison_count_retrieved"] = int(row["poison_count_retrieved"])
        row["f1"] = float(row["f1"])
        for bool_col in ("poison_retrieved", "correct_chunk_retrieved", "answer_correct",
                          "attack_success", "defense_enabled", "targeted_for_attack", "attack_injected",
                          "target_poison_retrieved", "strict_exact_match", "false_claim_match", "ambiguous_answer"):
            if bool_col not in row:
                continue
            row[bool_col] = str(row[bool_col]).strip().lower() == "true"
        for column in ("poison_count", "seed"):
            if column in row:
                row[column] = int(row[column])
        for column in ("poison_fraction", "latency_ms"):
            if column in row:
                row[column] = float(row[column])
        if "evidence" in row:
            row["evidence"] = json.loads(row["evidence"])
        records.append(row)
    return records
