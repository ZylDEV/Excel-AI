"""Service for SQL database connector."""

import logging
from typing import Any

from core.analysis.sql_connector import SQLConnector

logger = logging.getLogger(__name__)


def test_connection(conn_string: str, db_type: str = "") -> dict[str, Any]:
    """Test a database connection.

    Parameters
    ----------
    conn_string : str
        The full connection string.
    db_type : str
        Database type hint (optional).

    Returns
    -------
    dict with keys: success (bool), message (str).
    """
    connector = SQLConnector()
    try:
        connector.connect(conn_string)
        connector.disconnect()
        return {
            "success": True,
            "message": "Koneksi berhasil terhubung ke database.",
        }
    except Exception as e:
        logger.exception("Test koneksi gagal")
        return {
            "success": False,
            "message": f"Koneksi gagal: {e}",
        }


def get_tables(conn_string: str, db_type: str = "") -> dict[str, Any]:
    """Get list of tables from a database.

    Parameters
    ----------
    conn_string : str
        The full connection string.
    db_type : str
        Database type hint (optional).

    Returns
    -------
    dict with keys: tables (list[str]), count (int).
    """
    connector = SQLConnector()
    try:
        connector.connect(conn_string)
        tables = connector.get_tables()
        connector.disconnect()
        return {
            "tables": tables,
            "count": len(tables),
        }
    except Exception as e:
        logger.exception("Gagal mendapatkan tabel")
        return {
            "tables": [],
            "count": 0,
            "error": str(e),
        }


def preview_table(conn_string: str, db_type: str, table: str) -> dict[str, Any]:
    """Preview a table's data and metadata.

    Parameters
    ----------
    conn_string : str
        The full connection string.
    db_type : str
        Database type hint.
    table : str
        Table name to preview.

    Returns
    -------
    dict with keys: columns, preview_data, row_count.
    """
    connector = SQLConnector()
    try:
        connector.connect(conn_string)

        # Get column metadata
        columns = connector.get_columns(table)

        # Preview first 50 rows
        preview = connector.query(f"SELECT * FROM \"{table}\" LIMIT 50")

        connector.disconnect()
        return {
            "columns": columns,
            "preview_data": preview.get("data", []),
            "preview_headers": preview.get("headers", []),
            "row_count": preview.get("row_count", 0),
        }
    except Exception as e:
        logger.exception(f"Gagal preview tabel {table}")
        return {
            "columns": [],
            "preview_data": [],
            "preview_headers": [],
            "row_count": 0,
            "error": str(e),
        }


def import_data(conn_string: str, db_type: str, query: str) -> dict[str, Any]:
    """Import data from a database using a custom SQL query.

    Parameters
    ----------
    conn_string : str
        The full connection string.
    db_type : str
        Database type hint.
    query : str
        SQL query to execute.

    Returns
    -------
    dict with keys: data, headers, row_count.
    """
    connector = SQLConnector()
    try:
        connector.connect(conn_string)
        result = connector.query(query)
        connector.disconnect()
        return result
    except Exception as e:
        logger.exception("Gagal import data dari database")
        return {
            "data": [],
            "headers": [],
            "row_count": 0,
            "error": str(e),
        }
