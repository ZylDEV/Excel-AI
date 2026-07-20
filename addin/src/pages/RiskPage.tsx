import React, { useState, useCallback, useEffect } from "react";
import {
  AlertTriangle,
  Table2,
  RotateCcw,
  Shield,
  TrendingUp,
  TrendingDown,
  Minus,
} from "lucide-react";

import {
  calculateRisk,
  RiskResponse,
} from "../services/api";
import { useWorkbook } from "../contexts/WorkbookContext";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorAlert from "../components/ErrorAlert";

type PageState = "idle" | "loading" | "result" | "error";

const RiskPage: React.FC = () => {
  const { activeSheet, isLoading, error: wbError } = useWorkbook();
  const [pageState, setPageState] = useState<PageState>("idle");
  const [loadingMessage, setLoadingMessage] = useState("Memproses...");
  const [error, setError] = useState<string | null>(null);
  const [dataSource, setDataSource] = useState<{
    headers: string[];
    data: unknown[][];
    sheetName: string;
  } | null>(null);
  const [result, setResult] = useState<RiskResponse | null>(null);

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

  const handleCalculateRisk = useCallback(async () => {
    if (!dataSource) return;
    setError(null);
    setPageState("loading");
    setLoadingMessage("Menghitung skor risiko...");
    try {
      const res = await calculateRisk(dataSource.data, dataSource.headers);
      setResult(res);
      setPageState("result");
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Gagal menghitung skor risiko."
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

  const getRiskColor = (level: string): string => {
    switch (level.toLowerCase()) {
      case "high":
      case "very high":
      case "critical":
        return "#d32f2f";
      case "medium":
      case "moderate":
        return "#e65100";
      case "low":
        return "#2e7d32";
      default:
        return "#1565c0";
    }
  };

  const getScoreBarColor = (score: number): string => {
    if (score >= 70) return "#d32f2f";
    if (score >= 40) return "#e65100";
    if (score >= 20) return "#f9a825";
    return "#2e7d32";
  };

  return (
    <div className="page">
      <h2 className="page-title">Risk</h2>

      {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

      {wbError && !isLoading && (
        <ErrorAlert message={wbError} onDismiss={() => {}} />
      )}

      {isLoading && <LoadingSpinner message="Membaca data Excel..." />}

      {/* No data at all */}
      {!dataSource && !isLoading && (
        <div className="empty-state">
          <AlertTriangle size={40} style={{color:"var(--primary)",opacity:0.4}} />
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
          onClick={handleCalculateRisk}
        >
          <AlertTriangle size={16} />
          Hitung Skor Risiko
        </button>
      )}

      {/* Loading */}
      {pageState === "loading" && <LoadingSpinner message={loadingMessage} />}

      {/* Error */}
      {pageState === "error" && error && (
        <ErrorAlert message={error} onDismiss={() => setError(null)} />
      )}

      {/* Results */}
      {pageState === "result" && result && (
        <>
          {/* Overall Score + Risk Level */}
          <div className="result-card">
            <h3>Skor Risiko Keseluruhan</h3>
            <div className="risk-score-wrapper">
              <div className="risk-score-bar-container">
                <div
                  className="risk-score-bar"
                  style={{
                    width: `${Math.min(result.overall_score, 100)}%`,
                    background: getScoreBarColor(result.overall_score),
                  }}
                />
              </div>
              <div className="risk-score-value-section">
                <span
                  className="risk-score-number"
                  style={{ color: getScoreBarColor(result.overall_score) }}
                >
                  {result.overall_score.toFixed(1)}
                </span>
                <span className="risk-score-max">/ 100</span>
              </div>
            </div>
            <div className="risk-level-section">
              <span className="risk-level-label">Tingkat Risiko:</span>
              <span
                className="risk-level-badge"
                style={{
                  background: getRiskColor(result.risk_level) + "18",
                  color: getRiskColor(result.risk_level),
                  border: `1px solid ${getRiskColor(result.risk_level)}44`,
                }}
              >
                {result.risk_level.toUpperCase()}
              </span>
            </div>
          </div>

          {/* Dimensions */}
          {result.dimensions.length > 0 && (
            <div className="result-card">
              <h3>
                <Shield size={16} className="title-icon" />
                Dimensi Risiko
              </h3>
              <div className="risk-dimensions-list">
                {result.dimensions.map((dim, i) => (
                  <div key={i} className="risk-dimension-card">
                    <div className="risk-dimension-header">
                      <div className="risk-dimension-name">
                        <strong>{dim.name}</strong>
                        <span className="risk-dimension-weight">
                          Bobot: {(dim.weight * 100).toFixed(0)}%
                        </span>
                      </div>
                      <span
                        className="risk-dimension-score-label"
                        style={{ color: getScoreBarColor(dim.score) }}
                      >
                        {dim.score.toFixed(1)}
                      </span>
                    </div>
                    <div className="risk-dimension-bar-wrapper">
                      <div
                        className="risk-dimension-bar-fill"
                        style={{
                          width: `${Math.min(dim.score, 100)}%`,
                          background: getScoreBarColor(dim.score),
                        }}
                      />
                    </div>
                    {dim.factors.length > 0 && (
                      <div className="risk-dimension-factors">
                        {dim.factors.map((factor, fi) => (
                          <span key={fi} className="risk-factor-tag">
                            {factor}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Details */}
          {result.details.length > 0 && (
            <div className="result-card">
              <h3>Detail Risiko</h3>
              <ul className="risk-details-list">
                {result.details.map((detail, i) => (
                  <li key={i} className="risk-detail-item">
                    {detail}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default RiskPage;
