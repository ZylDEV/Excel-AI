"""Service for conversational Q&A about workbook data."""

import json
import logging
from typing import Any

import pandas as pd

from core.utils.llm_client import LLMClient
from core.utils.excel_reader import get_statistics, detect_column_types

logger = logging.getLogger(__name__)


def process_chat_message(
    message: str,
    workbook_context: list[dict[str, Any]] | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Process a chat message and return an AI reply, optionally with structured data.

    Parameters
    ----------
    message : str
        The user's message.
    workbook_context : list[dict] | None
        Optional list of sheet dicts with keys: name, headers, data.
    api_key : str | None
        Optional API key to use instead of the default from settings.

    Returns
    -------
    dict with keys: reply, data
    """
    # Build the system prompt
    system_prompt = (
        "You are an Excel data assistant with deep expertise in spreadsheets, "
        "data analysis, and business intelligence. You help users understand their "
        "data, answer questions, and provide actionable insights. "
        "Respond conversationally but be precise. "
        "When the user asks a question about their data, use the provided "
        "data summary to give specific, accurate answers."
    )

    # Build the user prompt
    prompt_parts: list[str] = []

    if workbook_context:
        summary_lines = _build_data_summary(workbook_context)
        prompt_parts.extend([
            "I have the following workbook data available:",
            "",
            summary_lines,
            "",
        ])

    prompt_parts.append(f"User question: {message}")

    # Determine if we should ask for structured JSON output
    wants_data = _message_requests_data(message)
    if wants_data:
        prompt_parts.extend([
            "",
            "If the user's question involves extracting or computing data, "
            "respond with a JSON object that has a 'reply' key (your text response) "
            "and a 'data' key (a structured dict of relevant data). "
            "Otherwise, just respond conversationally as text.",
            "",
            "IMPORTANT: Return your response as a JSON object with keys 'reply' and 'data'. "
            'Example: {"reply": "Here is the total...", "data": {"total": 12345}}',
        ])

    prompt = "\n".join(prompt_parts)

    try:
        client = LLMClient(api_key=api_key)

        if wants_data:
            result = client.generate_json(
                prompt=prompt,
                system_prompt=system_prompt,
            )
            reply = result.get("reply", str(result))
            data = result.get("data")
        else:
            reply = client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
            )
            data = None

        return {
            "reply": reply,
            "data": data,
        }
    except Exception as e:
        logger.warning(f"LLM chat failed, using fallback: {e}")
        # Fallback: answer based on data summary directly
        msg_lower = message.lower()

        if workbook_context:
            # Try to find max from data
            try:
                from core.analysis.explainer import DataExplainer
                for sheet in workbook_context:
                    df = _to_dataframe(sheet.get("headers", []), sheet.get("data", []))
                    if not df.empty and len(df.columns) > 0:
                        num_cols = df.select_dtypes(include=["number"]).columns
                        if len(num_cols) > 0:
                            col = num_cols[0]
                            max_val = df[col].max()
                            # Convert numpy types to native Python
                            if hasattr(max_val, "item"):
                                max_val = max_val.item()
                            return {
                                "reply": f"Nilai terbesar di kolom '{col}' adalah {max_val}.",
                                "data": {"column": str(col), "max_value": max_val}
                            }
            except Exception:
                pass

        if workbook_context:
            total_sheets = len(workbook_context)
            total_cols = sum(len(s.get("headers", [])) for s in workbook_context)
            total_rows = sum(len(s.get("data", [])) for s in workbook_context)
            return {
                "reply": f"Data workbook memiliki {total_sheets} sheet, {total_cols} kolom, dan {total_rows} baris. Untuk analisis lebih detail, silakan atur API key AI di Settings.",
                "data": {"sheets": total_sheets, "columns": total_cols, "rows": total_rows}
            }

        return {
            "reply": "Maaf, saya tidak bisa menjawab saat ini karena AI belum dikonfigurasi. Silakan atur API key di Settings untuk mengaktifkan AI.",
            "data": None
        }


def _build_data_summary(workbook_context: list[dict]) -> str:
    """Build a textual summary of the workbook data for the LLM prompt."""
    lines: list[str] = []
    for sheet in workbook_context:
        name = sheet.get("name", "Unnamed")
        headers = sheet.get("headers") or []
        data = sheet.get("data") or []

        # Build a DataFrame for statistics
        df = _to_dataframe(headers, data)

        lines.append(f"--- Sheet: {name} ---")
        lines.append(f"  Dimensions: {len(df)} rows x {len(df.columns)} columns")
        lines.append(f"  Columns: {', '.join(df.columns.tolist())}")

        stats = get_statistics(df)
        detected = detect_column_types(df)

        # Show dtypes
        for col, dtype in detected.items():
            lines.append(f"    - {col} ({dtype})")

        # Numeric hints
        num_stats = stats.get("numeric_stats", {})
        for col, s in num_stats.items():
            lines.append(
                f"    - {col}: range [{s.get('min', '?')}, {s.get('max', '?')}], "
                f"mean={s.get('mean', '?')}"
            )

        # Text hints
        text_stats = stats.get("text_stats", {})
        for col, s in text_stats.items():
            lines.append(
                f"    - {col}: {s.get('unique', '?')} unique values, "
                f"top='{s.get('top', '?')}' ({s.get('top_freq', '?')}x)"
            )

        # Show first 3 data rows as a sample
        sample = df.head(3)
        if not sample.empty:
            lines.append("  Sample rows:")
            for _, row in sample.iterrows():
                row_str = " | ".join(str(v) if v is not None else "" for v in row)
                lines.append(f"    {row_str}")

        lines.append("")

    return "\n".join(lines)


def _to_dataframe(headers: list[str], data: list[list]) -> pd.DataFrame:
    """Convert raw headers + data into a DataFrame."""
    if not headers or not data:
        return pd.DataFrame()
    col_names = [str(h) if h is not None else f"Column_{i}" for i, h in enumerate(headers)]
    df = pd.DataFrame(data, columns=col_names)
    import numpy as np
    df = df.map(lambda x: np.nan if x is None else x)
    # Coerce numeric columns
    for col in df.columns:
        try:
            converted = pd.to_numeric(df[col], errors="coerce")
            if converted.notna().sum() >= max(1, len(df) * 0.5):
                df[col] = converted
        except (ValueError, TypeError):
            pass
    return df


def _message_requests_data(message: str) -> bool:
    """Heuristic: does the message sound like it expects structured data back?"""
    triggers = [
        "total", "sum", "calculate", "average", "count", "number", "how many",
        "what is", "show me", "list", "find", "extract", "filter", "top",
        "maximum", "minimum", "compare", "breakdown", "distribution",
    ]
    msg_lower = message.lower()
    return any(t in msg_lower for t in triggers)
