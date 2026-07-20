"""Data quality analysis for AI Data Cleaner."""

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataQualityAnalyzer:
    """Analyses a DataFrame for quality issues and applies fixes."""

    def analyze(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        """Run all quality checks and return a list of identified issues.

        Each issue dict contains:
            type: str          — issue category
            severity: str      — "low" | "medium" | "high"
            column: str | None — affected column name
            details: dict      — additional metadata
            suggestion: str    — suggested fix label
        """
        issues: list[dict[str, Any]] = []

        issues.extend(self._check_missing_values(df))
        issues.extend(self._check_duplicates(df))
        issues.extend(self._check_outliers(df))
        issues.extend(self._check_invalid_data(df))
        issues.extend(self._check_constant_columns(df))
        issues.extend(self._check_high_cardinality(df))

        return issues

    def clean(self, df: pd.DataFrame, fixes: list[str]) -> pd.DataFrame:
        """Apply a list of fixes to the DataFrame.

        Supported fix labels (case-insensitive):
            - "remove_duplicates"
            - "fill_missing_mean" / "fill_missing_median" / "fill_missing_mode"
            - "drop_missing_high" — drop columns with >50 % missing
            - "remove_outliers_iqr"
            - "strip_whitespace"
            - "drop_constant_columns"
        """
        result = df.copy()
        applied: list[str] = []

        for fix in fixes:
            label = fix.strip().lower()

            if label == "remove_duplicates":
                before = len(result)
                result = result.drop_duplicates()
                after = len(result)
                if before > after:
                    applied.append(f"remove_duplicates: removed {before - after} row(s)")

            elif label == "fill_missing_mean":
                num_cols = result.select_dtypes(include=[np.number]).columns
                for col in num_cols:
                    if result[col].isna().any():
                        result[col] = result[col].fillna(result[col].mean())
                        applied.append(f"fill_missing_mean: {col}")
                # Also attempt coercion for object columns that are numeric-looking
                for col in result.select_dtypes(include=["object"]).columns:
                    if result[col].isna().any():
                        coerced = pd.to_numeric(result[col], errors="coerce")
                        if coerced.notna().sum() > 0:
                            mean_val = coerced.mean()
                            result[col] = result[col].map(
                                lambda x: mean_val if pd.isna(x) else x
                            )
                            applied.append(f"fill_missing_mean: {col} (coerced)")

            elif label == "fill_missing_median":
                num_cols = result.select_dtypes(include=[np.number]).columns
                for col in num_cols:
                    if result[col].isna().any():
                        result[col] = result[col].fillna(result[col].median())
                        applied.append(f"fill_missing_median: {col}")

            elif label == "fill_missing_mode":
                for col in result.columns:
                    if result[col].isna().any():
                        mode_vals = result[col].mode()
                        if not mode_vals.empty:
                            result[col] = result[col].fillna(mode_vals.iloc[0])
                            applied.append(f"fill_missing_mode: {col}")

            elif label == "drop_missing_high":
                threshold = 0.5
                for col in result.columns:
                    if result[col].isna().mean() > threshold:
                        result = result.drop(columns=[col])
                        applied.append(f"drop_missing_high: {col}")

            elif label == "remove_outliers_iqr":
                num_cols = result.select_dtypes(include=[np.number]).columns
                before_len = len(result)
                mask = pd.Series(True, index=result.index)
                for col in num_cols:
                    q1 = result[col].quantile(0.25)
                    q3 = result[col].quantile(0.75)
                    iqr = q3 - q1
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
                    col_mask = (result[col] >= lower) & (result[col] <= upper)
                    mask = mask & col_mask
                result = result[mask].reset_index(drop=True)
                after_len = len(result)
                if before_len > after_len:
                    applied.append(f"remove_outliers_iqr: removed {before_len - after_len} row(s)")

            elif label == "strip_whitespace":
                for col in result.select_dtypes(include=["object"]).columns:
                    result[col] = result[col].astype(str).str.strip()
                applied.append("strip_whitespace")

            elif label == "drop_constant_columns":
                for col in result.columns:
                    if result[col].nunique(dropna=True) <= 1:
                        result = result.drop(columns=[col])
                        applied.append(f"drop_constant_columns: {col}")

            else:
                logger.warning(f"Unknown fix label: {fix}")

        logger.info(f"Cleaning applied: {applied}")
        return result

    # ------------------------------------------------------------------
    # Internal check methods
    # ------------------------------------------------------------------

    def _check_missing_values(self, df: pd.DataFrame) -> list[dict]:
        issues: list[dict] = []
        total = len(df)
        for col in df.columns:
            count = int(df[col].isna().sum())
            if count == 0:
                continue
            pct = round(count / total * 100, 2)
            severity = "low"
            if pct > 50:
                severity = "high"
            elif pct > 20:
                severity = "medium"
            issues.append(
                {
                    "type": "missing_values",
                    "severity": severity,
                    "column": col,
                    "details": {"missing_count": count, "missing_percentage": pct, "total_rows": total},
                    "suggestion": f"Isi atau hapus nilai kosong di kolom '{col}' ({pct}% kosong)"
                }
            )
        return issues

    def _check_duplicates(self, df: pd.DataFrame) -> list[dict]:
        if df.empty:
            return []
        dup_count = int(df.duplicated().sum())
        if dup_count == 0:
            return []
        return [
            {
                "type": "duplicates",
                "severity": "medium" if dup_count > len(df) * 0.05 else "low",
                "column": None,
                "details": {"duplicate_rows": dup_count, "total_rows": len(df)},
                "suggestion": f"Hapus {dup_count} baris duplikat"
            }
        ]

    def _check_outliers(self, df: pd.DataFrame) -> list[dict]:
        issues: list[dict] = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            clean = df[col].dropna()
            if len(clean) < 10:
                continue
            q1 = clean.quantile(0.25)
            q3 = clean.quantile(0.75)
            iqr = q3 - q1
            if iqr == 0:
                continue
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outliers = clean[(clean < lower) | (clean > upper)]
            count = len(outliers)
            if count == 0:
                continue
            pct = round(count / len(clean) * 100, 2)
            severity = "low"
            if pct > 10:
                severity = "high"
            elif pct > 5:
                severity = "medium"
            issues.append(
                {
                    "type": "outliers",
                    "severity": severity,
                    "column": col,
                    "details": {
                        "outlier_count": count,
                        "outlier_percentage": pct,
                        "lower_bound": round(lower, 4),
                        "upper_bound": round(upper, 4),
                    },
                    "suggestion": f"Periksa {count} pencilan di kolom '{col}' ({pct}% dari nilai)"
                }
            )
        return issues

    def _check_invalid_data(self, df: pd.DataFrame) -> list[dict]:
        issues: list[dict] = []

        for col in df.columns:
            non_null = df[col].dropna()

            # Check for invalid dates
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                continue  # Already parsed; trust pandas

            # Check for negative values in numeric columns
            if pd.api.types.is_numeric_dtype(df[col]):
                neg = non_null[non_null < 0]
                if len(neg) > 0:
                    neg_pct = round(len(neg) / len(non_null) * 100, 2)
                    issues.append(
                        {
                            "type": "invalid_data",
                            "severity": "medium" if neg_pct > 5 else "low",
                            "column": col,
                            "details": {"negative_count": int(len(neg)), "negative_percentage": neg_pct},
                            "suggestion": f"Periksa {len(neg)} nilai negatif di kolom '{col}'"
                        }
                    )

            # Check for text columns containing error strings
            if df[col].dtype == object:
                error_patterns = ["#REF!", "#DIV/0!", "#N/A", "#VALUE!", "#####", "#NULL!", "#NUM!", "#NAME?"]
                for pattern in error_patterns:
                    count = non_null.astype(str).str.contains(pattern, na=False).sum()
                    if count > 0:
                        issues.append(
                            {
                                "type": "invalid_data",
                                "severity": "high",
                                "column": col,
                                "details": {"error_pattern": pattern, "count": int(count)},
                                "suggestion": f"Perbaiki {count} nilai '{pattern}' di kolom '{col}'"
                            }
                        )

        return issues

    def _check_constant_columns(self, df: pd.DataFrame) -> list[dict]:
        issues: list[dict] = []
        for col in df.columns:
            if df[col].nunique(dropna=True) <= 1:
                issues.append(
                    {
                        "type": "constant_column",
                        "severity": "low",
                        "column": col,
                        "details": {"unique_values": int(df[col].nunique(dropna=True))},
                        "suggestion": f"Hapus kolom konstan '{col}' (nilai tunggal)"
                    }
                )
        return issues

    def _check_high_cardinality(self, df: pd.DataFrame) -> list[dict]:
        issues: list[dict] = []
        total = len(df)
        for col in df.select_dtypes(include=["object"]).columns:
            nunique = df[col].nunique()
            if nunique > max(50, total * 0.5):
                issues.append(
                    {
                        "type": "high_cardinality",
                        "severity": "low",
                        "column": col,
                        "details": {"unique_count": int(nunique), "total_rows": total},
                        "suggestion": f"Pertimbangkan mengelompokkan kolom kardinalitas tinggi '{col}' ({nunique} unik)"
                    }
                )
        return issues
