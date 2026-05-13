from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
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
from storage.models import Document, EvalCase, IngestionJobRecord, StructuredRecord
from storage.repository import StorageRepository


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


@dataclass(frozen=True)
class IngestionRunResult:
    ingestion_result: IngestionResult
    job_record: IngestionJobRecord


def run_seed_ingestion(
    repo_root: str | Path,
    repository: StorageRepository,
    *,
    started_at: datetime | None = None,
) -> IngestionRunResult:
    job_started_at = started_at or datetime.now(UTC)
    try:
        ingestion_result = load_seed_dataset(repo_root)
        repository.save_structured_records(ingestion_result.structured_records)
        repository.save_documents(ingestion_result.documents)
        repository.save_eval_cases(ingestion_result.eval_cases)
        job_record = _build_ingestion_job_record(
            ingestion_result,
            status="completed",
            started_at=job_started_at,
            finished_at=datetime.now(UTC),
        )
        repository.save_ingestion_job_record(job_record)
        return IngestionRunResult(
            ingestion_result=ingestion_result,
            job_record=job_record,
        )
    except Exception as exc:
        job_record = IngestionJobRecord(
            job_id="ingest_seed_dataset_failed",
            dataset_name="unknown",
            source_ids=("unknown",),
            status="failed",
            document_count=0,
            structured_record_count=0,
            eval_case_count=0,
            started_at=job_started_at,
            finished_at=datetime.now(UTC),
            error_message=str(exc),
        )
        repository.save_ingestion_job_record(job_record)
        raise


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


def _build_ingestion_job_record(
    ingestion_result: IngestionResult,
    *,
    status: str,
    started_at: datetime,
    finished_at: datetime | None,
) -> IngestionJobRecord:
    return IngestionJobRecord(
        job_id=(
            f"ingest_{ingestion_result.manifest.dataset_name}_"
            f"{ingestion_result.manifest.version}"
        ),
        dataset_name=ingestion_result.manifest.dataset_name,
        source_ids=tuple(
            source.source.source_id for source in ingestion_result.resolved_sources
        ),
        status=status,
        document_count=len(ingestion_result.documents),
        structured_record_count=len(ingestion_result.structured_records),
        eval_case_count=len(ingestion_result.eval_cases),
        started_at=started_at,
        finished_at=finished_at,
    )
