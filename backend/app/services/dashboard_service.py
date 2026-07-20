"""Service for generating dashboard configurations."""

import logging
from typing import Any

from core.analysis.dashboard import DashboardGenerator
from core.utils.excel_reader import read_range

logger = logging.getLogger(__name__)


def generate_dashboard(
    data: list[list],
    headers: list[str],
    sheet_name: str = "",
) -> dict[str, Any]:
    """Generate a dashboard configuration (KPIs, charts, insights).

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
    dict with keys: kpis, charts, insights, summary.
    """
    try:
        df = read_range(data=[headers] + data, headers=True)
        if df.empty:
            return {
                "kpis": [],
                "charts": [],
                "insights": ["Data kosong, tidak dapat menghasilkan dashboard."],
                "summary": {},
            }

        result = DashboardGenerator.generate(
            df=df,
            sheet_name=sheet_name,
        )
        return result

    except Exception as e:
        logger.exception("Dashboard service gagal")
        return {
            "kpis": [],
            "charts": [],
            "insights": [f"Gagal menghasilkan dashboard: {e}"],
            "summary": {},
        }
