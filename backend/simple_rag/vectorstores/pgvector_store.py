"""pgvector VectorStore implementation (PostgreSQL + pgvector extension)."""

from __future__ import annotations

from simple_rag.vectorstores.base import VectorStore, IndexSpec, Point, QueryResult


class PgVectorStore(VectorStore):
    """pgvector-based vector store.

    Uses SQLAlchemy async engine + pgvector operators.
    Each IndexSpec.name maps to a Postgres table.
    """

    def __init__(self, dsn: str):
        self._dsn = dsn
        # TODO: create async engine on first use (lazy init)
        self._engine = None

    async def _get_engine(self):
        if self._engine is None:
            from sqlalchemy.ext.asyncio import create_async_engine

            self._engine = create_async_engine(self._dsn, echo=False)
        return self._engine

    async def ensure_index(self, spec: IndexSpec) -> None:
        """Create table + HNSW index if not exists."""
        engine = await self._get_engine()
        # TODO: CREATE TABLE IF NOT EXISTS ... (id text PK, embedding vector(dim), payload jsonb)
        #       CREATE INDEX ... USING hnsw (embedding vector_cosine_ops)
        pass

    async def upsert(self, index_name: str, points: list[Point]) -> int:
        """INSERT ... ON CONFLICT DO UPDATE."""
        engine = await self._get_engine()
        # TODO: batch upsert with COPY or executemany
        return len(points)

    async def query(
        self,
        index_name: str,
        vector: list[float],
        top_k: int = 20,
        filters: dict | None = None,
    ) -> list[QueryResult]:
        """SELECT ... ORDER BY embedding <=> $query LIMIT $top_k."""
        engine = await self._get_engine()
        # TODO: build query with optional WHERE filters, execute, map to QueryResult
        return []

    async def delete(self, index_name: str, ids: list[str] | None = None, filters: dict | None = None) -> int:
        engine = await self._get_engine()
        # TODO: DELETE FROM ... WHERE ...
        return 0
