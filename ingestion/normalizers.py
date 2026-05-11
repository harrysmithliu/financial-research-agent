from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from storage.models import Document, StructuredRecord


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
