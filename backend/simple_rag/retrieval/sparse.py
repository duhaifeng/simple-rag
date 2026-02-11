"""Sparse retriever — BM25 based retrieval."""

from __future__ import annotations

from simple_rag.retrieval.base import Retriever, RetrievalResult
from simple_rag.retrieval.bm25.engine import BM25Engine


class SparseRetriever(Retriever):
    """Use the BM25 engine (inverted index + Okapi BM25 scoring) for sparse retrieval."""

    def __init__(self, bm25_engine: BM25Engine):
        self._engine = bm25_engine

    async def retrieve(self, query: str, top_k: int = 200, filters: dict | None = None) -> list[RetrievalResult]:
        results = self._engine.search(query, top_k=top_k)
        return [
            RetrievalResult(
                chunk_id=r["chunk_id"],
                doc_id=r.get("doc_id", ""),
                text=r.get("text", ""),
                score=r["score"],
                rank=i + 1,
                source="sparse",
                metadata=r.get("metadata", {}),
            )
            for i, r in enumerate(results)
        ]
