import React, { useState, useCallback, useEffect } from "react";
import { Sparkles, Wrench } from "lucide-react";
import {
  analyzeQuality,
  applyCleaning,
  Issue,
} from "../services/api";
import { useWorkbook } from "../contexts/WorkbookContext";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorAlert from "../components/ErrorAlert";

const SEVERITY_LABELS: Record<string, string> = {
  high: "Tinggi",
  medium: "Sedang",
  low: "Rendah",
};

const CleanerPage: React.FC = () => {
  const { activeSheet, isLoading, error: wbError } = useWorkbook();
  const [sheetData, setSheetData] = useState<{
    headers: string[];
    data: unknown[][];
    sheetName: string;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [cleaning, setCleaning] = useState(false);
  const [error, setError] = useState("");
  const [issues, setIssues] = useState<Issue[]>([]);
  const [selectedFixes, setSelectedFixes] = useState<Set<string>>(new Set());
  const [cleanResult, setCleanResult] = useState<{
    data: unknown[][];
    headers: string[];
    applied_fixes: string[];
  } | null>(null);
  const [writeSuccess, setWriteSuccess] = useState(false);

  // Sync sheetData from activeSheet when context data is available
  useEffect(() => {
    if (activeSheet) {
      setSheetData(activeSheet);
      setIssues([]);
      setCleanResult(null);
      setWriteSuccess(false);
    }
  }, [activeSheet]);

  const handleAnalyze = useCallback(async () => {
    if (!sheetData) return;
    setError("");
    setAnalyzing(true);
    setIssues([]);
    setCleanResult(null);
    setWriteSuccess(false);
    try {
      const res = await analyzeQuality(sheetData.data, sheetData.headers);
      setIssues(res.issues);

      // Auto-select all issues
      const autoSelect = new Set<string>();
      res.issues.forEach((issue: Issue) => {
        if (issue.type === "missing_values") {
          autoSelect.add("fill_missing_mean");
        } else if (issue.type === "duplicates") {
          autoSelect.add("remove_duplicates");
        } else if (issue.type === "outliers") {
          autoSelect.add("remove_outliers_iqr");
        } else if (issue.type === "constant_column") {
          autoSelect.add("drop_constant_columns");
        }
      });
      setSelectedFixes(autoSelect);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Gagal menganalisis kualitas.";
      setError(msg);
    } finally {
      setAnalyzing(false);
    }
  }, [sheetData]);

  const toggleFix = useCallback((fix: string) => {
    setSelectedFixes((prev) => {
      const next = new Set(prev);
      if (next.has(fix)) {
        next.delete(fix);
      } else {
        next.add(fix);
      }
      return next;
    });
  }, []);

  const handleApply = useCallback(async () => {
    if (!sheetData || selectedFixes.size === 0) return;
    setError("");
    setCleaning(true);
    setCleanResult(null);
    setWriteSuccess(false);
    try {
      const res = await applyCleaning(
        sheetData.data,
        sheetData.headers,
        Array.from(selectedFixes)
      );
      setCleanResult(res);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Gagal membersihkan data.";
      setError(msg);
    } finally {
      setCleaning(false);
    }
  }, [sheetData, selectedFixes]);

  const handleWriteToExcel = useCallback(async () => {
    if (!cleanResult) return;
    setError("");
    try {
      await Excel.run(async (context) => {
        const sheet = context.workbook.worksheets.getActiveWorksheet();
        const range = sheet.getRange("A1");
        const allData = [cleanResult.headers, ...cleanResult.data];
        const targetRange = range.getResizedRange(
          allData.length - 1,
          cleanResult.headers.length - 1
        );
        targetRange.values = allData;
        await context.sync();
      });
      setWriteSuccess(true);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Gagal menulis ke Excel.";
      setError(msg);
    }
  }, [cleanResult]);

  // Group issues by type
  const groupedIssues = issues.reduce<Record<string, Issue[]>>((acc, issue) => {
    if (!acc[issue.type]) acc[issue.type] = [];
    acc[issue.type].push(issue);
    return acc;
  }, {});

  const issueTypeLabels: Record<string, string> = {
    missing_values: "Nilai Hilang",
    duplicates: "Duplikasi",
    outliers: "Pencilan (Outlier)",
    invalid_data: "Data Tidak Valid",
    constant_column: "Kolom Konstan",
    high_cardinality: "Kardinalitas Tinggi",
  };

  return (
    <div className="page-split">
      <div className="pane pane-left">
        <h2 className="page-title">Bersihkan</h2>

        {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}

        {wbError && !isLoading && (
          <ErrorAlert message={wbError} onDismiss={() => {}} />
        )}

        {writeSuccess && (
          <div className="success-banner">
            Data berhasil ditulis kembali ke Excel!
          </div>
        )}

        {isLoading && <LoadingSpinner message="Membaca data Excel..." />}

        {/* Empty state - no data */}
        {!sheetData && !isLoading && (
          <div className="empty-state">
            <Sparkles size={40} style={{ color: "var(--primary)", opacity: 0.4 }} />
            <p className="empty-state-text">
              Baca data dari sheet Excel aktif untuk memulai pembersihan.
            </p>
          </div>
        )}

        {sheetData && (
          <>
            <div className="data-info">
              <span className="badge badge-info">{sheetData.sheetName}</span>
              <span className="data-dims">
                {sheetData.data.length} baris &times; {sheetData.headers.length}{" "}
                kolom
              </span>
            </div>

            {/* Data preview */}
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
            </div>

            <button
              className="btn btn-primary btn-full"
              onClick={handleAnalyze}
              disabled={analyzing}
            >
              {analyzing ? "Menganalisis..." : "Analisis Kualitas"}
            </button>

            {analyzing && <LoadingSpinner message="Menganalisis kualitas..." />}

            {/* Issues */}
            {issues.length > 0 && (
              <div className="issues-section">
                <h3>
                  Ditemukan {issues.length} Masalah
                </h3>

                {Object.entries(groupedIssues).map(([type, typeIssues]) => (
                  <div key={type} className="issue-group">
                    <h4 className="issue-group-title">
                      {issueTypeLabels[type] || type}
                    </h4>
                    {typeIssues.map((issue, i) => (
                      <div key={i} className="issue-item">
                        <div className="issue-item-header">
                          <span
                            className={`badge badge-${issue.severity}`}
                          >
                            {SEVERITY_LABELS[issue.severity]}
                          </span>
                          {issue.column && (
                            <span className="issue-column">{issue.column}</span>
                          )}
                        </div>
                        <p className="issue-description">{issue.suggestion}</p>
                        {issue.details && (
                          <p className="issue-details">
                            {JSON.stringify(issue.details)}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            )}

            {issues.length === 0 && !analyzing && (
              <div className="empty-state">
                <p className="text-muted">
                  Tidak ada masalah kualitas yang ditemukan.
                </p>
              </div>
            )}

            <button
              className="btn btn-secondary btn-full"
              onClick={() => {
                setSheetData(null);
                setIssues([]);
                setCleanResult(null);
                setError("");
                setWriteSuccess(false);
              }}
              style={{ marginTop: 12 }}
            >
              Reset
            </button>
          </>
        )}
      </div>

      <div className="pane pane-right">
        {cleaning && <LoadingSpinner message="Membersihkan data..." />}

        {/* Clean result */}
        {cleanResult && (
          <div className="result-card">
            <h3>Hasil Pembersihan</h3>
            <p className="changes-count">
              {cleanResult.applied_fixes.length} perubahan diterapkan
            </p>
            <ul className="fixes-applied">
              {cleanResult.applied_fixes.map((f, i) => (
                <li key={i}>{f}</li>
              ))}
            </ul>

            <h4>Data Setelah Dibersihkan</h4>
            <div className="preview-table-wrapper">
              <table className="preview-table">
                <thead>
                  <tr>
                    {cleanResult.headers.map((h, i) => (
                      <th key={i}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {cleanResult.data.slice(0, 5).map((row, ri) => (
                    <tr key={ri}>
                      {row.map((cell, ci) => (
                        <td key={ci}>{cell != null ? String(cell) : ""}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              {cleanResult.data.length > 5 && (
                <p className="preview-note">
                  Menampilkan 5 dari {cleanResult.data.length} baris
                </p>
              )}
            </div>

            <button
              className="btn btn-success btn-full"
              onClick={handleWriteToExcel}
            >
              Tulis ke Excel
            </button>
          </div>
        )}

        {issues.length > 0 && !cleanResult && !cleaning && (
          <div className="fixes-section">
            <h4>Pilih Perbaikan:</h4>
            {selectedFixes.size > 0 ? (
              <div className="fixes-list">
                {Array.from(selectedFixes).map((fix) => (
                  <label key={fix} className="fix-checkbox">
                    <input
                      type="checkbox"
                      checked={selectedFixes.has(fix)}
                      onChange={() => toggleFix(fix)}
                    />
                    <span>{fix.replace(/_/g, " ")}</span>
                  </label>
                ))}
              </div>
            ) : (
              <p className="text-muted">
                Tidak ada perbaikan yang dapat diterapkan secara otomatis.
              </p>
            )}

            <button
              className="btn btn-primary btn-full"
              onClick={handleApply}
              disabled={cleaning || selectedFixes.size === 0}
            >
              {cleaning
                ? "Membersihkan..."
                : `Terapkan Perbaikan (${selectedFixes.size})`}
            </button>
          </div>
        )}

        {!issues.length && !cleanResult && !cleaning && (
          <div className="empty-state">
            <Wrench size={40} style={{ color: "var(--primary)", opacity: 0.4 }} />
            <p className="empty-state-text">
              Hasil pembersihan akan tampil di sini setelah analisis dan perbaikan diterapkan.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CleanerPage;
