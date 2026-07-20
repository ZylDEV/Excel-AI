"""Inventory analysis for insights on stock movement, aging, and reorder."""

import logging
import warnings
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class InventoryAnalyzer:
    """Analyzes inventory data for insights.

    Auto-detects columns and returns:
    - Categories (dead stock, slow-moving, fast-moving)
    - Stock aging (age brackets with counts/values)
    - Reorder suggestions
    - Overstock items
    - Warehouse distribution if detected
    """

    _ITEM_KEYS = {"item", "product", "produk", "barang", "name", "nama",
                  "sku", "material", "description", "part"}
    _STOCK_KEYS = {"stock", "stok", "quantity", "qty", "jumlah", "on hand",
                   "current stock", "balance", "remaining"}
    _PRICE_KEYS = {"price", "harga", "cost", "biaya", "value", "nilai",
                   "unit price", "unit cost", "harga satuan"}
    _LOCATION_KEYS = {"location", "lokasi", "warehouse", "gudang",
                      "storage", "penyimpanan", "shelf", "rak"}
    _DATE_KEYS = {"date", "tanggal", "received", "diterima", "in date",
                  "purchase date", "beli", "entry date", "masuk"}
    _CATEGORY_KEYS = {"category", "kategori", "type", "tipe", "group", "grup",
                      "class", "kelas"}
    _MOVEMENT_KEYS = {"movement", "sold", "terjual", "out", "keluar",
                      "usage", "pemakaian", "demand"}

    @staticmethod
    def _to_native(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: InventoryAnalyzer._to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [InventoryAnalyzer._to_native(v) for v in obj]
        elif isinstance(obj, tuple):
            return tuple(InventoryAnalyzer._to_native(v) for v in obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return InventoryAnalyzer._to_native(obj.tolist())
        elif isinstance(obj, pd.Timestamp):
            return str(obj)
        elif pd.isna(obj):
            return None
        return obj

    def _find_column(self, df: pd.DataFrame, keywords: set) -> str | None:
        for col in df.columns:
            col_lower = str(col).lower().strip()
            for kw in keywords:
                if kw in col_lower:
                    return col
        return None

    def analyze(self, df: pd.DataFrame) -> dict:
        """Analyze inventory data.

        Parameters
        ----------
        df : pd.DataFrame
            Inventory data.

        Returns
        -------
        dict with keys: categories, stock_aging, reorder_suggestions,
                        overstock_items, warehouse_distribution, summary.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            warnings.simplefilter("ignore", UserWarning)

            try:
                if df.empty:
                    return {
                        "categories": {},
                        "stock_aging": [],
                        "reorder_suggestions": [],
                        "overstock_items": [],
                        "warehouse_distribution": [],
                        "summary": "Data inventaris kosong.",
                    }

                # Auto-detect columns
                item_col = self._find_column(df, self._ITEM_KEYS)
                stock_col = self._find_column(df, self._STOCK_KEYS)
                price_col = self._find_column(df, self._PRICE_KEYS)
                location_col = self._find_column(df, self._LOCATION_KEYS)
                date_col = self._find_column(df, self._DATE_KEYS)
                category_col = self._find_column(df, self._CATEGORY_KEYS)
                movement_col = self._find_column(df, self._MOVEMENT_KEYS)

                categories = {}
                stock_aging = []
                reorder_suggestions = []
                overstock_items = []
                warehouse_distribution = []
                summary_parts = []

                # Convert numeric columns
                if stock_col:
                    df[stock_col] = pd.to_numeric(df[stock_col], errors="coerce")
                if price_col:
                    df[price_col] = pd.to_numeric(df[price_col], errors="coerce")
                if movement_col:
                    df[movement_col] = pd.to_numeric(df[movement_col], errors="coerce")

                # ── Category Analysis ────────────────────────────────
                if stock_col:
                    stock_data = df[stock_col].dropna()
                    if len(stock_data) > 0:
                        # Define stock categories based on quantity
                        dead_mask = stock_data == 0
                        low_threshold = stock_data.quantile(0.25)
                        high_threshold = stock_data.quantile(0.75)

                        item_name_col = item_col or stock_col
                        dead_items = df.loc[dead_mask.index[dead_mask], item_name_col].head(20).tolist() if dead_mask.any() else []
                        slow_items = df.loc[
                            (stock_data > 0) & (stock_data <= low_threshold),
                            item_name_col
                        ].head(20).tolist() if (stock_data > 0).any() else []
                        fast_items = df.loc[
                            stock_data > high_threshold,
                            item_name_col
                        ].head(20).tolist() if high_threshold > 0 else []

                        categories = {
                            "dead_stock": {
                                "count": int(dead_mask.sum()),
                                "items": [str(i) for i in dead_items],
                                "description": "Barang dengan stok 0 — perlu dihapus atau di-discontinue.",
                            },
                            "slow_moving": {
                                "count": int(((stock_data > 0) & (stock_data <= low_threshold)).sum()),
                                "items": [str(i) for i in slow_items],
                                "description": "Barang dengan stok rendah — pergerakan lambat.",
                            },
                            "fast_moving": {
                                "count": int((stock_data > high_threshold).sum()),
                                "items": [str(i) for i in fast_items],
                                "description": "Barang dengan stok tinggi — pergerakan cepat, perlu reorder rutin.",
                            },
                        }

                        total_items = len(stock_data)
                        dead_pct = (categories["dead_stock"]["count"] / total_items * 100) if total_items > 0 else 0
                        summary_parts.append(
                            f"Dari {total_items} item: {categories['dead_stock']['count']} dead stock "
                            f"({dead_pct:.1f}%), {categories['slow_moving']['count']} slow-moving, "
                            f"{categories['fast_moving']['count']} fast-moving."
                        )

                # ── Stock Aging ───────────────────────────────────────
                if date_col and stock_col:
                    try:
                        temp = df[[date_col, stock_col]].copy()
                        temp[date_col] = pd.to_datetime(temp[date_col], errors="coerce")
                        temp[stock_col] = pd.to_numeric(temp[stock_col], errors="coerce")
                        temp = temp.dropna(subset=[date_col, stock_col])

                        if not temp.empty:
                            now = pd.Timestamp.now()
                            temp["age_days"] = (now - temp[date_col]).dt.days

                            # Define age brackets
                            brackets = [
                                ("0-30 days", 0, 30),
                                ("31-90 days", 31, 90),
                                ("91-180 days", 91, 180),
                                ("181-365 days", 181, 365),
                                (">365 days", 366, 9999),
                            ]
                            for label, lo, hi in brackets:
                                mask = (temp["age_days"] >= lo) & (temp["age_days"] <= hi)
                                count = int(mask.sum())
                                if count > 0:
                                    total_value = float(temp.loc[mask, stock_col].sum())
                                    stock_aging.append({
                                        "bracket": label,
                                        "count": count,
                                        "total_value": round(total_value, 2),
                                    })

                            if stock_aging:
                                summary_parts.append(
                                    f"Analisis aging: {sum(s['count'] for s in stock_aging)} item terdistribusi "
                                    f"dalam {len(stock_aging)} kelompok usia."
                                )
                    except Exception as e:
                        logger.warning(f"Stock aging analysis gagal: {e}")

                # ── Reorder Suggestions ───────────────────────────────
                if item_col and stock_col:
                    stock_vals = pd.to_numeric(df[stock_col], errors="coerce")
                    if len(stock_vals.dropna()) > 0:
                        median_stock = stock_vals.median()
                        mean_stock = stock_vals.mean()
                        reorder_point = max(1, median_stock * 0.3)

                        # Items below reorder point
                        low_stock = df[stock_vals < reorder_point].copy()
                        if not low_stock.empty:
                            for _, row in low_stock.head(20).iterrows():
                                current = float(row[stock_col]) if pd.notna(row[stock_col]) else 0
                                suggested = int(max(mean_stock - current, reorder_point * 2))
                                reorder_suggestions.append({
                                    "item": str(row.get(item_col, f"Item-{_}")),
                                    "current_stock": current,
                                    "reorder_point": round(float(reorder_point), 2),
                                    "suggested_qty": suggested,
                                })

                            if reorder_suggestions:
                                summary_parts.append(
                                    f"{len(reorder_suggestions)} item di bawah titik reorder "
                                    f"({reorder_point:.0f}) — perlu reorder segera."
                                )

                # ── Overstock Items ──────────────────────────────────
                if item_col and stock_col:
                    stock_vals = pd.to_numeric(df[stock_col], errors="coerce")
                    if len(stock_vals.dropna()) > 0:
                        high_threshold = stock_vals.quantile(0.9)
                        overstock = df[stock_vals > high_threshold].head(20)
                        if not overstock.empty:
                            for _, row in overstock.iterrows():
                                overstock_items.append({
                                    "item": str(row.get(item_col, f"Item-{_}")),
                                    "stock": float(row[stock_col]) if pd.notna(row[stock_col]) else 0,
                                    "recommended_max": round(float(high_threshold), 2),
                                })

                            if overstock_items:
                                summary_parts.append(
                                    f"{len(overstock_items)} item overstock "
                                    f"(di atas persentil ke-90)."
                                )

                # ── Warehouse Distribution ───────────────────────────
                if location_col:
                    try:
                        loc_counts = df[location_col].value_counts()
                        total_loc = loc_counts.sum()
                        for loc, count in loc_counts.head(20).items():
                            pct = (count / total_loc * 100) if total_loc > 0 else 0
                            warehouse_distribution.append({
                                "location": str(loc),
                                "count": int(count),
                                "percentage": round(pct, 2),
                            })

                        if warehouse_distribution:
                            summary_parts.append(
                                f"Distribusi gudang: {len(warehouse_distribution)} lokasi terdeteksi."
                            )
                    except Exception as e:
                        logger.warning(f"Warehouse distribution analysis gagal: {e}")

                # ── Build Summary ─────────────────────────────────────
                if not summary_parts:
                    if stock_col:
                        total_items = len(df)
                        total_stock = float(df[stock_col].sum()) if stock_col else 0
                        summary_parts.append(
                            f"Total {total_items} item dengan total stok {total_stock:,.0f} unit."
                        )
                    else:
                        summary_parts.append("Data inventaris dianalisis. Kolom stok tidak terdeteksi secara eksplisit.")

                summary = " | ".join(summary_parts)

                return self._to_native({
                    "categories": categories,
                    "stock_aging": stock_aging,
                    "reorder_suggestions": reorder_suggestions,
                    "overstock_items": overstock_items,
                    "warehouse_distribution": warehouse_distribution,
                    "summary": summary,
                })

            except Exception as e:
                logger.exception("Inventory analysis gagal")
                return {
                    "categories": {},
                    "stock_aging": [],
                    "reorder_suggestions": [],
                    "overstock_items": [],
                    "warehouse_distribution": [],
                    "summary": f"Gagal menganalisis inventaris: {e}",
                }
