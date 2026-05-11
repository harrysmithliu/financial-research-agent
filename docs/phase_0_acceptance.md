# Phase 0 Acceptance Evidence

Date: 2026-05-11

Agent role: Foundation / DevOps Agent

## Purpose

This document records acceptance evidence for Phase 0: Project Foundation. It is intended for future development agents and reviewers who need to confirm that the local runtime foundation is installable, runnable, testable, and ready for later feature work.

## Scope Covered

Phase 0 foundation now includes:

- Python project metadata and packaging in `pyproject.toml`.
- FastAPI application entry point in `api/main.py`.
- Settings module in `config/settings.py`.
- Health endpoint in `api/routes/health.py`.
- Request ID middleware in `api/middleware.py`.
- Structured JSON logging foundation in `observability/logging.py`.
- Docker runtime files: `Dockerfile`, `.dockerignore`, and `docker-compose.yml`.
- PostgreSQL/pgvector initialization SQL in `infra/docker/postgres/init/001_enable_pgvector.sql`.
- Redis service in Docker Compose.
- GitHub Actions CI workflow in `.github/workflows/ci.yml`.
- Local environment template in `.env.example`.
- pytest configuration in `pyproject.toml`.

## Local Setup Evidence

Local test command:

```bash
python3 -m pytest
```

Result:

```text
34 passed
```

The pytest configuration in `pyproject.toml` sets `testpaths = ["tests"]` and `pythonpath = ["."]`, so tests no longer require manually setting `PYTHONPATH=.`

## Docker Compose Startup Evidence

Compose config validation command:

```bash
docker compose config
```

Result:

```text
Configuration rendered successfully.
```

Compose startup command:

```bash
docker compose up --build -d
```

Observed services:

```text
mcp-financial-research-agent-api-1        Up (healthy)
mcp-financial-research-agent-postgres-1   Up (healthy)
mcp-financial-research-agent-redis-1      Up (healthy)
```

The Compose stack includes:

- `api`: FastAPI application running through Uvicorn.
- `postgres`: `pgvector/pgvector:pg16`.
- `redis`: `redis:7-alpine`.

The stack was stopped after verification with:

```bash
docker compose down
```

## Health Endpoint Evidence

Health endpoint route:

```http
GET /health
```

Container-internal verification command:

```bash
docker compose exec -T api python -c "from urllib.request import urlopen; print(urlopen('http://127.0.0.1:8000/health', timeout=2).read().decode())"
```

Result:

```json
{"status":"ok","service":"financial-research-agent","environment":"local","request_id":"f0962918-468b-4bd2-838f-606fee01eac8"}
```

API container logs showed structured JSON application logs and request ID propagation for health checks.

## CI Evidence

GitHub Actions workflow added:

```text
.github/workflows/ci.yml
```

The workflow installs the package with development dependencies and runs:

```bash
python -m pytest
```

CI has not yet been verified on GitHub Actions in this local session. It should run after the next push.

## Known Gaps

- No database migrations yet.
- No persistent ingestion repository yet.
- No `POST /ingestion/jobs` API route yet.
- No MCP Gateway runtime wiring yet.
- No LangGraph workflow runtime yet.
- No full metrics endpoint yet.
- No OpenTelemetry exporter configuration yet.
- Host-side `curl http://127.0.0.1:8000/health` did not connect from this execution environment, while Docker health checks, Compose service health, and container-internal health requests succeeded.

## Out Of Scope For Phase 0

- PostgreSQL schema design and migrations.
- pgvector indexing.
- Redis-backed job execution.
- Full ingestion API implementation.
- MCP tools.
- Retrieval and reranking.
- Guardrails.
- Research answer generation.
- Human review workflow.
