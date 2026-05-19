from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol


class EmbeddingProvider(Protocol):
    """Provider contract for text-to-vector embedding generation."""

    def embed_texts(self, texts: tuple[str, ...]) -> tuple[list[float], ...]:
        ...


@dataclass(frozen=True)
class DeterministicEmbeddingProvider:
    """Low-cost deterministic provider for local retrieval baseline testing."""

    dimensions: int = 512

    def __post_init__(self) -> None:
        if self.dimensions <= 0:
            raise ValueError("dimensions must be positive")

    def embed_texts(self, texts: tuple[str, ...]) -> tuple[list[float], ...]:
        return tuple(self._embed_text(text) for text in texts)

    def _embed_text(self, text: str) -> list[float]:
        vector: list[float] = []
        seed = text.strip()
        for index in range(self.dimensions):
            digest = sha256(f"{seed}:{index}".encode("utf-8")).digest()
            value = int.from_bytes(digest[:8], "big", signed=False)
            # Map unsigned 64-bit value to [-1.0, 1.0].
            scale = value / ((2**64) - 1)
            vector.append((scale * 2.0) - 1.0)
        return vector
