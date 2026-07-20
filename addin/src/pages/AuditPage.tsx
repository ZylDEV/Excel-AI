import React, { useState, useCallback, useEffect } from "react";
import { MapPin, Lightbulb } from "lucide-react";
import { runAudit, AuditIssue } from "../services/api";
import { useWorkbook } from "../contexts/WorkbookContext";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorAlert from "../components/ErrorAlert";

const SEVERITY_LABELS: Record<string, string> = {
  high: "Tinggi",
  medium: "Sedang",
  low: "Rendah",
};

const CATEGORY_LABELS: Record<string, string> = {
  empty_sheet: "Sheet Kosong",
  inconsistent_columns: "Kolom Tidak Konsisten",
  empty_column: "Kolom Kosong",
  unexpected_negative: "Nilai Negatif Tak Terduga",
  suspicious_text: "Teks Mencurigakan",
  empty_header: "Header Kosong",
  header_special_chars: "Karakter Khusus di Header",
  header_starts_with_digit: "Header Diawali Angka",
  merged_cell_artifact: "Artifak Sel Gabungan",
};

const AuditPage: React.FC = () => {
  const { activeSheet, isLoading, error: wbError } = useWorkbook();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [issues, setIssues] = useState<AuditIssue[]>([]);
  const [hasRun, setHasRun] = useState(false);
  const [sheetsData, setSheetsData] = useState<{ name: string; headers: string[]; data: unknown[][] }[] | null>(null);

  // Build sheetsData from context when it becomes available
  useEffect(() => {
    if (activeSheet) {
      setSheetsData([{
        name: activeSheet.sheetName,
        headers: activeSheet.headers,
        data: activeSheet.data,
      }]);
    }
  }, [activeSheet]);

  const handleRunAudit = useCallback(async () => {
    setError("");
    setLoading(true);
    setIssues([]);
    setHasRun(false);
    try {
      if (!sheetsData || sheetsData.length === 0) {
        throw new Error("Tidak ada sheet ditemukan di workbook.");
      }
      const res = await runAudit(sheetsData);
      setIssues(res.issues);
      setHasRun(true);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Gagal menjalankan audit.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [sheetsData]);

  // Summary counts
  const total = issues.length;
  const highCount = issues.filter((i) => i.severity === "high").length;
  const mediumCount = issues.filter((i) => i.severity === "medium").length;
  const lowCount = issues.filter((i) => i.severity === "low").length;

  return (
    <div className="page-split">
      <div className="pane pane-left">
        <h2 className="page-title">Audit</h2>

        {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}

        {wbError && !isLoading && (
          <ErrorAlert message={wbError} onDismiss={() => {}} />
        )}

        {isLoading && <LoadingSpinner message="Membaca data Excel..." />}

        {!hasRun && !loading && !sheetsData && !isLoading && (
          <div className="empty-state">
            <p className="empty-state-text">
              Audit akan memeriksa seluruh sheet di workbook untuk menemukan
              masalah struktur dan data.
            </p>
          </div>
        )}

        {/* Ready to run audit with loaded data */}
        {!hasRun && !loading && sheetsData && (
          <div className="empty-state">
            <p className="empty-state-text">
              Audit akan memeriksa {sheetsData.length} sheet untuk menemukan masalah struktur dan data.
            </p>
            <button className="btn btn-primary" onClick={handleRunAudit}>
              Jalankan Audit
            </button>
          </div>
        )}

        {loading && <LoadingSpinner message="Menjalankan audit..." />}

        {hasRun && !loading && (
          <>
            {/* Summary */}
            <div className="audit-summary">
              <div className="summary-card">
                <span className="summary-number">{total}</span>
                <span className="summary-label">Total Masalah</span>
              </div>
              <div className="summary-card summary-high">
                <span className="summary-number">{highCount}</span>
                <span className="summary-label">Tinggi</span>
              </div>
              <div className="summary-card summary-medium">
                <span className="summary-number">{mediumCount}</span>
                <span className="summary-label">Sedang</span>
              </div>
              <div className="summary-card summary-low">
                <span className="summary-number">{lowCount}</span>
                <span className="summary-label">Rendah</span>
              </div>
            </div>

            <button
              className="btn btn-secondary btn-full"
              onClick={() => {
                setHasRun(false);
                setIssues([]);
                setSheetsData(null);
              }}
              style={{ marginTop: 12 }}
            >
              Audit Ulang
            </button>
          </>
        )}
      </div>

      <div className="pane pane-right">
        {hasRun && !loading && (
          <>
            {/* Issue list */}
            {issues.length === 0 ? (
              <div className="empty-state">
                <p className="text-success">
                  Tidak ditemukan masalah! Workbook Anda dalam kondisi baik.
                </p>
              </div>
            ) : (
              <div className="issues-list">
                {issues.map((issue, i) => (
                  <div key={i} className={`audit-issue severity-${issue.severity}`}>
                    <div className="audit-issue-header">
                      <span className={`badge badge-${issue.severity}`}>
                        {SEVERITY_LABELS[issue.severity]}
                      </span>
                      <span className="audit-category">
                        {CATEGORY_LABELS[issue.category] || issue.category}
                      </span>
                    </div>
                    <p className="audit-description">{issue.description}</p>
                    <div className="audit-meta">
                      <span className="audit-location">
                        <MapPin size={14} /> {issue.location}
                      </span>
                    </div>
                    <div className="audit-suggestion">
                      <Lightbulb size={14} /> {issue.suggestion}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {!hasRun && !loading && (
          <div className="empty-state">
            <p className="empty-state-text">
              Hasil audit akan tampil di sini setelah dijalankan.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AuditPage;
