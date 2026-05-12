from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from storage.models import Document, EvalCase, StructuredRecord


class NormalizationError(ValueError):
    """Raised when raw source data cannot be normalized."""


FUND_REQUIRED_STRING_FIELDS = {
    "record_type",
    "fund_id",
    "name",
    "category",
    "investment_style",
}

FUND_REQUIRED_NUMBER_FIELDS = {
    "expense_ratio",
    "return_1y",
    "return_3y",
    "volatility",
    "sharpe",
    "aum_millions",
}

FUND_REQUIRED_INTEGER_FIELDS = {
    "inception_year",
}

FUND_VALUE_FIELDS = (
    "fund_id",
    "name",
    "category",
    "investment_style",
    "expense_ratio",
    "return_1y",
    "return_3y",
    "volatility",
    "sharpe",
    "aum_millions",
    "inception_year",
)

ISSUE_REQUIRED_STRING_FIELDS = {
    "issue_id",
    "repo",
    "title",
    "body",
    "state",
    "source_uri",
    "created_at",
    "updated_at",
}

ISSUE_VALUE_FIELDS = (
    "issue_id",
    "repo",
    "number",
    "title",
    "labels",
    "state",
    "created_at",
    "updated_at",
)

COMMENT_REQUIRED_STRING_FIELDS = {
    "comment_id",
    "author",
    "body",
    "created_at",
}

EVAL_REQUIRED_STRING_FIELDS = {
    "case_id",
    "task_type",
    "question",
}


@dataclass(frozen=True)
class IssueNormalizationResult:
    issue_records: tuple[StructuredRecord, ...]
    documents: tuple[Document, ...]


def load_json_file(path: str | Path) -> Any:
    file_path = Path(path)
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise NormalizationError(f"Source file is not valid JSON: {file_path}") from exc


