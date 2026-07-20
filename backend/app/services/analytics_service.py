"""Service layer for DuckDB SQL analytics and predictive modeling."""

import logging
from typing import Any

from core.analysis.duckdb_analytics import DuckDBAnalytics
from core.ml.predictive import PredictiveModel
from core.utils.excel_reader import read_range

logger = logging.getLogger(__name__)


def run_sql_analytics(
    data: list[list],
    headers: list[str],
    sql_query: str,
) -> dict[str, Any]:
    """Run a SQL query on the provided data using DuckDB.

    Parameters
    ----------
    data : list[list]
        2-D array of cell values.
    headers : list[str]
        Column header names.
    sql_query : str
        SQL query to run. Use ``data`` as the table name.

    Returns
    -------
    dict with keys: columns, rows, row_count, error (optional).
    """
    try:
        df = read_range(data=[headers] + data, headers=True)
        if df.empty:
            return {
                "columns": [],
                "rows": [],
                "row_count": 0,
                "error": "Data kosong — tidak dapat menjalankan query.",
            }

        result_df = DuckDBAnalytics.query(df, sql_query)

        columns = list(result_df.columns)
        rows = [
            [DuckDBAnalytics._to_native(v) for v in row]
            for row in result_df.itertuples(index=False)
        ]

        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
        }

    except Exception as exc:
        logger.exception("SQL analytics service gagal")
        return {
            "columns": [],
            "rows": [],
            "row_count": 0,
            "error": str(exc),
        }


def train_predictive_model(
    data: list[list],
    headers: list[str],
    target_col: str,
    feature_cols: list[str] | None = None,
    model_type: str = "xgboost",
) -> dict[str, Any]:
    """Train a predictive model (XGBoost/LightGBM) on the provided data.

    Parameters
    ----------
    data : list[list]
        2-D array of cell values.
    headers : list[str]
        Column header names.
    target_col : str
        Name of the target column.
    feature_cols : list[str] | None
        Feature column names. If None, all numeric columns are used.
    model_type : str
        ``"xgboost"`` or ``"lightgbm"``.

    Returns
    -------
    dict with keys: metrics, feature_importance, predictions, model_type, summary.
    """
    try:
        df = read_range(data=[headers] + data, headers=True)
        if df.empty:
            return {
                "metrics": {"mae": 0.0, "rmse": 0.0, "r2": 0.0},
                "feature_importance": [],
                "predictions": [],
                "model_type": model_type,
                "summary": "Data kosong — tidak dapat melatih model.",
            }

        model = PredictiveModel()
        result = model.train(
            df=df,
            target_col=target_col,
            feature_cols=feature_cols,
            model_type=model_type,
        )

        # Convert numpy values to native types
        result = PredictiveModel._to_native(result)
        return result

    except Exception as exc:
        logger.exception("Predictive model training service gagal")
        return {
            "metrics": {"mae": 0.0, "rmse": 0.0, "r2": 0.0},
            "feature_importance": [],
            "predictions": [],
            "model_type": model_type,
            "summary": f"Training gagal: {exc}",
        }


def run_prediction(
    data: list[list],
    headers: list[str],
    target_col: str,
    feature_cols: list[str] | None = None,
    model_type: str = "xgboost",
) -> dict[str, Any]:
    """Train a model and return predictions on the same data.

    This is a convenience endpoint that trains and predicts in one call.
    For production use, consider separating train and predict with
    model persistence (future feature).

    Parameters
    ----------
    data : list[list]
        2-D array of cell values.
    headers : list[str]
        Column header names.
    target_col : str
        Name of the target column.
    feature_cols : list[str] | None
        Feature column names.
    model_type : str
        ``"xgboost"`` or ``"lightgbm"``.

    Returns
    -------
    dict with keys: metrics, feature_importance, predictions, model_type, summary.
    """
    try:
        df = read_range(data=[headers] + data, headers=True)
        if df.empty:
            return {
                "metrics": {"mae": 0.0, "rmse": 0.0, "r2": 0.0},
                "feature_importance": [],
                "predictions": [],
                "model_type": model_type,
                "summary": "Data kosong — tidak dapat melakukan prediksi.",
            }

        model = PredictiveModel()
        train_result = model.train(
            df=df,
            target_col=target_col,
            feature_cols=feature_cols,
            model_type=model_type,
        )

        # If training succeeded, run predictions
        if model._is_fitted:
            try:
                preds = model.predict(df)
                train_result["predictions"] = preds
            except Exception as pred_exc:
                logger.warning("Prediksi gagal setelah training: %s", pred_exc)
                train_result["predictions"] = []

        return PredictiveModel._to_native(train_result)

    except Exception as exc:
        logger.exception("Predictive model prediction service gagal")
        return {
            "metrics": {"mae": 0.0, "rmse": 0.0, "r2": 0.0},
            "feature_importance": [],
            "predictions": [],
            "model_type": model_type,
            "summary": f"Prediksi gagal: {exc}",
        }
