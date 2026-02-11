"""Control Plane API — profiles, documents, experiments."""

from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, BackgroundTasks

from simple_rag.api.schemas import DocumentUploadResponse, ProfileInfo

router = APIRouter()


# ---- Profiles ----

@router.get("/profiles", response_model=dict)
async def list_profiles():
    """List all profile groups (embedding, vector_store, retrieval, rerank)."""
    # TODO: wire to ProfileRegistry
    return {"message": "not yet implemented"}


# ---- Documents / Ingest ----

@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """Upload a document and queue parsing + indexing."""
    # TODO: save file, create document record, dispatch background task
    return DocumentUploadResponse(doc_id="todo", filename=file.filename or "unknown", status="queued")


# ---- Chunks ----

@router.get("/chunks")
async def list_chunks(doc_id: str | None = None, page: int = 1, page_size: int = 20):
    """List / preview chunks (optionally filtered by doc_id)."""
    # TODO: wire to DB
    return {"chunks": [], "total": 0, "page": page, "page_size": page_size}


# ---- Experiments ----

@router.get("/experiments")
async def list_experiments():
    """List experiment runs for recall testing / A-B comparison."""
    # TODO: wire to DB
    return {"experiments": []}
