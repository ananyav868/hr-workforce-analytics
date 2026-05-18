"""Unit tests for null handling and deduplication in DataIngestor."""

import logging

import numpy as np
import pandas as pd
import pytest

from src.etl.ingestion import DataIngestor
from src.pipeline.models import IngestionConfig


@pytest.fixture
def drop_config():
    """Config with null_strategy='drop'."""
    return IngestionConfig(
        required_columns=["employee_id", "name", "department", "hire_date"],
        null_strategy="drop",
        dedup_key="employee_id",
        dedup_sort="hire_date",
    )


@pytest.fixture
def fill_config():
    """Config with null_strategy='fill_default'."""
    return IngestionConfig(
        required_columns=["employee_id", "name", "department", "hire_date"],
        null_strategy="fill_default",
        dedup_key="employee_id",
        dedup_sort="hire_date",
    )


@pytest.fixture
def csv_with_nulls(tmp_path):
    """CSV with null values in required fields."""
    csv_path = tmp_path / "nulls.csv"
    csv_path.write_text(
        "employee_id,name,department,hire_date,salary\n"
        "1,Alice,Engineering,2020-01-15,80000\n"
        "2,,Marketing,2021-03-20,65000\n"
        "3,Charlie,,2022-05-10,70000\n"
        "4,Diana,Sales,2023-01-01,60000\n"
    )
    return str(csv_path)


@pytest.fixture
def csv_with_duplicates(tmp_path):
    """CSV with duplicate employee_id records."""
    csv_path = tmp_path / "dupes.csv"
    csv_path.write_text(
        "employee_id,name,department,hire_date,salary\n"
        "1,Alice,Engineering,2020-01-15,80000\n"
        "1,Alice,Engineering,2022-06-01,90000\n"
        "2,Bob,Marketing,2021-03-20,65000\n"
        "2,Bob,Marketing,2023-01-10,72000\n"
        "3,Charlie,Sales,2021-08-01,55000\n"
    )
    return str(csv_path)


class TestNullHandling:
    """Tests for null value handling in DataIngestor."""

    def test_drop_strategy_removes_rows_with_nulls(self, drop_config, csv_with_nulls):
        """Rows with nulls in required fields are dropped when strategy is 'drop'."""
        ingestor = DataIngestor(drop_config)
        df = ingestor.ingest(csv_with_nulls)
        assert len(df) == 2
        assert set(df["employee_id"].tolist()) == {1, 4}

    def test_fill_default_strategy_fills_string_with_empty(self, fill_config, csv_with_nulls):
        """String columns with nulls are filled with empty string when strategy is 'fill_default'."""
        ingestor = DataIngestor(fill_config)
        df = ingestor.ingest(csv_with_nulls)
        assert len(df) == 4
        row2 = df[df["employee_id"] == 2]
        assert row2["name"].iloc[0] == ""

    def test_fill_default_strategy_fills_object_col_with_empty(self, fill_config, csv_with_nulls):
        """Object columns with nulls are filled with empty string."""
        ingestor = DataIngestor(fill_config)
        df = ingestor.ingest(csv_with_nulls)
        row3 = df[df["employee_id"] == 3]
        assert row3["department"].iloc[0] == ""

    def test_null_handling_logs_row_indices(self, drop_config, csv_with_nulls, caplog):
        """Row indices with nulls are logged as a warning."""
        ingestor = DataIngestor(drop_config)
        with caplog.at_level(logging.WARNING, logger="src.etl.ingestion"):
            ingestor.ingest(csv_with_nulls)
        assert "row indices" in caplog.text.lower() or "Row indices" in caplog.text

    def test_no_nulls_returns_all_rows(self, drop_config, tmp_path):
        """When no nulls exist, all rows are returned unchanged."""
        csv_path = tmp_path / "clean.csv"
        csv_path.write_text(
            "employee_id,name,department,hire_date\n"
            "1,Alice,Engineering,2020-01-15\n"
            "2,Bob,Marketing,2021-03-20\n"
        )
        ingestor = DataIngestor(drop_config)
        df = ingestor.ingest(str(csv_path))
        assert len(df) == 2


class TestDeduplication:
    """Tests for deduplication logic in DataIngestor."""

    def test_dedup_keeps_most_recent_by_hire_date(self, drop_config, csv_with_duplicates):
        """Deduplication retains the most recent record per employee_id."""
        ingestor = DataIngestor(drop_config)
        df = ingestor.ingest(csv_with_duplicates)
        assert len(df) == 3
        alice = df[df["employee_id"] == 1]
        assert alice["hire_date"].iloc[0] == "2022-06-01"
        assert alice["salary"].iloc[0] == 90000

    def test_dedup_keeps_most_recent_for_all_duplicates(self, drop_config, csv_with_duplicates):
        """All duplicate groups keep only the most recent record."""
        ingestor = DataIngestor(drop_config)
        df = ingestor.ingest(csv_with_duplicates)
        bob = df[df["employee_id"] == 2]
        assert bob["hire_date"].iloc[0] == "2023-01-10"
        assert bob["salary"].iloc[0] == 72000

    def test_no_duplicates_returns_all_rows(self, drop_config, tmp_path):
        """When no duplicates exist, all rows are returned."""
        csv_path = tmp_path / "unique.csv"
        csv_path.write_text(
            "employee_id,name,department,hire_date\n"
            "1,Alice,Engineering,2020-01-15\n"
            "2,Bob,Marketing,2021-03-20\n"
            "3,Charlie,Sales,2022-05-10\n"
        )
        ingestor = DataIngestor(drop_config)
        df = ingestor.ingest(str(csv_path))
        assert len(df) == 3


class TestLargeDataset:
    """Tests for handling large datasets (10,000+ records)."""

    def test_ingest_10000_records(self, drop_config, tmp_path):
        """Ingestion supports at least 10,000 records without failure."""
        n = 10000
        data = {
            "employee_id": range(1, n + 1),
            "name": [f"Employee_{i}" for i in range(1, n + 1)],
            "department": np.random.default_rng(42).choice(
                ["Eng", "Sales", "HR", "Marketing"], n
            ),
            "hire_date": pd.date_range("2015-01-01", periods=n, freq="D")
            .strftime("%Y-%m-%d")
            .tolist(),
        }
        df = pd.DataFrame(data)
        csv_path = tmp_path / "large.csv"
        df.to_csv(csv_path, index=False)

        ingestor = DataIngestor(drop_config)
        result = ingestor.ingest(str(csv_path))
        assert len(result) == n
