"""ETL ingestion module for reading and validating employee CSV data."""

import logging

import pandas as pd

from src.pipeline.models import IngestionConfig, ValidationResult

logger = logging.getLogger(__name__)


class SchemaValidationError(Exception):
    """Raised when the CSV file is missing required columns."""

    def __init__(self, missing_columns: list[str]):
        self.missing_columns = missing_columns
        columns_str = ", ".join(missing_columns)
        super().__init__(f"Missing required columns: {columns_str}")


class DataIngestor:
    """Ingests raw employee CSV data with schema validation.

    Reads CSV files, validates that all required columns are present,
    and returns a validated DataFrame for downstream processing.
    """

    def __init__(self, config: IngestionConfig):
        """Initialize the ingestor with ingestion configuration.

        Args:
            config: IngestionConfig specifying required columns and strategies.
        """
        self.config = config

    def ingest(self, file_path: str) -> pd.DataFrame:
        """Read a CSV file, validate schema, handle nulls, and deduplicate.

        Args:
            file_path: Path to the CSV file to ingest.

        Returns:
            A validated, cleaned, and deduplicated pandas DataFrame.

        Raises:
            SchemaValidationError: If required columns are missing.
            FileNotFoundError: If the file does not exist.
        """
        df = pd.read_csv(file_path)
        self.validate_schema(df)
        df = self._handle_nulls(df)
        df = self._deduplicate(df)
        return df.reset_index(drop=True)

    def _handle_nulls(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle null values in required fields based on configured strategy.

        Logs row numbers (0-based indices) that contain nulls in required fields,
        then applies the null_strategy: 'drop' removes those rows, 'fill_default'
        fills with appropriate defaults (empty string for object/string columns,
        0 for numeric columns).

        Args:
            df: The DataFrame to process.

        Returns:
            DataFrame with nulls handled according to strategy.
        """
        required_cols = [
            col for col in self.config.required_columns if col in df.columns
        ]
        null_mask = df[required_cols].isnull().any(axis=1)
        null_row_indices = df.index[null_mask].tolist()

        if null_row_indices:
            logger.warning(
                "Null values found in required fields at row indices: %s",
                null_row_indices,
            )

        if not null_row_indices:
            return df

        if self.config.null_strategy == "drop":
            df = df[~null_mask]
        elif self.config.null_strategy == "fill_default":
            for col in required_cols:
                if df[col].dtype == object:
                    df[col] = df[col].fillna("")
                else:
                    df[col] = df[col].fillna(0)

        return df

    def _deduplicate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Deduplicate records by configured key, keeping the most recent.

        Groups by dedup_key (e.g. employee_id), sorts by dedup_sort (e.g. hire_date)
        descending, and keeps the first (most recent) record per group.

        Args:
            df: The DataFrame to deduplicate.

        Returns:
            Deduplicated DataFrame.
        """
        dedup_key = self.config.dedup_key
        dedup_sort = self.config.dedup_sort

        if dedup_key not in df.columns or dedup_sort not in df.columns:
            return df

        df = df.sort_values(by=dedup_sort, ascending=False)
        df = df.drop_duplicates(subset=[dedup_key], keep="first")
        return df

    def validate_schema(self, df: pd.DataFrame) -> ValidationResult:
        """Check that all required columns are present in the DataFrame.

        Args:
            df: The DataFrame to validate.

        Returns:
            A ValidationResult indicating success.

        Raises:
            SchemaValidationError: If any required columns are missing.
        """
        df_columns = set(df.columns)
        required = set(self.config.required_columns)
        missing = sorted(required - df_columns)

        if missing:
            raise SchemaValidationError(missing)

        return ValidationResult(is_valid=True, missing_columns=[])
