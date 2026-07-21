"""Service for data quality analysis and cleaning."""

import logging
from typing import Any

import pandas as pd

from core.analysis.data_quality import DataQualityAnalyzer
from core.utils.excel_reader import read_range

logger = logging.getLogger(__name__)


def analyze_quality(
    data: list[list[Any]],
    headers: list[str],
    api_key: str | None = None,
    provider: str | None = None,
) -> dict[str, Any]:
    """Analyse data quality and return issues.

    Parameters
    ----------
    data : list[list[Any]]
        2-D array of cell values.
    headers : list[str]
        Column header names.
    api_key : str | None
        Optional API key (unused by this service, kept for interface consistency).

    Returns
    -------
    dict with keys: issues
    """
    full_data = [headers] + data if headers else data
    df = read_range(full_data, headers=bool(headers))

    analyzer = DataQualityAnalyzer()
    issues = analyzer.analyze(df)

    return {
        "issues": issues,
    }


def apply_cleaning(
    data: list[list[Any]],
    headers: list[str],
    fixes: list[str],
    api_key: str | None = None,
    provider: str | None = None,
) -> dict[str, Any]:
    """Apply cleaning fixes to the data.

    Parameters
    ----------
    data : list[list[Any]]
        2-D array of cell values.
    headers : list[str]
        Column header names.
    fixes : list[str]
        List of fix labels to apply.
    api_key : str | None
        Optional API key (unused by this service, kept for interface consistency).

    Returns
    -------
    dict with keys: data (cleaned rows), headers, applied_fixes
    """
    full_data = [headers] + data if headers else data
    df = read_range(full_data, headers=bool(headers))

    analyzer = DataQualityAnalyzer()
    cleaned_df = analyzer.clean(df, fixes)

    # Build the applied fixes list by comparing before/after
    applied = _detect_applied_fixes(df, cleaned_df, fixes)

    # Convert cleaned DataFrame back to list-of-lists
    cleaned_headers = list(cleaned_df.columns)
    # Replace NaN/NaT with None for JSON serialisation
    cleaned_data = cleaned_df.where(cleaned_df.notna(), None).values.tolist()
    # Convert numpy types to native Python types
    cleaned_data = [[_clean_cell(cell) for cell in row] for row in cleaned_data]

    return {
        "data": cleaned_data,
        "headers": cleaned_headers,
        "applied_fixes": applied,
    }


def _detect_applied_fixes(
    original: pd.DataFrame,
    cleaned: pd.DataFrame,
    requested_fixes: list[str],
) -> list[str]:
    """Return a human-readable list of fixes that actually had an effect."""
    applied: list[str] = []
    fix_set = {f.strip().lower() for f in requested_fixes}

    if "remove_duplicates" in fix_set:
        orig_len = len(original)
        clean_len = len(cleaned)
        if clean_len < orig_len:
            applied.append(f"remove_duplicates: removed {orig_len - clean_len} row(s)")

    if "drop_constant_columns" in fix_set:
        dropped = set(original.columns) - set(cleaned.columns)
        for col in dropped:
            applied.append(f"drop_constant_columns: {col}")

    if "drop_missing_high" in fix_set:
        dropped = set(original.columns) - set(cleaned.columns)
        for col in dropped:
            if col in original.columns and original[col].isna().mean() > 0.5:
                applied.append(f"drop_missing_high: {col}")

    for fix in ["fill_missing_mean", "fill_missing_median", "fill_missing_mode"]:
        if fix in fix_set:
            common_cols = set(original.columns) & set(cleaned.columns)
            for col in common_cols:
                if original[col].isna().sum() > 0 and cleaned[col].isna().sum() < original[col].isna().sum():
                    applied.append(f"{fix}: {col}")

    if "remove_outliers_iqr" in fix_set:
        orig_len = len(original)
        clean_len = len(cleaned)
        if clean_len < orig_len and orig_len - clean_len != len(original) - len(original.drop_duplicates()):
            applied.append(f"remove_outliers_iqr: removed {orig_len - clean_len} row(s)")

    if "strip_whitespace" in fix_set:
        applied.append("strip_whitespace")

    if not applied:
        return ["No changes were needed or applied."]

    return applied


def _clean_cell(cell: Any) -> Any:
    """Convert numpy/pandas types to JSON-safe native Python types."""
    import numpy as np

    if cell is None:
        return None
    if isinstance(cell, (np.integer,)):
        return int(cell)
    if isinstance(cell, (np.floating,)):
        val = float(cell)
        return None if np.isnan(val) or np.isinf(val) else val
    if isinstance(cell, (np.bool_,)):
        return bool(cell)
    if hasattr(cell, "isoformat"):  # datetime / Timestamp
        return cell.isoformat()
    if isinstance(cell, (pd.Timestamp,)):
        return cell.isoformat()
    return cell
