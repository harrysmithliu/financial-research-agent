# Retrieval Evaluation

## Purpose
Define retrieval metrics, thresholds, and summary behavior for baseline validation.

## Intended Audience
- RAG / Retrieval Agent
- Guardrails / Evaluation Agent
- Project owner and reviewers

## Implemented Metrics
- `Recall@k`
- `MRR@k` (mean reciprocal rank)
- `Citation Coverage`

Implemented in:
- `eval/retrieval_metrics.py`
- tested by `tests/test_retrieval_metrics.py`

## Metric Definitions
- `Recall@k`: fraction of expected evidence source URIs that appear in top-k retrieval results.
- `ReciprocalRank@k`: `1/rank` of the first expected source URI in top-k; `0` if none found.
- `MRR@k`: average reciprocal rank across evaluation cases.
- `Citation Coverage`: fraction of expected evidence source URIs covered by both retrieval results and citation pool.
  - If explicit cited URIs are absent, top-k retrieved URIs are used as citation pool fallback.

## Baseline Thresholds (Approved)
- Recall@5 >= 0.70
- MRR@5 >= 0.45
- Citation Coverage >= 0.80

## Next-Stage Thresholds
- Recall@5 >= 0.80
- MRR@5 >= 0.55
- Citation Coverage >= 0.90

## Summary Behavior
`RetrievalEvaluationSummary` reports:
- case count
- k
- averaged `recall_at_k`
- averaged `mrr_at_k`
- averaged `citation_coverage`
- threshold pass/fail flag

---
Created By: RAG / Retrieval Agent (Codex)
Created At (UTC): 2026-05-19T18:40:15Z
Last Updated At (UTC): 2026-05-19T19:12:08Z
