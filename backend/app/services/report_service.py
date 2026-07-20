"""Service for generating PDF and PPTX reports."""

import logging
from pathlib import Path
from typing import Any

from core.analysis.reports import ReportGenerator

logger = logging.getLogger(__name__)

# Base URL for downloading generated reports (adjust in production)
DOWNLOAD_BASE_URL = "/api/v2/reports/download"


def _build_download_url(file_path: str) -> str:
    """Build a download URL from a file path."""
    p = Path(file_path)
    return f"{DOWNLOAD_BASE_URL}/{p.name}"


def generate_pdf_report(dashboard_data: dict) -> dict[str, Any]:
    """Generate a PDF report from dashboard data.

    Parameters
    ----------
    dashboard_data : dict
        Dashboard configuration data (output of DashboardGenerator).

    Returns
    -------
    dict with keys: file_path, file_name, download_url.
    """
    try:
        file_path = ReportGenerator.generate_pdf(dashboard_data)
        p = Path(file_path)

        return {
            "file_path": str(p),
            "file_name": p.name,
            "download_url": _build_download_url(str(p)),
        }

    except Exception as e:
        logger.exception("PDF report service gagal")
        return {
            "file_path": "",
            "file_name": "",
            "download_url": "",
            "error": str(e),
        }


def generate_ppt_report(dashboard_data: dict) -> dict[str, Any]:
    """Generate a PowerPoint report from dashboard data.

    Parameters
    ----------
    dashboard_data : dict
        Dashboard configuration data (output of DashboardGenerator).

    Returns
    -------
    dict with keys: file_path, file_name, download_url.
    """
    try:
        file_path = ReportGenerator.generate_ppt(dashboard_data)
        p = Path(file_path)

        return {
            "file_path": str(p),
            "file_name": p.name,
            "download_url": _build_download_url(str(p)),
        }

    except Exception as e:
        logger.exception("PPT report service gagal")
        return {
            "file_path": "",
            "file_name": "",
            "download_url": "",
            "error": str(e),
        }
