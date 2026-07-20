import React, { useState, useCallback, useEffect, useMemo } from "react";
import {
  BarChart3,
  Download,
  FileText,
  Presentation,
  RotateCcw,
  Table2,
  TrendingUp,
  TrendingDown,
  Minus,
} from "lucide-react";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Bar, Line, Pie, Doughnut } from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

import {
  generateDashboard,
  generatePdf,
  generatePpt,
  DashboardResponse,
  ChartConfig,
} from "../services/api";
import { useWorkbook } from "../contexts/WorkbookContext";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorAlert from "../components/ErrorAlert";

type PageState = "idle" | "loading" | "result" | "error";

const CHART_COLORS = [
  "#217346",
  "#f57c00",
  "#1976d2",
  "#d32f2f",
  "#9c27b0",
  "#00838f",
  "#e91e63",
  "#4caf50",
];

const DashboardPage: React.FC = () => {
  const { activeSheet, isLoading, error: wbError } = useWorkbook();
  const [pageState, setPageState] = useState<PageState>("idle");
  const [loadingMessage, setLoadingMessage] = useState("Memproses...");
  const [error, setError] = useState<string | null>(null);
  const [dataSource, setDataSource] = useState<{
    headers: string[];
    data: unknown[][];
    sheetName: string;
  } | null>(null);
  const [dashboard, setDashboard] = useState<DashboardResponse["dashboard"] | null>(null);

  // Sync dataSource from activeSheet
  useEffect(() => {
    if (activeSheet) {
      setDataSource(activeSheet);
      setDashboard(null);
      setPageState("idle");
    } else {
      setDataSource(null);
    }
  }, [activeSheet]);

  const handleGenerate = useCallback(async () => {
    if (!dataSource) return;
    setError(null);
    setPageState("loading");
    setLoadingMessage("Membangun dashboard...");
    try {
      const result = await generateDashboard(
        dataSource.data,
        dataSource.headers,
        dataSource.sheetName
      );
      setDashboard(result.dashboard);
      setPageState("result");
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Gagal menghasilkan dashboard."
      );
      setPageState("error");
    }
  }, [dataSource]);

  const handleExportPdf = useCallback(async () => {
    if (!dashboard) return;
    setLoadingMessage("Menyiapkan PDF...");
    setPageState("loading");
    try {
      const result = await generatePdf(dashboard);
      window.open(result.download_url, "_blank");
      setPageState("result");
    } catch (err: any) {
      setError(err.message || "Gagal mengekspor PDF.");
      setPageState("error");
    }
  }, [dashboard]);

  const handleExportPpt = useCallback(async () => {
    if (!dashboard) return;
    setLoadingMessage("Menyiapkan PPT...");
    setPageState("loading");
    try {
      const result = await generatePpt(dashboard);
      window.open(result.download_url, "_blank");
      setPageState("result");
    } catch (err: any) {
      setError(err.message || "Gagal mengekspor PPT.");
      setPageState("error");
    }
  }, [dashboard]);

  const handleReset = useCallback(() => {
    setDataSource(null);
    setDashboard(null);
    setError(null);
    setPageState("idle");
  }, []);

  const renderChart = (chart: ChartConfig, index: number) => {
    const commonProps = {
      data: {
        labels: chart.labels,
        datasets: chart.datasets.map((ds, i) => ({
          ...ds,
          backgroundColor: ds.backgroundColor || CHART_COLORS,
          borderColor: CHART_COLORS[i % CHART_COLORS.length],
          borderWidth: chart.type === "line" ? 2 : 1,
          tension: chart.type === "line" ? 0.3 : undefined,
        })),
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            position: "bottom" as const,
            labels: { boxWidth: 12, padding: 12, font: { size: 11 } },
          },
          title: {
            display: true,
            text: chart.title,
            font: { size: 13, weight: "bold" as const },
            padding: { bottom: 8 },
          },
        },
        scales:
          chart.type === "pie" || chart.type === "doughnut"
            ? undefined
            : {
                x: { grid: { display: false }, ticks: { font: { size: 10 } } },
                y: {
                  beginAtZero: true,
                  grid: { color: "rgba(0,0,0,0.06)" },
                  ticks: { font: { size: 10 } },
                },
              },
      },
    };

    const chartStyle = { maxHeight: 220, marginBottom: 8 } as React.CSSProperties;

    switch (chart.type) {
      case "bar":
        return (
          <div key={index} className="dashboard-chart">
            <Bar {...commonProps} style={chartStyle} />
          </div>
        );
      case "line":
        return (
          <div key={index} className="dashboard-chart">
            <Line {...commonProps} style={chartStyle} />
          </div>
        );
      case "pie":
        return (
          <div key={index} className="dashboard-chart">
            <Pie {...commonProps} style={chartStyle} />
          </div>
        );
      case "doughnut":
        return (
          <div key={index} className="dashboard-chart">
            <Doughnut {...commonProps} style={chartStyle} />
          </div>
        );
      default:
        return null;
    }
  };

  const renderTrendIcon = (changePct: number) => {
    if (changePct > 0) return <TrendingUp size={16} />;
    if (changePct < 0) return <TrendingDown size={16} />;
    return <Minus size={16} />;
  };

  return (
    <div className="page-split">
      <div className="pane pane-left">
        <h2 className="page-title">Dashboard</h2>

        {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

        {wbError && !isLoading && (
          <ErrorAlert message={wbError} onDismiss={() => {}} />
        )}

        {isLoading && <LoadingSpinner message="Membaca data Excel..." />}

        {/* No data at all */}
        {!dataSource && !isLoading && (
          <div className="empty-state">
            <Download size={40} style={{color:"var(--primary)",opacity:0.4}} />
            <p className="empty-state-text">
              Belum ada data. Buka add-in ini di Excel untuk membaca data dari lembar
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
            <BarChart3 size={16} />
            Generate Dashboard
          </button>
        )}

        {/* Loading */}
        {pageState === "loading" && <LoadingSpinner message={loadingMessage} />}

        {/* Error */}
        {pageState === "error" && error && (
          <ErrorAlert message={error} onDismiss={() => setError(null)} />
        )}

        {/* KPI Cards */}
        {pageState === "result" && dashboard && (
          <div className="kpi-grid">
            {dashboard.kpis.map((kpi, i) => {
              const isPositive = kpi.change_pct > 0;
              const isNegative = kpi.change_pct < 0;
              return (
                <div
                  key={i}
                  className="kpi-card"
                  style={{ borderTopColor: kpi.color || CHART_COLORS[i % CHART_COLORS.length] }}
                >
                  <div className="kpi-header">
                    <span className="kpi-label">{kpi.label}</span>
                    <span
                      className={`kpi-trend ${isPositive ? "trend-up" : isNegative ? "trend-down" : "trend-flat"}`}
                    >
                      {renderTrendIcon(kpi.change_pct)}
                    </span>
                  </div>
                  <div className="kpi-value">
                    {kpi.prefix || ""}
                    {kpi.value.toLocaleString("id-ID")}
                    {kpi.suffix || ""}
                  </div>
                  <div
                    className={`kpi-change ${isPositive ? "text-up" : isNegative ? "text-down" : "text-flat"}`}
                  >
                    {isPositive ? "+" : ""}
                    {kpi.change_pct.toFixed(1)}%
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="pane pane-right">
        {/* Dashboard Results */}
        {pageState === "result" && dashboard && (
          <>
            {/* Charts */}
            {dashboard.charts.length > 0 && (
              <div className="result-card">
                <h3>Grafik</h3>
                <div className="charts-grid">
                  {dashboard.charts.map((chart, i) => renderChart(chart, i))}
                </div>
              </div>
            )}

            {/* Key Insights */}
            {dashboard.insights.length > 0 && (
              <div className="result-card">
                <h3>Insight Utama</h3>
                <ul className="insights-list">
                  {dashboard.insights.map((insight, i) => (
                    <li key={i}>{insight}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Export Buttons */}
            <div className="button-row">
              <button className="btn btn-success" onClick={handleExportPdf}>
                <FileText size={16} />
                Export PDF
              </button>
              <button className="btn btn-primary" onClick={handleExportPpt}>
                <Presentation size={16} />
                Export PPT
              </button>
            </div>
          </>
        )}

        {pageState !== "result" && !isLoading && (
          <div className="empty-state">
            <BarChart3 size={40} style={{color:"var(--primary)",opacity:0.4}} />
            <p className="empty-state-text">
              Dashboard akan tampil di sini setelah data dianalisis.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;
