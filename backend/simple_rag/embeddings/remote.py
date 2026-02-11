"""Remote embedding provider — OpenAI-compatible API."""

from __future__ import annotations

import httpx

from simple_rag.embeddings.base import Embedder


class RemoteEmbedder(Embedder):
    """Call a remote embedding service that exposes an OpenAI-compatible /v1/embeddings endpoint."""

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str = "",
        dim: int = 1024,
        timeout_s: float = 10.0,
        batch_size: int = 128,
    ):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key
        self._dim_val = dim
        self._timeout = timeout_s
        self._batch_size = batch_size

    def embed(self, texts: list[str]) -> list[list[float]]:
        all_vectors: list[list[float]] = []
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i : i + self._batch_size]
            resp = httpx.post(
                f"{self._base_url}/v1/embeddings",
                json={"input": batch, "model": self._model},
                headers={"Authorization": f"Bearer {self._api_key}"} if self._api_key else {},
                timeout=self._timeout,
            )
            resp.raise_for_status()
            data = resp.json()["data"]
            all_vectors.extend([item["embedding"] for item in sorted(data, key=lambda x: x["index"])])
        return all_vectors

    @property
    def dim(self) -> int:
        return self._dim_val

    @property
    def model_id(self) -> str:
        return self._model
