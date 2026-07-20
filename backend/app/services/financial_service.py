"""Service for financial health analysis."""

import logging
from typing import Any

from core.analysis.financial_health import FinancialHealthAnalyzer
from core.utils.excel_reader import read_range

logger = logging.getLogger(__name__)


def analyze_financial_health(
    data: list[list],
    headers: list[str],
    sheet_name: str = "",
) -> dict[str, Any]:
    """Analyze financial health from P&L / balance sheet data.

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
    dict with keys: profitability_ratios, liquidity_ratios, efficiency_ratios,
                    growth_metrics, health_score, health_level, insights.
    """
    try:
        df = read_range(data=[headers] + data, headers=True)
        if df.empty:
            return {
                "profitability_ratios": [],
                "liquidity_ratios": [],
                "efficiency_ratios": [],
                "growth_metrics": [],
                "health_score": 0.0,
                "health_level": "poor",
                "insights": ["Data kosong, tidak dapat menganalisis kesehatan finansial."],
            }

        analyzer = FinancialHealthAnalyzer()
        result = analyzer.analyze(df)
        return result

    except Exception as e:
        logger.exception("Financial health analysis service gagal")
        return {
            "profitability_ratios": [],
            "liquidity_ratios": [],
            "efficiency_ratios": [],
            "growth_metrics": [],
            "health_score": 0.0,
            "health_level": "poor",
            "insights": [f"Gagal menganalisis kesehatan finansial: {e}"],
        }
