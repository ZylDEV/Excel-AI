"""API router for inventory intelligence (V3)."""

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import InventoryAnalysisRequest, InventoryAnalysisResponse
from app.services.inventory_service import analyze_inventory

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Inventory Intelligence V3"])


@router.post("/inventory/analyze", response_model=InventoryAnalysisResponse)
async def api_analyze_inventory(req: InventoryAnalysisRequest):
    """Analyze inventory data for stock insights and reorder suggestions.

    Auto-detects column types and returns stock categories,
    aging analysis, reorder suggestions, and warehouse distribution.
    """
    try:
        result = analyze_inventory(
            data=req.data,
            headers=req.headers,
            sheet_name=req.sheet_name,
        )
        return InventoryAnalysisResponse(**result)
    except Exception as e:
        logger.exception("Inventory analysis gagal")
        raise HTTPException(status_code=500, detail=str(e))
