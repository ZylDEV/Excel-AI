"""API router for risk scoring (V3)."""

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import RiskScoreRequest, RiskScoreResponse
from app.services.risk_service import calculate_risk

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Risk Scoring V3"])


@router.post("/risk/score", response_model=RiskScoreResponse)
async def api_calculate_risk(req: RiskScoreRequest):
    """Calculate multi-factor risk scores from spreadsheet data.

    Evaluates volatility risk, concentration risk, trend risk,
    and missing data risk.
    """
    try:
        result = calculate_risk(
            data=req.data,
            headers=req.headers,
            sheet_name=req.sheet_name,
        )
        return RiskScoreResponse(**result)
    except Exception as e:
        logger.exception("Risk scoring gagal")
        raise HTTPException(status_code=500, detail=str(e))
