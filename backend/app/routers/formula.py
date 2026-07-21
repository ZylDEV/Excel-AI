"""API router for Excel formula generation and explanation."""

import logging

from fastapi import APIRouter, Header, HTTPException

from app.models.schemas import (
    FormulaExplainRequest,
    FormulaGenerateRequest,
    FormulaResponse,
)
from app.services.formula_service import explain_formula, generate_formula

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Formula"])


@router.post("/formula/generate", response_model=FormulaResponse)
async def api_generate_formula(
    req: FormulaGenerateRequest,
    x_api_key: str = Header(None, alias="X-API-Key"),
    x_llm_provider: str = Header(None, alias="X-LLM-Provider"),
):
    """Generate an Excel formula from a natural-language description."""
    try:
        result = generate_formula(
            description=req.description,
            sheet_context=req.sheet_context,
            api_key=x_api_key,
            provider=x_llm_provider,
        )
        return FormulaResponse(**result)
    except Exception as e:
        logger.exception("Formula generation failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/formula/explain", response_model=FormulaResponse)
async def api_explain_formula(
    req: FormulaExplainRequest,
    x_api_key: str = Header(None, alias="X-API-Key"),
    x_llm_provider: str = Header(None, alias="X-LLM-Provider"),
):
    """Explain an Excel formula in plain English."""
    try:
        result = explain_formula(
            formula=req.formula,
            api_key=x_api_key,
            provider=x_llm_provider,
        )
        return FormulaResponse(**result)
    except Exception as e:
        logger.exception("Formula explanation failed")
        raise HTTPException(status_code=500, detail=str(e))
