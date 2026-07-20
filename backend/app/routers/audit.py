"""API router for workbook audit."""

import logging

from fastapi import APIRouter, Header, HTTPException

from app.models.schemas import AuditRunRequest, AuditRunResponse
from app.services.audit_service import run_audit

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Audit"])


@router.post("/audit/run", response_model=AuditRunResponse)
async def api_run_audit(
    req: AuditRunRequest,
    x_api_key: str = Header(None, alias="X-API-Key"),
):
    """Run a full audit on workbook data (multiple sheets)."""
    try:
        # Convert SheetData models to plain dicts for the service
        sheets = [s.model_dump() for s in req.workbook_data]
        result = run_audit(workbook_data=sheets)
        return AuditRunResponse(**result)
    except Exception as e:
        logger.exception("Audit run failed")
        raise HTTPException(status_code=500, detail=str(e))
