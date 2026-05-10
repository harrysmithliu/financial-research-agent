# MCP Financial Research Agent Requirements

## 1. Project Purpose

MCP Financial Research Agent is a production financial research and platform intelligence system built with MCP-based tool access, retrieval-augmented generation, guardrails, caching, auditability, human review, evaluation pipelines, and observability.

The project supports local development and production-oriented deployment boundaries. It covers MCP Server, MCP Gateway, AI Agent workflows, document vectorization, responsible AI controls, caching, reliability, and evaluation.

The system does not provide real investment advice.

## 2. Confirmed Implementation Target

The project will use the following implementation stack:

- Python 3.11+
- FastAPI
- MCP Python SDK, or a minimal MCP-compatible local abstraction where needed
- LangGraph for agent workflow orchestration
- PostgreSQL with pgvector
- Redis for cache and lightweight background jobs
- Docker Compose for local runtime
- OpenTelemetry-compatible instrumentation and structured JSON logging
- pytest for automated tests
- GitHub Actions for CI
- Provider adapter for OpenAI-compatible APIs and an expansion path for AWS Bedrock

The first production release should avoid unnecessary infrastructure:

- No Kubernetes requirement
- No separate vector database beyond pgvector
- No Kafka requirement in the first implementation
- No paid cloud dependency for normal local development
- No frontend requirement unless explicitly added later

## 3. Target System Capabilities

The system should provide:

- MCP Server, MCP Gateway, and AI Agent architecture
- LangGraph workflow for planning, retrieval, generation, guardrails, review, and persistence
- batch ingestion of financial and operational data sources
- document loading, cleaning, chunking, embedding, pgvector indexing, and citation-aware retrieval
- structured data lookup through MCP tools
- guardrails for PII filtering, moderation, prompt-injection checks, and unsafe financial advice checks
- caching for embeddings, retrieval results, tool calls, and optional model responses
- audit trails for agent runs, tool calls, retrieved evidence, review decisions, and final outputs
- anonymized evaluation records and repeatable regression reports
- production engineering habits: clean APIs, tests, Docker-based local run, structured logs, request IDs, metrics, and documentation

## 4. Data Source Strategy

The system has two primary forms of data input:

1. Batch input: prepares the knowledge base, structured records, operational issue corpus, and evaluation datasets.
2. Manual single-request input: runs one user-facing research or analysis task.

Evaluation runs are a third operational mode: they consume a batch of eval cases and internally generate many research requests.

### 4.1 Batch Input Sources

The first production release should use a curated combination of:

- synthetic fund facts and synthetic fund factsheets for fund comparison and due diligence workflows
- a small sample from a public finance QA or financial report dataset, such as TAT-QA
- a small sample from an agentic finance benchmark, such as FinAgent Benchmark, for evaluation
- optional GitHub issues and comments from an open-source finance or financial platform repository, such as OpenBB or QuantConnect Lean, for platform intelligence scenarios

Batch input is used to populate:

- structured PostgreSQL records
- document records
- document chunks
- embeddings in pgvector
- evaluation cases

### 4.2 Manual Single-Request Input

Manual input is the runtime request submitted by a user, service client, or operational script. It is represented by `ResearchRequest` and is handled through the research API.

Examples:

- compare two funds based on performance, risk, fees, and investment style
- generate a due diligence brief for one fund
- summarize recent GitHub issues related to a financial platform topic
- answer a freeform financial research question with citations

### 4.3 Evaluation Run Input

Evaluation input is represented by `EvalCase` records. An evaluation run loads a dataset, converts each case into a `ResearchRequest`, runs the agent workflow, and stores `EvaluationRecord` outputs.

## 5. Canonical Internal Data Formats

Raw sources should not be passed directly to the agent. They must first be normalized into a small set of canonical internal formats.

### 5.1 Document

`Document` represents text-bearing source material used for retrieval and citation.

Examples:

- fund factsheet
- annual report excerpt
- SEC filing excerpt
- TAT-QA context
- GitHub issue body
- GitHub issue comment

