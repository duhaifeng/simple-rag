"""Control Plane API — profiles, documents, experiments."""

from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException

from simple_rag.api.schemas import DocumentUploadResponse, ProfileInfo
from simple_rag.config.settings import get_settings, load_profiles
from simple_rag.ingest.pipeline import process_document, reindex_all_vectors
from simple_rag.storage.documents import (
    create_document,
    delete_document as delete_document_record,
    list_documents as list_documents_store,
    new_doc_id,
    read_chunks,
)
from simple_rag.storage.local import LocalStorage

router = APIRouter()


# ---- Profiles ----

@router.get("/profiles")
async def list_profiles():
    """List all profile groups (embedding, vector_store, retrieval, rerank)."""
    raw = load_profiles()
    result: dict[str, dict] = {}

    for group_name, group_data in raw.items():
        active = group_data.get("active", "")
        profiles_dict = group_data.get("profiles", {})
        profile_list = []
        for prof_name, prof_conf in profiles_dict.items():
            conf = dict(prof_conf) if isinstance(prof_conf, dict) else {}
            provider = conf.pop("provider", "")
            profile_list.append(
                ProfileInfo(
                    name=prof_name,
                    provider=provider,
                    active=(prof_name == active),
                    config=conf,
                ).model_dump()
            )
        result[group_name] = {
            "active": active,
            "profiles": profile_list,
        }

    return result


# ---- Documents / Ingest ----

@router.get("/documents")
async def list_documents(page: int = 1, page_size: int = 20):
    """List uploaded documents with parsing status."""
    settings = get_settings()
    return await list_documents_store(settings.storage_dir, page=page, page_size=page_size)


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """Upload a document and queue parsing + indexing."""
    settings = get_settings()
    filename = file.filename or "unknown"
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="empty file")

    doc_id = new_doc_id()
    storage = LocalStorage(base_dir=settings.storage_dir)
    raw_relpath = await storage.save_raw(doc_id, filename, content)
    await create_document(settings.storage_dir, doc_id=doc_id, filename=filename, raw_path=raw_relpath, status="queued")

    background_tasks.add_task(process_document, settings.storage_dir, doc_id, filename)
    return DocumentUploadResponse(doc_id=doc_id, filename=filename, status="queued")


@router.post("/documents/reindex_vectors")
async def reindex_vectors(background_tasks: BackgroundTasks):
    """Rebuild vector index for all already-parsed documents."""
    settings = get_settings()
    background_tasks.add_task(reindex_all_vectors, settings.storage_dir)
    return {"ok": True, "status": "queued"}


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document and its chunks."""
    settings = get_settings()
    removed = await delete_document_record(settings.storage_dir, doc_id)
    if not removed:
        raise HTTPException(status_code=404, detail="document not found")
    LocalStorage(base_dir=settings.storage_dir).delete_doc(doc_id)
    return {"ok": True}


# ---- Chunks ----

@router.get("/chunks")
async def list_chunks(doc_id: str | None = None, page: int = 1, page_size: int = 20):
    """List / preview chunks (optionally filtered by doc_id)."""
    settings = get_settings()
    if not doc_id:
        return {"chunks": [], "total": 0, "page": page, "page_size": page_size}

    chunks = await read_chunks(settings.storage_dir, doc_id)
    total = len(chunks)
    page = max(1, int(page))
    page_size = min(200, max(1, int(page_size)))
    start = (page - 1) * page_size
    return {"chunks": chunks[start : start + page_size], "total": total, "page": page, "page_size": page_size}


# ---- Experiments ----

@router.get("/experiments")
async def list_experiments():
    """List experiment runs for recall testing / A-B comparison."""
    # TODO: wire to DB
    return {"experiments": []}
