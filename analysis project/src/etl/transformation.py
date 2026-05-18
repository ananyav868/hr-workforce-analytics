"""ETL transformation module for cleaning and standardizing employee data."""

import logging
import re
from typing import Any, Callable, Dict

import pandas as pd

from src.pipeline.models import TransformationConfig, TransformationLog

logger = logging.getLogger(__name__)


class DataTransformer:
    """Transforms raw employee data into a cleaned, standardized dataset.

    Applies column name standardization, data type enforcement,
    deduplication, and config-driven feature derivation. Logs each
    transformation applied.
    """

    # Registry mapping logic type names to derivation callables.
    # Each callable has signature: (df, derivation_config) -> pd.Series
    _derivation_registry: Dict[str, Callable[[pd.DataFrame, Dict[str, Any]], pd.Series]] = {}

    @classmethod
    def register_derivation(cls, logic_name: str):
        """Decorator to register a new derivation logic type.

        Args:
            logic_name: The name used in config to reference this logic.

        Returns:
            Decorator that registers the function.
        """
        def decorator(func: Callable[[pd.DataFrame, Dict[str, Any]], pd.Series]):
            cls._derivation_registry[logic_name] = func
            return func
        return decorator

    def __init__(self, config: TransformationConfig):
        """Initialize the transformer with transformation configuration.

        Args:
            config: TransformationConfig specifying encoding strategy
                and feature derivations.
        """
        self.config = config

    def transform(self, df: pd.DataFrame) -> tuple[pd.DataFrame, TransformationLog]:
        """Apply cleaning and standardization transformations to the DataFrame.

        Steps:
            1. Standardize column names to snake_case
            2. Enforce consistent data types
            3. Remove duplicate rows
            4. Derive features from config
            5. Encode categorical columns

        Args:
            df: The raw DataFrame to transform.

        Returns:
            A tuple of (cleaned DataFrame, TransformationLog recording operations).
        """
        log = TransformationLog()

        df = self._standardize_column_names(df, log)
        df = self._enforce_data_types(df, log)
        df = self._remove_duplicates(df, log)
        df = self.derive_features(df, log)
        df = self.encode_categoricals(df, log)

        return df.reset_index(drop=True), log

    def derive_features(
        self, df: pd.DataFrame, log: TransformationLog | None = None
    ) -> pd.DataFrame:
        """Derive new feature columns based on configuration.

        Iterates over config.feature_derivations and applies the registered
        logic for each derivation. New logic types can be added via the
        register_derivation class method without modifying this code.

        Args:
            df: The DataFrame to derive features on.
            log: Optional TransformationLog to record operations.

        Returns:
            DataFrame with derived feature columns added.
        """
        if not self.config.feature_derivations:
            return df

        df = df.copy()

        for derivation in self.config.feature_derivations:
            name = derivation["name"]
            logic = derivation["logic"]
            source = derivation["source"]

            if logic not in self._derivation_registry:
                logger.warning(
                    "Unknown derivation logic '%s' for feature '%s', skipping.",
                    logic,
                    name,
                )
                continue

            if source not in df.columns:
                logger.warning(
                    "Source column '%s' not found for feature '%s', skipping.",
                    source,
                    name,
                )
                continue

            derive_fn = self._derivation_registry[logic]
            df[name] = derive_fn(df, derivation)

            rows_affected = df[name].notna().sum()
            if log is not None:
                log.add(
                    column=name,
                    operation=f"derive_feature_{logic}",
                    rows_affected=int(rows_affected),
                )
            logger.info(
                "Derived feature '%s' using logic '%s' from source '%s' (%d rows)",
                name,
                logic,
                source,
                rows_affected,
            )

        return df

    def encode_categoricals(
        self, df: pd.DataFrame, log: TransformationLog | None = None
    ) -> pd.DataFrame:
        """Encode categorical columns using the configured encoding strategy.

        Identifies columns with object dtype and applies either label encoding
        (using pandas factorize) or one-hot encoding (using pd.get_dummies)
        based on the encoding_strategy in config.

        Args:
            df: The DataFrame with categorical columns to encode.
            log: Optional TransformationLog to record operations.

        Returns:
            DataFrame with categorical columns encoded.
        """
        strategy = self.config.encoding_strategy
        categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()

        if not categorical_cols:
            return df

        df = df.copy()

        if strategy == "onehot":
            df = pd.get_dummies(df, columns=categorical_cols, dtype=int)
            for col in categorical_cols:
                if log is not None:
                    log.add(
                        column=col,
                        operation="encode_onehot",
                        rows_affected=len(df),
                    )
                logger.info(
                    "Applied one-hot encoding to column '%s' (%d rows)",
                    col,
                    len(df),
                )
        else:
            # Default to label encoding
            for col in categorical_cols:
                codes, _ = pd.factorize(df[col])
                df[col] = codes
                if log is not None:
                    log.add(
                        column=col,
                        operation="encode_label",
                        rows_affected=len(df),
                    )
                logger.info(
                    "Applied label encoding to column '%s' (%d rows)",
                    col,
                    len(df),
                )

        return df

    def _standardize_column_names(
        self, df: pd.DataFrame, log: TransformationLog
    ) -> pd.DataFrame:
        """Standardize all column names to snake_case.

        Converts to lowercase, replaces spaces and hyphens with underscores,
        removes non-alphanumeric characters (except underscores), and collapses
        consecutive underscores.

        Args:
            df: The DataFrame whose columns to standardize.
            log: TransformationLog to record the operation.

        Returns:
            DataFrame with standardized column names.
        """
        original_columns = list(df.columns)
        new_columns = [self._to_snake_case(col) for col in original_columns]

        renamed_count = sum(
            1 for old, new in zip(original_columns, new_columns) if old != new
        )

        df = df.copy()
        df.columns = new_columns

        if renamed_count > 0:
            log.add(
                column="*",
                operation="standardize_column_names",
                rows_affected=renamed_count,
            )
            logger.info(
                "Standardized %d column name(s) to snake_case", renamed_count
            )

        return df

    def _to_snake_case(self, name: str) -> str:
        """Convert a column name to snake_case.

        Args:
            name: The original column name.

        Returns:
            The snake_case version of the name.
        """
        # Convert to lowercase
        result = name.lower()
        # Replace spaces and hyphens with underscores
        result = re.sub(r"[\s\-]+", "_", result)
        # Remove non-alphanumeric characters (except underscores)
        result = re.sub(r"[^a-z0-9_]", "", result)
        # Collapse consecutive underscores
        result = re.sub(r"_+", "_", result)
        # Strip leading/trailing underscores
        result = result.strip("_")
        return result

    def _enforce_data_types(
        self, df: pd.DataFrame, log: TransformationLog
    ) -> pd.DataFrame:
        """Enforce consistent data types on known columns.

        Converts date-like columns to datetime and numeric-like columns
        to appropriate numeric types.

        Args:
            df: The DataFrame to type-enforce.
            log: TransformationLog to record the operations.

        Returns:
            DataFrame with enforced data types.
        """
        df = df.copy()

        # Columns that should be datetime
        date_columns = [
            col for col in df.columns if "date" in col
        ]

        for col in date_columns:
            if col in df.columns and not pd.api.types.is_datetime64_any_dtype(df[col]):
                original_nulls = df[col].isnull().sum()
                df[col] = pd.to_datetime(df[col], errors="coerce")
                new_nulls = df[col].isnull().sum()
                coerced_count = new_nulls - original_nulls
                log.add(
                    column=col,
                    operation="convert_to_datetime",
                    rows_affected=len(df),
                    values_imputed=coerced_count,
                )
                logger.info(
                    "Converted column '%s' to datetime (%d values coerced to NaT)",
                    col,
                    coerced_count,
                )

        # Columns that should be numeric
        numeric_columns = [
            col
            for col in df.columns
            if col in ("age", "salary", "satisfaction_score", "overtime_hours")
        ]

        for col in numeric_columns:
            if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
                original_nulls = df[col].isnull().sum()
                df[col] = pd.to_numeric(df[col], errors="coerce")
                new_nulls = df[col].isnull().sum()
                coerced_count = new_nulls - original_nulls
                log.add(
                    column=col,
                    operation="convert_to_numeric",
                    rows_affected=len(df),
                    values_imputed=coerced_count,
                )
                logger.info(
                    "Converted column '%s' to numeric (%d values coerced to NaN)",
                    col,
                    coerced_count,
                )

        return df

    def _remove_duplicates(
        self, df: pd.DataFrame, log: TransformationLog
    ) -> pd.DataFrame:
        """Remove duplicate rows from the DataFrame.

        Args:
            df: The DataFrame to deduplicate.
            log: TransformationLog to record the operation.

        Returns:
            DataFrame with duplicate rows removed.
        """
        original_count = len(df)
        df = df.drop_duplicates()
        removed_count = original_count - len(df)

        if removed_count > 0:
            log.add(
                column="*",
                operation="remove_duplicates",
                rows_affected=removed_count,
            )
            logger.info("Removed %d duplicate row(s)", removed_count)

        return df

