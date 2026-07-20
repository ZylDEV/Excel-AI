import React, { useState, useCallback, useEffect } from "react";
import {
  Lightbulb,
  Table2,
  RotateCcw,
  TrendingUp,
  TrendingDown,
  Minus,
  ArrowUp,
  ArrowDown,
  Activity,
  Link2,
  FileText,
  AlertTriangle,
} from "lucide-react";

import {
  generateInsights,
  InsightResponse,
} from "../services/api";
import { useWorkbook } from "../contexts/WorkbookContext";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorAlert from "../components/ErrorAlert";

type PageState = "idle" | "loading" | "result" | "error";

const InsightPage: React.FC = () => {
  const { activeSheet, isLoading, error: wbError } = useWorkbook();
  const [pageState, setPageState] = useState<PageState>("idle");
  const [loadingMessage, setLoadingMessage] = useState("Memproses...");
  const [error, setError] = useState<string | null>(null);
  const [dataSource, setDataSource] = useState<{
    headers: string[];
    data: unknown[][];
    sheetName: string;
  } | null>(null);
  const [insightResult, setInsightResult] = useState<InsightResponse | null>(null);

  // Sync dataSource from activeSheet
  useEffect(() => {
    if (activeSheet) {
      setDataSource(activeSheet);
      setInsightResult(null);
      setPageState("idle");
    } else {
      setDataSource(null);
    }
  }, [activeSheet]);

  const handleGenerate = useCallback(async () => {
    if (!dataSource) return;
    setError(null);
    setPageState("loading");
    setLoadingMessage("Menganalisis data dan menghasilkan insight...");
    try {
      const result = await generateInsights(
        dataSource.data,
        dataSource.headers,
        dataSource.sheetName
      );
      setInsightResult(result);
      setPageState("result");
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Gagal menghasilkan insight."
      );
      setPageState("error");
    }
  }, [dataSource]);

  const handleReset = useCallback(() => {
    setDataSource(null);
    setInsightResult(null);
    setError(null);
    setPageState("idle");
  }, []);

  const renderTrendDirection = (direction: string) => {
    switch (direction.toLowerCase()) {
      case "up":
      case "increasing":
      case "naik":
        return <ArrowUp size={18} className="trend-icon-up" />;
      case "down":
      case "decreasing":
      case "turun":
        return <ArrowDown size={18} className="trend-icon-down" />;
      default:
        return <Minus size={18} className="trend-icon-flat" />;
    }
  };

  const getCorrelationStrength = (pearson: number): { label: string; className: string } => {
    const abs = Math.abs(pearson);
    if (abs >= 0.8) return { label: "Sangat Kuat", className: "corr-very-strong" };
    if (abs >= 0.6) return { label: "Kuat", className: "corr-strong" };
    if (abs >= 0.4) return { label: "Sedang", className: "corr-moderate" };
    if (abs >= 0.2) return { label: "Lemah", className: "corr-weak" };
    return { label: "Sangat Lemah", className: "corr-very-weak" };
  };

  const renderZScoreBadge = (zScore: number) => {
    const abs = Math.abs(zScore);
    if (abs >= 3) return <span className="badge badge-high">Ekstrim</span>;
    if (abs >= 2) return <span className="badge badge-medium">Signifikan</span>;
    return <span className="badge badge-low">Ringan</span>;
  };

  return (
    <div className="page-split">
      <div className="pane pane-left">
        <h2 className="page-title">Insight</h2>

        {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

        {wbError && !isLoading && (
          <ErrorAlert message={wbError} onDismiss={() => {}} />
        )}

        {isLoading && <LoadingSpinner message="Membaca data Excel..." />}

        {/* No data at all */}
        {!dataSource && !isLoading && (
          <div className="empty-state">
            <Lightbulb size={40} style={{color:"var(--primary)",opacity:0.4}} />
            <p className="empty-state-text">
              Belum ada data. Buka add-in ini di Excel untuk mengambil data dari lembar
              kerja aktif.
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
                  {dataSource.data.length} baris &times; {dataSource.headers.length} kolom
                </span>
              </div>
              <button className="btn btn-sm btn-secondary" onClick={handleReset}>
                <RotateCcw size={14} />
                Reset
              </button>
            </div>

            {/* Preview */}
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
              <p className="preview-note">Menampilkan 5 dari {dataSource.data.length} baris</p>
            )}
          </div>
        )}

        {/* Generate Button */}
        {dataSource && pageState !== "result" && (
          <button className="btn btn-primary btn-full" onClick={handleGenerate}>
            <Lightbulb size={16} />
            Generate Insight
          </button>
        )}

        {/* Loading */}
        {pageState === "loading" && <LoadingSpinner message={loadingMessage} />}

        {/* Error */}
        {pageState === "error" && error && (
          <ErrorAlert message={error} onDismiss={() => setError(null)} />
        )}

        {/* AI Summary */}
        {pageState === "result" && insightResult && insightResult.summary && (
          <div className="result-card">
            <div className="result-header">
              <h3>
                <FileText size={16} className="inline-icon" />
                Ringkasan AI
              </h3>
            </div>
            <div className="explanation-text">
              <p>{insightResult.summary}</p>
            </div>
          </div>
        )}
      </div>

      <div className="pane pane-right">
        {/* Results */}
        {pageState === "result" && insightResult && (
          <>
            {/* Trends */}
            {insightResult.trends.length > 0 && (
              <div className="result-card">
                <h3>
                  <Activity size={16} className="inline-icon" />
                  Tren
                </h3>
                <div className="trends-list">
                  {insightResult.trends.map((trend, i) => (
                    <div key={i} className="trend-item">
                      <div className="trend-item-header">
                        <span className="trend-direction-icon">
                          {renderTrendDirection(trend.direction)}
                        </span>
                        <span className="trend-metric">{trend.metric}</span>
                        <span
                          className={`trend-change ${
                            trend.change_pct >= 0 ? "text-up" : "text-down"
                          }`}
                        >
                          {trend.change_pct >= 0 ? "+" : ""}
                          {trend.change_pct.toFixed(1)}%
                        </span>
                      </div>
                      <p className="trend-description">{trend.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Anomalies */}
            {insightResult.anomalies.length > 0 && (
              <div className="result-card">
                <h3>
                  <AlertTriangle size={16} className="inline-icon" />
                  Anomali
                </h3>
                <div className="anomalies-list">
                  {insightResult.anomalies.map((anomaly, i) => (
                    <div key={i} className="anomaly-item">
                      <div className="anomaly-item-header">
                        <span className="anomaly-column">{anomaly.column}</span>
                        {renderZScoreBadge(anomaly.z_score)}
                      </div>
                      <div className="anomaly-value">
                        Nilai:{" "}
                        <strong>
                          {typeof anomaly.value === "number"
                            ? anomaly.value.toLocaleString("id-ID")
                            : String(anomaly.value)}
                        </strong>
                        <span className="anomaly-zscore">
                          (Z-score: {anomaly.z_score.toFixed(2)})
                        </span>
                      </div>
                      <p className="anomaly-description">{anomaly.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Correlations */}
            {insightResult.correlations.length > 0 && (
              <div className="result-card">
                <h3>
                  <Link2 size={16} className="inline-icon" />
                  Korelasi
                </h3>
                <div className="correlations-list">
                  {insightResult.correlations.map((corr, i) => {
                    const strength = getCorrelationStrength(corr.pearson);
                    return (
                      <div key={i} className="correlation-item">
                        <div className="correlation-header">
                          <span className="correlation-vars">
                            {corr.col1} &times; {corr.col2}
                          </span>
                          <span className={`correlation-strength ${strength.className}`}>
                            {strength.label}
                          </span>
                        </div>
                        <div className="correlation-bar-wrapper">
                          <div className="correlation-bar">
                            <div
                              className="correlation-bar-fill"
                              style={{
                                width: `${Math.abs(corr.pearson) * 100}%`,
                                backgroundColor:
                                  corr.pearson >= 0 ? "#217346" : "#d32f2f",
                              }}
                            />
                          </div>
                          <span className="correlation-value">
                            {corr.pearson >= 0 ? "+" : ""}
                            {corr.pearson.toFixed(3)}
                          </span>
                        </div>
                        <p className="correlation-description">{corr.description}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </>
        )}

        {pageState !== "result" && !isLoading && (
          <div className="empty-state">
            <Lightbulb size={40} style={{color:"var(--primary)",opacity:0.4}} />
            <p className="empty-state-text">
              Insight akan tampil di sini setelah data dianalisis.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default InsightPage;
