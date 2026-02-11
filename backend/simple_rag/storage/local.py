"""Local file storage — MVP object storage (S3-compatible interface reserved)."""

from __future__ import annotations

import shutil
from pathlib import Path

import aiofiles


class LocalStorage:
    """Store raw documents and parsed artifacts on the local filesystem.

    Directory layout:
        {base_dir}/
          raw/{doc_id}/{filename}
          parsed/{doc_id}/{artifact}
    """

    def __init__(self, base_dir: str = "./data/storage"):
        self._base = Path(base_dir)
        self._base.mkdir(parents=True, exist_ok=True)

    async def save_raw(self, doc_id: str, filename: str, content: bytes) -> str:
        """Save a raw uploaded file. Returns the relative path."""
        dest_dir = self._base / "raw" / doc_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / filename
        async with aiofiles.open(dest, "wb") as f:
            await f.write(content)
        return str(dest.relative_to(self._base))

    async def read_raw(self, doc_id: str, filename: str) -> bytes:
        path = self._base / "raw" / doc_id / filename
        async with aiofiles.open(path, "rb") as f:
            return await f.read()

    def delete_doc(self, doc_id: str) -> None:
        """Delete all files for a document."""
        for subdir in ("raw", "parsed"):
            target = self._base / subdir / doc_id
            if target.exists():
                shutil.rmtree(target)
