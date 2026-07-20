"""Fraud detection using Isolation Forest + rule-based detection."""

import logging
import warnings
from collections import Counter
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class FraudDetector:
    """Detects potentially fraudulent transactions/entries using ML + rules.

    Detection methods:
    1. Isolation Forest on numeric columns
    2. Duplicate transaction detection
    3. Unusual timing patterns (if date column exists)
    4. Round number detection (for invoice fraud)
    5. Benford's Law analysis for numeric columns
    """

    @staticmethod
    def _to_native(obj: Any) -> Any:
        """Recursively convert numpy/pandas types to native Python types."""
        if isinstance(obj, dict):
            return {k: FraudDetector._to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [FraudDetector._to_native(v) for v in obj]
        elif isinstance(obj, tuple):
            return tuple(FraudDetector._to_native(v) for v in obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return FraudDetector._to_native(obj.tolist())
        elif isinstance(obj, pd.Timestamp):
            return str(obj)
        elif pd.isna(obj):
            return None
        return obj

    @staticmethod
    def _find_numeric_cols(df: pd.DataFrame) -> list[str]:
        """Find suitable numeric columns for analysis."""
        return df.select_dtypes(include=[np.number]).columns.tolist()

    @staticmethod
    def _find_date_cols(df: pd.DataFrame) -> list[str]:
        """Find date/datetime columns."""
        return df.select_dtypes(include=["datetime64"]).columns.tolist()

    def detect(self, df: pd.DataFrame) -> dict:
        """Run all fraud detection methods against the data.

        Parameters
        ----------
        df : pd.DataFrame
            The input data to analyse.

        Returns
        -------
        dict with keys:
            - anomalies : list of {column, value, score, description, severity}
            - suspicious_patterns : list of {pattern, description, count, examples}
            - fraud_score : float (0-100)
            - summary : str
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            warnings.simplefilter("ignore", UserWarning)

            try:
                if df.empty:
                    return {
                        "anomalies": [],
                        "suspicious_patterns": [],
                        "fraud_score": 0.0,
                        "summary": "Data kosong, tidak dapat mendeteksi fraud.",
                    }

                numeric_cols = self._find_numeric_cols(df)
                date_cols = self._find_date_cols(df)

                anomalies: list[dict] = []
                suspicious_patterns: list[dict] = []

                # 1. Isolation Forest
                if numeric_cols:
                    try:
                        iso_anomalies = self._isolation_forest_anomalies(df, numeric_cols)
                        anomalies.extend(iso_anomalies)
                    except Exception as e:
                        logger.warning(f"Isolation Forest gagal: {e}")

                # 2. Duplicate detection
                try:
                    dupes = self._detect_duplicates(df)
                    if dupes:
                        suspicious_patterns.append({
                            "pattern": "Duplicate Rows",
                            "description": f"Ditemukan {len(dupes)} baris yang identik atau hampir identik, "
                                           f"indikasi duplikasi data.",
                            "count": len(dupes),
                            "examples": dupes[:5],
                        })
                except Exception as e:
                    logger.warning(f"Duplicate detection gagal: {e}")

                # 3. Unusual timing patterns (if date cols exist)
                if date_cols:
                    try:
                        timing = self._detect_timing_patterns(df, date_cols)
                        if timing:
                            suspicious_patterns.append({
                                "pattern": "Unusual Timing Patterns",
                                "description": timing["description"],
                                "count": timing["count"],
                                "examples": timing["examples"],
                            })
                    except Exception as e:
                        logger.warning(f"Timing detection gagal: {e}")

                # 4. Round number detection
                if numeric_cols:
                    try:
                        round_anomalies = self._detect_round_numbers(df, numeric_cols)
                        if round_anomalies:
                            suspicious_patterns.append({
                                "pattern": "Round Number Anomalies",
                                "description": "Sejumlah nilai adalah angka bulat (rounded), "
                                               "indikasi fraud invoice.",
                                "count": len(round_anomalies),
                                "examples": round_anomalies[:5],
                            })
                    except Exception as e:
                        logger.warning(f"Round number detection gagal: {e}")

                # 5. Benford's Law analysis
                benford_findings = []
                for col in numeric_cols[:3]:  # Limit to first 3 numeric columns
                    try:
                        bf = self._benford_analysis(df, col)
                        if bf and bf.get("anomaly_detected"):
                            benford_findings.append(bf)
                    except Exception as e:
                        logger.warning(f"Benford analysis gagal untuk {col}: {e}")

                for bf in benford_findings:
                    suspicious_patterns.append({
                        "pattern": f"Benford's Law Deviation — {bf['column']}",
                        "description": bf["description"],
                        "count": bf.get("deviant_digits", 0),
                        "examples": bf.get("examples", []),
                    })

                # Calculate fraud score
                anomaly_count = len(anomalies)
                pattern_count = len([p for p in suspicious_patterns if p["count"] > 0])
                fraud_score = float(min(100.0, (anomaly_count * 5) + (pattern_count * 15)))

                # Build summary
                parts = []
                if anomaly_count > 0:
                    parts.append(f"Terdeteksi {anomaly_count} anomali numerik.")
                if suspicious_patterns:
                    for p in suspicious_patterns:
                        parts.append(f"{p['pattern']}: {p['description']}")
                if not parts:
                    parts.append("Tidak ditemukan indikasi fraud yang signifikan.")
                summary = " ".join(parts)

                return self._to_native({
                    "anomalies": anomalies,
                    "suspicious_patterns": suspicious_patterns,
                    "fraud_score": round(fraud_score, 2),
                    "summary": summary,
                })

            except Exception as e:
                logger.exception("Fraud detection gagal")
                return {
                    "anomalies": [],
                    "suspicious_patterns": [],
                    "fraud_score": 0.0,
                    "summary": f"Gagal mendeteksi fraud: {e}",
                }

    def _isolation_forest_anomalies(
        self, df: pd.DataFrame, cols: list[str]
    ) -> list[dict]:
        """Run Isolation Forest on numeric columns."""
        from sklearn.ensemble import IsolationForest

        data = df[cols].copy()
        # Drop rows that are all NaN
        clean = data.dropna(how="all")
        if len(clean) < 5:
            # Too few rows for Isolation Forest
            return self._simple_stat_anomalies(df, cols)

        # Fill remaining NaNs with column median
        clean = clean.fillna(clean.median())

        model = IsolationForest(
            n_estimators=100,
            contamination="auto",
            random_state=42,
        )
        preds = model.fit_predict(clean)
        scores = model.score_samples(clean)

        # Map to original index
        anomaly_indices = clean.index[preds == -1].tolist()

        results = []
        for idx in anomaly_indices:
            row = clean.loc[idx]
            # Find the most anomalous column for this row
            col_means = clean.mean()
            col_deviations = (row - col_means).abs()
            worst_col = col_deviations.idxmax()
            worst_val = row[worst_col]
            score = float(scores[clean.index.get_loc(idx)])
            # Normalise score to 0-1 (Isolation Forest scores are negative for anomalies)
            norm_score = min(1.0, max(0.0, 1.0 - abs(score)))

            results.append({
                "column": worst_col,
                "value": self._to_native(worst_val),
                "score": round(norm_score, 4),
                "description": f"Nilai {worst_val} pada kolom '{worst_col}' "
                               f"terdeteksi sebagai anomali oleh Isolation Forest.",
                "severity": "high" if norm_score > 0.7 else "medium",
            })

        return results[:20]  # Limit to top 20

    def _simple_stat_anomalies(self, df: pd.DataFrame, cols: list[str]) -> list[dict]:
        """Fallback: use Z-score based anomaly detection for small datasets."""
        results = []
        for col in cols:
            serie = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(serie) < 3:
                continue
            mean = serie.mean()
            std = serie.std()
            if std == 0:
                continue
            z_scores = ((serie - mean) / std).abs()
            outliers = z_scores[z_scores > 2.5]
            for idx in outliers.index:
                results.append({
                    "column": col,
                    "value": self._to_native(serie.loc[idx]),
                    "score": round(min(1.0, float(outliers.loc[idx]) / 5.0), 4),
                    "description": f"Nilai {serie.loc[idx]} pada kolom '{col}' "
                                   f"berjarak {outliers.loc[idx]:.1f} standar deviasi dari rata-rata.",
                    "severity": "high" if outliers.loc[idx] > 3.5 else "medium",
                })
        return results

    def _benford_analysis(self, df: pd.DataFrame, col: str) -> dict | None:
        """Perform Benford's Law analysis on a numeric column.

        Benford's Law states that in many naturally occurring datasets,
        the first digit follows a logarithmic distribution. Deviations
        may indicate fraud.
        """
        serie = pd.to_numeric(df[col], errors="coerce").dropna()
        # Remove zeros and negative values
        serie = serie[serie > 0]
        if len(serie) < 50:
            return None  # Not enough data for Benford

        first_digits = serie.astype(str).str[0]
        first_digits = first_digits[first_digits.str.isdigit()]
        if len(first_digits) < 50:
            return None

        digit_counts = first_digits.value_counts(normalize=True).sort_index()
        expected = {
            "1": 0.301, "2": 0.176, "3": 0.125, "4": 0.097,
            "5": 0.079, "6": 0.067, "7": 0.058, "8": 0.051, "9": 0.046,
        }

        deviations = []
        for d in "123456789":
            actual = digit_counts.get(d, 0.0)
            exp = expected[d]
            dev = abs(actual - exp)
            if dev > 0.05:
                deviations.append({"digit": d, "expected": exp, "actual": round(actual, 4), "deviation": round(dev, 4)})

        if not deviations:
            return None

        # Build example values with deviant first digits
        examples = []
        for d_info in deviations[:3]:
            matching = serie[first_digits == d_info["digit"]]
            if not matching.empty:
                examples.extend([self._to_native(v) for v in matching.head(3).tolist()])

        return {
            "column": col,
            "deviant_digits": len(deviations),
            "description": f"Distribusi digit pertama pada kolom '{col}' "
                           f"menyimpang dari Benford's Law ({len(deviations)} digit melenceng). "
                           f"Ini bisa mengindikasikan manipulasi data.",
            "details": self._to_native(deviations),
            "examples": examples[:5],
            "anomaly_detected": True,
        }

    def _detect_duplicates(self, df: pd.DataFrame) -> list[dict]:
        """Detect duplicate or near-duplicate rows."""
        if df.empty:
            return []

        # Exact duplicates
        exact_dupes = df[df.duplicated(keep=False)]
        if exact_dupes.empty:
            return []

        # Group to get duplicate sets
        grouped = exact_dupes.groupby(list(df.columns)).size().reset_index(name="count")
        results = []
        for _, row in grouped.iterrows():
            results.append({
                "duplicate_count": int(row["count"]),
                "values": self._to_native(dict(row.drop("count"))),
            })
        return results

    def _detect_timing_patterns(
        self, df: pd.DataFrame, date_cols: list[str]
    ) -> dict | None:
        """Detect unusual timing patterns (e.g., late night entries, weekends)."""
        for col in date_cols[:2]:  # Check first 2 date columns
            serie = pd.to_datetime(df[col], errors="coerce").dropna()
            if len(serie) < 5:
                continue

            # Check for weekend entries
            weekend_mask = serie.dt.dayofweek >= 5
            weekend_count = weekend_mask.sum()
            weekend_examples = serie[weekend_mask].head(5).tolist()

            # Check for late night entries (if time component exists)
            has_time = serie.dt.time.nunique() > 1
            late_night_count = 0
            late_night_examples = []
            if has_time:
                late_mask = (serie.dt.hour >= 22) | (serie.dt.hour <= 4)
                late_night_count = int(late_mask.sum())
                late_night_examples = [str(s) for s in serie[late_mask].head(5).tolist()]

            if weekend_count > 0 or late_night_count > 0:
                desc_parts = []
                if weekend_count > 0:
                    desc_parts.append(f"{weekend_count} transaksi terjadi pada akhir pekan")
                if late_night_count > 0:
                    desc_parts.append(f"{late_night_count} transaksi terjadi pada jam tidak biasa (22:00-04:00)")
                if not desc_parts:
                    continue

                examples = []
                if weekend_examples:
                    examples.extend([str(s) for s in weekend_examples])
                if late_night_examples:
                    examples.extend(late_night_examples)

                return {
                    "description": f"Kolom '{col}': {'; '.join(desc_parts)}. "
                                   f"Pola waktu tidak biasa memerlukan investigasi lebih lanjut.",
                    "count": int(weekend_count + late_night_count),
                    "examples": examples[:5],
                }
        return None

    def _detect_round_numbers(
        self, df: pd.DataFrame, cols: list[str]
    ) -> list[dict]:
        """Detect suspicious round numbers that may indicate invoice fraud.

        Looks for values that are exact multiples of common round thresholds
        (e.g., 100, 500, 1000, 10000).
        """
        results = []
        round_thresholds = [100, 500, 1000, 5000, 10000, 50000, 100000]

        for col in cols:
            serie = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(serie) < 5:
                continue

            for threshold in round_thresholds:
                mask = (serie % threshold == 0) & (serie >= threshold)
                count = mask.sum()
                if count >= 3:  # At least 3 values at this threshold
                    examples = serie[mask].head(5).tolist()
                    results.append({
                        "column": col,
                        "threshold": threshold,
                        "count": int(count),
                        "examples": self._to_native(examples),
                    })

        return results
