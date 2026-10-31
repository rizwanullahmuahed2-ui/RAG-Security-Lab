"""Shared CLI/dashboard runner with isolated, self-describing experiment artifacts."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version, PackageNotFoundError
import json
from pathlib import Path
import platform
from uuid import uuid4

import pandas as pd
from src.data.loaders import load_all
from src.defenses.reranker import get_reranker
from src.defenses.source_filter import get_source_filter
from src.embeddings.embedding_service import get_embedding_service
from src.evaluation.evaluator import DEFENSE_VARIANTS, run_condition, summarize
from src.evaluation.io import save_records
from src.evaluation.visualization import generate_all_figures
from src.generation.llm_interface import get_llm
from src.vectorstore.chroma_store import ChromaVectorStore
from src.vectorstore.exact_store import get_vector_store


def build_plan(experiment: str, counts: list[int]):
    variants = {
        "clean": [("none", False, False)], "poisoning": [("none", False, False)],
        "reranking": [("reranking", True, False)],
        "source_filtering": [("source_filtering", False, True)],
        "filtering": [("reranking+source_filtering", True, True)], "all": DEFENSE_VARIANTS,
    }
    if experiment not in variants:
        raise ValueError(f"Unknown experiment: {experiment}")
    return [(count, *variant) for count in ([0] if experiment == "clean" else sorted(counts))
            for variant in variants[experiment]]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def input_hashes(config) -> dict:
    return {name: sha256(Path(getattr(config.paths, name))) for name in
            ("documents_csv", "chunks_csv", "questions_csv", "poisoned_passages_csv")}


def execute(config, experiment="all", seeds=None, split="all", progress=None):
    """Do not merge prior results. Seeds vary attack selection only."""
    config.validate()
    before_load = input_hashes(config)
    data = load_all(config.paths)
    if input_hashes(config) != before_load:
        raise RuntimeError("Dataset changed while being loaded")
    questions = data["questions"]
    if split != "all":
        if "split" not in questions:
            raise ValueError("Dataset has no split labels")
        questions = questions.loc[questions["split"] == split]
    if questions.empty:
        raise ValueError("No questions selected")
    plan = build_plan(experiment, config.poisoning.counts)
    if max(count for count, *_ in plan) > len(data["poisoned_passages"]):
        raise ValueError("Configured poison count exceeds available poison pool")
    seeds = seeds if seeds is not None else [config.poisoning.random_seed]
    if not seeds or len(seeds) != len(set(seeds)) or any(type(s) is not int or not 0 <= s < 2**32 for s in seeds):
        raise ValueError("Seeds must be unique integers in [0, 2**32)")
    root = config.resolve("results")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    output = root / "runs" / run_id
    output.mkdir(parents=True, exist_ok=False)
    config_dict = json.loads(json.dumps(asdict(config), default=str))
    (output / "config.json").write_text(json.dumps(config_dict, indent=2), encoding="utf-8")
    manifest = {
        "schema_version": 2, "run_id": run_id, "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(), "experiment": experiment,
        "seeds": seeds, "split": split, "n_questions": len(questions),
        "dataset_sha256": before_load, "config": config_dict,
        "python": platform.python_version(), "platform": platform.platform(),
        "source_sha256": {str(p.relative_to(config.project_root)): sha256(p)
                          for p in sorted((config.project_root / "src").rglob("*.py"))},
        "dependencies": {},
        "limitations": ["Lexical answer scoring is not entailment; negation requires manual review",
                        "WDI years/paraphrases are correlated; Wilson intervals are descriptive",
                        "Source filtering assumes trustworthy ingestion metadata",
                        "Seeds vary attack selection, not independent question samples"],
    }
    for package in ("numpy", "pandas", "scikit-learn", "chromadb", "streamlit", "sentence-transformers", "anthropic"):
        try:
            manifest["dependencies"][package] = version(package)
        except PackageNotFoundError:
            manifest["dependencies"][package] = None
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    try:
        embedder, llm = get_embedding_service(config), get_llm(config)
        reranker, source_filter = get_reranker(config), get_source_filter(config)
        manifest["actual_backends"] = dict(embedding=embedder.backend_name, reranker=reranker.backend_name, generation=llm.backend_name, vector_store=config.vector_db.backend)
        manifest["offline_demo"] = llm.backend_name == "extractive-stub" or embedder.backend_name.startswith("hashing")
        all_records = []
        for seed in seeds:
            run_config = deepcopy(config)
            run_config.poisoning.random_seed = seed
            store = get_vector_store(config)
            for count, defense, rerank, filtering in plan:
                records = run_condition(
                    clean_chunks=data["chunks"], poison_pool=data["poisoned_passages"], questions=questions,
                    embedder=embedder, store=store, reranker=reranker, source_filter=source_filter,
                    llm=llm, config=run_config, poison_count=count, apply_reranking=rerank,
                    apply_filtering=filtering, collection_name=f"experiment_{count}",
                )
                all_records.extend(records)
                if progress:
                    progress(len(all_records) / (len(seeds) * len(plan) * len(questions)),
                             f"Seed {seed}, {count} poisoned passages, {defense}")
        if input_hashes(config) != manifest["dataset_sha256"]:
            raise RuntimeError("Dataset changed during the run; refusing inconsistent results")
        save_records(all_records, output / "results.csv")
        summary = summarize(all_records)
        summary.to_csv(output / "summary_metrics.csv", index=False)
        metric_columns = ["answer_accuracy", "recall_at_k", "mrr", "attack_success_rate", "attack_success_rate_injected"]
        aggregate = summary.groupby(["condition", "defense_method", "poison_count"])[metric_columns].agg(["mean", "std"])
        aggregate.columns = ["_".join(pair) for pair in aggregate.columns]
        aggregate.reset_index().to_csv(output / "seed_summary.csv", index=False)
        for dimension in ("category", "split"):
            parts = []
            for value in sorted({r[dimension] for r in all_records}):
                part = summarize([r for r in all_records if r[dimension] == value])
                part[dimension] = value
                parts.append(part)
            pd.concat(parts, ignore_index=True).to_csv(output / f"by_{dimension}.csv", index=False)
        generate_all_figures(summary, output / "figures")
        manifest.update(status="completed", completed_at=datetime.now(timezone.utc).isoformat(),
                        n_records=len(all_records), n_configurations=len(plan),
                        output_sha256={p.name: sha256(p) for p in output.glob("*.csv")})
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        temporary = root / f"latest_{run_id}.tmp"
        temporary.write_text(json.dumps({"run_id": run_id}), encoding="utf-8")
        temporary.replace(root / "latest.json")
        return output, summary
    except Exception as exc:
        manifest.update(status="failed", error_type=type(exc).__name__)
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        raise
