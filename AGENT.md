# Agent Development Principles

## Purpose

This file defines the engineering principles for building MCP Financial Research Agent. All implementation work should treat the system as a production service, even when running locally during development.

## Development Execution Agents

The project is executed by specialized development agents. Each agent owns a bounded delivery area, but all agents share responsibility for preserving production-shaped interfaces, tests, documentation, and handoff clarity.

### Data Engineering Agent

- Owns source data selection, synthetic seed data, curated external samples, source provenance, licensing notes, and data quality checks.
- Maintains `data/`, dataset manifests, sample source documentation, and small inspectable evaluation samples.
- Ensures no real client data, credentials, live brokerage data, or unsafe investment advice enter fixtures, tests, or examples.

### Ingestion / Backend Agent

- Owns batch ingestion, loaders, normalizers, canonical internal data models, ingestion jobs, and storage model mapping.
- Maintains the path from raw source files to `Document`, `DocumentChunk`, `StructuredRecord`, and `EvalCase` outputs.
- Keeps ingestion deterministic, testable, and ready for later PostgreSQL, pgvector, Redis, and MCP tool integration.

### Foundation / DevOps Agent

- Owns project foundation, runtime scaffolding, local developer experience, environment templates, dependency metadata, Docker Compose, pytest setup, and CI.
- Maintains `pyproject.toml`, `.env.example`, `docker-compose.yml`, `.github/workflows/`, basic settings, health checks, and service startup evidence.
- Ensures Phase 0 leaves the system installable, runnable, testable, and observable enough for later feature agents.

### API / Workflow Agent

- Owns FastAPI application structure, API routes, request/response schemas, workflow state transitions, and user-facing service contracts.
- Maintains research, ingestion, review, evaluation, and health endpoints as they become part of the implementation phases.
- Coordinates LangGraph workflow entry points without bypassing MCP Gateway, repository, guardrail, or audit boundaries.

### MCP Gateway / Tooling Agent

- Owns MCP Gateway routing, MCP server wiring, tool permission boundaries, tool schemas, structured tool errors, rate-limit hooks, cache hooks, and tool-call audit logs.
- Maintains MCP tools such as `fund_search`, `fund_metrics`, `document_retrieval`, `issue_search`, `citation_validator`, `pii_filter`, `moderation`, and `eval_runner`.
- Ensures agent workflows access operational capabilities through explicit tools rather than hidden direct dependencies.

### RAG / Retrieval Agent

- Owns chunking strategy, embedding integration, vector indexing, retrieval, reranking, citation candidate generation, and retrieval quality tests.
- Maintains retrieval modules and the evidence path from stored documents to cited research output.
- Preserves citation metadata, source references, and reproducibility needed for review, audit, and evaluation.

### Guardrails / Evaluation Agent

- Owns responsible AI checks, review report logic, evaluation case execution, anonymized evaluation records, metrics, and safety regression reporting.
- Maintains PII masking, moderation, prompt-injection checks, citation coverage, faithfulness checks, unsafe-financial-advice checks, and blocked-output behavior.
- Ensures quality and safety failures are visible through tests, review reports, audit records, and evaluation outputs.

## Product Boundaries

- Build a financial research and platform intelligence system, not an investment advisory product.
- Do not use real client data in local development, tests, fixtures, or examples.
- All financial outputs must preserve uncertainty, cite evidence where required, and include safety language when the workflow calls for it.
- Human review is part of the product workflow, not an optional decoration.

## Architecture Principles

- Keep the runtime path explicit: API request, LangGraph workflow, MCP Gateway, MCP tools, storage, guardrails, review, audit, and response.
- Raw external sources must be normalized before use. The canonical ingestion outputs are `Document`, `DocumentChunk`, `StructuredRecord`, and `EvalCase`.
- Agent workflows should access data through MCP tools or repository interfaces, not by reaching into source-specific loaders directly.
- MCP Gateway responsibilities include routing, permission boundaries, request ID propagation, audit logging, cache hooks, rate-limit hooks, and structured errors.
- Prefer replaceable adapters for external systems, including LLM providers, embedding providers, GitHub ingestion, and dataset loaders.

## Data Principles

- Separate batch ingestion from single research requests.
- Batch ingestion prepares knowledge, structured records, issue corpora, embeddings, and evaluation cases.
- `ResearchRequest` is the primary runtime input for user-facing work.
- Evaluation runs consume `EvalCase` records and generate repeatable `EvaluationRecord` outputs.
- Persist enough metadata to support citation, audit, debugging, replay, and anonymized evaluation.

## Implementation Stack

- Use Python 3.11+, FastAPI, LangGraph, PostgreSQL with pgvector, Redis, Docker Compose, OpenTelemetry-compatible instrumentation, pytest, and GitHub Actions.
- Use the MCP Python SDK where practical. If a local abstraction is needed, keep it protocol-compatible and easy to replace.
- Keep AWS Bedrock support behind a provider adapter. The default local path may use an OpenAI-compatible provider.
- Do not introduce Kubernetes, Kafka, a separate vector database, or a frontend unless a later requirement explicitly adds them.

## Reliability And Observability

- Every request must carry a request ID.
- Agent runs, MCP tool calls, guardrail checks, review decisions, ingestion jobs, and eval runs must be traceable.
- Logs must be structured JSON logs.
- Metrics should include request count, error count, latency, tool-call count, cache hit/miss, ingestion job status, and evaluation run status.
- Failures should be visible and diagnosable through logs, stored audit records, and clear API errors.

## Security And Responsible AI

- Run PII detection and masking where user input, external text, or generated output can contain sensitive data.
- Run moderation, prompt-injection, citation coverage, faithfulness, and unsafe-financial-advice checks where required by the workflow.
- Do not finalize blocked outputs.
- Keep tool permission boundaries explicit.
- Avoid logging secrets, raw credentials, access tokens, or unnecessary personal data.

## Testing Principles

- Add tests at the boundary where behavior matters: API routes, ingestion normalization, MCP tools, retrieval, guardrails, evaluation, and full workflow paths.
- Prefer deterministic fixtures for unit and integration tests.
- Test both success and failure paths, especially blocked outputs, missing citations, cache misses, and malformed inputs.
- Keep tests close to the contract they protect.

## Development Workflow

- Implement vertically: each phase should leave the system runnable and testable.
- Keep interfaces stable before expanding source coverage or model behavior.
- Favor simple production-shaped components over throwaway scripts.
- Before writing explanatory Markdown documents, agents must first state the document's purpose and intended audience, then ask the human which file name and directory are approved for writing.
- Document acceptance evidence for each phase, including commands, sample requests, sample responses, logs, metrics, and known gaps.
- Do not hide uncertainty. If a feature is incomplete, mark the gap explicitly in the phase report.

## Coding Style

- Keep modules small and ownership clear.
- Use English for code, comments, documentation, API schemas, logs, error messages, test names, fixtures, and commit messages.
- Use typed models for API contracts and canonical data formats.
- Prefer structured parsers and repository methods over ad hoc string manipulation.
- Add comments only where they clarify non-obvious workflow or safety decisions.
- Keep configuration in settings and environment variables, not hardcoded constants.

## Review Checklist

Before considering a change complete, verify:

- The relevant API or workflow path runs locally.
- Tests covering the changed behavior pass.
- Logs include request IDs and useful lifecycle events.
- Audit records capture key tool calls, citations, guardrail results, and review decisions when applicable.
- New data sources normalize into canonical formats.
- No real client data, secrets, or unsafe financial advice have been introduced.
