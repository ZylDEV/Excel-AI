import React, { useState, useCallback, useEffect } from "react";
import { FunctionSquare, Sigma, Copy, Check, History, Star, Lightbulb, Table2, RotateCcw } from "lucide-react";
import { generateFormula, explainFormula } from "../services/api";
import { useWorkbook } from "../contexts/WorkbookContext";
import { useRightSidebar } from "../contexts/RightSidebarContext";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorAlert from "../components/ErrorAlert";

type Mode = "generate" | "explain";

const CATEGORIES = [
  { label: "Matematika", desc: "SUM, AVERAGE, COUNT, MIN, MAX" },
  { label: "Logika", desc: "IF, AND, OR, IFERROR, SWITCH" },
  { label: "Lookup", desc: "VLOOKUP, XLOOKUP, INDEX, MATCH" },
  { label: "Teks", desc: "LEFT, RIGHT, MID, LEN, TEXT" },
  { label: "Tanggal", desc: "DATE, DATEDIF, TODAY, EOMONTH" },
  { label: "Statistik", desc: "AVERAGEIF, COUNTIF, SUMIF, LARGE" },
];

const SAMPLE_BUTTONS = [
  { label: "Total penjualan", desc: "Hitung total penjualan dari kolom Total" },
  { label: "Rata-rata per kategori", desc: "Hitung rata-rata penjualan per kategori produk menggunakan AVERAGEIF" },
  { label: "IF kondisi", desc: "Buat rumus IF untuk menandai penjualan di atas 100 sebagai 'High' dan sisanya 'Low'" },
  { label: "VLOOKUP", desc: "Cari harga produk berdasarkan ID menggunakan VLOOKUP" },
  { label: "Count kondisi", desc: "Hitung jumlah produk yang terjual lebih dari 50 unit" },
];

interface HistoryItem {
  id: number;
  mode: Mode;
  input: string;
  result: { formula: string; explanation: string; example: string };
  timestamp: Date;
}

