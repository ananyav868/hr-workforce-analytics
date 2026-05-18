"""Unit tests for the DataTransformer class - cleaning and standardization."""

import pandas as pd
import pytest

from src.etl.transformation import DataTransformer
from src.pipeline.models import TransformationConfig, TransformationLog


@pytest.fixture
def config():
    """Create a basic TransformationConfig for testing."""
    return TransformationConfig(
        encoding_strategy="label",
        feature_derivations=[],
    )


@pytest.fixture
def transformer(config):
    """Create a DataTransformer instance."""
    return DataTransformer(config)


class TestColumnStandardization:
    """Tests for column name standardization to snake_case."""

    def test_spaces_replaced_with_underscores(self, transformer):
        df = pd.DataFrame({"First Name": ["Alice"], "Last Name": ["Smith"]})
        result, log = transformer.transform(df)
        assert "first_name" in result.columns
        assert "last_name" in result.columns

    def test_hyphens_replaced_with_underscores(self, transformer):
        df = pd.DataFrame({"hire-date": ["2023-01-01"], "job-role": ["Engineer"]})
        result, log = transformer.transform(df)
        assert "hire_date" in result.columns
        assert "job_role" in result.columns

    def test_uppercase_converted_to_lowercase(self, transformer):
        df = pd.DataFrame({"EmployeeID": [1], "Department": ["HR"]})
        result, log = transformer.transform(df)
        assert "employeeid" in result.columns
        assert "department" in result.columns

    def test_mixed_separators(self, transformer):
        df = pd.DataFrame({"Hire Date": ["2023-01-01"], "Over-Time Hours": [10]})
        result, log = transformer.transform(df)
        assert "hire_date" in result.columns
        assert "over_time_hours" in result.columns

    def test_already_snake_case_unchanged(self, transformer):
        df = pd.DataFrame({"employee_id": [1], "hire_date": ["2023-01-01"]})
        result, log = transformer.transform(df)
        assert "employee_id" in result.columns
        assert "hire_date" in result.columns

    def test_special_characters_removed(self, transformer):
        df = pd.DataFrame({"salary($)": [50000], "score%": [85]})
        result, log = transformer.transform(df)
        assert "salary" in result.columns
        assert "score" in result.columns

    def test_standardization_logged(self, transformer):
        df = pd.DataFrame({"First Name": ["Alice"], "employee_id": [1]})
        result, log = transformer.transform(df)
        ops = [t for t in log.transformations if t["operation"] == "standardize_column_names"]
        assert len(ops) == 1
        assert ops[0]["rows_affected"] == 1  # Only "First Name" was renamed


class TestDataTypeEnforcement:
    """Tests for consistent data type enforcement."""

    def test_date_columns_converted_to_datetime(self, transformer):
        df = pd.DataFrame({
            "hire_date": ["2023-01-15", "2022-06-01"],
            "name": ["Alice", "Bob"],
        })
        result, log = transformer.transform(df)
        assert pd.api.types.is_datetime64_any_dtype(result["hire_date"])

    def test_invalid_dates_coerced_to_nat(self, transformer):
        df = pd.DataFrame({
            "hire_date": ["2023-01-15", "not-a-date", "2022-06-01"],
            "name": ["Alice", "Bob", "Charlie"],
        })
        result, log = transformer.transform(df)
        assert pd.api.types.is_datetime64_any_dtype(result["hire_date"])
        assert result["hire_date"].isnull().sum() == 1

    def test_numeric_columns_converted(self, transformer):
        df = pd.DataFrame({
            "age": ["30", "25", "40"],
            "salary": ["50000", "60000", "70000"],
            "name": ["Alice", "Bob", "Charlie"],
        })
        result, log = transformer.transform(df)
        assert pd.api.types.is_numeric_dtype(result["age"])
        assert pd.api.types.is_numeric_dtype(result["salary"])

    def test_invalid_numeric_coerced_to_nan(self, transformer):
        df = pd.DataFrame({
            "age": ["30", "unknown", "40"],
            "name": ["Alice", "Bob", "Charlie"],
        })
        result, log = transformer.transform(df)
        assert pd.api.types.is_numeric_dtype(result["age"])
        assert result["age"].isnull().sum() == 1

    def test_already_correct_types_not_reprocessed(self, transformer):
        df = pd.DataFrame({
            "hire_date": pd.to_datetime(["2023-01-15", "2022-06-01"]),
            "age": [30, 25],
            "name": ["Alice", "Bob"],
        })
        result, log = transformer.transform(df)
        # No type conversion entries should be logged for already-correct types
        type_ops = [
            t for t in log.transformations
            if t["operation"] in ("convert_to_datetime", "convert_to_numeric")
        ]
        assert len(type_ops) == 0

    def test_type_enforcement_logged(self, transformer):
        df = pd.DataFrame({
            "hire_date": ["2023-01-15"],
            "age": ["30"],
            "name": ["Alice"],
        })
        result, log = transformer.transform(df)
        ops = [t for t in log.transformations if t["operation"] == "convert_to_datetime"]
        assert len(ops) == 1
        assert ops[0]["column"] == "hire_date"

        ops = [t for t in log.transformations if t["operation"] == "convert_to_numeric"]
        assert len(ops) == 1
        assert ops[0]["column"] == "age"


class TestDuplicateRemoval:
    """Tests for duplicate row removal."""

    def test_duplicate_rows_removed(self, transformer):
        df = pd.DataFrame({
            "employee_id": [1, 1, 2],
            "name": ["Alice", "Alice", "Bob"],
            "age": [30, 30, 25],
        })
        result, log = transformer.transform(df)
        assert len(result) == 2

    def test_no_duplicates_no_change(self, transformer):
        df = pd.DataFrame({
            "employee_id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
        })
        result, log = transformer.transform(df)
        assert len(result) == 3

    def test_duplicate_removal_logged(self, transformer):
        df = pd.DataFrame({
            "employee_id": [1, 1, 2],
            "name": ["Alice", "Alice", "Bob"],
            "age": [30, 30, 25],
        })
        result, log = transformer.transform(df)
        ops = [t for t in log.transformations if t["operation"] == "remove_duplicates"]
        assert len(ops) == 1
        assert ops[0]["rows_affected"] == 1

    def test_no_log_entry_when_no_duplicates(self, transformer):
        df = pd.DataFrame({
            "employee_id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
        })
        result, log = transformer.transform(df)
        ops = [t for t in log.transformations if t["operation"] == "remove_duplicates"]
        assert len(ops) == 0


class TestTransformationLog:
    """Tests for transformation log completeness."""

    def test_log_captures_all_operations(self, transformer):
        df = pd.DataFrame({
            "Hire Date": ["2023-01-15", "2023-01-15"],
            "Age": ["30", "30"],
            "Name": ["Alice", "Alice"],
        })
        result, log = transformer.transform(df)
        # Should have: column standardization, date conversion, numeric conversion, dedup
        assert len(log.transformations) >= 3

    def test_log_entries_have_required_fields(self, transformer):
        df = pd.DataFrame({
            "Hire Date": ["2023-01-15"],
            "Name": ["Alice"],
        })
        result, log = transformer.transform(df)
        for entry in log.transformations:
            assert "column" in entry
            assert "operation" in entry
            assert "rows_affected" in entry
            assert "values_imputed" in entry

    def test_transform_returns_tuple(self, transformer):
        df = pd.DataFrame({"name": ["Alice"]})
        result = transformer.transform(df)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], pd.DataFrame)
        assert isinstance(result[1], TransformationLog)
