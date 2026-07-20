import React, { useState, useCallback, useEffect } from "react";
import {
  DollarSign,
  Table2,
  RotateCcw,
  TrendingUp,
  TrendingDown,
  Minus,
  Lightbulb,
} from "lucide-react";

import {
  analyzeFinancial,
  FinancialResponse,
} from "../services/api";
import { useWorkbook } from "../contexts/WorkbookContext";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorAlert from "../components/ErrorAlert";

type PageState = "idle" | "loading" | "result" | "error";

const FinancialPage: React.FC = () => {
  const { activeSheet, isLoading, error: wbError } = useWorkbook();
  const [pageState, setPageState] = useState<PageState>("idle");
  const [loadingMessage, setLoadingMessage] = useState("Memproses...");
  const [error, setError] = useState<string | null>(null);
  const [dataSource, setDataSource] = useState<{
    headers: string[];
    data: unknown[][];
    sheetName: string;
  } | null>(null);
  const [result, setResult] = useState<FinancialResponse | null>(null);

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

  const handleAnalyze = useCallback(async () => {
    if (!dataSource) return;
    setError(null);
    setPageState("loading");
    setLoadingMessage("Menganalisis data keuangan...");
    try {
      const res = await analyzeFinancial(dataSource.data, dataSource.headers);
      setResult(res);
      setPageState("result");
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Gagal menganalisis data keuangan."
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

  const getStatusColor = (status: string): string => {
    switch (status.toLowerCase()) {
      case "healthy":
      case "good":
      case "baik":
        return "#2e7d32";
      case "warning":
      case "fair":
      case "sedang":
        return "#e65100";
      case "poor":
      case "critical":
      case "buruk":
        return "#d32f2f";
      default:
        return "#757575";
    }
  };

  const getStatusBadge = (status: string) => {
    const color = getStatusColor(status);
    return (
      <span
        className="fin-status-badge"
        style={{
          background: color + "18",
          color,
          border: `1px solid ${color}44`,
        }}
      >
        {status.toUpperCase()}
      </span>
    );
  };

  const getScoreBarColor = (score: number): string => {
    if (score >= 70) return "#2e7d32";
    if (score >= 40) return "#e65100";
    return "#d32f2f";
  };

  // Group ratios by category
  const groupedRatios: Record<string, FinancialResponse["ratios"]> = {};
  if (result) {
    result.ratios.forEach((r) => {
      if (!groupedRatios[r.category]) groupedRatios[r.category] = [];
      groupedRatios[r.category].push(r);
    });
  }

  const getCategoryLabel = (cat: string): string => {
    switch (cat.toLowerCase()) {
      case "profitability":
        return "Profitabilitas";
      case "liquidity":
        return "Likuiditas";
      case "efficiency":
        return "Efisiensi";
      case "solvency":
        return "Solvabilitas";
      case "leverage":
        return "Leverage";
      default:
        return cat;
    }
  };

  return (
    <div className="page-split">
      <div className="pane pane-left">
        <h2 className="page-title">Keuangan</h2>

        {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

        {wbError && !isLoading && (
          <ErrorAlert message={wbError} onDismiss={() => {}} />
        )}

        {isLoading && <LoadingSpinner message="Membaca data Excel..." />}

        {/* No data at all */}
        {!dataSource && !isLoading && (
          <div className="empty-state">
            <DollarSign size={40} style={{color:"var(--primary)",opacity:0.4}} />
            <p className="empty-state-text">
              Belum ada data keuangan. Buka add-in ini di Excel untuk mengambil data
              laporan keuangan dari lembar kerja aktif.
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
          <button className="btn btn-primary btn-full" onClick={handleAnalyze}>
            <DollarSign size={16} />
            Analisis Keuangan
          </button>
        )}

        {/* Loading */}
        {pageState === "loading" && <LoadingSpinner message={loadingMessage} />}

        {/* Error */}
        {pageState === "error" && error && (
          <ErrorAlert message={error} onDismiss={() => setError(null)} />
        )}

        {/* Health Score */}
        {pageState === "result" && result && (
          <div className="result-card">
            <div className="result-header">
              <h3>Skor Kesehatan</h3>
              {getStatusBadge(result.health_level)}
            </div>
            <div className="fin-health-score-bar-container">
              <div
                className="fin-health-score-bar"
                style={{
                  width: `${Math.min(result.health_score, 100)}%`,
                  background: getScoreBarColor(result.health_score),
                }}
              />
            </div>
            <div className="fin-health-score-value">
              <span
                className="fin-health-score-number"
                style={{ color: getScoreBarColor(result.health_score) }}
              >
                {result.health_score.toFixed(1)}
              </span>
              <span className="fin-health-score-max">/ 100</span>
            </div>
          </div>
        )}
      </div>

      <div className="pane pane-right">
        {/* Results */}
        {pageState === "result" && result && (
          <>
            {/* Ratios by Category */}
            {Object.keys(groupedRatios).length > 0 && (
              <div className="result-card">
                <h3>Rasio Keuangan</h3>
                {Object.entries(groupedRatios).map(([cat, ratios]) => (
                  <div key={cat} className="fin-ratio-category">
                    <h4 className="fin-ratio-category-title">
                      {getCategoryLabel(cat)}
                    </h4>
                    <div className="fin-ratios-table-wrapper">
                      <table className="fin-ratios-table">
                        <thead>
                          <tr>
                            <th>Rasio</th>
                            <th>Nilai</th>
                            <th>Benchmark</th>
                            <th>Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {ratios.map((ratio, ri) => (
                            <tr key={ri}>
                              <td className="fin-ratio-name">{ratio.name}</td>
                              <td className="fin-ratio-value">
                                {ratio.value.toFixed(2)}
                              </td>
                              <td className="fin-ratio-benchmark">
                                {ratio.benchmark.toFixed(2)}
                              </td>
                              <td>{getStatusBadge(ratio.status)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Insights */}
            {result.insights.length > 0 && (
              <div className="result-card">
                <h3>
                  <Lightbulb size={16} className="title-icon" />
                  Insight Keuangan
                </h3>
                <ul className="insights-list">
                  {result.insights.map((insight, i) => (
                    <li key={i}>{insight}</li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}

        {pageState !== "result" && !isLoading && (
          <div className="empty-state">
            <DollarSign size={40} style={{color:"var(--primary)",opacity:0.4}} />
            <p className="empty-state-text">
              Hasil analisis keuangan akan tampil di sini.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default FinancialPage;
