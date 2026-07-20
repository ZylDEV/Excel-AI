"""Multi-factor risk scoring engine."""

import logging
import warnings
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class RiskScorer:
    """Calculates risk scores across multiple dimensions.

    Evaluates:
    - Volatility risk (coefficient of variation, outliers)
    - Concentration risk (dependency on few customers/suppliers)
    - Trend risk (declining patterns over time)
    - Missing data risk (incomplete records)
    """

    @staticmethod
    def _to_native(obj: Any) -> Any:
        """Recursively convert numpy/pandas types to native Python types."""
        if isinstance(obj, dict):
            return {k: RiskScorer._to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [RiskScorer._to_native(v) for v in obj]
        elif isinstance(obj, tuple):
            return tuple(RiskScorer._to_native(v) for v in obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return RiskScorer._to_native(obj.tolist())
        elif isinstance(obj, pd.Timestamp):
            return str(obj)
        elif pd.isna(obj):
            return None
        return obj

    @staticmethod
    def _find_numeric_cols(df: pd.DataFrame) -> list[str]:
        return df.select_dtypes(include=[np.number]).columns.tolist()

    @staticmethod
    def _find_text_cols(df: pd.DataFrame) -> list[str]:
        return df.select_dtypes(include=["object", "string"]).columns.tolist()

    @staticmethod
    def _find_date_cols(df: pd.DataFrame) -> list[str]:
        return df.select_dtypes(include=["datetime64"]).columns.tolist()

    def score(self, df: pd.DataFrame, context: dict = None) -> dict:
        """Calculate multi-factor risk scores.

        Parameters
        ----------
        df : pd.DataFrame
            The input data to evaluate.
        context : dict, optional
            Additional context about the data (e.g., sheet name, industry).

        Returns
        -------
        dict with keys:
            - overall_score : float (0-100, higher = riskier)
            - dimensions : list of {name, score, weight, factors}
            - risk_level : "low" | "medium" | "high" | "critical"
            - details : list of descriptions per risk factor
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            warnings.simplefilter("ignore", UserWarning)

            try:
                if df.empty:
                    return {
                        "overall_score": 0.0,
                        "dimensions": [],
                        "risk_level": "low",
                        "details": ["Data kosong, tidak ada risiko terdeteksi."],
                    }

                dimensions = []
                details = []

                # Volatility risk
                try:
                    vol = self._volatility_risk(df)
                    dimensions.append(vol)
                    if vol["score"] > 0:
                        for f in vol.get("factors", []):
                            details.append(f)
                except Exception as e:
                    logger.warning(f"Volatility risk gagal: {e}")

                # Concentration risk
                try:
                    conc = self._concentration_risk(df)
                    dimensions.append(conc)
                    if conc["score"] > 0:
                        for f in conc.get("factors", []):
                            details.append(f)
                except Exception as e:
                    logger.warning(f"Concentration risk gagal: {e}")

                # Trend risk
                try:
                    trend = self._trend_risk(df)
                    dimensions.append(trend)
                    if trend["score"] > 0:
                        for f in trend.get("factors", []):
                            details.append(f)
                except Exception as e:
                    logger.warning(f"Trend risk gagal: {e}")

                # Missing data risk
                try:
                    missing = self._missing_data_risk(df)
                    dimensions.append(missing)
                    if missing["score"] > 0:
                        for f in missing.get("factors", []):
                            details.append(f)
                except Exception as e:
                    logger.warning(f"Missing data risk gagal: {e}")

                # Overall score (weighted average)
                if dimensions:
                    total_weight = sum(d.get("weight", 1.0) for d in dimensions)
                    if total_weight > 0:
                        overall_score = sum(
                            d["score"] * d.get("weight", 1.0) for d in dimensions
                        ) / total_weight
                    else:
                        overall_score = 0.0
                else:
                    overall_score = 0.0

                overall_score = round(min(100.0, max(0.0, overall_score)), 2)

                # Determine risk level
                if overall_score >= 75:
                    risk_level = "critical"
                elif overall_score >= 50:
                    risk_level = "high"
                elif overall_score >= 25:
                    risk_level = "medium"
                else:
                    risk_level = "low"

                if not details:
                    details.append("Tidak ditemukan faktor risiko signifikan.")

                return self._to_native({
                    "overall_score": overall_score,
                    "dimensions": dimensions,
                    "risk_level": risk_level,
                    "details": details,
                })

            except Exception as e:
                logger.exception("Risk scoring gagal")
                return {
                    "overall_score": 0.0,
                    "dimensions": [],
                    "risk_level": "low",
                    "details": [f"Gagal menghitung risiko: {e}"],
                }

    def _volatility_risk(self, df: pd.DataFrame) -> dict:
        """Assess volatility risk using coefficient of variation."""
        numeric_cols = self._find_numeric_cols(df)
        if not numeric_cols:
            return {
                "name": "Volatility Risk",
                "score": 0.0,
                "weight": 0.3,
                "factors": [],
            }

        high_vol_cols = []
        max_cv = 0.0
        for col in numeric_cols:
            serie = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(serie) < 5:
                continue
            mean = serie.mean()
            std = serie.std()
            if mean == 0 or std == 0:
                continue
            cv = std / abs(mean)
            if cv > 0.5:
                high_vol_cols.append({"column": col, "cv": round(cv, 4)})
            if cv > max_cv:
                max_cv = cv

        score = float(min(100.0, max_cv * 100))
        factors = []
        if high_vol_cols:
            cols_str = ", ".join(h["column"] for h in high_vol_cols[:5])
            factors.append(
                f"Volatilitas tinggi terdeteksi pada kolom: {cols_str}. "
                f"Koefisien variasi > 50% menunjukkan fluktuasi ekstrem."
            )

        return {
            "name": "Volatility Risk",
            "score": round(score, 2),
            "weight": 0.3,
            "factors": factors,
        }

    def _concentration_risk(self, df: pd.DataFrame) -> dict:
        """Assess concentration risk — dependency on few values.

        If text columns with categorical data (e.g., customer, supplier names)
        are present, check if a small number of values dominate.
        """
        text_cols = self._find_text_cols(df)
        if not text_cols:
            return {
                "name": "Concentration Risk",
                "score": 0.0,
                "weight": 0.25,
                "factors": [],
            }

        max_concentration = 0.0
        concentration_factors = []

        for col in text_cols:
            serie = df[col].dropna()
            if len(serie) < 10:
                continue
            unique_count = serie.nunique()
            if unique_count < 2:
                continue

            # Check top-1 and top-3 concentration
            value_counts = serie.value_counts(normalize=True)
            top1_pct = value_counts.iloc[0]
            top3_pct = value_counts.iloc[:3].sum()

            if top1_pct > 0.5:  # One value dominates >50%
                conc_score = top1_pct * 100
                if conc_score > max_concentration:
                    max_concentration = conc_score
                concentration_factors.append(
                    f"Kolom '{col}': nilai '{value_counts.index[0]}' mendominasi "
                    f"{top1_pct:.1%} dari data. Konsentrasi tinggi meningkatkan risiko."
                )
            elif top3_pct > 0.8:  # Top 3 dominate >80%
                conc_score = top3_pct * 80
                if conc_score > max_concentration:
                    max_concentration = conc_score
                tops = [str(v) for v in value_counts.index[:3]]
                concentration_factors.append(
                    f"Kolom '{col}': 3 nilai teratas ({', '.join(tops)}) "
                    f"mencakup {top3_pct:.1%} data. Konsentrasi cukup tinggi."
                )

        score = float(min(100.0, max_concentration))
        return {
            "name": "Concentration Risk",
            "score": round(score, 2),
            "weight": 0.25,
            "factors": concentration_factors,
        }

    def _trend_risk(self, df: pd.DataFrame) -> dict:
        """Assess trend risk — declining patterns over time.

        Requires at least one date column and one numeric column.
        """
        date_cols = self._find_date_cols(df)
        numeric_cols = self._find_numeric_cols(df)

        if not date_cols or not numeric_cols:
            return {
                "name": "Trend Risk",
                "score": 0.0,
                "weight": 0.25,
                "factors": [],
            }

        factors = []
        max_decline = 0.0

        for date_col in date_cols[:2]:
            for num_col in numeric_cols[:3]:
                temp = df[[date_col, num_col]].copy()
                temp[date_col] = pd.to_datetime(temp[date_col], errors="coerce")
                temp[num_col] = pd.to_numeric(temp[num_col], errors="coerce")
                temp = temp.dropna().sort_values(date_col)
                if len(temp) < 5:
                    continue

                # Simple linear regression slope
                x = np.arange(len(temp)).astype(float)
                y = temp[num_col].values.astype(float)
                if y.std() == 0:
                    continue

                slope = np.polyfit(x, y, 1)[0]
                mean_y = y.mean()
                decline_pct = (slope * len(temp) / abs(mean_y)) * 100 if mean_y != 0 else 0

                if decline_pct < -10:  # Declining >10%
                    trend_score = float(min(100.0, abs(decline_pct) * 2))
                    if trend_score > max_decline:
                        max_decline = trend_score
                    factors.append(
                        f"Kolom '{num_col}' menunjukkan tren menurun {abs(decline_pct):.1f}% "
                        f"berdasarkan kolom tanggal '{date_col}'. Ini mengindikasikan "
                        f"risiko penurunan bisnis."
                    )

        score = float(min(100.0, max_decline))
        return {
            "name": "Trend Risk",
            "score": round(score, 2),
            "weight": 0.25,
            "factors": factors,
        }

    def _missing_data_risk(self, df: pd.DataFrame) -> dict:
        """Assess risk from missing/incomplete data."""
        if df.empty:
            return {
                "name": "Missing Data Risk",
                "score": 100.0,
                "weight": 0.2,
                "factors": ["Data kosong — risiko data hilang sangat tinggi."],
            }

        total_cells = df.size
        missing_cells = int(df.isna().sum().sum())
        missing_pct = (missing_cells / total_cells * 100) if total_cells > 0 else 0

        factors = []
        # Per-column missing analysis
        high_missing_cols = []
        for col in df.columns:
            col_missing = int(df[col].isna().sum())
            col_pct = col_missing / len(df) * 100 if len(df) > 0 else 0
            if col_pct > 20:
                high_missing_cols.append(f"'{col}' ({col_pct:.1f}%)")

        if high_missing_cols:
            factors.append(
                f"Kolom dengan data hilang >20%: {', '.join(high_missing_cols[:5])}. "
                f"Data tidak lengkap dapat mengurangi akurasi analisis."
            )
        elif missing_pct > 0:
            factors.append(
                f"Terdapat {missing_cells} sel kosong ({missing_pct:.1f}% dari total). "
                f"Tingkat kelengkapan data cukup baik."
            )
        else:
            factors.append("Tidak ada data yang hilang — kelengkapan data 100%.")

        score = float(min(100.0, missing_pct * 2))
        return {
            "name": "Missing Data Risk",
            "score": round(score, 2),
            "weight": 0.2,
            "factors": factors,
        }
