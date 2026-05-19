from __future__ import annotations

import pytest

from eval.retrieval_metrics import (
    BASELINE_THRESHOLDS,
    RetrievalCaseMetrics,
    evaluate_retrieval_case,
    expected_source_uris_for_eval_case,
    summarize_retrieval_metrics,
)
from storage.models import EvalCase


def test_expected_source_uris_for_eval_case_preserves_order_and_uniqueness() -> None:
    eval_case = EvalCase(
        case_id="case_001",
        task_type="financial_qa",
        question="What changed in the expense ratio?",
        entities=[],
        expected_citations=[
            {"source_uri": "data/doc_a.md"},
            {"source_uri": "data/doc_b.md"},
            {"source_uri": "data/doc_a.md"},
            {"source_uri": " "},
            {},
        ],
        evaluation_tags=["citation_required"],
        safety_expectations={"must_include_uncertainty": True},
    )

    assert expected_source_uris_for_eval_case(eval_case) == (
        "data/doc_a.md",
        "data/doc_b.md",
    )


def test_evaluate_retrieval_case_calculates_recall_mrr_and_coverage() -> None:
    metrics = evaluate_retrieval_case(
        case_id="case_002",
        expected_source_uris=("data/doc_a.md", "data/doc_b.md"),
        retrieved_source_uris=("data/doc_c.md", "data/doc_b.md", "data/doc_a.md"),
        k=2,
    )

    assert metrics.case_id == "case_002"
    assert metrics.recall_at_k == 0.5
    assert metrics.reciprocal_rank_at_k == 0.5
    assert metrics.citation_coverage == 0.5


def test_evaluate_retrieval_case_coverage_can_use_explicit_citations() -> None:
    metrics = evaluate_retrieval_case(
        case_id="case_003",
        expected_source_uris=("data/doc_a.md", "data/doc_b.md"),
        retrieved_source_uris=("data/doc_a.md", "data/doc_b.md"),
        cited_source_uris=("data/doc_a.md",),
        k=2,
    )

    assert metrics.recall_at_k == 1.0
    assert metrics.reciprocal_rank_at_k == 1.0
    assert metrics.citation_coverage == 0.5


def test_summarize_retrieval_metrics_applies_baseline_thresholds() -> None:
    summary = summarize_retrieval_metrics(
        (
            RetrievalCaseMetrics(
                case_id="case_004",
                recall_at_k=0.8,
                reciprocal_rank_at_k=0.5,
                citation_coverage=0.9,
            ),
            RetrievalCaseMetrics(
                case_id="case_005",
                recall_at_k=0.8,
                reciprocal_rank_at_k=0.6,
                citation_coverage=0.8,
            ),
        ),
        k=5,
        thresholds=BASELINE_THRESHOLDS,
    )

    assert summary.case_count == 2
    assert summary.k == 5
    assert summary.recall_at_k == 0.8
    assert summary.mrr_at_k == 0.55
    assert summary.citation_coverage == pytest.approx(0.85)
    assert summary.passes_thresholds is True


def test_summarize_retrieval_metrics_handles_empty_input() -> None:
    summary = summarize_retrieval_metrics((), k=5)

    assert summary.case_count == 0
    assert summary.recall_at_k == 0.0
    assert summary.mrr_at_k == 0.0
    assert summary.citation_coverage == 0.0
    assert summary.passes_thresholds is False


def test_evaluate_retrieval_case_rejects_non_positive_k() -> None:
    try:
        evaluate_retrieval_case(
            case_id="case_006",
            expected_source_uris=("data/doc_a.md",),
            retrieved_source_uris=("data/doc_a.md",),
            k=0,
        )
    except ValueError as exc:
        assert str(exc) == "k must be positive"
    else:
        raise AssertionError("Expected ValueError for non-positive k")
