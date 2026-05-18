"""Attrition prediction scoring module for generating employee attrition probabilities."""

import joblib
import pandas as pd


class ModelScorer:
    """Loads a serialized model and generates attrition probability predictions."""

    def __init__(self, model_path: str):
        """Load a serialized model from disk.

        Args:
            model_path: Path to a serialized .joblib model file.
        """
        self.model_path = model_path
        self.model = joblib.load(model_path)

    def score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate attrition probabilities for each employee.

        Accepts a DataFrame with the same feature columns the model was trained on
        (excluding the 'attrition' target column). Uses predict_proba to get the
        probability of attrition (class 1) and adds it as a new column.

        Args:
            df: DataFrame with feature columns matching the trained model's expectations.

        Returns:
            DataFrame with an added 'attrition_probability' column containing
            predicted probabilities in the [0, 1] range.
        """
        # Drop target column if present to get only features
        feature_df = df.drop(columns=["attrition"], errors="ignore")

        # Get probability of class 1 (attrition)
        probabilities = self.model.predict_proba(feature_df)[:, 1]

        # Add predictions to the original DataFrame
        result = df.copy()
        result["attrition_probability"] = probabilities

        return result
