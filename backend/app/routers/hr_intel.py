"""API router for HR intelligence (V3)."""

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import HRAnalysisRequest, HRAnalysisResponse
from app.services.hr_intel_service import analyze_hr

logger = logging.getLogger(__name__)

router = APIRouter(tags=["HR Intelligence V3"])


@router.post("/hr/analyze", response_model=HRAnalysisResponse)
async def api_analyze_hr(req: HRAnalysisRequest):
    """Analyze HR/employee data.

    Provides salary analysis, headcount, overtime analysis,
    attendance patterns, duplicate detection, and productivity metrics.
    """
    try:
        result = analyze_hr(
            data=req.data,
            headers=req.headers,
            sheet_name=req.sheet_name,
        )
        return HRAnalysisResponse(**result)
    except Exception as e:
        logger.exception("HR analysis gagal")
        raise HTTPException(status_code=500, detail=str(e))
