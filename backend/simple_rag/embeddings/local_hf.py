"""Local HuggingFace / sentence-transformers embedding provider."""

from __future__ import annotations

from simple_rag.embeddings.base import Embedder


class LocalHFEmbedder(Embedder):
    """Load an open-source embedding model locally via sentence-transformers."""

    def __init__(self, model_name: str = "BAAI/bge-m3", batch_size: int = 16, device: str = "cpu"):
        from sentence_transformers import SentenceTransformer

        self._model_name = model_name
        self._batch_size = batch_size
        self._model = SentenceTransformer(model_name, device=device)
        self._dim = self._model.get_sentence_embedding_dimension()

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(texts, batch_size=self._batch_size, normalize_embeddings=True, show_progress_bar=False)
        return vectors.tolist()

    @property
    def dim(self) -> int:
        return self._dim

    @property
    def model_id(self) -> str:
        return self._model_name
