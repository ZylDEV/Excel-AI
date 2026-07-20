"""Service for explaining data using DataExplainer."""

import logging
from typing import Any

import pandas as pd

from core.analysis.explainer import DataExplainer
from core.utils.excel_reader import read_range

logger = logging.getLogger(__name__)


def explain_data(
    data: list[list[Any]],
    headers: list[str],
    sheet_name: str = "",
    api_key: str | None = None,
) -> dict[str, Any]:
    """Generate insights, statistics, and a natural-language explanation.

    Parameters
    ----------
    data : list[list[Any]]
        2-D array of cell values (rows × columns).
    headers : list[str]
        Column header names.
    sheet_name : str, optional
        Name of the sheet being analysed.
    api_key : str | None
        Optional API key to use instead of the default from settings.

    Returns
    -------
    dict with keys: insights, statistics, explanation
    """
    # Build DataFrame from raw data
    # We re-use read_range by embedding headers into the data shape
    full_data = [headers] + data if headers else data
    df = read_range(full_data, headers=bool(headers))

    explainer = DataExplainer()

    insights = explainer.get_insights(df)
    statistics = explainer.get_summary_statistics(df)

    context = f"Sheet name: {sheet_name}\n" if sheet_name else ""
    explanation = explainer.generate_explanation(df, question="", api_key=api_key)

    return {
        "insights": insights,
        "statistics": statistics,
        "explanation": explanation,
    }
