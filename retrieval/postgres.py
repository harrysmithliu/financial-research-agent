from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from storage.postgres import PostgresConnection


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    document_id: str
    chunk_index: int
    source_uri: str
    text: str
    metadata: dict[str, Any]
    distance: float


def ensure_document_chunk_vector_index(connection: PostgresConnection) -> str:
    """Create a cosine-distance vector index with a safe fallback path."""

    try:
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_vector_hnsw
            ON document_chunks
            USING hnsw (embedding_vector vector_cosine_ops)
            WHERE embedding_vector IS NOT NULL
            """,
            (),
        )
        return "hnsw"
    except Exception:
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_vector_ivfflat
            ON document_chunks
            USING ivfflat (embedding_vector vector_cosine_ops)
            WITH (lists = 100)
            WHERE embedding_vector IS NOT NULL
            """,
            (),
        )
        return "ivfflat"


def backfill_document_chunk_vectors(
    connection: PostgresConnection,
    *,
    embedding_dimensions: int,
) -> int:
    """Backfill vector column from JSONB embeddings where dimensions match."""

    if embedding_dimensions <= 0:
        raise ValueError("embedding_dimensions must be positive")

    cursor = connection.execute(
        """
        UPDATE document_chunks
        SET embedding_vector = embedding::text::vector
        WHERE embedding IS NOT NULL
          AND embedding_vector IS NULL
          AND jsonb_typeof(embedding) = 'array'
          AND jsonb_array_length(embedding) = %s
        """,
        (embedding_dimensions,),
    )
    rowcount = getattr(cursor, "rowcount", 0)
    if isinstance(rowcount, int) and rowcount > 0:
        return rowcount
    return 0


def search_document_chunks_by_vector(
    connection: PostgresConnection,
    *,
    query_embedding: list[float],
    top_k: int,
) -> tuple[RetrievedChunk, ...]:
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    _validate_embedding(query_embedding)
    query_vector = _embedding_vector_literal(query_embedding)

    rows = connection.execute(
        """
        SELECT
            chunk_id,
            document_id,
            chunk_index,
            source_uri,
            text,
            metadata,
            embedding_vector <=> %s::vector AS distance
        FROM document_chunks
        WHERE embedding_vector IS NOT NULL
        ORDER BY embedding_vector <=> %s::vector, chunk_id
        LIMIT %s
        """,
        (query_vector, query_vector, top_k),
    ).fetchall()

    return tuple(_retrieved_chunk_from_row(row) for row in rows)


def _validate_embedding(embedding: list[float]) -> None:
    if not embedding:
        raise ValueError("query_embedding must not be empty")
    if not all(isinstance(value, int | float) for value in embedding):
        raise ValueError("query_embedding must contain numeric values")


def _embedding_vector_literal(values: list[float]) -> str:
    joined = ",".join(str(value) for value in values)
    return f"[{joined}]"


def _retrieved_chunk_from_row(row: Any) -> RetrievedChunk:
    if isinstance(row, dict):
        return RetrievedChunk(
            chunk_id=row["chunk_id"],
            document_id=row["document_id"],
            chunk_index=row["chunk_index"],
            source_uri=row["source_uri"],
            text=row["text"],
            metadata=dict(row["metadata"]),
            distance=float(row["distance"]),
        )

    return RetrievedChunk(
        chunk_id=row[0],
        document_id=row[1],
        chunk_index=row[2],
        source_uri=row[3],
        text=row[4],
        metadata=dict(row[5]),
        distance=float(row[6]),
    )
