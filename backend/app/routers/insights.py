"""API router for business insights (V2)."""

import logging

from fastapi import APIRouter, Header, HTTPException

from app.models.schemas import InsightsGenerateRequest, InsightsGenerateResponse
from app.services.insight_service import generate_insights

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Insights V2"])


@router.post("/insights/generate", response_model=InsightsGenerateResponse)
async def api_generate_insights(
    req: InsightsGenerateRequest,
    x_api_key: str = Header(None, alias="X-API-Key"),
    x_llm_provider: str = Header(None, alias="X-LLM-Provider"),
):
    """Generate business intelligence insights from spreadsheet data.

    Detects trends, anomalies, correlations, and top performers.
    If an X-API-Key header is provided, the summary will be enhanced
    using an LLM.
    """
    try:
        result = generate_insights(
            data=req.data,
            headers=req.headers,
            sheet_name=req.sheet_name,
            api_key=x_api_key,
            provider=x_llm_provider,
        )
        return InsightsGenerateResponse(**result)
    except Exception as e:
        logger.exception("Insights generation gagal")
        raise HTTPException(status_code=500, detail=str(e))
