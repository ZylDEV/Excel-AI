"""Service for fraud detection."""

import logging
from typing import Any

from core.analysis.fraud_detection import FraudDetector
from core.utils.excel_reader import read_range

logger = logging.getLogger(__name__)


def detect_fraud(
    data: list[list],
    headers: list[str],
    sheet_name: str = "",
) -> dict[str, Any]:
    """Detect potentially fraudulent transactions using ML + rules.

    Parameters
    ----------
    data : list[list]
        2-D array of cell values.
    headers : list[str]
        Column header names.
    sheet_name : str
        Optional sheet name for context.

    Returns
    -------
    dict with keys: anomalies, suspicious_patterns, fraud_score, summary.
    """
    try:
        df = read_range(data=[headers] + data, headers=True)
        if df.empty:
            return {
                "anomalies": [],
                "suspicious_patterns": [],
                "fraud_score": 0.0,
                "summary": "Data kosong, tidak dapat mendeteksi fraud.",
            }

        detector = FraudDetector()
        result = detector.detect(df)
        return result

    except Exception as e:
        logger.exception("Fraud detection service gagal")
        return {
            "anomalies": [],
            "suspicious_patterns": [],
            "fraud_score": 0.0,
            "summary": f"Gagal mendeteksi fraud: {e}",
        }