const FormulaPage: React.FC = () => {
  const { activeSheet, isLoading, error: wbError } = useWorkbook();
  const { setItems } = useRightSidebar();
  const [mode, setMode] = useState<Mode>("generate");
  const [description, setDescription] = useState("");
  const [formulaInput, setFormulaInput] = useState("");
  const [sheetContext, setSheetContext] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<{ formula: string; explanation: string; example: string } | null>(null);
  const [copied, setCopied] = useState(false);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  // Set right sidebar
  useEffect(() => {
    setItems([
      { key: "generate", label: "Generate", icon: <Sigma size={16} />, active: mode === "generate", onClick: () => { setMode("generate"); setResult(null); setError(""); } },
      { key: "explain", label: "Explain", icon: <FunctionSquare size={16} />, active: mode === "explain", onClick: () => { setMode("explain"); setResult(null); setError(""); } },
    ]);
    return () => setItems([]);
  }, [mode, setItems]);

  // Auto-populate sheet context
  useEffect(() => {
    if (activeSheet) {
      setSheetContext(`Sheet: ${activeSheet.sheetName}\nHeaders: ${activeSheet.headers.join(", ")}\nRows: ${activeSheet.data.length}`);
    }
  }, [activeSheet]);

  const handleSampleFormula = useCallback((desc: string) => {
    setDescription(desc);
    setError("");
  }, []);

  const handleCategoryClick = useCallback((cat: string) => {
    setSelectedCategory(cat === selectedCategory ? null : cat);
    const prompts: Record<string, string> = {
      "Matematika": "Jumlahkan total nilai di kolom Sales menggunakan SUM",
      "Logika": "Buat rumus IF untuk menandai nilai di atas rata-rata sebagai 'Baik'",
      "Lookup": "Cari nilai di kolom B berdasarkan nilai di kolom A menggunakan VLOOKUP",
      "Teks": "Ambil 3 karakter pertama dari teks di kolom Nama menggunakan LEFT",
      "Tanggal": "Hitung selisih hari antara tanggal di kolom A dan B menggunakan DATEDIF",
      "Statistik": "Hitung rata-rata penjualan untuk produk 'Laptop' menggunakan AVERAGEIF",
    };
    if (prompts[cat]) {
      setDescription(prompts[cat]);
      setMode("generate");
    }
  }, [selectedCategory]);

  const addToHistory = useCallback((item: HistoryItem) => {
    setHistory((prev) => [item, ...prev].slice(0, 20));
  }, []);

  const loadFromHistory = useCallback((item: HistoryItem) => {
    if (item.mode === "generate") {
      setDescription(item.input);
      setMode("generate");
    } else {
      setFormulaInput(item.input);
      setMode("explain");
    }
    setResult(item.result);
    setShowHistory(false);
  }, []);

  const handleGenerate = useCallback(async () => {
    if (!description.trim()) { setError("Silakan masukkan deskripsi rumus."); return; }
    setError(""); setLoading(true); setResult(null);
    try {
      const res = await generateFormula(description, sheetContext);
      setResult(res);
      addToHistory({ id: Date.now(), mode: "generate", input: description, result: res, timestamp: new Date() });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Gagal menghasilkan rumus.");
    } finally { setLoading(false); }
  }, [description, sheetContext, addToHistory]);

  const handleExplain = useCallback(async () => {
    if (!formulaInput.trim()) { setError("Silakan masukkan rumus."); return; }
    setError(""); setLoading(true); setResult(null);
    try {
      const res = await explainFormula(formulaInput);
      setResult(res);
      addToHistory({ id: Date.now(), mode: "explain", input: formulaInput, result: res, timestamp: new Date() });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Gagal menjelaskan rumus.");
    } finally { setLoading(false); }
  }, [formulaInput, addToHistory]);

  const handleCopy = useCallback(() => {
    if (result?.formula) {
      navigator.clipboard.writeText(result.formula).then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      });
    }
  }, [result]);

  // Simple formula syntax highlighting
  const highlightFormula = (formula: string) => {
    if (!formula) return "";
    return formula
      .replace(/(=?\b[A-Z]+\b)(?=\()/g, '<span class="formula-fn">$1</span>')
      .replace(/([""][^""]*[""])/g, '<span class="formula-str">$1</span>')
      .replace(/(\b\d+(?:\.\d+)?\b)/g, '<span class="formula-num">$1</span>')
      .replace(/([(),])/g, '<span class="formula-paren">$1</span>')
      .replace(/([<>=!]+)/g, '<span class="formula-op">$1</span>');
  };

  return (
    <div className="page">
      {/* Top section: mode indicator + history */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
        <h2 className="page-title" style={{ margin: 0, border: "none", padding: 0, flex: 1 }}>
          {mode === "generate" ? "Buat Rumus Excel" : "Jelaskan Rumus"}
        </h2>
        <button
          className="btn btn-sm btn-secondary"
          onClick={() => setShowHistory(!showHistory)}
          title="Riwayat"
          style={{ padding: "4px 8px" }}
        >
          <History size={14} />
        </button>
        <button
          className="btn btn-sm btn-secondary"
          onClick={() => { setResult(null); setError(""); setDescription(""); setFormulaInput(""); }}
          title="Reset"
          style={{ padding: "4px 8px" }}
        >
          <RotateCcw size={14} />
        </button>
      </div>

      {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}
      {wbError && !isLoading && <ErrorAlert message={wbError} onDismiss={() => {}} />}
      {isLoading && <LoadingSpinner message="Menghubungi AI..." />}

      {/* History panel */}
      {showHistory && history.length > 0 && (
        <div style={{ background: "var(--grey-50)", borderRadius: 8, padding: 10, border: "1px solid var(--grey-200)", maxHeight: 200, overflowY: "auto" }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: "var(--grey-500)", marginBottom: 6, textTransform: "uppercase", letterSpacing: 0.5 }}>Riwayat</div>
          {history.map((h) => (
            <button key={h.id} onClick={() => loadFromHistory(h)}
              style={{ display: "block", width: "100%", textAlign: "left", padding: "6px 8px", border: "none", background: "transparent", borderRadius: 4, cursor: "pointer", fontSize: 12, color: "var(--grey-700)" }}>
              <span style={{ fontWeight: 600, color: "var(--primary)" }}>{h.mode === "generate" ? "GEN" : "EXP"}</span>
              {" "}{h.input.slice(0, 60)}{h.input.length > 60 ? "..." : ""}
            </button>
          ))}
        </div>
      )}

      {/* Generate Mode */}
      {mode === "generate" && (
        <>
          {/* Category presets */}
          <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
            {CATEGORIES.map((cat) => (
              <button key={cat.label} onClick={() => handleCategoryClick(cat.label)}
                style={{
                  padding: "3px 10px", border: "1px solid", borderRadius: 12, fontSize: 10, fontWeight: 600, cursor: "pointer",
                  background: selectedCategory === cat.label ? "var(--primary)" : "transparent",
                  color: selectedCategory === cat.label ? "white" : "var(--primary)",
                  borderColor: "var(--primary)", transition: "all 0.15s"
                }}>
                {cat.label}
              </button>
            ))}
          </div>

          <div className="form-group">
            <label className="form-label">Deskripsi Rumus</label>
            <textarea
              className="form-textarea"
              rows={3}
              placeholder="Contoh: Jumlahkan nilai di kolom A jika kolom B berisi 'Lunas'"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              style={{ fontSize: 14 }}
            />
          </div>

          {/* Sample quick buttons */}
          <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
            <div style={{ fontSize: 10, color: "var(--grey-400)", fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.5 }}>Coba cepat:</div>
            {SAMPLE_BUTTONS.map((btn, i) => (
              <button key={i} className="btn-sample-formula" onClick={() => handleSampleFormula(btn.desc)}>
                <Star size={10} style={{ marginRight: 4, color: "#ff9800" }} />
                {btn.label}
              </button>
            ))}
          </div>

          <div className="form-group">
            <label className="form-label">Konteks Sheet</label>
            <textarea className="form-textarea form-textarea-sm" rows={2}
              placeholder="Otomatis dari Excel..."
              value={sheetContext} onChange={(e) => setSheetContext(e.target.value)} />
          </div>

          <button className="btn btn-primary btn-full" onClick={handleGenerate} disabled={loading || !description.trim()}
            style={{ padding: "10px 16px", fontSize: 14 }}>
            {loading ? "⏳ Memproses..." : "✨ Generate Rumus"}
          </button>
        </>
      )}

      {/* Explain Mode */}
      {mode === "explain" && (
        <>
          <div className="form-group">
            <label className="form-label">Masukkan Rumus Excel</label>
            <input className="form-input" type="text"
              placeholder={'=SUMIF(A2:A10,">0",B2:B10)'}
              value={formulaInput} onChange={(e) => setFormulaInput(e.target.value)}
              style={{ fontFamily: "monospace", fontSize: 14, padding: "10px 12px" }} />
          </div>
          <button className="btn btn-primary btn-full" onClick={handleExplain} disabled={loading || !formulaInput.trim()}
            style={{ padding: "10px 16px", fontSize: 14 }}>
            {loading ? "⏳ Menganalisis..." : "🔍 Jelaskan Rumus"}
          </button>
        </>
      )}

      {loading && <LoadingSpinner message="Menghubungi AI..." />}

      {/* Result */}
      {result && (
        <div className="result-card">
          {/* Formula with copy */}
          <div style={{ position: "relative" }}>
            <div className="formula-block" style={{ padding: "14px 16px", background: "#1e1e2e", borderRadius: 8 }}>
              <code style={{ color: "#cdd6f4", fontSize: 15, fontFamily: "'Cascadia Code', 'Fira Code', 'Consolas', monospace", lineHeight: 1.6, wordBreak: "break-all" }}
                dangerouslySetInnerHTML={{ __html: highlightFormula(result.formula) }} />
            </div>
            <button onClick={handleCopy}
              style={{
                position: "absolute", top: 6, right: 6, display: "flex", alignItems: "center", gap: 4,
                padding: "4px 10px", border: "none", borderRadius: 4, fontSize: 11, fontWeight: 600, cursor: "pointer",
                background: copied ? "rgba(76,175,80,0.2)" : "rgba(255,255,255,0.15)",
                color: copied ? "#81c784" : "rgba(255,255,255,0.6)", transition: "all 0.2s"
              }}>
              {copied ? <><Check size={13} /> Tersalin</> : <><Copy size={13} /> Salin</>}
            </button>
          </div>

          {/* Quick actions */}
          <div style={{ display: "flex", gap: 6 }}>
            <button className="btn btn-sm btn-outline" onClick={handleCopy}
              style={{ flex: 1, justifyContent: "center" }}>
              <Copy size={13} /> Salin Rumus
            </button>
          </div>

          {/* Explanation */}
          <div>
            <h4 style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 13, fontWeight: 600, color: "var(--grey-700)", marginBottom: 6 }}>
              <Lightbulb size={14} style={{ color: "#ff9800" }} /> Penjelasan
            </h4>
            <div style={{ background: "var(--grey-50)", borderRadius: 6, padding: "10px 12px", fontSize: 13, lineHeight: 1.6, color: "var(--grey-700)" }}>
              {result.explanation}
            </div>
          </div>

          {/* Example */}
          {result.example && (
            <div>
              <h4 style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 13, fontWeight: 600, color: "var(--grey-700)", marginBottom: 6 }}>
                <Table2 size={14} style={{ color: "var(--primary)" }} /> Contoh Penggunaan
              </h4>
              <div style={{ background: "var(--primary-light)", borderRadius: 6, padding: "10px 12px", fontSize: 13, lineHeight: 1.6, color: "var(--primary-dark)" }}>
                {result.example}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default FormulaPage;
