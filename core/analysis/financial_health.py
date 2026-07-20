"""Financial health analysis and scoring from P&L / balance sheet data."""

import logging
import warnings
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class FinancialHealthAnalyzer:
    """Analyzes financial health from P&L / balance sheet data.

    Auto-detects columns and calculates:
    - Profitability ratios (gross margin, net margin, operating margin)
    - Liquidity ratios (current ratio, quick ratio)
    - Efficiency ratios (asset turnover, inventory turnover)
    - Growth metrics (revenue growth, profit growth)
    - Health score and level
    """

    # Keywords to detect column types (case-insensitive)
    _REVENUE_KEYS = {"revenue", "pendapatan", "sales", "penjualan", "income", "omset"}
    _COGS_KEYS = {"cogs", "cost of goods sold", "hpp", "cost of sales",
                  "harga pokok", "beban pokok"}
    _PROFIT_KEYS = {"profit", "laba", "net income", "laba bersih", "earning",
                    "net profit", "gross profit", "laba kotor"}
    _EXPENSE_KEYS = {"expense", "beban", "cost", "biaya", "operating expense"}
    _ASSET_KEYS = {"asset", "aset", "total asset", "total aset"}
    _LIABILITY_KEYS = {"liability", "liabilitas", "utang", "kewajiban"}
    _EQUITY_KEYS = {"equity", "ekuitas", "modal"}
    _CURRENT_ASSET_KEYS = {"current asset", "aset lancar", "current asset"}
    _CURRENT_LIABILITY_KEYS = {"current liability", "utang lancar", "liabilitas jangka pendek"}
    _INVENTORY_KEYS = {"inventory", "persediaan", "stock", "inventaris"}
    _RECEIVABLE_KEYS = {"receivable", "piutang", "account receivable"}
    _DATE_KEYS = {"date", "tanggal", "period", "periode", "tahun", "year", "month", "bulan"}

    @staticmethod
    def _to_native(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: FinancialHealthAnalyzer._to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [FinancialHealthAnalyzer._to_native(v) for v in obj]
        elif isinstance(obj, tuple):
            return tuple(FinancialHealthAnalyzer._to_native(v) for v in obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return FinancialHealthAnalyzer._to_native(obj.tolist())
        elif isinstance(obj, pd.Timestamp):
            return str(obj)
        elif pd.isna(obj):
            return None
        return obj

    def _find_column(self, df: pd.DataFrame, keywords: set) -> str | None:
        """Find a column matching one of the given keywords (case-insensitive, partial match)."""
        for col in df.columns:
            col_lower = str(col).lower().strip()
            for kw in keywords:
                if kw in col_lower:
                    return col
        return None

    def analyze(self, df: pd.DataFrame) -> dict:
        """Analyze financial health from the given data.

        Parameters
        ----------
        df : pd.DataFrame
            Input data. Should contain financial statement data with
            columns that can be auto-detected.

        Returns
        -------
        dict with keys:
            - profitability_ratios : list of dicts
            - liquidity_ratios : list of dicts
            - efficiency_ratios : list of dicts
            - growth_metrics : list of dicts
            - health_score : float (0-100)
            - health_level : str
            - insights : list of key findings
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            warnings.simplefilter("ignore", UserWarning)

            try:
                if df.empty:
                    return {
                        "profitability_ratios": [],
                        "liquidity_ratios": [],
                        "efficiency_ratios": [],
                        "growth_metrics": [],
                        "health_score": 0.0,
                        "health_level": "poor",
                        "insights": ["Data kosong, tidak dapat menganalisis kesehatan finansial."],
                    }

                # Auto-detect columns
                revenue_col = self._find_column(df, self._REVENUE_KEYS)
                cogs_col = self._find_column(df, self._COGS_KEYS)
                profit_col = self._find_column(df, self._PROFIT_KEYS)
                expense_col = self._find_column(df, self._EXPENSE_KEYS)
                asset_col = self._find_column(df, self._ASSET_KEYS)
                liability_col = self._find_column(df, self._LIABILITY_KEYS)
                equity_col = self._find_column(df, self._EQUITY_KEYS)
                current_asset_col = self._find_column(df, self._CURRENT_ASSET_KEYS)
                current_liability_col = self._find_column(df, self._CURRENT_LIABILITY_KEYS)
                inventory_col = self._find_column(df, self._INVENTORY_KEYS)
                receivable_col = self._find_column(df, self._RECEIVABLE_KEYS)
                date_col = self._find_column(df, self._DATE_KEYS)

                profitability_ratios = []
                liquidity_ratios = []
                efficiency_ratios = []
                growth_metrics = []
                insights = []

                # Helper to get latest numeric value
                def _latest_val(col_name: str) -> float | None:
                    if col_name and col_name in df.columns:
                        serie = pd.to_numeric(df[col_name], errors="coerce").dropna()
                        if not serie.empty:
                            return float(serie.iloc[-1])
                    return None

                def _earliest_val(col_name: str) -> float | None:
                    if col_name and col_name in df.columns:
                        serie = pd.to_numeric(df[col_name], errors="coerce").dropna()
                        if not serie.empty:
                            return float(serie.iloc[0])
                    return None

                revenue = _latest_val(revenue_col)
                cogs = _latest_val(cogs_col)
                profit = _latest_val(profit_col)
                expenses = _latest_val(expense_col)
                assets = _latest_val(asset_col)
                liabilities = _latest_val(liability_col)
                equity = _latest_val(equity_col)
                current_assets = _latest_val(current_asset_col)
                current_liabilities = _latest_val(current_liability_col)
                inventory = _latest_val(inventory_col)
                receivables = _latest_val(receivable_col)

                # ── Profitability Ratios ─────────────────────────────
                if revenue and revenue > 0:
                    # Gross margin
                    if cogs is not None:
                        gross_profit = revenue - cogs
                        gross_margin = (gross_profit / revenue) * 100
                        profitability_ratios.append({
                            "name": "Gross Margin",
                            "value": round(gross_margin, 2),
                            "unit": "%",
                            "description": "Margin laba kotor — persentase pendapatan setelah HPP.",
                            "verdict": "Baik" if gross_margin > 40 else ("Cukup" if gross_margin > 20 else "Rendah"),
                        })

                    # Net margin (using profit column or revenue - expenses)
                    net_income = profit if profit is not None else (
                        revenue - expenses if expenses is not None else None
                    )
                    if net_income is not None:
                        net_margin = (net_income / revenue) * 100
                        profitability_ratios.append({
                            "name": "Net Margin",
                            "value": round(net_margin, 2),
                            "unit": "%",
                            "description": "Margin laba bersih — persentase laba setelah semua biaya.",
                            "verdict": "Baik" if net_margin > 15 else ("Cukup" if net_margin > 5 else "Rendah"),
                        })

                    # Operating margin
                    if expenses is not None and cogs is not None:
                        op_income = revenue - cogs - expenses
                        op_margin = (op_income / revenue) * 100
                        profitability_ratios.append({
                            "name": "Operating Margin",
                            "value": round(op_margin, 2),
                            "unit": "%",
                            "description": "Margin operasi — efisiensi operasional bisnis.",
                            "verdict": "Baik" if op_margin > 20 else ("Cukup" if op_margin > 10 else "Rendah"),
                        })
                elif profit is not None:
                    # Fallback: just report profit ratio if no revenue found
                    profitability_ratios.append({
                        "name": "Profit Indicator",
                        "value": round(float(profit), 2),
                        "unit": "currency",
                        "description": "Nilai laba terdeteksi, namun kolom pendapatan tidak ditemukan.",
                        "verdict": "Positif" if profit > 0 else "Negatif",
                    })

                # ── Liquidity Ratios ─────────────────────────────────
                if current_assets is not None and current_liabilities is not None and current_liabilities > 0:
                    current_ratio = current_assets / current_liabilities
                    liquidity_ratios.append({
                        "name": "Current Ratio",
                        "value": round(current_ratio, 2),
                        "unit": "x",
                        "description": "Rasio lancar — kemampuan membayar kewajiban jangka pendek.",
                        "verdict": "Sehat" if current_ratio > 1.5 else ("Cukup" if current_ratio > 1.0 else "Rendah"),
                    })

                    # Quick ratio (current assets - inventory)
                    quick_assets = current_assets - (inventory or 0)
                    quick_ratio = quick_assets / current_liabilities
                    liquidity_ratios.append({
                        "name": "Quick Ratio",
                        "value": round(quick_ratio, 2),
                        "unit": "x",
                        "description": "Rasio cepat — kemampuan bayar tanpa mengandalkan persediaan.",
                        "verdict": "Sehat" if quick_ratio > 1.0 else ("Cukup" if quick_ratio > 0.5 else "Rendah"),
                    })
                elif assets is not None and liabilities is not None and liabilities > 0:
                    # Use total assets / total liabilities as proxy
                    solvency = assets / liabilities
                    liquidity_ratios.append({
                        "name": "Solvency Ratio",
                        "value": round(solvency, 2),
                        "unit": "x",
                        "description": "Rasio solvabilitas — aset terhadap kewajiban.",
                        "verdict": "Sehat" if solvency > 1.5 else ("Cukup" if solvency > 1.0 else "Rendah"),
                    })

                # ── Efficiency Ratios ────────────────────────────────
                if revenue and revenue > 0 and assets and assets > 0:
                    asset_turnover = revenue / assets
                    efficiency_ratios.append({
                        "name": "Asset Turnover",
                        "value": round(asset_turnover, 4),
                        "unit": "x",
                        "description": "Perputaran aset — efisiensi penggunaan aset untuk menghasilkan pendapatan.",
                        "verdict": "Efisien" if asset_turnover > 1.0 else "Kurang Efisien",
                    })

                if revenue and revenue > 0 and inventory is not None and inventory > 0:
                    inv_turnover = revenue / inventory
                    efficiency_ratios.append({
                        "name": "Inventory Turnover",
                        "value": round(inv_turnover, 2),
                        "unit": "x",
                        "description": "Perputaran persediaan — seberapa cepat persediaan terjual.",
                        "verdict": "Cepat" if inv_turnover > 6 else ("Normal" if inv_turnover > 3 else "Lambat"),
                    })

                if revenue and revenue > 0 and receivables is not None and receivables > 0:
                    rec_turnover = revenue / receivables
                    efficiency_ratios.append({
                        "name": "Receivables Turnover",
                        "value": round(rec_turnover, 2),
                        "unit": "x",
                        "description": "Perputaran piutang — kecepatan penagihan piutang.",
                        "verdict": "Cepat" if rec_turnover > 12 else ("Normal" if rec_turnover > 6 else "Lambat"),
                    })

                # ── Growth Metrics ───────────────────────────────────
                if date_col and revenue_col:
                    try:
                        temp = df[[date_col, revenue_col]].copy()
                        temp[date_col] = pd.to_datetime(temp[date_col], errors="coerce")
                        temp[revenue_col] = pd.to_numeric(temp[revenue_col], errors="coerce")
                        temp = temp.dropna().sort_values(date_col)
                        if len(temp) >= 2:
                            first_rev = float(temp[revenue_col].iloc[0])
                            last_rev = float(temp[revenue_col].iloc[-1])
                            if first_rev > 0:
                                rev_growth = ((last_rev - first_rev) / first_rev) * 100
                                growth_metrics.append({
                                    "name": "Revenue Growth",
                                    "value": round(rev_growth, 2),
                                    "unit": "%",
                                    "period": f"{temp[date_col].iloc[0]} - {temp[date_col].iloc[-1]}",
                                    "verdict": "Tumbuh" if rev_growth > 0 else "Menurun",
                                })
                    except Exception as e:
                        logger.warning(f"Revenue growth calculation gagal: {e}")

                if date_col and profit_col:
                    try:
                        temp = df[[date_col, profit_col]].copy()
                        temp[date_col] = pd.to_datetime(temp[date_col], errors="coerce")
                        temp[profit_col] = pd.to_numeric(temp[profit_col], errors="coerce")
                        temp = temp.dropna().sort_values(date_col)
                        if len(temp) >= 2:
                            first_profit = float(temp[profit_col].iloc[0])
                            last_profit = float(temp[profit_col].iloc[-1])
                            if first_profit != 0:
                                profit_growth = ((last_profit - first_profit) / abs(first_profit)) * 100
                            elif last_profit > 0:
                                profit_growth = 100.0
                            else:
                                profit_growth = 0.0
                            growth_metrics.append({
                                "name": "Profit Growth",
                                "value": round(profit_growth, 2),
                                "unit": "%",
                                "period": f"{temp[date_col].iloc[0]} - {temp[date_col].iloc[-1]}",
                                "verdict": "Tumbuh" if profit_growth > 0 else "Menurun",
                            })
                    except Exception as e:
                        logger.warning(f"Profit growth calculation gagal: {e}")

                # ── Health Score ──────────────────────────────────────
                score = 50.0  # Start neutral
                count = 0

                for ratio in profitability_ratios:
                    if ratio.get("verdict") == "Baik" or ratio.get("verdict") == "Positif":
                        score += 10
                    elif ratio.get("verdict") == "Cukup":
                        score += 5
                    elif ratio.get("verdict") == "Rendah" or ratio.get("verdict") == "Negatif":
                        score -= 10
                    count += 1

                for ratio in liquidity_ratios:
                    if ratio.get("verdict") == "Sehat":
                        score += 10
                    elif ratio.get("verdict") == "Cukup":
                        score += 5
                    elif ratio.get("verdict") == "Rendah":
                        score -= 10
                    count += 1

                for metric in efficiency_ratios:
                    if metric.get("verdict") in ("Efisien", "Cepat"):
                        score += 8
                    elif metric.get("verdict") in ("Kurang Efisien", "Lambat"):
                        score -= 5
                    count += 1

                for metric in growth_metrics:
                    if metric.get("verdict") == "Tumbuh":
                        score += 10
                    elif metric.get("verdict") == "Menurun":
                        score -= 10
                    count += 1

                health_score = min(100.0, max(0.0, score))

                # Determine health level
                if health_score >= 80:
                    health_level = "excellent"
                elif health_score >= 60:
                    health_level = "good"
                elif health_score >= 40:
                    health_level = "fair"
                elif health_score >= 20:
                    health_level = "poor"
                else:
                    health_level = "critical"

                # ── Insights ──────────────────────────────────────────
                # Profitability insights
                for ratio in profitability_ratios:
                    insights.append(
                        f"{ratio['name']}: {ratio['value']}{ratio['unit']} — {ratio['verdict']}. "
                        f"{ratio['description']}"
                    )

                # Liquidity insights
                for ratio in liquidity_ratios:
                    insights.append(
                        f"{ratio['name']}: {ratio['value']}{ratio['unit']} — {ratio['verdict']}. "
                        f"{ratio['description']}"
                    )

                # Efficiency insights
                for metric in efficiency_ratios:
                    insights.append(
                        f"{metric['name']}: {metric['value']}{metric['unit']} — {metric['verdict']}. "
                        f"{metric['description']}"
                    )

                # Growth insights
                for metric in growth_metrics:
                    insights.append(
                        f"{metric['name']}: {metric['value']}{metric['unit']} ({metric.get('period', 'N/A')}) "
                        f"— {metric['verdict']}."
                    )

                if not insights:
                    insights.append(
                        "Data tidak cukup untuk menghitung rasio keuangan. "
                        "Pastikan data mengandung kolom pendapatan, biaya, aset, atau kewajiban."
                    )

                return self._to_native({
                    "profitability_ratios": profitability_ratios,
                    "liquidity_ratios": liquidity_ratios,
                    "efficiency_ratios": efficiency_ratios,
                    "growth_metrics": growth_metrics,
                    "health_score": round(health_score, 2),
                    "health_level": health_level,
                    "insights": insights,
                })

            except Exception as e:
                logger.exception("Financial health analysis gagal")
                return {
                    "profitability_ratios": [],
                    "liquidity_ratios": [],
                    "efficiency_ratios": [],
                    "growth_metrics": [],
                    "health_score": 0.0,
                    "health_level": "poor",
                    "insights": [f"Gagal menganalisis kesehatan finansial: {e}"],
                }