Minimum fields:

- `document_id`
- `source_type`
- `source_uri`
- `title`
- `body`
- `metadata`
- `created_at`
- `updated_at`

Example:

```json
{
  "document_id": "doc_openbb_issue_7473",
  "source_type": "github_issue",
  "source_uri": "https://github.com/OpenBB-finance/OpenBB/issues/7473",
  "title": "[Bug] OptionsChainsData schema/serializer mismatch",
  "body": "Issue body text...",
  "metadata": {
    "repo": "OpenBB-finance/OpenBB",
    "labels": ["bug", "platform"],
    "domain": "financial_platform"
  }
}
```

### 5.2 DocumentChunk

`DocumentChunk` is the retrieval unit stored with an embedding.

Minimum fields:

- `chunk_id`
- `document_id`
- `chunk_index`
- `text`
- `embedding`
- `metadata`
- `source_uri`

### 5.3 StructuredRecord

`StructuredRecord` represents queryable structured facts stored in relational tables.

Examples:

- fund facts
- fund metrics
- GitHub issue metadata
- evaluation dataset metadata

Example fund record:

```json
{
  "record_type": "fund",
  "fund_id": "FUND_A",
  "name": "Northstar Growth Fund",
  "category": "US Equity",
  "expense_ratio": 0.65,
  "return_1y": 12.4,
  "return_3y": 8.9,
  "volatility": 15.2,
  "sharpe": 0.71
}
```

### 5.4 EvalCase

`EvalCase` represents a repeatable test case for quality, retrieval, citation, reasoning, or safety regression.

Minimum fields:

- `case_id`
- `task_type`
- `question`
- `entities`
- `expected_answer`
- `expected_citations`
- `evaluation_tags`
- `safety_expectations`

Example:

```json
{
  "case_id": "finagent_001",
  "task_type": "financial_qa",
  "question": "What was the year-over-year revenue growth?",
  "entities": [],
  "expected_answer": "...",
  "expected_citations": [
    {
      "source_uri": "sec://sample/10-k/2024",
      "evidence_text": "..."
    }
  ],
  "evaluation_tags": ["numerical_reasoning", "citation_required"],
  "safety_expectations": {
    "should_refuse": false,
    "requires_disclaimer": false
  }
}
```

## 6. System Entry Points

The first production release should expose three primary API entry points and one review entry point.

### 6.1 Batch Ingestion

Endpoint:

```http
POST /ingestion/jobs
```

Purpose:

Start a batch ingestion job for local files, curated datasets, or GitHub issues.

Example request:

```json
{
  "source_type": "local_directory",
  "source_uri": "data/sample_documents",
  "dataset_name": "sample_fund_docs",
  "options": {
    "rebuild_index": true
  }
}
```

Supported source types for the first production release:

- `local_directory`
- `local_file`
- `sample_dataset`
- `github_issues`

### 6.2 Research Request

Endpoint:

```http
POST /research
```

Purpose:

Run one user-facing agent workflow.

Example request:

```json
{
  "user_id": "user_001",
  "session_id": "session_001",
  "task_type": "fund_comparison",
  "question": "Compare Fund A and Fund B based on performance, risk, fees, and investment style.",
  "entities": [
    {
      "entity_type": "fund",
      "entity_id": "FUND_A"
    },
    {
      "entity_type": "fund",
      "entity_id": "FUND_B"
    }
  ],
  "retrieval_filters": {
    "source_types": ["fund_fact_sheet", "annual_report"]
  },
  "options": {
    "require_citations": true,
    "require_review": true,
    "output_format": "summary"
  }
}
```

Supported task types for the first production release:

- `fund_comparison`
- `due_diligence_brief`
- `financial_qa`
- `platform_issue_research`

### 6.3 Evaluation Run

Endpoint:

```http
POST /eval/runs
```

Purpose:

Run a batch of eval cases and produce anonymized evaluation records and a regression report.

Example request:

