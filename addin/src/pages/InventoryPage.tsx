import React, { useState, useCallback, useEffect } from "react";
import {
  PackageSearch,
  Table2,
  RotateCcw,
  AlertCircle,
  Clock,
  ShoppingCart,
  Warehouse,
  Layers,
} from "lucide-react";

import {
  analyzeInventory,
  InventoryResponse,
} from "../services/api";
import { useWorkbook } from "../contexts/WorkbookContext";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorAlert from "../components/ErrorAlert";

type PageState = "idle" | "loading" | "result" | "error";

const InventoryPage: React.FC = () => {
  const { activeSheet, isLoading, error: wbError } = useWorkbook();
  const [pageState, setPageState] = useState<PageState>("idle");
  const [loadingMessage, setLoadingMessage] = useState("Memproses...");
  const [error, setError] = useState<string | null>(null);
  const [dataSource, setDataSource] = useState<{
    headers: string[];
    data: unknown[][];
    sheetName: string;
  } | null>(null);
  const [result, setResult] = useState<InventoryResponse | null>(null);

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
    setLoadingMessage("Menganalisis data gudang...");
    try {
      const res = await analyzeInventory(dataSource.data, dataSource.headers);
      setResult(res);
      setPageState("result");
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Gagal menganalisis data gudang."
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

  const getCategoryColor = (type: string): string => {
    switch (type.toLowerCase()) {
      case "dead stock":
      case "dead":
        return "#d32f2f";
      case "slow moving":
      case "slow":
        return "#e65100";
      case "fast moving":
      case "fast":
        return "#2e7d32";
      default:
        return "#1565c0";
    }
  };

  const getCategoryIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case "dead stock":
      case "dead":
        return <AlertCircle size={16} />;
      case "slow moving":
      case "slow":
        return <Clock size={16} />;
      case "fast moving":
      case "fast":
        return <ShoppingCart size={16} />;
      default:
        return <Layers size={16} />;
    }
  };

  return (
    <div className="page-split">
      <div className="pane pane-left">
        <h2 className="page-title">Gudang</h2>

        {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

        {wbError && !isLoading && (
          <ErrorAlert message={wbError} onDismiss={() => {}} />
        )}

        {isLoading && <LoadingSpinner message="Membaca data Excel..." />}

        {/* No data at all */}
        {!dataSource && !isLoading && (
          <div className="empty-state">
            <PackageSearch size={40} style={{color:"var(--primary)",opacity:0.4}} />
            <p className="empty-state-text">
              Belum ada data inventaris. Buka add-in ini di Excel untuk mengambil data
              gudang dari lembar kerja aktif.
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
            <PackageSearch size={16} />
            Analisis Gudang
          </button>
        )}

        {/* Loading */}
        {pageState === "loading" && <LoadingSpinner message={loadingMessage} />}

        {/* Error */}
        {pageState === "error" && error && (
          <ErrorAlert message={error} onDismiss={() => setError(null)} />
        )}

        {/* Stock Categories */}
        {pageState === "result" && result && result.categories.length > 0 && (
          <div className="result-card">
            <h3>
              <Layers size={16} className="title-icon" />
              Kategori Stok
            </h3>
            <div className="inv-categories-grid">
              {result.categories.map((cat, i) => {
                const color = getCategoryColor(cat.type);
                return (
                  <div
                    key={i}
                    className="inv-category-card"
                    style={{
                      borderTop: `3px solid ${color}`,
                    }}
                  >
                    <div
                      className="inv-category-header"
                      style={{ color }}
                    >
                      {getCategoryIcon(cat.type)}
                      <strong>{cat.type}</strong>
                    </div>
                    <div className="inv-category-count">
                      {cat.count} item
                    </div>
                    <div className="inv-category-value">
                      Rp {cat.value.toLocaleString("id-ID")}
                    </div>
                    <div className="inv-category-items">
                      {cat.items.slice(0, 5).map((item, ii) => (
                        <span key={ii} className="inv-category-tag">
                          {item}
                        </span>
                      ))}
                      {cat.items.length > 5 && (
                        <span className="inv-category-tag inv-category-more">
                          +{cat.items.length - 5} lagi
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      <div className="pane pane-right">
        {/* Results */}
        {pageState === "result" && result && (
          <>
            {/* Stock Aging */}
            {result.stock_aging.length > 0 && (
              <div className="result-card">
                <h3>
                  <Clock size={16} className="title-icon" />
                  Umur Stok
                </h3>
                <div className="preview-table-wrapper">
                  <table className="preview-table">
                    <thead>
                      <tr>
                        <th>Kategori Umur</th>
                        <th>Jumlah Item</th>
                        <th>Nilai</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.stock_aging.map((aging, i) => (
                        <tr key={i}>
                          <td>
                            <strong>{aging.bracket}</strong>
                          </td>
                          <td>{aging.count}</td>
                          <td>
                            Rp {aging.value.toLocaleString("id-ID")}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Reorder Suggestions */}
            {result.reorder_suggestions.length > 0 && (
              <div className="result-card">
                <h3>
                  <ShoppingCart size={16} className="title-icon" />
                  Rekomendasi Pemesanan Ulang
                </h3>
                <div className="inv-reorder-list">
                  {result.reorder_suggestions.map((rec, i) => (
                    <div key={i} className="inv-reorder-item">
                      <div className="inv-reorder-item-header">
                        <strong>{rec.item}</strong>
                      </div>
                      <div className="inv-reorder-details">
                        <div className="inv-reorder-detail">
                          <span className="inv-reorder-label">Stok Saat Ini</span>
                          <span className="inv-reorder-value inv-reorder-low">
                            {rec.stock}
                          </span>
                        </div>
                        <div className="inv-reorder-detail">
                          <span className="inv-reorder-label">
                            Reorder Point
                          </span>
                          <span className="inv-reorder-value">
                            {rec.reorder_point}
                          </span>
                        </div>
                        <div className="inv-reorder-detail">
                          <span className="inv-reorder-label">
                            Jumlah Disarankan
                          </span>
                          <span className="inv-reorder-value inv-reorder-suggest">
                            {rec.suggested_qty}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Summary */}
            {result.summary && (
              <div className="result-card">
                <h3>Ringkasan</h3>
                <p className="result-section">{result.summary}</p>
              </div>
            )}
          </>
        )}

        {pageState !== "result" && !isLoading && (
          <div className="empty-state">
            <PackageSearch size={40} style={{color:"var(--primary)",opacity:0.4}} />
            <p className="empty-state-text">
              Hasil analisis gudang akan tampil di sini.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default InventoryPage;
