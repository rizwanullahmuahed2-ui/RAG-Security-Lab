"""Embedding layer (spec section 10).

Provides one abstract interface, `EmbeddingService`, with two
implementations:

- `SentenceTransformerEmbeddingService`: the real embedding model. This is
  the intended production path, but it requires downloading model weights
  from Hugging Face on first use, which needs outbound internet access.

- `HashingEmbeddingService`: a deterministic, dependency-light fallback
  (scikit-learn's HashingVectorizer + TF-IDF reweighting) that needs no
  network access or model download at all. It is NOT a substitute for a
  real semantic embedding model in a production research run — it captures
  lexical/token overlap, not deep semantic similarity — but it lets the
  entire pipeline (chunking -> embedding -> vector store -> retrieval ->
  attack -> defense -> evaluation) run and be verified end-to-end in
  network-restricted environments (CI, offline machines, this sandbox),
  which is exactly what section 32's "minimal prototype" is for.

`get_embedding_service(config)` tries the configured primary backend first
and falls back ONLY if it cannot be loaded, logging a clear warning when it
does — silently swapping the embedding model would be exactly the kind of
error section 30 says must not be hidden.
"""
from __future__ import annotations

import abc
import hashlib
import re

import numpy as np

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


class EmbeddingService(abc.ABC):
    """A batch text-embedding service with a stable output dimension."""

    @property
    @abc.abstractmethod
    def dimension(self) -> int: ...

    @property
    @abc.abstractmethod
    def backend_name(self) -> str: ...

    @abc.abstractmethod
    def encode(self, texts: list[str]) -> np.ndarray:
        """Encode a batch of texts -> (n_texts, dimension) float32 array."""

    def encode_one(self, text: str) -> np.ndarray:
        return self.encode([text])[0]


class SentenceTransformerEmbeddingService(EmbeddingService):
    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer  # deferred import

        self._model_name = model_name
        self._model = SentenceTransformer(model_name)
        self._dim = self._model.get_sentence_embedding_dimension()

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def backend_name(self) -> str:
        return f"sentence_transformers:{self._model_name}"

    def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self._dim), dtype=np.float32)
        vectors = self._model.encode(
            texts, batch_size=32, show_progress_bar=False, convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return vectors.astype(np.float32)


class HashingEmbeddingService(EmbeddingService):
    """Deterministic, offline, no-download fallback embedder.

    Implementation: hashed bag-of-words counts (stable across runs and
    processes, unlike Python's built-in hash()) -> log-scaled TF -> L2
    normalization. This is deliberately simple and auditable rather than
    trying to imitate a neural embedding model.
    """

    def __init__(self, dimension: int = 512):
        if dimension <= 0:
            raise ValueError("dimension must be positive")
        self._dim = dimension

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def backend_name(self) -> str:
        return f"hashing:{self._dim}d"

    def _hash_token(self, token: str) -> int:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        return int.from_bytes(digest[:4], "big") % self._dim

    def _vectorize_one(self, text: str) -> np.ndarray:
        vec = np.zeros(self._dim, dtype=np.float32)
        tokens = re.findall(r"\w+(?:[.%-]\w+)*", text.casefold())
        for tok in tokens:
            vec[self._hash_token(tok)] += 1.0
        vec = np.log1p(vec)  # log-scaled term frequency, dampens very common tokens
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self._dim), dtype=np.float32)
        return np.stack([self._vectorize_one(t) for t in texts]).astype(np.float32)


def get_embedding_service(config) -> EmbeddingService:
    """Build the configured embedding backend, falling back on failure.

    `config` is a src.config.config.Config (duck-typed: needs
    embedding_backend, embedding_model, embedding_fallback,
    hashing_embedding_dim).
    """
    if config.embedding_backend == "sentence_transformers":
        try:
            service = SentenceTransformerEmbeddingService(config.embedding_model)
            logger.info("Embedding backend: %s (dim=%d)", service.backend_name, service.dimension)
            return service
        except Exception as exc:  # noqa: BLE001 - deliberately broad: any load failure -> fallback
            if not getattr(config, "allow_fallback", False):
                raise RuntimeError("Embedding model could not load; fallback is disabled") from exc
            logger.warning(
                "Could not load sentence-transformers model '%s' (%s: %s). "
                "Falling back to '%s' embedding backend. Results produced with the "
                "fallback backend are NOT equivalent to a real semantic-embedding run "
                "and should not be reported as the primary experiment result.",
                config.embedding_model, type(exc).__name__, exc, config.embedding_fallback,
            )

    if config.embedding_backend == "hashing" or (config.embedding_backend == "sentence_transformers" and config.embedding_fallback == "hashing"):
        service = HashingEmbeddingService(config.hashing_embedding_dim)
        logger.info("Embedding backend: %s (dim=%d)", service.backend_name, service.dimension)
        return service

    raise RuntimeError(f"Unknown embedding_backend/fallback in config: {config.embedding_backend}")