# --- Registered derivation logic functions ---
# New derivation types can be added by decorating a function with
# @DataTransformer.register_derivation("logic_name") without modifying
# existing code.


@DataTransformer.register_derivation("months_since_hire")
def _derive_months_since_hire(df: pd.DataFrame, derivation: Dict[str, Any]) -> pd.Series:
    """Compute months between hire_date and today.

    Args:
        df: The source DataFrame.
        derivation: Config dict with 'source' key pointing to the date column.

    Returns:
        Series of tenure in months (float).
    """
    source = derivation["source"]
    today = pd.Timestamp.now().normalize()
    dates = pd.to_datetime(df[source], errors="coerce")
    # Calculate months as approximate difference
    delta = today - dates
    months = delta.dt.days / 30.44  # average days per month
    return months.round(1)


@DataTransformer.register_derivation("bucket")
def _derive_bucket(df: pd.DataFrame, derivation: Dict[str, Any]) -> pd.Series:
    """Bucket a numeric column using pd.cut with configured bins and labels.

    Args:
        df: The source DataFrame.
        derivation: Config dict with 'source', 'params.bins', 'params.labels'.

    Returns:
        Series of categorical bucket labels.
    """
    source = derivation["source"]
    params = derivation.get("params", {})
    bins = params["bins"]
    labels = params["labels"]
    values = pd.to_numeric(df[source], errors="coerce")
    return pd.cut(values, bins=bins, labels=labels, include_lowest=True)


