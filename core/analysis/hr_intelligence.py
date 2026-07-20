"""HR / people analytics module."""

import logging
import warnings
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class HRAnalyzer:
    """Analyzes HR/employee data.

    Auto-detects columns and returns:
    - Salary analysis (avg, median, range, by department)
    - Headcount (total, by department, by location)
    - Overtime analysis (total hours, cost, by employee)
    - Attendance patterns if detected
    - Duplicate employees
    - Productivity metrics if detected
    - Summary
    """

    _EMPLOYEE_KEYS = {"employee", "karyawan", "name", "nama", "staff",
                      "pegawai", "employee name", "full name", "nama lengkap",
                      "person", "pekerja"}
    _SALARY_KEYS = {"salary", "gaji", "wage", "upah", "income", "pendapatan",
                    "pay", "compensation", "kompensasi", "base pay"}
    _DEPT_KEYS = {"department", "departemen", "dept", "division", "divisi",
                  "unit", "bagian", "team", "tim"}
    _LOCATION_KEYS = {"location", "lokasi", "office", "kantor", "branch",
                      "cabang", "city", "kota", "site"}
    _OVERTIME_KEYS = {"overtime", "lembur", "ot", "hours", "jam kerja",
                      "extra hours", "extra time"}
    _ATTENDANCE_KEYS = {"attendance", "absensi", "hadir", "present",
                        "absent", "absen", "sick", "sakit", "leave", "cuti",
                        "late", "telat"}
    _DATE_KEYS = {"date", "tanggal", "period", "periode", "month", "bulan",
                  "year", "tahun"}
    _POSITION_KEYS = {"position", "posisi", "jabatan", "role", "peran",
                      "title", "jabatan", "grade", "level"}
    _PRODUCTIVITY_KEYS = {"productivity", "produktivitas", "kpi", "performance",
                          "kinerja", "target", "achievement", "capaian"}

    @staticmethod
    def _to_native(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: HRAnalyzer._to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [HRAnalyzer._to_native(v) for v in obj]
        elif isinstance(obj, tuple):
            return tuple(HRAnalyzer._to_native(v) for v in obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return HRAnalyzer._to_native(obj.tolist())
        elif isinstance(obj, pd.Timestamp):
            return str(obj)
        elif pd.isna(obj):
            return None
        return obj

    def _find_column(self, df: pd.DataFrame, keywords: set) -> str | None:
        for col in df.columns:
            col_lower = str(col).lower().strip()
            for kw in keywords:
                if kw in col_lower:
                    return col
        return None

    def analyze(self, df: pd.DataFrame) -> dict:
        """Analyze HR/employee data.

        Parameters
        ----------
        df : pd.DataFrame
            HR data.

        Returns
        -------
        dict with keys: salary_analysis, headcount, overtime_analysis,
                        attendance_patterns, duplicate_employees,
                        productivity_metrics, summary.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            warnings.simplefilter("ignore", UserWarning)

            try:
                if df.empty:
                    return {
                        "salary_analysis": {},
                        "headcount": {},
                        "overtime_analysis": {},
                        "attendance_patterns": {},
                        "duplicate_employees": [],
                        "productivity_metrics": {},
                        "summary": "Data HR kosong.",
                    }

                # Auto-detect columns
                emp_col = self._find_column(df, self._EMPLOYEE_KEYS)
                salary_col = self._find_column(df, self._SALARY_KEYS)
                dept_col = self._find_column(df, self._DEPT_KEYS)
                loc_col = self._find_column(df, self._LOCATION_KEYS)
                overtime_col = self._find_column(df, self._OVERTIME_KEYS)
                attendance_col = self._find_column(df, self._ATTENDANCE_KEYS)
                date_col = self._find_column(df, self._DATE_KEYS)
                position_col = self._find_column(df, self._POSITION_KEYS)
                productivity_col = self._find_column(df, self._PRODUCTIVITY_KEYS)

                salary_analysis = {}
                headcount = {}
                overtime_analysis = {}
                attendance_patterns = {}
                duplicate_employees = []
                productivity_metrics = {}
                summary_parts = []

                # Convert numeric columns
                if salary_col:
                    df[salary_col] = pd.to_numeric(df[salary_col], errors="coerce")
                if overtime_col:
                    df[overtime_col] = pd.to_numeric(df[overtime_col], errors="coerce")
                if productivity_col:
                    df[productivity_col] = pd.to_numeric(df[productivity_col], errors="coerce")

                # ── Salary Analysis ───────────────────────────────────
                if salary_col:
                    try:
                        salaries = df[salary_col].dropna()
                        if not salaries.empty:
                            salary_data = {
                                "avg": round(float(salaries.mean()), 2),
                                "median": round(float(salaries.median()), 2),
                                "min": round(float(salaries.min()), 2),
                                "max": round(float(salaries.max()), 2),
                                "range": round(float(salaries.max() - salaries.min()), 2),
                                "std_dev": round(float(salaries.std()), 2),
                                "total": round(float(salaries.sum()), 2),
                            }

                            # By department
                            if dept_col:
                                try:
                                    dept_salary = df.groupby(dept_col)[salary_col].agg(["mean", "median", "count"])
                                    salary_data["by_department"] = {
                                        str(dept): {
                                            "avg": round(float(row["mean"]), 2),
                                            "median": round(float(row["median"]), 2),
                                            "count": int(row["count"]),
                                        }
                                        for dept, row in dept_salary.iterrows()
                                    }
                                except Exception as e:
                                    logger.warning(f"Salary by dept analysis gagal: {e}")

                            salary_analysis = salary_data
                            summary_parts.append(
                                f"Analisis gaji: rata-rata {salary_data['avg']:,.0f}, "
                                f"median {salary_data['median']:,.0f}, "
                                f"kisaran {salary_data['min']:,.0f} - {salary_data['max']:,.0f}."
                            )
                    except Exception as e:
                        logger.warning(f"Salary analysis gagal: {e}")

                # ── Headcount ─────────────────────────────────────────
                total_employees = len(df)
                headcount = {"total": total_employees}

                if emp_col:
                    unique_employees = df[emp_col].nunique()
                    headcount["unique_employees"] = int(unique_employees)
                    if unique_employees < total_employees:
                        headcount["note"] = "Terdapat duplikasi nama karyawan."

                if dept_col:
                    try:
                        dept_count = df[dept_col].value_counts()
                        headcount["by_department"] = {
                            str(dept): int(count) for dept, count in dept_count.items()
                        }
                    except Exception as e:
                        logger.warning(f"Headcount by dept gagal: {e}")

                if loc_col:
                    try:
                        loc_count = df[loc_col].value_counts()
                        headcount["by_location"] = {
                            str(loc): int(count) for loc, count in loc_count.items()
                        }
                    except Exception as e:
                        logger.warning(f"Headcount by location gagal: {e}")

                summary_parts.append(f"Total headcount: {total_employees} karyawan.")

                # ── Overtime Analysis ─────────────────────────────────
                if overtime_col:
                    try:
                        ot_data = df[overtime_col].dropna()
                        if not ot_data.empty:
                            overtime_analysis["total_hours"] = round(float(ot_data.sum()), 2)
                            overtime_analysis["avg_hours"] = round(float(ot_data.mean()), 2)
                            overtime_analysis["max_hours"] = round(float(ot_data.max()), 2)

                            # By employee if employee column exists
                            if emp_col:
                                ot_by_emp = df.groupby(emp_col)[overtime_col].sum().sort_values(ascending=False)
                                overtime_analysis["by_employee"] = [
                                    {
                                        "employee": str(emp),
                                        "total_hours": round(float(hrs), 2),
                                    }
                                    for emp, hrs in ot_by_emp.head(20).items()
                                ]

                            # Estimate cost if salary is available
                            if salary_col:
                                avg_hourly = salary_analysis.get("avg", 0) / 173  # ~173 working hours/month
                                estimated_cost = avg_hourly * float(ot_data.sum()) * 1.5  # 1.5x overtime rate
                                overtime_analysis["estimated_cost"] = round(estimated_cost, 2)

                            summary_parts.append(
                                f"Analisis lembur: total {overtime_analysis['total_hours']:,.0f} jam, "
                                f"rata-rata {overtime_analysis['avg_hours']:.1f} jam per karyawan."
                            )
                    except Exception as e:
                        logger.warning(f"Overtime analysis gagal: {e}")

                # ── Attendance Patterns ───────────────────────────────
                if attendance_col:
                    try:
                        att_data = df[attendance_col].dropna()
                        if not att_data.empty:
                            attendance_patterns = {
                                "unique_values": int(att_data.nunique()),
                                "distribution": {
                                    str(k): int(v) for k, v in att_data.value_counts().head(10).items()
                                },
                            }
                            # If date column exists, group by date
                            if date_col:
                                try:
                                    temp = df[[date_col, attendance_col]].copy()
                                    temp[date_col] = pd.to_datetime(temp[date_col], errors="coerce")
                                    temp = temp.dropna(subset=[date_col])
                                    if not temp.empty:
                                        temp["month"] = temp[date_col].dt.to_period("M").astype(str)
                                        monthly = temp.groupby("month")[attendance_col].value_counts().head(20)
                                        attendance_patterns["monthly_summary"] = {
                                            str(k): int(v) for k, v in monthly.items()
                                        }
                                except Exception as e:
                                    logger.warning(f"Attendance by date gagal: {e}")

                            summary_parts.append("Pola kehadiran terdeteksi.")
                    except Exception as e:
                        logger.warning(f"Attendance analysis gagal: {e}")

                # ── Duplicate Employees ──────────────────────────────
                if emp_col:
                    try:
                        dup_mask = df[emp_col].duplicated(keep=False)
                        if dup_mask.any():
                            dup_names = df.loc[dup_mask, emp_col].unique().tolist()
                            for name in dup_names[:20]:
                                dup_rows = df[df[emp_col] == name]
                                duplicate_employees.append({
                                    "name": str(name),
                                    "count": len(dup_rows),
                                    "details": self._to_native({
                                        col: dup_rows[col].tolist()
                                        for col in [emp_col, salary_col, dept_col]
                                        if col is not None and col in df.columns
                                    }),
                                })

                            if duplicate_employees:
                                summary_parts.append(
                                    f"Peringatan: {len(duplicate_employees)} nama karyawan duplikat terdeteksi."
                                )
                    except Exception as e:
                        logger.warning(f"Duplicate detection gagal: {e}")

                # ── Productivity Metrics ──────────────────────────────
                if productivity_col:
                    try:
                        prod_data = df[productivity_col].dropna()
                        if not prod_data.empty:
                            prod_metrics = {
                                "avg": round(float(prod_data.mean()), 2),
                                "median": round(float(prod_data.median()), 2),
                                "min": round(float(prod_data.min()), 2),
                                "max": round(float(prod_data.max()), 2),
                                "unit": "value",
                            }

                            # By employee
                            if emp_col:
                                prod_by_emp = df.groupby(emp_col)[productivity_col].mean().sort_values(ascending=False)
                                prod_metrics["top_performers"] = [
                                    {"employee": str(emp), "score": round(float(sc), 2)}
                                    for emp, sc in prod_by_emp.head(10).items()
                                ]
                                prod_metrics["bottom_performers"] = [
                                    {"employee": str(emp), "score": round(float(sc), 2)}
                                    for emp, sc in prod_by_emp.tail(5).items()
                                ]

                            productivity_metrics = prod_metrics
                            summary_parts.append(
                                f"Produktivitas: rata-rata {prod_metrics['avg']:.2f}, "
                                f"rentang {prod_metrics['min']:.2f} - {prod_metrics['max']:.2f}."
                            )
                    except Exception as e:
                        logger.warning(f"Productivity analysis gagal: {e}")

                # ── Build Summary ─────────────────────────────────────
                if not summary_parts:
                    summary_parts.append(f"{len(df)} baris data HR dianalisis.")

                summary = " | ".join(summary_parts)

                return self._to_native({
                    "salary_analysis": salary_analysis,
                    "headcount": headcount,
                    "overtime_analysis": overtime_analysis,
                    "attendance_patterns": attendance_patterns,
                    "duplicate_employees": duplicate_employees,
                    "productivity_metrics": productivity_metrics,
                    "summary": summary,
                })

            except Exception as e:
                logger.exception("HR analysis gagal")
                return {
                    "salary_analysis": {},
                    "headcount": {},
                    "overtime_analysis": {},
                    "attendance_patterns": {},
                    "duplicate_employees": [],
                    "productivity_metrics": {},
                    "summary": f"Gagal menganalisis data HR: {e}",
                }
