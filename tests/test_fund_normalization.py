from __future__ import annotations

from pathlib import Path

import pytest

from ingestion.normalizers import (
    NormalizationError,
    normalize_fund_records,
    normalize_fund_records_file,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
FUNDS_SOURCE_URI = "data/sample_funds/funds.json"
FUNDS_PATH = REPO_ROOT / FUNDS_SOURCE_URI


def test_normalize_sample_funds_file_returns_four_fund_records() -> None:
    records = normalize_fund_records_file(
        FUNDS_PATH,
        source_uri=FUNDS_SOURCE_URI,
        dataset_name="synthetic_fund_seed",
    )

    assert len(records) == 4
    assert {record.record_type for record in records} == {"fund"}
    assert {record.values["fund_id"] for record in records} == {
        "FUND_A",
        "FUND_B",
        "FUND_C",
        "FUND_D",
    }
    assert all(record.source_uri == FUNDS_SOURCE_URI for record in records)
    assert all(
        record.metadata["dataset_name"] == "synthetic_fund_seed"
        for record in records
    )


def test_normalized_fund_record_preserves_canonical_fields() -> None:
    records = normalize_fund_records_file(
        FUNDS_PATH,
        source_uri=FUNDS_SOURCE_URI,
        dataset_name="synthetic_fund_seed",
    )

    first_record = records[0].to_mapping()

    assert first_record == {
        "record_type": "fund",
        "fund_id": "FUND_A",
        "name": "Northstar Growth Fund",
        "category": "US Equity",
        "investment_style": "growth",
        "expense_ratio": 0.65,
        "return_1y": 12.4,
        "return_3y": 8.9,
        "volatility": 15.2,
        "sharpe": 0.71,
        "aum_millions": 1840,
        "inception_year": 2016,
        "source_uri": FUNDS_SOURCE_URI,
        "metadata": {
            "dataset_name": "synthetic_fund_seed",
            "source_record_index": 0,
        },
    }


def test_fund_normalization_rejects_non_list_source() -> None:
    with pytest.raises(NormalizationError, match="must be a list"):
        normalize_fund_records(
            {"record_type": "fund"},
            source_uri=FUNDS_SOURCE_URI,
            dataset_name="synthetic_fund_seed",
        )


def test_fund_normalization_rejects_missing_required_field() -> None:
    raw_records = [
        {
            "record_type": "fund",
            "fund_id": "FUND_X",
            "name": "Example Fund",
            "category": "US Equity",
            "investment_style": "growth",
            "expense_ratio": 0.5,
            "return_1y": 1.0,
            "return_3y": 2.0,
            "volatility": 3.0,
            "sharpe": 0.4,
            "aum_millions": 100,
        }
    ]

    with pytest.raises(NormalizationError, match="inception_year"):
        normalize_fund_records(
            raw_records,
            source_uri=FUNDS_SOURCE_URI,
            dataset_name="synthetic_fund_seed",
        )


def test_fund_normalization_rejects_wrong_record_type() -> None:
    raw_records = [
        {
            "record_type": "company",
            "fund_id": "FUND_X",
            "name": "Example Fund",
            "category": "US Equity",
            "investment_style": "growth",
            "expense_ratio": 0.5,
            "return_1y": 1.0,
            "return_3y": 2.0,
            "volatility": 3.0,
            "sharpe": 0.4,
            "aum_millions": 100,
            "inception_year": 2024,
        }
    ]

    with pytest.raises(NormalizationError, match="record_type"):
        normalize_fund_records(
            raw_records,
            source_uri=FUNDS_SOURCE_URI,
            dataset_name="synthetic_fund_seed",
        )