```json
{
  "dataset_id": "finagent_small",
  "run_name": "baseline_local",
  "anonymize": true
}
```

### 6.4 Review Decision

Endpoint:

```http
POST /review/decisions
```

Purpose:

Allow a reviewer to approve, reject, or request changes for an agent output.

Example request:

```json
{
  "review_report_id": "review_001",
  "decision": "approved",
  "reviewer_id": "reviewer_001",
  "comment": "Citations and safety checks look acceptable."
}
```

Supported decisions:

- `approved`
- `rejected`
- `changes_requested`

## 7. Core Product Loop

The minimal closed-loop workflow is:

1. User submits a `ResearchRequest`.
2. LangGraph planner creates a short research plan.
3. Agent calls MCP tools through the MCP Gateway.
4. MCP tools retrieve structured fund facts, issue metadata, document chunks, and citation candidates.
5. Agent generates a cited research answer, due diligence brief, or platform issue summary.
6. Guardrails run before finalization.
7. A human-readable review report is generated.
8. Reviewer approves, rejects, or requests changes.
9. Approved output is stored with audit logs and evaluation metadata.

## 8. Primary Product Scenarios

### 8.1 Scenario A: Fund Research Q&A

User asks:

```text
Compare Fund A and Fund B based on performance, risk, fees, and investment style.
```

Expected output:

- concise comparison summary
- fund metrics table
- cited evidence from source documents
- risk and uncertainty notes
- financial-safety disclaimer
- review report with guardrail and evidence checks

### 8.2 Scenario B: Due Diligence Brief Generator

User selects one fund and asks the agent to generate a due diligence brief.

Expected sections:

- fund overview
- strategy and style summary
- performance notes
- risk summary
- fee and expense summary
- portfolio exposure notes
- key concerns
- analyst review checklist
- cited evidence
- review report

### 8.3 Scenario C: Responsible AI Review Pipeline

Every generated answer should pass through review checks:

- PII filtering
- moderation
- prompt-injection detection
- citation coverage check
- faithfulness check
- unsafe financial advice check
- anonymized evaluation record generation

### 8.4 Scenario D: Platform Issue Research

User asks:

```text
Summarize recent OpenBB issues related to options data schemas and identify common failure patterns.
```

Expected output:

- issue summary grouped by theme
- cited GitHub issues and comments
- status and label summary
- operational risk notes
- suggested follow-up questions

This scenario covers GitHub issue ingestion, MCP tool access, RAG over operational text, and production platform intelligence.

## 9. Suggested System Architecture

```text
mcp-financial-research-agent/
|
|- agents/
|  |- graph.py
|  |- planner.py
|  |- research_agent.py
|  |- review_agent.py
|  `- state.py
|
|- api/
|  |- main.py
|  `- routes/
|     |- ingestion.py
|     |- research.py
|     |- review.py
|     |- eval.py
|     `- health.py
|
|- mcp_gateway/
|  |- router.py
|  |- auth.py
|  |- rate_limit.py
|  |- cache.py
|  `- audit.py
|
|- mcp_server/
|  |- server.py
|  `- tools/
|     |- fund_search.py
|     |- fund_metrics.py
|     |- document_retrieval.py
|     |- issue_search.py
|     |- citation_validator.py
|     |- pii_filter.py
|     |- moderation.py
|     `- eval_runner.py
|
|- ingestion/
|  |- jobs.py
|  |- loaders.py
|  |- normalizers.py
|  |- chunker.py
|  |- embedder.py
|  |- indexer.py
|  `- sources/
|     |- local_files.py
|     |- sample_datasets.py
|     `- github_issues.py
|
|- retrieval/
|  |- vector_store.py
|  |- retriever.py
|  `- reranker.py
|
|- eval/
|  |- datasets/
|  |- runner.py
|  |- metrics.py
|  |- llm_judge.py
|  `- reports.py
|
|- storage/
|  |- models.py
|  |- repository.py
|  `- migrations/
|
|- llm/
|  |- provider.py
|  |- openai_compatible.py
|  `- bedrock.py
|
|- observability/
|  |- logging.py
|  |- tracing.py
|  `- metrics.py
|
|- config/
|  |- settings.py
|  `- prompts/
|     |- research.yaml
|     |- review.yaml
|     `- safety.yaml
|
|- data/
|  |- sample_documents/
|  |- sample_funds/
|  |- sample_issues/
|  `- eval_cases/
|
|- infra/
|  |- docker/
|  `- observability/
|
|- tests/
|- docs/
|- pyproject.toml
|- docker-compose.yml
|- README.md
`- .env.example
```

