"""Utilities for reading and processing Excel data."""

import logging
from typing import Any, Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def read_range(
    data: list[list[Any]],
    headers: bool = True,
) -> pd.DataFrame:
    """Parse a 2-D list (Excel range) into a pandas DataFrame.

    Parameters
    ----------
    data : list[list]
        Row-major 2-D list of cell values as extracted from Excel.
    headers : bool
        If True the first row is used as column names.

    Returns
    -------
    pd.DataFrame
    """
    if not data or not data[0]:
        return pd.DataFrame()

    rows = data[1:] if headers else data
    col_names: Optional[list[str]]

    if headers:
        col_names = [str(h) if h is not None else f"Column_{i}" for i, h in enumerate(data[0])]
    else:
        col_names = [f"Column_{i}" for i in range(len(data[0]))]

    df = pd.DataFrame(rows, columns=col_names)

    # Normalise None → NaN
    df = df.map(lambda x: np.nan if x is None else x)

    # Try to cast each column to the best possible dtype
    for col in df.columns:
        _coerce_column(df, col)

    return df


def _coerce_column(df: pd.DataFrame, col: str):
    """Best-effort type coercion for a single column."""
    # Skip if mostly NaN (>90 %)
    if df[col].isna().mean() > 0.9:
        df[col] = df[col].astype(object)
        return

    # Try numeric
    try:
        converted = pd.to_numeric(df[col], errors="coerce")
        if converted.notna().sum() >= max(1, len(df) * 0.5):
            df[col] = converted
            return
    except (ValueError, TypeError):
        pass

    # Try datetime (common Excel formats)
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            converted = pd.to_datetime(df[col], errors="coerce")
        if converted.notna().sum() >= max(1, len(df) * 0.5):
            df[col] = converted
            return
    except (ValueError, TypeError):
        pass


def get_statistics(df: pd.DataFrame) -> dict[str, Any]:
    """Return basic descriptive statistics for a DataFrame.

    Returns
    -------
    dict with keys: row_count, column_count, numeric_stats, text_stats, missing.
    """
    result: dict[str, Any] = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": list(df.columns),
        "missing": {
            col: int(df[col].isna().sum()) for col in df.columns
        },
        "dtypes": {col: str(df[col].dtype) for col in df.columns},
    }

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    text_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()
    date_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()

    result["numeric_columns"] = numeric_cols
    result["text_columns"] = text_cols
    result["date_columns"] = date_cols

    # Numeric stats
    if numeric_cols:
        desc = df[numeric_cols].describe(percentiles=[0.25, 0.5, 0.75]).to_dict()
        result["numeric_stats"] = {
            col: {
                "count": int(v["count"]) if not np.isnan(v["count"]) else 0,
                "mean": float(v["mean"]) if not np.isnan(v["mean"]) else None,
                "std": float(v["std"]) if not np.isnan(v["std"]) else None,
                "min": float(v["min"]) if not np.isnan(v["min"]) else None,
                "25%": float(v["25%"]) if not np.isnan(v["25%"]) else None,
                "50%": float(v["50%"]) if not np.isnan(v["50%"]) else None,
                "75%": float(v["75%"]) if not np.isnan(v["75%"]) else None,
                "max": float(v["max"]) if not np.isnan(v["max"]) else None,
            }
            for col, v in desc.items()
        }
    else:
        result["numeric_stats"] = {}

    # Text stats
    if text_cols:
        result["text_stats"] = {
            col: {
                "unique": int(df[col].nunique()),
                "top": str(df[col].mode().iloc[0]) if not df[col].mode().empty else None,
                "top_freq": int(df[col].value_counts().iloc[0]) if not df[col].value_counts().empty else 0,
                "empty_count": int(df[col].isna().sum()),
            }
            for col in text_cols
        }
    else:
        result["text_stats"] = {}

    return result


def detect_column_types(df: pd.DataFrame) -> dict[str, str]:
    """Detect the semantic type of each column.

    Returns
    -------
    dict mapping column name → "numeric" | "text" | "date" | "boolean" | "mixed".
    """
    _BOOLEAN_LIKE = {"true", "false", "yes", "no", "1", "0", "y", "n", "t", "f"}

    types: dict[str, str] = {}
    for col in df.columns:
        dtype = df[col].dtype
        non_null = df[col].dropna()

        if pd.api.types.is_bool_dtype(dtype):
            types[col] = "boolean"
        elif non_null.nunique() == 2 and non_null.astype(str).str.lower().isin(
            _BOOLEAN_LIKE
        ).all():
            types[col] = "boolean"
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            types[col] = "date"
        elif pd.api.types.is_numeric_dtype(dtype):
            types[col] = "numeric"
        elif pd.api.types.is_string_dtype(dtype) or dtype == object:
            # Heuristic: if most values look numeric, label it numeric
            if len(non_null) > 0:
                numeric_ratio = pd.to_numeric(non_null, errors="coerce").notna().mean()
                if numeric_ratio > 0.8:
                    types[col] = "numeric"
                else:
                    types[col] = "text"
            else:
                types[col] = "text"
        else:
            types[col] = "mixed"
    return types
