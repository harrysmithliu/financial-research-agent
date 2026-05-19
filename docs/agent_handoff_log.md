# Agent Handoff Log

This document is the shared handoff log for all agents working on MCP Financial Research Agent.

## How To Use This Document

All agents should treat this file as durable project memory for cross-agent handoffs.

When an agent finishes a bounded phase or hands work to another agent, add a new UTC-timestamped handoff entry. Do not delete or rewrite completed handoff entries unless the user explicitly asks for cleanup.

Completed handoffs use this top-level heading format:

```markdown
## Handoff YYYY-MM-DD-HHMMZ: Short Title

`HHMMZ` is the 24-hour UTC hour and minute, and `Z` means UTC. For completed handoffs, the heading timestamp is the actual handoff time.

Top-level handoff sections must be ordered strictly by their heading timestamps from earliest to latest. A top-level `## Handoff ...` section represents an actual completed handoff, not a future task placeholder.

Each handoff entry should include:

From: Agent / Role
To: Agent / Role
### Completions
### Inputs
### Outputs
### Suggestions
### Expectations

Completions = what the current handoff owner has already completed.
Inputs = the input context received by the current agent.
Outputs = the deliverables produced by the current agent.
Suggestions = recommended next actions.
Expectations = what the next agent is expected to achieve in the next phase.

If Agent A expects the work to return later, Agent A may add a nested planned checkpoint under that same handoff. Planned checkpoints are optional and are not top-level sections. Do not add a planned checkpoint unless there is a clear expected return point; prefer keeping the task flow linear when no explicit return is needed:

### Planned Checkpoint: Short Title
Return to: Agent / Role
#### Trigger
```

The nested planned checkpoint should only include `Return To:` and `#### Trigger`.
When the role listed in `To:` for a handoff completes that handoff, it should remove the nested planned checkpoint from that handoff and create a new top-level `## Handoff YYYY-MM-DD-HHMMZ: Short Title` entry using the actual handoff time. 

Keep the wording as concise as possible while preserving necessary information. The next agent should be able to start work from the latest relevant entry without reconstructing context from chat history.

The main body is below: 

## Handoff 2026-05-11-1347Z: Data Seed To Ingestion

From: Data Engineering Agent

To: Ingestion / Backend Agent

### Completions

Defined the kickoff scope for the first production-shaped batch ingestion path over the local synthetic seed dataset.

The path should read `data/manifest.json`, load each declared source, normalize raw source data into canonical internal formats, and keep interfaces clear for later chunking, embedding, storage, and MCP tool access.

### Inputs

Data sources:

- `data/manifest.json`
- `data/sample_funds/funds.json`
- `data/sample_documents/fund_a_factsheet.md`
- `data/sample_documents/fund_b_factsheet.md`
- `data/sample_documents/fund_c_factsheet.md`
- `data/sample_documents/fund_d_factsheet.md`
- `data/sample_issues/issues.json`
- `data/eval_cases/fund_eval_cases.json`

Reference docs:

- `docs/financial_research_agent_requirements.md`
- `docs/canonical_data_formats.md`
- `data/README.md`

### Outputs

Initial Phase 1 ingestion skeleton:

