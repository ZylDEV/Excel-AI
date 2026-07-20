"""Service for time series forecasting."""

import logging
from typing import Any

import pandas as pd

from core.analysis.forecast import TimeSeriesForecaster
from core.utils.excel_reader import read_range

logger = logging.getLogger(__name__)


def run_forecast(
    data: list[list],
    headers: list[str],
    date_col: str,
    value_col: str,
    periods: int = 12,
) -> dict[str, Any]:
    """Run time series forecasting on the provided data.

    Parameters
    ----------
    data : list[list]
        2-D array of cell values.
    headers : list[str]
        Column header names.
    date_col : str
        Name of the date column.
    value_col : str
        Name of the numeric value column to forecast.
    periods : int
        Number of future periods to forecast (default 12).

    Returns
    -------
    dict with keys: forecast, history, metrics, seasonality.
    """
    try:
        df = read_range(data=[headers] + data, headers=True)
        if df.empty:
            return {
                "forecast": [],
                "history": [],
                "metrics": {"mae": 0.0, "rmse": 0.0, "mape": 0.0},
                "seasonality": {"trend": None, "yearly": None, "weekly": None, "daily": None},
                "error": "Data kosong",
            }

        result = TimeSeriesForecaster.forecast(
            df=df,
            date_col=date_col,
            value_col=value_col,
            periods=periods,
        )
        return result

    except Exception as e:
        logger.exception("Forecast service gagal")
        return {
            "forecast": [],
            "history": [],
            "metrics": {"mae": 0.0, "rmse": 0.0, "mape": 0.0},
            "seasonality": {"trend": None, "yearly": None, "weekly": None, "daily": None},
            "error": str(e),
        }
