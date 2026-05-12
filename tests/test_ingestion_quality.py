from __future__ import annotations

from pathlib import Path

from ingestion.normalizers import normalize_eval_cases_file
from ingestion.quality import check_eval_cases_quality
from storage.models import EvalCase


REPO_ROOT = Path(__file__).resolve().parents[1]
FINAGENT_SOURCE_URI = "data/external/finagent_benchmark_sample.json"
FINAGENT_PATH = REPO_ROOT / FINAGENT_SOURCE_URI


def test_finagent_eval_cases_pass_quality_checks() -> None:
    cases = normalize_eval_cases_file(
        FINAGENT_PATH,
        source_uri=FINAGENT_SOURCE_URI,
        dataset_name="synthetic_fund_seed",
    )

    result = check_eval_cases_quality(cases)

    assert result.passed
    assert result.issues == ()


def test_quality_check_detects_duplicate_case_id() -> None:
    eval_case = _eval_case(case_id="duplicate_case")

    result = check_eval_cases_quality((eval_case, eval_case))

    assert not result.passed
    assert [issue.code for issue in result.issues] == ["duplicate_case_id"]
    assert result.issues[0].case_id == "duplicate_case"


def test_quality_check_detects_missing_expected_citations() -> None:
    eval_case = _eval_case(case_id="missing_citations", expected_citations=[])

    result = check_eval_cases_quality((eval_case,))

    assert not result.passed
    assert [issue.code for issue in result.issues] == ["missing_expected_citations"]


def test_quality_check_detects_missing_citation_source_uri() -> None:
    eval_case = _eval_case(
        case_id="missing_source_uri",
        expected_citations=[{"evidence_text": "Evidence without source URI"}],
    )

    result = check_eval_cases_quality((eval_case,))

    assert not result.passed
    assert [issue.code for issue in result.issues] == ["missing_citation_source_uri"]


def test_quality_check_detects_unsupported_task_type() -> None:
    eval_case = _eval_case(case_id="bad_task", task_type="unsupported_task")

    result = check_eval_cases_quality((eval_case,))

    assert not result.passed
    assert [issue.code for issue in result.issues] == ["unsupported_task_type"]


def _eval_case(
    *,
    case_id: str,
    task_type: str = "financial_qa",
    expected_citations: list[dict[str, str]] | None = None,
) -> EvalCase:
    return EvalCase(
        case_id=case_id,
        task_type=task_type,
        question="Which value is requested?",
        entities=[],
        expected_answer="Example answer",
        expected_citations=(
            expected_citations
            if expected_citations is not None
            else [{"source_uri": "memory://source", "evidence_text": "Evidence"}]
        ),
        evaluation_tags=["citation_required"],
        safety_expectations={"should_refuse": False},
    )

