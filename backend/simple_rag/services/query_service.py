"""QueryService — orchestrates retrieval + rerank pipeline."""

from __future__ import annotations

from simple_rag.retrieval.base import Retriever, RetrievalResult
from simple_rag.rerank.base import Reranker, RerankCandidate


class QueryService:
    """High-level service that wires Retriever + Reranker (optional)."""

    def __init__(self, retriever: Retriever, reranker: Reranker | None = None):
        self._retriever = retriever
        self._reranker = reranker

    async def search(
        self,
        query: str,
        top_k: int = 200,
        top_n: int = 20,
        filters: dict | None = None,
        enable_rerank: bool = True,
    ) -> list[RetrievalResult]:
        """Run full retrieval pipeline: retrieve -> (optional rerank) -> return top_n."""
        candidates = await self._retriever.retrieve(query, top_k=top_k, filters=filters)

        if enable_rerank and self._reranker and candidates:
            rerank_candidates = [
                RerankCandidate(chunk_id=c.chunk_id, text=c.text, metadata=c.metadata)
                for c in candidates
            ]
            reranked = self._reranker.rerank(query, rerank_candidates, top_n=top_n)

            # Map rerank results back to full RetrievalResult
            candidates_map = {c.chunk_id: c for c in candidates}
            results = []
            for rr in reranked:
                orig = candidates_map.get(rr.chunk_id)
                if orig:
                    results.append(
                        RetrievalResult(
                            chunk_id=rr.chunk_id,
                            doc_id=orig.doc_id,
                            text=orig.text,
                            score=rr.score,
                            rank=rr.rank,
                            source=orig.source,
                            metadata=orig.metadata,
                        )
                    )
            return results

        return candidates[:top_n]
