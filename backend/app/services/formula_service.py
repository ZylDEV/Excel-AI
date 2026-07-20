"""Service for generating and explaining Excel formulas via LLM."""

import json
import logging
from typing import Any

from core.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)


def generate_formula(
    description: str,
    sheet_context: str = "",
    api_key: str | None = None,
) -> dict[str, Any]:
    """Generate an Excel formula from a natural-language description.

    Parameters
    ----------
    description : str
        Natural language description of the formula needed.
    sheet_context : str, optional
        Context about the sheet structure / column names.
    api_key : str | None
        Optional API key to use instead of the default from settings.

    Returns
    -------
    dict with keys: formula, explanation, example
    """
    prompt_parts = [
        "You are an Excel formula expert. Generate a working Excel formula for the following request.",
        "",
        f"Request: {description}",
    ]
    if sheet_context:
        prompt_parts.extend(["", "Sheet context:", sheet_context])

    prompt_parts.extend([
        "",
        "Respond with a JSON object containing exactly these keys:",
        '  - "formula": the Excel formula string (start with =)',
        '  - "explanation": a brief plain-English explanation of how the formula works',
        '  - "example": a short example showing the formula in use with hypothetical data',
        "",
        "Example response format:",
        '{"formula": "=SUMIF(A2:A10,\\">0\\",B2:B10)", "explanation": "Sums values in B2:B10 where A2:A10 > 0", "example": "With A2:A10 containing sales regions and B2:B10 containing amounts, this sums all amounts for regions with positive values."}',
    ])

    prompt = "\n".join(prompt_parts)

    try:
        client = LLMClient(api_key=api_key)
        result = client.generate_json(
            prompt=prompt,
            system_prompt="You are an Excel formula expert. Always return valid JSON with keys: formula, explanation, example.",
        )
        return {
            "formula": result.get("formula", "=TEXT(1,0)"),
            "explanation": result.get("explanation", "Could not generate explanation."),
            "example": result.get("example", ""),
        }
    except Exception as e:
        logger.warning(f"LLM formula generation failed, using rule-based fallback: {e}")
        # Rule-based fallback for common formula patterns
        desc_lower = description.lower()
        formula = "=TEXT(1,0)"
        explanation = f"Could not connect to AI. Please set up your API key in Settings."
        example = ""

        if "sum" in desc_lower or "total" in desc_lower or "jumlah" in desc_lower:
            formula = "=SUM(A2:A100)"
            explanation = "Menjumlahkan semua nilai dalam range A2 sampai A100"
            example = "Gunakan =SUM(A2:A100) untuk menjumlahkan data di kolom A"
        elif "average" in desc_lower or "rata" in desc_lower or "mean" in desc_lower:
            formula = "=AVERAGE(A2:A100)"
            explanation = "Menghitung rata-rata dari nilai dalam range A2 sampai A100"
            example = "Gunakan =AVERAGE(A2:A100) untuk menghitung rata-rata data di kolom A"
        elif "count" in desc_lower or "hitung" in desc_lower or "jumlah data" in desc_lower:
            formula = "=COUNT(A2:A100)"
            explanation = "Menghitung jumlah sel yang berisi angka dalam range A2 sampai A100"
            example = "Gunakan =COUNT(A2:A100) untuk menghitung berapa banyak data numerik di kolom A"
        elif "max" in desc_lower or "terbesar" in desc_lower or "maksimum" in desc_lower:
            formula = "=MAX(A2:A100)"
            explanation = "Mencari nilai terbesar dalam range A2 sampai A100"
            example = "Gunakan =MAX(A2:A100) untuk mencari nilai tertinggi di kolom A"
        elif "min" in desc_lower or "terkecil" in desc_lower or "minimum" in desc_lower:
            formula = "=MIN(A2:A100)"
            explanation = "Mencari nilai terkecil dalam range A2 sampai A100"
            example = "Gunakan =MIN(A2:A100) untuk mencari nilai terendah di kolom A"
        elif "if" in desc_lower or "jika" in desc_lower or "conditional" in desc_lower:
            formula = '=IF(A2>100,"High","Low")'
            explanation = "Mengembalikan 'High' jika nilai di A2 lebih dari 100, selain itu 'Low'"
            example = 'Gunakan =IF(A2>100,"High","Low") untuk mengkategorikan data'
        elif "vlookup" in desc_lower or "cari" in desc_lower:
            formula = "=VLOOKUP(E2,A2:B100,2,FALSE)"
            explanation = "Mencari nilai E2 di kolom A dan mengembalikan nilai yang sesuai dari kolom B"
            example = "Gunakan =VLOOKUP(E2,A2:B100,2,FALSE) untuk mencari data berdasarkan ID"

        return {
            "formula": formula,
            "explanation": explanation,
            "example": example,
        }


def explain_formula(
    formula: str,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Explain an Excel formula in plain English.

    Parameters
    ----------
    formula : str
        The Excel formula to explain.
    api_key : str | None
        Optional API key to use instead of the default from settings.

    Returns
    -------
    dict with keys: formula, explanation, example
    """
    prompt = f"""You are an Excel formula expert. Explain the following Excel formula in plain English.

Formula: {formula}

Respond with a JSON object containing exactly these keys:
  - "formula": the original formula string
  - "explanation": a step-by-step plain-English explanation of what the formula does
  - "example": a concrete example with hypothetical data showing how the formula works

Example response format:
{{"formula": "=SUMIF(A2:A10,\\">0\\",B2:B10)", "explanation": "This formula sums values in B2:B10 where A2:A10 > 0", "example": "If A2:A10 contains sales amounts and B2:B10 contains profits, this sums profits only for positive sales."}}
"""

    try:
        client = LLMClient(api_key=api_key)
        result = client.generate_json(
            prompt=prompt,
            system_prompt="You are an Excel formula expert. Always return valid JSON with keys: formula, explanation, example.",
        )
        return {
            "formula": result.get("formula", formula),
            "explanation": result.get("explanation", "Could not generate explanation."),
            "example": result.get("example", ""),
        }
    except Exception as e:
        logger.warning(f"LLM formula explanation failed, using rule-based fallback: {e}")
        # Rule-based fallback
        formula_upper = formula.upper()
        parts = []

        if "SUM" in formula_upper:
            parts.append("Fungsi SUM menjumlahkan nilai-nilai angka dalam range yang ditentukan.")
        if "AVERAGE" in formula_upper:
            parts.append("Fungsi AVERAGE menghitung rata-rata dari nilai-nilai angka.")
        if "IF" in formula_upper:
            parts.append("Fungsi IF melakukan pengecekan kondisi dan mengembalikan nilai berbeda tergantung hasilnya.")
        if "VLOOKUP" in formula_upper:
            parts.append("Fungsi VLOOKUP mencari nilai di kolom pertama suatu range dan mengembalikan nilai dari kolom lain di baris yang sama.")
        if "COUNT" in formula_upper:
            parts.append("Fungsi COUNT menghitung jumlah sel yang berisi angka.")
        if "MAX" in formula_upper:
            parts.append("Fungsi MAX mencari nilai terbesar.")
        if "MIN" in formula_upper:
            parts.append("Fungsi MIN mencari nilai terkecil.")

        if not parts:
            parts.append(f"Fungsi ini menggunakan {formula.split('(')[0]} untuk memproses data Excel.")

        return {
            "formula": formula,
            "explanation": " ".join(parts),
            "example": "Aktifkan AI dengan mengatur API key untuk penjelasan yang lebih detail.",
        }
