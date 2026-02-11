"""Local cross-encoder reranker — loads model via sentence-transformers."""

from __future__ import annotations

from simple_rag.rerank.base import Reranker, RerankCandidate, RerankResult


class LocalCrossEncoderReranker(Reranker):
    """Run a cross-encoder reranker locally (CPU or MPS)."""

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-base",
        batch_size: int = 8,
        max_input_chars: int = 600,
        device: str = "cpu",
    ):
        from sentence_transformers import CrossEncoder

        self._model_name = model_name
        self._batch_size = batch_size
        self._max_input_chars = max_input_chars
        self._model = CrossEncoder(model_name, device=device)

    def rerank(self, query: str, candidates: list[RerankCandidate], top_n: int = 20) -> list[RerankResult]:
        if not candidates:
            return []

        # Build (query, truncated_text) pairs
        pairs = [(query, c.text[: self._max_input_chars]) for c in candidates]

        # Score in batches
        scores = self._model.predict(pairs, batch_size=self._batch_size, show_progress_bar=False)

        # Pair scores with chunk_ids, sort descending, take top_n
        scored = sorted(
            zip(candidates, scores.tolist() if hasattr(scores, "tolist") else list(scores)),
            key=lambda x: x[1],
            reverse=True,
        )[:top_n]

        return [
            RerankResult(chunk_id=c.chunk_id, score=s, rank=i + 1)
            for i, (c, s) in enumerate(scored)
        ]

    @property
    def model_id(self) -> str:
        return self._model_name
