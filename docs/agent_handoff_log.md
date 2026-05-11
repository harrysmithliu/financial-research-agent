# Agent Handoff Log

This document is the shared handoff log for all agents working on MCP Financial Research Agent.

## How To Use This Document

All agents should treat this file as durable project memory for cross-agent handoffs.

When an agent finishes a bounded phase or hands work to another agent, append a new dated handoff entry in chronological order. Do not delete or rewrite completed handoff entries unless the user explicitly asks for cleanup.

Completed handoffs and planned future checkpoints use different heading formats:

- Completed handoff: `## Handoff YYYY-MM-DD-A: Short Title`
- Planned future checkpoint: `## Planned Checkpoint: Short Title`

Only completed handoffs receive dated sequence suffixes such as `A`, `B`, or `C`. Planned checkpoints do not receive sequence numbers and do not reserve a position in the completed handoff history.

If a new completed handoff occurs before a planned checkpoint becomes active, append the new completed handoff above or below the planned checkpoint wherever it is easiest to keep the document readable. Do not renumber completed historical handoffs. When a planned checkpoint actually becomes active, convert it into a new completed handoff using that day's dated heading, or create a new completed handoff that references the planned checkpoint.

Each handoff entry should include:

- from agent or role
- to agent or role
- handoff status: `ready`, `blocked`, or `planned`
- goal for the next agent
- input artifacts and reference docs
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

- `docs/mcp_financial_research_agent_requirements.md`
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

- Follow the package layout in `docs/mcp_financial_research_agent_requirements.md`.
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

## Planned Checkpoint: Ingestion Stable To External Data Expansion

Date: 2026-05-11

From agent: Ingestion / Backend Agent

To agent: Data Engineering Agent

Status: `planned`

### Trigger

Start this handoff only after the first local ingestion path is stable.

Minimum trigger conditions:

- `data/manifest.json` is parsed by code.
- All local synthetic sources resolve from the repository root.
- Fund records, factsheets, synthetic issues, and eval cases normalize into canonical objects.
- At least one local ingestion test path passes end to end without requiring PostgreSQL, pgvector, Redis, or an LLM provider.
- Canonical model fields are stable enough that external samples can be mapped without repeated schema churn.

### Goal

Expand the local seed dataset with small, curated external samples from Hugging Face and GitHub while preserving the same manifest-driven ingestion contract.

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

The external data expansion handoff is complete when:

- External source provenance is documented.
- New samples are listed in `data/manifest.json`.
- New samples normalize through the same ingestion path as synthetic seed data.
- Eval cases include expected citations or clear evidence references.
- No real client data, credentials, or unsafe investment advice are introduced.

### Out Of Scope

- Large-scale dataset mirroring
- Unbounded GitHub crawling
- Paid cloud ingestion
- Live brokerage or trading data
- Production use of real client data
