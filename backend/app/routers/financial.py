"""API router for financial health analysis (V3)."""

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import FinancialHealthRequest, FinancialHealthResponse
from app.services.financial_service import analyze_financial_health

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Financial Health V3"])


@router.post("/financial/analyze", response_model=FinancialHealthResponse)
async def api_analyze_financial_health(req: FinancialHealthRequest):
    """Analyze financial health from P&L / balance sheet data.

    Auto-detects columns and calculates profitability ratios,
    liquidity ratios, efficiency ratios, and growth metrics.
    """
    try:
        result = analyze_financial_health(
            data=req.data,
            headers=req.headers,
            sheet_name=req.sheet_name,
        )
        return FinancialHealthResponse(**result)
    except Exception as e:
        logger.exception("Financial health analysis gagal")
        raise HTTPException(status_code=500, detail=str(e))
