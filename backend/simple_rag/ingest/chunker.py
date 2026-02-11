"""Text chunking strategies — configurable, versioned."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from simple_rag.utils.normalize import content_hash


@dataclass
class Chunk:
    """A single chunk produced by the chunker."""

    chunk_id: str
    doc_id: str
    chunk_index: int
    text: str
    content_hash: str
    chunker_version: str
    metadata: dict = field(default_factory=dict)


class SimpleOverlapChunker:
    """Split text into overlapping chunks by character length.

    This is the simplest strategy; more advanced (paragraph / heading / semantic)
    chunkers can implement the same interface.
    """

    VERSION = "simple_overlap_v1"

    def __init__(self, chunk_size: int = 500, overlap: int = 100):
        self._chunk_size = chunk_size
        self._overlap = overlap

    def chunk(self, doc_id: str, text: str, metadata: dict | None = None) -> list[Chunk]:
        """Split text into chunks."""
        metadata = metadata or {}
        chunks: list[Chunk] = []
        start = 0
        idx = 0

        while start < len(text):
            end = start + self._chunk_size
            chunk_text = text[start:end]

            # Try to break at sentence boundary if possible
            if end < len(text):
                last_period = max(
                    chunk_text.rfind("。"),
                    chunk_text.rfind("."),
                    chunk_text.rfind("\n"),
                )
                if last_period > self._chunk_size * 0.3:
                    chunk_text = chunk_text[: last_period + 1]
                    end = start + last_period + 1

            c_hash = content_hash(chunk_text)
            chunks.append(
                Chunk(
                    chunk_id=f"{doc_id}__{idx}",
                    doc_id=doc_id,
                    chunk_index=idx,
                    text=chunk_text,
                    content_hash=c_hash,
                    chunker_version=self.VERSION,
                    metadata=metadata,
                )
            )
            idx += 1
            start = end - self._overlap if end < len(text) else end

        return chunks
