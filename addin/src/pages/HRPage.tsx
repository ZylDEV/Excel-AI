import React, { useState, useCallback, useEffect } from "react";
import {
  Users,
  Table2,
  RotateCcw,
  DollarSign,
  UserCheck,
  AlertTriangle,
  Building2,
  Clock,
  CalendarCheck,
} from "lucide-react";

import {
  analyzeHR,
  HRResponse,
} from "../services/api";
import { useWorkbook } from "../contexts/WorkbookContext";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorAlert from "../components/ErrorAlert";

type PageState = "idle" | "loading" | "result" | "error";

const HRPage: React.FC = () => {
  const { activeSheet, isLoading, error: wbError } = useWorkbook();
  const [pageState, setPageState] = useState<PageState>("idle");
  const [loadingMessage, setLoadingMessage] = useState("Memproses...");
  const [error, setError] = useState<string | null>(null);
  const [dataSource, setDataSource] = useState<{
    headers: string[];
    data: unknown[][];
    sheetName: string;
  } | null>(null);
  const [result, setResult] = useState<HRResponse | null>(null);

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
    setLoadingMessage("Menganalisis data SDM...");
    try {
      const res = await analyzeHR(dataSource.data, dataSource.headers);
      setResult(res);
      setPageState("result");
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Gagal menganalisis data SDM."
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

  const getDepartmentEntries = (obj: Record<string, number>): [string, number][] => {
    return Object.entries(obj).sort(([, a], [, b]) => b - a);
  };

  return (
    <div className="page-split">
      <div className="pane pane-left">
        <h2 className="page-title">HR</h2>

        {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}

        {wbError && !isLoading && (
          <ErrorAlert message={wbError} onDismiss={() => {}} />
        )}

        {isLoading && <LoadingSpinner message="Membaca data Excel..." />}

        {/* No data at all */}
        {!dataSource && !isLoading && (
          <div className="empty-state">
            <Users size={40} style={{color:"var(--primary)",opacity:0.4}} />
            <p className="empty-state-text">
              Belum ada data SDM. Buka add-in ini di Excel untuk mengambil data
              karyawan dari lembar kerja aktif.
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
            <Users size={16} />
            Analisis SDM
          </button>
        )}

        {/* Loading */}
        {pageState === "loading" && <LoadingSpinner message={loadingMessage} />}

        {/* Error */}
        {pageState === "error" && error && (
          <ErrorAlert message={error} onDismiss={() => setError(null)} />
        )}

        {/* Headcount */}
        {pageState === "result" && result && (
          <div className="result-card">
            <h3>
              <UserCheck size={16} className="title-icon" />
              Headcount
            </h3>
            <div className="hr-headcount-total">
              <span className="hr-headcount-number">
                {result.headcount.total}
              </span>
              <span className="hr-headcount-label">Total Karyawan</span>
            </div>
          </div>
        )}

        {/* Salary Analysis */}
        {pageState === "result" && result && (
          <div className="result-card">
            <h3>
              <DollarSign size={16} className="title-icon" />
              Analisis Gaji
            </h3>
            <div className="hr-salary-grid">
              <div className="hr-salary-card">
                <span className="hr-salary-label">Rata-rata</span>
                <span className="hr-salary-value">
                  {formatCurrency(result.salary_analysis.avg)}
                </span>
              </div>
              <div className="hr-salary-card">
                <span className="hr-salary-label">Median</span>
                <span className="hr-salary-value">
                  {formatCurrency(result.salary_analysis.median)}
                </span>
              </div>
              <div className="hr-salary-card">
                <span className="hr-salary-label">Range</span>
                <span className="hr-salary-value">
                  {formatCurrency(result.salary_analysis.range[0])} –{" "}
                  {formatCurrency(result.salary_analysis.range[1])}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="pane pane-right">
        {/* Results */}
        {pageState === "result" && result && (
          <>
            {/* Department Breakdown (from headcount) */}
            {getDepartmentEntries(result.headcount.by_department).length > 0 && (
              <div className="result-card">
                <h4>Headcount per Departemen</h4>
                <div className="hr-department-list">
                  {getDepartmentEntries(result.headcount.by_department).map(
                    ([dept, count], i) => (
                      <div key={i} className="hr-department-item">
                        <span className="hr-department-name">
                          <Building2 size={14} className="inline-icon" />
                          {dept}
                        </span>
                        <div className="hr-department-bar-wrapper">
                          <div
                            className="hr-department-bar-fill"
                            style={{
                              width: `${
                                (count / result.headcount.total) * 100
                              }%`,
                            }}
                          />
                        </div>
                        <span className="hr-department-count">{count}</span>
                      </div>
                    )
                  )}
                </div>
              </div>
            )}

            {/* Salary by Department */}
            {getDepartmentEntries(result.salary_analysis.by_department).length > 0 && (
              <div className="result-card">
                <h4>Gaji per Departemen</h4>
                <div className="preview-table-wrapper">
                  <table className="preview-table">
                    <thead>
                      <tr>
                        <th>Departemen</th>
                        <th>Rata-rata Gaji</th>
                      </tr>
                    </thead>
                    <tbody>
                      {getDepartmentEntries(
                        result.salary_analysis.by_department
                      ).map(([dept, val], i) => (
                        <tr key={i}>
                          <td>{dept}</td>
                          <td>{formatCurrency(val)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Duplicate Employees Warning */}
            {result.duplicate_employees > 0 && (
              <div className="error-alert">
                <span className="error-alert-icon">
                  <AlertTriangle size={16} />
                </span>
                <span className="error-alert-text">
                  Terdeteksi {result.duplicate_employees} karyawan duplikat dalam
                  data. Harap verifikasi dan bersihkan data.
                </span>
              </div>
            )}

            {/* Overtime */}
            {result.overtime && (
              <div className="result-card">
                <h3>
                  <Clock size={16} className="title-icon" />
                  Lembur
                </h3>
                <div className="hr-overtime-avg">
                  Rata-rata jam lembur:{" "}
                  <strong>{result.overtime.avg_hours.toFixed(1)} jam</strong>
                </div>
                {getDepartmentEntries(result.overtime.by_department).length > 0 && (
                  <div className="preview-table-wrapper">
                    <table className="preview-table">
                      <thead>
                        <tr>
                          <th>Departemen</th>
                          <th>Rata-rata Jam Lembur</th>
                        </tr>
                      </thead>
                      <tbody>
                        {getDepartmentEntries(
                          result.overtime.by_department
                        ).map(([dept, hours], i) => (
                          <tr key={i}>
                            <td>{dept}</td>
                            <td>{hours.toFixed(1)} jam</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* Attendance */}
            {result.attendance && (
              <div className="result-card">
                <h3>
                  <CalendarCheck size={16} className="title-icon" />
                  Kehadiran
                </h3>
                <div className="hr-attendance-avg">
                  Rata-rata kehadiran:{" "}
                  <strong>
                    {(result.attendance.avg_attendance * 100).toFixed(1)}%
                  </strong>
                </div>
                {getDepartmentEntries(result.attendance.by_department).length > 0 && (
                  <div className="preview-table-wrapper">
                    <table className="preview-table">
                      <thead>
                        <tr>
                          <th>Departemen</th>
                          <th>Kehadiran</th>
                        </tr>
                      </thead>
                      <tbody>
                        {getDepartmentEntries(
                          result.attendance.by_department
                        ).map(([dept, att], i) => (
                          <tr key={i}>
                            <td>{dept}</td>
                            <td>{(att * 100).toFixed(1)}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* Summary */}
            {result.summary && (
              <div className="result-card">
                <h3>Ringkasan SDM</h3>
                <p className="result-section">{result.summary}</p>
              </div>
            )}

            {/* No duplicates */}
            {result.duplicate_employees === 0 && (
              <div className="alert alert-success">
                <UserCheck size={16} />
                Tidak ditemukan data karyawan duplikat.
              </div>
            )}
          </>
        )}

        {pageState !== "result" && !isLoading && (
          <div className="empty-state">
            <Users size={40} style={{color:"var(--primary)",opacity:0.4}} />
            <p className="empty-state-text">
              Hasil analisis SDM akan tampil di sini.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default HRPage;
