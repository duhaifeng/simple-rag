"""MVP document index stored as JSON under storage_dir.

This is intentionally simple to unblock the control plane UI without requiring
DB migrations. It can be replaced later by SQLAlchemy models.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Any

import aiofiles

_LOCK = asyncio.Lock()


def new_doc_id() -> str:
    return uuid.uuid4().hex


def _now_ms() -> int:
    return int(time.time() * 1000)


def _base(storage_dir: str) -> Path:
    p = Path(storage_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _index_path(storage_dir: str) -> Path:
    return _base(storage_dir) / "documents.json"


async def _load_index(storage_dir: str) -> dict[str, Any]:
    path = _index_path(storage_dir)
    if not path.exists():
        return {"documents": []}

    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        raw = await f.read()
    if not raw.strip():
        return {"documents": []}

    try:
        data = json.loads(raw)
        if isinstance(data, dict) and isinstance(data.get("documents"), list):
            return data
    except json.JSONDecodeError:
        pass

    return {"documents": []}


async def _save_index(storage_dir: str, data: dict[str, Any]) -> None:
    path = _index_path(storage_dir)
    tmp = path.with_suffix(".tmp")
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    async with aiofiles.open(tmp, "w", encoding="utf-8") as f:
        await f.write(payload)
    tmp.replace(path)


def _find_doc(index: dict[str, Any], doc_id: str) -> dict[str, Any] | None:
    for d in index.get("documents", []):
        if d.get("doc_id") == doc_id:
            return d
    return None


async def create_document(
    storage_dir: str,
    *,
    doc_id: str,
    filename: str,
    raw_path: str,
    status: str = "queued",
) -> dict[str, Any]:
    async with _LOCK:
        index = await _load_index(storage_dir)
        now = _now_ms()
        doc = {
            "doc_id": doc_id,
            "filename": filename,
            "status": status,
            "raw_path": raw_path,
            "chunks_path": None,
            "error": None,
            "created_at_ms": now,
            "updated_at_ms": now,
        }
        index["documents"].insert(0, doc)
        await _save_index(storage_dir, index)
        return doc


async def list_documents(storage_dir: str, *, page: int = 1, page_size: int = 20) -> dict[str, Any]:
    async with _LOCK:
        index = await _load_index(storage_dir)
        docs = list(index.get("documents", []))

    docs.sort(key=lambda d: int(d.get("created_at_ms") or 0), reverse=True)
    total = len(docs)
    page = max(1, int(page))
    page_size = min(200, max(1, int(page_size)))
    start = (page - 1) * page_size
    return {"documents": docs[start : start + page_size], "total": total, "page": page, "page_size": page_size}


async def set_status(storage_dir: str, doc_id: str, status: str, *, error: str | None = None) -> None:
    async with _LOCK:
        index = await _load_index(storage_dir)
        doc = _find_doc(index, doc_id)
        if not doc:
            return
        doc["status"] = status
        doc["updated_at_ms"] = _now_ms()
        doc["error"] = error
        await _save_index(storage_dir, index)


async def set_chunks_path(storage_dir: str, doc_id: str, chunks_path: str) -> None:
    async with _LOCK:
        index = await _load_index(storage_dir)
        doc = _find_doc(index, doc_id)
        if not doc:
            return
        doc["chunks_path"] = chunks_path
        doc["updated_at_ms"] = _now_ms()
        await _save_index(storage_dir, index)


async def delete_document(storage_dir: str, doc_id: str) -> dict[str, Any] | None:
    async with _LOCK:
        index = await _load_index(storage_dir)
        docs = index.get("documents", [])
        for i, d in enumerate(docs):
            if d.get("doc_id") == doc_id:
                removed = docs.pop(i)
                await _save_index(storage_dir, index)
                return removed
    return None


async def write_chunks(storage_dir: str, doc_id: str, chunks: list[dict[str, Any]]) -> str:
    base = _base(storage_dir)
    dest_dir = base / "parsed" / doc_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "chunks.json"

    payload = json.dumps({"chunks": chunks}, ensure_ascii=False, indent=2)
    async with aiofiles.open(dest, "w", encoding="utf-8") as f:
        await f.write(payload)

    rel = str(dest.relative_to(base))
    await set_chunks_path(storage_dir, doc_id, rel)
    return rel


async def read_chunks(storage_dir: str, doc_id: str) -> list[dict[str, Any]]:
    base = _base(storage_dir)
    path = base / "parsed" / doc_id / "chunks.json"
    if not path.exists():
        return []
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        raw = await f.read()
    try:
        data = json.loads(raw)
        chunks = data.get("chunks", [])
        if isinstance(chunks, list):
            return chunks
    except json.JSONDecodeError:
        return []
    return []

