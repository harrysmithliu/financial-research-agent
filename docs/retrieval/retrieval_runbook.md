# Retrieval Runbook

## Purpose
Provide concrete local steps to run and validate the retrieval baseline.

## Intended Audience
- RAG / Retrieval Agent
- Ingestion / Backend Agent
- Foundation / DevOps Agent
- Contributors validating retrieval locally

## Prerequisites
- Docker Desktop running
- repository root as working directory

## 1. Start Local Runtime
```bash
docker compose up --build -d
docker compose ps
```
Expected: `api`, `postgres`, `redis` all healthy.

## 2. Ensure Dataset Is Available In API Container
Current Dockerfile does not copy `data/` into `/app`, so copy it manually for runtime verification:
```bash
docker compose cp data api:/app/data
```

## 3. Run Seed Ingestion To PostgreSQL
```bash
docker compose exec -T api python - <<'PY'
from ingestion.postgres_runner import run_seed_ingestion_to_postgres

result = run_seed_ingestion_to_postgres(
    '/app',
    database_url='postgresql://financial_research:financial_research@postgres:5432/financial_research',
)
print(result.job_record.status)
print(len(result.structured_records), len(result.documents), len(result.document_chunks), len(result.eval_cases))
PY
```
Expected counts: `7 13 17 10`.

## 4. Validate Stored Chunk Metadata
```bash
docker compose exec -T api python - <<'PY'
from storage.postgres import connect_postgres_repository

repo = connect_postgres_repository('postgresql://financial_research:financial_research@postgres:5432/financial_research')
chunk = repo.list_document_chunks()[0]
print(chunk.chunk_id)
print(chunk.document_id)
print(chunk.source_uri)
print(sorted(chunk.metadata.keys())[:8])
close = getattr(repo.connection, 'close', None)
if callable(close):
    close()
PY
```
Expected: `chunk_id`, `document_id`, `source_uri`, and metadata keys are present.

## 5. Run Retrieval Tests
```bash
python3 -m pytest tests/test_retrieval_embeddings.py tests/test_retrieval_postgres.py tests/test_retrieval_metrics.py
```

## 6. Run Full Tests
```bash
python3 -m pytest tests
```

## 7. Teardown
```bash
docker compose down
```

## Troubleshooting
- `psycopg is required` on host: run ingestion checks inside `api` container or install project deps locally.
- `FileNotFoundError /app/data/manifest.json`: copy data directory with `docker compose cp data api:/app/data`.
- Empty retrieval results: verify embeddings exist and backfill vector column via retrieval service before querying.
- Vector index creation fallback: retrieval utilities try `hnsw` first, then `ivfflat`.

---
Created By: RAG / Retrieval Agent (Codex)
Created At (UTC): 2026-05-19T18:40:15Z
Last Updated At (UTC): 2026-05-19T19:12:08Z
