"""High-performance data processing using Polars (with pandas fallback)."""

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Attempt to import Polars
try:
    import polars as pl

    POLARS_AVAILABLE = True
except ImportError:
    POLARS_AVAILABLE = False
    logger.info("Polars tidak tersedia, menggunakan pandas sebagai fallback")


class DataEngine:
    """High-performance data processing using Polars (with pandas fallback).

    All public methods accept and return pandas DataFrames for seamless
    integration with the rest of the codebase.  When Polars is installed
    the heavy lifting is done by Polars internally for better speed.
    """

    @staticmethod
    def _to_native(obj: Any) -> Any:
        """Recursively convert numpy/pandas types to native Python types."""
        if isinstance(obj, dict):
            return {k: DataEngine._to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [DataEngine._to_native(v) for v in obj]
        elif isinstance(obj, tuple):
            return tuple(DataEngine._to_native(v) for v in obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return DataEngine._to_native(obj.tolist())
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif hasattr(obj, "isoformat"):
            return obj.isoformat()
        try:
            if isinstance(obj, float) and (pd.isna(obj) or np.isnan(obj)):
                return None
        except Exception:
            pass
        return obj

    @staticmethod
    def _pd_to_pl(df: pd.DataFrame) -> Any:
        """Convert pandas DataFrame to Polars DataFrame."""
        if not POLARS_AVAILABLE:
            return None
        try:
            return pl.from_pandas(df)
        except Exception as exc:
            logger.warning("Konversi pandas ke polars gagal: %s", exc)
            return None

    @staticmethod
    def _pl_to_pd(pl_df: Any) -> pd.DataFrame | None:
        """Convert Polars DataFrame to pandas DataFrame."""
        try:
            return pl_df.to_pandas()
        except Exception as exc:
            logger.warning("Konversi polars ke pandas gagal: %s", exc)
            return None

    @staticmethod
    def read_range(headers: list[str], data: list[list]) -> pd.DataFrame:
        """Read tabular data into a DataFrame, preferring Polars internally.

        Parameters
        ----------
        headers : list[str]
            Column header names.
        data : list[list]
            2-D array of cell values (rows × columns).

        Returns
        -------
        pd.DataFrame
        """
        try:
            if POLARS_AVAILABLE:
                try:
                    pl_df = pl.DataFrame(data, schema=headers, orient="row")
                    pd_df = pl_df.to_pandas()
                except Exception as exc:
                    logger.debug("Polars read_range gagal, fallback ke pandas: %s", exc)
                    pd_df = pd.DataFrame(data, columns=headers)
            else:
                pd_df = pd.DataFrame(data, columns=headers)

            # Coerce types
            for col in pd_df.columns:
                try:
                    converted = pd.to_numeric(pd_df[col], errors="coerce")
                    if converted.notna().sum() >= max(1, len(pd_df) * 0.5):
                        pd_df[col] = converted
                except (ValueError, TypeError):
                    pass

            return pd_df

        except Exception as exc:
            logger.exception("DataEngine.read_range gagal")
            return pd.DataFrame(data, columns=headers)

    @staticmethod
    def fast_aggregate(
        df: pd.DataFrame,
        group_col: str,
        agg_col: str,
        agg_func: str = "sum",
    ) -> pd.DataFrame:
        """Fast aggregation using Polars if available, otherwise pandas.

        Parameters
        ----------
        df : pd.DataFrame
            Source data.
        group_col : str
            Column name to group by.
        agg_col : str
            Column name to aggregate.
        agg_func : str
            Aggregate function: ``"sum"``, ``"mean"``, ``"count"``,
            ``"min"``, ``"max"``, ``"std"``, ``"var"``.

        Returns
        -------
        pd.DataFrame with columns [group_col, agg_col].
        """
        try:
            if POLARS_AVAILABLE:
                pl_df = DataEngine._pd_to_pl(df)
                if pl_df is not None:
                    try:
                        agg_expr = getattr(pl.col(agg_col), agg_func)()
                        result_pl = pl_df.group_by(group_col).agg(agg_expr).sort(group_col)
                        result_pd = result_pl.to_pandas()
                        result_pd.columns = [group_col, agg_col]
                        return result_pd
                    except Exception as exc:
                        logger.debug("Polars aggregasi gagal, fallback: %s", exc)

            # Fallback pandas
            result = df.groupby(group_col, sort=True)[agg_col].agg(agg_func).reset_index()
            return result

        except Exception as exc:
            logger.exception("DataEngine.fast_aggregate gagal")
            raise ValueError(
                f"Agregasi gagal untuk kolom group='{group_col}', agg='{agg_col}': {exc}"
            )

    @staticmethod
    def fast_filter(
        df: pd.DataFrame,
        col: str,
        min_val: float,
        max_val: float,
    ) -> pd.DataFrame:
        """Fast filtered data using Polars if available, otherwise pandas.

        Parameters
        ----------
        df : pd.DataFrame
            Source data.
        col : str
            Numeric column name to filter on.
        min_val : float
            Minimum value (inclusive).
        max_val : float
            Maximum value (inclusive).

        Returns
        -------
        pd.DataFrame with rows where ``min_val <= col <= max_val``.
        """
        try:
            if POLARS_AVAILABLE:
                pl_df = DataEngine._pd_to_pl(df)
                if pl_df is not None:
                    try:
                        filtered = pl_df.filter(
                            (pl.col(col) >= min_val) & (pl.col(col) <= max_val)
                        )
                        return filtered.to_pandas()
                    except Exception as exc:
                        logger.debug("Polars filter gagal, fallback: %s", exc)

            # Fallback pandas
            numeric = pd.to_numeric(df[col], errors="coerce")
            mask = numeric.between(min_val, max_val)
            return df.loc[mask].copy()

        except Exception as exc:
            logger.exception("DataEngine.fast_filter gagal")
            raise ValueError(
                f"Filter gagal untuk kolom '{col}' rentang [{min_val}, {max_val}]: {exc}"
            )

    @staticmethod
    def to_native_dict(obj: Any) -> Any:
        """Public helper to deep-convert numpy/pandas types."""
        return DataEngine._to_native(obj)
