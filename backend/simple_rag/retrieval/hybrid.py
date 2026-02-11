"""Hybrid retriever — fuse Dense + Sparse results via RRF or weighted score."""

from __future__ import annotations

from simple_rag.retrieval.base import Retriever, RetrievalResult


class HybridRetriever(Retriever):
    """Run multiple sub-retrievers in parallel and fuse their results."""

    def __init__(
        self,
        retrievers: list[Retriever],
        fusion: str = "rrf",  # "rrf" | "weighted"
        rrf_k: int = 60,
        weights: list[float] | None = None,
    ):
        self._retrievers = retrievers
        self._fusion = fusion
        self._rrf_k = rrf_k
        self._weights = weights or [1.0] * len(retrievers)

    async def retrieve(self, query: str, top_k: int = 200, filters: dict | None = None) -> list[RetrievalResult]:
        # Collect results from all sub-retrievers
        all_results: list[list[RetrievalResult]] = []
        for retriever in self._retrievers:
            results = await retriever.retrieve(query, top_k=top_k, filters=filters)
            all_results.append(results)

        if self._fusion == "rrf":
            return self._fuse_rrf(all_results, top_k)
        else:
            return self._fuse_weighted(all_results, top_k)

    def _fuse_rrf(self, all_results: list[list[RetrievalResult]], top_k: int) -> list[RetrievalResult]:
        """Reciprocal Rank Fusion: score(d) = sum( 1 / (k + rank_r(d)) )."""
        scores: dict[str, float] = {}
        best_result: dict[str, RetrievalResult] = {}

        for results in all_results:
            for r in results:
                rrf_score = 1.0 / (self._rrf_k + r.rank)
                scores[r.chunk_id] = scores.get(r.chunk_id, 0.0) + rrf_score
                # Keep the result with highest individual score for metadata
                if r.chunk_id not in best_result or r.score > best_result[r.chunk_id].score:
                    best_result[r.chunk_id] = r

        sorted_ids = sorted(scores, key=lambda cid: scores[cid], reverse=True)[:top_k]
        return [
            RetrievalResult(
                chunk_id=cid,
                doc_id=best_result[cid].doc_id,
                text=best_result[cid].text,
                score=scores[cid],
                rank=i + 1,
                source="hybrid",
                metadata=best_result[cid].metadata,
            )
            for i, cid in enumerate(sorted_ids)
        ]

    def _fuse_weighted(self, all_results: list[list[RetrievalResult]], top_k: int) -> list[RetrievalResult]:
        """Weighted score fusion with min-max normalization per retriever."""
        scores: dict[str, float] = {}
        best_result: dict[str, RetrievalResult] = {}

        for weight, results in zip(self._weights, all_results):
            if not results:
                continue
            min_s = min(r.score for r in results)
            max_s = max(r.score for r in results)
            range_s = max_s - min_s if max_s > min_s else 1.0
            for r in results:
                norm_score = (r.score - min_s) / range_s
                scores[r.chunk_id] = scores.get(r.chunk_id, 0.0) + weight * norm_score
                if r.chunk_id not in best_result or r.score > best_result[r.chunk_id].score:
                    best_result[r.chunk_id] = r

        sorted_ids = sorted(scores, key=lambda cid: scores[cid], reverse=True)[:top_k]
        return [
            RetrievalResult(
                chunk_id=cid,
                doc_id=best_result[cid].doc_id,
                text=best_result[cid].text,
                score=scores[cid],
                rank=i + 1,
                source="hybrid",
                metadata=best_result[cid].metadata,
            )
            for i, cid in enumerate(sorted_ids)
        ]
