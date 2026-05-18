"""Shared data classes and type definitions for the HR analytics pipeline."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class IngestionConfig:
    """Configuration for the data ingestion stage."""

    required_columns: List[str]
    null_strategy: str  # "drop" or "fill_default"
    dedup_key: str
    dedup_sort: str


@dataclass
class TransformationConfig:
    """Configuration for the data transformation stage."""

    encoding_strategy: str  # "label" or "onehot"
    feature_derivations: List[Dict[str, Any]]


@dataclass
class ModelConfig:
    """Configuration for the prediction modeling stage."""

    algorithms: List[str]
    test_size: float
    random_seed: int
    hyperparameters: Dict[str, Dict[str, Any]]


@dataclass
class ValidationResult:
    """Result of schema validation during ingestion."""

    is_valid: bool
    missing_columns: List[str] = field(default_factory=list)
    error_messages: List[str] = field(default_factory=list)


@dataclass
class TransformationLog:
    """Log of transformations applied during the transformation stage."""

    transformations: List[Dict[str, Any]] = field(default_factory=list)
    # Each entry: {"column": str, "operation": str, "rows_affected": int, "values_imputed": int}

    def add(self, column: str, operation: str, rows_affected: int = 0, values_imputed: int = 0) -> None:
        """Add a transformation record to the log."""
        self.transformations.append({
            "column": column,
            "operation": operation,
            "rows_affected": rows_affected,
            "values_imputed": values_imputed,
        })


@dataclass
class TrainingResult:
    """Result of model training and evaluation."""

    model_comparison: List[Dict[str, Any]]  # List of dicts with model name and metrics
    best_model_name: str
    feature_importances: Dict[str, float]
    metrics: Dict[str, Dict[str, float]]  # {model_name: {metric_name: value}}


@dataclass
class LoadResult:
    """Result of loading data into the SQL star schema."""

    rows_inserted: int
    rows_updated: int
    rows_rejected: int
    success: bool


@dataclass
class StageResult:
    """Result of an individual pipeline stage execution."""

    stage_name: str
    status: str  # "success" or "failure"
    start_time: datetime
    end_time: datetime
    row_count: int = 0
    error_message: Optional[str] = None


@dataclass
class PipelineResult:
    """Overall pipeline execution result."""

    stage_results: List[StageResult] = field(default_factory=list)
    total_time_seconds: float = 0.0
    final_status: str = "not_started"  # "success", "failure", or "not_started"