@DataTransformer.register_derivation("threshold")
def _derive_threshold(df: pd.DataFrame, derivation: Dict[str, Any]) -> pd.Series:
    """Create a boolean flag: 1 if value > threshold, 0 otherwise.

    Args:
        df: The source DataFrame.
        derivation: Config dict with 'source' and 'params.threshold'.

    Returns:
        Series of integer flags (1 or 0).
    """
    source = derivation["source"]
    params = derivation.get("params", {})
    threshold = params["threshold"]
    values = pd.to_numeric(df[source], errors="coerce")
    return (values > threshold).astype(int)


@DataTransformer.register_derivation("months_since_event")
def _derive_months_since_event(df: pd.DataFrame, derivation: Dict[str, Any]) -> pd.Series:
    """Compute months between a date column and today.

    Similar to months_since_hire but for arbitrary date events (e.g., promotion_date).
    Returns NaN for null/missing dates.

    Args:
        df: The source DataFrame.
        derivation: Config dict with 'source' key pointing to the date column.

    Returns:
        Series of months since the event (float), NaN where date is missing.
    """
    source = derivation["source"]
    today = pd.Timestamp.now().normalize()
    dates = pd.to_datetime(df[source], errors="coerce")
    delta = today - dates
    months = delta.dt.days / 30.44
    return months.round(1)
