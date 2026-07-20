"""API router for sales intelligence (V3)."""

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import SalesAnalysisRequest, SalesAnalysisResponse
from app.services.sales_intel_service import analyze_sales

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Sales Intelligence V3"])


@router.post("/sales/analyze", response_model=SalesAnalysisResponse)
async def api_analyze_sales(req: SalesAnalysisRequest):
    """Analyze sales data for business intelligence.

    Identifies top customers, customer segments, sales trends,
    product performance, regional analysis, and cross-selling opportunities.
    """
    try:
        result = analyze_sales(
            data=req.data,
            headers=req.headers,
            sheet_name=req.sheet_name,
        )
        return SalesAnalysisResponse(**result)
    except Exception as e:
        logger.exception("Sales analysis gagal")
        raise HTTPException(status_code=500, detail=str(e))
