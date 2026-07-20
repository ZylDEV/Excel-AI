"""Service for inventory intelligence."""

import logging
from typing import Any

from core.analysis.inventory_intelligence import InventoryAnalyzer
from core.utils.excel_reader import read_range

logger = logging.getLogger(__name__)


def analyze_inventory(
    data: list[list],
    headers: list[str],
    sheet_name: str = "",
) -> dict[str, Any]:
    """Analyze inventory data for stock insights and reorder suggestions.

    Parameters
    ----------
    data : list[list]
        2-D array of cell values.
    headers : list[str]
        Column header names.
    sheet_name : str
        Optional sheet name for context.

    Returns
    -------
    dict with keys: categories, stock_aging, reorder_suggestions,
                    overstock_items, warehouse_distribution, summary.
    """
    try:
        df = read_range(data=[headers] + data, headers=True)
        if df.empty:
            return {
                "categories": {},
                "stock_aging": [],
                "reorder_suggestions": [],
                "overstock_items": [],
                "warehouse_distribution": [],
                "summary": "Data inventaris kosong.",
            }

        analyzer = InventoryAnalyzer()
        result = analyzer.analyze(df)
        return result

    except Exception as e:
        logger.exception("Inventory analysis service gagal")
        return {
            "categories": {},
            "stock_aging": [],
            "reorder_suggestions": [],
            "overstock_items": [],
            "warehouse_distribution": [],
            "summary": f"Gagal menganalisis inventaris: {e}",
        }
