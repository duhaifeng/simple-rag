"""Text normalization utilities for retrieval pipeline."""

from __future__ import annotations

import re
import unicodedata


def normalize_text(text: str, lowercase: bool = False) -> str:
    """Standard text normalization for the retrieval pipeline.

    Steps:
    1. NFKC Unicode normalization (fullwidth/halfwidth, compatibility characters)
    2. Whitespace collapsing (multiple spaces/newlines -> single space)
    3. Optional lowercasing

    Note: this is used for indexing / retrieval / cache key computation.
    Original text should be preserved separately.
    """
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text).strip()
    if lowercase:
        text = text.lower()
    return text


def content_hash(text: str) -> str:
    """Compute a stable hash of normalized text — for dedup & embedding cache."""
    import hashlib

    normalized = normalize_text(text, lowercase=False)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