## 10. MCP Tool Requirements

The first production release should expose these MCP tools:

- `fund_search`: search available funds by name, category, or identifier
- `fund_metrics`: return structured fund metrics for selected funds
- `document_retrieval`: retrieve relevant chunks with citation metadata
- `issue_search`: search ingested GitHub issues and comments by repo, label, state, and text query
- `citation_validator`: check whether key claims have supporting evidence
- `pii_filter`: detect and mask PII in inputs and outputs
- `moderation`: detect unsafe or disallowed content
- `eval_runner`: run or inspect evaluation cases

The MCP Gateway must provide:

- tool routing
- tool permission boundary
- request ID propagation
- audit logging
- rate-limit hooks
- cache hooks
- structured error handling

## 11. Data Model Requirements

Minimum entities:

- `Fund`
- `Document`
- `DocumentChunk`
- `ResearchRequest`
- `AgentRun`
- `ToolCall`
- `ReviewReport`
- `ReviewDecision`
- `EvaluationCase`
- `EvaluationRun`
- `EvaluationRecord`
- `IngestionJob`
- `CacheRecord`
- `GitHubIssue`
- `GitHubIssueComment`

Minimum audit fields:

- request id
- user/session id placeholder
- task type
- prompt version
- model/provider id
- tool name
- tool input hash
- tool output reference
- retrieved document references
- citation references
- guardrail result
- reviewer decision
- final output reference
- latency
- cache hit/miss
- timestamps

## 12. Non-Functional Requirements

### 12.1 Local Runtime

- The service must run locally through Docker Compose.
- PostgreSQL, pgvector, Redis, and the API service must be included.
- Local development should not require paid cloud infrastructure.

### 12.2 Observability

- Logs must be structured JSON logs.
- Every request must have a request ID.
- Agent runs, MCP tool calls, guardrail checks, review decisions, and eval runs must be traceable.
- A metrics endpoint should expose basic latency, error count, request count, tool-call count, and cache-hit metrics.

### 12.3 Caching

The first production release should support:

- embedding cache
- retrieval cache
- tool result cache
- optional model response cache

Cache invalidation rules must be documented.

### 12.4 Security and Responsible AI

The first production release should include:

- PII detection and masking
- moderation checks
- prompt-injection checks
- unsafe financial advice checks
- tool permission boundaries
- no use of real client data
- disclaimers for financial research outputs

### 12.5 Testing

The first production release should include:

- API route tests
- ingestion tests
- MCP tool tests
- retrieval tests
- guardrail tests
- eval runner tests
- workflow tests for at least one complete research path

## 13. Implementation Phases

### Phase 0: Project Foundation

Goal:

Create the local service foundation and selected stack.

Scope:

- project skeleton
- FastAPI app
- settings module
- health endpoint
- Docker Compose with API, PostgreSQL/pgvector, and Redis
- structured logging foundation
- pytest setup
- GitHub Actions CI

Acceptance report must include:

- local setup evidence
- health endpoint result
- Docker Compose startup evidence
- test command output
- known gaps

### Phase 1: Batch Ingestion and Storage

Goal:

Load canonical source data into PostgreSQL and pgvector.

Scope:

- `POST /ingestion/jobs`
- local file and local directory ingestion
- sample fund facts ingestion
- document normalization
- chunking
- embedding
- pgvector indexing
- ingestion audit records

