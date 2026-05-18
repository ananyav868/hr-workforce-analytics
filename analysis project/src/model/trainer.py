"""Attrition prediction model training and evaluation module."""

import os
import warnings
from typing import Any, Dict, List

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from src.pipeline.models import ModelConfig, TrainingResult


class ModelTrainer:
    """Trains and evaluates classification models for attrition prediction."""

    def __init__(self, config: ModelConfig):
        """Configure algorithms, hyperparameters, random seed, and test split.

        Args:
            config: ModelConfig with algorithms, test_size, random_seed, hyperparameters.
        """
        self.config = config
        self.models: Dict[str, Any] = {}

    def train(self, df: pd.DataFrame) -> TrainingResult:
        """Train models, evaluate, and rank by AUC-ROC.

        Expects a DataFrame with an 'attrition' target column (binary 0/1)
        and all other columns as features.

        Args:
            df: DataFrame with features and 'attrition' target column.

        Returns:
            TrainingResult with comparison table, best model name,
            feature importances, and per-model metrics.

        Warns:
            UserWarning: If dataset has fewer than 100 records.
        """
        if len(df) < 100:
            warnings.warn(
                f"Dataset has only {len(df)} records. "
                "Model reliability may be compromised with fewer than 100 records.",
                UserWarning,
                stacklevel=2,
            )

        # Separate features and target
        X = df.drop(columns=["attrition"])
        y = df["attrition"]

        # Split data 80/20 with deterministic seed
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=self.config.test_size,
            random_state=self.config.random_seed,
            stratify=y,
        )

        feature_names = list(X.columns)

        # Train and evaluate each configured algorithm
        metrics: Dict[str, Dict[str, float]] = {}
        model_comparison: List[Dict[str, Any]] = []

        for algorithm in self.config.algorithms:
            model = self._create_model(algorithm)
            model.fit(X_train, y_train)
            self.models[algorithm] = model

            # Generate predictions
            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test)[:, 1]

            # Evaluate metrics
            model_metrics = {
                "accuracy": accuracy_score(y_test, y_pred),
                "precision": precision_score(y_test, y_pred, zero_division=0),
                "recall": recall_score(y_test, y_pred, zero_division=0),
                "f1": f1_score(y_test, y_pred, zero_division=0),
                "auc_roc": roc_auc_score(y_test, y_proba),
            }
            metrics[algorithm] = model_metrics

            model_comparison.append({
                "model_name": algorithm,
                "accuracy": model_metrics["accuracy"],
                "precision": model_metrics["precision"],
                "recall": model_metrics["recall"],
                "f1": model_metrics["f1"],
                "auc_roc": model_metrics["auc_roc"],
            })

        # Sort comparison table by AUC-ROC descending
        model_comparison.sort(key=lambda x: x["auc_roc"], reverse=True)

        # Determine best model
        best_model_name = model_comparison[0]["model_name"]
        best_model = self.models[best_model_name]

        # Extract feature importances from best model
        feature_importances = self._extract_feature_importances(
            best_model, feature_names
        )

        return TrainingResult(
            model_comparison=model_comparison,
            best_model_name=best_model_name,
            feature_importances=feature_importances,
            metrics=metrics,
        )

    def _create_model(self, algorithm: str) -> Any:
        """Create a model instance with configured hyperparameters.

        Args:
            algorithm: Name of the algorithm (logistic_regression or random_forest).

        Returns:
            Configured sklearn model instance.

        Raises:
            ValueError: If algorithm is not supported.
        """
        hyperparams = self.config.hyperparameters.get(algorithm, {})

        if algorithm == "logistic_regression":
            return LogisticRegression(
                random_state=self.config.random_seed,
                **hyperparams,
            )
        elif algorithm == "random_forest":
            return RandomForestClassifier(
                random_state=self.config.random_seed,
                **hyperparams,
            )
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

    def get_feature_importance(
        self, model: Any, feature_names: List[str]
    ) -> pd.DataFrame:
        """Extract and rank feature importances from a trained model.

        For tree-based models (e.g., random forest), uses feature_importances_.
        For linear models (e.g., logistic regression), uses abs(coef_).

        Args:
            model: Trained sklearn model.
            feature_names: List of feature column names.

        Returns:
            DataFrame with columns ['feature', 'importance'] sorted by
            importance descending.
        """
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
        elif hasattr(model, "coef_"):
            importances = np.abs(model.coef_[0])
        else:
            # Fallback: equal importance
            importances = np.ones(len(feature_names)) / len(feature_names)

        df = pd.DataFrame({
            "feature": feature_names,
            "importance": importances.astype(float),
        })
        df = df.sort_values("importance", ascending=False).reset_index(drop=True)
        return df

    def serialize_model(self, model: Any, path: str) -> None:
        """Save a trained model to disk as a .joblib file.

        Ensures the target directory exists before saving.

        Args:
            model: Trained sklearn model to serialize.
            path: File path where the model should be saved (should end with .joblib).
        """
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        joblib.dump(model, path)

    def _extract_feature_importances(
        self, model: Any, feature_names: List[str]
    ) -> Dict[str, float]:
        """Extract feature importances from a trained model.

        For logistic regression, uses absolute coefficient values.
        For random forest, uses built-in feature_importances_.

        Args:
            model: Trained sklearn model.
            feature_names: List of feature column names.

        Returns:
            Dict mapping feature name to importance value, sorted descending.
        """
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
        elif hasattr(model, "coef_"):
            importances = np.abs(model.coef_[0])
        else:
            # Fallback: equal importance
            importances = np.ones(len(feature_names)) / len(feature_names)

        # Create dict sorted by importance descending
        importance_pairs = sorted(
            zip(feature_names, importances),
            key=lambda x: x[1],
            reverse=True,
        )
        return {name: float(value) for name, value in importance_pairs}
