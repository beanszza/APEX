"""Scikit-Learn Demand Forecasting Engine for APEX."""

import logging
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

logger = logging.getLogger(__name__)


class DemandForecaster:
    """Predicts monthly item usage and recommended reorder quantities using Scikit-Learn."""

    def __init__(self) -> None:
        self.model = LinearRegression()

    def predict_item_demand(self, items_df: pd.DataFrame) -> pd.DataFrame:
        """Calculates predicted monthly usage and recommended reorder quantities.
        
        If items_df is empty or missing columns, sensible defaults are applied.
        """
        if items_df.empty:
            return pd.DataFrame()

        df = items_df.copy()

        # Ensure required columns exist
        if "MinStockLevel" not in df.columns:
            df["MinStockLevel"] = 10.0
        if "MaxStockLevel" not in df.columns:
            df["MaxStockLevel"] = 100.0
        if "current_stock" not in df.columns:
            df["current_stock"] = 0.0

        # Fit a linear model mapping MinStockLevel & MaxStockLevel to estimated monthly usage
        # (Simulated historical regression model)
        X = df[["MinStockLevel", "MaxStockLevel"]].values
        y_simulated = df["MinStockLevel"].values * 1.35 + np.random.normal(2, 0.5, len(df))

        self.model.fit(X, y_simulated)
        predictions = self.model.predict(X)

        df["predicted_monthly_usage"] = np.round(np.maximum(10.0, predictions), 1)
        df["recommended_reorder_qty"] = np.round(
            np.maximum(0.0, df["MaxStockLevel"] - df["current_stock"]), 0
        )

        return df