Acceptance report must include:

- sample ingestion request
- source-to-Document example
- source-to-StructuredRecord example
- chunk and embedding example
- ingestion test summary

### Phase 2: Research Q&A Closed Loop

Goal:

Deliver a complete research workflow.

Scope:

- `POST /research`
- LangGraph workflow state
- planner node
- MCP Gateway router
- MCP tools for fund metrics and document retrieval
- cited answer generation
- audit record persistence
- basic provider adapter

Acceptance report must include:

- sample research request
- sample response
- LangGraph step summary
- MCP tool call trace
- citation examples
- test summary

### Phase 3: Human Review and Guardrail Pipeline

Goal:

Add responsible AI review before final output approval.

Scope:

- human-readable review report
- reviewer decision endpoint
- PII filter
- moderation check
- prompt-injection check
- unsafe financial advice check
- blocked-output behavior

Acceptance report must include:

- review report example
- approval/rejection examples
- guardrail test cases
- audit log sample

### Phase 4: Due Diligence Brief Generator

Goal:

Deliver a richer financial research output.

Scope:

- due diligence brief task type
- structured report generation
- analyst checklist
- expanded fund metadata
- citation validation
- report storage

Acceptance report must include:

- generated brief sample
- citation coverage summary
- reviewer decision
- quality gaps and next steps

### Phase 5: Platform Issue Research

Goal:

Deliver GitHub issue ingestion and operational intelligence over a finance-related platform.

Scope:

- GitHub issues batch ingestion
- GitHub issue and comment normalization
- `issue_search` MCP tool
- platform issue research task type
- cited issue summary output

Acceptance report must include:

- GitHub ingestion sample
- normalized issue example
- issue-search tool trace
- platform issue summary response

### Phase 6: Caching and Performance Hardening

Goal:

Show production-minded cost and latency controls.

Scope:

- embedding cache
- retrieval cache
- tool result cache
- optional model response cache
- latency and cache-hit metrics
- cache invalidation documentation

Acceptance report must include:

- before/after latency comparison
- cache-hit examples
- invalidation policy
- risk notes

### Phase 7: Evaluation and Anonymized Regression Pipeline

Goal:

Make quality measurable and repeatable.

Scope:

- `POST /eval/runs`
- eval case format
- anonymized input/output records
- retrieval relevance metric
- citation coverage metric
- faithfulness judge
- safety regression report

Acceptance report must include:

- eval dataset sample
- metric report
- anonymization example
- quality trend notes

### Phase 8: Deployment and Observability

Goal:

Make the system operate as a production service.

Scope:

- Docker Compose local runtime
- structured logs
- request ids
- OpenTelemetry-compatible tracing
- tool-call tracing
- metrics endpoint
- deployment notes
- operational runbook

Acceptance report must include:

- Docker run evidence
- log sample
- trace or request lifecycle sample
- metrics sample
- operational runbook notes

## 14. Release Acceptance Checklist

The release must show:

- batch ingestion of sample fund documents and structured fund facts
- a fund comparison question answered with citations
- a due diligence brief generated from sample data
- a human-readable responsible AI review report
- reviewer approval, rejection, or changes-requested flow
- MCP tool calls flowing through the gateway
- audit logs for tool calls and review decisions
- GitHub issue ingestion and platform issue research
- evaluation report with anonymized examples
- cache-hit evidence
- Docker-based local run
- structured logs and metrics
- clear README and architecture diagram

## 15. Non-Goals

- Real investment advice
- Live brokerage or trading integration
- Production use with real client data
- Large-scale document crawling
- Paid cloud dependency for local development
- Fully autonomous financial recommendations without review
- A full frontend application
- Kubernetes deployment in the first production release

## 16. Success Criteria

The project is successful when an operator can run it locally, ingest sample data, submit a realistic financial research request, inspect MCP tool calls, review the generated answer and guardrail report, approve the output, run an evaluation batch, and see the result stored with audit, citation, cache, and evaluation metadata.
