"""Deterministic text preprocessing.

Section 8 is explicit that the SAME function must run on legitimate and
poisoned text — a preprocessing path that treats poisoned text specially
would give the attack (or the defense) an artificial advantage that
wouldn't exist in a real deployment.
"""
from __future__ import annotations

import re
import unicodedata


def normalize_whitespace(text: str) -> str:
    """Collapse runs of whitespace and strip leading/trailing space."""
    return re.sub(r"\s+", " ", text).strip()


def clean_text(text: str) -> str:
    """Deterministic cleaning applied identically to clean and poisoned text.

    - Unicode NFC normalization (stable across platforms/encodings).
    - Strip control characters (but keep normal punctuation/diacritics).
    - Collapse whitespace.

    Deliberately does NOT lowercase, strip stopwords, or otherwise destroy
    information — the embedding model (or hashing fallback) handles
    normalization for retrieval purposes; this function only removes noise
    that would never carry meaning.
    """
    text = unicodedata.normalize("NFC", text)
    text = "".join(ch for ch in text if ch == "\n" or ch == "\t" or not unicodedata.category(ch).startswith("C"))
    return normalize_whitespace(text)
