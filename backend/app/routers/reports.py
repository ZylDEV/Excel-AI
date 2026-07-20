"""API router for PDF and PPTX report generation (V2)."""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.models.schemas import ReportGenerateRequest, ReportGenerateResponse
from app.services.report_service import generate_pdf_report, generate_ppt_report

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Reports V2"])


@router.post("/reports/pdf", response_model=ReportGenerateResponse)
async def api_generate_pdf(req: ReportGenerateRequest):
    """Generate a PDF report from dashboard data.

    Accepts dashboard configuration data (output of /api/v2/dashboard/generate)
    and produces a downloadable PDF file with cover page, executive summary,
    KPI table, chart info, and insights.
    """
    try:
        result = generate_pdf_report(dashboard_data=req.dashboard_data)
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])
        return ReportGenerateResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("PDF report generation gagal")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/ppt", response_model=ReportGenerateResponse)
async def api_generate_ppt(req: ReportGenerateRequest):
    """Generate a PowerPoint report from dashboard data.

    Accepts dashboard configuration data and produces a downloadable PPTX
    file with title slide, executive summary, KPI summary, charts, and insights.
    """
    try:
        result = generate_ppt_report(dashboard_data=req.dashboard_data)
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])
        return ReportGenerateResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("PPT report generation gagal")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/download/{file_name}")
async def download_report(file_name: str):
    """Download a generated report file."""
    reports_dir = Path(__file__).resolve().parent.parent.parent / "reports"
    file_path = reports_dir / file_name

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"File '{file_name}' tidak ditemukan")

    return FileResponse(
        path=str(file_path),
        filename=file_name,
        media_type="application/octet-stream",
    )
