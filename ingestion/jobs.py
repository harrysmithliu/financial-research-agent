from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ingestion.loaders import (
    Manifest,
    ResolvedManifestSource,
    load_and_resolve_manifest,
)
from ingestion.normalizers import (
    normalize_eval_cases_file,
    normalize_fund_records_file,
    normalize_issue_records_file,
    normalize_markdown_document_file,
)
from storage.models import Document, EvalCase, StructuredRecord


class IngestionJobError(ValueError):
    """Raised when a resolved source cannot be handled by the local ingestion job."""


@dataclass(frozen=True)
class IngestionResult:
    manifest: Manifest
    resolved_sources: tuple[ResolvedManifestSource, ...]
    fund_records: tuple[StructuredRecord, ...]
    documents: tuple[Document, ...]
    issue_records: tuple[StructuredRecord, ...]
    eval_cases: tuple[EvalCase, ...]

    @property
    def structured_records(self) -> tuple[StructuredRecord, ...]:
        return self.fund_records + self.issue_records


def load_seed_dataset(repo_root: str | Path) -> IngestionResult:
    manifest, resolved_sources = load_and_resolve_manifest(repo_root)

    fund_records: list[StructuredRecord] = []
    documents: list[Document] = []
    issue_records: list[StructuredRecord] = []
    eval_cases: list[EvalCase] = []

    for resolved_source in resolved_sources:
        source = resolved_source.source

        if source.content_type == "structured_records" and source.record_type == "fund":
            fund_records.extend(
                normalize_fund_records_file(
                    resolved_source.path,
                    source_uri=source.source_uri,
                    dataset_name=manifest.dataset_name,
                )
            )
        elif source.content_type == "document":
            documents.append(
                normalize_markdown_document_file(
                    resolved_source.path,
                    source_id=source.source_id,
                    source_type=source.source_type,
                    source_uri=source.source_uri,
                    dataset_name=manifest.dataset_name,
                    fund_id=source.fund_id,
                )
            )
        elif (
            source.content_type == "structured_records"
            and source.record_type == "github_issue"
        ):
            issue_result = normalize_issue_records_file(
                resolved_source.path,
                source_uri=source.source_uri,
                dataset_name=manifest.dataset_name,
            )
            issue_records.extend(issue_result.issue_records)
            documents.extend(issue_result.documents)
        elif source.content_type == "eval_cases":
            eval_cases.extend(
                normalize_eval_cases_file(
                    resolved_source.path,
                    source_uri=source.source_uri,
                    dataset_name=manifest.dataset_name,
                )
            )
        else:
            raise IngestionJobError(
                "Unsupported manifest source combination: "
                f"source_id={source.source_id}, "
                f"source_type={source.source_type}, "
                f"content_type={source.content_type}, "
                f"record_type={source.record_type}"
            )

    return IngestionResult(
        manifest=manifest,
        resolved_sources=resolved_sources,
        fund_records=tuple(fund_records),
        documents=tuple(documents),
        issue_records=tuple(issue_records),
        eval_cases=tuple(eval_cases),
    )

