import React, { useState, useCallback, useEffect } from "react";
import {
  ShieldAlert,
  Table2,
  RotateCcw,
  AlertTriangle,
  CheckCircle2,
  Search,
  TrendingUp,
} from "lucide-react";

import {
  detectFraud,
  FraudResponse,
} from "../services/api";
import { useWorkbook } from "../contexts/WorkbookContext";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorAlert from "../components/ErrorAlert";

type PageState = "idle" | "loading" | "result" | "error";

const FraudPage: React.FC = () => {
  const { activeSheet, isLoading, error: wbError } = useWorkbook();
  const [pageState, setPageState] = useState<PageState>("idle");
  const [loadingMessage, setLoadingMessage] = useState("Memproses...");
  const [error, setError] = useState<string | null>(null);
  const [dataSource, setDataSource] = useState<{
    headers: string[];
    data: unknown[][];
    sheetName: string;
  } | null>(null);
  const [result, setResult] = useState<FraudResponse | null>(null);

  // Sync dataSource from activeSheet
  useEffect(() => {
    if (activeSheet) {
      setDataSource(activeSheet);
      setResult(null);
      setPageState("idle");
    } else {
      setDataSource(null);
    }
  }, [activeSheet]);

  const handleDetectFraud = useCallback(async () => {
    if (!dataSource) return;
    setError(null);
    setPageState("loading");
    setLoadingMessage("Mendeteksi kecurangan...");
    try {
      const res = await detectFraud(dataSource.data, dataSource.headers);
      setResult(res);
      setPageState("result");
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Gagal mendeteksi kecurangan."
      );
      setPageState("error");
    }
  }, [dataSource]);

  const handleReset = useCallback(() => {
    setDataSource(null);
    setResult(null);
    setError(null);
    setPageState("idle");
  }, []);

  const getScoreColor = (score: number): string => {
    if (score >= 70) return "#d32f2f";
    if (score >= 40) return "#e65100";
    if (score >= 20) return "#f9a825";
    return "#2e7d32";
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case "high":
      case "critical":
        return <span className="badge badge-high">Kritis</span>;
      case "medium":
        return <span className="badge badge-medium">Sedang</span>;
      case "low":
        return <span className="badge badge-low">Rendah</span>;
      default:
        return <span className="badge badge-info">{severity}</span>;
    }
  };

  return (
    <div className="page-split">
      <div className="pane pane-left">
        <h2 className="page-title">Fraud</h2>

        {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

        {wbError && !isLoading && (
          <ErrorAlert message={wbError} onDismiss={() => {}} />
        )}

        {isLoading && <LoadingSpinner message="Membaca data Excel..." />}

        {/* No data at all */}
        {!dataSource && !isLoading && (
          <div className="empty-state">
            <ShieldAlert size={40} style={{color:"var(--primary)",opacity:0.4}} />
            <p className="empty-state-text">
              Belum ada data. Buka add-in ini di Excel untuk mengambil data transaksi
              dari lembar kerja aktif.
            </p>
          </div>
        )}

        {/* Data Source Info */}
        {dataSource && (
          <div className="result-card">
            <div className="result-header">
              <div className="data-info">
                <Table2 size={16} />
                <strong>{dataSource.sheetName}</strong>
                <span className="data-dims">
                  {dataSource.data.length} baris &times;{" "}
                  {dataSource.headers.length} kolom
                </span>
              </div>
              <button className="btn btn-sm btn-secondary" onClick={handleReset}>
                <RotateCcw size={14} />
                Reset
              </button>
            </div>
            <div className="preview-table-wrapper">
              <table className="preview-table">
                <thead>
                  <tr>
                    {dataSource.headers.slice(0, 5).map((h, i) => (
                      <th key={i}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {dataSource.data.slice(0, 5).map((row, ri) => (
                    <tr key={ri}>
                      {row.slice(0, 5).map((cell, ci) => (
                        <td key={ci}>{String(cell ?? "")}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {dataSource.data.length > 5 && (
              <p className="preview-note">
                Menampilkan 5 dari {dataSource.data.length} baris
              </p>
            )}
          </div>
        )}

        {/* Analyze Button */}
        {dataSource && pageState !== "result" && (
          <button
            className="btn btn-primary btn-full"
            onClick={handleDetectFraud}
          >
            <ShieldAlert size={16} />
            Deteksi Kecurangan
          </button>
        )}

        {/* Loading */}
        {pageState === "loading" && <LoadingSpinner message={loadingMessage} />}

        {/* Error */}
        {pageState === "error" && error && (
          <ErrorAlert message={error} onDismiss={() => setError(null)} />
        )}
      </div>

      <div className="pane pane-right">
        {/* Results */}
        {pageState === "result" && result && (
          <>
            {/* Fraud Score */}
            <div className="result-card">
              <h3>Skor Kecurangan</h3>
              <div className="fraud-score-wrapper">
                <div
                  className="fraud-score-bar"
                  style={
                    {
                      "--score-pct": `${Math.min(result.fraud_score, 100)}%`,
                      "--score-color": getScoreColor(result.fraud_score),
                    } as React.CSSProperties
                  }
                >
                  <div
                    className="fraud-score-fill"
                    style={{
                      width: `${Math.min(result.fraud_score, 100)}%`,
                      background: getScoreColor(result.fraud_score),
                    }}
                  />
                </div>
                <div className="fraud-score-value">
                  <span
                    className="fraud-score-number"
                    style={{ color: getScoreColor(result.fraud_score) }}
                  >
                    {result.fraud_score.toFixed(1)}
                  </span>
                  <span className="fraud-score-max">/ 100</span>
                </div>
              </div>
            </div>

            {/* Summary */}
            {result.summary && (
              <div className="result-card">
                <h3>Ringkasan</h3>
                <p className="result-section">{result.summary}</p>
              </div>
            )}

            {/* Anomalies */}
            {result.anomalies.length > 0 && (
              <div className="result-card">
                <h3>
                  <AlertTriangle size={16} className="title-icon" />
                  Anomali Terdeteksi ({result.anomalies.length})
                </h3>
                <div className="anomalies-list-v3">
                  {result.anomalies.map((item, i) => (
                    <div key={i} className="anomaly-item-v3">
                      <div className="anomaly-item-v3-header">
                        <div className="anomaly-item-v3-left">
                          <strong>{item.column}</strong>
                          <span className="anomaly-item-v3-value">
                            {typeof item.value === "number"
                              ? item.value.toLocaleString("id-ID")
                              : String(item.value)}
                          </span>
                        </div>
                        {getSeverityBadge(item.severity)}
                      </div>
                      <p className="anomaly-item-v3-desc">{item.description}</p>
                      <div className="anomaly-item-v3-score">
                        Skor Anomali: {item.score.toFixed(2)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Suspicious Patterns */}
            {result.suspicious_patterns.length > 0 && (
              <div className="result-card">
                <h3>
                  <Search size={16} className="title-icon" />
                  Pola Mencurigakan ({result.suspicious_patterns.length})
                </h3>
                <div className="patterns-list-v3">
                  {result.suspicious_patterns.map((pat, i) => (
                    <div key={i} className="pattern-item-v3">
                      <div className="pattern-item-v3-header">
                        <strong>{pat.pattern}</strong>
                        <span className="badge badge-high">
                          {pat.count}x
                        </span>
                      </div>
                      <p className="pattern-item-v3-desc">{pat.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* No issues found */}
            {result.anomalies.length === 0 &&
              result.suspicious_patterns.length === 0 && (
                <div className="alert alert-success">
                  <CheckCircle2 size={16} />
                  Tidak ditemukan indikasi kecurangan pada data Anda.
                </div>
              )}
          </>
        )}

        {pageState !== "result" && !isLoading && (
          <div className="empty-state">
            <ShieldAlert size={40} style={{color:"var(--primary)",opacity:0.4}} />
            <p className="empty-state-text">
              Hasil deteksi kecurangan akan tampil di sini.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default FraudPage;
