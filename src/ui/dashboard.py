"""Small, testable view models; no Streamlit or model initialization here."""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd


DEFENSE_LABELS = {
    "none": "No defense",
    "reranking": "Relevance reranking",
    "source_filtering": "Trusted-source filtering",
    "reranking+source_filtering": "Reranking + source filtering",
}


def parse_selection_seeds(value: str) -> list[int]:
    """Reject ambiguous inputs before an expensive experiment begins."""
    try:
        seeds = [int(part) for part in value.split()]
    except ValueError as exc:
        raise ValueError("Enter whole-number seeds separated by spaces, for example 17 42 91.") from exc
    if not seeds or any(not 0 <= seed < 2**32 for seed in seeds):
        raise ValueError("Enter at least one seed between 0 and 4294967295.")
    if len(seeds) != len(set(seeds)):
        raise ValueError("Use each seed once; duplicate seeds would repeat the same selection.")
    return seeds


def filter_rows(frame: pd.DataFrame, query: str) -> pd.DataFrame:
    """Case-insensitive literal search, including punctuation from user input."""
    if not query.strip():
        return frame
    matches = frame.astype(str).apply(
        lambda column: column.str.contains(query.strip(), case=False, regex=False)
    ).any(axis=1)
    return frame.loc[matches]


def completed_runs(root: Path) -> tuple[list[tuple[Path, dict]], list[str]]:
    """A partial or malformed historical run must not break the question UI."""
    valid, skipped = [], []
    for path in sorted(root.glob("*/manifest.json"), reverse=True):
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(manifest, dict):
                raise ValueError("Manifest must be an object")
            if manifest.get("status") != "completed":
                continue
            for name in ("summary_metrics.csv", "results.csv"):
                if not (path.parent / name).is_file():
                    raise ValueError(f"Missing {name}")
            valid.append((path, manifest))
        except (OSError, ValueError):
            skipped.append(path.parent.name)
    return valid, skipped


def safe_source_url(value: object) -> str | None:
    """Only expose ordinary web links from untrusted evidence metadata."""
    if not isinstance(value, str):
        return None
    try:
        parsed = urlparse(value)
        return value if parsed.scheme in {"http", "https"} and parsed.hostname else None
    except ValueError:
        return None


def evidence_table(saved: dict) -> pd.DataFrame:
    rows = []
    for rank, evidence in enumerate(saved["result"].retrieved_documents, 1):
        rows.append({
            "Rank": rank,
            "Evidence": "Injected poison" if evidence["chunk_id"] in saved["poison_ids"] else "Corpus passage",
            "Chunk": evidence["chunk_id"],
            "Source": evidence.get("source", ""),
            "Trust": evidence.get("trust_level", ""),
            "Verification": evidence.get("verification_status", ""),
            "Similarity": evidence.get("original_similarity"),
            "Rerank score": evidence.get("rerank_score"),
        })
    return pd.DataFrame(rows)


def answer_export(saved: dict, config: dict, hashes: dict) -> str:
    """Keep answer, exact context, attack attribution and provenance together."""
    content = {
        "schema_version": 1,
        "question_id": saved["selection_key"][0],
        "custom_query": saved["selection_key"][1],
        "mode": saved["mode"], "poison_count": saved["count"],
        "defense": saved["defense"], "seed": saved["seed"],
        "actual_backends": saved["backends"],
        "config": config, "dataset_sha256": hashes,
        "result": asdict(saved["result"]), "verdict": saved["verdict"],
        "ground_truth": saved["gold"] if saved["verdict"] is not None else None,
        "injected_poison_ids": sorted(saved["poison_ids"]),
        "target_copies_injected": saved["target_copies_injected"],
        "target_copies_retrieved": saved["target_copies_retrieved"],
        "limitations": [
            "Lexical answer matching is not factual entailment.",
            "Repeated passages are duplicate evidence, not independent sources.",
            "Source filtering assumes trusted ingestion metadata.",
        ],
    }
    return json.dumps(content, indent=2, ensure_ascii=False, default=str)
