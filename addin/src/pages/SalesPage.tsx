import React, { useState, useCallback, useEffect } from "react";
import {
  TrendingUp,
  Table2,
  RotateCcw,
  Users,
  BarChart3,
  Globe,
  Package,
} from "lucide-react";

import {
  analyzeSales,
  SalesResponse,
} from "../services/api";
import { useWorkbook } from "../contexts/WorkbookContext";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorAlert from "../components/ErrorAlert";

type PageState = "idle" | "loading" | "result" | "error";

const SalesPage: React.FC = () => {
  const { activeSheet, isLoading, error: wbError } = useWorkbook();
  const [pageState, setPageState] = useState<PageState>("idle");
  const [loadingMessage, setLoadingMessage] = useState("Memproses...");
  const [error, setError] = useState<string | null>(null);
  const [dataSource, setDataSource] = useState<{
    headers: string[];
    data: unknown[][];
    sheetName: string;
  } | null>(null);
  const [result, setResult] = useState<SalesResponse | null>(null);

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
    setLoadingMessage("Menganalisis data penjualan...");
    try {
      const res = await analyzeSales(dataSource.data, dataSource.headers);
      setResult(res);
      setPageState("result");
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Gagal menganalisis data penjualan."
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

  const formatCurrency = (val: number): string => {
    return "Rp " + val.toLocaleString("id-ID");
  };

  return (
    <div className="page-split">
      <div className="pane pane-left">
        <h2 className="page-title">Sales</h2>

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
              Belum ada data penjualan. Buka add-in ini di Excel untuk mengambil data
              penjualan dari lembar kerja aktif.
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
            <TrendingUp size={16} />
            Analisis Penjualan
          </button>
        )}

        {/* Loading */}
        {pageState === "loading" && <LoadingSpinner message={loadingMessage} />}

        {/* Error */}
        {pageState === "error" && error && (
          <ErrorAlert message={error} onDismiss={() => setError(null)} />
        )}

        {/* Top Customers */}
        {pageState === "result" && result && result.top_customers.length > 0 && (
          <div className="result-card">
            <h3>
              <Users size={16} className="title-icon" />
              Pelanggan Teratas
            </h3>
            <div className="preview-table-wrapper">
              <table className="preview-table">
                <thead>
                  <tr>
                    <th>Pelanggan</th>
                    <th>Pendapatan</th>
                    <th>Kontribusi</th>
                  </tr>
                </thead>
                <tbody>
                  {result.top_customers.map((c, i) => (
                    <tr key={i}>
                      <td>
                        <strong>{c.name}</strong>
                      </td>
                      <td>{formatCurrency(c.revenue)}</td>
                      <td>
                        <div className="sales-pct-bar-wrapper">
                          <div
                            className="sales-pct-bar-fill"
                            style={{ width: `${Math.min(c.pct, 100)}%` }}
                          />
                          <span className="sales-pct-label">
                            {c.pct.toFixed(1)}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      <div className="pane pane-right">
        {/* Results */}
        {pageState === "result" && result && (
          <>
            {/* Summary */}
            {result.summary && (
              <div className="result-card">
                <h3>Ringkasan Penjualan</h3>
                <p className="result-section">{result.summary}</p>
              </div>
            )}

            {/* Sales Trend */}
            {result.sales_trend.length > 0 && (
              <div className="result-card">
                <h3>
                  <BarChart3 size={16} className="title-icon" />
                  Tren Penjualan
                </h3>
                <div className="preview-table-wrapper">
                  <table className="preview-table">
                    <thead>
                      <tr>
                        <th>Periode</th>
                        <th>Pendapatan</th>
                        <th>Pertumbuhan</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.sales_trend.map((t, i) => (
                        <tr key={i}>
                          <td>
                            <strong>{t.period}</strong>
                          </td>
                          <td>{formatCurrency(t.revenue)}</td>
                          <td>
                            <span
                              className={
                                t.growth >= 0 ? "text-success" : "text-danger"
                              }
                              style={{
                                color: t.growth >= 0 ? "#2e7d32" : "#d32f2f",
                                fontWeight: 600,
                              }}
                            >
                              {t.growth >= 0 ? "+" : ""}
                              {t.growth.toFixed(1)}%
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Product Performance */}
            {result.product_performance.length > 0 && (
              <div className="result-card">
                <h3>
                  <Package size={16} className="title-icon" />
                  Performa Produk
                </h3>
                <div className="sales-product-list">
                  {result.product_performance.map((p, i) => (
                    <div key={i} className="sales-product-item">
                      <div className="sales-product-item-header">
                        <strong>{p.name}</strong>
                      </div>
                      <div className="sales-product-details">
                        <div className="sales-product-detail">
                          <span className="sales-product-label">
                            Pendapatan
                          </span>
                          <span className="sales-product-value">
                            {formatCurrency(p.revenue)}
                          </span>
                        </div>
                        <div className="sales-product-detail">
                          <span className="sales-product-label">Margin</span>
                          <span
                            className="sales-product-value"
                            style={{
                              color: p.margin >= 0 ? "#2e7d32" : "#d32f2f",
                            }}
                          >
                            {p.margin.toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Regional Analysis */}
            {result.regional_analysis.length > 0 && (
              <div className="result-card">
                <h3>
                  <Globe size={16} className="title-icon" />
                  Analisis Regional
                </h3>
                <div className="preview-table-wrapper">
                  <table className="preview-table">
                    <thead>
                      <tr>
                        <th>Region</th>
                        <th>Pendapatan</th>
                        <th>Transaksi</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.regional_analysis.map((r, i) => (
                        <tr key={i}>
                          <td>
                            <strong>{r.region}</strong>
                          </td>
                          <td>{formatCurrency(r.revenue)}</td>
                          <td>{r.count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}

        {pageState !== "result" && !isLoading && (
          <div className="empty-state">
            <TrendingUp size={40} style={{color:"var(--primary)",opacity:0.4}} />
            <p className="empty-state-text">
              Hasil analisis penjualan akan tampil di sini.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default SalesPage;
