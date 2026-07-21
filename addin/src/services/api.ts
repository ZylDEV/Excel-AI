/** Axios-based API client for the Excel AI backend. */

import axios from "axios";

const BASE_URL_V1 = "http://localhost:8000/api/v1";
const BASE_URL_V2 = "http://localhost:8000/api/v2";
const BASE_URL_V3 = "http://localhost:8000/api/v3";

function getApiKey(): string {
  return localStorage.getItem("openai_api_key") || "";
}

const api = axios.create({
  baseURL: BASE_URL_V1,
  timeout: 60000,
  headers: { "Content-Type": "application/json" },
});

const apiV2 = axios.create({
  baseURL: BASE_URL_V2,
  timeout: 120000,
  headers: { "Content-Type": "application/json" },
});

const apiV3 = axios.create({
  baseURL: BASE_URL_V3,
  timeout: 120000,
  headers: { "Content-Type": "application/json" },
});

apiV3.interceptors.request.use((config) => {
  const key = getApiKey();
  if (key) {
    config.headers["X-API-Key"] = key;
  }
  const provider = localStorage.getItem("llm_provider") || "";
  if (provider) {
    config.headers["X-LLM-Provider"] = provider;
  }
  return config;
});

// Add interceptor to attach API key & provider to every request
api.interceptors.request.use((config) => {
  const key = getApiKey();
  if (key) {
    config.headers["X-API-Key"] = key;
  }
  const provider = localStorage.getItem("llm_provider") || "";
  if (provider) {
    config.headers["X-LLM-Provider"] = provider;
  }
  return config;
});

apiV2.interceptors.request.use((config) => {
  const key = getApiKey();
  if (key) {
    config.headers["X-API-Key"] = key;
  }
  const provider = localStorage.getItem("llm_provider") || "";
  if (provider) {
    config.headers["X-LLM-Provider"] = provider;
  }
  return config;
});

// ── Public helpers ──────────────────────────────────────────────────

/** Read the currently selected range (or used range) from the active worksheet. */
export async function getActiveSheetData(): Promise<{
  headers: string[];
  data: unknown[][];
  sheetName: string;
}> {
  // Coba baca dari Excel (hanya jalan kalau di dalam Excel add-in)
  const isExcelContext = typeof Excel !== "undefined" && typeof Excel.run === "function";

  if (isExcelContext) {
    try {
      return await Excel.run(async (context) => {
        const sheet = context.workbook.worksheets.getActiveWorksheet();
        sheet.load("name");
        const range = sheet.getUsedRange();
        range.load("values");
        await context.sync();

        const sheetName = sheet.name;
        const values: unknown[][] = range.values;

        if (!values || values.length === 0) {
          throw new Error("Tidak ada data ditemukan di sheet aktif.");
        }

        const headers = (values[0] as string[]).map((h) =>
          h != null ? String(h) : ""
        );
        const data = values.slice(1);

        return { headers, data, sheetName };
      });
    } catch (err) {
      // Gagal baca Excel — fallback ke sample data
      console.warn("Gagal baca Excel, pakai sample data:", err);
    }
  }

  // Browser mode atau gagal baca — pakai sample data
  return getSampleData();
}

