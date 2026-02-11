"""Pydantic schemas for API request / response."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---- Query API ----

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User query text")
    retrieval_profile: str | None = Field(None, description="Override active retrieval profile")
    rerank_profile: str | None = Field(None, description="Override active rerank profile")
    top_k: int | None = Field(None, ge=1, le=1000, description="Override dense/sparse topK")
    top_n: int | None = Field(None, ge=1, le=200, description="Override final topN")
    filters: dict | None = Field(None, description="Metadata filters (key-value)")


class ChunkResult(BaseModel):
    chunk_id: str
    doc_id: str
    text: str
    score: float
    rank: int
    source: str | None = None
    metadata: dict | None = None


class QueryResponse(BaseModel):
    query: str
    rewritten_query: str | None = None
    results: list[ChunkResult]
    debug: dict | None = None  # timing, profiles used, per-stage candidates, etc.


# ---- Document / Ingest API ----

class DocumentUploadResponse(BaseModel):
    doc_id: str
    filename: str
    status: str  # "queued" | "processing" | "done" | "error"


# ---- Profile API ----

class ProfileInfo(BaseModel):
    name: str
    provider: str
    active: bool = False
    config: dict | None = None
