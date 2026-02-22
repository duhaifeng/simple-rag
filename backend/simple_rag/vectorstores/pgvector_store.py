"""pgvector VectorStore implementation (PostgreSQL + pgvector extension)."""

from __future__ import annotations

import json
import re

from sqlalchemy import text

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
        index_name = _safe_ident(spec.name)
        dim = int(spec.dimension)
        ops = _metric_ops(spec.metric.value)
        hnsw_m = int(spec.extra_params.get("m", 16))
        hnsw_ef = int(spec.extra_params.get("ef_construction", 64))

        async with engine.begin() as conn:
            # pgvector extension (may require privileges; ignore failures)
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            except Exception:  # noqa: BLE001
                pass

            await conn.execute(
                text(
                    f"""
CREATE TABLE IF NOT EXISTS {index_name} (
  id TEXT PRIMARY KEY,
  embedding vector({dim}) NOT NULL,
  payload JSONB NOT NULL DEFAULT '{{}}'::jsonb
)
""".strip()
                )
            )

            # HNSW index if available (pgvector >= 0.5); fall back to ivfflat
            try:
                await conn.execute(
                    text(
                        f"""
CREATE INDEX IF NOT EXISTS {index_name}__embedding_hnsw
ON {index_name}
USING hnsw (embedding {ops})
WITH (m={hnsw_m}, ef_construction={hnsw_ef})
""".strip()
                    )
                )
            except Exception:  # noqa: BLE001
                try:
                    await conn.execute(
                        text(
                            f"""
CREATE INDEX IF NOT EXISTS {index_name}__embedding_ivfflat
ON {index_name}
USING ivfflat (embedding {ops})
WITH (lists=100)
""".strip()
                        )
                    )
                except Exception:  # noqa: BLE001
                    # Index creation is optional for correctness
                    pass

    async def upsert(self, index_name: str, points: list[Point]) -> int:
        """INSERT ... ON CONFLICT DO UPDATE."""
        engine = await self._get_engine()
        if not points:
            return 0

        index_name = _safe_ident(index_name)
        rows = [
            {
                "id": p.id,
                "embedding": _vector_literal(p.vector),
                "payload": json.dumps(p.payload or {}, ensure_ascii=False),
            }
            for p in points
        ]

        sql = f"""
INSERT INTO {index_name} (id, embedding, payload)
VALUES (:id, (:embedding)::vector, (:payload)::jsonb)
ON CONFLICT (id) DO UPDATE
SET embedding = EXCLUDED.embedding,
    payload = EXCLUDED.payload
"""
        async with engine.begin() as conn:
            await conn.execute(text(sql), rows)
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
        index_name = _safe_ident(index_name)
        top_k = max(1, min(200, int(top_k)))

        params: dict[str, object] = {"qv": _vector_literal(vector), "top_k": top_k}
        where = ""
        if filters and "doc_id" in filters and filters["doc_id"] is not None:
            params["doc_id"] = str(filters["doc_id"])
            where = "WHERE payload->>'doc_id' = :doc_id"

        # Cosine distance: <=> (smaller better); return score = 1 - distance
        sql = f"""
SELECT id,
       payload,
       (1 - (embedding <=> (:qv)::vector)) AS score
FROM {index_name}
{where}
ORDER BY embedding <=> (:qv)::vector
LIMIT :top_k
"""
        async with engine.connect() as conn:
            result = await conn.execute(text(sql), params)
            rows = result.fetchall()

        out: list[QueryResult] = []
        for r in rows:
            out.append(QueryResult(id=r[0], score=float(r[2]), payload=r[1] or {}))
        return out

    async def delete(self, index_name: str, ids: list[str] | None = None, filters: dict | None = None) -> int:
        engine = await self._get_engine()
        index_name = _safe_ident(index_name)
        params: dict[str, object] = {}
        where_clauses: list[str] = []

        if ids:
            params["ids"] = [str(i) for i in ids]
            where_clauses.append("id = ANY(:ids)")

        if filters and "doc_id" in filters and filters["doc_id"] is not None:
            params["doc_id"] = str(filters["doc_id"])
            where_clauses.append("payload->>'doc_id' = :doc_id")

        if not where_clauses:
            return 0

        where = " AND ".join(where_clauses)
        sql = f"DELETE FROM {index_name} WHERE {where}"
        async with engine.begin() as conn:
            res = await conn.execute(text(sql), params)
            return int(res.rowcount or 0)


_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _safe_ident(name: str) -> str:
    if not isinstance(name, str) or not name:
        raise ValueError("index_name must be non-empty string")
    if not _IDENT_RE.match(name):
        raise ValueError(f"unsafe index name: {name!r}")
    return name


def _metric_ops(metric: str) -> str:
    m = (metric or "").lower()
    if m == "cosine":
        return "vector_cosine_ops"
    if m in {"ip", "inner_product"}:
        return "vector_ip_ops"
    if m in {"l2", "euclidean"}:
        return "vector_l2_ops"
    return "vector_cosine_ops"


def _vector_literal(vec: list[float]) -> str:
    # pgvector accepts '[1,2,3]' input format
    return "[" + ",".join(f"{float(x):.10f}" for x in vec) + "]"
