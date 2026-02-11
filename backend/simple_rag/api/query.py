"""Query API — online retrieval / QA endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from simple_rag.api.schemas import QueryRequest, QueryResponse

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    """Run retrieval (dense + sparse hybrid) with optional rerank."""
    # TODO: wire to QueryService
    return QueryResponse(
        query=req.query,
        results=[],
        debug={"message": "not yet implemented"},
    )
