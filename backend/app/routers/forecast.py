"""API router for time series forecasting (V2)."""

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import ForecastRunRequest, ForecastRunResponse
from app.services.forecast_service import run_forecast

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Forecast V2"])


@router.post("/forecast/run", response_model=ForecastRunResponse)
async def api_run_forecast(req: ForecastRunRequest):
    """Run time series forecasting using Prophet (or linear regression fallback).

    Accepts tabular data, auto-detects date frequency, and returns
    forecasted values with confidence intervals, metrics, and seasonality.
    """
    try:
        result = run_forecast(
            data=req.data,
            headers=req.headers,
            date_col=req.date_col,
            value_col=req.value_col,
            periods=req.periods,
        )
        return ForecastRunResponse(**result)
    except Exception as e:
        logger.exception("Forecast run gagal")
        raise HTTPException(status_code=500, detail=str(e))
