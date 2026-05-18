"""Unit tests for ModelTrainer class."""

import warnings

import numpy as np
import pandas as pd
import pytest

from src.model.trainer import ModelTrainer
from src.pipeline.models import ModelConfig


@pytest.fixture
def model_config():
    """Create a standard ModelConfig for testing."""
    return ModelConfig(
        algorithms=["logistic_regression", "random_forest"],
        test_size=0.2,
        random_seed=42,
        hyperparameters={
            "logistic_regression": {
                "max_iter": 1000,
                "solver": "lbfgs",
                "C": 1.0,
            },
            "random_forest": {
                "n_estimators": 100,
                "max_depth": 10,
                "min_samples_split": 5,
                "min_samples_leaf": 2,
            },
        },
    )


@pytest.fixture
def sample_df():
    """Create a sample DataFrame with enough records for training."""
    np.random.seed(42)
    n = 200
    df = pd.DataFrame({
        "feature_1": np.random.randn(n),
        "feature_2": np.random.randn(n),
        "feature_3": np.random.randint(0, 10, n),
        "feature_4": np.random.uniform(0, 1, n),
        "attrition": np.random.choice([0, 1], size=n, p=[0.7, 0.3]),
    })
    return df


@pytest.fixture
def small_df():
    """Create a small DataFrame with fewer than 100 records."""
    np.random.seed(42)
    n = 50
    df = pd.DataFrame({
        "feature_1": np.random.randn(n),
        "feature_2": np.random.randn(n),
        "attrition": np.random.choice([0, 1], size=n, p=[0.7, 0.3]),
    })
    return df


class TestModelTrainer:
    """Tests for ModelTrainer class."""

    def test_train_returns_training_result(self, model_config, sample_df):
        """Test that train() returns a valid TrainingResult."""
        trainer = ModelTrainer(model_config)
        result = trainer.train(sample_df)

        assert result.best_model_name in ["logistic_regression", "random_forest"]
        assert len(result.model_comparison) == 2
        assert len(result.metrics) == 2
        assert len(result.feature_importances) > 0

    def test_model_comparison_sorted_by_auc_roc(self, model_config, sample_df):
        """Test that model_comparison is sorted by AUC-ROC descending."""
        trainer = ModelTrainer(model_config)
        result = trainer.train(sample_df)

        auc_values = [m["auc_roc"] for m in result.model_comparison]
        assert auc_values == sorted(auc_values, reverse=True)

    def test_metrics_contain_all_required_fields(self, model_config, sample_df):
        """Test that each model's metrics include all required fields."""
        trainer = ModelTrainer(model_config)
        result = trainer.train(sample_df)

        required_metrics = {"accuracy", "precision", "recall", "f1", "auc_roc"}
        for model_name, model_metrics in result.metrics.items():
            assert set(model_metrics.keys()) == required_metrics

    def test_metrics_values_in_valid_range(self, model_config, sample_df):
        """Test that all metric values are between 0 and 1."""
        trainer = ModelTrainer(model_config)
        result = trainer.train(sample_df)

        for model_name, model_metrics in result.metrics.items():
            for metric_name, value in model_metrics.items():
                assert 0.0 <= value <= 1.0, (
                    f"{model_name}.{metric_name} = {value} is out of [0, 1] range"
                )

    def test_comparison_table_fields(self, model_config, sample_df):
        """Test that comparison table entries have all required fields."""
        trainer = ModelTrainer(model_config)
        result = trainer.train(sample_df)

        required_fields = {"model_name", "accuracy", "precision", "recall", "f1", "auc_roc"}
        for entry in result.model_comparison:
            assert set(entry.keys()) == required_fields

    def test_best_model_matches_highest_auc_roc(self, model_config, sample_df):
        """Test that best_model_name corresponds to highest AUC-ROC."""
        trainer = ModelTrainer(model_config)
        result = trainer.train(sample_df)

        assert result.best_model_name == result.model_comparison[0]["model_name"]

    def test_feature_importances_match_features(self, model_config, sample_df):
        """Test that feature importances cover all input features."""
        trainer = ModelTrainer(model_config)
        result = trainer.train(sample_df)

        feature_cols = [c for c in sample_df.columns if c != "attrition"]
        assert set(result.feature_importances.keys()) == set(feature_cols)

    def test_feature_importances_sorted_descending(self, model_config, sample_df):
        """Test that feature importances are sorted by value descending."""
        trainer = ModelTrainer(model_config)
        result = trainer.train(sample_df)

        values = list(result.feature_importances.values())
        assert values == sorted(values, reverse=True)

    def test_models_stored_as_instance_attributes(self, model_config, sample_df):
        """Test that trained models are stored in self.models dict."""
        trainer = ModelTrainer(model_config)
        trainer.train(sample_df)

        assert "logistic_regression" in trainer.models
        assert "random_forest" in trainer.models

    def test_warning_raised_for_small_dataset(self, model_config, small_df):
        """Test that a warning is raised when dataset has fewer than 100 records."""
        trainer = ModelTrainer(model_config)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            trainer.train(small_df)

            assert len(w) >= 1
            warning_messages = [str(warning.message) for warning in w]
            assert any("fewer than 100 records" in msg for msg in warning_messages)

    def test_deterministic_results_with_same_seed(self, model_config, sample_df):
        """Test that training with the same seed produces identical results."""
        trainer1 = ModelTrainer(model_config)
        result1 = trainer1.train(sample_df)

        trainer2 = ModelTrainer(model_config)
        result2 = trainer2.train(sample_df)

        for m1, m2 in zip(result1.model_comparison, result2.model_comparison):
            assert m1["auc_roc"] == m2["auc_roc"]
            assert m1["model_name"] == m2["model_name"]

    def test_unsupported_algorithm_raises_error(self, model_config, sample_df):
        """Test that an unsupported algorithm raises ValueError."""
        model_config.algorithms = ["unsupported_algo"]
        model_config.hyperparameters["unsupported_algo"] = {}
        trainer = ModelTrainer(model_config)

        with pytest.raises(ValueError, match="Unsupported algorithm"):
            trainer.train(sample_df)
