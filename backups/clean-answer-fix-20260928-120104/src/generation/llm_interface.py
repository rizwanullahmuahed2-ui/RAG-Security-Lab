"""Provider-independent LLM interface (spec section 14).

`llm_backend: "extractive"` (config.yaml default) needs no API key and no
network access: it answers by picking the most query-relevant sentence(s)
out of the supplied context, and explicitly says the evidence is
insufficient if nothing in the context overlaps the query. It is a
deterministic STUB, not a claim that it reasons like an LLM — but it keeps
the retrieval-vs-generation distinction in the evaluation real and
reproducible in a sandboxed/offline environment, per the "no fake results"
rule (section 4): every answer it returns is actually computed from the
actual retrieved context, not invented.

`llm_backend: "anthropic"` is the real generative-model path for anyone
running this project with API access; it requires ANTHROPIC_API_KEY and
raises a clear error rather than silently falling back if that's missing,
because silently downgrading the generation step would make the
generation-impact and attack-success metrics meaningless without saying so.
"""
from __future__ import annotations

import abc
import os
import re

from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "of", "in", "on", "for", "to",
    "what", "which", "who", "how", "many", "much", "does", "did", "do", "and",
    "or", "according", "afghanistan", "afghanistan's",
}


class LLMInterface(abc.ABC):
    @property
    @abc.abstractmethod
    def backend_name(self) -> str: ...

    @abc.abstractmethod
    def generate(self, query: str, context: str, system_prompt: str,
                 temperature: float = 0.0, max_tokens: int = 300) -> str: ...


class ExtractiveLLM(LLMInterface):
    """Deterministic no-API-key stub. See module docstring."""

    @property
    def backend_name(self) -> str:
        return "extractive-stub"

    @staticmethod
    def _keywords(text: str) -> set[str]:
        words = re.findall(r"[a-zA-Z0-9%.\-]+", text.lower())
        return {w for w in words if w not in _STOPWORDS and len(w) > 1}

    @staticmethod
    def _sentences(text: str) -> list[str]:
        # Simple sentence splitter; good enough for the short KB passages
        # in this dataset without pulling in an NLP-toolkit dependency.
        parts = re.split(r"(?<=[.!?])\s+", text.strip())
        return [p.strip() for p in parts if p.strip()]

    def generate(self, query: str, context: str, system_prompt: str,
                 temperature: float = 0.0, max_tokens: int = 300) -> str:
        del system_prompt, temperature, max_tokens  # unused by this deterministic stub
        query_kw = self._keywords(query)
        if not context.strip() or not query_kw:
            return "The supplied context does not contain sufficient evidence to answer this question."

        best_sentence, best_score = None, 0
        for sentence in self._sentences(context):
            sent_kw = self._keywords(sentence)
            overlap = len(query_kw & sent_kw)
            if overlap > best_score:
                best_sentence, best_score = sentence, overlap

        if best_sentence is None or best_score == 0:
            return "The supplied context does not contain sufficient evidence to answer this question."
        return best_sentence


class AnthropicLLM(LLMInterface):
    """Real generative-model backend. Requires ANTHROPIC_API_KEY."""

    def __init__(self, model: str):
        if not model.strip():
            raise ValueError("A provider-supported llm_model must be configured")
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "llm_backend='anthropic' requires the ANTHROPIC_API_KEY environment "
                "variable to be set. Refusing to silently fall back to a different "
                "backend, since that would make generation-impact metrics misleading "
                "without saying so — set llm_backend='extractive' in config.yaml "
                "instead if you don't have API access."
            )
        import anthropic  # deferred import
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    @property
    def backend_name(self) -> str:
        return f"anthropic:{self._model}"

    def generate(self, query: str, context: str, system_prompt: str,
                 temperature: float = 0.0, max_tokens: int = 300) -> str:
        message = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {query}",
            }],
        )
        return "".join(block.text for block in message.content if block.type == "text").strip()


def get_llm(config) -> LLMInterface:
    if config.llm_backend == "extractive":
        return ExtractiveLLM()
    if config.llm_backend == "anthropic":
        return AnthropicLLM(config.llm_model)
    raise ValueError(f"Unknown llm_backend in config: {config.llm_backend}")
