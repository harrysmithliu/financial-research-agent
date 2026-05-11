# Agent Handoff Log

This document is the shared handoff log for all agents working on MCP Financial Research Agent.

## How To Use This Document

All agents should treat this file as durable project memory for cross-agent handoffs.

When an agent finishes a bounded phase or hands work to another agent, append a new dated handoff entry in chronological order. Do not delete or rewrite completed handoff entries unless the user explicitly asks for cleanup.

Completed handoffs and planned future checkpoints use different heading formats:

- Completed handoff: `## Handoff YYYY-MM-DD-A: Short Title`
- Planned future checkpoint: `## Planned Checkpoint: Short Title`

Only completed handoffs receive dated sequence suffixes such as `A`, `B`, or `C`. Planned checkpoints do not receive sequence numbers and do not reserve a position in the completed handoff history.

Write a planned checkpoint when a future return point is already known but the current agent is not ready to hand off completed work yet. Planned checkpoints are especially useful for cross-agent loops, such as external data expansion returning to ingestion, or canonical ingestion returning later for storage persistence.

Place planned checkpoints immediately after the completed handoff that creates or explains the future return point. Keep them in expected workflow order. If a new completed handoff occurs before a planned checkpoint becomes active, insert the completed handoff in chronological order without renumbering previous completed handoffs, and keep the planned checkpoint near the handoff it logically follows.

When a planned checkpoint becomes active, either convert it into a completed handoff using that day's dated heading, or create a new completed handoff that explicitly references the planned checkpoint. Do not leave an active checkpoint marked as `planned` after the handoff is complete.

Each handoff entry should include:

- from agent or role
- to agent or role
- handoff status: `ready`, `blocked`, or `planned`
- goal for the next agent
- input artifacts and reference docs
- suggested first task
- acceptance criteria
- known gaps or out-of-scope work

Each planned checkpoint should include:

- date
- from agent or role
- to agent or role
- status: `planned`
- trigger conditions
- goal
- suggested first task
- acceptance criteria
- known gaps or out-of-scope work

Agents should keep this document concise but operational. The next agent should be able to start work from the latest relevant entry without reconstructing context from chat history.

## Handoff 2026-05-11-A: Data Seed To Ingestion

Date: 2026-05-11

From agent: Data Engineering Agent

To agent: Ingestion / Backend Agent

Status: `ready`

### Goal

Implement the first production-shaped batch ingestion path for the local synthetic seed dataset.

The ingestion path should read `data/manifest.json`, load each declared source, normalize raw source data into canonical internal formats, and leave clear interfaces for chunking, embedding, storage, and MCP tool access.

### Input Artifacts

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

### Suggested First Task

Create the initial project code skeleton for Phase 1 ingestion:

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

Keep models and loaders small. The first milestone should run locally without PostgreSQL, pgvector, Redis, or an LLM provider.

### Required Normalization Behavior

Implement loading and normalization for:

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

### Implementation Notes

- Follow the package layout in `docs/financial_research_agent_requirements.md`.
- Place database-facing models in `storage/models.py`.
- Keep API schemas separate from storage models when API routes are added.
- Do not pass raw source data directly to agent workflows.
- Preserve `source_uri`, `source_type`, `dataset_name`, and entity metadata for citation, audit, debugging, replay, and evaluation.
- Do not introduce real client data or live investment advice.

### Minimal Acceptance Criteria

The first ingestion handoff is complete when:

- `data/manifest.json` can be parsed.
- All declared local source files can be resolved from the repository root.
- `funds.json` normalizes into four fund `StructuredRecord` items.
- Four factsheets normalize into four `Document` items.
- Issue sample data normalizes into issue metadata records plus issue/comment documents.
- Five fund eval cases normalize into five `EvalCase` items.
- Unit tests cover successful loading and at least one malformed input path.

### Suggested Test Focus

Start with deterministic tests around:

- manifest parsing
- source path resolution
- fund record validation
- markdown factsheet title/body extraction
- issue/comment normalization
- eval case validation

### Out Of Scope

- Embedding generation
- pgvector indexing
- PostgreSQL migrations
- Redis-backed jobs
- FastAPI route wiring
- LangGraph workflow execution
- MCP Gateway and MCP tools

These should follow after the local normalization path is stable.

## Handoff 2026-05-11-B: Ingestion Stable To External Data Expansion

Date: 2026-05-11

From agent: Ingestion / Backend Agent

To agent: Data Engineering Agent

Status: `ready`

### Completed Ingestion Work

The first local manifest-driven ingestion path is stable and ready for external data expansion.

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

Current output shape:

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

### Goal

Expand the local seed dataset with small, curated external samples from Hugging Face and GitHub while preserving the same manifest-driven ingestion contract.

The next agent should start with data expansion, not backend rewiring. Keep additions small and inspectable.

### Input Artifacts And Reference Docs

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

### Suggested Data Sources

