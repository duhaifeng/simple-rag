"""Remote reranker — calls an external rerank service via HTTP."""

from __future__ import annotations

import httpx

from simple_rag.rerank.base import Reranker, RerankCandidate, RerankResult


class RemoteReranker(Reranker):
    """Call a remote rerank API (batch endpoint)."""

    def __init__(
        self,
        url: str,
        api_key: str = "",
        model: str = "default",
        timeout_ms: int = 800,
        batch_size: int = 64,
        on_timeout: str = "fallback_to_unreranked",
    ):
        self._url = url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout_ms / 1000.0
        self._batch_size = batch_size
        self._on_timeout = on_timeout

    def rerank(self, query: str, candidates: list[RerankCandidate], top_n: int = 20) -> list[RerankResult]:
        if not candidates:
            return []

        payload = {
            "query": query,
            "documents": [c.text for c in candidates],
            "model": self._model,
            "top_n": top_n,
        }

        try:
            resp = httpx.post(
                f"{self._url}/rerank",
                json=payload,
                headers={"Authorization": f"Bearer {self._api_key}"} if self._api_key else {},
                timeout=self._timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            return [
                RerankResult(
                    chunk_id=candidates[item["index"]].chunk_id,
                    score=item["relevance_score"],
                    rank=i + 1,
                )
                for i, item in enumerate(data["results"][:top_n])
            ]
        except (httpx.TimeoutException, httpx.HTTPStatusError):
            if self._on_timeout == "fallback_to_unreranked":
                # Fallback: return original order with dummy scores
                return [
                    RerankResult(chunk_id=c.chunk_id, score=0.0, rank=i + 1)
                    for i, c in enumerate(candidates[:top_n])
                ]
            raise

    @property
    def model_id(self) -> str:
        return self._model
