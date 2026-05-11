# Sample Data

This directory contains the first local seed dataset for MCP Financial Research Agent.

All files in this directory are synthetic and safe for local development, tests, examples, and demos. They do not contain real client data and should not be treated as investment advice.

## Dataset Manifest

`manifest.json` is the entry point for ingestion. It identifies each local source file, source type, content type, and record mapping.

Current dataset:

- Dataset name: `synthetic_fund_seed`
- Version: `0.1.0`
- Created at: `2026-05-11`

## Directory Layout

```text
data/
|- manifest.json
|- sample_funds/
|  `- funds.json
|- sample_documents/
|  |- fund_a_factsheet.md
|  |- fund_b_factsheet.md
|  |- fund_c_factsheet.md
|  `- fund_d_factsheet.md
|- sample_issues/
|  `- issues.json
`- eval_cases/
   `- fund_eval_cases.json
```

## Source Files

### `sample_funds/funds.json`

Structured synthetic fund records used for fund search, fund metrics lookup, and numerical financial QA.

Expected normalized output:

- `StructuredRecord`
- Later storage target: `Fund` or equivalent relational model

### `sample_documents/*.md`

Synthetic fund factsheets used for retrieval, citation, fund comparison, and due diligence brief generation.

Expected normalized output:

- `Document`
- `DocumentChunk`

### `sample_issues/issues.json`

Synthetic GitHub-like issue and comment records for platform intelligence workflows.

Expected normalized output:

- `StructuredRecord` for issue metadata
- `Document` records for issue body and comments

### `eval_cases/fund_eval_cases.json`

Repeatable evaluation cases for fund comparison, due diligence brief generation, and financial QA.

Expected normalized output:

- `EvalCase`

## Canonical Formats

Canonical internal data contracts are documented in:

- `docs/canonical_data_formats.md`

Raw source files should be normalized before agent workflows use them.

## Replacement Path

These local synthetic sources can later be replaced or expanded with:

- TAT-QA samples for financial QA and table/text reasoning
- FinAgent Benchmark samples for agentic finance evaluation
- GitHub API exports from OpenBB or QuantConnect Lean for platform issue research

External data should still flow through the same manifest and canonical normalization process.
