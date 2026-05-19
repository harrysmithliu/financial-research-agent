from __future__ import annotations

from retrieval.embeddings import DeterministicEmbeddingProvider


def test_deterministic_embedding_provider_returns_stable_vectors() -> None:
    provider = DeterministicEmbeddingProvider(dimensions=8)

    first = provider.embed_texts(("Fund A",))[0]
    second = provider.embed_texts(("Fund A",))[0]

    assert first == second
    assert len(first) == 8


def test_deterministic_embedding_provider_value_range_is_bounded() -> None:
    provider = DeterministicEmbeddingProvider(dimensions=16)

    vector = provider.embed_texts(("Fund B",))[0]

    assert all(-1.0 <= value <= 1.0 for value in vector)


def test_deterministic_embedding_provider_rejects_non_positive_dimensions() -> None:
    try:
        DeterministicEmbeddingProvider(dimensions=0)
    except ValueError as exc:
        assert str(exc) == "dimensions must be positive"
    else:
        raise AssertionError("Expected ValueError for non-positive dimensions")
