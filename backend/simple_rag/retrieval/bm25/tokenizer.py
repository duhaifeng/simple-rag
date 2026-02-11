"""Tokenizer abstraction — pluggable Chinese/English text segmentation."""

from __future__ import annotations

import re
import unicodedata
from abc import ABC, abstractmethod
from pathlib import Path


class Tokenizer(ABC):
    """Base tokenizer interface."""

    @abstractmethod
    def tokenize(self, text: str) -> list[str]:
        """Split text into tokens (terms)."""
        ...


class JiebaTokenizer(Tokenizer):
    """Chinese + English tokenizer based on jieba.

    Features:
    - NFKC Unicode normalization (fullwidth/halfwidth, compatibility chars)
    - Whitespace collapsing
    - Optional lowercasing (default True for BM25)
    - Optional custom dictionary
    - Optional stopwords
    """

    def __init__(
        self,
        user_dict_path: str | None = None,
        stopwords_path: str | None = None,
        lowercase: bool = True,
        min_token_len: int = 1,
    ):
        import jieba

        self._jieba = jieba
        self._lowercase = lowercase
        self._min_token_len = min_token_len

        if user_dict_path and Path(user_dict_path).exists():
            self._jieba.load_userdict(user_dict_path)

        self._stopwords: set[str] = set()
        if stopwords_path and Path(stopwords_path).exists():
            with open(stopwords_path, "r", encoding="utf-8") as f:
                self._stopwords = {line.strip() for line in f if line.strip()}

    def _normalize(self, text: str) -> str:
        """NFKC normalization + whitespace collapsing."""
        text = unicodedata.normalize("NFKC", text)
        text = re.sub(r"\s+", " ", text).strip()
        if self._lowercase:
            text = text.lower()
        return text

    def tokenize(self, text: str) -> list[str]:
        text = self._normalize(text)
        tokens = self._jieba.lcut(text)
        return [
            t
            for t in tokens
            if len(t) >= self._min_token_len and t.strip() and t not in self._stopwords
        ]
