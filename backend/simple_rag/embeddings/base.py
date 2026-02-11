"""Embedder abstract base class — unified interface for local & remote embedding providers."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Embedder(ABC):
    """All embedding providers must implement this interface."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts and return vectors.

        Args:
            texts: list of raw text strings.

        Returns:
            list of vectors (each vector is a list of floats), same order as input.
        """
        ...

    @property
    @abstractmethod
    def dim(self) -> int:
        """Dimensionality of the embedding vectors."""
        ...

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Unique identifier for this embedding model (used in index naming & metadata)."""
        ...

    @property
    def normalize(self) -> bool:
        """Whether vectors are L2-normalized. Default True."""
        return True