```text
ingestion/
|- __init__.py
|- loaders.py
|- normalizers.py
`- sources/
   |- __init__.py
   `- local_files.py

storage/
|- __init__.py
`- models.py
```

Required normalization coverage:

1. Structured fund records
   - Source: `data/sample_funds/funds.json`
   - Canonical output: `StructuredRecord`
   - Later storage target: `Fund`
2. Fund factsheets
   - Source: `data/sample_documents/*.md`
   - Canonical output: `Document`
   - Later processing target: `DocumentChunk`
3. Synthetic platform issues
   - Source: `data/sample_issues/issues.json`
   - Canonical output: issue metadata as `StructuredRecord`
   - Canonical output: issue bodies and comments as `Document`
4. Fund evaluation cases
   - Source: `data/eval_cases/fund_eval_cases.json`
   - Canonical output: `EvalCase`

Implementation constraints:

- Follow the package layout in `docs/financial_research_agent_requirements.md`.
- Place database-facing models in `storage/models.py`.
- Keep API schemas separate from storage models when API routes are added.
- Do not pass raw source data directly to agent workflows.
- Preserve `source_uri`, `source_type`, `dataset_name`, and entity metadata for citation, audit, debugging, replay, and evaluation.
- Do not introduce real client data or live investment advice.

### Suggestions

Create the initial project code skeleton shown above and keep modules small.

The first milestone should run locally without PostgreSQL, pgvector, Redis, or an LLM provider.

Suggested test focus:

- manifest parsing
- source path resolution
- fund record validation
- markdown factsheet title/body extraction
- issue/comment normalization
- eval case validation

### Expectations

- Build deterministic normalization for all listed seed sources through the planned ingestion skeleton.
- Keep canonical outputs stable for `StructuredRecord`, `Document`, and `EvalCase`.
- Add focused tests for manifest parsing, source resolution, and malformed input paths.
- Preserve citation/audit metadata fields needed by later phases.

- Do not implement embeddings, pgvector indexing, PostgreSQL migrations, Redis jobs, FastAPI route wiring, LangGraph runtime, or MCP Gateway tools.

## Handoff 2026-05-11-1910Z: Ingestion Stable To External Data Expansion

From: Ingestion / Backend Agent

To: Data Engineering Agent

### Completions

Confirmed the first local manifest-driven ingestion path is stable and ready for external data expansion.

Implemented code artifacts:

- `ingestion/loaders.py`
- `ingestion/sources/local_files.py`
- `ingestion/normalizers.py`
- `ingestion/jobs.py`
- `storage/models.py`

Current local ingestion entry point:

```python
from ingestion.jobs import load_seed_dataset

result = load_seed_dataset(repo_root)
```

Current deterministic output shape:

- 4 fund `StructuredRecord` items from `data/sample_funds/funds.json`
- 4 factsheet `Document` items from `data/sample_documents/*.md`
- 3 issue metadata `StructuredRecord` items from `data/sample_issues/issues.json`
- 9 issue/comment `Document` items from `data/sample_issues/issues.json`
- 5 `EvalCase` items from `data/eval_cases/fund_eval_cases.json`
- 7 total structured records via `IngestionResult.structured_records`

Verification command:

```bash
python3 -m pytest tests
```

Latest verified result:

```text
30 passed
```

### Inputs

Code:

- `ingestion/jobs.py`
- `ingestion/loaders.py`
- `ingestion/normalizers.py`
- `storage/models.py`
- `tests/test_seed_ingestion_job.py`

Data:

- `data/manifest.json`
- `data/sample_funds/funds.json`
- `data/sample_documents/*.md`
- `data/sample_issues/issues.json`
- `data/eval_cases/fund_eval_cases.json`

Reference docs:

- `docs/financial_research_agent_requirements.md`
- `docs/canonical_data_formats.md`
- `data/README.md`

### Outputs

Expansion target:

- Preserve the same manifest-driven ingestion contract while adding small curated external samples.

Suggested external sources:

- TAT-QA small sample for financial QA and table/text reasoning.
- FinAgent Benchmark small sample for agentic finance evaluation.
- OpenBB or QuantConnect Lean GitHub issues/comments for platform issue research.

Required data engineering work:

- Add curated external samples in small batches only.
- Normalize Hugging Face samples into `Document` and `EvalCase`.
- Normalize GitHub issues/comments into issue metadata `StructuredRecord` plus issue/comment `Document` records.
- Update `data/manifest.json` for each new source.
- Update `data/README.md` with provenance, sample size, licensing notes, and replacement path.
- Add data quality checks for missing fields, duplicate `source_uri`, broken citations, and unsupported task types.

### Suggestions

Add a tiny external eval dataset slice:

- 5 to 10 TAT-QA-style cases, or
- 5 to 10 FinAgent Benchmark cases.

Keep the first external batch small enough for manual review.

### Expectations

- Add a small curated external data slice with documented provenance and licensing.
- Keep new samples compatible with the existing manifest-driven ingestion path.
- Ensure eval cases keep clear citation/evidence references and remain safe for local use.
- Keep changes inspectable and reversible so ingestion hardening can proceed safely.

- Do not perform large-scale dataset mirroring, unbounded crawling, paid-cloud ingestion, or real-client/live-trading data use.
- Do not expand into embeddings, PostgreSQL migrations, or other runtime-surface work in this handoff.

## Handoff 2026-05-11-2041Z: Phase 0 Runtime Foundation

From: Foundation / DevOps Agent

To: API / Workflow Agent, Ingestion / Backend Agent, MCP Gateway / Tooling Agent


### Completions

Completed the Phase 0 runtime foundation so feature work can start from a runnable, testable, Docker-backed baseline.

Foundation verification completed:

- Local tests:
  - `python3 -m pytest`
  - result: `34 passed`
- Docker Compose runtime:
  - `docker compose config`
  - `docker compose up --build -d`
  - `docker compose exec -T api python -c "from urllib.request import urlopen; print(urlopen('http://127.0.0.1:8000/health', timeout=2).read().decode())"`
  - `docker compose down`
- Observed API, PostgreSQL/pgvector, and Redis services as healthy during the Compose run.

### Inputs

Reference acceptance document:

- `docs/phase_0_acceptance.md`

Runtime baseline modules used by follow-up agents:

- `api/main.py`
- `config/settings.py`
- `observability/logging.py`
- `observability/request_context.py`

### Outputs

Delivered Phase 0 foundation artifacts:

- `pyproject.toml`
- `.env.example`
- `.dockerignore`
- `Dockerfile`
- `docker-compose.yml`
- `.github/workflows/ci.yml`
- `api/main.py`
- `api/middleware.py`
- `api/routes/health.py`
- `config/settings.py`
- `observability/logging.py`
- `observability/request_context.py`
- `infra/docker/postgres/init/001_enable_pgvector.sql`
- `docs/phase_0_acceptance.md`

### Suggestions

Use this runtime baseline rather than creating parallel app or service entry points.

- API / Workflow Agent:
  - Add route skeletons behind the existing FastAPI app factory.
  - Keep request ID propagation and JSON logging intact.
- Ingestion / Backend Agent:
  - Begin repository boundary design before database writes.
  - Keep in-memory ingestion tests stable while introducing persistence.
- MCP Gateway / Tooling Agent:
  - Reuse settings, logging, and request context modules when introducing gateway routing.

### Expectations

- Reuse the Phase 0 runtime baseline instead of creating parallel app/config/logging/Docker/CI paths.
- Preserve request ID propagation and health endpoint stability while adding feature code.
- Keep feature additions behind existing package boundaries (`api`, `config`, `observability`).

- No replacement of the core runtime entry points.
- No unrelated expansion into full metrics exporter wiring, MCP Gateway runtime, or LangGraph runtime unless explicitly planned in the next handoff.

### Planned Checkpoint: Foundation Runtime Back To Feature Agents

Return To: API / Workflow Agent, Ingestion / Backend Agent, MCP Gateway / Tooling Agent

#### Trigger

Start this checkpoint when a feature agent is ready to build on the Phase 0 runtime foundation.

- Phase 0 foundation artifacts are present.
- `docs/phase_0_acceptance.md` records setup, health, Compose, and test evidence.
- Local tests pass with `python3 -m pytest`.
- Docker Compose config and startup have been verified at least once.
- Feature work needs an API route, repository boundary, gateway component, or runtime integration.

## Handoff 2026-05-11-2325Z: External Data Expansion Back To Ingestion

From: Data Engineering Agent

To: Ingestion / Backend Agent

### Completions

Completed the first external data expansion slice so ingestion can be hardened against a real curated Hugging Face sample while keeping synthetic seed ingestion stable.

Added a tiny curated sample from FinAgent Benchmark:

- Source dataset: `Guen/finagent-benchmark`
- Source URL: `https://huggingface.co/datasets/Guen/finagent-benchmark`
- License: MIT
- Raw local snapshot: `data/external/raw/finagent-benchmark/`
- Raw source file: `benchmark_questions.json`
- Full raw dataset size: 133 benchmark questions
- Tracked curated sample: `data/external/finagent_benchmark_sample.json`
- Curated sample size: 5 eval cases

Selected source records:

- `FE_001`: fact extraction
- `NR_001`: numerical reasoning
- `TR_001`: temporal reasoning
- `MH_001`: multi-hop comparison
- `ADV_001`: adversarial not-available case

Verification evidence:

- JSON validation:
  - `python3 -m json.tool data/external/finagent_benchmark_sample.json`
  - `python3 -m json.tool data/manifest.json`
- Ingestion entry point smoke check:
  - `python3 - <<'PY' ... load_seed_dataset('.') ... PY`
- Latest observed result:
  - `documents 13`
  - `structured_records 7`
  - `eval_cases 10`
  - case IDs include `finagent_FE_001`, `finagent_NR_001`, `finagent_TR_001`, `finagent_MH_001`, `finagent_ADV_001`

### Inputs

External and local sources:

- `Guen/finagent-benchmark` (curated local subset)
- `data/external/raw/finagent-benchmark/benchmark_questions.json`
- Existing seed ingestion path via `ingestion.jobs.load_seed_dataset`

Reference context:

- Existing manifest-driven ingestion contract
- Existing canonical formats and ingestion tests

### Outputs

Produced artifacts:

- `data/external/finagent_benchmark_sample.json`
- `docs/external_data_source_selection.md`
- `scripts/download_finagent_benchmark.py`
- `.gitignore` update to ignore `data/external/raw/`
- `data/manifest.json` registration for `finagent_benchmark_sample`
- `data/README.md` updates for provenance, license, sample size, and selection method

Normalization/output implications:

- External sample is now wired into the same manifest-driven ingestion flow as synthetic seed data.
- Curated cases are available to exercise downstream retrieval, citation, and evaluation behavior.

### Suggestions

Add deterministic ingestion tests for the external FinAgent sample.

Suggested focus:

- manifest parsing for `finagent_benchmark_sample`
- normalization into five `EvalCase` items
- preservation of external provenance fields
- adversarial `NOT_AVAILABLE` expected-answer behavior
- duplicate or missing citation detection if a data quality helper already exists

### Expectations

- Harden the FinAgent sample path with deterministic tests and stable provenance handling.
- Keep external sample behavior reproducible through the existing ingestion flow.
- Preserve explicit rationale for deferred `huggingface_dataset` source-type expansion.

- Do not add PostgreSQL persistence in this handoff.
- Keep the raw Hugging Face snapshot untracked.
- Do not start large-scale mirroring or add new dataset families until this first external path is proven.

## Handoff 2026-05-12-1858Z: FinAgent Ingestion Hardening Complete

From: Ingestion / Backend Agent

To: Ingestion / Backend Agent


### Completions

Closed the first FinAgent sample ingestion hardening loop and stabilized the external-sample path for the next storage phase.

Implemented and verified:

- Manifest and end-to-end ingestion tests now expect `finagent_benchmark_sample`.
- `load_seed_dataset` loads 8 manifest sources and 10 eval cases.
- `EvalCase` now includes `metadata` for provenance and source-specific metadata.
- FinAgent `source_metadata` is preserved under `EvalCase.metadata["source_metadata"]`.
- `safety_expectations` remains focused on safety and behavior expectations.
- FinAgent-specific deterministic tests cover all 5 curated cases.
- The adversarial `finagent_ADV_001` case preserves `expected_answer: NOT_AVAILABLE`, `should_state_not_available`, `not_available_expected`, `hf://` citation, and source metadata.
- Added data quality checks for duplicate case IDs, missing expected citations, missing citation `source_uri`, and unsupported task types.
- Documented the source type decision to keep `finagent_benchmark_sample` as `source_type: sample_dataset` and defer `huggingface_dataset`.

Verification evidence:

- `python3 -m pytest tests`
- Latest result: `42 passed`

### Inputs

Upstream inputs from prior external-data expansion:

- `data/external/finagent_benchmark_sample.json`
- `data/manifest.json`
- `data/README.md`
- `docs/external_data_source_selection.md`

Code and test surfaces used in hardening:

- seed ingestion path via `ingestion.jobs.load_seed_dataset`
- eval case normalization and ingestion test suite

### Outputs

Hardening outputs:

- Stable FinAgent external ingestion behavior with deterministic coverage
- Preserved external provenance through `EvalCase.metadata`
- Explicit deferred decision for `huggingface_dataset` source type
- Data quality checks for eval case integrity

Related commits:

- `ed13859` Update ingestion tests for FinAgent sample
- `aa4ab77` Preserve eval case source metadata
- `8ba6e20` Add FinAgent eval case normalization tests
- `847beaf` Add eval case data quality checks
- `9759582` Document FinAgent source type decision

### Suggestions

Begin storage persistence work by designing the repository boundary between canonical ingestion outputs and durable storage models.

### Expectations

- Start storage-persistence implementation from canonical ingestion outputs through a clear repository boundary.
- Keep synthetic seed and FinAgent ingestion behavior stable while extending storage depth.
- Preserve provenance and adversarial-case behavior coverage as storage work begins.

- No FastAPI route wiring, MCP Gateway tooling, or LangGraph workflow expansion in this handoff.
- No chunking/embedding/pgvector implementation in this specific step.

## Handoff 2026-05-13-1634Z: Canonical Ingestion Storage Boundary

From: Ingestion / Backend Agent

To: Ingestion / Backend Agent


### Completions

Completed `Canonical Ingestion To Storage Persistence` at the repository-boundary level without introducing PostgreSQL writes.

Implemented:

- `storage/repository.py`
- `StorageRepository` protocol
- `InMemoryStorageRepository`
- `IngestionJobRecord`
- `IngestionRunResult`
- `run_seed_ingestion(repo_root, repository, started_at=None)`

Seed ingestion now loads manifest-driven data, persists canonical objects through the repository boundary, records ingestion job counts and source IDs, and records failed jobs with error messages before re-raising.

Verification:

- `python3 -m pytest tests`
- Latest result at handoff time: `54 passed`

Related commits:

- `13b6206` Add storage repository boundary
- `3ebde32` Add ingestion job storage records
- `7e525e6` Persist seed ingestion through repository
- `79fba03` Cover storage repository audit metadata
- `f8e5485` Protect ingestion storage runtime boundary

### Inputs

- Upstream stable canonical ingestion outputs from prior handoffs.
- Existing manifest-driven ingestion flow and seed dataset.
- Requirement to preserve citation/audit metadata and keep storage runtime decoupled from API surface.

### Outputs

- A durable repository boundary that accepts and returns `Document`, `StructuredRecord`, `EvalCase`, and `IngestionJobRecord`.
- Ingestion orchestration path that writes canonical outputs and ingestion job records via repository abstractions.
- Local test-backed storage boundary that does not require LLM provider integration.
- Runtime-boundary behavior confirming ingestion/storage code does not import FastAPI or `api.main`.

### Suggestions

Continue within Ingestion / Backend Agent for PostgreSQL repository implementation. If priority is API triggering, hand to API / Workflow Agent for a `POST /ingestion/jobs` route over the existing repository boundary.

### Expectations

- Preserve synthetic seed and FinAgent stability while extending from repository boundary to PostgreSQL persistence.
- Keep citation/audit/provenance fields intact end to end.
- Maintain decoupling from API, MCP Gateway, and LangGraph runtime surfaces during storage-depth work.
- PostgreSQL persistence, migrations, document chunking, embedding, pgvector indexing, and FastAPI ingestion route wiring remain next-phase work beyond this handoff.

## Handoff 2026-05-13-2330Z: Ingestion Storage Ready For Retrieval

From: Ingestion / Backend Agent

To: RAG / Retrieval Agent


### Completions

Completed canonical ingestion and storage persistence handoff so retrieval can start from stored `DocumentChunk` records.

Implemented PostgreSQL-backed storage path:

- `storage/postgres.py`
- `PostgresStorageRepository`
- PostgreSQL connection helper
- ingestion storage migration runner
- JSONB parameter handling for canonical payloads
- read-side hydration into canonical storage models

Implemented document chunk storage and deterministic chunk generation:

- `DocumentChunk` repository methods in `StorageRepository`
- `InMemoryStorageRepository.save_document_chunks`
- `InMemoryStorageRepository.list_document_chunks`
- `document_chunks` table in `storage/migrations/001_ingestion_storage.sql`
- `ingestion/chunker.py`
- `IngestionResult.document_chunks`
- `run_seed_ingestion` persistence of generated chunks

Implemented Postgres seed ingestion runner:

- `ingestion/postgres_runner.py`
- `run_seed_ingestion_to_postgres(repo_root, settings=None, database_url=None, started_at=None)`

Runner behavior covers database URL resolution, connection open, migration run, repository persistence, commit/rollback, and connection close.

Deterministic output counts:

- 7 structured records
- 13 documents
- 17 document chunks
- 10 eval cases

Verification:

- `python3 -m pytest tests` -> `76 passed`
- `python3 -m pytest tests/test_postgres_ingestion_runner.py tests/test_postgres_storage_repository.py` -> `18 passed`

Related commits:

- `89a5402` Add PostgreSQL storage adapter scaffold
- `703f413` Add Postgres storage connection helpers
- `705e142` Add Postgres repository read methods
- `b841640` Add document chunk storage boundary
- `0a99b8f` Add deterministic document chunking
- `0ba1e44` Add Postgres seed ingestion runner

### Inputs

- Upstream canonical ingestion/storage boundary from the prior handoff.
- Manifest-driven seed ingestion outputs and existing storage migration baseline.
- Requirement to keep retrieval-ready citation metadata (`chunk_id`, `document_id`, `source_uri`) intact.

### Outputs

- PostgreSQL persistence path for ingestion jobs, documents, document chunks, structured records, and eval cases.
- Stored `DocumentChunk` boundary usable by retrieval work.
- Postgres ingestion runner with tested transaction behavior.
- Retrieval-ready deterministic dataset persisted through repository boundaries.

### Suggestions

RAG / Retrieval Agent should start from stored `DocumentChunk` records:

- define embedding adapter interface
- define embedding representation before pgvector conversion
- add pgvector-compatible indexing for `DocumentChunk`
- preserve `chunk_id`, `document_id`, `source_uri`, and citation metadata in retrieval results

API / Workflow Agent can run in parallel by wrapping `run_seed_ingestion_to_postgres` behind `POST /ingestion/jobs` without bypassing repository boundaries.

### Expectations

- Establish a retrieval baseline over stored chunks while preserving citation/provenance integrity.
- Keep retrieval/storage work decoupled from MCP Gateway and LangGraph runtime expansion in this phase.
- Embedding provider adapter, pgvector search path, and live Docker Compose PostgreSQL smoke verification remain next-phase tasks.

## Handoff 2026-05-19-1912Z: Retrieval Baseline Over Stored Chunks

From: RAG / Retrieval Agent

To: Data Engineering Agent, API / Workflow Agent, Foundation / DevOps Agent

### Completions

Completed the first retrieval baseline over PostgreSQL-stored `DocumentChunk` records with deterministic embedding support, pgvector-ready storage shape, vector retrieval query path, and retrieval metric evaluation utilities.

Delivered runtime-backed smoke evidence in Docker Compose:

- `api`, `postgres`, and `redis` all healthy
- `run_seed_ingestion_to_postgres` completed
- persisted deterministic counts verified:
  - `structured_records=7`
  - `documents=13`
  - `document_chunks=17`
  - `eval_cases=10`
- chunk readback preserved citation-critical fields:
  - `chunk_id`
  - `document_id`
  - `source_uri`
  - `metadata`

### Inputs

- `Ingestion Storage Ready For Retrieval`
- canonical ingestion/storage persistence path with deterministic chunk outputs
- requirement to preserve citation/provenance metadata end to end
- approved baseline thresholds:
  - Recall@5 >= 0.70
  - MRR@5 >= 0.45
  - Citation Coverage >= 0.80

### Outputs

Code artifacts:

- `storage/migrations/002_document_chunk_embedding_vector.sql`
- `storage/postgres.py` dual-write for `embedding` (JSONB) and `embedding_vector` (`vector(512)`)
- `retrieval/embeddings.py`
- `retrieval/postgres.py`
- `retrieval/service.py`
- `eval/retrieval_metrics.py`

Test artifacts:

- `tests/test_retrieval_embeddings.py`
- `tests/test_retrieval_postgres.py`
- `tests/test_retrieval_metrics.py`

Documentation artifacts:

- `docs/retrieval/embedding_provider_selection.md`
- `docs/retrieval/retrieval_baseline.md`
- `docs/retrieval/retrieval_evaluation.md`
- `docs/retrieval/retrieval_runbook.md`

Verified test status after retrieval baseline implementation:

- `python3 -m pytest tests` -> `91 passed`

Local commits produced in this retrieval phase:

- `3d2e869` docs: add retrieval baseline planning docs
- `0c87d01` feat: add pgvector retrieval baseline and dual-write column
- `4886fed` feat: add retrieval quality metrics and threshold evaluation

### Suggestions

- Data Engineering Agent:
  - start the next small curated external slice (recommended: TAT-QA tiny) and validate retrieval recall deltas against the new baseline utilities
- API / Workflow Agent:
  - integrate retrieval service through MCP `document_retrieval` tool boundary before exposing direct API-level retrieval internals
- Foundation / DevOps Agent:
  - decide whether Docker image should include `data/` for smoke runs or keep the explicit `docker compose cp data api:/app/data` step in runbook

### Expectations

- Keep retrieval metadata contracts stable (`chunk_id`, `document_id`, `source_uri`, `metadata`) while expanding dataset coverage.
- Keep embedding dimension alignment explicit between provider output and `document_chunks.embedding_vector`.
- Keep retrieval quality changes measurable through `eval/retrieval_metrics.py` and deterministic tests before expanding workflow surface.

## Handoff 2026-05-19-2106Z: MCP Retrieval Flow Wired Through API Workflow

From: API / Workflow Agent

To: MCP Gateway / Tooling Agent, Guardrails / Evaluation Agent

### Completions

Completed the first end-to-end API workflow path for research requests using MCP `document_retrieval` tool boundaries.

Implemented in incremental local commits:

- `document_retrieval` tool request/response contracts and structured tool error model.
- MCP Gateway route skeleton with permission checker, rate-limit hook, cache hook, request ID propagation, and per-call audit records.
- `document_retrieval` handler wiring to retrieval service search path with validation/error mapping.
- Research workflow entry point that retrieves evidence only via gateway tool invocation.
- `POST /research` route with typed request/response schema and tool-error-to-HTTP status mapping.
- End-to-end regression coverage for `API -> workflow -> MCP gateway -> document_retrieval tool`.

Verification:

- `python3 -m pytest tests`
- result: `106 passed`

### Inputs

- API / Workflow responsibilities and boundaries from `AGENTS.md`.
- Product contracts and runtime chain requirements from `README.md`.
- Retrieval baseline handoff guidance from `docs/agent_handoff_log.md` (`Handoff 2026-05-19-1912Z`), especially:
  - integrate retrieval through MCP `document_retrieval` tool boundary
  - keep retrieval citation metadata contracts stable

### Outputs

Code artifacts:

- `mcp_gateway/errors.py`
- `mcp_gateway/schemas.py`
- `mcp_gateway/audit.py`
- `mcp_gateway/hooks.py`
- `mcp_gateway/gateway.py`
- `mcp_gateway/factory.py`
- `mcp_gateway/tools/document_retrieval.py`
- `agents/research_workflow.py`
- `api/routes/research.py`
- `api/main.py` updates for workflow wiring

Test artifacts:

- `tests/test_mcp_tool_contracts.py`
- `tests/test_mcp_gateway.py`
- `tests/test_mcp_document_retrieval_tool.py`
- `tests/test_research_workflow.py`
- `tests/test_research_api.py`
- `tests/test_research_e2e_mcp_path.py`

Behavior contracts now enforced:

- request ID propagates from API request to MCP tool calls and audit records
- retrieval evidence returned with `chunk_id`, `document_id`, `source_uri`, `metadata`
- `POST /research` maps tool errors to stable HTTP statuses (`422/403/429/503/500`)

### Suggestions

- MCP Gateway / Tooling Agent:
  - align gateway audit record schema with broader tool-call audit requirements (input hash, output refs, latency, cache hit/miss) before additional tools are added.
  - replace no-op cache/rate-limit hooks with concrete adapters once Redis-backed policies are finalized.
- Guardrails / Evaluation Agent:
  - insert citation coverage, faithfulness, moderation, and unsafe-financial-advice checks after workflow retrieval and before final output approval.
  - add blocked-output regression tests through `POST /research` once guardrail pipeline nodes are wired.

### Expectations

- Continue expanding research workflow through MCP tool boundaries only; avoid direct retrieval internals from API routes.
- Preserve tool and citation metadata contracts while adding more tools (`fund_metrics`, `citation_validator`, etc.).
- Keep request-traceability and auditability intact for every new workflow node and tool call.
