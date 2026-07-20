"""API router for data quality analysis and cleaning."""

import logging

from fastapi import APIRouter, Header, HTTPException

from app.models.schemas import (
    CleanerAnalyzeRequest,
    CleanerAnalyzeResponse,
    CleanerApplyRequest,
    CleanerApplyResponse,
)
from app.services.cleaner_service import analyze_quality, apply_cleaning

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Cleaner"])


@router.post("/cleaner/analyze", response_model=CleanerAnalyzeResponse)
async def api_analyze_quality(
    req: CleanerAnalyzeRequest,
    x_api_key: str = Header(None, alias="X-API-Key"),
):
    """Analyse data quality and return a list of issues found."""
    try:
        result = analyze_quality(
            data=req.data,
            headers=req.headers,
            api_key=x_api_key,
        )
        return CleanerAnalyzeResponse(**result)
    except Exception as e:
        logger.exception("Quality analysis failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleaner/apply", response_model=CleanerApplyResponse)
async def api_apply_cleaning(
    req: CleanerApplyRequest,
    x_api_key: str = Header(None, alias="X-API-Key"),
):
    """Apply cleaning fixes to the data."""
    try:
        result = apply_cleaning(
            data=req.data,
            headers=req.headers,
            fixes=req.fixes,
            api_key=x_api_key,
        )
        return CleanerApplyResponse(**result)
    except Exception as e:
        logger.exception("Cleaning apply failed")
        raise HTTPException(status_code=500, detail=str(e))
