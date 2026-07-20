"""Service for sales intelligence analysis."""

import logging
from typing import Any

from core.analysis.sales_intelligence import SalesAnalyzer
from core.utils.excel_reader import read_range

logger = logging.getLogger(__name__)


def analyze_sales(
    data: list[list],
    headers: list[str],
    sheet_name: str = "",
) -> dict[str, Any]:
    """Analyze sales data for business intelligence.

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
    dict with keys: top_customers, customer_segments, sales_trend,
                    product_performance, regional_analysis,
                    cross_selling_opportunities, summary.
    """
    try:
        df = read_range(data=[headers] + data, headers=True)
        if df.empty:
            return {
                "top_customers": [],
                "customer_segments": [],
                "sales_trend": [],
                "product_performance": [],
                "regional_analysis": [],
                "cross_selling_opportunities": [],
                "summary": "Data penjualan kosong.",
            }

        analyzer = SalesAnalyzer()
        result = analyzer.analyze(df)
        return result

    except Exception as e:
        logger.exception("Sales analysis service gagal")
        return {
            "top_customers": [],
            "customer_segments": [],
            "sales_trend": [],
            "product_performance": [],
            "regional_analysis": [],
            "cross_selling_opportunities": [],
            "summary": f"Gagal menganalisis penjualan: {e}",
        }
