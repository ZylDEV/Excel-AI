import React, { useState, useCallback, useEffect, useMemo } from "react";
import {
  TrendingUp,
  Table2,
  RotateCcw,
  Play,
  Calendar,
} from "lucide-react";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line } from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

import {
  runForecast,
  ForecastResponse,
} from "../services/api";
import { useWorkbook } from "../contexts/WorkbookContext";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorAlert from "../components/ErrorAlert";

type PageState = "idle" | "loading" | "result" | "error";

const PERIOD_OPTIONS = [
  { value: 3, label: "3 Bulan" },
  { value: 6, label: "6 Bulan" },
  { value: 12, label: "12 Bulan" },
];

const ForecastPage: React.FC = () => {
  const { activeSheet, isLoading, error: wbError } = useWorkbook();
  const [pageState, setPageState] = useState<PageState>("idle");
  const [loadingMessage, setLoadingMessage] = useState("Memproses...");
  const [error, setError] = useState<string | null>(null);
  const [dataSource, setDataSource] = useState<{
    headers: string[];
    data: unknown[][];
    sheetName: string;
  } | null>(null);
  const [dateCol, setDateCol] = useState("");
  const [valueCol, setValueCol] = useState("");
  const [periods, setPeriods] = useState(6);
  const [forecastResult, setForecastResult] = useState<ForecastResponse | null>(null);

  // Sync dataSource from activeSheet
  useEffect(() => {
    if (activeSheet) {
      setDataSource(activeSheet);
      setForecastResult(null);
      // Auto-detect date and value columns
      if (activeSheet.headers.length > 0) {
        setDateCol(activeSheet.headers[0]);
        setValueCol(activeSheet.headers.length > 1 ? activeSheet.headers[1] : activeSheet.headers[0]);
      }
      setPageState("idle");
    } else {
      setDataSource(null);
    }
  }, [activeSheet]);

  const handleRunForecast = useCallback(async () => {
    if (!dataSource) return;
    setError(null);
    setPageState("loading");
    setLoadingMessage("Menjalankan forecast...");
    try {
      const result = await runForecast(
        dataSource.data,
        dataSource.headers,
        dateCol,
        valueCol,
        periods
      );
      setForecastResult(result);
      setPageState("result");
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Gagal menjalankan forecast."
      );
      setPageState("error");
    }
  }, [dataSource, dateCol, valueCol, periods]);

  const handleReset = useCallback(() => {
    setDataSource(null);
    setForecastResult(null);
    setError(null);
    setPageState("idle");
    setDateCol("");
    setValueCol("");
    setPeriods(6);
  }, []);

  // Build chart data
  const chartData = useMemo(() => {
    if (!forecastResult) return null;

    // Combine history + forecast dates for x-axis
    const allDates = [
      ...forecastResult.history.map((h) => h.ds),
      ...forecastResult.forecast.map((f) => f.ds),
    ];

    // History values + null padding for forecast period
    const historyValues = [
      ...forecastResult.history.map((h) => h.y),
      ...forecastResult.forecast.map(() => null),
    ];

    // Null padding for history + forecast values
    const forecastValues = [
      ...forecastResult.history.map(() => null),
      ...forecastResult.forecast.map((f) => f.yhat),
    ];

    // Confidence interval upper/lower
    const upperValues = [
      ...forecastResult.history.map(() => null),
      ...forecastResult.forecast.map((f) => f.yhat_upper),
    ];
    const lowerValues = [
      ...forecastResult.history.map(() => null),
      ...forecastResult.forecast.map((f) => f.yhat_lower),
    ];

    return {
      labels: allDates,
      datasets: [
        {
          label: "Riwayat",
          data: historyValues,
          borderColor: "#217346",
          backgroundColor: "#217346",
          borderWidth: 2,
          pointRadius: 3,
          pointBackgroundColor: "#217346",
          tension: 0.3,
          spanGaps: false,
        },
        {
          label: "Forecast",
          data: forecastValues,
          borderColor: "#f57c00",
          backgroundColor: "#f57c00",
          borderWidth: 2,
          borderDash: [5, 5],
          pointRadius: 3,
          pointBackgroundColor: "#f57c00",
          tension: 0.3,
          spanGaps: false,
        },
        {
          label: "Batas Atas",
          data: upperValues,
          borderColor: "rgba(245, 124, 0, 0.2)",
          backgroundColor: "rgba(245, 124, 0, 0.05)",
          borderWidth: 1,
          borderDash: [3, 3],
          pointRadius: 0,
          fill: "+2",
          tension: 0.3,
          spanGaps: false,
        },
        {
          label: "Batas Bawah",
          data: lowerValues,
          borderColor: "rgba(245, 124, 0, 0.2)",
          backgroundColor: "rgba(245, 124, 0, 0.05)",
          borderWidth: 1,
          borderDash: [3, 3],
          pointRadius: 0,
          fill: false,
          tension: 0.3,
          spanGaps: false,
        },
      ],
    };
  }, [forecastResult]);

  return (
    <div className="page-split">
      <div className="pane pane-left">
        <h2 className="page-title">Forecast</h2>

        {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

        {wbError && !isLoading && (
          <ErrorAlert message={wbError} onDismiss={() => {}} />
        )}

        {isLoading && <LoadingSpinner message="Membaca data Excel..." />}

        {/* No data at all */}
        {!dataSource && !isLoading && (
          <div className="empty-state">
            <TrendingUp size={40} style={{color:"var(--primary)",opacity:0.4}} />
            <p className="empty-state-text">
              Belum ada data. Buka add-in ini di Excel untuk mengambil data time series
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
                  {dataSource.data.length} baris &times; {dataSource.headers.length} kolom
                </span>
              </div>
              <button className="btn btn-sm btn-secondary" onClick={handleReset}>
                <RotateCcw size={14} />
                Reset
              </button>
            </div>

            {/* Column Selectors */}
            <div className="input-row" style={{ marginTop: 8 }}>
              <div className="form-group" style={{ flex: 1, minWidth: 0 }}>
                <label className="form-label">Kolom Tanggal</label>
                <select
                  className="form-select"
                  value={dateCol}
                  onChange={(e) => setDateCol(e.target.value)}
                >
                  {dataSource.headers.map((h) => (
                    <option key={h} value={h}>
                      {h}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group" style={{ flex: 1, minWidth: 0 }}>
                <label className="form-label">Kolom Nilai</label>
                <select
                  className="form-select"
                  value={valueCol}
                  onChange={(e) => setValueCol(e.target.value)}
                >
                  {dataSource.headers.map((h) => (
                    <option key={h} value={h}>
                      {h}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Preview */}
            <div className="preview-table-wrapper" style={{ marginTop: 8 }}>
              <table className="preview-table">
                <thead>
                  <tr>
                    {dataSource.headers.slice(0, 4).map((h, i) => (
                      <th key={i}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {dataSource.data.slice(0, 5).map((row, ri) => (
                    <tr key={ri}>
                      {row.slice(0, 4).map((cell, ci) => (
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

        {/* Period Selector + Run */}
        {dataSource && pageState !== "result" && (
          <div className="result-card">
            <div className="input-row" style={{ alignItems: "flex-end" }}>
              <div className="form-group" style={{ flex: 1, minWidth: 0 }}>
                <label className="form-label">
                  <Calendar size={14} className="inline-icon" />
                  Periode Forecast
                </label>
                <select
                  className="form-select"
                  value={periods}
                  onChange={(e) => setPeriods(Number(e.target.value))}
                >
                  {PERIOD_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
              <button className="btn btn-primary" onClick={handleRunForecast}>
                <Play size={16} />
                Run Forecast
              </button>
            </div>
          </div>
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
        {pageState === "result" && forecastResult && chartData && (
          <>
            {/* Forecast Chart */}
            <div className="result-card">
              <h3>Grafik Forecast</h3>
              <Line
                data={chartData}
                options={{
                  responsive: true,
                  maintainAspectRatio: true,
                  plugins: {
                    legend: {
                      position: "bottom",
                      labels: { boxWidth: 12, padding: 12, font: { size: 11 } },
                    },
                  },
                  scales: {
                    x: {
                      grid: { display: false },
                      ticks: { font: { size: 10 }, maxTicksLimit: 12 },
                    },
                    y: {
                      beginAtZero: false,
                      grid: { color: "rgba(0,0,0,0.06)" },
                      ticks: { font: { size: 10 } },
                    },
                  },
                }}
                style={{ maxHeight: 240 }}
              />
            </div>

            {/* Metrics */}
            <div className="forecast-metrics">
              <div className="metric-card">
                <span className="metric-label">MAE</span>
                <span className="metric-value">{forecastResult.metrics.mae.toFixed(2)}</span>
              </div>
              <div className="metric-card">
                <span className="metric-label">RMSE</span>
                <span className="metric-value">{forecastResult.metrics.rmse.toFixed(2)}</span>
              </div>
              <div className="metric-card">
                <span className="metric-label">MAPE</span>
                <span className="metric-value">{forecastResult.metrics.mape.toFixed(2)}%</span>
              </div>
            </div>

            {/* Forecast Table */}
            <div className="result-card">
              <h3>Tabel Forecast</h3>
              <div className="preview-table-wrapper">
                <table className="preview-table">
                  <thead>
                    <tr>
                      <th>Periode</th>
                      <th>Prediksi</th>
                      <th>Bawah</th>
                      <th>Atas</th>
                    </tr>
                  </thead>
                  <tbody>
                    {forecastResult.forecast.map((row, i) => (
                      <tr key={i}>
                        <td>{row.ds}</td>
                        <td>
                          {row.yhat.toLocaleString("id-ID", {
                            minimumFractionDigits: 0,
                            maximumFractionDigits: 0,
                          })}
                        </td>
                        <td>
                          {row.yhat_lower.toLocaleString("id-ID", {
                            minimumFractionDigits: 0,
                            maximumFractionDigits: 0,
                          })}
                        </td>
                        <td>
                          {row.yhat_upper.toLocaleString("id-ID", {
                            minimumFractionDigits: 0,
                            maximumFractionDigits: 0,
                          })}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        {pageState !== "result" && !isLoading && (
          <div className="empty-state">
            <TrendingUp size={40} style={{color:"var(--primary)",opacity:0.4}} />
            <p className="empty-state-text">
              Hasil forecast akan tampil di sini setelah dijalankan.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ForecastPage;
