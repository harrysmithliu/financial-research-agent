from __future__ import annotations

from dataclasses import dataclass

from storage.models import EvalCase


SUPPORTED_EVAL_TASK_TYPES = {
    "due_diligence_brief",
    "financial_qa",
    "fund_comparison",
    "platform_issue_research",
}


@dataclass(frozen=True)
class DataQualityIssue:
    code: str
    message: str
    case_id: str | None = None


@dataclass(frozen=True)
class DataQualityResult:
    issues: tuple[DataQualityIssue, ...]

    @property
    def passed(self) -> bool:
        return not self.issues


def check_eval_cases_quality(eval_cases: tuple[EvalCase, ...]) -> DataQualityResult:
    issues: list[DataQualityIssue] = []
    seen_case_ids: set[str] = set()

    for eval_case in eval_cases:
        if eval_case.case_id in seen_case_ids:
            issues.append(
                DataQualityIssue(
                    code="duplicate_case_id",
                    message=f"Duplicate eval case id: {eval_case.case_id}",
                    case_id=eval_case.case_id,
                )
            )
        seen_case_ids.add(eval_case.case_id)

        if eval_case.task_type not in SUPPORTED_EVAL_TASK_TYPES:
            issues.append(
                DataQualityIssue(
                    code="unsupported_task_type",
                    message=(
                        f"Unsupported task_type '{eval_case.task_type}' "
                        f"for eval case {eval_case.case_id}"
                    ),
                    case_id=eval_case.case_id,
                )
            )

        if not eval_case.expected_citations:
            issues.append(
                DataQualityIssue(
                    code="missing_expected_citations",
                    message=f"Eval case {eval_case.case_id} has no expected citations",
                    case_id=eval_case.case_id,
                )
            )

        for citation_index, citation in enumerate(eval_case.expected_citations):
            source_uri = citation.get("source_uri")
            if not isinstance(source_uri, str) or not source_uri.strip():
                issues.append(
                    DataQualityIssue(
                        code="missing_citation_source_uri",
                        message=(
                            f"Eval case {eval_case.case_id} citation "
                            f"at index {citation_index} is missing source_uri"
                        ),
                        case_id=eval_case.case_id,
                    )
                )

    return DataQualityResult(issues=tuple(issues))

