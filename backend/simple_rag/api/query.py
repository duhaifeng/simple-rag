"""Query API — online retrieval / QA endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from simple_rag.api.schemas import QueryRequest, QueryResponse
from simple_rag.config.settings import get_settings
from simple_rag.retrieval.dense import DenseRetriever
from simple_rag.retrieval.hybrid import HybridRetriever
from simple_rag.retrieval.sparse import SparseRetriever
from simple_rag.retrieval.bm25.engine import BM25Engine
from simple_rag.runtime.providers import get_embedder, get_retrieval_profile, get_vector_index_spec, get_vector_store
from simple_rag.services.query_service import QueryService
from simple_rag.storage.documents import list_documents as list_documents_store, read_chunks

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    """Run retrieval (dense + sparse hybrid) with optional rerank."""
    settings = get_settings()
    retrieval = get_retrieval_profile(req.retrieval_profile)
    rconf = retrieval["conf"]
    strategy = (rconf.get("strategy") or "hybrid").lower()

    top_n = req.top_n or int(rconf.get("topn", 20) or 20)
    top_k = req.top_k or int(max(rconf.get("dense_topk", 200) or 200, rconf.get("sparse_topk", 200) or 200))

    # Build corpus chunks from local artifacts (MVP)
    docs_resp = await list_documents_store(settings.storage_dir, page=1, page_size=10_000)
    docs = docs_resp.get("documents", [])
    done_docs = [d for d in docs if d.get("status") == "done"]
    all_chunks: list[dict] = []
    for d in done_docs:
        doc_id = d.get("doc_id") or ""
        if doc_id:
            all_chunks.extend(await read_chunks(settings.storage_dir, doc_id))

    debug: dict = {
        "retrieval_profile": retrieval["name"],
        "strategy": strategy,
        "docs_total": len(docs),
        "docs_done": len(done_docs),
        "chunks_loaded": len(all_chunks),
    }

    # Sparse retriever (BM25)
    sparse_engine = BM25Engine()
    sparse_engine.add_documents(all_chunks)
    sparse = SparseRetriever(sparse_engine)
    debug.update({"bm25_docs": sparse_engine.num_documents, "bm25_terms": sparse_engine.num_terms})

    # Choose retriever by strategy
    dense_error: str | None = None
    dense = None
    need_dense = strategy in {"dense", "hybrid"}
    if need_dense:
        # Dense retriever (pgvector)
        try:
            embedder = get_embedder()
            vector_store = get_vector_store()
            index_spec = get_vector_index_spec()
            await vector_store.ensure_index(index_spec)
            dense = DenseRetriever(embedder=embedder, vector_store=vector_store, index_name=index_spec.name)
            debug.update({"vector_index": index_spec.name, "embedder_model": embedder.model_id, "embedder_dim": embedder.dim})
        except Exception as e:  # noqa: BLE001
            dense_error = str(e)
            debug["dense_error"] = dense_error
    else:
        debug["dense_skipped"] = True

    if strategy == "dense":
        if dense is None:
            # Keep API usable: fall back to sparse
            retriever = sparse
            debug["fallback"] = "dense_unavailable -> sparse"
        else:
            retriever = dense
    elif strategy == "sparse":
        retriever = sparse
    else:
        if dense is None:
            retriever = sparse
            debug["fallback"] = "hybrid_dense_unavailable -> sparse"
        else:
            fusion = (rconf.get("fusion") or "rrf").lower()
            rrf_k = int(rconf.get("rrf_k", 60) or 60)
            retriever = HybridRetriever([dense, sparse], fusion=fusion, rrf_k=rrf_k)

    service = QueryService(retriever=retriever, reranker=None)
    hits = await service.search(req.query, top_k=top_k, top_n=top_n, filters=req.filters, enable_rerank=False)

    results = [
        {
            "chunk_id": h.chunk_id,
            "doc_id": h.doc_id,
            "text": h.text,
            "score": float(h.score),
            "rank": int(h.rank),
            "source": h.source,
            "metadata": h.metadata,
        }
        for h in hits
    ]

    return QueryResponse(query=req.query, results=results, debug=debug)
