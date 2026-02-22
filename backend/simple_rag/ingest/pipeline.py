"""Document ingest pipeline (MVP).

Uploads are stored to local storage, parsed into text (limited file types),
chunked, and saved as JSON artifacts. Status is updated in the document index.
"""

from __future__ import annotations

import html as _html
import json
import re
from pathlib import Path

from simple_rag.ingest.chunker import SimpleOverlapChunker
from simple_rag.runtime.providers import get_embedder, get_vector_index_spec, get_vector_store
from simple_rag.storage.documents import list_documents as list_documents_store, read_chunks, set_status, write_chunks
from simple_rag.storage.local import LocalStorage
from simple_rag.vectorstores.base import Point


def _extract_text(filename: str, content: bytes) -> str:
    ext = Path(filename).suffix.lower()
    text_exts = {".txt", ".md", ".markdown", ".log", ".csv", ".json", ".html", ".htm"}
    if ext not in text_exts:
        raise ValueError(f"unsupported_file_type: {ext or '(no extension)'}")

    raw = content.decode("utf-8", errors="ignore")

    if ext == ".json":
        try:
            obj = json.loads(raw)
            return json.dumps(obj, ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            return raw

    if ext in {".html", ".htm"}:
        raw = _html.unescape(raw)
        raw = re.sub(r"<script[\\s\\S]*?</script>", " ", raw, flags=re.IGNORECASE)
        raw = re.sub(r"<style[\\s\\S]*?</style>", " ", raw, flags=re.IGNORECASE)
        raw = re.sub(r"<[^>]+>", " ", raw)
        raw = re.sub(r"\\s+", " ", raw).strip()
        return raw

    return raw


async def process_document(storage_dir: str, doc_id: str, filename: str) -> None:
    """Background task: parse -> chunk -> save artifacts -> update status."""
    await set_status(storage_dir, doc_id, "processing")
    storage = LocalStorage(base_dir=storage_dir)

    try:
        content = await storage.read_raw(doc_id, filename)
        text = _extract_text(filename, content)
        chunker = SimpleOverlapChunker(chunk_size=500, overlap=100)
        chunks = chunker.chunk(doc_id=doc_id, text=text, metadata={"filename": filename})
        chunk_dicts = [
            {
                "chunk_id": c.chunk_id,
                "doc_id": c.doc_id,
                "chunk_index": c.chunk_index,
                "text": c.text,
                "content_hash": c.content_hash,
                "chunker_version": c.chunker_version,
                "metadata": c.metadata,
            }
            for c in chunks
        ]
        await write_chunks(storage_dir, doc_id, chunk_dicts)

        # ---- Vector index (pgvector) ----
        embedder = get_embedder()
        index_spec = get_vector_index_spec()
        vector_store = get_vector_store()
        await vector_store.ensure_index(index_spec)

        texts = [c["text"] for c in chunk_dicts]
        vectors = embedder.embed(texts)
        points = [
            Point(
                id=c["chunk_id"],
                vector=vectors[i],
                payload={
                    "doc_id": c["doc_id"],
                    "chunk_id": c["chunk_id"],
                    "chunk_index": c["chunk_index"],
                    "text": c["text"],
                    **(c.get("metadata") or {}),
                },
            )
            for i, c in enumerate(chunk_dicts)
        ]

        # Upsert in batches to avoid huge SQL packets
        batch = 128
        for i in range(0, len(points), batch):
            await vector_store.upsert(index_spec.name, points[i : i + batch])

        await set_status(storage_dir, doc_id, "done")
    except Exception as e:  # noqa: BLE001 - surface message to UI
        await set_status(storage_dir, doc_id, "error", error=str(e))


async def reindex_all_vectors(storage_dir: str) -> dict[str, int]:
    """(Re)build vector index for all documents that already have chunks artifacts."""
    embedder = get_embedder()
    index_spec = get_vector_index_spec()
    vector_store = get_vector_store()
    await vector_store.ensure_index(index_spec)

    docs_resp = await list_documents_store(storage_dir, page=1, page_size=100_000)
    docs = docs_resp.get("documents", [])
    done_docs = [d for d in docs if d.get("status") == "done"]

    total_chunks = 0
    total_points = 0
    batch_points: list[Point] = []
    batch_texts: list[str] = []

    async def _flush():
        nonlocal total_points
        if not batch_points:
            return
        vectors = embedder.embed(batch_texts)
        for i, v in enumerate(vectors):
            batch_points[i].vector = v
        await vector_store.upsert(index_spec.name, batch_points)
        total_points += len(batch_points)
        batch_points.clear()
        batch_texts.clear()

    for d in done_docs:
        doc_id = d.get("doc_id") or ""
        if not doc_id:
            continue
        chunks = await read_chunks(storage_dir, doc_id)
        total_chunks += len(chunks)
        for c in chunks:
            payload = c.get("metadata", {}) or {}
            payload.update(
                {
                    "doc_id": c.get("doc_id", doc_id),
                    "chunk_id": c.get("chunk_id", ""),
                    "chunk_index": c.get("chunk_index", 0),
                    "text": c.get("text", ""),
                }
            )
            batch_points.append(Point(id=str(c.get("chunk_id")), vector=[], payload=payload))
            batch_texts.append(str(c.get("text", "")))
            if len(batch_points) >= 128:
                await _flush()

    await _flush()
    return {"docs": len(done_docs), "chunks": total_chunks, "points": total_points}

