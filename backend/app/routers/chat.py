"""API router for chat-based data Q&A."""

import logging

from fastapi import APIRouter, Header, HTTPException

from app.models.schemas import ChatMessageRequest, ChatMessageResponse
from app.services.chat_service import process_chat_message

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])


@router.post("/chat/message", response_model=ChatMessageResponse)
async def api_chat_message(
    req: ChatMessageRequest,
    x_api_key: str = Header(None, alias="X-API-Key"),
):
    """Send a chat message about the workbook data and get an AI-powered reply."""
    try:
        # Convert SheetContext models to plain dicts for the service
        context = None
        if req.workbook_context:
            context = [s.model_dump() for s in req.workbook_context]

        result = process_chat_message(
            message=req.message,
            workbook_context=context,
            api_key=x_api_key,
        )
        return ChatMessageResponse(**result)
    except Exception as e:
        logger.exception("Chat processing failed")
        raise HTTPException(status_code=500, detail=str(e))
