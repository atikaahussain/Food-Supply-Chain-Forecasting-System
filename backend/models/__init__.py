"""
Models package.

Do not eagerly import model implementations here: some models (ARIMA/XGBoost/LSTM)
have optional heavy dependencies. Import them directly, e.g.:

  from backend.models.linear_model import LinearForecastModel
"""

from .base_model import BaseModel

__all__ = ["BaseModel"]

