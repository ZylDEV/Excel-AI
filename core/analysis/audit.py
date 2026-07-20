"""Basic workbook audit."""

import logging
import re
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class WorkbookAuditor:
    """Audits a workbook (multiple sheets) for structural and data issues."""

    def audit(self, sheets_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Run audit checks on each sheet.

        Parameters
        ----------
        sheets_data : list[dict]
            Each dict must have:
                - name : str            – sheet name
                - headers : list[str]   – column headers
                - data : list[list]     – row data

        Returns
        -------
        list[dict]  Each issue has:
            severity, category, description, location, suggestion
        """
        issues: list[dict[str, Any]] = []

        if not sheets_data:
            issues.append(self._issue("high", "empty_workbook", "Workbook tidak memiliki sheet", "N/A", "Tambahkan setidaknya satu sheet dengan data"))
            return issues

        for sheet in sheets_data:
            sheet_name = sheet.get("name", "Tanpa Nama")
            headers = sheet.get("headers") or []
            data = sheet.get("data") or []
            location = f"Sheet: {sheet_name}"

            # Build a DataFrame for deeper checks
            df = self._to_dataframe(headers, data)

            issues.extend(self._check_empty_sheet(sheet_name, df, location))
            issues.extend(self._check_inconsistent_columns(sheet_name, headers, data, location))
            issues.extend(self._check_all_nan_columns(sheet_name, df, location))
            issues.extend(self._check_negative_values(sheet_name, df, location))
            issues.extend(self._check_suspicious_patterns(sheet_name, df, location))
            issues.extend(self._check_headers(sheet_name, headers, location))
            issues.extend(self._check_merged_cell_artifacts(sheet_name, df, location))

        return issues

    def _issue(
        self,
        severity: str,
        category: str,
        description: str,
        location: str,
        suggestion: str,
    ) -> dict[str, Any]:
        return {
            "severity": severity,
            "category": category,
            "description": description,
            "location": location,
            "suggestion": suggestion,
        }

    def _to_dataframe(self, headers: list[str], data: list[list]) -> pd.DataFrame:
        if not headers or not data:
            return pd.DataFrame()
        col_names = [str(h) if h is not None else f"Column_{i}" for i, h in enumerate(headers)]
        df = pd.DataFrame(data, columns=col_names)
        df = df.map(lambda x: np.nan if x is None else x)
        # Coerce numeric
        for col in df.columns:
            try:
                converted = pd.to_numeric(df[col], errors="coerce")
                if converted.notna().sum() >= max(1, len(df) * 0.5):
                    df[col] = converted
            except (ValueError, TypeError):
                pass
        return df

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _check_empty_sheet(self, sheet_name: str, df: pd.DataFrame, location: str) -> list[dict]:
        if df.empty or df.dropna(how="all").empty:
            return [
                self._issue(
                    "high",
                    "empty_sheet",
                    f"Sheet '{sheet_name}' kosong atau hanya berisi baris kosong",
                    location,
                    "Hapus sheet kosong atau isi dengan data",
                )
            ]
        return []

    def _check_inconsistent_columns(
        self, sheet_name: str, headers: list[str], data: list[list], location: str
    ) -> list[dict]:
        if not headers or not data:
            return []
        expected = len(headers)
        issues: list[dict] = []
        for i, row in enumerate(data):
            if len(row) != expected:
                issues.append(
                    self._issue(
                        "medium",
                        "inconsistent_columns",
                        f"Baris {i + 1} memiliki {len(row)} kolom, seharusnya {expected}",
                        f"{location}, Baris {i + 1}",
                        "Pastikan semua baris memiliki jumlah kolom yang sama dengan header",
                    )
                )
        return issues

    def _check_all_nan_columns(self, sheet_name: str, df: pd.DataFrame, location: str) -> list[dict]:
        issues: list[dict] = []
        for col in df.columns:
            if df[col].isna().all():
                issues.append(
                    self._issue(
                        "medium",
                        "empty_column",
                        f"Kolom '{col}' seluruhnya kosong",
                        f"{location}, Kolom: {col}",
                        "Hapus kolom kosong atau isi dengan data",
                    )
                )
        return issues

    def _check_negative_values(self, sheet_name: str, df: pd.DataFrame, location: str) -> list[dict]:
        issues: list[dict] = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            # Heuristic: columns whose name suggests they should be non-negative
            nonneg_keywords = [
                "qty", "quantity", "count", "total", "sum", "amount",
                "price", "cost", "revenue", "profit", "age", "year",
                "month", "day", "hour", "percentage", "rate", "score",
                "id", "index", "number", "unit", "size", "length",
            ]
            col_lower = col.lower()
            if not any(kw in col_lower for kw in nonneg_keywords):
                continue
            neg = df[col].dropna()
            neg = neg[neg < 0]
            if len(neg) > 0:
                issues.append(
                    self._issue(
                        "medium",
                        "unexpected_negative",
                        f"Kolom '{col}' mengandung {len(neg)} nilai negatif, padahal seharusnya non-negatif",
                        f"{location}, Kolom: {col}",
                        f"Verifikasi {len(neg)} nilai negatif di kolom '{col}' sudah benar",
                    )
                )
        return issues

    def _check_suspicious_patterns(self, sheet_name: str, df: pd.DataFrame, location: str) -> list[dict]:
        issues: list[dict] = []
        error_patterns = [
            (r"#REF!", "error #REF! Excel (referensi sel tidak valid)"),
            (r"#DIV/0!", "error #DIV/0! Excel (pembagian dengan nol)"),
            (r"#N/A", "error #N/A Excel (nilai tidak tersedia)"),
            (r"#VALUE!", "error #VALUE! Excel (tipe nilai tidak valid)"),
            (r"^#{5,}", "Sel terisi '#' (kolom terlalu sempit)"),
            (r"#NULL!", "error #NULL! Excel (interseksi tidak valid)"),
            (r"#NUM!", "error #NUM! Excel (nilai numerik tidak valid)"),
            (r"#NAME\?", "error #NAME? Excel (nama formula tidak dikenal)"),
        ]

        for col in df.select_dtypes(include=["object"]).columns:
            for pattern, desc in error_patterns:
                matches = df[col].astype(str).str.contains(pattern, na=False)
                count = matches.sum()
                if count > 0:
                    issues.append(
                        self._issue(
                            "high",
                            "suspicious_text",
                            f"Kolom '{col}' mengandung {count} kejadian {desc}",
                            f"{location}, Kolom: {col}",
                            f"Perbaiki {count} nilai error di kolom '{col}'",
                        )
                    )

        return issues

    def _check_headers(self, sheet_name: str, headers: list[str], location: str) -> list[dict]:
        issues: list[dict] = []
        special_chars_pattern = re.compile(r'[ #@!$%^&*()+=\[\]{}|\\;:\'",.<>/?~`]')

        for i, h in enumerate(headers):
            header_str = str(h) if h is not None else ""
            if not header_str.strip():
                issues.append(
                    self._issue(
                        "low",
                        "empty_header",
                        f"Header di kolom {i + 1} kosong",
                        f"{location}, Kolom {i + 1}",
                        "Berikan nama header yang bermakna untuk setiap kolom",
                    )
                )
            elif special_chars_pattern.search(header_str):
                issues.append(
                    self._issue(
                        "low",
                        "header_special_chars",
                        f"Header '{header_str}' mengandung spasi atau karakter khusus",
                        f"{location}, Kolom: {header_str}",
                        "Ganti karakter khusus dengan underscore atau CamelCase",
                    )
                )
            elif header_str[0].isdigit():
                issues.append(
                    self._issue(
                        "low",
                        "header_starts_with_digit",
                        f"Header '{header_str}' diawali dengan angka",
                        f"{location}, Kolom: {header_str}",
                        "Awali header dengan huruf atau underscore",
                    )
                )

        return issues

    def _check_merged_cell_artifacts(self, sheet_name: str, df: pd.DataFrame, location: str) -> list[dict]:
        """Detect potential merged-cell artifacts.

        A common artifact is that Excel fills the *first* cell of a merged
        range and leaves the rest as None.  We look for runs of identical
        non-None values followed by None."""
        issues: list[dict] = []
        for col in df.columns:
            if df[col].dtype != object:
                continue
            vals = df[col].tolist()
            none_run = 0
            for v in vals:
                if v is None or (isinstance(v, float) and np.isnan(v)):
                    none_run += 1
                else:
                    if none_run > 0 and none_run <= 20:
                        # A short run of None after a value could be a merge artifact
                        pass  # We'll detect differently below
                    none_run = 0

            # More robust: find consecutive None blocks
            is_none = df[col].isna()
            if is_none.sum() < 2:
                continue
            # Look for pattern: value, then None, None, ..., then different value
            # i.e. a block of None surrounded by non-None
            non_none_idx = df.index[~is_none].tolist()
            for i in range(len(non_none_idx) - 1):
                gap = non_none_idx[i + 1] - non_none_idx[i]
                if 1 < gap <= 20:
                    issues.append(
                        self._issue(
                            "low",
                            "merged_cell_artifact",
                            f"Kolom '{col}' memiliki celah {gap - 1} sel kosong antara baris "
                            f"{non_none_idx[i] + 1} dan {non_none_idx[i + 1] + 1} — kemungkinan sel gabungan",
                            f"{location}, Kolom: {col}, Baris {non_none_idx[i] + 1}–{non_none_idx[i + 1] + 1}",
                            "Pisahkan sel gabungan atau isi sel kosong secara eksplisit",
                        )
                    )
            break  # Only report once per column

        return issues