- TAT-QA small sample for financial QA and table/text reasoning.
- FinAgent Benchmark small sample for agentic finance evaluation.
- OpenBB or QuantConnect Lean GitHub issues and comments for platform issue research.

### Required Data Engineering Work

- Add curated external samples in small batches only.
- Normalize Hugging Face samples into `Document` and `EvalCase` records.
- Normalize GitHub issues and comments into issue metadata `StructuredRecord` items plus issue/comment `Document` records.
- Update `data/manifest.json` with each new source.
- Update `data/README.md` with source provenance, sample size, licensing notes, and replacement path.
- Add data quality checks for missing fields, duplicate `source_uri`, broken citations, and unsupported task types.

### Suggested First Task

Add a tiny external eval dataset slice:

- 5 to 10 TAT-QA-style cases, or
- 5 to 10 FinAgent Benchmark cases.

Keep the first external batch small enough that reviewers can inspect every record manually.

### Minimal Acceptance Criteria

The next data expansion handoff is complete when:

- External source provenance is documented.
- New samples are listed in `data/manifest.json`.
- New samples normalize through the same ingestion path as synthetic seed data.
- Eval cases include expected citations or clear evidence references.
- No real client data, credentials, or unsafe investment advice are introduced.

### Known Gaps And Out Of Scope

Known gaps:

- `load_seed_dataset` is local and synchronous.
- No PostgreSQL persistence, pgvector indexing, Redis jobs, FastAPI route wiring, MCP Gateway, or LangGraph execution yet.
- External data source schemas are not implemented yet.
- Data quality checks are limited to deterministic model and normalizer validation.

Out of scope for the next Data Engineering Agent:

- Large-scale dataset mirroring
- Unbounded GitHub crawling
- Paid cloud ingestion
- Live brokerage or trading data
- Production use of real client data
- Real investment advice

### Out Of Scope

- Embedding generation
- pgvector indexing
- PostgreSQL migrations
- Redis-backed jobs
- FastAPI route wiring
- LangGraph workflow execution
- MCP Gateway and MCP tools

## Planned Checkpoint: External Data Expansion Back To Ingestion

Date: 2026-05-11

From agent: Data Engineering Agent

To agent: Ingestion / Backend Agent

Status: `planned`

### Trigger

Start this handoff after the Data Engineering Agent has added a small, curated external dataset batch.

Minimum trigger conditions:

- New external sample files are present in `data/`.
- `data/manifest.json` lists each new external source.
- `data/README.md` documents source provenance, sample size, licensing notes, and replacement path.
- External samples are small enough for manual review.
- No real client data, credentials, live trading data, or unsafe investment advice has been introduced.

### Goal

Adapt and harden the ingestion normalization layer so external samples pass through the same canonical contract as the local synthetic seed dataset.

### Suggested First Task

Run the existing ingestion test suite, inspect the new manifest entries, and identify whether each new source can map to existing `Document`, `StructuredRecord`, or `EvalCase` models without schema changes.

### Acceptance Criteria

- New external sources normalize through the manifest-driven ingestion path.
- Any new source type or record type has deterministic normalizer coverage.
- Tests cover successful normalization and at least one malformed external sample path.
- Existing synthetic seed ingestion remains stable.
- Canonical fields required for citation, audit, filtering, and evaluation are preserved.

### Known Gaps Or Out Of Scope

- Do not add PostgreSQL persistence in this checkpoint unless explicitly directed.
- Do not start large-scale crawling or dataset mirroring.
- Do not introduce paid cloud dependencies.
- Keep external sample handling small, reviewable, and reversible.

## Planned Checkpoint: Canonical Ingestion To Storage Persistence

Date: 2026-05-11

From agent: Ingestion / Backend Agent

To agent: Ingestion / Backend Agent

Status: `planned`

### Trigger

Start this checkpoint after local and first external sample normalization are stable enough that schema churn is low.

Minimum trigger conditions:

- Synthetic seed ingestion passes end to end.
- First external sample batch normalizes through the same ingestion path.
- Canonical `Document`, `StructuredRecord`, and `EvalCase` fields are stable.
- Data quality checks cover missing fields, duplicate source identifiers, broken citations, and unsupported task types.

### Goal

Move from in-memory canonical normalization toward durable ingestion storage while preserving auditability and replay.

### Suggested First Task

Design the repository boundary between canonical ingestion outputs and storage models before adding database writes.

### Acceptance Criteria

- Canonical objects can be mapped to planned PostgreSQL entities without losing citation or audit metadata.
- Ingestion job records include source identifiers, dataset name, counts, status, errors, and timestamps.
- Storage work remains testable locally and does not require an LLM provider.
- PostgreSQL/pgvector integration is introduced behind clear repository or indexer interfaces.

### Known Gaps Or Out Of Scope

- Do not wire the full `POST /ingestion/jobs` API until the repository boundary is clear.
- Do not generate embeddings or build pgvector indexes before document chunking behavior is agreed.
- Do not implement MCP Gateway, LangGraph workflows, or research answer generation in this checkpoint.
