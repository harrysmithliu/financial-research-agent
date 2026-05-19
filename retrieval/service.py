from __future__ import annotations

from dataclasses import dataclass

from retrieval.embeddings import EmbeddingProvider
from retrieval.postgres import (
    RetrievedChunk,
    backfill_document_chunk_vectors,
    ensure_document_chunk_vector_index,
    search_document_chunks_by_vector,
)
from storage.postgres import PostgresConnection


@dataclass(frozen=True)
class RetrievalService:
    connection: PostgresConnection
    embedding_provider: EmbeddingProvider
    embedding_dimensions: int = 512
    default_top_k: int = 5

    def prepare_vector_index(self) -> str:
        return ensure_document_chunk_vector_index(self.connection)

    def backfill_vector_column(self) -> int:
        return backfill_document_chunk_vectors(
            self.connection,
            embedding_dimensions=self.embedding_dimensions,
        )

    def search(self, query: str, *, top_k: int | None = None) -> tuple[RetrievedChunk, ...]:
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("query must not be empty")

        result_limit = self.default_top_k if top_k is None else top_k
        query_embedding = self.embedding_provider.embed_texts((normalized_query,))[0]
        return search_document_chunks_by_vector(
            self.connection,
            query_embedding=query_embedding,
            top_k=result_limit,
        )
