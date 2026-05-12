from __future__ import annotations

import json
from pathlib import Path

import pytest

from ingestion.loaders import (
    ManifestError,
    load_and_resolve_manifest,
    load_manifest,
    resolve_manifest_sources,
)
from ingestion.sources.local_files import SourcePathError


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_load_manifest_and_resolve_declared_sources() -> None:
    manifest, resolved_sources = load_and_resolve_manifest(REPO_ROOT)

    assert manifest.dataset_name == "synthetic_fund_seed"
    assert len(manifest.sources) == 8
    assert len(resolved_sources) == 8
    assert {resolved.source.source_id for resolved in resolved_sources} == {
        "synthetic_fund_records",
        "fund_a_factsheet",
        "fund_b_factsheet",
        "fund_c_factsheet",
        "fund_d_factsheet",
        "synthetic_platform_issues",
        "fund_eval_cases",
        "finagent_benchmark_sample",
    }
    assert all(resolved.path.exists() for resolved in resolved_sources)


def test_missing_manifest_source_path_raises_clear_error(tmp_path: Path) -> None:
    missing_file = tmp_path / "missing.json"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "dataset_name": "bad_dataset",
                "version": "0.1.0",
                "sources": [
                    {
                        "source_id": "missing_source",
                        "source_type": "sample_dataset",
                        "source_uri": str(missing_file),
                        "content_type": "structured_records",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest = load_manifest(manifest_path)

    with pytest.raises(SourcePathError, match="Manifest source does not exist"):
        resolve_manifest_sources(manifest, tmp_path)


def test_unsupported_manifest_source_type_raises_clear_error(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "dataset_name": "bad_dataset",
                "version": "0.1.0",
                "sources": [
                    {
                        "source_id": "bad_source",
                        "source_type": "unsupported_source",
                        "source_uri": "data/source.json",
                        "content_type": "structured_records",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ManifestError, match="Unsupported source_type"):
        load_manifest(manifest_path)
