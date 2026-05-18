"""Pipeline orchestrator module for sequencing and executing all pipeline stages.

Provides the PipelineOrchestrator class that loads configuration, initializes
logging, and runs ingestion, transformation, modeling, and SQL loading stages
sequentially with error handling and timing.

Requirements: 10.1, 10.2, 10.3, 10.5
"""

import logging
import random
import time
from datetime import datetime
from typing import Callable

import numpy as np
import yaml

from src.pipeline.models import (
    IngestionConfig,
    ModelConfig,
    PipelineResult,
    StageResult,
    TransformationConfig,
)

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orchestrates the end-to-end HR analytics pipeline.

    Loads YAML configuration, sets deterministic seeds for reproducibility,
    and executes pipeline stages sequentially: ingestion, transformation,
    modeling, and SQL loading. Halts on any stage failure.
    """

    def __init__(self, config_path: str):
        """Load YAML config, initialize logger, and set deterministic seed.

        Args:
            config_path: Path to the pipeline_config.yaml file.
        """
        self.config_path = config_path

        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        # Configure logging
        log_path = self.config.get("pipeline", {}).get("log_path", "logs/pipeline_run.log")
        self._configure_logging(log_path)

        # Set deterministic seed for reproducibility
        random_seed = self.config.get("model", {}).get("random_seed", 42)
        np.random.seed(random_seed)
        random.seed(random_seed)

        logger.info("PipelineOrchestrator initialized with config: %s", config_path)

    def run(self) -> PipelineResult:
        """Execute all pipeline stages sequentially. Halt on failure.

        Stages are executed in order:
            1. Ingestion - read and validate CSV data
            2. Transformation - clean and engineer features
            3. Modeling - train and evaluate attrition models
            4. SQL Loading - load results into star schema

        Returns:
            PipelineResult with per-stage status, timing, and row counts.
        """
        pipeline_start = time.time()
        result = PipelineResult()
        self._current_df = None

        logger.info("Pipeline execution started")

        stages = [
            ("ingestion", self._run_ingestion),
            ("transformation", self._run_transformation),
            ("modeling", self._run_modeling),
            ("sql_loading", self._run_sql_loading),
        ]

        for stage_name, stage_fn in stages:
            stage_result = self._run_stage(stage_name, stage_fn)
            result.stage_results.append(stage_result)

            if stage_result.status == "failure":
                result.final_status = "failure"
                result.total_time_seconds = time.time() - pipeline_start
                logger.error(
                    "Pipeline halted due to failure in stage '%s': %s",
                    stage_name,
                    stage_result.error_message,
                )
                return result

        result.final_status = "success"
        result.total_time_seconds = time.time() - pipeline_start
        logger.info(
            "Pipeline completed successfully in %.2f seconds",
            result.total_time_seconds,
        )
        return result

    def _run_stage(self, stage_name: str, stage_fn: Callable) -> StageResult:
        """Execute a single stage with timing, logging, and error capture.

        Args:
            stage_name: Human-readable name of the stage.
            stage_fn: Callable that executes the stage logic and returns a row count.

        Returns:
            StageResult with timing, status, and row count information.
        """
        logger.info("Stage '%s' started", stage_name)
        start_time = datetime.now()

        try:
            row_count = stage_fn()
            end_time = datetime.now()

            stage_result = StageResult(
                stage_name=stage_name,
                status="success",
                start_time=start_time,
                end_time=end_time,
                row_count=row_count if row_count is not None else 0,
            )

            logger.info(
                "Stage '%s' completed successfully: %d rows, duration=%.2fs",
                stage_name,
                stage_result.row_count,
                (end_time - start_time).total_seconds(),
            )

        except Exception as e:
            end_time = datetime.now()
            stage_result = StageResult(
                stage_name=stage_name,
                status="failure",
                start_time=start_time,
                end_time=end_time,
                row_count=0,
                error_message=str(e),
            )

            logger.error(
                "Stage '%s' failed after %.2fs: %s",
                stage_name,
                (end_time - start_time).total_seconds(),
                str(e),
            )

        return stage_result

    def _run_ingestion(self) -> int:
        """Execute the ingestion stage.

        Returns:
            Number of rows ingested.
        """
        from src.etl.ingestion import DataIngestor

        ingestion_cfg = self.config["ingestion"]
        config = IngestionConfig(
            required_columns=ingestion_cfg["required_columns"],
            null_strategy=ingestion_cfg["null_strategy"],
            dedup_key=ingestion_cfg["dedup_key"],
            dedup_sort=ingestion_cfg["dedup_sort"],
        )

        ingestor = DataIngestor(config)

        # Determine source file path from config or default
        file_path = ingestion_cfg.get("source_file", "data/employee_data.csv")
        self._current_df = ingestor.ingest(file_path)

        row_count = len(self._current_df)
        logger.info("Ingestion produced %d rows", row_count)
        return row_count

    def _run_transformation(self) -> int:
        """Execute the transformation stage.

        Returns:
            Number of rows after transformation.
        """
        from src.etl.transformation import DataTransformer

        transformation_cfg = self.config["transformation"]
        config = TransformationConfig(
            encoding_strategy=transformation_cfg["encoding_strategy"],
            feature_derivations=transformation_cfg.get("feature_derivations", []),
        )

        transformer = DataTransformer(config)
        self._current_df, transformation_log = transformer.transform(self._current_df)

        # Save a copy with original string values for SQL staging
        # (before encoding converts strings to integers)
        config_no_encode = TransformationConfig(
            encoding_strategy="label",  # doesn't matter, we skip encoding
            feature_derivations=transformation_cfg.get("feature_derivations", []),
        )
        transformer_raw = DataTransformer(config_no_encode)
        # Re-run without encoding: just clean + derive features
        from src.etl.ingestion import DataIngestor
        from src.pipeline.models import IngestionConfig
        ingestion_cfg = self.config["ingestion"]
        ingestor = DataIngestor(IngestionConfig(
            required_columns=ingestion_cfg["required_columns"],
            null_strategy=ingestion_cfg["null_strategy"],
            dedup_key=ingestion_cfg["dedup_key"],
            dedup_sort=ingestion_cfg["dedup_sort"],
        ))
        file_path = ingestion_cfg.get("source_file", "data/employee_data.csv")
        raw_df = ingestor.ingest(file_path)
        # Apply cleaning and feature derivation only (no encoding)
        import re
        import pandas as pd
        raw_df.columns = [re.sub(r'[\s\-]+', '_', c.lower()).strip('_') for c in raw_df.columns]
        # Derive features on raw data
        for derivation in transformation_cfg.get("feature_derivations", []):
            source = derivation["source"]
            name = derivation["name"]
            logic = derivation["logic"]
            if source not in raw_df.columns:
                continue
            if logic == "months_since_hire":
                dates = pd.to_datetime(raw_df[source], errors="coerce")
                raw_df[name] = ((pd.Timestamp.now().normalize() - dates).dt.days / 30.44).round(1)
            elif logic == "bucket":
                params = derivation.get("params", {})
                values = pd.to_numeric(raw_df[source], errors="coerce")
                raw_df[name] = pd.cut(values, bins=params["bins"], labels=params["labels"], include_lowest=True).astype(str)
            elif logic == "threshold":
                params = derivation.get("params", {})
                values = pd.to_numeric(raw_df[source], errors="coerce")
                raw_df[name] = (values > params["threshold"]).astype(int)
            elif logic == "months_since_event":
                dates = pd.to_datetime(raw_df[source], errors="coerce")
                raw_df[name] = ((pd.Timestamp.now().normalize() - dates).dt.days / 30.44).round(1)
        self._staging_df = raw_df

        row_count = len(self._current_df)
        logger.info("Transformation produced %d rows", row_count)
        return row_count

    def _run_modeling(self) -> int:
        """Execute the modeling stage.

        Trains models, serializes the best model to artifacts/.

        Returns:
            Number of rows scored.
        """
        from src.model.trainer import ModelTrainer

        model_cfg = self.config["model"]
        config = ModelConfig(
            algorithms=model_cfg["algorithms"],
            test_size=model_cfg["test_size"],
            random_seed=model_cfg["random_seed"],
            hyperparameters=model_cfg.get("hyperparameters", {}),
        )

        trainer = ModelTrainer(config)

        # Drop datetime columns and select only numeric features for modeling
        # (derived features like tenure_months, promotion_recency are numeric;
        #  categorical columns were label-encoded to integers, but pd.cut
        #  produces Categorical dtype that needs special handling)
        import pandas as pd
        model_df = self._current_df.copy()
        # Drop datetime columns
        datetime_cols = model_df.select_dtypes(include=["datetime64[ns]", "datetime64"]).columns
        model_df = model_df.drop(columns=datetime_cols)
        # Convert any remaining categorical columns to their integer codes
        for col in model_df.select_dtypes(include=["category"]).columns:
            model_df[col] = model_df[col].cat.codes
        # Drop any remaining object columns that weren't encoded
        object_cols = model_df.select_dtypes(include=["object"]).columns
        model_df = model_df.drop(columns=object_cols)
        # Fill NaN values (e.g., promotion_recency for employees without promotions)
        model_df = model_df.fillna(0)

        training_result = trainer.train(model_df)

        # Serialize best model to artifacts/
        best_model = trainer.models[training_result.best_model_name]
        model_path = "artifacts/best_model.joblib"
        trainer.serialize_model(best_model, model_path)

        logger.info(
            "Best model: %s (AUC-ROC: %.4f), saved to %s",
            training_result.best_model_name,
            training_result.model_comparison[0]["auc_roc"],
            model_path,
        )

        row_count = len(self._current_df)
        return row_count

    def _run_sql_loading(self) -> int:
        """Execute the SQL loading stage.

        Loads data to staging table and executes the star schema load procedure.

        Returns:
            Number of rows loaded to staging.
        """
        from src.sql.loader import SQLDataLoader

        db_cfg = self.config["database"]
        connection_string = db_cfg["connection_string"]
        staging_table = db_cfg["staging_table"]

        loader = SQLDataLoader(connection_string)

        # Load the pre-encoding DataFrame (with original string values) to staging
        staging_df = self._staging_df if hasattr(self, '_staging_df') else self._current_df
        row_count = loader.load_to_staging(staging_df, staging_table)

        # Validate row counts
        source_count = len(staging_df)
        if not loader.validate_row_counts(source_count, row_count):
            raise RuntimeError(
                f"Row count mismatch: source={source_count}, staging={row_count}"
            )

        logger.info(
            "SQL loading complete: %d rows loaded to staging table '%s'",
            row_count,
            staging_table,
        )

        return row_count

    def _configure_logging(self, log_path: str) -> None:
        """Configure structured logging to file and console.

        Sets up the root logger with both a FileHandler (writing to the
        configured log path) and a StreamHandler (writing to stdout), so
        that all modules in the project emit structured log output.

        Args:
            log_path: Path to the pipeline run log file.
        """
        import os
        import sys

        log_dir = os.path.dirname(log_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        # Structured log format with timestamp, level, module, and message
        log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(log_format, datefmt=date_format)

        # Configure the root logger so all modules (src.etl, src.model, etc.) log correctly
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        # File handler - write to logs/pipeline_run.log
        if not any(
            isinstance(h, logging.FileHandler)
            and getattr(h, "baseFilename", "").endswith(os.path.basename(log_path))
            for h in root_logger.handlers
        ):
            file_handler = logging.FileHandler(log_path, mode="a")
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

        # Console handler - write to stdout
        if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) for h in root_logger.handlers):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
