"""Service for running workbook audits."""

import logging
from typing import Any

from core.analysis.audit import WorkbookAuditor

logger = logging.getLogger(__name__)


def run_audit(workbook_data: list[dict[str, Any]]) -> dict[str, Any]:
    """Run a full audit on the workbook data.

    Each item in ``workbook_data`` must have:
        - name : str
        - headers : list[str]
        - data : list[list]

    Returns
    -------
    dict with keys: issues
    """
    auditor = WorkbookAuditor()
    issues = auditor.audit(workbook_data)

    # Sort by severity: high → medium → low
    severity_order = {"high": 0, "medium": 1, "low": 2}
    issues.sort(key=lambda i: severity_order.get(i.get("severity", "low"), 99))

    return {
        "issues": issues,
    }
