"""In-process SQL analytics engine using DuckDB."""

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Attempt to import DuckDB
try:
    import duckdb

    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False
    logger.info("DuckDB tidak tersedia, SQL queries tidak dapat dijalankan")


class DuckDBAnalytics:
    """Run SQL queries directly on pandas DataFrames using DuckDB.

    The registered table name is always ``"data"`` so SQL queries should
    reference ``FROM data``.
    """

    @staticmethod
    def _to_native(obj: Any) -> Any:
        """Recursively convert numpy/pandas types to native Python types."""
        if isinstance(obj, dict):
            return {k: DuckDBAnalytics._to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [DuckDBAnalytics._to_native(v) for v in obj]
        elif isinstance(obj, tuple):
            return tuple(DuckDBAnalytics._to_native(v) for v in obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return DuckDBAnalytics._to_native(obj.tolist())
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
    def query(df: pd.DataFrame, sql: str) -> pd.DataFrame:
        """Run a SQL query on the DataFrame using DuckDB.

        Parameters
        ----------
        df : pd.DataFrame
            Source data. Referenced as ``"data"`` in SQL.
        sql : str
            SQL query string. Use ``data`` as the table name.

        Returns
        -------
        pd.DataFrame with query results.
        """
        if not DUCKDB_AVAILABLE:
            raise RuntimeError(
                "DuckDB tidak terinstall. Jalankan: pip install duckdb"
            )

        if df.empty:
            return pd.DataFrame()

        try:
            duckdb.register("data", df)
            result = duckdb.sql(sql).df()
            duckdb.unregister("data")
            return result
        except Exception as exc:
            logger.exception("DuckDB SQL query gagal")
            raise ValueError(
                f"Query SQL gagal dijalankan.\nSQL: {sql}\nError: {exc}"
            )

    @staticmethod
    def auto_analyze(df: pd.DataFrame) -> dict:
        """Auto-generate useful SQL queries and return results.

        Generates and executes queries for:
        - Top values per column (text columns)
        - Value distributions (text columns)
        - Summary statistics (numeric columns)
        - Correlation-like analysis (top numeric pairs)

        Parameters
        ----------
        df : pd.DataFrame
            Source data.

        Returns
        -------
        dict with keys: top_values, distributions, statistics, correlations.
        """
        if not DUCKDB_AVAILABLE:
            raise RuntimeError(
                "DuckDB tidak terinstall. Jalankan: pip install duckdb"
            )

        result: dict[str, Any] = {
            "top_values": {},
            "distributions": {},
            "statistics": {},
            "correlations": [],
        }

        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            text_cols = df.select_dtypes(include=["object", "string", "category"]).columns.tolist()

            # ── Top values for text columns ──────────────────────────
            for col in text_cols:
                try:
                    sql = f"""
                        SELECT "{col}" AS value, COUNT(*) AS count
                        FROM data
                        WHERE "{col}" IS NOT NULL
                        GROUP BY "{col}"
                        ORDER BY count DESC
                        LIMIT 10
                    """
                    top_df = DuckDBAnalytics.query(df, sql)
                    result["top_values"][col] = DuckDBAnalytics._to_native(
                        top_df.to_dict(orient="records")
                    )
                except Exception as exc:
                    logger.debug("Top values gagal untuk kolom '%s': %s", col, exc)
                    result["top_values"][col] = []

            # ── Value distributions for text columns ─────────────────
            for col in text_cols:
                try:
                    sql = f"""
                        SELECT
                            "{col}" AS value,
                            COUNT(*) AS count,
                            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM data WHERE "{col}" IS NOT NULL), 2) AS pct
                        FROM data
                        WHERE "{col}" IS NOT NULL
                        GROUP BY "{col}"
                        ORDER BY count DESC
                        LIMIT 20
                    """
                    dist_df = DuckDBAnalytics.query(df, sql)
                    result["distributions"][col] = DuckDBAnalytics._to_native(
                        dist_df.to_dict(orient="records")
                    )
                except Exception as exc:
                    logger.debug("Distribusi gagal untuk kolom '%s': %s", col, exc)
                    result["distributions"][col] = []

            # ── Summary statistics for numeric columns ───────────────
            if numeric_cols:
                col_exprs = []
                for col in numeric_cols:
                    col_exprs.append(f'COUNT("{col}") AS "{col}_count"')
                    col_exprs.append(f'AVG("{col}") AS "{col}_mean"')
                    col_exprs.append(f'STDDEV("{col}") AS "{col}_std"')
                    col_exprs.append(f'MIN("{col}") AS "{col}_min"')
                    col_exprs.append(f'MAX("{col}") AS "{col}_max"')
                    col_exprs.append(f'PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY "{col}") AS "{col}_p25"')
                    col_exprs.append(f'MEDIAN("{col}") AS "{col}_median"')
                    col_exprs.append(f'PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY "{col}") AS "{col}_p75"')

                sql = f"SELECT {', '.join(col_exprs)} FROM data"
                stats_df = DuckDBAnalytics.query(df, sql)
                if not stats_df.empty:
                    row = stats_df.iloc[0].to_dict()
                    parsed = {}
                    for col in numeric_cols:
                        parsed[col] = {
                            "count": DuckDBAnalytics._to_native(row.get(f"{col}_count")),
                            "mean": DuckDBAnalytics._to_native(row.get(f"{col}_mean")),
                            "std": DuckDBAnalytics._to_native(row.get(f"{col}_std")),
                            "min": DuckDBAnalytics._to_native(row.get(f"{col}_min")),
                            "max": DuckDBAnalytics._to_native(row.get(f"{col}_max")),
                            "p25": DuckDBAnalytics._to_native(row.get(f"{col}_p25")),
                            "median": DuckDBAnalytics._to_native(row.get(f"{col}_median")),
                            "p75": DuckDBAnalytics._to_native(row.get(f"{col}_p75")),
                        }
                    result["statistics"] = parsed

            # ── Correlation-like analysis (top numeric pairs) ────────
            if len(numeric_cols) >= 2:
                for i in range(len(numeric_cols)):
                    for j in range(i + 1, len(numeric_cols)):
                        a, b = numeric_cols[i], numeric_cols[j]
                        try:
                            sql = f"""
                                SELECT
                                    CORR("{a}", "{b}") AS correlation
                                FROM data
                                WHERE "{a}" IS NOT NULL AND "{b}" IS NOT NULL
                            """
                            corr_df = DuckDBAnalytics.query(df, sql)
                            if not corr_df.empty:
                                corr_val = corr_df.iloc[0]["correlation"]
                                if corr_val is not None and not (isinstance(corr_val, float) and np.isnan(corr_val)):
                                    result["correlations"].append({
                                        "col_1": a,
                                        "col_2": b,
                                        "correlation": DuckDBAnalytics._to_native(corr_val),
                                    })
                        except Exception as exc:
                            logger.debug("Korelasi gagal untuk %s vs %s: %s", a, b, exc)

            return result

        except Exception as exc:
            logger.exception("DuckDB auto_analyze gagal")
            return result
