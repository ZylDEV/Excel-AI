"""SQLite/PostgreSQL storage for workbook analysis history using SQLAlchemy."""

import json
import logging
from datetime import datetime, timezone
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# Attempt to import SQLAlchemy
try:
    from sqlalchemy import (
        Column,
        DateTime,
        Integer,
        String,
        Text,
        create_engine,
    )
    from sqlalchemy.orm import DeclarativeBase, Session

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logger.info("SQLAlchemy tidak tersedia, database storage tidak dapat digunakan")


if SQLALCHEMY_AVAILABLE:

    class _Base(DeclarativeBase):
        pass

    class _AnalysisRecord(_Base):
        """ORM model for storing analysis results."""
        __tablename__ = "analysis_history"

        id = Column(Integer, primary_key=True, autoincrement=True)
        sheet_name = Column(String(255), nullable=False, index=True)
        analysis_type = Column(String(100), nullable=False, index=True)
        result_json = Column(Text, nullable=False)
        created_at = Column(DateTime, default=datetime.now(timezone.utc))

    class _WorkbookData(_Base):
        """ORM model for storing workbook raw data."""
        __tablename__ = "workbook_data"

        id = Column(Integer, primary_key=True, autoincrement=True)
        sheet_name = Column(String(255), nullable=False, unique=True, index=True)
        headers_json = Column(Text, nullable=False)
        data_json = Column(Text, nullable=False)
        row_count = Column(Integer, default=0)
        created_at = Column(DateTime, default=datetime.now(timezone.utc))
        updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))


class DatabaseManager:
    """Store and retrieve workbook analysis history using SQLAlchemy.

    Supports both SQLite (default) and PostgreSQL backends.
    """

    def __init__(self, db_url: str = "sqlite:///./data/excel_genius.db"):
        """Initialize database engine and create tables if needed.

        Parameters
        ----------
        db_url : str
            SQLAlchemy database URL. Default: ``sqlite:///./data/excel_genius.db``
        """
        self._db_url = db_url
        self._engine = None
        self._session_cls = None

        if not SQLALCHEMY_AVAILABLE:
            logger.warning(
                "SQLAlchemy tidak terinstall. DatabaseManager tidak akan berfungsi. "
                "Jalankan: pip install sqlalchemy"
            )
            return

        try:
            self._engine = create_engine(db_url, echo=False)
            _Base.metadata.create_all(self._engine)
            self._session_cls = Session
            logger.info("Database terhubung: %s", db_url)
        except Exception as exc:
            logger.exception("Gagal menginisialisasi database: %s", db_url)
            self._engine = None
            self._session_cls = None

    @property
    def _is_ready(self) -> bool:
        return self._engine is not None and self._session_cls is not None

    def _get_session(self):
        """Create a new database session."""
        if not self._is_ready:
            raise RuntimeError("Database tidak tersedia. Periksa koneksi SQLAlchemy.")
        return self._session_cls(bind=self._engine)

    @staticmethod
    def _serialize(obj: Any) -> str:
        """Serialize a Python object to JSON, handling numpy types."""
        def _default(o):
            if isinstance(o, np.integer):
                return int(o)
            if isinstance(o, np.floating):
                return float(o)
            if isinstance(o, np.bool_):
                return bool(o)
            if isinstance(o, np.ndarray):
                return o.tolist()
            if isinstance(o, datetime):
                return o.isoformat()
            raise TypeError(f"Object of type {type(o)} is not JSON serializable")
        return json.dumps(obj, default=_default)

    def save_analysis(
        self, sheet_name: str, analysis_type: str, result: dict
    ) -> int:
        """Save an analysis result to the database.

        Parameters
        ----------
        sheet_name : str
            Name of the sheet being analysed.
        analysis_type : str
            Type of analysis (e.g. ``"dashboard"``, ``"forecast"``, ``"fraud"``).
        result : dict
            Analysis result data.

        Returns
        -------
        int
            The ID of the saved record, or -1 if saving failed.
        """
        if not self._is_ready:
            logger.error("Database tidak siap, tidak dapat menyimpan analisis")
            return -1

        try:
            with self._get_session() as session:
                record = _AnalysisRecord(
                    sheet_name=sheet_name,
                    analysis_type=analysis_type,
                    result_json=self._serialize(result),
                )
                session.add(record)
                session.commit()
                record_id = record.id
                logger.info(
                    "Analisis tersimpan: id=%d, sheet='%s', type='%s'",
                    record_id,
                    sheet_name,
                    analysis_type,
                )
                return record_id if record_id is not None else -1
        except Exception as exc:
            logger.exception("Gagal menyimpan analisis ke database")
            return -1

    def get_history(
        self, analysis_type: str | None = None, limit: int = 20
    ) -> list[dict]:
        """Get analysis history from the database.

        Parameters
        ----------
        analysis_type : str | None
            If provided, filter by analysis type.
        limit : int
            Maximum number of records to return (default 20).

        Returns
        -------
        list[dict] with keys: id, sheet_name, analysis_type, result, created_at.
        """
        if not self._is_ready:
            logger.error("Database tidak siap, tidak dapat mengambil histori")
            return []

        try:
            with self._get_session() as session:
                query = session.query(_AnalysisRecord)

                if analysis_type:
                    query = query.filter(_AnalysisRecord.analysis_type == analysis_type)

                records = (
                    query.order_by(_AnalysisRecord.created_at.desc())
                    .limit(limit)
                    .all()
                )

                history = []
                for rec in records:
                    try:
                        result_data = json.loads(rec.result_json)
                    except (json.JSONDecodeError, TypeError):
                        result_data = {}

                    history.append({
                        "id": rec.id,
                        "sheet_name": rec.sheet_name,
                        "analysis_type": rec.analysis_type,
                        "result": result_data,
                        "created_at": rec.created_at.isoformat() if rec.created_at else None,
                    })

                return history

        except Exception as exc:
            logger.exception("Gagal mengambil histori analisis")
            return []

    def get_workbook_data(self, sheet_name: str) -> dict | None:
        """Get previously saved workbook data.

        Parameters
        ----------
        sheet_name : str
            Name of the sheet.

        Returns
        -------
        dict with keys: headers, data, row_count, created_at, updated_at,
        or None if not found.
        """
        if not self._is_ready:
            logger.error("Database tidak siap, tidak dapat mengambil data workbook")
            return None

        try:
            with self._get_session() as session:
                record = (
                    session.query(_WorkbookData)
                    .filter(_WorkbookData.sheet_name == sheet_name)
                    .first()
                )

                if record is None:
                    return None

                try:
                    headers = json.loads(record.headers_json)
                except (json.JSONDecodeError, TypeError):
                    headers = []

                try:
                    data = json.loads(record.data_json)
                except (json.JSONDecodeError, TypeError):
                    data = []

                return {
                    "headers": headers,
                    "data": data,
                    "row_count": record.row_count,
                    "created_at": record.created_at.isoformat() if record.created_at else None,
                    "updated_at": record.updated_at.isoformat() if record.updated_at else None,
                }

        except Exception as exc:
            logger.exception("Gagal mengambil data workbook: %s", sheet_name)
            return None
