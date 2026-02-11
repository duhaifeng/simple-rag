"""Dense retriever — vector similarity search via Embedder + VectorStore."""

from __future__ import annotations

from simple_rag.embeddings.base import Embedder
from simple_rag.vectorstores.base import VectorStore
from simple_rag.retrieval.base import Retriever, RetrievalResult


class DenseRetriever(Retriever):
    """Embed the query and search the vector store."""

    def __init__(self, embedder: Embedder, vector_store: VectorStore, index_name: str):
        self._embedder = embedder
        self._vector_store = vector_store
        self._index_name = index_name

    async def retrieve(self, query: str, top_k: int = 200, filters: dict | None = None) -> list[RetrievalResult]:
        query_vector = self._embedder.embed([query])[0]
        vs_results = await self._vector_store.query(self._index_name, query_vector, top_k=top_k, filters=filters)
        return [
            RetrievalResult(
                chunk_id=r.id,
                doc_id=r.payload.get("doc_id", ""),
                text=r.payload.get("text", ""),
                score=r.score,
                rank=i + 1,
                source="dense",
                metadata=r.payload,
            )
            for i, r in enumerate(vs_results)
        ]
