"""Core analysis modules for Excel AI."""

from core.analysis.audit import WorkbookAuditor
from core.analysis.business_insights import BusinessInsights
from core.analysis.dashboard import DashboardGenerator
from core.analysis.data_quality import DataQualityAnalyzer
from core.analysis.explainer import DataExplainer
from core.analysis.forecast import TimeSeriesForecaster
from core.analysis.reports import ReportGenerator

# V3
from core.analysis.fraud_detection import FraudDetector
from core.analysis.risk_scoring import RiskScorer
from core.analysis.financial_health import FinancialHealthAnalyzer
from core.analysis.inventory_intelligence import InventoryAnalyzer
from core.analysis.sales_intelligence import SalesAnalyzer
from core.analysis.hr_intelligence import HRAnalyzer
from core.analysis.sql_connector import SQLConnector

from core.analysis.duckdb_analytics import DuckDBAnalytics
from core.analysis.visualizations import ChartGenerator

__all__ = [
    "WorkbookAuditor",
    "BusinessInsights",
    "DashboardGenerator",
    "DataQualityAnalyzer",
    "DataExplainer",
    "TimeSeriesForecaster",
    "ReportGenerator",
    # V3
    "FraudDetector",
    "RiskScorer",
    "FinancialHealthAnalyzer",
    "InventoryAnalyzer",
    "SalesAnalyzer",
    "HRAnalyzer",
    "SQLConnector",
    # Added technologies
    "DuckDBAnalytics",
    "ChartGenerator",
]
