"""API router for SQL analytics and predictive modeling (V3)."""

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    AnalyticsSQLRequest,
    AnalyticsSQLResponse,
    PredictiveTrainRequest,
    PredictiveTrainResponse,
    PredictivePredictRequest,
    PredictivePredictResponse,
)
from app.services.analytics_service import (
    run_prediction,
    run_sql_analytics,
    train_predictive_model,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Analytics V3"])


@router.post("/analytics/sql", response_model=AnalyticsSQLResponse)
async def api_sql_analytics(req: AnalyticsSQLRequest):
    """Run a SQL query on tabular data using DuckDB.

    Accepts tabular data and a SQL query string.  The table is
    registered as ``data`` so queries should reference ``FROM data``.
    """
    try:
        result = run_sql_analytics(
            data=req.data,
            headers=req.headers,
            sql_query=req.sql_query,
        )
        return AnalyticsSQLResponse(**result)
    except Exception as e:
        logger.exception("SQL analytics endpoint gagal")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analytics/train", response_model=PredictiveTrainResponse)
async def api_train_model(req: PredictiveTrainRequest):
    """Train a predictive model (XGBoost or LightGBM).

    Returns metrics (MAE, RMSE, R²), feature importance, and
    train/test predictions.
    """
    try:
        result = train_predictive_model(
            data=req.data,
            headers=req.headers,
            target_col=req.target_col,
            feature_cols=req.feature_cols,
            model_type=req.model_type,
        )
        return PredictiveTrainResponse(**result)
    except Exception as e:
        logger.exception("Model training endpoint gagal")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analytics/predict", response_model=PredictivePredictResponse)
async def api_predict(req: PredictivePredictRequest):
    """Train a model and return predictions on the provided data.

    Trains an XGBoost or LightGBM model on the data, then returns
    predictions for every row.  Useful for quick what-if analysis.
    """
    try:
        result = run_prediction(
            data=req.data,
            headers=req.headers,
            target_col=req.target_col,
            feature_cols=req.feature_cols,
            model_type=req.model_type,
        )
        return PredictivePredictResponse(**result)
    except Exception as e:
        logger.exception("Predict endpoint gagal")
        raise HTTPException(status_code=500, detail=str(e))
