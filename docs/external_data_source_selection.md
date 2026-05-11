# External Data Source Selection

Created by: Data Engineering Agent

Created at: 2026-05-11 16:18:08 EDT

Date: 2026-05-11

Current phase: external data expansion after local manifest-driven ingestion is stable.

## Decision

Use `Guen/finagent-benchmark` as the first external dataset batch.

Primary source:

- Hugging Face dataset: `Guen/finagent-benchmark`
- URL: `https://huggingface.co/datasets/Guen/finagent-benchmark`
- License: MIT
- Size: fewer than 1,000 rows; dataset card states 133 benchmark questions
- Domain: SEC EDGAR-grounded financial QA

## Why This Source First

`Guen/finagent-benchmark` is the best first external batch because it is small, evaluation-oriented, and structurally close to the project's existing `EvalCase` contract.

Useful fields include:

- `id`
- `question`
- `type`
- `difficulty`
- `source_companies`
- `source_filing_types`
- `tolerance_pct`
- `requires_tools`
- `gold_answer`
- `gold_answer_numeric`
- `gold_evidence`
- `explanation`
- `verification_note`

These fields map naturally to:

- `EvalCase.question`
- `EvalCase.task_type`
- `EvalCase.expected_answer`
- `EvalCase.expected_citations`
- `EvalCase.evaluation_tags`
- `EvalCase.safety_expectations`
- supporting `Document` records built from `gold_evidence`

The dataset also includes adversarial and unavailable-answer cases, which are useful for future hallucination and citation-faithfulness checks.

## Runner-Up Source

`next-tat/TAT-QA` is a strong second source, but should come after FinAgent Benchmark.

Source:

- Hugging Face dataset: `next-tat/TAT-QA`
- URL: `https://huggingface.co/datasets/next-tat/TAT-QA`
- License: CC BY 4.0
- Size: 16,552 questions across 2,757 hybrid financial-report contexts
- Domain: table-text financial QA with numerical reasoning

Why not first:

- Larger dataset.
- More complex table-plus-paragraph source shape.
- Requires more careful conversion into `Document` and citation evidence records.
- Better suited after the first external batch proves the external-data normalization path.

## First Batch Scope

Add only 5 to 10 FinAgent Benchmark examples.

Prefer a balanced mini-slice:

- 1 fact extraction case
- 1 numerical reasoning case
- 1 temporal reasoning case
- 1 multi-hop or comparison case
- 1 adversarial or not-available case

Keep the sample small enough for manual review.

## Proposed Local Files

Recommended next-step files:

```text
data/external/
`- finagent_benchmark_sample.json
```

Optional later structure if source evidence is separated:

```text
data/external/
|- finagent_benchmark_sample.json
`- finagent_benchmark_evidence_documents.json
```

## Manifest Plan

After the sample is added, register it in `data/manifest.json` with:

```json
{
  "source_id": "finagent_benchmark_sample",
  "source_type": "huggingface_dataset",
  "source_uri": "data/external/finagent_benchmark_sample.json",
  "content_type": "eval_cases",
  "record_type": "eval_case",
  "dataset_name": "Guen/finagent-benchmark"
}
```

If evidence snippets are stored as separate documents, add a second manifest source with `content_type: "document"`.

## Provenance And License Notes

Document the following in `data/README.md` when the sample is added:

- source dataset URL
- source dataset license
- sample size
- retrieval date
- selection method
- whether records were copied directly, transformed, or manually curated
- reminder that source SEC filings are public regulatory disclosures, not client data

## Known Caveat

The Hugging Face dataset preview reported a dataset viewer generation error during review. The dataset card and file metadata were still available. The next step should prefer fetching the raw dataset file directly rather than relying on the hosted preview table.
