"""API router for fraud detection (V3)."""

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import FraudDetectRequest, FraudDetectResponse
from app.services.fraud_service import detect_fraud

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Fraud Detection V3"])


@router.post("/fraud/detect", response_model=FraudDetectResponse)
async def api_detect_fraud(req: FraudDetectRequest):
    """Detect potentially fraudulent transactions/entries using ML + rules.

    Uses Isolation Forest, duplicate detection, timing analysis,
    round number detection, and Benford's Law analysis.
    """
    try:
        result = detect_fraud(
            data=req.data,
            headers=req.headers,
            sheet_name=req.sheet_name,
        )
        return FraudDetectResponse(**result)
    except Exception as e:
        logger.exception("Fraud detection gagal")
        raise HTTPException(status_code=500, detail=str(e))
