"""VectorStore abstract base class — unified interface for pgvector / Qdrant / Milvus etc."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class DistanceMetric(str, Enum):
    COSINE = "cosine"
    IP = "ip"  # inner product
    L2 = "l2"


@dataclass
class IndexSpec:
    """Specification for creating / verifying an index (collection / table)."""

    name: str  # e.g. "my_dataset__bge-m3"
    dimension: int
    metric: DistanceMetric = DistanceMetric.COSINE
    extra_params: dict = field(default_factory=dict)  # HNSW m, ef_construction, etc.


@dataclass
class Point:
    """A single vector point to upsert."""

    id: str
    vector: list[float]
    payload: dict = field(default_factory=dict)  # metadata (doc_id, chunk_index, source, ...)


@dataclass
class QueryResult:
    """A single result from a vector query."""

    id: str
    score: float  # always "higher = more relevant" (adapter layer handles conversion)
    payload: dict = field(default_factory=dict)


class VectorStore(ABC):
    """All vector store backends must implement this interface."""

    @abstractmethod
    async def ensure_index(self, spec: IndexSpec) -> None:
        """Create the index / collection if it does not exist."""
        ...

    @abstractmethod
    async def upsert(self, index_name: str, points: list[Point]) -> int:
        """Batch upsert points. Returns number of points upserted."""
        ...

    @abstractmethod
    async def query(
        self,
        index_name: str,
        vector: list[float],
        top_k: int = 20,
        filters: dict | None = None,
    ) -> list[QueryResult]:
        """Query nearest neighbours. Results are sorted by score descending."""
        ...

    @abstractmethod
    async def delete(self, index_name: str, ids: list[str] | None = None, filters: dict | None = None) -> int:
        """Delete points by ids or filter. Returns number deleted."""
        ...
