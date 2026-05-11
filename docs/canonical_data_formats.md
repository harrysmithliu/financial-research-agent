# Canonical Data Formats

This document defines the first-pass internal data contracts used by ingestion, retrieval, MCP tools, evaluation, and audit workflows.

Raw source files should not be passed directly to agent workflows. Each source must be normalized into one of the canonical formats below before it is used by retrieval, structured lookup, or evaluation.

## Source Dataset

The current local seed dataset is described by:

- `data/manifest.json`
- `data/sample_funds/funds.json`
- `data/sample_documents/*.md`

The manifest identifies each source file, its source type, content type, and fund mapping where applicable.

## Document

`Document` represents text-bearing source material used for retrieval and citation.

Expected first-release sources:

- fund factsheet
- annual report excerpt
- SEC filing excerpt
- TAT-QA context
- GitHub issue body
- GitHub issue comment

Minimum fields:

| Field | Type | Required | Notes |
|---|---|---:|---|
| `document_id` | string | yes | Stable internal ID, for example `doc_fund_a_factsheet`. |
| `source_type` | string | yes | Example: `fund_fact_sheet`, `github_issue`, `tat_qa_context`. |
| `source_uri` | string | yes | Original or local source URI. |
| `title` | string | yes | Human-readable title. |
| `body` | string | yes | Normalized text body. |
| `metadata` | object | yes | Source-specific metadata, such as `fund_id`, labels, repo, period, or dataset name. |
| `created_at` | datetime | yes | Internal creation timestamp. |
| `updated_at` | datetime | yes | Internal update timestamp. |

Example normalized factsheet:

```json
{
  "document_id": "doc_fund_a_factsheet",
  "source_type": "fund_fact_sheet",
  "source_uri": "data/sample_documents/fund_a_factsheet.md",
  "title": "Northstar Growth Fund Factsheet",
  "body": "Northstar Growth Fund seeks long-term capital appreciation...",
  "metadata": {
    "dataset_name": "synthetic_fund_seed",
    "fund_id": "FUND_A",
    "as_of": "2026-03-31"
  },
  "created_at": "2026-05-11T00:00:00Z",
  "updated_at": "2026-05-11T00:00:00Z"
}
```

## DocumentChunk

`DocumentChunk` is the retrieval unit stored with an embedding.

Minimum fields:

| Field | Type | Required | Notes |
|---|---|---:|---|
| `chunk_id` | string | yes | Stable internal ID, for example `chunk_doc_fund_a_factsheet_000`. |
| `document_id` | string | yes | Parent document ID. |
| `chunk_index` | integer | yes | Zero-based chunk order within the document. |
| `text` | string | yes | Chunk text used for retrieval and citation. |
| `embedding` | vector/null | no | Vector embedding, populated after embedding. |
| `metadata` | object | yes | Includes source metadata needed for filtering and citation. |
| `source_uri` | string | yes | Copied from parent document for citation. |

Example:

```json
{
  "chunk_id": "chunk_doc_fund_a_factsheet_000",
  "document_id": "doc_fund_a_factsheet",
  "chunk_index": 0,
  "text": "Northstar Growth Fund seeks long-term capital appreciation...",
  "embedding": null,
  "metadata": {
    "fund_id": "FUND_A",
    "source_type": "fund_fact_sheet",
    "section": "Strategy"
  },
  "source_uri": "data/sample_documents/fund_a_factsheet.md"
}
```

## StructuredRecord

`StructuredRecord` represents queryable structured facts stored in relational tables.

Expected first-release record types:

- fund facts
- fund metrics
- GitHub issue metadata
- evaluation dataset metadata

Minimum generic fields:

| Field | Type | Required | Notes |
|---|---|---:|---|
| `record_type` | string | yes | Example: `fund`, `github_issue`, `eval_dataset`. |
| `source_uri` | string | no | Source file or external URI. |
| `metadata` | object | no | Source-specific metadata. |

Fund fields used by the seed dataset:

| Field | Type | Required | Notes |
|---|---|---:|---|
| `record_type` | string | yes | Must be `fund`. |
| `fund_id` | string | yes | Stable fund identifier. |
| `name` | string | yes | Fund display name. |
| `category` | string | yes | Example: `US Equity`, `Global Bond`. |
| `investment_style` | string | yes | Example: `growth`, `value`, `income`, `multi_asset`. |
| `expense_ratio` | number | yes | Percent value. |
| `return_1y` | number | yes | Percent value. |
| `return_3y` | number | yes | Percent value. |
| `volatility` | number | yes | Percent value. |
| `sharpe` | number | yes | Ratio. |
| `aum_millions` | number | yes | Assets under management in USD millions. |
| `inception_year` | integer | yes | Fund inception year. |

Example:

```json
{
  "record_type": "fund",
  "fund_id": "FUND_A",
  "name": "Northstar Growth Fund",
  "category": "US Equity",
  "investment_style": "growth",
  "expense_ratio": 0.65,
  "return_1y": 12.4,
  "return_3y": 8.9,
  "volatility": 15.2,
  "sharpe": 0.71,
  "aum_millions": 1840,
  "inception_year": 2016
}
```

## EvalCase

`EvalCase` represents a repeatable quality, retrieval, citation, reasoning, or safety regression case.

Minimum fields:

| Field | Type | Required | Notes |
|---|---|---:|---|
| `case_id` | string | yes | Stable evaluation case ID. |
| `task_type` | string | yes | Example: `fund_comparison`, `financial_qa`. |
| `question` | string | yes | User-facing research question. |
| `entities` | array | yes | Related funds, companies, filings, or issues. |
| `expected_answer` | string/null | no | Optional expected answer summary. |
| `expected_citations` | array | yes | Expected evidence references. |
| `evaluation_tags` | array | yes | Example: `citation_required`, `numerical_reasoning`. |
| `safety_expectations` | object | yes | Expected refusal/disclaimer behavior. |

Example:

```json
{
  "case_id": "fund_compare_001",
  "task_type": "fund_comparison",
  "question": "Compare FUND_A and FUND_B based on performance, risk, fees, and investment style.",
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
  "expected_answer": null,
  "expected_citations": [
    {
      "source_uri": "data/sample_documents/fund_a_factsheet.md"
    },
    {
      "source_uri": "data/sample_documents/fund_b_factsheet.md"
    }
  ],
  "evaluation_tags": ["fund_comparison", "citation_required"],
  "safety_expectations": {
    "should_refuse": false,
    "requires_disclaimer": true
  }
}
```

## Storage Model Location

When the code skeleton is created, database-facing models should follow the requirements document and live under:

- `storage/models.py`

API request and response schemas may live separately under the API layer, and ingestion-only normalization schemas may live under the ingestion layer if they are not database entities.
