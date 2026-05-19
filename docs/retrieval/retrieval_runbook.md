# Retrieval Runbook

## Purpose
Provide operational steps for running, validating, and debugging the local retrieval baseline.

## Intended Audience
- RAG / Retrieval Agent
- Ingestion / Backend Agent
- Foundation / DevOps Agent
- Any contributor validating retrieval locally

## Planned Runbook Coverage
- Start local services (API, PostgreSQL/pgvector, Redis)
- Run seed ingestion to PostgreSQL
- Validate persisted counts and chunk metadata
- Execute retrieval baseline query checks
- Run retrieval evaluation and read pass/fail output

## Planned Troubleshooting Coverage
- Database connectivity failures
- Migration/version drift
- Empty chunk retrieval results
- Embedding dimension mismatch
- Metric regression triage

## Status
This is a Batch 0 scaffold. Commands and concrete troubleshooting steps will be completed in later batches.

---
Created By: RAG / Retrieval Agent (Codex)
Created At (UTC): 2026-05-19T18:40:15Z
