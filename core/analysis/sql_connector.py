"""SQL database connector service.

Supports PostgreSQL, MySQL, MSSQL, and SQLite.
Provides methods to connect, browse tables/columns, run queries, and disconnect.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class SQLConnector:
    """Connects to external databases and extracts data.

    Supported databases:
    - PostgreSQL
    - MySQL
    - Microsoft SQL Server
    - SQLite
    """

    SUPPORTED_DBS = ["postgresql", "mysql", "mssql", "sqlite"]

    def __init__(self):
        self._connection = None
        self._engine = None
        self._db_type = ""
        self._connected = False

    def connect(self, conn_string: str) -> bool:
        """Connect to a database using a connection string.

        Parameters
        ----------
        conn_string : str
            The full connection string for the database.
            Examples:
            - PostgreSQL: postgresql://user:pass@host:5432/dbname
            - MySQL: mysql+pymysql://user:pass@host:3306/dbname
            - MSSQL: mssql+pyodbc://user:pass@host/dbname?driver=...
            - SQLite: sqlite:///path/to/database.db

        Returns
        -------
        bool
            True if connection succeeded.
        """
        from sqlalchemy import create_engine, text

        try:
            # Detect database type from connection string
            conn_lower = conn_string.lower()
            for db_type in self.SUPPORTED_DBS:
                if conn_lower.startswith(db_type):
                    self._db_type = db_type
                    break
            if not self._db_type:
                # Try to detect from prefix
                if conn_lower.startswith("postgresql"):
                    self._db_type = "postgresql"
                elif conn_lower.startswith("mysql"):
                    self._db_type = "mysql"
                elif conn_lower.startswith("mssql"):
                    self._db_type = "mssql"
                elif conn_lower.startswith("sqlite"):
                    self._db_type = "sqlite"
                else:
                    raise ValueError(
                        f"Tipe database tidak dikenal. Gunakan salah satu: "
                        f"{', '.join(self.SUPPORTED_DBS)}"
                    )

            # Create engine with appropriate connect args
            connect_args = {}
            if self._db_type == "sqlite":
                connect_args["check_same_thread"] = False

            self._engine = create_engine(
                conn_string,
                connect_args=connect_args,
                pool_pre_ping=True,
                pool_recycle=3600,
            )

            # Test connection
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                conn.commit()

            self._connected = True
            logger.info(f"Berhasil terhubung ke database {self._db_type}")
            return True

        except Exception as e:
            logger.exception("Koneksi database gagal")
            self._connected = False
            self._engine = None
            raise ConnectionError(f"Gagal terhubung ke database: {e}")

    def get_tables(self) -> list[str]:
        """Get list of table names from the connected database.

        Returns
        -------
        list[str]
            Table names available in the database/schema.
        """
        from sqlalchemy import inspect, text

        if not self._connected or not self._engine:
            raise RuntimeError("Belum terhubung ke database. Panggil connect() terlebih dahulu.")

        try:
            inspector = inspect(self._engine)
            tables = inspector.get_table_names()

            # Also check for views
            try:
                with self._engine.connect() as conn:
                    result = conn.execute(
                        text(
                            "SELECT table_name FROM information_schema.views "
                            "WHERE table_schema = 'public'"
                        )
                    )
                    views = [row[0] for row in result]
                    tables.extend(views)
            except Exception:
                pass  # Views may not be supported on all DB types

            return sorted(set(tables))

        except Exception as e:
            logger.exception("Gagal mendapatkan daftar tabel")
            raise RuntimeError(f"Gagal mendapatkan daftar tabel: {e}")

    def get_columns(self, table: str) -> list[dict]:
        """Get column metadata for a given table.

        Parameters
        ----------
        table : str
            Table name.

        Returns
        -------
        list[dict]
            Each dict has keys: name, type, nullable, default.
        """
        from sqlalchemy import inspect

        if not self._connected or not self._engine:
            raise RuntimeError("Belum terhubung ke database. Panggil connect() terlebih dahulu.")

        try:
            inspector = inspect(self._engine)
            columns = inspector.get_columns(table)

            result = []
            for col in columns:
                result.append({
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col.get("nullable", True),
                    "default": str(col.get("default", "")) if col.get("default") is not None else None,
                    "primary_key": False,  # Will be updated below
                })

            # Mark primary keys
            try:
                pk_constraint = inspector.get_pk_constraint(table)
                pk_cols = pk_constraint.get("constrained_columns", [])
                for col_info in result:
                    if col_info["name"] in pk_cols:
                        col_info["primary_key"] = True
            except Exception:
                pass

            return result

        except Exception as e:
            logger.exception(f"Gagal mendapatkan kolom untuk tabel {table}")
            raise RuntimeError(f"Gagal mendapatkan kolom tabel '{table}': {e}")

    def query(self, sql: str) -> dict:
        """Execute a SQL query and return results.

        Parameters
        ----------
        sql : str
            The SQL query to execute.

        Returns
        -------
        dict with keys:
            - data : list[list] — rows of data
            - headers : list[str] — column names
            - row_count : int — number of rows returned
        """
        from sqlalchemy import text

        if not self._connected or not self._engine:
            raise RuntimeError("Belum terhubung ke database. Panggil connect() terlebih dahulu.")

        try:
            with self._engine.connect() as conn:
                result = conn.execute(text(sql))

                # Check if it returns results (SELECT) or just executes (INSERT/UPDATE/DELETE)
                if result.returns_rows:
                    headers = list(result.keys())
                    rows = [list(row) for row in result.fetchall()]

                    # Convert non-serializable types
                    cleaned_rows = []
                    for row in rows:
                        cleaned_row = []
                        for val in row:
                            if hasattr(val, "isoformat"):  # datetime
                                cleaned_row.append(str(val))
                            elif isinstance(val, (int, float)):
                                cleaned_row.append(val)
                            elif val is None:
                                cleaned_row.append(None)
                            else:
                                cleaned_row.append(str(val))
                        cleaned_rows.append(cleaned_row)

                    conn.commit()
                    return {
                        "data": cleaned_rows,
                        "headers": headers,
                        "row_count": len(cleaned_rows),
                    }
                else:
                    conn.commit()
                    return {
                        "data": [],
                        "headers": [],
                        "row_count": 0,
                        "message": "Query berhasil dieksekusi (bukan SELECT).",
                    }

        except Exception as e:
            logger.exception("Query gagal")
            raise RuntimeError(f"Gagal menjalankan query: {e}")

    def disconnect(self):
        """Close the database connection."""
        try:
            if self._engine:
                self._engine.dispose()
            self._connection = None
            self._engine = None
            self._connected = False
            self._db_type = ""
            logger.info("Koneksi database ditutup")
        except Exception as e:
            logger.warning(f"Gagal menutup koneksi: {e}")
