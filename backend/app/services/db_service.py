"""Service layer for database storage operations."""

import logging
from typing import Any

from core.utils.database import DatabaseManager

logger = logging.getLogger(__name__)

# Singleton instance — use the DATABASE_URL from config if available
_db_manager: DatabaseManager | None = None


def _get_db() -> DatabaseManager:
    """Get or create the DatabaseManager singleton."""
    global _db_manager
    if _db_manager is None:
        try:
            from app.config import settings

            db_url = settings.database_url
        except (ImportError, AttributeError):
            db_url = "sqlite:///./data/excel_genius.db"

        _db_manager = DatabaseManager(db_url)
    return _db_manager


def save_analysis(
    sheet_name: str,
    analysis_type: str,
    result: dict,
) -> dict[str, Any]:
    """Save an analysis result to the database.

    Parameters
    ----------
    sheet_name : str
        Name of the sheet being analysed.
    analysis_type : str
        Type of analysis.
    result : dict
        Analysis result data.

    Returns
    -------
    dict with keys: success, record_id, message.
    """
    try:
        db = _get_db()
        record_id = db.save_analysis(
            sheet_name=sheet_name,
            analysis_type=analysis_type,
            result=result,
        )

        if record_id > 0:
            return {
                "success": True,
                "record_id": record_id,
                "message": f"Analisis '{analysis_type}' untuk sheet '{sheet_name}' berhasil disimpan.",
            }
        else:
            return {
                "success": False,
                "record_id": -1,
                "message": "Gagal menyimpan analisis ke database.",
            }

    except Exception as exc:
        logger.exception("Gagal menyimpan analisis")
        return {
            "success": False,
            "record_id": -1,
            "message": f"Error: {exc}",
        }


def get_history(
    analysis_type: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Get analysis history from the database.

    Parameters
    ----------
    analysis_type : str | None
        Filter by analysis type (optional).
    limit : int
        Maximum records to return.

    Returns
    -------
    dict with keys: records, count, message.
    """
    try:
        db = _get_db()
        records = db.get_history(analysis_type=analysis_type, limit=limit)

        return {
            "records": records,
            "count": len(records),
            "message": f"Menampilkan {len(records)} record histori.",
        }

    except Exception as exc:
        logger.exception("Gagal mengambil histori analisis")
        return {
            "records": [],
            "count": 0,
            "message": f"Gagal mengambil histori: {exc}",
        }
