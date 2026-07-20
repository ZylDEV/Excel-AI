"""Time series forecasting using Prophet with scikit-learn fallback."""

import logging
import warnings
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class TimeSeriesForecaster:
    """Forecast time series data using Prophet (or linear regression fallback).

    Auto-detects date column frequency (monthly, daily, weekly) and fits a
    Prophet model.  If the data is too short for Prophet (< 2 periods),
    falls back to linear regression.
    """

    @staticmethod
    def _to_native(obj: Any) -> Any:
        """Recursively convert numpy types to native Python types."""
        if isinstance(obj, dict):
            return {k: TimeSeriesForecaster._to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [TimeSeriesForecaster._to_native(v) for v in obj]
        elif isinstance(obj, tuple):
            return tuple(TimeSeriesForecaster._to_native(v) for v in obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return TimeSeriesForecaster._to_native(obj.tolist())
        elif pd.isna(obj):
            return None
        return obj

    @staticmethod
    def _detect_frequency(dates: pd.Series) -> str:
        """Auto-detect the frequency of a date series.

        Returns one of ``"D"``, ``"W"``, ``"M"``, or ``"D"`` (default).
        """
        if len(dates) < 2:
            return "D"

        diffs = pd.Series(dates).sort_values().diff().dropna()
        if diffs.empty:
            return "D"

        median_diff = diffs.median()
        # Approximate using pd.Timedelta
        if median_diff <= pd.Timedelta(days=2):
            return "D"
        elif median_diff <= pd.Timedelta(days=10):
            return "W"
        else:
            return "M"

    @staticmethod
    def _calc_metrics(actual: pd.Series | np.ndarray, predicted: pd.Series | np.ndarray) -> dict[str, float]:
        """Calculate MAE, RMSE, and MAPE."""
        if isinstance(actual, np.ndarray):
            actual = pd.Series(actual)
        if isinstance(predicted, np.ndarray):
            predicted = pd.Series(predicted)
        mask = actual.notna() & predicted.notna()
        actual = actual[mask]
        predicted = predicted[mask]

        if len(actual) == 0:
            return {"mae": 0.0, "rmse": 0.0, "mape": 0.0}

        mae = float(np.mean(np.abs(actual - predicted)))
        rmse = float(np.sqrt(np.mean((actual - predicted) ** 2)))
        # MAPE: avoid division by zero
        non_zero = actual.abs() > 1e-9
        if non_zero.sum() > 0:
            mape = float(np.mean(np.abs((actual[non_zero] - predicted[non_zero]) / actual[non_zero]))) * 100
        else:
            mape = 0.0

        return {"mae": round(mae, 4), "rmse": round(rmse, 4), "mape": round(mape, 4)}

    @classmethod
    def forecast(
        cls,
        df: pd.DataFrame,
        date_col: str,
        value_col: str,
        periods: int = 12,
    ) -> dict[str, Any]:
        """Run time series forecasting.

        Parameters
        ----------
        df : pd.DataFrame
            Source data.
        date_col : str
            Name of the date column.
        value_col : str
            Name of the numeric value column to forecast.
        periods : int
            Number of future periods to forecast (default 12).

        Returns
        -------
        dict with keys:
            - forecast : list[dict]  — future predictions
            - history : list[dict]   — historical actuals
            - metrics : dict         — MAE, RMSE, MAPE
            - seasonality : dict    — trend / yearly / weekly / daily components
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            warnings.simplefilter("ignore", UserWarning)

            try:
                # ── Prepare data ──────────────────────────────────────
                if date_col not in df.columns or value_col not in df.columns:
                    raise ValueError(
                        f"Kolom '{date_col}' atau '{value_col}' tidak ditemukan dalam data. "
                        f"Kolom tersedia: {list(df.columns)}"
                    )

                ts = df[[date_col, value_col]].copy()
                ts[date_col] = pd.to_datetime(ts[date_col], errors="coerce")
                ts[value_col] = pd.to_numeric(ts[value_col], errors="coerce")
                ts = ts.dropna(subset=[date_col, value_col]).sort_values(date_col)
                ts = ts.drop_duplicates(subset=[date_col]).reset_index(drop=True)

                if ts.empty:
                    return {
                        "forecast": [],
                        "history": [],
                        "metrics": {"mae": 0.0, "rmse": 0.0, "mape": 0.0},
                        "seasonality": {"trend": None, "yearly": None, "weekly": None, "daily": None},
                        "error": "Data kosong setelah pembersihan",
                    }

                freq = cls._detect_frequency(ts[date_col])
                min_periods = 2 if freq == "M" else (4 if freq == "W" else 14)

                if len(ts) < min_periods:
                    # Fallback: linear regression
                    return cls._linear_regression_forecast(ts, date_col, value_col, periods)

                # ── Fit Prophet ───────────────────────────────────────
                from prophet import Prophet

                prophet_df = ts.rename(columns={date_col: "ds", value_col: "y"})

                model = Prophet(
                    yearly_seasonality="auto",
                    weekly_seasonality="auto",
                    daily_seasonality=False,
                    seasonality_mode="multiplicative",
                    changepoint_prior_scale=0.05,
                )
                model.fit(prophet_df)

                # ── Forecast ──────────────────────────────────────────
                future = model.make_future_dataframe(periods=periods, freq=freq)
                forecast_result = model.predict(future)

                # Extract history
                history = []
                for _, row in prophet_df.iterrows():
                    history.append({
                        "ds": cls._to_native(row["ds"]),
                        "y": cls._to_native(row["y"]),
                    })

                # Extract forecast
                fc = forecast_result[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(periods)
                forecast_list = []
                for _, row in fc.iterrows():
                    forecast_list.append({
                        "ds": cls._to_native(row["ds"]),
                        "yhat": cls._to_native(row["yhat"]),
                        "yhat_lower": cls._to_native(row["yhat_lower"]),
                        "yhat_upper": cls._to_native(row["yhat_upper"]),
                    })

                # ── Metrics ───────────────────────────────────────────
                fitted = forecast_result.iloc[: len(prophet_df)]
                metrics = cls._calc_metrics(
                    prophet_df["y"].values,
                    fitted["yhat"].values,
                )

                # ── Seasonality ──────────────────────────────────────
                seasonality = {
                    "trend": cls._to_native(forecast_result[["ds", "trend"]].tail(periods).to_dict(orient="records")),
                    "yearly": None,
                    "weekly": None,
                    "daily": None,
                }

                # Check which seasonalities are present
                if "yearly" in forecast_result.columns:
                    seasonality["yearly"] = cls._to_native(
                        forecast_result[["ds", "yearly"]].dropna().to_dict(orient="records")
                    )
                if "weekly" in forecast_result.columns:
                    seasonality["weekly"] = cls._to_native(
                        forecast_result[["ds", "weekly"]].dropna().to_dict(orient="records")
                    )
                if "daily" in forecast_result.columns:
                    seasonality["daily"] = cls._to_native(
                        forecast_result[["ds", "daily"]].dropna().to_dict(orient="records")
                    )

                return {
                    "forecast": forecast_list,
                    "history": history,
                    "metrics": metrics,
                    "seasonality": cls._to_native(seasonality),
                }

            except Exception as e:
                logger.exception("Prophet forecasting gagal, mencoba fallback linear regression")
                # Try linear regression as a last resort
                try:
                    ts = df[[date_col, value_col]].copy()
                    ts[date_col] = pd.to_datetime(ts[date_col], errors="coerce")
                    ts[value_col] = pd.to_numeric(ts[value_col], errors="coerce")
                    ts = ts.dropna(subset=[date_col, value_col]).sort_values(date_col)
                    return cls._linear_regression_forecast(ts, date_col, value_col, periods)
                except Exception as fallback_err:
                    return {
                        "forecast": [],
                        "history": [],
                        "metrics": {"mae": 0.0, "rmse": 0.0, "mape": 0.0},
                        "seasonality": {"trend": None, "yearly": None, "weekly": None, "daily": None},
                        "error": f"Forecasting gagal: {e}. Fallback juga gagal: {fallback_err}",
                    }

    @classmethod
    def _linear_regression_forecast(
        cls,
        ts: pd.DataFrame,
        date_col: str,
        value_col: str,
        periods: int,
    ) -> dict[str, Any]:
        """Fallback forecast using simple linear regression on time index."""
        from sklearn.linear_model import LinearRegression

        ts = ts.reset_index(drop=True)
        # Use integer index as the predictor
        X = np.arange(len(ts)).reshape(-1, 1)
        y = ts[value_col].values.astype(float)

        model = LinearRegression()
        model.fit(X, y)

        # In-sample predictions for metrics
        y_pred = model.predict(X)
        metrics = cls._calc_metrics(pd.Series(y), pd.Series(y_pred))

        # Future predictions
        future_idx = np.arange(len(ts), len(ts) + periods).reshape(-1, 1)
        future_pred = model.predict(future_idx)

        # Infer frequency for date generation
        if len(ts) >= 2:
            date_diffs = ts[date_col].diff().dropna()
            freq_mode = date_diffs.mode()
            step = freq_mode.iloc[0] if not freq_mode.empty else pd.Timedelta(days=30)
        else:
            step = pd.Timedelta(days=30)

        last_date = ts[date_col].iloc[-1]
        future_dates = [last_date + step * (i + 1) for i in range(periods)]

        # Build forecast
        forecast_list = []
        for i, d in enumerate(future_dates):
            forecast_list.append({
                "ds": cls._to_native(d),
                "yhat": cls._to_native(future_pred[i]),
                "yhat_lower": cls._to_native(future_pred[i] * 0.9),
                "yhat_upper": cls._to_native(future_pred[i] * 1.1),
            })

        history = []
        for _, row in ts.iterrows():
            history.append({
                "ds": cls._to_native(row[date_col]),
                "y": cls._to_native(row[value_col]),
            })

        return {
            "forecast": forecast_list,
            "history": history,
            "metrics": cls._to_native(metrics),
            "seasonality": {
                "trend": [{"ds": cls._to_native(d), "trend": cls._to_native(v)}
                          for d, v in zip(future_dates, future_pred)],
                "yearly": None,
                "weekly": None,
                "daily": None,
            },
        }
