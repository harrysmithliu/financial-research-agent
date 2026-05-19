# Retrieval Baseline

## Purpose
Capture the baseline retrieval contract, default parameters, and data scope used for the first production-shaped retrieval implementation.

## Intended Audience
- RAG / Retrieval Agent
- API / Workflow Agent
- Guardrails / Evaluation Agent
- Project reviewers

## Baseline Scope (Batch 0 Draft)
- Data scope: seed dataset + FinAgent curated sample
- Retrieval source: stored `DocumentChunk` records
- Output contract: preserve `chunk_id`, `document_id`, `source_uri`, and citation metadata
- Runtime target: PostgreSQL-backed local environment

## Default Runtime Parameters
- `top_k`: 5
- Evaluation slices: k in {3, 5, 10}

## Deferred Items
- Reranker strategy
- Hybrid retrieval (sparse + dense)
- Cross-source weighting policy

## Exit Criteria For Baseline Completion
- End-to-end retrieval query path over persisted chunks
- Metadata-preserving retrieval results
- Baseline metrics report recorded

---
Created By: RAG / Retrieval Agent (Codex)
Created At (UTC): 2026-05-19T18:40:15Z
