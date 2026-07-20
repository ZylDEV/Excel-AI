"""Sales analytics for business intelligence."""

import logging
import warnings
from collections import defaultdict
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class SalesAnalyzer:
    """Analyzes sales data for business intelligence.

    Auto-detects columns and returns:
    - Top customers
    - Customer segments
    - Sales trends
    - Product performance
    - Regional analysis
    - Cross-selling opportunities
    - Summary
    """

    _CUSTOMER_KEYS = {"customer", "pelanggan", "client", "klien", "buyer",
                      "pembeli", "customer name", "nama pelanggan"}
    _PRODUCT_KEYS = {"product", "produk", "item", "barang", "service",
                     "layanan", "sku", "description", "deskripsi"}
    _REVENUE_KEYS = {"revenue", "pendapatan", "amount", "jumlah", "total",
                     "sales", "penjualan", "price", "harga", "value", "nilai"}
    _QTY_KEYS = {"quantity", "qty", "jumlah", "unit", "pcs"}
    _DATE_KEYS = {"date", "tanggal", "order date", "transaction", "transaksi",
                  "tgl", "invoice date", "period", "periode"}
    _REGION_KEYS = {"region", "wilayah", "city", "kota", "state", "provinsi",
                    "country", "negara", "area", "cabang", "branch"}
    _CATEGORY_KEYS = {"category", "kategori", "type", "tipe", "group", "grup",
                      "segment", "segmen"}
    _PROFIT_KEYS = {"profit", "laba", "margin", "keuntungan", "gross profit"}

    @staticmethod
    def _to_native(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: SalesAnalyzer._to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [SalesAnalyzer._to_native(v) for v in obj]
        elif isinstance(obj, tuple):
            return tuple(SalesAnalyzer._to_native(v) for v in obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return SalesAnalyzer._to_native(obj.tolist())
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
        """Analyze sales data.

        Parameters
        ----------
        df : pd.DataFrame
            Sales data with various columns.

        Returns
        -------
        dict with keys: top_customers, customer_segments, sales_trend,
                        product_performance, regional_analysis,
                        cross_selling_opportunities, summary.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            warnings.simplefilter("ignore", UserWarning)

            try:
                if df.empty:
                    return {
                        "top_customers": [],
                        "customer_segments": [],
                        "sales_trend": [],
                        "product_performance": [],
                        "regional_analysis": [],
                        "cross_selling_opportunities": [],
                        "summary": "Data penjualan kosong.",
                    }

                # Auto-detect columns
                cust_col = self._find_column(df, self._CUSTOMER_KEYS)
                prod_col = self._find_column(df, self._PRODUCT_KEYS)
                rev_col = self._find_column(df, self._REVENUE_KEYS)
                qty_col = self._find_column(df, self._QTY_KEYS)
                date_col = self._find_column(df, self._DATE_KEYS)
                region_col = self._find_column(df, self._REGION_KEYS)
                cat_col = self._find_column(df, self._CATEGORY_KEYS)
                profit_col = self._find_column(df, self._PROFIT_KEYS)

                top_customers = []
                customer_segments = []
                sales_trend = []
                product_performance = []
                regional_analysis = []
                cross_selling_opportunities = []
                summary_parts = []

                total_revenue = 0.0

                # ── Convert numeric columns ──────────────────────────
                if rev_col:
                    df[rev_col] = pd.to_numeric(df[rev_col], errors="coerce")
                    total_revenue = float(df[rev_col].sum())
                if qty_col:
                    df[qty_col] = pd.to_numeric(df[qty_col], errors="coerce")
                if profit_col:
                    df[profit_col] = pd.to_numeric(df[profit_col], errors="coerce")

                # ── Top Customers ─────────────────────────────────────
                if cust_col and rev_col:
                    try:
                        cust_rev = df.groupby(cust_col)[rev_col].sum().sort_values(ascending=False)
                        total = float(cust_rev.sum())
                        if total > 0:
                            for cust, rev in cust_rev.head(20).items():
                                top_customers.append({
                                    "name": str(cust),
                                    "revenue": round(float(rev), 2),
                                    "pct_total": round(float(rev) / total * 100, 2),
                                })

                            summary_parts.append(
                                f"Top customers: {len(top_customers)} pelanggan teratas "
                                f"menyumbang {(sum(c['revenue'] for c in top_customers) / total * 100):.1f}% "
                                f"dari total pendapatan."
                            )
                    except Exception as e:
                        logger.warning(f"Top customers analysis gagal: {e}")

                # ── Customer Segments ─────────────────────────────────
                if cust_col and rev_col:
                    try:
                        cust_data = df.groupby(cust_col)[rev_col].agg(["sum", "count"]).sort_values("sum", ascending=False)
                        total = float(cust_data["sum"].sum())
                        if total > 0 and len(cust_data) > 1:
                            # Segment using Pareto principle
                            cumulative = cust_data["sum"].cumsum() / total
                            top_pct = float(cumulative[cumulative <= 0.8].count()) / len(cust_data) * 100

                            # Calculate average revenue per customer
                            avg_rev = float(cust_data["sum"].mean())

                            # Determine segments
                            high_value = cust_data[cust_data["sum"] > avg_rev * 2]
                            medium_value = cust_data[
                                (cust_data["sum"] > avg_rev * 0.5) &
                                (cust_data["sum"] <= avg_rev * 2)
                            ]
                            low_value = cust_data[cust_data["sum"] <= avg_rev * 0.5]

                            segments = [
                                {
                                    "segment": "High Value",
                                    "count": len(high_value),
                                    "pct_customers": round(len(high_value) / len(cust_data) * 100, 2),
                                    "pct_revenue": round(float(high_value["sum"].sum()) / total * 100, 2) if total > 0 else 0,
                                    "description": "Pelanggan dengan kontribusi sangat tinggi — perlu retention khusus.",
                                },
                                {
                                    "segment": "Medium Value",
                                    "count": len(medium_value),
                                    "pct_customers": round(len(medium_value) / len(cust_data) * 100, 2),
                                    "pct_revenue": round(float(medium_value["sum"].sum()) / total * 100, 2) if total > 0 else 0,
                                    "description": "Pelanggan dengan kontribusi moderat — potensi untuk ditingkatkan.",
                                },
                                {
                                    "segment": "Low Value",
                                    "count": len(low_value),
                                    "pct_customers": round(len(low_value) / len(cust_data) * 100, 2),
                                    "pct_revenue": round(float(low_value["sum"].sum()) / total * 100, 2) if total > 0 else 0,
                                    "description": "Pelanggan dengan kontribusi rendah — perlu strategi aktivasi.",
                                },
                            ]
                            customer_segments = segments
                    except Exception as e:
                        logger.warning(f"Customer segmentation gagal: {e}")

                # ── Sales Trends ──────────────────────────────────────
                if date_col and rev_col:
                    try:
                        temp = df[[date_col, rev_col]].copy()
                        temp[date_col] = pd.to_datetime(temp[date_col], errors="coerce")
                        temp[rev_col] = pd.to_numeric(temp[rev_col], errors="coerce")
                        temp = temp.dropna(subset=[date_col, rev_col])

                        if not temp.empty:
                            # Auto-detect frequency
                            date_range = temp[date_col].max() - temp[date_col].min()
                            if date_range.days <= 35:
                                freq = "D"
                                freq_label = "daily"
                            elif date_range.days <= 180:
                                freq = "W"
                                freq_label = "weekly"
                            else:
                                freq = "ME"
                                freq_label = "monthly"

                            temp["period"] = temp[date_col].dt.to_period(freq).astype(str)
                            trend = temp.groupby("period")[rev_col].sum().sort_index()

                            trend_list = []
                            prev_rev = None
                            for period, rev in trend.items():
                                growth = None
                                if prev_rev is not None and prev_rev > 0:
                                    growth = round((float(rev) - prev_rev) / prev_rev * 100, 2)
                                trend_list.append({
                                    "period": str(period),
                                    "revenue": round(float(rev), 2),
                                    "growth": growth,
                                })
                                prev_rev = float(rev)
                            sales_trend = trend_list

                            if trend_list:
                                growth_rates = [t["growth"] for t in trend_list if t["growth"] is not None]
                                if growth_rates:
                                    avg_growth = sum(growth_rates) / len(growth_rates)
                                    direction = "meningkat" if avg_growth > 2 else ("stabil" if avg_growth > -2 else "menurun")
                                    summary_parts.append(
                                        f"Tren penjualan ({freq_label}): {direction} "
                                        f"(rata-rata perubahan {avg_growth:+.1f}% per periode)."
                                    )
                    except Exception as e:
                        logger.warning(f"Sales trend analysis gagal: {e}")

                # ── Product Performance ───────────────────────────────
                if prod_col and rev_col:
                    try:
                        prod_data = df.groupby(prod_col)[rev_col].sum().sort_values(ascending=False)
                        if profit_col:
                            profit_data = df.groupby(prod_col)[profit_col].sum()

                        total_prod_rev = float(prod_data.sum())
                        for prod, rev in prod_data.head(20).items():
                            margin = None
                            if profit_col and prod in profit_data.index:
                                pft = float(profit_data[prod])
                                if rev > 0:
                                    margin = round(pft / rev * 100, 2)
                            product_performance.append({
                                "product": str(prod),
                                "revenue": round(float(rev), 2),
                                "profit": round(float(profit_data.get(prod, 0)), 2) if profit_col else None,
                                "margin": margin,
                                "pct_total": round(float(rev) / total_prod_rev * 100, 2) if total_prod_rev > 0 else 0,
                            })

                        summary_parts.append(
                            f"{len(product_performance)} produk/unit bisnis dianalisis. "
                            f"Produk teratas: {product_performance[0]['product']} "
                            f"({product_performance[0]['pct_total']:.1f}% dari pendapatan)."
                        )
                    except Exception as e:
                        logger.warning(f"Product performance analysis gagal: {e}")

                # ── Regional Analysis ─────────────────────────────────
                if region_col and rev_col:
                    try:
                        region_data = df.groupby(region_col)[rev_col].agg(["sum", "count"]).sort_values("sum", ascending=False)
                        total_reg_rev = float(region_data["sum"].sum())
                        for region, row in region_data.head(20).iterrows():
                            regional_analysis.append({
                                "region": str(region),
                                "revenue": round(float(row["sum"]), 2),
                                "count": int(row["count"]),
                                "pct_revenue": round(float(row["sum"]) / total_reg_rev * 100, 2) if total_reg_rev > 0 else 0,
                            })

                        summary_parts.append(
                            f"Analisis regional: {len(regional_analysis)} region terdeteksi."
                        )
                    except Exception as e:
                        logger.warning(f"Regional analysis gagal: {e}")

                # ── Cross-Selling Opportunities ───────────────────────
                if cust_col and prod_col and len(df) >= 10:
                    try:
                        # Look for customers who bought multiple products
                        cust_prod = df.groupby(cust_col)[prod_col].apply(set)
                        multi_purchase = cust_prod[cust_prod.apply(len) >= 2]

                        if len(multi_purchase) >= 3:
                            # Count product pairs
                            pair_counts = defaultdict(int)
                            for products in multi_purchase:
                                prod_list = sorted([str(p) for p in products if pd.notna(p)])
                                for i in range(len(prod_list)):
                                    for j in range(i + 1, len(prod_list)):
                                        pair = (prod_list[i], prod_list[j])
                                        pair_counts[pair] += 1

                            sorted_pairs = sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)
                            for (p1, p2), count in sorted_pairs[:10]:
                                cross_selling_opportunities.append({
                                    "product_pair": [p1, p2],
                                    "frequency": int(count),
                                })

                            if cross_selling_opportunities:
                                summary_parts.append(
                                    f"{len(cross_selling_opportunities)} peluang cross-selling terdeteksi "
                                    f"— produk yang sering dibeli bersamaan."
                                )
                    except Exception as e:
                        logger.warning(f"Cross-selling analysis gagal: {e}")

                # ── Build Summary ─────────────────────────────────────
                if not summary_parts:
                    if total_revenue > 0:
                        summary_parts.append(
                            f"Total pendapatan: {total_revenue:,.2f}. "
                            f"{len(df)} transaksi dianalisis."
                        )
                    else:
                        summary_parts.append("Data penjualan dianalisis. Kolom pendapatan tidak terdeteksi.")

                summary = " | ".join(summary_parts)

                return self._to_native({
                    "top_customers": top_customers,
                    "customer_segments": customer_segments,
                    "sales_trend": sales_trend,
                    "product_performance": product_performance,
                    "regional_analysis": regional_analysis,
                    "cross_selling_opportunities": cross_selling_opportunities,
                    "summary": summary,
                })

            except Exception as e:
                logger.exception("Sales analysis gagal")
                return {
                    "top_customers": [],
                    "customer_segments": [],
                    "sales_trend": [],
                    "product_performance": [],
                    "regional_analysis": [],
                    "cross_selling_opportunities": [],
                    "summary": f"Gagal menganalisis penjualan: {e}",
                }
