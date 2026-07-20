"""Dashboard generator — produces KPI cards and chart configurations."""

import logging
import warnings
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DashboardGenerator:
    """Auto-generate dashboard configuration from tabular data.

    Detects column types and produces KPI cards, chart configs, key
    insights, and a numeric summary.  Designed to work with *any* column
    names — no hard-coded label matching.
    """

    @staticmethod
    def _to_native(obj: Any) -> Any:
        """Recursively convert numpy types to native Python types."""
        if isinstance(obj, dict):
            return {k: DashboardGenerator._to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [DashboardGenerator._to_native(v) for v in obj]
        elif isinstance(obj, tuple):
            return tuple(DashboardGenerator._to_native(v) for v in obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(round(obj, 6))
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return DashboardGenerator._to_native(obj.tolist())
        elif pd.isna(obj):
            return None
        return obj

    @classmethod
    def generate(cls, df: pd.DataFrame, sheet_name: str = "") -> dict[str, Any]:
        """Generate a full dashboard configuration.

        Parameters
        ----------
        df : pd.DataFrame
            The data to build the dashboard from.
        sheet_name : str
            Optional sheet name for context.

        Returns
        -------
        dict with keys:
            - kpis : list[dict]
            - charts : list[dict]
            - insights : list[str]
            - summary : dict
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            warnings.simplefilter("ignore", UserWarning)

            try:
                cols = cls._auto_detect_columns(df)
                kpis = cls._build_kpis(df, cols)
                charts = cls._build_charts(df, cols)
                insights = cls._generate_insights(df, cols, kpis, charts)
                summary = cls._build_summary(df, cols)

                return {
                    "kpis": cls._to_native(kpis),
                    "charts": cls._to_native(charts),
                    "insights": insights,
                    "summary": cls._to_native(summary),
                }

            except Exception as e:
                logger.exception("Gagal menghasilkan dashboard")
                return {
                    "kpis": [],
                    "charts": [],
                    "insights": [f"Gagal menghasilkan dashboard: {e}"],
                    "summary": {},
                }

    @staticmethod
    def _auto_detect_columns(df: pd.DataFrame) -> dict[str, Any]:
        """Classify columns into semantic groups.

        Returns a dict with:
            - numeric: list[str]
            - text: list[str]
            - date: list[str]
            - boolean: list[str]
        """
        numeric = df.select_dtypes(include=[np.number]).columns.tolist()
        date = df.select_dtypes(include=["datetime64"]).columns.tolist()
        bool_cols = df.select_dtypes(include=["bool"]).columns.tolist()

        # Remaining object/string columns are text
        all_covered = set(numeric) | set(date) | set(bool_cols)
        text = [c for c in df.columns if c not in all_covered]

        return {
            "numeric": numeric,
            "text": text,
            "date": date,
            "boolean": bool_cols,
        }

    @staticmethod
    def _build_kpis(df: pd.DataFrame, cols: dict) -> list[dict[str, Any]]:
        """Build KPI cards from numeric columns.

        For each numeric column, creates KPIs for sum, mean, min, and max.
        Period-over-period change is calculated by splitting the data in half.
        """
        kpis: list[dict[str, Any]] = []
        numeric = cols.get("numeric", [])
        date_cols = cols.get("date", [])

        for col in numeric:
            series = df[col].dropna()
            if series.empty:
                continue

            total = float(series.sum())
            avg = float(series.mean())
            minimum = float(series.min())
            maximum = float(series.max())

            # Period-over-period change (split data in half)
            half = len(series) // 2
            if half > 1:
                first_half = float(series.iloc[:half].mean())
                second_half = float(series.iloc[half: 2 * half].mean())
                change_pct = ((second_half - first_half) / first_half * 100) if abs(first_half) > 1e-9 else 0.0
            else:
                change_pct = 0.0

            kpis.append({
                "label": f"Total {col}",
                "value": round(total, 2),
                "change_pct": round(change_pct, 2),
                "icon": "trending_up",
                "color": "#4CAF50" if change_pct >= 0 else "#F44336",
                "prefix": "",
                "suffix": "",
            })

            kpis.append({
                "label": f"Rata-rata {col}",
                "value": round(avg, 2),
                "change_pct": round(change_pct, 2),
                "icon": "equalizer",
                "color": "#2196F3",
                "prefix": "",
                "suffix": "",
            })

            kpis.append({
                "label": f"Min {col}",
                "value": round(minimum, 2),
                "change_pct": 0.0,
                "icon": "arrow_downward",
                "color": "#FF9800",
                "prefix": "",
                "suffix": "",
            })

            kpis.append({
                "label": f"Max {col}",
                "value": round(maximum, 2),
                "change_pct": 0.0,
                "icon": "arrow_upward",
                "color": "#9C27B0",
                "prefix": "",
                "suffix": "",
            })

        # If there is a date column, add row-based KPIs
        if date_cols:
            date_series = df[date_cols[0]].dropna()
            if not date_series.empty:
                kpis.append({
                    "label": "Periode Data",
                    "value": f"{date_series.min().strftime('%d/%m/%Y')} - {date_series.max().strftime('%d/%m/%Y')}",
                    "change_pct": 0.0,
                    "icon": "date_range",
                    "color": "#607D8B",
                    "prefix": "",
                    "suffix": "",
                })

        # Limit to 12 KPIs max
        return kpis[:12]

    @staticmethod
    def _build_charts(df: pd.DataFrame, cols: dict) -> list[dict[str, Any]]:
        """Build chart configurations from detected columns.

        Produces:
        - Trend (line) chart for date + numeric columns
        - Bar chart for text + numeric aggregates
        - Pie chart for text column value distributions
        """
        charts: list[dict[str, Any]] = []
        numeric = cols.get("numeric", [])
        text = cols.get("text", [])
        date_cols = cols.get("date", [])

        # 1. Trend chart: date vs numeric
        if date_cols and numeric:
            date_col = date_cols[0]
            for num_col in numeric[:3]:  # Limit to first 3 numeric cols
                temp = df[[date_col, num_col]].dropna().sort_values(date_col)
                if temp.empty:
                    continue
                labels = [str(d.date()) if hasattr(d, "date") else str(d) for d in temp[date_col]]
                charts.append({
                    "type": "line",
                    "title": f"Tren {num_col}",
                    "labels": labels,
                    "datasets": [{
                        "label": num_col,
                        "data": [round(float(v), 4) for v in temp[num_col]],
                        "borderColor": "#2196F3",
                        "fill": False,
                    }],
                    "options": {
                        "responsive": True,
                        "maintainAspectRatio": True,
                    },
                })

        # 2. Bar chart: text categories vs numeric aggregates
        if text and numeric:
            for cat_col in text[:2]:  # Limit to first 2 text cols
                cat_series = df[cat_col].dropna()
                if cat_series.nunique() < 2 or cat_series.nunique() > 20:
                    continue
                for num_col in numeric[:2]:  # Limit to first 2 numeric cols
                    grouped = df.groupby(cat_col)[num_col].mean().dropna().nlargest(10)
                    if grouped.empty:
                        continue
                    charts.append({
                        "type": "bar",
                        "title": f"Rata-rata {num_col} per {cat_col}",
                        "labels": [str(k) for k in grouped.index],
                        "datasets": [{
                            "label": num_col,
                            "data": [round(float(v), 4) for v in grouped.values],
                            "backgroundColor": "#4CAF50",
                        }],
                        "options": {
                            "responsive": True,
                            "maintainAspectRatio": True,
                        },
                    })
                    break  # Only one bar chart per text col

        # 3. Pie chart: text column distributions
        for cat_col in text[:3]:  # Limit to first 3 text cols
            cat_series = df[cat_col].dropna()
            if cat_series.nunique() < 2 or cat_series.nunique() > 10:
                continue
            value_counts = cat_series.value_counts().nlargest(8)
            if value_counts.empty:
                continue
            charts.append({
                "type": "pie",
                "title": f"Distribusi {cat_col}",
                "labels": [str(k) for k in value_counts.index],
                "datasets": [{
                    "label": "Jumlah",
                    "data": [int(v) for v in value_counts.values],
                    "backgroundColor": [
                        "#4CAF50", "#2196F3", "#FF9800", "#9C27B0",
                        "#F44336", "#00BCD4", "#FF5722", "#607D8B",
                    ],
                }],
                "options": {
                    "responsive": True,
                    "maintainAspectRatio": True,
                },
            })

        return charts

    @staticmethod
    def _generate_insights(
        df: pd.DataFrame,
        cols: dict,
        kpis: list[dict],
        charts: list[dict],
    ) -> list[str]:
        """Generate top key insight statements."""
        insights: list[str] = []
        numeric = cols.get("numeric", [])
        text = cols.get("text", [])
        date_cols = cols.get("date", [])

        # Insight 1: Dataset overview
        insights.append(
            f"Dataset memiliki {len(df)} baris dan {len(df.columns)} kolom "
            f"dengan {len(numeric)} kolom numerik, {len(text)} kolom teks, "
            f"dan {len(date_cols)} kolom tanggal."
        )

        # Insight 2: Numeric spread
        for col in numeric[:2]:
            series = df[col].dropna()
            if not series.empty:
                insights.append(
                    f"Nilai {col} berkisar dari {float(series.min()):.2f} "
                    f"sampai {float(series.max()):.2f} "
                    f"(rata-rata {float(series.mean()):.2f})."
                )

        # Insight 3: Top text categories
        for col in text[:2]:
            series = df[col].dropna()
            if not series.empty and series.nunique() <= 20:
                top = series.value_counts().head(3)
                top_str = ", ".join(f"'{k}' ({int(v)})" for k, v in top.items())
                insights.append(
                    f"Kategori teratas di '{col}': {top_str}."
                )

        # Insight 4: Date range
        if date_cols:
            date_series = df[date_cols[0]].dropna()
            if not date_series.empty:
                insights.append(
                    f"Periode data {date_cols[0]}: "
                    f"{date_series.min().strftime('%d/%m/%Y')} - "
                    f"{date_series.max().strftime('%d/%m/%Y')}."
                )

        # Insight 5: KPI changes
        positive_kpis = [k for k in kpis if k.get("change_pct", 0) > 5]
        negative_kpis = [k for k in kpis if k.get("change_pct", 0) < -5]
        if positive_kpis:
            insights.append(
                f"Terdapat {len(positive_kpis)} metrik dengan tren positif, "
                f"menunjukkan pertumbuhan yang baik."
            )
        if negative_kpis:
            insights.append(
                f"Terdapat {len(negative_kpis)} metrik dengan tren negatif "
                f"yang mungkin memerlukan perhatian."
            )

        return insights[:5]

    @staticmethod
    def _build_summary(df: pd.DataFrame, cols: dict) -> dict[str, Any]:
        """Build a numeric summary of the data."""
        numeric = cols.get("numeric", [])
        total_revenue = 0.0
        total_profit = 0.0
        growth = 0.0

        if numeric:
            for col in numeric:
                series = df[col].dropna()
                if not series.empty:
                    # Use the first numeric col for total_revenue
                    total_revenue = float(series.sum())
                    break

        if len(numeric) >= 2:
            # Pick first two numeric cols as proxy for revenue and profit
            s1 = df[numeric[0]].dropna()
            s2 = df[numeric[1]].dropna()
            total_revenue = float(s1.sum()) if not s1.empty else 0.0
            total_profit = float(s2.sum()) if not s2.empty else 0.0

            half1 = len(s1) // 2
            if half1 > 1:
                g1 = float(s1.iloc[:half1].sum())
                g2 = float(s1.iloc[half1:].sum())
                growth = ((g2 - g1) / g1 * 100) if abs(g1) > 1e-9 else 0.0

        return {
            "total_revenue": round(total_revenue, 2),
            "total_profit": round(total_profit, 2),
            "growth": round(growth, 2),
            "row_count": len(df),
            "column_count": len(df.columns),
            "numeric_count": len(numeric),
        }
