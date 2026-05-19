# Embedding Provider Selection

## Purpose
Define the embedding provider strategy for retrieval baseline execution with low-cost defaults and explicit swap conditions.

## Intended Audience
- RAG / Retrieval Agent
- Ingestion / Backend Agent
- MCP Gateway / Tooling Agent
- Maintainers operating local runtime

## Scope
This document only covers embedding generation for retrieval. It does not define generation-model policy.

## Current Decision
- Provider path: OpenAI-compatible adapter first
- Baseline provider implementation: deterministic local provider (`retrieval/embeddings.py`) for low-cost practice and repeatable tests
- Runtime embedding dimension: `512` by default (`Settings.retrieval_embedding_dimension`)
- Runtime top_k default: `5` (`Settings.retrieval_top_k`)

## Why This Decision
- Lowest operational cost for initial end-to-end integration
- Deterministic vectors make baseline retrieval tests reproducible
- Adapter boundary allows future switch to model-backed providers without changing retrieval contracts

## Swap Conditions
Move from deterministic to model-backed embeddings when all baseline thresholds are stable and one of the following is true:
- retrieval metrics plateau below target despite chunking/index tuning
- cross-dataset generalization requires semantic quality beyond deterministic vectors
- product workflow enters quality validation for user-facing research output

## Required Invariants During Provider Swap
- Keep `chunk_id`, `document_id`, `source_uri`, and citation metadata preserved in retrieval outputs
- Keep `embedding_dimension` consistent with `document_chunks.embedding_vector` schema
- Rebuild or backfill vectors before enabling model-backed search in shared environments

## Related Implementation
- Adapter: `retrieval/embeddings.py`
- Retrieval service: `retrieval/service.py`
- Vector search path: `retrieval/postgres.py`
- Storage dual-write: `storage/postgres.py`

---
Created By: RAG / Retrieval Agent (Codex)
Created At (UTC): 2026-05-19T18:40:15Z
Last Updated At (UTC): 2026-05-19T19:12:08Z
