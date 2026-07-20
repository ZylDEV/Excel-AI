"""Predictive modeling using XGBoost or LightGBM."""

import logging
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder

logger = logging.getLogger(__name__)

# Attempt to import XGBoost
try:
    import xgboost as xgb

    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.info("XGBoost tidak tersedia")

# Attempt to import LightGBM
try:
    import lightgbm as lgb

    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    logger.info("LightGBM tidak tersedia")


class PredictiveModel:
    """Train and use XGBoost or LightGBM models for prediction.

    Both model types are supported.  The class handles small datasets
    gracefully by falling back to simpler approaches when needed.
    """

    def __init__(self):
        self._model = None
        self._model_type: str | None = None
        self._feature_cols: list[str] = []
        self._target_col: str | None = None
        self._label_encoders: dict[str, LabelEncoder] = {}
        self._is_fitted: bool = False

    @staticmethod
    def _to_native(obj: Any) -> Any:
        """Recursively convert numpy/pandas types to native Python types."""
        if isinstance(obj, dict):
            return {k: PredictiveModel._to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [PredictiveModel._to_native(v) for v in obj]
        elif isinstance(obj, tuple):
            return tuple(PredictiveModel._to_native(v) for v in obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return PredictiveModel._to_native(obj.tolist())
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif hasattr(obj, "isoformat"):
            return obj.isoformat()
        try:
            if isinstance(obj, float) and (pd.isna(obj) or np.isnan(obj)):
                return None
        except Exception:
            pass
        return obj

    def _prepare_features(
        self, df: pd.DataFrame, feature_cols: list[str] | None
    ) -> tuple[pd.DataFrame, list[str]]:
        """Prepare feature matrix: encode categoricals, drop missing.

        Returns
        -------
        (X, used_columns)
        """
        if feature_cols:
            cols = [c for c in feature_cols if c in df.columns]
        else:
            cols = [
                c
                for c in df.columns
                if c != self._target_col and pd.api.types.is_numeric_dtype(df[c])
            ]

        if not cols:
            raise ValueError(
                "Tidak ada kolom fitur yang valid ditemukan. "
                "Pastikan setidaknya ada satu kolom numerik."
            )

        X = df[cols].copy()

        # Encode categorical columns
        for col in X.columns:
            if not pd.api.types.is_numeric_dtype(X[col]):
                le = LabelEncoder()
                X[col] = X[col].astype(str).fillna("NaN")
                X[col] = le.fit_transform(X[col])
                self._label_encoders[col] = le

        # Drop rows with NaN
        X = X.dropna()
        return X, cols

    def train(
        self,
        df: pd.DataFrame,
        target_col: str,
        feature_cols: list[str] | None = None,
        model_type: str = "xgboost",
    ) -> dict:
        """Train a regression model and return metrics, importance, and predictions.

        Parameters
        ----------
        df : pd.DataFrame
            Source data.
        target_col : str
            Name of the target column to predict.
        feature_cols : list[str] | None
            Feature column names. If None, all numeric columns (except target) are used.
        model_type : str
            ``"xgboost"`` or ``"lightgbm"``.

        Returns
        -------
        dict with keys:
            - metrics: {mae, rmse, r2}
            - feature_importance: [{feature, importance}]
            - predictions: [{actual, predicted}]
            - model_type: str
            - summary: str (Indonesian)
        """
        self._target_col = target_col
        self._model_type = model_type.lower()

        if target_col not in df.columns:
            return {
                "metrics": {"mae": 0.0, "rmse": 0.0, "r2": 0.0},
                "feature_importance": [],
                "predictions": [],
                "model_type": self._model_type,
                "summary": f"Kolom target '{target_col}' tidak ditemukan dalam data.",
            }

        try:
            # Prepare features
            X, used_cols = self._prepare_features(df, feature_cols)
            self._feature_cols = used_cols

            # Prepare target
            y = df.loc[X.index, target_col]
            y = pd.to_numeric(y, errors="coerce")
            mask = y.notna()
            X = X.loc[mask]
            y = y.loc[mask]

            if len(X) < 3:
                return {
                    "metrics": {"mae": 0.0, "rmse": 0.0, "r2": 0.0},
                    "feature_importance": [],
                    "predictions": [],
                    "model_type": self._model_type,
                    "summary": "Data terlalu sedikit (minimal 3 baris diperlukan untuk training).",
                }

            # Split
            test_size = 0.3 if len(X) >= 10 else 0.2
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )

            # Train model
            if self._model_type == "lightgbm" and LIGHTGBM_AVAILABLE:
                self._model = lgb.LGBMRegressor(
                    n_estimators=100,
                    learning_rate=0.1,
                    max_depth=6,
                    random_state=42,
                    verbose=-1,
                )
                self._model.fit(X_train, y_train)
            elif self._model_type == "xgboost" and XGBOOST_AVAILABLE:
                self._model = xgb.XGBRegressor(
                    n_estimators=100,
                    learning_rate=0.1,
                    max_depth=6,
                    random_state=42,
                    verbosity=0,
                )
                self._model.fit(X_train, y_train)
            else:
                # Fallback: use sklearn LinearRegression
                from sklearn.linear_model import LinearRegression

                logger.info(
                    "%s tidak tersedia, menggunakan LinearRegression sebagai fallback",
                    self._model_type,
                )
                self._model = LinearRegression()
                self._model.fit(X_train, y_train)
                self._model_type = "linear_regression"

            self._is_fitted = True

            # Predict
            y_pred = self._model.predict(X_test)

            # Metrics
            mae = float(mean_absolute_error(y_test, y_pred))
            rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
            r2 = float(r2_score(y_test, y_pred))

            metrics = {
                "mae": round(mae, 4),
                "rmse": round(rmse, 4),
                "r2": round(r2, 4),
            }

            # Feature importance
            importance_list = self._get_importance(used_cols)

            # Predictions list
            predictions = [
                {"actual": self._to_native(a), "predicted": self._to_native(p)}
                for a, p in zip(y_test.values, y_pred)
            ]

            # Summary (Indonesian)
            model_label = {
                "xgboost": "XGBoost",
                "lightgbm": "LightGBM",
                "linear_regression": "Linear Regression (fallback)",
            }.get(self._model_type, self._model_type)

            summary = (
                f"Model {model_label} berhasil dilatih dengan {len(used_cols)} fitur "
                f"({len(X_train)} train, {len(X_test)} test). "
                f"R² = {r2:.3f}, MAE = {mae:.3f}, RMSE = {rmse:.3f}."
            )

            return {
                "metrics": metrics,
                "feature_importance": importance_list,
                "predictions": predictions,
                "model_type": self._model_type,
                "summary": summary,
            }

        except Exception as exc:
            logger.exception("PredictiveModel.train gagal")
            return {
                "metrics": {"mae": 0.0, "rmse": 0.0, "r2": 0.0},
                "feature_importance": [],
                "predictions": [],
                "model_type": self._model_type or model_type,
                "summary": f"Training gagal: {exc}",
            }

    def _get_importance(self, used_cols: list[str]) -> list[dict]:
        """Extract feature importance from the trained model."""
        try:
            if hasattr(self._model, "feature_importances_"):
                importances = self._model.feature_importances_
                if importances is not None and len(importances) == len(used_cols):
                    total = importances.sum()
                    if total > 0:
                        norm = (importances / total * 100).tolist()
                    else:
                        norm = [0.0] * len(used_cols)
                    return [
                        {"feature": col, "importance": round(float(v), 2)}
                        for col, v in sorted(
                            zip(used_cols, norm), key=lambda x: x[1], reverse=True
                        )
                    ]
            elif hasattr(self._model, "coef_"):
                coefs = self._model.coef_
                if coefs is not None and len(coefs) == len(used_cols):
                    abs_coefs = np.abs(coefs)
                    total = abs_coefs.sum()
                    if total > 0:
                        norm = (abs_coefs / total * 100).tolist()
                    else:
                        norm = [0.0] * len(used_cols)
                    return [
                        {"feature": col, "importance": round(float(v), 2)}
                        for col, v in sorted(
                            zip(used_cols, norm), key=lambda x: x[1], reverse=True
                        )
                    ]
        except Exception as exc:
            logger.debug("Ekstraksi feature importance gagal: %s", exc)
        return [{"feature": col, "importance": 0.0} for col in used_cols]

    def predict(self, df: pd.DataFrame) -> list[float]:
        """Make predictions on new data using the trained model.

        Parameters
        ----------
        df : pd.DataFrame
            New data with the same feature columns used during training.

        Returns
        -------
        list[float] of predicted values.
        """
        if not self._is_fitted or self._model is None:
            raise RuntimeError(
                "Model belum dilatih. Panggil .train() terlebih dahulu."
            )

        try:
            X = df[self._feature_cols].copy()

            # Encode categoricals using the same encoders
            for col in X.columns:
                if col in self._label_encoders:
                    le = self._label_encoders[col]
                    X[col] = X[col].astype(str).fillna("NaN")
                    # Handle unseen labels
                    seen = set(le.classes_)
                    X[col] = X[col].map(
                        lambda v: le.transform([v])[0] if v in seen else -1
                    )
                elif not pd.api.types.is_numeric_dtype(X[col]):
                    X[col] = pd.to_numeric(X[col], errors="coerce")

            X = X.fillna(0)
            preds = self._model.predict(X)
            return [round(float(v), 4) for v in preds]

        except Exception as exc:
            logger.exception("PredictiveModel.predict gagal")
            raise RuntimeError(f"Prediksi gagal: {exc}")