/** Return sample/demo data for browser testing mode. */
function getSampleData(): Promise<{
  headers: string[];
  data: unknown[][];
  sheetName: string;
}> {
  const sampleData = {
    sheetName: "Penjualan",
    headers: ["Tanggal", "Produk", "Kategori", "Jumlah", "Harga", "Total", "Wilayah"],
    data: [
      ["2024-01-05", "Laptop ThinkPad", "Elektronik", 5, 15000000, 75000000, "Jakarta"],
      ["2024-01-12", "Mouse Wireless", "Aksesoris", 20, 250000, 5000000, "Bandung"],
      ["2024-01-18", "Keyboard Mechanical", "Aksesoris", 15, 850000, 12750000, "Jakarta"],
      ["2024-02-03", "Monitor 24inch", "Elektronik", 8, 3500000, 28000000, "Surabaya"],
      ["2024-02-14", "Laptop ThinkPad", "Elektronik", 3, 15000000, 45000000, "Bandung"],
      ["2024-02-20", "USB Hub 4 Port", "Aksesoris", 30, 180000, 5400000, "Jakarta"],
      ["2024-03-02", "Webcam HD", "Elektronik", 12, 750000, 9000000, "Surabaya"],
      ["2024-03-10", "Mouse Wireless", "Aksesoris", 25, 250000, 6250000, "Medan"],
      ["2024-03-22", "Monitor 24inch", "Elektronik", 6, 3500000, 21000000, "Jakarta"],
      ["2024-04-05", "Keyboard Mechanical", "Aksesoris", 18, 850000, 15300000, "Surabaya"],
      ["2024-04-15", "Laptop ThinkPad", "Elektronik", 7, 15000000, 105000000, "Jakarta"],
      ["2024-04-28", "Webcam HD", "Elektronik", 10, 750000, 7500000, "Bandung"],
    ],
  };
  return Promise.resolve(sampleData);
}

/** Read all worksheets from the workbook. */
export async function getAllSheetsData(): Promise<
  { sheetName: string; headers: string[]; data: unknown[][] }[]
> {
  if (typeof Excel === "undefined" || !Excel.run) {
    throw new Error("Excel AI harus dijalankan di dalam Microsoft Excel. Silakan buka add-in ini melalui menu Insert > Add-ins di Excel.");
  }

  return new Promise((resolve, reject) => {
    try {
      Excel.run(async (context) => {
        const sheets = context.workbook.worksheets;
        sheets.load("items,name");
        await context.sync();

        const result: { sheetName: string; headers: string[]; data: unknown[][] }[] = [];

        for (const sheet of sheets.items) {
          const range = sheet.getUsedRange();
          range.load("values");
          await context.sync();

          const values: unknown[][] = range.values;
          if (values && values.length > 0) {
            const headers = (values[0] as string[]).map((h) =>
              h != null ? String(h) : ""
            );
            const data = values.slice(1);
            result.push({ sheetName: sheet.name, headers, data });
          } else {
            result.push({ sheetName: sheet.name, headers: [], data: [] });
          }
        }

        resolve(result);
      });
    } catch (err) {
      reject(
        new Error(
          "Gagal membaca seluruh sheet dari workbook. Pastikan Anda berada di dalam workbook Excel."
        )
      );
    }
  });
}

// ── Formula ─────────────────────────────────────────────────────────

export async function generateFormula(
  description: string,
  sheetContext?: string
): Promise<{ formula: string; explanation: string; example: string }> {
  const res = await api.post("/formula/generate", {
    description,
    sheet_context: sheetContext || "",
  });
  return res.data;
}

export async function explainFormula(
  formula: string
): Promise<{ formula: string; explanation: string; example: string }> {
  const res = await api.post("/formula/explain", { formula });
  return res.data;
}

// ── Explain ─────────────────────────────────────────────────────────

export async function explainData(
  data: unknown[][],
  headers: string[],
  sheetName?: string
): Promise<{
  insights: string[];
  statistics: Record<string, unknown>;
  explanation: string;
}> {
  const res = await api.post("/explain/data", {
    data,
    headers,
    sheet_name: sheetName || "Sheet1",
  });
  return res.data;
}

// ── Cleaner ─────────────────────────────────────────────────────────

export async function analyzeQuality(
  data: unknown[][],
  headers: string[]
): Promise<{ issues: Issue[] }> {
  const res = await api.post("/cleaner/analyze", { data, headers });
  return res.data;
}

export async function applyCleaning(
  data: unknown[][],
  headers: string[],
  fixes: string[]
): Promise<{
  data: unknown[][];
  headers: string[];
  applied_fixes: string[];
}> {
  const res = await api.post("/cleaner/apply", { data, headers, fixes });
  return res.data;
}

// ── Audit ───────────────────────────────────────────────────────────

export async function runAudit(
  workbookData: { name: string; headers: string[]; data: unknown[][] }[]
): Promise<{
  issues: AuditIssue[];
}> {
  const res = await api.post("/audit/run", {
    workbook_data: workbookData,
  });
  return res.data;
}

