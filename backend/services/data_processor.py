from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd


@dataclass
class DataProcessor:
    df: Optional[pd.DataFrame] = None

    def load_data(self, file_path: str, limit: Optional[int] = None) -> pd.DataFrame:
        """Load CSV or Excel file. Optionally limit rows for quick testing."""
        if file_path.endswith(".csv"):
            self.df = pd.read_csv(file_path)
        elif file_path.endswith((".xlsx", ".xls")):
            self.df = pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file format")

        if limit is not None:
            self.df = self.df.head(int(limit)).copy()

        return self.df

    def clean_data(self) -> pd.DataFrame:
        if self.df is None:
            raise RuntimeError("No data loaded. Call load_data() first.")

        initial_rows = len(self.df)

        # Remove duplicates
        self.df = self.df.drop_duplicates()

        # Handle missing values
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if self.df[col].isnull().any():
                self.df[col] = self.df[col].fillna(self.df[col].median())

        categorical_cols = self.df.select_dtypes(include=["object"]).columns
        for col in categorical_cols:
            if col != "date" and self.df[col].isnull().any():
                self.df[col] = self.df[col].fillna(self.df[col].mode().iloc[0])

        # Normalize date column if present
        if "date" in self.df.columns:
            self.df["date"] = pd.to_datetime(self.df["date"], errors="coerce")
            self.df = self.df.dropna(subset=["date"])

        # Remove outliers (3-sigma) for numeric columns (skip obvious identifiers)
        id_like = {"id", "outlet_id", "item_id", "center_id", "meal_id", "week"}
        for col in numeric_cols:
            if col in id_like:
                continue
            series = self.df[col]
            std = float(series.std())
            if std == 0 or np.isnan(std):
                continue
            mean = float(series.mean())
            mask = (series < mean - 3 * std) | (series > mean + 3 * std)
            if mask.any():
                self.df = self.df.loc[~mask].copy()

        _ = initial_rows  # keep for possible future logging without printing in server context
        return self.df

    def feature_engineering(self) -> pd.DataFrame:
        if self.df is None:
            raise RuntimeError("No data loaded. Call load_data() first.")

        # Discount features
        if {"base_price", "checkout_price"}.issubset(self.df.columns):
            self.df["discount_amount"] = self.df["base_price"] - self.df["checkout_price"]
            base = self.df["base_price"].replace(0, np.nan)
            self.df["discount_percent"] = (self.df["discount_amount"] / base) * 100

        # Rolling 4-week mean of orders per (center_id, meal_id)
        if {"num_orders", "week", "center_id", "meal_id"}.issubset(self.df.columns):
            self.df = self.df.sort_values(["center_id", "meal_id", "week"])
            self.df["rolling_orders_4wk"] = (
                self.df.groupby(["center_id", "meal_id"])["num_orders"]
                .transform(lambda x: x.rolling(window=4, min_periods=1).mean())
            )

        return self.df

    def save_processed_data(self, output_path: str) -> None:
        if self.df is None:
            raise RuntimeError("No data loaded. Call load_data() first.")
        self.df.to_csv(output_path, index=False)

