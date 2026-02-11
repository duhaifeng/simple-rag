"""Retriever abstract base class — dense / sparse / hybrid."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class RetrievalResult:
    """A single candidate from retrieval."""

    chunk_id: str
    doc_id: str
    text: str
    score: float
    rank: int
    source: str = ""  # "dense" | "sparse" | "hybrid"
    metadata: dict = field(default_factory=dict)


class Retriever(ABC):
    """All retriever implementations (dense, sparse, hybrid) implement this."""

    @abstractmethod
    async def retrieve(self, query: str, top_k: int = 200, filters: dict | None = None) -> list[RetrievalResult]:
        """Retrieve top-K candidates for the given query.

        Args:
            query: raw or rewritten query text.
            top_k: max number of candidates to return.
            filters: metadata filters.

        Returns:
            list of RetrievalResult sorted by score descending.
        """
        ...
