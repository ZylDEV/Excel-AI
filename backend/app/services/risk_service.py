"""Service for risk scoring."""

import logging
from typing import Any

from core.analysis.risk_scoring import RiskScorer
from core.utils.excel_reader import read_range

logger = logging.getLogger(__name__)


def calculate_risk(
    data: list[list],
    headers: list[str],
    sheet_name: str = "",
) -> dict[str, Any]:
    """Calculate multi-factor risk scores from spreadsheet data.

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
    dict with keys: overall_score, dimensions, risk_level, details.
    """
    try:
        df = read_range(data=[headers] + data, headers=True)
        if df.empty:
            return {
                "overall_score": 0.0,
                "dimensions": [],
                "risk_level": "low",
                "details": ["Data kosong, tidak ada risiko terdeteksi."],
            }

        scorer = RiskScorer()
        result = scorer.score(df, context={"sheet_name": sheet_name})
        return result

    except Exception as e:
        logger.exception("Risk scoring service gagal")
        return {
            "overall_score": 0.0,
            "dimensions": [],
            "risk_level": "low",
            "details": [f"Gagal menghitung risiko: {e}"],
        }
