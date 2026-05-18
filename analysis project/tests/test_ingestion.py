"""Unit tests for the DataIngestor class - CSV reading and schema validation."""

import os
import tempfile

import pandas as pd
import pytest

from src.etl.ingestion import DataIngestor, SchemaValidationError
from src.pipeline.models import IngestionConfig


@pytest.fixture
def config():
    """Create a basic IngestionConfig for testing."""
    return IngestionConfig(
        required_columns=["employee_id", "name", "department", "hire_date"],
        null_strategy="drop",
        dedup_key="employee_id",
        dedup_sort="hire_date",
    )


@pytest.fixture
def valid_csv(tmp_path):
    """Create a valid CSV file with all required columns."""
    csv_path = tmp_path / "valid.csv"
    csv_path.write_text(
        "employee_id,name,department,hire_date,salary\n"
        "1,Alice,Engineering,2020-01-15,80000\n"
        "2,Bob,Marketing,2021-03-20,65000\n"
    )
    return str(csv_path)


@pytest.fixture
def missing_columns_csv(tmp_path):
    """Create a CSV file missing required columns."""
    csv_path = tmp_path / "missing.csv"
    csv_path.write_text(
        "employee_id,salary\n"
        "1,80000\n"
        "2,65000\n"
    )
    return str(csv_path)


class TestDataIngestorSchemaValidation:
    """Tests for schema validation in DataIngestor."""

    def test_ingest_valid_csv_returns_dataframe(self, config, valid_csv):
        """Valid CSV with all required columns returns a DataFrame."""
        ingestor = DataIngestor(config)
        df = ingestor.ingest(valid_csv)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2

    def test_ingest_valid_csv_has_correct_columns(self, config, valid_csv):
        """Returned DataFrame contains all expected columns."""
        ingestor = DataIngestor(config)
        df = ingestor.ingest(valid_csv)
        for col in config.required_columns:
            assert col in df.columns

    def test_ingest_missing_columns_raises_error(self, config, missing_columns_csv):
        """CSV missing required columns raises SchemaValidationError."""
        ingestor = DataIngestor(config)
        with pytest.raises(SchemaValidationError) as exc_info:
            ingestor.ingest(missing_columns_csv)
        assert "department" in exc_info.value.missing_columns
        assert "hire_date" in exc_info.value.missing_columns
        assert "name" in exc_info.value.missing_columns

    def test_schema_validation_error_contains_missing_column_names(self, config, missing_columns_csv):
        """SchemaValidationError message lists the missing columns."""
        ingestor = DataIngestor(config)
        with pytest.raises(SchemaValidationError) as exc_info:
            ingestor.ingest(missing_columns_csv)
        error_msg = str(exc_info.value)
        assert "department" in error_msg
        assert "hire_date" in error_msg
        assert "name" in error_msg

    def test_validate_schema_returns_valid_result(self, config):
        """validate_schema returns ValidationResult with is_valid=True for valid data."""
        ingestor = DataIngestor(config)
        df = pd.DataFrame({
            "employee_id": [1],
            "name": ["Alice"],
            "department": ["Eng"],
            "hire_date": ["2020-01-01"],
        })
        result = ingestor.validate_schema(df)
        assert result.is_valid is True
        assert result.missing_columns == []

    def test_ingest_nonexistent_file_raises_error(self, config):
        """Ingesting a file that doesn't exist raises FileNotFoundError."""
        ingestor = DataIngestor(config)
        with pytest.raises(FileNotFoundError):
            ingestor.ingest("/nonexistent/path/data.csv")
