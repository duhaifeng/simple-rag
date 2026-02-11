"""Reranker abstract base class — cross-encoder / LLM / remote rerank service."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RerankCandidate:
    """A candidate to be reranked."""

    chunk_id: str
    text: str  # typically: title + heading + chunk_text (truncated)
    metadata: dict | None = None


@dataclass
class RerankResult:
    """A reranked candidate."""

    chunk_id: str
    score: float  # higher = more relevant
    rank: int


class Reranker(ABC):
    """All rerank providers must implement this interface."""

    @abstractmethod
    def rerank(self, query: str, candidates: list[RerankCandidate], top_n: int = 20) -> list[RerankResult]:
        """Rerank candidates given a query.

        Args:
            query: the user query.
            candidates: list of candidates (text already truncated by caller).
            top_n: number of results to return after reranking.

        Returns:
            list of RerankResult sorted by score descending, length <= top_n.
        """
        ...

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Unique identifier for this rerank model / service."""
        ...
