"""API router for dashboard generation (V2)."""

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import DashboardGenerateRequest, DashboardGenerateResponse
from app.services.dashboard_service import generate_dashboard

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Dashboard V2"])


@router.post("/dashboard/generate", response_model=DashboardGenerateResponse)
async def api_generate_dashboard(req: DashboardGenerateRequest):
    """Generate dashboard configuration (KPIs, charts, insights) from spreadsheet data.

    Accepts raw data (2-D array) and headers, and auto-detects column types
    to build KPI cards, chart configurations, and key insights.
    """
    try:
        result = generate_dashboard(
            data=req.data,
            headers=req.headers,
            sheet_name=req.sheet_name,
        )
        return DashboardGenerateResponse(**result)
    except Exception as e:
        logger.exception("Dashboard generation gagal")
        raise HTTPException(status_code=500, detail=str(e))
