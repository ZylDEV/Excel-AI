"""Excel AI - Backend API"""
import sys
from pathlib import Path

# Add project root to sys.path so 'core' module is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.routers import (
    formula,
    explain,
    cleaner,
    audit,
    chat,
    settings as settings_router,
    # V2
    dashboard,
    forecast,
    insights,
    reports,
    # V3
    fraud,
    risk,
    financial,
    inventory,
    sales_intel,
    hr_intel,
    connector,
    # V3 — Added technologies
    analytics,
    database,
)

app = FastAPI(
    title="Excel AI",
    version="0.2.0",
    description="Enterprise Intelligence Platform di dalam Excel",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include V1 API routers ---
app.include_router(formula.router, prefix="/api/v1")
app.include_router(explain.router, prefix="/api/v1")
app.include_router(cleaner.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(settings_router.router, prefix="/api/v1")

# --- Include V2 API routers ---
app.include_router(dashboard.router, prefix="/api/v2")
app.include_router(forecast.router, prefix="/api/v2")
app.include_router(insights.router, prefix="/api/v2")
app.include_router(reports.router, prefix="/api/v2")

# --- Include V3 API routers ---
app.include_router(fraud.router, prefix="/api/v3")
app.include_router(risk.router, prefix="/api/v3")
app.include_router(financial.router, prefix="/api/v3")
app.include_router(inventory.router, prefix="/api/v3")
app.include_router(sales_intel.router, prefix="/api/v3")
app.include_router(hr_intel.router, prefix="/api/v3")
app.include_router(connector.router, prefix="/api/v3")
app.include_router(analytics.router, prefix="/api/v3")
app.include_router(database.router, prefix="/api/v3")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "excel-genius-ai"}


@app.get("/")
async def root():
    return {
        "message": "Excel AI - Enterprise Intelligence Platform",
        "version": "0.1.0",
        "docs": "/docs",
    }
