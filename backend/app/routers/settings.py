"""API router for BYOK settings (key validation, provider config)."""

import logging

from fastapi import APIRouter
from pydantic import BaseModel

from core.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Settings"])


class ValidateKeyRequest(BaseModel):
    api_key: str
    provider: str = "openai"


class ValidateKeyResponse(BaseModel):
    valid: bool
    message: str


@router.post("/settings/validate-key", response_model=ValidateKeyResponse)
async def validate_api_key(req: ValidateKeyRequest):
    """Test if an API key works by making a small LLM call."""
    try:
        client = LLMClient(api_key=req.api_key, provider=req.provider)
        response = client.generate(
            prompt="Say 'OK' and nothing else.",
            system_prompt="You are a test assistant.",
        )
        return ValidateKeyResponse(valid=True, message=response)
    except Exception as e:
        logger.warning(f"API key validation failed: {e}")
        return ValidateKeyResponse(valid=False, message=str(e))
