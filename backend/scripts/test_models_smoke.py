"""
Smoke-test all forecasting models without needing the DB.

Run:
  ./.venv/bin/python backend/scripts/test_models_smoke.py
"""

import sys
from pathlib import Path

# Ensure repo root on sys.path so `import backend.*` works
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import numpy as np
import pandas as pd

from backend.models.linear_model import LinearForecastModel


def make_supervised_df(n_days: int = 120) -> pd.DataFrame:
    rng = pd.date_range("2024-01-01", periods=n_days, freq="D")
    base = 120 + 10 * np.sin(np.arange(n_days) / 7.0) + np.random.normal(0, 3, size=n_days)
    qty = np.maximum(base, 0).round().astype(int)

    df = pd.DataFrame({"date": rng, "quantity_sold": qty})
    df["month"] = df["date"].dt.month
    df["day_of_week"] = df["date"].dt.dayofweek
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)
    df["lag_1"] = df["quantity_sold"].shift(1)
    df["lag_7"] = df["quantity_sold"].shift(7)
    df["lag_30"] = df["quantity_sold"].shift(30)
    df["rolling_mean_7"] = df["quantity_sold"].rolling(window=7, min_periods=1).mean()
    df["rolling_std_7"] = df["quantity_sold"].rolling(window=7, min_periods=1).std().fillna(0.0)
    return df.dropna().reset_index(drop=True)


def main():
    df = make_supervised_df()
    feature_cols = [
        "month",
        "day_of_week",
        "is_weekend",
        "week_of_year",
        "lag_1",
        "lag_7",
        "lag_30",
        "rolling_mean_7",
        "rolling_std_7",
    ]

    X = df[feature_cols]
    y = df["quantity_sold"]
    split = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    print("\n== Linear ==")
    lin = LinearForecastModel()
    lin.train(X_train, y_train)
    lin.evaluate(X_test, y_test)

    try:
        from backend.models.arima_model import ARIMAForecastModel

        print("\n== ARIMA ==")
        ts = df.set_index("date")["quantity_sold"]
        arima = ARIMAForecastModel()
        arima.train(ts)
        preds = arima.predict(steps=7)
        print("Next 7 day forecast:", preds)
    except Exception as e:
        print("\n== ARIMA (skipped) ==")
        print(e)

    try:
        from backend.models.xgboost_model import XGBoostForecastModel

        print("\n== XGBoost ==")
        xgb = XGBoostForecastModel()
        xgb.train(X_train, y_train)
        xgb.evaluate(X_test, y_test)
    except Exception as e:
        print("\n== XGBoost (skipped) ==")
        print(e)

    try:
        from backend.models.lstm_model import LSTMForecastModel

        print("\n== LSTM ==")
        lstm = LSTMForecastModel(sequence_length=7)
        lstm.train(df["quantity_sold"].astype(float).values, epochs=3)
        next7 = lstm.predict_next_days(df["quantity_sold"].values[-7:], days=7)
        print("Next 7 day forecast:", next7)
    except Exception as e:
        print("\n== LSTM (skipped) ==")
        print(e)


if __name__ == "__main__":
    main()

