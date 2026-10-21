"""Central configuration loader.

Everything else in `src/` reads its parameters from a single `Config`
object built here, rather than hardcoding values — see config.yaml for the
authoritative parameter list.
"""
from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any

import yaml


@dataclasses.dataclass
class VectorDBConfig:
    persist_directory: str
    clean_collection: str
    poisoned_collection_prefix: str
    backend: str = "exact"


@dataclasses.dataclass
class ChunkingConfig:
    chunk_size_tokens: int
    chunk_overlap_tokens: int


@dataclasses.dataclass
class RetrievalConfig:
    top_k: int
    candidate_k: int


@dataclasses.dataclass
class RerankingConfig:
    backend: str
    fallback_backend: str
    model: str
    final_k: int


@dataclasses.dataclass
class FilteringConfig:
    allowed_trust_levels: list[str]
    allowed_verification_statuses: list[str]


@dataclasses.dataclass
class PoisoningConfig:
    counts: list[int]
    random_seed: int


@dataclasses.dataclass
class PathsConfig:
    documents_csv: str
    chunks_csv: str
    questions_csv: str
    poisoned_passages_csv: str
    results_raw_dir: str
    results_tables_dir: str
    results_figures_dir: str


@dataclasses.dataclass
class Config:
    embedding_backend: str
    embedding_fallback: str
    embedding_model: str
    hashing_embedding_dim: int

    llm_backend: str
    llm_model: str
    llm_system_prompt: str
    llm_temperature: float
    llm_max_tokens: int

    vector_db: VectorDBConfig
    chunking: ChunkingConfig
    retrieval: RetrievalConfig
    reranking: RerankingConfig
    filtering: FilteringConfig
    poisoning: PoisoningConfig
    paths: PathsConfig
    random_seed: int

    project_root: Path = dataclasses.field(default_factory=Path.cwd)
    allow_fallback: bool = False

    def validate(self) -> None:
        if self.vector_db.backend not in {"exact", "chroma"}:
            raise ValueError("vector_db.backend must be exact or chroma")
        if self.llm_backend == "anthropic" and not self.llm_model.strip():
            raise ValueError("Set llm_model to a provider-supported model ID")
        if self.embedding_backend not in {"hashing", "sentence_transformers"}:
            raise ValueError("Unknown embedding_backend")
        if self.embedding_fallback not in {"hashing", "none"}:
            raise ValueError("Unknown embedding_fallback")
        if self.llm_backend not in {"extractive", "anthropic"}:
            raise ValueError("Unknown llm_backend")
        if self.reranking.backend not in {"lexical_overlap", "cross_encoder"}:
            raise ValueError("Unknown reranking.backend")
        if self.reranking.fallback_backend not in {"lexical_overlap", "none"}:
            raise ValueError("Unknown reranking.fallback_backend")
        for name, value in {
            "hashing_embedding_dim": self.hashing_embedding_dim,
            "top_k": self.retrieval.top_k, "candidate_k": self.retrieval.candidate_k,
            "final_k": self.reranking.final_k, "llm_max_tokens": self.llm_max_tokens,
            "chunk_size_tokens": self.chunking.chunk_size_tokens,
        }.items():
            if type(value) is not int or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if self.retrieval.candidate_k < max(self.retrieval.top_k, self.reranking.final_k):
            raise ValueError("candidate_k must be >= top_k and final_k")
        if not 0 <= self.chunking.chunk_overlap_tokens < self.chunking.chunk_size_tokens:
            raise ValueError("chunk_overlap_tokens must be >= 0 and < chunk_size_tokens")
        counts = self.poisoning.counts
        if not counts or any(type(c) is not int or c < 0 for c in counts):
            raise ValueError("poisoning.counts must contain nonnegative integers")
        if 0 not in counts or len(counts) != len(set(counts)):
            raise ValueError("poisoning.counts must be unique and include clean baseline 0")
        if type(self.allow_fallback) is not bool:
            raise ValueError("allow_fallback must be a boolean")
        for name, value in (("random_seed", self.random_seed),
                            ("poisoning.random_seed", self.poisoning.random_seed)):
            if type(value) is not int or not 0 <= value < 2**32:
                raise ValueError(f"{name} must be an integer in [0, 2**32)")
        if not self.filtering.allowed_trust_levels or not self.filtering.allowed_verification_statuses:
            raise ValueError("Filtering allow lists must not be empty")

    def resolve(self, relative_path: str) -> Path:
        """Resolve a path from config.yaml relative to the project root."""
        return (self.project_root / relative_path).resolve()


def load_config(config_path: str | Path = "config.yaml") -> Config:
    config_path = Path(config_path)
    project_root = config_path.parent.resolve()
    with open(config_path, "r", encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f)

    config = Config(
        embedding_backend=raw["embedding_backend"],
        embedding_fallback=raw["embedding_fallback"],
        embedding_model=raw["embedding_model"],
        hashing_embedding_dim=raw["hashing_embedding_dim"],
        llm_backend=raw["llm_backend"],
        llm_model=raw["llm_model"],
        llm_system_prompt=raw["llm_system_prompt"],
        llm_temperature=raw["llm_temperature"],
        llm_max_tokens=raw["llm_max_tokens"],
        vector_db=VectorDBConfig(**raw["vector_db"]),
        chunking=ChunkingConfig(**raw["chunking"]),
        retrieval=RetrievalConfig(**raw["retrieval"]),
        reranking=RerankingConfig(**raw["reranking"]),
        filtering=FilteringConfig(**raw["filtering"]),
        poisoning=PoisoningConfig(**raw["poisoning"]),
        paths=PathsConfig(**raw["paths"]),
        random_seed=raw["random_seed"],
        project_root=project_root,
        allow_fallback=raw.get("allow_fallback", False),
    )
    config.validate()
    # All input/output paths have the same semantics from CLI, UI, and library callers.
    for field in dataclasses.fields(config.paths):
        setattr(config.paths, field.name, str(config.resolve(getattr(config.paths, field.name))))
    return config
