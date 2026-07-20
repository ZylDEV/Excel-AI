"""API routers for Excel Genius AI."""
from backend.app.routers import formula
from backend.app.routers import explain
from backend.app.routers import cleaner
from backend.app.routers import audit
from backend.app.routers import chat

# V2
from backend.app.routers import dashboard
from backend.app.routers import forecast
from backend.app.routers import insights
from backend.app.routers import reports

# V3
from backend.app.routers import fraud
from backend.app.routers import risk
from backend.app.routers import financial
from backend.app.routers import inventory
from backend.app.routers import sales_intel
from backend.app.routers import hr_intel
from backend.app.routers import connector
from backend.app.routers import analytics
from backend.app.routers import database

__all__ = [
    "formula", "explain", "cleaner", "audit", "chat",
    "dashboard", "forecast", "insights", "reports",
    "fraud", "risk", "financial", "inventory",
    "sales_intel", "hr_intel", "connector",
    "analytics", "database",
]
