"""API router for SQL database connector (V3)."""

import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    ConnectorTestRequest,
    ConnectorTestResponse,
    ConnectorTablesRequest,
    ConnectorTablesResponse,
    ConnectorPreviewRequest,
    ConnectorPreviewResponse,
    ConnectorImportRequest,
    ConnectorImportResponse,
)
from app.services.connector_service import (
    test_connection,
    get_tables,
    preview_table,
    import_data,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Database Connector V3"])


@router.post("/connector/test", response_model=ConnectorTestResponse)
async def api_test_connection(req: ConnectorTestRequest):
    """Test a database connection string."""
    try:
        result = test_connection(
            conn_string=req.connection_string,
            db_type=req.db_type or "",
        )
        return ConnectorTestResponse(**result)
    except Exception as e:
        logger.exception("Test koneksi gagal")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connector/tables", response_model=ConnectorTablesResponse)
async def api_get_tables(req: ConnectorTablesRequest):
    """Get list of tables from a database."""
    try:
        result = get_tables(
            conn_string=req.connection_string,
            db_type=req.db_type or "",
        )
        return ConnectorTablesResponse(**result)
    except Exception as e:
        logger.exception("Get tables gagal")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connector/preview", response_model=ConnectorPreviewResponse)
async def api_preview_table(req: ConnectorPreviewRequest):
    """Preview a table's structure and data."""
    try:
        result = preview_table(
            conn_string=req.connection_string,
            db_type=req.db_type or "",
            table=req.table_name,
        )
        return ConnectorPreviewResponse(**result)
    except Exception as e:
        logger.exception("Preview table gagal")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connector/import", response_model=ConnectorImportResponse)
async def api_import_data(req: ConnectorImportRequest):
    """Import data from a database using a custom SQL query."""
    try:
        result = import_data(
            conn_string=req.connection_string,
            db_type=req.db_type or "",
            query=req.query,
        )
        return ConnectorImportResponse(**result)
    except Exception as e:
        logger.exception("Import data gagal")
        raise HTTPException(status_code=500, detail=str(e))
