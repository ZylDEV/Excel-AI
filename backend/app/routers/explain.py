"""API router for data explanation."""

import logging

from fastapi import APIRouter, Header, HTTPException

from app.models.schemas import ExplainDataRequest, ExplainDataResponse
from app.services.explain_service import explain_data

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Explain"])


@router.post("/explain/data", response_model=ExplainDataResponse)
async def api_explain_data(
    req: ExplainDataRequest,
    x_api_key: str = Header(None, alias="X-API-Key"),
    x_llm_provider: str = Header(None, alias="X-LLM-Provider"),
):
    """Generate insights, statistics, and a natural-language explanation of the provided data."""
    try:
        result = explain_data(
            data=req.data,
            headers=req.headers,
            sheet_name=req.sheet_name,
            api_key=x_api_key,
            provider=x_llm_provider,
        )
        return ExplainDataResponse(**result)
    except Exception as e:
        logger.exception("Data explanation failed")
        raise HTTPException(status_code=500, detail=str(e))
