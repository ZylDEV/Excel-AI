import React, { useState, useCallback, useEffect } from "react";
import { FileSpreadsheet } from "lucide-react";
import { explainData } from "../services/api";
import { useWorkbook } from "../contexts/WorkbookContext";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorAlert from "../components/ErrorAlert";

const ExplainPage: React.FC = () => {
  const { activeSheet, isLoading, error: wbError } = useWorkbook();
  const [sheetData, setSheetData] = useState<{
    headers: string[];
    data: unknown[][];
    sheetName: string;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [explaining, setExplaining] = useState(false);
  const [error, setError] = useState("");
  const [showManualInput, setShowManualInput] = useState(false);
  const [manualCsv, setManualCsv] = useState("");
  const [result, setResult] = useState<{
    insights: string[];
    statistics: Record<string, unknown>;
    explanation: string;
  } | null>(null);

  // Sync sheetData from activeSheet when context data is available
  useEffect(() => {
    if (activeSheet) {
      setSheetData(activeSheet);
      setShowManualInput(false);
      setResult(null);
    }
  }, [activeSheet]);

  const handleManualCsvParse = useCallback(() => {
    setError("");
    if (!manualCsv.trim()) {
      setError("Silakan tempel data CSV terlebih dahulu.");
      return;
    }
    try {
      const lines = manualCsv.trim().split("\n").filter(l => l.trim());
      if (lines.length < 2) {
        setError("Data harus memiliki setidaknya header dan satu baris data.");
        return;
      }
      const headers = lines[0].split(",").map(h => h.trim());
      const data = lines.slice(1).map(line => {
        return line.split(",").map(cell => {
          const trimmed = cell.trim();
          // Try to parse numbers
          const num = Number(trimmed);
          if (!isNaN(num) && trimmed !== "") return num;
          return trimmed;
        });
      });
      setSheetData({ headers, data, sheetName: "Data Manual" });
      setShowManualInput(false);
      setResult(null);
    } catch {
      setError("Gagal memparse data CSV. Pastikan formatnya benar.");
    }
  }, [manualCsv]);

  const handleExplain = useCallback(async () => {
    if (!sheetData) return;
    setError("");
    setExplaining(true);
    setResult(null);
    try {
      const res = await explainData(
        sheetData.data,
        sheetData.headers,
        sheetData.sheetName
      );
      setResult(res);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Gagal menganalisis data.";
      setError(msg);
    } finally {
      setExplaining(false);
    }
  }, [sheetData]);

  const statsEntries = result?.statistics
    ? Object.entries(result.statistics).filter(
        ([, v]) => typeof v === "object" && v !== null && !Array.isArray(v)
      )
    : [];

  return (
    <div className="page-split">
      <div className="pane pane-left">
        <h2 className="page-title">Analisis</h2>

        {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}

        {wbError && !isLoading && (
          <ErrorAlert message={wbError} onDismiss={() => {}} />
        )}

        {isLoading && <LoadingSpinner message="Membaca data Excel..." />}

        {/* Empty state - no data at all */}
        {!sheetData && !isLoading && (
          <div className="empty-state">
            <p className="empty-state-text">
              Baca data dari sheet Excel aktif untuk memulai analisis.
            </p>

            {/* Manual input toggle */}
            <button
              className="manual-input-toggle"
              onClick={() => setShowManualInput(!showManualInput)}
            >
              {showManualInput ? "Sembunyikan Input Manual" : "Input Data Manual (CSV)"}
            </button>

            {showManualInput && (
              <div className="manual-input-area">
                <textarea
                  className="form-textarea"
                  rows={6}
                  placeholder={
                    "Tempel data CSV di sini...\nContoh:\nBulan,Kota,Penjualan\nJan,Jakarta,100\nFeb,Bandung,200"
                  }
                  value={manualCsv}
                  onChange={(e) => setManualCsv(e.target.value)}
                />
                <p className="manual-hint">
                  Baris pertama akan digunakan sebagai header. Pisahkan nilai dengan koma.
                </p>
                <button
                  className="btn btn-primary btn-full"
                  onClick={handleManualCsvParse}
                  style={{ marginTop: 8 }}
                >
                  Gunakan Data Ini
                </button>
              </div>
            )}
          </div>
        )}

        {/* Data preview */}
        {sheetData && (
          <>
            <div className="data-info">
              <span className="badge badge-info">
                {sheetData.sheetName}
              </span>
              <span className="data-dims">
                {sheetData.data.length} baris &times; {sheetData.headers.length} kolom
              </span>
            </div>

            <div className="preview-table-wrapper">
              <table className="preview-table">
                <thead>
                  <tr>
                    {sheetData.headers.map((h, i) => (
                      <th key={i}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sheetData.data.slice(0, 5).map((row, ri) => (
                    <tr key={ri}>
                      {row.map((cell, ci) => (
                        <td key={ci}>{cell != null ? String(cell) : ""}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              {sheetData.data.length > 5 && (
                <p className="preview-note">
                  Menampilkan 5 dari {sheetData.data.length} baris
                </p>
              )}
            </div>

            <button
              className="btn btn-primary btn-full"
              onClick={handleExplain}
              disabled={explaining}
            >
              {explaining ? "Menganalisis..." : "Analisis Data"}
            </button>

            {explaining && (
              <LoadingSpinner message="AI sedang menganalisis data..." />
            )}

            {/* Reset */}
            <button
              className="btn btn-secondary btn-full"
              onClick={() => {
                setSheetData(null);
                setResult(null);
                setError("");
              }}
              style={{ marginTop: 12 }}
            >
              Reset
            </button>
          </>
        )}
      </div>

      <div className="pane pane-right">
        {/* Results */}
        {result && (
          <div className="result-card">
            <h3>Insight Utama</h3>
            <ul className="insights-list">
              {result.insights.map((insight, i) => (
                <li key={i}>{insight}</li>
              ))}
            </ul>

            <h3>Statistik</h3>
            {statsEntries.length > 0 ? (
              <div className="stats-grid">
                {statsEntries.map(([key, val]) => (
                  <details key={key} className="stats-group">
                    <summary className="stats-group-title">{key}</summary>
                    <div className="stats-group-body">
                      {Object.entries(val as Record<string, unknown>).map(
                        ([k, v]) => (
                          <div key={k} className="stat-row">
                            <span className="stat-key">{k}</span>
                            <span className="stat-value">
                              {typeof v === "object"
                                ? JSON.stringify(v)
                                : String(v ?? "-")}
                            </span>
                          </div>
                        )
                      )}
                    </div>
                  </details>
                ))}
              </div>
            ) : (
              <p className="text-muted">Tidak ada data statistik.</p>
            )}

            <h3>Penjelasan AI</h3>
            <div className="explanation-text">
              {result.explanation.split("\n").map((line, i) => (
                <p key={i}>{line || "\u00A0"}</p>
              ))}
            </div>
          </div>
        )}

        {!result && !explaining && (
          <div className="empty-state">
            <FileSpreadsheet size={40} style={{color:"var(--primary)",opacity:0.4}} />
            <p className="empty-state-text">
              Hasil analisis akan tampil di sini setelah data dianalisis.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExplainPage;
