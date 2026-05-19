# Retrieval Evaluation

## Purpose
Define retrieval quality metrics, threshold policy, and reporting format for baseline validation.

## Intended Audience
- RAG / Retrieval Agent
- Guardrails / Evaluation Agent
- Project owner and reviewers

## Baseline Metrics
- Recall@k
- MRR@k
- Citation Coverage

## Baseline Thresholds (Approved)
- Recall@5 >= 0.70
- MRR@5 >= 0.45
- Citation Coverage >= 0.80

## Next-Stage Target Thresholds
- Recall@5 >= 0.80
- MRR@5 >= 0.55
- Citation Coverage >= 0.90

## Reporting Requirements
Each evaluation record should include:
- dataset slice
- k values tested
- metric values
- pass/fail vs baseline thresholds
- known failure patterns

## Notes
Metric formulas and evaluation scripts will be linked after Batch 3 implementation.

---
Created By: RAG / Retrieval Agent (Codex)
Created At (UTC): 2026-05-19T18:40:15Z
