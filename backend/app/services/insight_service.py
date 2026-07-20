"""Service for generating business insights."""

import logging
from typing import Any

from core.analysis.business_insights import BusinessInsights
from core.utils.excel_reader import read_range

logger = logging.getLogger(__name__)


def generate_insights(
    data: list[list],
    headers: list[str],
    sheet_name: str = "",
    api_key: str | None = None,
) -> dict[str, Any]:
    """Generate business intelligence insights from tabular data.

    Parameters
    ----------
    data : list[list]
        2-D array of cell values.
    headers : list[str]
        Column header names.
    sheet_name : str
        Optional sheet name for context.
    api_key : str | None
        Optional API key for LLM-enhanced summary.

    Returns
    -------
    dict with keys: trends, anomalies, correlations, top_performers, summary.
    """
    try:
        df = read_range(data=[headers] + data, headers=True)
        if df.empty:
            return {
                "trends": [],
                "anomalies": [],
                "correlations": [],
                "top_performers": [],
                "summary": "Data kosong, tidak dapat menghasilkan insights.",
            }

        result = BusinessInsights.generate(
            df=df,
            sheet_name=sheet_name,
            api_key=api_key,
        )
        return result

    except Exception as e:
        logger.exception("Insight service gagal")
        return {
            "trends": [],
            "anomalies": [],
            "correlations": [],
            "top_performers": [],
            "summary": f"Gagal menghasilkan insights: {e}",
        }
