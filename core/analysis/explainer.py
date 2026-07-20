"""Data explanation and insight generation."""

import logging
from typing import Any

import numpy as np
import pandas as pd

from core.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)


class DataExplainer:
    """Generates data-driven insights, summary statistics, and LLM-powered explanations."""

    def get_insights(self, df: pd.DataFrame) -> list[str]:
        """Generate a list of data-driven insight strings."""
        insights: list[str] = []
        total = len(df)

        if df.empty:
            return ["The dataset is empty."]

        # Basic dimensions
        insights.append(f"The dataset contains {total} rows and {len(df.columns)} columns.")

        # Missing values
        total_missing = int(df.isna().sum().sum())
        if total_missing > 0:
            pct = round(total_missing / (total * len(df.columns)) * 100, 1)
            insights.append(f"There are {total_missing} missing values overall ({pct}% of all cells).")
        else:
            insights.append("The dataset has no missing values.")

        # Duplicates
        dup_count = int(df.duplicated().sum())
        if dup_count > 0:
            pct = round(dup_count / total * 100, 1)
            insights.append(f"Found {dup_count} duplicate row(s) ({pct}% of data).")

        # Numeric column insights
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            clean = df[col].dropna()
            if len(clean) == 0:
                continue
            insights.append(
                f"'{col}' ranges from {clean.min():.2f} to {clean.max():.2f} "
                f"(mean: {clean.mean():.2f}, median: {clean.median():.2f})."
            )
            # Skewness hint
            skew = clean.skew()
            if abs(skew) > 1:
                direction = "right (positively)" if skew > 0 else "left (negatively)"
                insights.append(
                    f"'{col}' is skewed to the {direction} (skewness: {skew:.2f})."
                )

        # Text column insights
        text_cols = df.select_dtypes(include=["object"]).columns
        for col in text_cols:
            nunique = df[col].nunique()
            if nunique <= 1:
                insights.append(f"'{col}' has only one unique value.")
            elif nunique < 20:
                top = df[col].mode().iloc[0] if not df[col].mode().empty else "N/A"
                insights.append(
                    f"'{col}' has {nunique} unique values (most common: '{top}')."
                )
            else:
                insights.append(
                    f"'{col}' has {nunique} unique values (high cardinality)."
                )

        # Date column insights
        date_cols = df.select_dtypes(include=["datetime64"]).columns
        for col in date_cols:
            clean = df[col].dropna()
            if len(clean) > 0:
                insights.append(
                    f"'{col}' spans from {clean.min().strftime('%Y-%m-%d')} to "
                    f"{clean.max().strftime('%Y-%m-%d')}."
                )

        return insights

    def get_summary_statistics(self, df: pd.DataFrame) -> dict[str, Any]:
        """Return comprehensive summary statistics."""
        summary: dict[str, Any] = {
            "shape": {"rows": len(df), "columns": len(df.columns)},
            "column_names": list(df.columns),
            "dtypes": {col: str(df[col].dtype) for col in df.columns},
            "missing": {},
            "memory_usage_bytes": int(df.memory_usage(deep=True).sum()),
        }

        # Per-column missing
        for col in df.columns:
            missing_count = int(df[col].isna().sum())
            missing_pct = round(missing_count / len(df) * 100, 2) if len(df) > 0 else 0
            summary["missing"][col] = {
                "count": missing_count,
                "percentage": missing_pct,
            }

        # Numeric statistics
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            desc = df[numeric_cols].describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95])
            stats = desc.to_dict()
            summary["numeric"] = {
                col: {
                    "count": int(v.get("count", 0)),
                    "mean": _safe_float(v.get("mean")),
                    "std": _safe_float(v.get("std")),
                    "min": _safe_float(v.get("min")),
                    "5%": _safe_float(v.get("5%")),
                    "25%": _safe_float(v.get("25%")),
                    "50%": _safe_float(v.get("50%")),
                    "75%": _safe_float(v.get("75%")),
                    "95%": _safe_float(v.get("95%")),
                    "max": _safe_float(v.get("max")),
                    "skew": _safe_float(df[col].skew()),
                    "kurtosis": _safe_float(df[col].kurtosis()),
                }
                for col, v in stats.items()
            }
        else:
            summary["numeric"] = {}

        # Categorical statistics
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        if cat_cols:
            summary["categorical"] = {}
            for col in cat_cols:
                val_counts = df[col].value_counts(dropna=False).head(10)
                top_items = [
                    {"value": str(k), "count": int(v)}
                    for k, v in val_counts.items()
                ]
                summary["categorical"][col] = {
                    "unique_count": int(df[col].nunique()),
                    "top_10": top_items,
                    "missing_count": int(df[col].isna().sum()),
                }
        else:
            summary["categorical"] = {}

        # Correlation matrix for numeric columns (if ≥ 2)
        if len(numeric_cols) >= 2:
            corr = df[numeric_cols].corr().round(4)
            summary["correlation"] = corr.to_dict()
        else:
            summary["correlation"] = {}

        return summary

    def generate_explanation(self, df: pd.DataFrame, question: str = "", api_key: str | None = None) -> str:
        """Use the LLM to generate a natural-language explanation of the data."""
        # Build a compact summary for the prompt
        summary = self.get_summary_statistics(df)
        insights = self.get_insights(df)

        numeric_preview = ""
        if summary.get("numeric"):
            for col, stats in summary["numeric"].items():
                numeric_preview += (
                    f"  - {col}: count={stats['count']}, mean={stats['mean']}, "
                    f"min={stats['min']}, max={stats['max']}, std={stats['std']}\n"
                )

        cat_preview = ""
        if summary.get("categorical"):
            for col, stats in summary["categorical"].items():
                top_str = ", ".join(
                    f"{t['value']} ({t['count']})" for t in stats["top_10"][:5]
                )
                cat_preview += f"  - {col}: {stats['unique_count']} unique, top: {top_str}\n"

        columns_detail = "\n".join(
            f"  - {col} ({dtype})"
            for col, dtype in summary["dtypes"].items()
        )

        prompt_parts = [
            "You are a data analyst. Explain the following dataset to a business user.",
            "",
            "## Dataset Overview",
            f"- Rows: {summary['shape']['rows']}",
            f"- Columns: {summary['shape']['columns']}",
            "",
            "## Columns",
            columns_detail,
            "",
            "## Key Insights",
        ]
        for ins in insights:
            prompt_parts.append(f"- {ins}")

        if numeric_preview:
            prompt_parts.extend(["", "## Numeric Columns Summary", numeric_preview.strip()])
        if cat_preview:
            prompt_parts.extend(["", "## Categorical Columns Summary", cat_preview.strip()])

        # Show a sample of data
        sample = df.head(5).to_string()
        prompt_parts.extend(["", "## Sample Data (first 5 rows)", sample])

        if question:
            prompt_parts.extend(
                [
                    "",
                    "## User Question",
                    f"The user asks: {question}",
                    "Please answer this question directly based on the data provided.",
                ]
            )
        else:
            prompt_parts.extend(
                [
                    "",
                    "Please provide:",
                    "1. A brief overview of what this dataset contains",
                    "2. Key patterns, trends, or anomalies",
                    "3. Any recommendations or next steps",
                ]
            )

        prompt = "\n".join(prompt_parts)

        try:
            client = LLMClient(api_key=api_key)
            return client.generate(
                prompt=prompt,
                system_prompt="You are a helpful data analyst. Provide clear, concise explanations suitable for business users. Avoid excessive technical jargon.",
            )
        except Exception as e:
            logger.error(f"LLM explanation failed: {e}")
            return (
                "I was unable to generate an LLM-powered explanation. "
                "Here are the key observations from the data:\n\n"
                + "\n".join(f"- {ins}" for ins in insights)
            )


def _safe_float(val: Any) -> float | None:
    """Convert a value to float, returning None if not possible."""
    if val is None:
        return None
    try:
        f = float(val)
        return None if np.isnan(f) or np.isinf(f) else round(f, 4)
    except (ValueError, TypeError):
        return None
