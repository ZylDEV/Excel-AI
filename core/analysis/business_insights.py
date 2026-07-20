"""Business intelligence insights generator."""

import logging
import warnings
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class BusinessInsights:
    """Generate business intelligence insights from tabular data.

    Detects trends, anomalies, correlations, and top performers, with an
    optional LLM-generated summary when an API key is available.
    """

    @staticmethod
    def _to_native(obj: Any) -> Any:
        """Recursively convert numpy types to native Python types."""
        if isinstance(obj, dict):
            return {k: BusinessInsights._to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [BusinessInsights._to_native(v) for v in obj]
        elif isinstance(obj, tuple):
            return tuple(BusinessInsights._to_native(v) for v in obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(round(obj, 6))
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return BusinessInsights._to_native(obj.tolist())
        elif pd.isna(obj):
            return None
        return obj

    @classmethod
    def generate(cls, df: pd.DataFrame, sheet_name: str = "", api_key: str | None = None) -> dict[str, Any]:
        """Generate comprehensive business insights from a DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            The data to analyse.
        sheet_name : str
            Optional sheet name for context.
        api_key : str | None
            If provided, the LLM summary is generated. Otherwise a
            statistics-based summary is returned.

        Returns
        -------
        dict with keys:
            - trends : list[dict]
            - anomalies : list[dict]
            - correlations : list[dict]
            - top_performers : list[dict]
            - summary : str
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            warnings.simplefilter("ignore", UserWarning)

            try:
                trends = cls._detect_trends(df)
                anomalies = cls._detect_anomalies(df)
                correlations = cls._find_correlations(df)
                top_performers = cls._find_top_performers(df)
                summary = cls._generate_summary(
                    df, trends, anomalies, correlations, top_performers, sheet_name, api_key
                )

                return {
                    "trends": cls._to_native(trends),
                    "anomalies": cls._to_native(anomalies),
                    "correlations": cls._to_native(correlations),
                    "top_performers": cls._to_native(top_performers),
                    "summary": summary,
                }

            except Exception as e:
                logger.exception("Gagal menghasilkan business insights")
                return {
                    "trends": [],
                    "anomalies": [],
                    "correlations": [],
                    "top_performers": [],
                    "summary": f"Gagal menghasilkan insights: {e}",
                }

    @staticmethod
    def _detect_trends(df: pd.DataFrame) -> list[dict[str, Any]]:
        """Detect upward/downward trends in numeric columns.

        Uses slope-based detection: if a simple linear regression over the
        row index has an absolute slope > 1% of the column mean, it is
        considered a trend.
        """
        trends: list[dict[str, Any]] = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) < 5:
                continue

            x = np.arange(len(series))
            y = series.values.astype(float)
            mean_y = float(np.mean(y))
            if abs(mean_y) < 1e-9:
                continue

            # Simple linear regression slope
            slope, _ = np.polyfit(x, y, 1)
            change_pct = (slope * len(series)) / mean_y * 100

            if abs(change_pct) < 5:
                continue  # Insignificant change

            direction = "naik" if change_pct > 0 else "turun"

            trends.append({
                "metric": col,
                "direction": direction,
                "change_pct": round(change_pct, 2),
                "description": (
                    f"Kolom '{col}' menunjukkan tren {direction} sebesar "
                    f"{abs(change_pct):.2f}% selama periode data"
                ),
            })

        return trends

    @staticmethod
    def _detect_anomalies(df: pd.DataFrame) -> list[dict[str, Any]]:
        """Detect anomalies in numeric columns using z-score > 3.

        For each numeric column, values with |z-score| > 3 are flagged.
        """
        anomalies: list[dict[str, Any]] = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) < 5:
                continue

            mean = float(series.mean())
            std = float(series.std())
            if std < 1e-9:
                continue

            z_scores = np.abs((series - mean) / std)
            anomaly_mask = z_scores > 3
            anomaly_indices = series.index[anomaly_mask]

            for idx in anomaly_indices:
                val = float(series.loc[idx])
                z = float(z_scores.loc[idx])
                anomalies.append({
                    "column": col,
                    "value": val,
                    "z_score": round(z, 4),
                    "description": (
                        f"Nilai {val} di kolom '{col}' (baris {int(idx) + 1}) "
                        f"adalah anomali dengan z-score {z:.2f}"
                    ),
                })

        # Limit to top 50 anomalies
        anomalies.sort(key=lambda a: a["z_score"], reverse=True)
        return anomalies[:50]

    @staticmethod
    def _find_correlations(df: pd.DataFrame) -> list[dict[str, Any]]:
        """Find strong Pearson correlations between numeric columns.

        Returns pairs with |r| >= 0.5 (excluding self-correlations).
        """
        correlations: list[dict[str, Any]] = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        if len(numeric_cols) < 2:
            return correlations

        corr_matrix = df[numeric_cols].corr(method="pearson")

        for i, col1 in enumerate(numeric_cols):
            for col2 in numeric_cols[i + 1:]:
                r = corr_matrix.loc[col1, col2]
                if pd.isna(r):
                    continue
                r_val = float(r)
                if abs(r_val) >= 0.5:
                    strength = "sangat kuat" if abs(r_val) >= 0.8 else "kuat" if abs(r_val) >= 0.6 else "cukup"
                    direction = "positif" if r_val > 0 else "negatif"
                    correlations.append({
                        "col1": col1,
                        "col2": col2,
                        "pearson": round(r_val, 4),
                        "description": (
                            f"Korelasi {direction} {strength} ({r_val:.2f}) "
                            f"antara '{col1}' dan '{col2}'"
                        ),
                    })

        correlations.sort(key=lambda c: abs(c["pearson"]), reverse=True)
        return correlations

    @staticmethod
    def _find_top_performers(df: pd.DataFrame) -> list[dict[str, Any]]:
        """Identify top performers in categorical-numeric relationships.

        For each text/categorical column with a numeric column, finds the
        top 5 categories by mean value.
        """
        top_performers: list[dict[str, Any]] = []
        text_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        for cat_col in text_cols:
            cat_series = df[cat_col].dropna()
            if cat_series.nunique() < 2 or cat_series.nunique() > 50:
                continue

            for num_col in numeric_cols[:3]:  # Limit to first 3 numeric cols to avoid explosion
                grouped = df.groupby(cat_col)[num_col].mean().dropna()
                if grouped.empty:
                    continue

                top = grouped.nlargest(5)
                for rank, (category, value) in enumerate(top.items(), 1):
                    top_performers.append({
                        "category": str(category),
                        "value": float(round(value, 4)),
                        "rank": rank,
                        "metric": num_col,
                    })

        return top_performers

    @staticmethod
    def _generate_summary(
        df: pd.DataFrame,
        trends: list[dict],
        anomalies: list[dict],
        correlations: list[dict],
        top_performers: list[dict],
        sheet_name: str = "",
        api_key: str | None = None,
    ) -> str:
        """Generate a summary text, optionally using LLM."""
        # Build a statistics-based summary as the base
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        text_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()
        date_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()

        lines = [
            f"Analisis data{' ' + sheet_name if sheet_name else ''}",
            f"Dataset memiliki {len(df)} baris dan {len(df.columns)} kolom.",
            f"Terdapat {len(numeric_cols)} kolom numerik, {len(text_cols)} kolom teks, {len(date_cols)} kolom tanggal.",
        ]

        if trends:
            lines.append(f"Terdeteksi {len(trends)} tren signifikan.")
        if anomalies:
            lines.append(f"Ditemukan {len(anomalies)} anomali statistik.")
        if correlations:
            lines.append(f"Terdapat {len(correlations)} korelasi signifikan antar variabel.")

        if api_key:
            try:
                llm_summary = BusinessInsights._llm_summary(
                    df, trends, anomalies, correlations, top_performers, sheet_name, api_key
                )
                return llm_summary
            except Exception:
                logger.warning("LLM summary gagal, menggunakan fallback statistik")

        return " ".join(lines)

    @staticmethod
    def _llm_summary(
        df: pd.DataFrame,
        trends: list[dict],
        anomalies: list[dict],
        correlations: list[dict],
        top_performers: list[dict],
        sheet_name: str = "",
        api_key: str = "",
    ) -> str:
        """Generate a natural-language business summary using LLM."""
        from core.utils.llm_client import LLMClient

        context = (
            f"Sheet: {sheet_name or 'Tidak bernama'}, "
            f"Baris: {len(df)}, Kolom: {len(df.columns)}, "
            f"Kolom numerik: {df.select_dtypes(include=[np.number]).columns.tolist()}, "
            f"Kolom teks: {df.select_dtypes(include=['object', 'string']).columns.tolist()}"
        )

        trends_text = "; ".join(
            f"{t['metric']}: {t['direction']} {t['change_pct']}%" for t in trends[:5]
        ) if trends else "Tidak ada tren signifikan"

        anomalies_text = "; ".join(
            f"{a['column']}={a['value']} (z={a['z_score']:.1f})" for a in anomalies[:5]
        ) if anomalies else "Tidak ada anomali signifikan"

        corr_text = "; ".join(
            f"{c['col1']}-{c['col2']}: {c['pearson']:.2f}" for c in correlations[:5]
        ) if correlations else "Tidak ada korelasi signifikan"

        prompt = (
            f"Buat ringkasan bisnis singkat (2-3 paragraf) dalam Bahasa Indonesia "
            f"berdasarkan data berikut:\n\n"
            f"Konteks: {context}\n\n"
            f"Tren: {trends_text}\n\n"
            f"Anomali: {anomalies_text}\n\n"
            f"Korelasi: {corr_text}\n\n"
            f"Berikan wawasan bisnis yang actionable."
        )

        client = LLMClient(api_key=api_key)
        return client.generate(prompt)
