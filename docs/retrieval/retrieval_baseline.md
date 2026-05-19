# Retrieval Baseline

## Purpose
Capture the first production-shaped retrieval baseline over stored document chunks.

## Intended Audience
- RAG / Retrieval Agent
- API / Workflow Agent
- Guardrails / Evaluation Agent
- Project reviewers

## Baseline Scope
- Data scope: seed dataset + FinAgent curated sample
- Retrieval source: persisted `document_chunks` records in PostgreSQL
- Output contract: preserve `chunk_id`, `document_id`, `source_uri`, `metadata`, and distance
- Runtime target: local Docker Compose (`api`, `postgres`, `redis`)

## Implemented Baseline Components
- Settings:
  - `retrieval_embedding_dimension` (default `512`)
  - `retrieval_top_k` (default `5`)
- Embedding provider interface and deterministic baseline provider:
  - `retrieval/embeddings.py`
- Retrieval service boundary:
  - `retrieval/service.py`
- PostgreSQL vector retrieval utilities:
  - `retrieval/postgres.py`
- Storage dual-write support:
  - `storage/postgres.py` now writes both
    - `embedding` (JSONB)
    - `embedding_vector` (`vector(512)`)
- Migration:
  - `storage/migrations/002_document_chunk_embedding_vector.sql`

## Runtime Verification (Smoke)
Verified through Docker Compose runtime:
- services healthy: `api`, `postgres`, `redis`
- seed ingestion to PostgreSQL completed
- persisted counts verified:
  - `structured_records=7`
  - `documents=13`
  - `document_chunks=17`
  - `eval_cases=10`
- chunk readback preserved citation-critical fields:
  - `chunk_id`
  - `document_id`
  - `source_uri`
  - `metadata`

## Deferred Items
- model-backed embedding provider integration
- reranking strategy
- hybrid retrieval (sparse + dense)
- workflow-level citation post-validation

---
Created By: RAG / Retrieval Agent (Codex)
Created At (UTC): 2026-05-19T18:40:15Z
Last Updated At (UTC): 2026-05-19T19:12:08Z
