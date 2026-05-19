from __future__ import annotations

from dataclasses import dataclass

from storage.models import EvalCase


@dataclass(frozen=True)
class RetrievalThresholds:
    recall_at_5_min: float
    mrr_at_5_min: float
    citation_coverage_min: float


@dataclass(frozen=True)
class RetrievalCaseMetrics:
    case_id: str
    recall_at_k: float
    reciprocal_rank_at_k: float
    citation_coverage: float


@dataclass(frozen=True)
class RetrievalEvaluationSummary:
    case_count: int
    k: int
    recall_at_k: float
    mrr_at_k: float
    citation_coverage: float
    passes_thresholds: bool


BASELINE_THRESHOLDS = RetrievalThresholds(
    recall_at_5_min=0.70,
    mrr_at_5_min=0.45,
    citation_coverage_min=0.80,
)

NEXT_STAGE_THRESHOLDS = RetrievalThresholds(
    recall_at_5_min=0.80,
    mrr_at_5_min=0.55,
    citation_coverage_min=0.90,
)


def evaluate_retrieval_case(
    *,
    case_id: str,
    expected_source_uris: tuple[str, ...],
    retrieved_source_uris: tuple[str, ...],
    k: int,
    cited_source_uris: tuple[str, ...] = (),
) -> RetrievalCaseMetrics:
    if k <= 0:
        raise ValueError("k must be positive")

    expected = _normalize_source_uris(expected_source_uris)
    retrieved_at_k = tuple(retrieved_source_uris[:k])

    recall = _recall_at_k(expected, retrieved_at_k)
    reciprocal_rank = _reciprocal_rank_at_k(expected, retrieved_at_k)
    citation_coverage = _citation_coverage(
        expected,
        retrieved_at_k,
        cited_source_uris,
    )

    return RetrievalCaseMetrics(
        case_id=case_id,
        recall_at_k=recall,
        reciprocal_rank_at_k=reciprocal_rank,
        citation_coverage=citation_coverage,
    )


def summarize_retrieval_metrics(
    case_metrics: tuple[RetrievalCaseMetrics, ...],
    *,
    k: int,
    thresholds: RetrievalThresholds = BASELINE_THRESHOLDS,
) -> RetrievalEvaluationSummary:
    if k <= 0:
        raise ValueError("k must be positive")

    if not case_metrics:
        return RetrievalEvaluationSummary(
            case_count=0,
            k=k,
            recall_at_k=0.0,
            mrr_at_k=0.0,
            citation_coverage=0.0,
            passes_thresholds=False,
        )

    count = len(case_metrics)
    recall = sum(metric.recall_at_k for metric in case_metrics) / count
    mrr = sum(metric.reciprocal_rank_at_k for metric in case_metrics) / count
    coverage = sum(metric.citation_coverage for metric in case_metrics) / count

    passes = (
        recall >= thresholds.recall_at_5_min
        and mrr >= thresholds.mrr_at_5_min
        and coverage >= thresholds.citation_coverage_min
    )

    return RetrievalEvaluationSummary(
        case_count=count,
        k=k,
        recall_at_k=recall,
        mrr_at_k=mrr,
        citation_coverage=coverage,
        passes_thresholds=passes,
    )


def expected_source_uris_for_eval_case(eval_case: EvalCase) -> tuple[str, ...]:
    ordered_source_uris: list[str] = []
    seen: set[str] = set()

    for citation in eval_case.expected_citations:
        source_uri = citation.get("source_uri")
        if not isinstance(source_uri, str) or not source_uri.strip():
            continue
        normalized = source_uri.strip()
        if normalized in seen:
            continue
        seen.add(normalized)
        ordered_source_uris.append(normalized)

    return tuple(ordered_source_uris)


def _normalize_source_uris(source_uris: tuple[str, ...]) -> tuple[str, ...]:
    normalized: list[str] = []
    seen: set[str] = set()
    for source_uri in source_uris:
        if not isinstance(source_uri, str):
            continue
        candidate = source_uri.strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        normalized.append(candidate)
    return tuple(normalized)


def _recall_at_k(expected: tuple[str, ...], retrieved_at_k: tuple[str, ...]) -> float:
    if not expected:
        return 1.0
    hits = set(expected).intersection(retrieved_at_k)
    return len(hits) / len(expected)


def _reciprocal_rank_at_k(expected: tuple[str, ...], retrieved_at_k: tuple[str, ...]) -> float:
    expected_set = set(expected)
    if not expected_set:
        return 1.0

    for rank, source_uri in enumerate(retrieved_at_k, start=1):
        if source_uri in expected_set:
            return 1.0 / rank
    return 0.0


def _citation_coverage(
    expected: tuple[str, ...],
    retrieved_at_k: tuple[str, ...],
    cited_source_uris: tuple[str, ...],
) -> float:
    if not expected:
        return 1.0

    cited = _normalize_source_uris(cited_source_uris)
    citation_pool = set(cited) if cited else set(retrieved_at_k)

    covered = set(expected).intersection(retrieved_at_k).intersection(citation_pool)
    return len(covered) / len(expected)
