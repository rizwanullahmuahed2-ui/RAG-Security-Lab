"""Run reproducible RAG poisoning experiments or validate the benchmark."""
from __future__ import annotations
import argparse
from pathlib import Path
import json
from src.config.config import load_config
from src.data.loaders import load_all
from src.evaluation.runner import build_plan, execute

_build_plan = build_plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(Path(__file__).with_name("config.yaml")))
    parser.add_argument("--experiment", choices=["clean", "poisoning", "reranking", "source_filtering", "filtering", "all"], default="all")
    parser.add_argument("--seeds", nargs="+", type=int, help="Attack selection seeds, e.g. 17 42 91")
    parser.add_argument("--split", choices=["all", "development", "validation", "test"], default="all")
    parser.add_argument("--offline", action="store_true", help="Use hashing, lexical reranking, and extractive generation")
    parser.add_argument("--validate-only", action="store_true", help="Check dataset without loading models")
    args = parser.parse_args()
    config = load_config(args.config)
    if args.offline:
        config.embedding_backend = "hashing"
        config.reranking.backend = "lexical_overlap"
        config.llm_backend = "extractive"
    if args.validate_only:
        data = load_all(config.paths)
        if max(config.poisoning.counts) > len(data["poisoned_passages"]):
            parser.error("poisoning.counts exceeds available poison pool")
        print(json.dumps({name: len(table) for name, table in data.items()}, indent=2))
        return
    output, summary = execute(config, args.experiment, args.seeds, args.split)
    print(summary.to_string(index=False))
    print(f"\nResults: {output}")


if __name__ == "__main__":
    main()