def load_text_file(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def normalize_markdown_document_file(
    path: str | Path,
    *,
    source_id: str,
    source_type: str,
    source_uri: str,
    dataset_name: str,
    fund_id: str | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> Document:
    return normalize_markdown_document(
        load_text_file(path),
        source_id=source_id,
        source_type=source_type,
        source_uri=source_uri,
        dataset_name=dataset_name,
        fund_id=fund_id,
        created_at=created_at,
        updated_at=updated_at,
    )


def normalize_markdown_document(
    raw_text: str,
    *,
    source_id: str,
    source_type: str,
    source_uri: str,
    dataset_name: str,
    fund_id: str | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> Document:
    body = raw_text.strip()
    if not body:
        raise NormalizationError(f"Document source '{source_uri}' is empty")

    title = _extract_markdown_title(body, source_uri=source_uri)
    header_metadata = _extract_markdown_header_metadata(body)
    normalized_fund_id = fund_id or header_metadata.get("fund_id")

    metadata = {
        "dataset_name": dataset_name,
        "source_id": source_id,
        "source_type": source_type,
    }
    if normalized_fund_id is not None:
        metadata["fund_id"] = normalized_fund_id
    if header_metadata.get("as_of") is not None:
        metadata["as_of"] = header_metadata["as_of"]

    timestamp = datetime.now(UTC)
    return Document(
        document_id=f"doc_{source_id}",
        source_type=source_type,
        source_uri=source_uri,
        title=title,
        body=body,
        metadata=metadata,
        created_at=created_at or timestamp,
        updated_at=updated_at or created_at or timestamp,
    )


def normalize_issue_records_file(
    path: str | Path,
    *,
    source_uri: str,
    dataset_name: str,
) -> IssueNormalizationResult:
    return normalize_issue_records(
        load_json_file(path),
        source_uri=source_uri,
        dataset_name=dataset_name,
    )


def normalize_issue_records(
    raw_issues: Any,
    *,
    source_uri: str,
    dataset_name: str,
) -> IssueNormalizationResult:
    if not isinstance(raw_issues, list):
        raise NormalizationError("Issue source must be a list of records")

    issue_records = []
    documents = []
    for index, raw_issue in enumerate(raw_issues):
        if not isinstance(raw_issue, dict):
            raise NormalizationError(f"Issue record at index {index} must be an object")
        issue_records.append(
            normalize_issue_metadata_record(
                raw_issue,
                source_uri=source_uri,
                dataset_name=dataset_name,
                index=index,
            )
        )
        documents.extend(
            normalize_issue_documents(
                raw_issue,
                dataset_name=dataset_name,
                index=index,
            )
        )

    return IssueNormalizationResult(
        issue_records=tuple(issue_records),
        documents=tuple(documents),
    )


def normalize_issue_metadata_record(
    raw_issue: dict[str, Any],
    *,
    source_uri: str,
    dataset_name: str,
    index: int,
) -> StructuredRecord:
    _validate_issue_record(raw_issue, index=index)

    return StructuredRecord(
        record_type="github_issue",
        source_uri=source_uri,
        metadata={
            "dataset_name": dataset_name,
            "source_record_index": index,
        },
        values={
            **{field_name: raw_issue[field_name] for field_name in ISSUE_VALUE_FIELDS},
            "comment_count": len(raw_issue["comments"]),
        },
    )


def normalize_issue_documents(
    raw_issue: dict[str, Any],
    *,
    dataset_name: str,
    index: int,
) -> tuple[Document, ...]:
    _validate_issue_record(raw_issue, index=index)

    issue_created_at = _parse_source_datetime(
        raw_issue["created_at"],
        field_name="created_at",
        record_name=f"Issue record at index {index}",
    )
    issue_updated_at = _parse_source_datetime(
        raw_issue["updated_at"],
        field_name="updated_at",
        record_name=f"Issue record at index {index}",
    )

    documents = [
        Document(
            document_id=f"doc_{raw_issue['issue_id']}",
            source_type="github_issue",
            source_uri=raw_issue["source_uri"],
            title=raw_issue["title"],
            body=raw_issue["body"],
            metadata={
                "dataset_name": dataset_name,
                "source_id": raw_issue["issue_id"],
                "issue_id": raw_issue["issue_id"],
                "repo": raw_issue["repo"],
                "number": raw_issue["number"],
                "labels": list(raw_issue["labels"]),
                "state": raw_issue["state"],
                "document_kind": "issue_body",
            },
            created_at=issue_created_at,
            updated_at=issue_updated_at,
        )
    ]

    for comment_index, raw_comment in enumerate(raw_issue["comments"]):
        _validate_issue_comment(
            raw_comment,
            issue_index=index,
            comment_index=comment_index,
        )
        comment_created_at = _parse_source_datetime(
            raw_comment["created_at"],
            field_name="created_at",
            record_name=f"Issue comment at issue index {index}, comment index {comment_index}",
        )
        documents.append(
            Document(
                document_id=f"doc_{raw_comment['comment_id']}",
                source_type="github_issue_comment",
                source_uri=f"{raw_issue['source_uri']}#comment-{raw_comment['comment_id']}",
                title=f"Comment on {raw_issue['title']}",
                body=raw_comment["body"],
                metadata={
                    "dataset_name": dataset_name,
                    "source_id": raw_comment["comment_id"],
                    "issue_id": raw_issue["issue_id"],
                    "comment_id": raw_comment["comment_id"],
                    "repo": raw_issue["repo"],
                    "number": raw_issue["number"],
                    "author": raw_comment["author"],
                    "document_kind": "issue_comment",
                    "parent_source_uri": raw_issue["source_uri"],
                },
                created_at=comment_created_at,
                updated_at=comment_created_at,
            )
        )

    return tuple(documents)


def normalize_eval_cases_file(
    path: str | Path,
    *,
    source_uri: str,
    dataset_name: str,
) -> tuple[EvalCase, ...]:
    return normalize_eval_cases(
        load_json_file(path),
        source_uri=source_uri,
        dataset_name=dataset_name,
    )


def normalize_eval_cases(
    raw_cases: Any,
    *,
    source_uri: str,
    dataset_name: str,
) -> tuple[EvalCase, ...]:
    if not isinstance(raw_cases, list):
        raise NormalizationError("Eval case source must be a list of records")

    eval_cases = []
    for index, raw_case in enumerate(raw_cases):
        if not isinstance(raw_case, dict):
            raise NormalizationError(f"Eval case at index {index} must be an object")
        eval_cases.append(
            normalize_eval_case(
                raw_case,
                source_uri=source_uri,
                dataset_name=dataset_name,
                index=index,
            )
        )
    return tuple(eval_cases)


def normalize_eval_case(
    raw_case: dict[str, Any],
    *,
    source_uri: str,
    dataset_name: str,
    index: int,
) -> EvalCase:
    _validate_eval_case(raw_case, index=index)

    return EvalCase(
        case_id=raw_case["case_id"],
        task_type=raw_case["task_type"],
        question=raw_case["question"],
        entities=list(raw_case["entities"]),
        expected_answer=raw_case.get("expected_answer"),
        expected_citations=list(raw_case["expected_citations"]),
        evaluation_tags=list(raw_case["evaluation_tags"]),
        safety_expectations=dict(raw_case["safety_expectations"]),
        metadata=_build_eval_case_metadata(
            raw_case,
            source_uri=source_uri,
            dataset_name=dataset_name,
            index=index,
        ),
    )


def normalize_fund_records(
    raw_records: Any,
    *,
    source_uri: str,
    dataset_name: str,
) -> tuple[StructuredRecord, ...]:
    if not isinstance(raw_records, list):
        raise NormalizationError("Fund source must be a list of records")

    normalized_records = []
    for index, raw_record in enumerate(raw_records):
        if not isinstance(raw_record, dict):
            raise NormalizationError(f"Fund record at index {index} must be an object")
        normalized_records.append(
            normalize_fund_record(
                raw_record,
                source_uri=source_uri,
                dataset_name=dataset_name,
                index=index,
            )
        )
    return tuple(normalized_records)


def normalize_fund_records_file(
    path: str | Path,
    *,
    source_uri: str,
    dataset_name: str,
) -> tuple[StructuredRecord, ...]:
    return normalize_fund_records(
        load_json_file(path),
        source_uri=source_uri,
        dataset_name=dataset_name,
    )


def normalize_fund_record(
    raw_record: dict[str, Any],
    *,
    source_uri: str,
    dataset_name: str,
    index: int,
) -> StructuredRecord:
    _validate_fund_record(raw_record, index=index)

    return StructuredRecord(
        record_type="fund",
        source_uri=source_uri,
        metadata={
            "dataset_name": dataset_name,
            "source_record_index": index,
        },
        values={field_name: raw_record[field_name] for field_name in FUND_VALUE_FIELDS},
    )


def _extract_markdown_title(body: str, *, source_uri: str) -> str:
    for line in body.splitlines():
        stripped_line = line.strip()
        if stripped_line.startswith("# "):
            title = stripped_line.removeprefix("# ").strip()
            if title:
                return title
    raise NormalizationError(f"Document source '{source_uri}' is missing an H1 title")


def _extract_markdown_header_metadata(body: str) -> dict[str, str]:
    metadata = {}
    for line in body.splitlines():
        stripped_line = line.strip()
        if not stripped_line:
            continue
        if stripped_line.startswith("## "):
            break
        if ":" not in stripped_line:
            continue

        key, value = stripped_line.split(":", 1)
        normalized_key = key.strip().lower().replace(" ", "_")
        normalized_value = value.strip()
        if normalized_key == "fund_id" and normalized_value:
            metadata["fund_id"] = normalized_value
        elif normalized_key == "as_of" and normalized_value:
            metadata["as_of"] = normalized_value
    return metadata


def _validate_fund_record(raw_record: dict[str, Any], *, index: int) -> None:
    for field_name in FUND_REQUIRED_STRING_FIELDS:
        value = raw_record.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise NormalizationError(
                f"Fund record at index {index} field '{field_name}' must be a non-empty string"
            )

    if raw_record["record_type"] != "fund":
        raise NormalizationError(
            f"Fund record at index {index} field 'record_type' must be 'fund'"
        )

    for field_name in FUND_REQUIRED_NUMBER_FIELDS:
        value = raw_record.get(field_name)
        if not isinstance(value, int | float):
            raise NormalizationError(
                f"Fund record at index {index} field '{field_name}' must be a number"
            )

    for field_name in FUND_REQUIRED_INTEGER_FIELDS:
        value = raw_record.get(field_name)
        if not isinstance(value, int):
            raise NormalizationError(
                f"Fund record at index {index} field '{field_name}' must be an integer"
            )


def _validate_issue_record(raw_issue: dict[str, Any], *, index: int) -> None:
    for field_name in ISSUE_REQUIRED_STRING_FIELDS:
        value = raw_issue.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise NormalizationError(
                f"Issue record at index {index} field '{field_name}' must be a non-empty string"
            )

    if not isinstance(raw_issue.get("number"), int):
        raise NormalizationError(
            f"Issue record at index {index} field 'number' must be an integer"
        )
    if not isinstance(raw_issue.get("labels"), list) or not all(
        isinstance(label, str) and label.strip() for label in raw_issue.get("labels", [])
    ):
        raise NormalizationError(
            f"Issue record at index {index} field 'labels' must be a list of strings"
        )
    if not isinstance(raw_issue.get("comments"), list):
        raise NormalizationError(
            f"Issue record at index {index} field 'comments' must be a list"
        )


def _validate_issue_comment(
    raw_comment: dict[str, Any],
    *,
    issue_index: int,
    comment_index: int,
) -> None:
    if not isinstance(raw_comment, dict):
        raise NormalizationError(
            f"Issue comment at issue index {issue_index}, comment index {comment_index} must be an object"
        )
    for field_name in COMMENT_REQUIRED_STRING_FIELDS:
        value = raw_comment.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise NormalizationError(
                "Issue comment at issue index "
                f"{issue_index}, comment index {comment_index} field '{field_name}' "
                "must be a non-empty string"
            )


def _validate_eval_case(raw_case: dict[str, Any], *, index: int) -> None:
    for field_name in EVAL_REQUIRED_STRING_FIELDS:
        value = raw_case.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise NormalizationError(
                f"Eval case at index {index} field '{field_name}' must be a non-empty string"
            )
    if not isinstance(raw_case.get("entities"), list):
        raise NormalizationError(
            f"Eval case at index {index} field 'entities' must be a list"
        )
    if not isinstance(raw_case.get("expected_citations"), list):
        raise NormalizationError(
            f"Eval case at index {index} field 'expected_citations' must be a list"
        )
    if not isinstance(raw_case.get("evaluation_tags"), list) or not all(
        isinstance(tag, str) and tag.strip()
        for tag in raw_case.get("evaluation_tags", [])
    ):
        raise NormalizationError(
            f"Eval case at index {index} field 'evaluation_tags' must be a list of strings"
        )
    if not isinstance(raw_case.get("safety_expectations"), dict):
        raise NormalizationError(
            f"Eval case at index {index} field 'safety_expectations' must be a mapping"
        )
    source_metadata = raw_case.get("source_metadata")
    if source_metadata is not None and not isinstance(source_metadata, dict):
        raise NormalizationError(
            f"Eval case at index {index} field 'source_metadata' must be a mapping"
        )
    expected_answer = raw_case.get("expected_answer")
    if expected_answer is not None and (
        not isinstance(expected_answer, str) or not expected_answer.strip()
    ):
        raise NormalizationError(
            f"Eval case at index {index} field 'expected_answer' must be null or a non-empty string"
        )


def _build_eval_case_metadata(
    raw_case: dict[str, Any],
    *,
    source_uri: str,
    dataset_name: str,
    index: int,
) -> dict[str, Any]:
    metadata = {
        "dataset_name": dataset_name,
        "source_uri": source_uri,
        "source_record_index": index,
    }
    if raw_case.get("source_metadata") is not None:
        metadata["source_metadata"] = dict(raw_case["source_metadata"])
    return metadata


def _parse_source_datetime(
    value: str,
    *,
    field_name: str,
    record_name: str,
) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise NormalizationError(
            f"{record_name} field '{field_name}' must be an ISO datetime"
        ) from exc