// ── Chat ────────────────────────────────────────────────────────────

export async function sendChatMessage(
  message: string,
  workbookContext?: { name: string; headers: string[]; data: unknown[][] }[]
): Promise<{ reply: string; data?: Record<string, unknown> }> {
  const res = await api.post("/chat/message", {
    message,
    workbook_context: workbookContext || null,
  });
  return res.data;
}

// ── Settings ────────────────────────────────────────────────────────

export async function validateApiKey(
  apiKey: string,
  provider: string = "openai"
): Promise<{ valid: boolean; message: string }> {
  const res = await api.post("/settings/validate-key", {
    api_key: apiKey,
    provider,
  });
  return res.data;
}

// ── Types ───────────────────────────────────────────────────────────

export interface Issue {
  type: string;
  severity: "low" | "medium" | "high";
  column?: string;
  details: Record<string, unknown>;
  suggestion: string;
}

export interface AuditIssue {
  severity: "low" | "medium" | "high";
  category: string;
  description: string;
  location: string;
  suggestion: string;
}

// === V2: Dashboard ===
export async function generateDashboard(
  data: unknown[][],
  headers: string[],
  sheetName?: string
): Promise<DashboardResponse> {
  const res = await apiV2.post("/dashboard/generate", {
    data, headers, sheet_name: sheetName || "Sheet1"
  });
  return res.data;
}

// === V2: Forecast ===
export async function runForecast(
  data: unknown[][],
  headers: string[],
  dateCol: string,
  valueCol: string,
  periods: number = 12
): Promise<ForecastResponse> {
  const res = await apiV2.post("/forecast/run", {
    data, headers, date_col: dateCol, value_col: valueCol, periods
  });
  return res.data;
}

// === V2: Insights ===
export async function generateInsights(
  data: unknown[][],
  headers: string[],
  sheetName?: string
): Promise<InsightResponse> {
  const res = await apiV2.post("/insights/generate", {
    data, headers, sheet_name: sheetName || "Sheet1"
  });
  return res.data;
}

// === V2: Reports ===
export async function generatePdf(dashboardData: DashboardResponse['dashboard']): Promise<ReportResponse> {
  const res = await apiV2.post("/reports/pdf", { dashboard_data: dashboardData });
  return res.data;
}

export async function generatePpt(dashboardData: DashboardResponse['dashboard']): Promise<ReportResponse> {
  const res = await apiV2.post("/reports/ppt", { dashboard_data: dashboardData });
  return res.data;
}

// === V2 Types ===
export interface DashboardResponse {
  dashboard: {
    kpis: KpiItem[];
    charts: ChartConfig[];
    insights: string[];
    summary: Record<string, unknown>;
  };
}

export interface KpiItem {
  label: string;
  value: number;
  change_pct: number;
  icon: string;
  color: string;
  prefix?: string;
  suffix?: string;
}

export interface ChartConfig {
  type: "bar" | "line" | "pie" | "doughnut";
  title: string;
  labels: string[];
  datasets: { label: string; data: number[]; backgroundColor?: string[] }[];
}

export interface ForecastResponse {
  forecast: { ds: string; yhat: number; yhat_lower: number; yhat_upper: number }[];
  history: { ds: string; y: number }[];
  metrics: { mae: number; rmse: number; mape: number };
}

export interface InsightResponse {
  trends: { metric: string; direction: string; change_pct: number; description: string }[];
  anomalies: { column: string; value: number; z_score: number; description: string }[];
  correlations: { col1: string; col2: string; pearson: number; description: string }[];
  summary: string;
}

export interface ReportResponse {
  file_path: string;
  file_name: string;
  download_url: string;
}

// ═══════════════════════════════════════════════════════════════
// V3: Fraud Detection
// ═══════════════════════════════════════════════════════════════

export interface FraudResponse {
  anomalies: { column: string; value: number; score: number; description: string; severity: string }[];
  suspicious_patterns: { pattern: string; description: string; count: number }[];
  fraud_score: number;
  summary: string;
}

export async function detectFraud(data: unknown[][], headers: string[]): Promise<FraudResponse> {
  const res = await apiV3.post("/fraud/detect", { data, headers });
  return res.data;
}

