import React, { useState, useCallback } from "react";
import {
  Database,
  Plug,
  Table2,
  RotateCcw,
  Eye,
  Download,
  CheckCircle2,
  XCircle,
  Loader2,
  ChevronDown,
  FileSpreadsheet,
} from "lucide-react";

import {
  testConnection,
  getConnectorTables,
  previewTable,
  importData,
} from "../services/api";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorAlert from "../components/ErrorAlert";

type PageState = "idle" | "connecting" | "connected" | "loading" | "result" | "error";

const DB_TYPES = [
  { value: "postgresql", label: "PostgreSQL" },
  { value: "mysql", label: "MySQL" },
  { value: "sqlserver", label: "SQL Server" },
  { value: "sqlite", label: "SQLite" },
];

const ConnectorPage: React.FC = () => {
  const [pageState, setPageState] = useState<PageState>("idle");
  const [loadingMessage, setLoadingMessage] = useState("Memproses...");
  const [error, setError] = useState<string | null>(null);

  // Connection form
  const [connString, setConnString] = useState("");
  const [dbType, setDbType] = useState("postgresql");

  // Connection result
  const [connectionMessage, setConnectionMessage] = useState("");
  const [connectionSuccess, setConnectionSuccess] = useState(false);

  // Tables
  const [tables, setTables] = useState<{ name: string; schema: string }[]>([]);
  const [selectedTable, setSelectedTable] = useState("");

  // Imported data
  const [importedData, setImportedData] = useState<{
    headers: string[];
    data: unknown[][];
    rowCount: number;
  } | null>(null);
  const [previewData, setPreviewData] = useState<{
    headers: string[];
    data: unknown[][];
  } | null>(null);

  const handleTestConnection = useCallback(async () => {
    if (!connString.trim()) {
      setError("Silakan masukkan connection string terlebih dahulu.");
      return;
    }
    setError(null);
    setPageState("connecting");
    setLoadingMessage("Menguji koneksi...");
    setTables([]);
    setSelectedTable("");
    setImportedData(null);
    setPreviewData(null);
    try {
      const res = await testConnection(connString, dbType);
      setConnectionSuccess(res.success);
      setConnectionMessage(res.message);
      if (res.success) {
        setPageState("connected");
      } else {
        setPageState("idle");
      }
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Gagal menguji koneksi."
      );
      setPageState("idle");
    }
  }, [connString, dbType]);

  const handleLoadTables = useCallback(async () => {
    setError(null);
    setPageState("loading");
    setLoadingMessage("Memuat daftar tabel...");
    try {
      const res = await getConnectorTables(connString, dbType);
      setTables(res.tables);
      setPageState("connected");
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Gagal memuat daftar tabel."
      );
      setPageState("connected");
    }
  }, [connString, dbType]);

  const handlePreviewTable = useCallback(async () => {
    if (!selectedTable) {
      setError("Silakan pilih tabel terlebih dahulu.");
      return;
    }
    setError(null);
    setPageState("loading");
    setLoadingMessage("Memuat pratinjau tabel...");
    try {
      const res = await previewTable(connString, dbType, selectedTable);
      setPreviewData(res);
      setImportedData(null);
      setPageState("connected");
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Gagal memuat pratinjau tabel."
      );
      setPageState("connected");
    }
  }, [connString, dbType, selectedTable]);

  const handleImportTable = useCallback(async () => {
    if (!selectedTable) {
      setError("Silakan pilih tabel terlebih dahulu.");
      return;
    }
    setError(null);
    setPageState("loading");
    setLoadingMessage("Mengimpor data...");
    try {
      const query = `SELECT * FROM ${selectedTable}`;
      const res = await importData(connString, dbType, query);
      setImportedData({
        headers: res.headers,
        data: res.data,
        rowCount: res.row_count,
      });
      setPreviewData(null);
      setPageState("result");
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Gagal mengimpor data."
      );
      setPageState("connected");
    }
  }, [connString, dbType, selectedTable]);

  const handleReset = useCallback(() => {
    setError(null);
    setPageState("idle");
    setConnString("");
    setDbType("postgresql");
    setConnectionMessage("");
    setConnectionSuccess(false);
    setTables([]);
    setSelectedTable("");
    setImportedData(null);
    setPreviewData(null);
  }, []);

  return (
    <div className="page">
      <h2 className="page-title">Konektor</h2>

      {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

      {/* Connection Form */}
      <div className="result-card">
        <h3>Konfigurasi Koneksi</h3>
        <div className="form-group">
          <label className="form-label">Tipe Database</label>
          <select
            className="form-select"
            value={dbType}
            onChange={(e) => setDbType(e.target.value)}
            disabled={pageState === "connecting" || pageState === "loading"}
          >
            {DB_TYPES.map((db) => (
              <option key={db.value} value={db.value}>
                {db.label}
              </option>
            ))}
          </select>
        </div>
        <div className="form-group" style={{ marginTop: 8 }}>
          <label className="form-label">Connection String</label>
          <input
            className="form-input"
            type="text"
            value={connString}
            onChange={(e) => setConnString(e.target.value)}
            placeholder={
              dbType === "sqlite"
                ? "contoh: sqlite:///path/to/database.db"
                : dbType === "mysql"
                ? "contoh: mysql://user:pass@localhost:3306/dbname"
                : dbType === "sqlserver"
                ? "contoh: mssql://user:pass@host:1433/dbname"
                : "contoh: postgresql://user:pass@localhost:5432/dbname"
            }
            disabled={pageState === "connecting" || pageState === "loading"}
          />
        </div>

        <div className="button-row" style={{ marginTop: 8 }}>
          <button
            className="btn btn-primary"
            onClick={handleTestConnection}
            disabled={
              pageState === "connecting" ||
              pageState === "loading" ||
              !connString.trim()
            }
          >
            {pageState === "connecting" ? (
              <>
                <Loader2 size={16} className="spin-icon" />
                Menguji...
              </>
            ) : (
              <>
                <Plug size={16} />
                Uji Koneksi
              </>
            )}
          </button>
          {(pageState === "connected" || pageState === "result") && (
            <button className="btn btn-secondary" onClick={handleReset}>
              <RotateCcw size={16} />
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Connection Result */}
      {connectionMessage && (
        <div
          className={`alert ${connectionSuccess ? "alert-success" : "alert-error"}`}
        >
          {connectionSuccess ? (
            <CheckCircle2 size={16} />
          ) : (
            <XCircle size={16} />
          )}
          {connectionMessage}
        </div>
      )}

      {/* Loading */}
      {pageState === "loading" && <LoadingSpinner message={loadingMessage} />}

      {/* Table Browser */}
      {(pageState === "connected" || pageState === "result") && (
        <>
          <div className="result-card">
            <div className="result-header">
              <h3>
                <Table2 size={16} className="title-icon" />
                Browser Tabel
              </h3>
              <button
                className="btn btn-sm btn-secondary"
                onClick={handleLoadTables}
              >
                <Database size={14} />
                Muat Tabel
              </button>
            </div>

            {tables.length > 0 && (
              <>
                <div className="form-group">
                  <label className="form-label">Pilih Tabel</label>
                  <select
                    className="form-select"
                    value={selectedTable}
                    onChange={(e) => {
                      setSelectedTable(e.target.value);
                      setPreviewData(null);
                      setImportedData(null);
                    }}
                  >
                    <option value="">-- Pilih tabel --</option>
                    {tables.map((t, i) => (
                      <option key={i} value={t.name}>
                        {t.schema ? `${t.schema}.${t.name}` : t.name}
                      </option>
                    ))}
                  </select>
                </div>

                {selectedTable && (
                  <div className="button-row" style={{ marginTop: 8 }}>
                    <button
                      className="btn btn-outline"
                      onClick={handlePreviewTable}
                    >
                      <Eye size={16} />
                      Pratinjau
                    </button>
                    <button
                      className="btn btn-primary"
                      onClick={handleImportTable}
                    >
                      <Download size={16} />
                      Impor Data
                    </button>
                  </div>
                )}
              </>
            )}

            {tables.length === 0 && (
              <p className="text-muted" style={{ textAlign: "center", padding: 12 }}>
                Klik "Muat Tabel" untuk menampilkan daftar tabel dari database.
              </p>
            )}
          </div>

          {/* Preview Data */}
          {previewData && (
            <div className="result-card">
              <h3>
                <Eye size={16} className="title-icon" />
                Pratinjau: {selectedTable}
              </h3>
              <div className="preview-table-wrapper">
                <table className="preview-table">
                  <thead>
                    <tr>
                      {previewData.headers.map((h, i) => (
                        <th key={i}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {previewData.data.slice(0, 10).map((row, ri) => (
                      <tr key={ri}>
                        {row.map((cell, ci) => (
                          <td key={ci}>{cell != null ? String(cell) : ""}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {previewData.data.length > 10 && (
                <p className="preview-note">
                  Menampilkan 10 dari {previewData.data.length} baris
                </p>
              )}
            </div>
          )}

          {/* Imported Data */}
          {importedData && (
            <div className="result-card">
              <div className="result-header">
                <h3>
                  <Download size={16} className="title-icon" />
                  Data Terimpor: {selectedTable}
                </h3>
              </div>
              <div className="data-info">
                <Table2 size={16} />
                <strong>{importedData.rowCount} baris</strong>
                <span className="data-dims">
                  &times; {importedData.headers.length} kolom
                </span>
              </div>
              <div className="preview-table-wrapper">
                <table className="preview-table">
                  <thead>
                    <tr>
                      {importedData.headers.map((h, i) => (
                        <th key={i}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {importedData.data.slice(0, 10).map((row, ri) => (
                      <tr key={ri}>
                        {row.map((cell, ci) => (
                          <td key={ci}>{cell != null ? String(cell) : ""}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {importedData.data.length > 10 && (
                <p className="preview-note">
                  Menampilkan 10 dari {importedData.data.length} baris
                </p>
              )}
            </div>
          )}
        </>
      )}

      {/* Idle */}
      {pageState === "idle" && !connectionMessage && (
        <div className="empty-state">
          <Database size={40} style={{color:"var(--primary)",opacity:0.4}} />
          <p className="empty-state-text">
            Hubungkan ke database SQL Anda untuk mengimpor data langsung ke
            Excel AI. Masukkan connection string dan pilih tipe database
            untuk memulai.
          </p>
        </div>
      )}
    </div>
  );
};

export default ConnectorPage;
