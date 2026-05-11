from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ingestion.sources.local_files import resolve_existing_source_path


SUPPORTED_SOURCE_TYPES = {
    "fund_fact_sheet",
    "github_issues",
    "local_directory",
    "local_file",
    "sample_dataset",
}

SUPPORTED_CONTENT_TYPES = {
    "document",
    "eval_cases",
    "structured_records",
}


class ManifestError(ValueError):
    """Raised when the ingestion manifest is malformed."""


@dataclass(frozen=True)
class ManifestSource:
    source_id: str
    source_type: str
    source_uri: str
    content_type: str
    record_type: str | None = None
    fund_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, raw_source: dict[str, Any]) -> "ManifestSource":
        required_fields = ("source_id", "source_type", "source_uri", "content_type")
        missing_fields = [
            field_name
            for field_name in required_fields
            if not raw_source.get(field_name)
        ]
        if missing_fields:
            raise ManifestError(
                f"Manifest source is missing required field(s): {', '.join(missing_fields)}"
            )

        source_type = str(raw_source["source_type"])
        if source_type not in SUPPORTED_SOURCE_TYPES:
            raise ManifestError(f"Unsupported source_type: {source_type}")

        content_type = str(raw_source["content_type"])
        if content_type not in SUPPORTED_CONTENT_TYPES:
            raise ManifestError(f"Unsupported content_type: {content_type}")

        known_fields = {
            "source_id",
            "source_type",
            "source_uri",
            "content_type",
            "record_type",
            "fund_id",
        }
        metadata = {
            key: value for key, value in raw_source.items() if key not in known_fields
        }

        return cls(
            source_id=str(raw_source["source_id"]),
            source_type=source_type,
            source_uri=str(raw_source["source_uri"]),
            content_type=content_type,
            record_type=(
                str(raw_source["record_type"])
                if raw_source.get("record_type") is not None
                else None
            ),
            fund_id=(
                str(raw_source["fund_id"]) if raw_source.get("fund_id") is not None else None
            ),
            metadata=metadata,
        )


@dataclass(frozen=True)
class Manifest:
    dataset_name: str
    version: str
    description: str | None
    created_at: str | None
    sources: tuple[ManifestSource, ...]

    @classmethod
    def from_mapping(cls, raw_manifest: dict[str, Any]) -> "Manifest":
        if not raw_manifest.get("dataset_name"):
            raise ManifestError("Manifest is missing required field: dataset_name")
        if not raw_manifest.get("version"):
            raise ManifestError("Manifest is missing required field: version")

        raw_sources = raw_manifest.get("sources")
        if not isinstance(raw_sources, list) or not raw_sources:
            raise ManifestError("Manifest field 'sources' must be a non-empty list")

        sources = []
        for index, raw_source in enumerate(raw_sources):
            if not isinstance(raw_source, dict):
                raise ManifestError(f"Manifest source at index {index} must be an object")
            try:
                sources.append(ManifestSource.from_mapping(raw_source))
            except ManifestError as exc:
                raise ManifestError(f"Invalid manifest source at index {index}: {exc}") from exc

        return cls(
            dataset_name=str(raw_manifest["dataset_name"]),
            version=str(raw_manifest["version"]),
            description=(
                str(raw_manifest["description"])
                if raw_manifest.get("description") is not None
                else None
            ),
            created_at=(
                str(raw_manifest["created_at"])
                if raw_manifest.get("created_at") is not None
                else None
            ),
            sources=tuple(sources),
        )


@dataclass(frozen=True)
class ResolvedManifestSource:
    source: ManifestSource
    path: Path


def load_manifest(manifest_path: str | Path) -> Manifest:
    manifest_file = Path(manifest_path)
    try:
        raw_manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestError(f"Manifest is not valid JSON: {manifest_file}") from exc

    if not isinstance(raw_manifest, dict):
        raise ManifestError("Manifest root must be an object")

    return Manifest.from_mapping(raw_manifest)


def load_manifest_from_repo(repo_root: str | Path) -> Manifest:
    return load_manifest(Path(repo_root) / "data" / "manifest.json")


def resolve_manifest_sources(
    manifest: Manifest, repo_root: str | Path
) -> tuple[ResolvedManifestSource, ...]:
    return tuple(
        ResolvedManifestSource(
            source=source,
            path=resolve_existing_source_path(repo_root, source.source_uri),
        )
        for source in manifest.sources
    )


def load_and_resolve_manifest(repo_root: str | Path) -> tuple[Manifest, tuple[ResolvedManifestSource, ...]]:
    manifest = load_manifest_from_repo(repo_root)
    return manifest, resolve_manifest_sources(manifest, repo_root)