// ═══════════════════════════════════════════════════════════════
// V3: Risk Scoring
// ═══════════════════════════════════════════════════════════════

export interface RiskResponse {
  overall_score: number;
  risk_level: string;
  dimensions: { name: string; score: number; weight: number; factors: string[] }[];
  details: string[];
}

export async function calculateRisk(data: unknown[][], headers: string[]): Promise<RiskResponse> {
  const res = await apiV3.post("/risk/score", { data, headers });
  return res.data;
}

// ═══════════════════════════════════════════════════════════════
// V3: Financial Health
// ═══════════════════════════════════════════════════════════════

export interface FinancialResponse {
  ratios: { category: string; name: string; value: number; benchmark: number; status: string }[];
  health_score: number;
  health_level: string;
  insights: string[];
}

export async function analyzeFinancial(data: unknown[][], headers: string[]): Promise<FinancialResponse> {
  const res = await apiV3.post("/financial/analyze", { data, headers });
  return res.data;
}

// ═══════════════════════════════════════════════════════════════
// V3: Inventory Intelligence
// ═══════════════════════════════════════════════════════════════

export interface InventoryResponse {
  categories: { type: string; items: string[]; count: number; value: number }[];
  stock_aging: { bracket: string; count: number; value: number }[];
  reorder_suggestions: { item: string; stock: number; reorder_point: number; suggested_qty: number }[];
  overstock: { item: string; stock: number; suggested_qty: number }[];
  summary: string;
}

export async function analyzeInventory(data: unknown[][], headers: string[]): Promise<InventoryResponse> {
  const res = await apiV3.post("/inventory/analyze", { data, headers });
  return res.data;
}

// ═══════════════════════════════════════════════════════════════
// V3: Sales Intelligence
// ═══════════════════════════════════════════════════════════════

export interface SalesResponse {
  top_customers: { name: string; revenue: number; pct: number }[];
  sales_trend: { period: string; revenue: number; growth: number }[];
  product_performance: { name: string; revenue: number; margin: number }[];
  regional_analysis: { region: string; revenue: number; count: number }[];
  summary: string;
}

export async function analyzeSales(data: unknown[][], headers: string[]): Promise<SalesResponse> {
  const res = await apiV3.post("/sales/analyze", { data, headers });
  return res.data;
}

// ═══════════════════════════════════════════════════════════════
// V3: HR Intelligence
// ═══════════════════════════════════════════════════════════════

export interface HRResponse {
  salary_analysis: { avg: number; median: number; range: [number, number]; by_department: Record<string, number> };
  headcount: { total: number; by_department: Record<string, number> };
  duplicate_employees: number;
  overtime: { avg_hours: number; by_department: Record<string, number> };
  attendance: { avg_attendance: number; by_department: Record<string, number> };
  summary: string;
}

export async function analyzeHR(data: unknown[][], headers: string[]): Promise<HRResponse> {
  const res = await apiV3.post("/hr/analyze", { data, headers });
  return res.data;
}

// ═══════════════════════════════════════════════════════════════
// V3: Connector (SQL Database)
// ═══════════════════════════════════════════════════════════════

export async function testConnection(connString: string, dbType: string): Promise<{ success: boolean; message: string }> {
  const res = await apiV3.post("/connector/test", { conn_string: connString, db_type: dbType });
  return res.data;
}

export async function getConnectorTables(connString: string, dbType: string): Promise<{ tables: { name: string; schema: string }[] }> {
  const res = await apiV3.post("/connector/tables", { conn_string: connString, db_type: dbType });
  return res.data;
}

export async function previewTable(connString: string, dbType: string, table: string): Promise<{ data: unknown[][]; headers: string[] }> {
  const res = await apiV3.post("/connector/preview", { conn_string: connString, db_type: dbType, table });
  return res.data;
}

export async function importData(connString: string, dbType: string, query: string): Promise<{ data: unknown[][]; headers: string[]; row_count: number }> {
  const res = await apiV3.post("/connector/import", { conn_string: connString, db_type: dbType, query });
  return res.data;
}


