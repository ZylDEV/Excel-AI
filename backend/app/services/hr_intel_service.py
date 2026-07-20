"""Service for HR intelligence analysis."""

import logging
from typing import Any

from core.analysis.hr_intelligence import HRAnalyzer
from core.utils.excel_reader import read_range

logger = logging.getLogger(__name__)


def analyze_hr(
    data: list[list],
    headers: list[str],
    sheet_name: str = "",
) -> dict[str, Any]:
    """Analyze HR/employee data.

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
    dict with keys: salary_analysis, headcount, overtime_analysis,
                    attendance_patterns, duplicate_employees,
                    productivity_metrics, summary.
    """
    try:
        df = read_range(data=[headers] + data, headers=True)
        if df.empty:
            return {
                "salary_analysis": {},
                "headcount": {},
                "overtime_analysis": {},
                "attendance_patterns": {},
                "duplicate_employees": [],
                "productivity_metrics": {},
                "summary": "Data HR kosong.",
            }

        analyzer = HRAnalyzer()
        result = analyzer.analyze(df)
        return result

    except Exception as e:
        logger.exception("HR analysis service gagal")
        return {
            "salary_analysis": {},
            "headcount": {},
            "overtime_analysis": {},
            "attendance_patterns": {},
            "duplicate_employees": [],
            "productivity_metrics": {},
            "summary": f"Gagal menganalisis data HR: {e}",
        }
