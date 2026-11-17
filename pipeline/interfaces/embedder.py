"""Multilingual text embedder interface.

Default: BGE-M3 (multilingual, supports Hindi and English).
Configurable via settings.embedding_model_name.
Queries in either language should match chunks in either language.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class Embedder(ABC):
    """Abstract embedding interface.

    Implementations must:
    - Support Hindi (Devanagari) and English in the same batch
    - Return normalized float vectors (cosine similarity ready)
    - Report the model name for audit logging
    """

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts and return a list of float vectors."""
        ...

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model name and version for audit logging."""
        ...

    @abstractmethod
    def get_dimension(self) -> int:
        """Return the embedding vector dimension."""
        ...


class StubEmbedder(Embedder):
    """Stub embedder for testing. Returns zero vectors."""

    _DIM = 128

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * self._DIM for _ in texts]

    def get_model_name(self) -> str:
        return "StubEmbedder/0.1"

    def get_dimension(self) -> int:
        return self._DIM
