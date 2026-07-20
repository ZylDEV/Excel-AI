"""API router for database storage operations (V3)."""

import logging

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import (
    DBSaveRequest,
    DBSaveResponse,
    DBHistoryResponse,
)
from app.services.db_service import get_history, save_analysis

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Database V3"])


@router.post("/db/save", response_model=DBSaveResponse)
async def api_save_analysis(req: DBSaveRequest):
    """Save an analysis result to the database.

    Stores the full analysis result as JSON for later retrieval.
    """
    try:
        result = save_analysis(
            sheet_name=req.sheet_name,
            analysis_type=req.analysis_type,
            result=req.result,
        )
        return DBSaveResponse(**result)
    except Exception as e:
        logger.exception("Database save endpoint gagal")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/db/history", response_model=DBHistoryResponse)
async def api_get_history(
    analysis_type: str | None = Query(None, description="Filter berdasarkan tipe analisis"),
    limit: int = Query(20, description="Jumlah maksimal record", ge=1, le=100),
):
    """Get analysis history from the database.

    Optionally filter by analysis type.  Results are sorted newest first.
    """
    try:
        result = get_history(
            analysis_type=analysis_type,
            limit=limit,
        )
        return DBHistoryResponse(**result)
    except Exception as e:
        logger.exception("Database history endpoint gagal")
        raise HTTPException(status_code=500, detail=str(e))
