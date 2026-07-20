"""Pydantic models for API request/response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ── Formula ──────────────────────────────────────────────────────────

class FormulaGenerateRequest(BaseModel):
    description: str = Field(..., description="Natural language description of what the formula should do")
    sheet_context: str = Field("", description="Optional context about the sheet structure / column names")


class FormulaResponse(BaseModel):
    formula: str = Field(..., description="The generated Excel formula")
    explanation: str = Field(..., description="Plain-English explanation of the formula")
    example: str = Field("", description="Example usage of the formula")


class FormulaExplainRequest(BaseModel):
    formula: str = Field(..., description="An Excel formula to explain")


# ── Explain ──────────────────────────────────────────────────────────

class ExplainDataRequest(BaseModel):
    data: list[list[Any]] = Field(..., description="2-D array of cell values (rows × columns)")
    headers: list[str] = Field(..., description="Column header names")
    sheet_name: str = Field("Sheet1", description="Name of the sheet being analysed")


class ExplainDataResponse(BaseModel):
    insights: list[str] = Field(..., description="Data-driven insight statements")
    statistics: dict[str, Any] = Field(..., description="Comprehensive summary statistics")
    explanation: str = Field(..., description="Natural-language explanation of the data")


# ── Cleaner ──────────────────────────────────────────────────────────

class CleanerAnalyzeRequest(BaseModel):
    data: list[list[Any]] = Field(..., description="2-D array of cell values")
    headers: list[str] = Field(..., description="Column header names")


class CleanerAnalyzeResponse(BaseModel):
    issues: list[dict[str, Any]] = Field(..., description="List of quality issues found")


class CleanerApplyRequest(BaseModel):
    data: list[list[Any]] = Field(..., description="2-D array of cell values")
    headers: list[str] = Field(..., description="Column header names")
    fixes: list[str] = Field(..., description="List of fix labels to apply")


class CleanerApplyResponse(BaseModel):
    data: list[list[Any]] = Field(..., description="Cleaned data (rows × columns)")
    headers: list[str] = Field(..., description="Headers after cleaning")
    applied_fixes: list[str] = Field(..., description="Fixes that were actually applied")


# ── Audit ────────────────────────────────────────────────────────────

class SheetData(BaseModel):
    name: str = Field(..., description="Sheet name")
    headers: list[str] = Field(..., description="Column headers")
    data: list[list[Any]] = Field(..., description="Row data")


class AuditRunRequest(BaseModel):
    workbook_data: list[SheetData] = Field(..., description="List of sheets to audit")


class AuditRunResponse(BaseModel):
    issues: list[dict[str, Any]] = Field(..., description="All audit issues found")


# ── Chat ─────────────────────────────────────────────────────────────

class SheetContext(BaseModel):
    name: str = Field("Sheet1", description="Sheet name")
    headers: list[str] = Field(default_factory=list, description="Column headers")
    data: list[list[Any]] = Field(default_factory=list, description="Row data")


class ChatMessageRequest(BaseModel):
    message: str = Field(..., description="The user's chat message")
    workbook_context: list[SheetContext] | None = Field(None, description="Optional workbook data context")


class ChatMessageResponse(BaseModel):
    reply: str = Field(..., description="The AI's reply")
    data: dict[str, Any] | None = Field(None, description="Optional structured data extracted from the reply")


# ═════════════════════════════════════════════════════════════════════
# V2 — Dashboard
# ═════════════════════════════════════════════════════════════════════

class DashboardGenerateRequest(BaseModel):
    data: list[list[Any]] = Field(..., description="2-D array of cell values (rows x columns)")
    headers: list[str] = Field(..., description="Column header names")
    sheet_name: str = Field("Sheet1", description="Nama sheet yang dianalisis")


class DashboardGenerateResponse(BaseModel):
    kpis: list[dict[str, Any]] = Field(default_factory=list, description="KPI cards")
    charts: list[dict[str, Any]] = Field(default_factory=list, description="Chart configurations")
    insights: list[str] = Field(default_factory=list, description="Key insight statements")
    summary: dict[str, Any] = Field(default_factory=dict, description="Numeric summary")


# ═════════════════════════════════════════════════════════════════════
# V2 — Forecast
# ═════════════════════════════════════════════════════════════════════

class ForecastRunRequest(BaseModel):
    data: list[list[Any]] = Field(..., description="2-D array of cell values")
    headers: list[str] = Field(..., description="Column header names")
    date_col: str = Field(..., description="Nama kolom tanggal")
    value_col: str = Field(..., description="Nama kolom nilai yang akan di-forecast")
    periods: int = Field(12, description="Jumlah periode ke depan untuk di-forecast", ge=1, le=120)


class ForecastRunResponse(BaseModel):
    forecast: list[dict[str, Any]] = Field(default_factory=list, description="Hasil forecast (ds, yhat, yhat_lower, yhat_upper)")
    history: list[dict[str, Any]] = Field(default_factory=list, description="Data historis (ds, y)")
    metrics: dict[str, Any] = Field(default_factory=dict, description="Metrik akurasi (mae, rmse, mape)")
    seasonality: dict[str, Any] = Field(default_factory=dict, description="Komponen musiman (trend, yearly, weekly, daily)")
    error: str | None = Field(None, description="Pesan error jika forecasting gagal")


# ═════════════════════════════════════════════════════════════════════
# V2 — Insights
# ═════════════════════════════════════════════════════════════════════

class InsightsGenerateRequest(BaseModel):
    data: list[list[Any]] = Field(..., description="2-D array of cell values")
    headers: list[str] = Field(..., description="Column header names")
    sheet_name: str = Field("Sheet1", description="Nama sheet yang dianalisis")


class InsightsGenerateResponse(BaseModel):
    trends: list[dict[str, Any]] = Field(default_factory=list, description="Tren yang terdeteksi")
    anomalies: list[dict[str, Any]] = Field(default_factory=list, description="Anomali yang terdeteksi")
    correlations: list[dict[str, Any]] = Field(default_factory=list, description="Korelasi antar variabel")
    top_performers: list[dict[str, Any]] = Field(default_factory=list, description="Kategori dengan performa terbaik")
    summary: str = Field("", description="Ringkasan insights (LLM-enhanced jika API key tersedia)")


# ═════════════════════════════════════════════════════════════════════
# V2 — Reports
# ═════════════════════════════════════════════════════════════════════

class ReportGenerateRequest(BaseModel):
    dashboard_data: dict[str, Any] = Field(..., description="Dashboard configuration dari endpoint /dashboard/generate")


class ReportGenerateResponse(BaseModel):
    file_path: str = Field("", description="Path absolut file laporan yang dihasilkan")
    file_name: str = Field("", description="Nama file laporan")
    download_url: str = Field("", description="URL untuk mengunduh laporan")
    error: str | None = Field(None, description="Pesan error jika pembuatan laporan gagal")


# ═════════════════════════════════════════════════════════════════════
# V3 — Fraud Detection
# ═════════════════════════════════════════════════════════════════════


class FraudDetectRequest(BaseModel):
    data: list[list[Any]] = Field(..., description="2-D array of cell values (rows x columns)")
    headers: list[str] = Field(..., description="Column header names")
    sheet_name: str = Field("Sheet1", description="Nama sheet yang dianalisis")


class FraudDetectResponse(BaseModel):
    anomalies: list[dict[str, Any]] = Field(default_factory=list, description="Anomali yang terdeteksi")
    suspicious_patterns: list[dict[str, Any]] = Field(default_factory=list, description="Pola mencurigakan")
    fraud_score: float = Field(0.0, description="Skor fraud 0-100")
    summary: str = Field("", description="Ringkasan hasil deteksi")


# ═════════════════════════════════════════════════════════════════════
# V3 — Risk Scoring
# ═════════════════════════════════════════════════════════════════════


class RiskScoreRequest(BaseModel):
    data: list[list[Any]] = Field(..., description="2-D array of cell values (rows x columns)")
    headers: list[str] = Field(..., description="Column header names")
    sheet_name: str = Field("Sheet1", description="Nama sheet yang dianalisis")


class RiskScoreResponse(BaseModel):
    overall_score: float = Field(0.0, description="Skor risiko keseluruhan 0-100")
    dimensions: list[dict[str, Any]] = Field(default_factory=list, description="Dimensi risiko")
    risk_level: str = Field("low", description="Level risiko: low | medium | high | critical")
    details: list[str] = Field(default_factory=list, description="Detail faktor risiko")


# ═════════════════════════════════════════════════════════════════════
# V3 — Financial Health
# ═════════════════════════════════════════════════════════════════════


class FinancialHealthRequest(BaseModel):
    data: list[list[Any]] = Field(..., description="2-D array of cell values (rows x columns)")
    headers: list[str] = Field(..., description="Column header names")
    sheet_name: str = Field("Sheet1", description="Nama sheet yang dianalisis")


class FinancialHealthResponse(BaseModel):
    profitability_ratios: list[dict[str, Any]] = Field(default_factory=list, description="Rasio profitabilitas")
    liquidity_ratios: list[dict[str, Any]] = Field(default_factory=list, description="Rasio likuiditas")
    efficiency_ratios: list[dict[str, Any]] = Field(default_factory=list, description="Rasio efisiensi")
    growth_metrics: list[dict[str, Any]] = Field(default_factory=list, description="Metrik pertumbuhan")
    health_score: float = Field(0.0, description="Skor kesehatan finansial 0-100")
    health_level: str = Field("poor", description="Level kesehatan: excellent | good | fair | poor | critical")
    insights: list[str] = Field(default_factory=list, description="Temuan kunci")


# ═════════════════════════════════════════════════════════════════════
# V3 — Inventory Intelligence
# ═════════════════════════════════════════════════════════════════════


class InventoryAnalysisRequest(BaseModel):
    data: list[list[Any]] = Field(..., description="2-D array of cell values (rows x columns)")
    headers: list[str] = Field(..., description="Column header names")
    sheet_name: str = Field("Sheet1", description="Nama sheet yang dianalisis")


class InventoryAnalysisResponse(BaseModel):
    categories: dict[str, Any] = Field(default_factory=dict, description="Kategori stok")
    stock_aging: list[dict[str, Any]] = Field(default_factory=list, description="Aging stok")
    reorder_suggestions: list[dict[str, Any]] = Field(default_factory=list, description="Saran reorder")
    overstock_items: list[dict[str, Any]] = Field(default_factory=list, description="Item overstock")
    warehouse_distribution: list[dict[str, Any]] = Field(default_factory=list, description="Distribusi gudang")
    summary: str = Field("", description="Ringkasan analisis")


# ═════════════════════════════════════════════════════════════════════
# V3 — Sales Intelligence
# ═════════════════════════════════════════════════════════════════════


class SalesAnalysisRequest(BaseModel):
    data: list[list[Any]] = Field(..., description="2-D array of cell values (rows x columns)")
    headers: list[str] = Field(..., description="Column header names")
    sheet_name: str = Field("Sheet1", description="Nama sheet yang dianalisis")


class SalesAnalysisResponse(BaseModel):
    top_customers: list[dict[str, Any]] = Field(default_factory=list, description="Pelanggan teratas")
    customer_segments: list[dict[str, Any]] = Field(default_factory=list, description="Segmen pelanggan")
    sales_trend: list[dict[str, Any]] = Field(default_factory=list, description="Tren penjualan")
    product_performance: list[dict[str, Any]] = Field(default_factory=list, description="Performa produk")
    regional_analysis: list[dict[str, Any]] = Field(default_factory=list, description="Analisis regional")
    cross_selling_opportunities: list[dict[str, Any]] = Field(default_factory=list, description="Peluang cross-selling")
    summary: str = Field("", description="Ringkasan analisis")


# ═════════════════════════════════════════════════════════════════════
# V3 — HR Intelligence
# ═════════════════════════════════════════════════════════════════════


class HRAnalysisRequest(BaseModel):
    data: list[list[Any]] = Field(..., description="2-D array of cell values (rows x columns)")
    headers: list[str] = Field(..., description="Column header names")
    sheet_name: str = Field("Sheet1", description="Nama sheet yang dianalisis")


class HRAnalysisResponse(BaseModel):
    salary_analysis: dict[str, Any] = Field(default_factory=dict, description="Analisis gaji")
    headcount: dict[str, Any] = Field(default_factory=dict, description="Data headcount")
    overtime_analysis: dict[str, Any] = Field(default_factory=dict, description="Analisis lembur")
    attendance_patterns: dict[str, Any] = Field(default_factory=dict, description="Pola kehadiran")
    duplicate_employees: list[dict[str, Any]] = Field(default_factory=list, description="Karyawan duplikat")
    productivity_metrics: dict[str, Any] = Field(default_factory=dict, description="Metrik produktivitas")
    summary: str = Field("", description="Ringkasan analisis")


# ═════════════════════════════════════════════════════════════════════
# V3 — Database Connector
# ═════════════════════════════════════════════════════════════════════


class ConnectorTestRequest(BaseModel):
    connection_string: str = Field(..., description="Koneksi string database")
    db_type: str = Field("", description="Tipe database (postgresql | mysql | mssql | sqlite)")


class ConnectorTestResponse(BaseModel):
    success: bool = Field(False, description="Status koneksi")
    message: str = Field("", description="Pesan hasil koneksi")


class ConnectorTablesRequest(BaseModel):
    connection_string: str = Field(..., description="Koneksi string database")
    db_type: str = Field("", description="Tipe database")


class ConnectorTablesResponse(BaseModel):
    tables: list[str] = Field(default_factory=list, description="Daftar tabel")
    count: int = Field(0, description="Jumlah tabel")
    error: str | None = Field(None, description="Pesan error jika ada")


class ConnectorPreviewRequest(BaseModel):
    connection_string: str = Field(..., description="Koneksi string database")
    db_type: str = Field("", description="Tipe database")
    table_name: str = Field(..., description="Nama tabel untuk di-preview")


class ConnectorPreviewResponse(BaseModel):
    columns: list[dict[str, Any]] = Field(default_factory=list, description="Metadata kolom")
    preview_data: list[list[Any]] = Field(default_factory=list, description="Data preview")
    preview_headers: list[str] = Field(default_factory=list, description="Header preview")
    row_count: int = Field(0, description="Jumlah baris")
    error: str | None = Field(None, description="Pesan error jika ada")


class ConnectorImportRequest(BaseModel):
    connection_string: str = Field(..., description="Koneksi string database")
    db_type: str = Field("", description="Tipe database")
    query: str = Field(..., description="SQL query untuk import data")


class ConnectorImportResponse(BaseModel):
    data: list[list[Any]] = Field(default_factory=list, description="Data hasil query")
    headers: list[str] = Field(default_factory=list, description="Header data")
    row_count: int = Field(0, description="Jumlah baris data")
    error: str | None = Field(None, description="Pesan error jika ada")


# ═════════════════════════════════════════════════════════════════════
# V3 — SQL Analytics
# ═════════════════════════════════════════════════════════════════════


class AnalyticsSQLRequest(BaseModel):
    data: list[list[Any]] = Field(..., description="2-D array of cell values (rows x columns)")
    headers: list[str] = Field(..., description="Column header names")
    sql_query: str = Field(..., description="SQL query to run. Table name is 'data'")


class AnalyticsSQLResponse(BaseModel):
    columns: list[str] = Field(default_factory=list, description="Nama kolom hasil query")
    rows: list[list[Any]] = Field(default_factory=list, description="Baris hasil query")
    row_count: int = Field(0, description="Jumlah baris hasil")
    error: str | None = Field(None, description="Pesan error jika query gagal")


# ═════════════════════════════════════════════════════════════════════
# V3 — Predictive Model (XGBoost / LightGBM)
# ═════════════════════════════════════════════════════════════════════


class PredictiveTrainRequest(BaseModel):
    data: list[list[Any]] = Field(..., description="2-D array of cell values (rows x columns)")
    headers: list[str] = Field(..., description="Column header names")
    target_col: str = Field(..., description="Nama kolom target yang akan diprediksi")
    feature_cols: list[str] | None = Field(None, description="Nama kolom fitur (optional, default semua numerik)")
    model_type: str = Field("xgboost", description="Jenis model: xgboost | lightgbm")


class PredictiveTrainResponse(BaseModel):
    metrics: dict[str, Any] = Field(default_factory=dict, description="Metrik evaluasi: mae, rmse, r2")
    feature_importance: list[dict[str, Any]] = Field(default_factory=list, description="Feature importance")
    predictions: list[dict[str, Any]] = Field(default_factory=list, description="Prediksi vs aktual (test set)")
    model_type: str = Field("", description="Jenis model yang digunakan")
    summary: str = Field("", description="Ringkasan hasil training")


class PredictivePredictRequest(BaseModel):
    data: list[list[Any]] = Field(..., description="2-D array of cell values (rows x columns)")
    headers: list[str] = Field(..., description="Column header names")
    target_col: str = Field(..., description="Nama kolom target")
    feature_cols: list[str] | None = Field(None, description="Nama kolom fitur")
    model_type: str = Field("xgboost", description="Jenis model: xgboost | lightgbm")


class PredictivePredictResponse(BaseModel):
    metrics: dict[str, Any] = Field(default_factory=dict, description="Metrik evaluasi: mae, rmse, r2")
    feature_importance: list[dict[str, Any]] = Field(default_factory=list, description="Feature importance")
    predictions: list[float] = Field(default_factory=list, description="Hasil prediksi untuk setiap baris")
    model_type: str = Field("", description="Jenis model yang digunakan")
    summary: str = Field("", description="Ringkasan hasil prediksi")


# ═════════════════════════════════════════════════════════════════════
# V3 — Database Storage
# ═════════════════════════════════════════════════════════════════════


class DBSaveRequest(BaseModel):
    sheet_name: str = Field(..., description="Nama sheet yang dianalisis")
    analysis_type: str = Field(..., description="Tipe analisis (dashboard, forecast, fraud, dll)")
    result: dict[str, Any] = Field(..., description="Data hasil analisis yang akan disimpan")


class DBSaveResponse(BaseModel):
    success: bool = Field(False, description="Status penyimpanan")
    record_id: int = Field(-1, description="ID record yang disimpan")
    message: str = Field("", description="Pesan hasil penyimpanan")


class DBHistoryRequest(BaseModel):
    analysis_type: str | None = Field(None, description="Filter berdasarkan tipe analisis")
    limit: int = Field(20, description="Jumlah maksimal record", ge=1, le=100)


class DBHistoryResponse(BaseModel):
    records: list[dict[str, Any]] = Field(default_factory=list, description="Daftar histori analisis")
    count: int = Field(0, description="Jumlah record")
    message: str = Field("", description="Pesan hasil")


# ═════════════════════════════════════════════════════════════════════
# V3 — Visualization / Charts
# ═════════════════════════════════════════════════════════════════════


class ChartGenerateRequest(BaseModel):
    dashboard_data: dict[str, Any] = Field(..., description="Dashboard configuration dari endpoint /dashboard/generate")


class ChartGenerateResponse(BaseModel):
    charts: list[dict[str, Any]] = Field(default_factory=list, description="Daftar chart dalam format Plotly JSON")
    count: int = Field(0, description="Jumlah chart yang dihasilkan")
    error: str | None = Field(None, description="Pesan error jika pembuatan chart gagal")
