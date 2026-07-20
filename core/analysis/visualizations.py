"""Generate Plotly charts for export (PDF/PPT reports)."""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Attempt to import Plotly
try:
    import plotly.graph_objects as go

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.info("Plotly tidak tersedia, chart tidak dapat dibuat")


class ChartGenerator:
    """Generate Plotly charts for report exports.

    Converts dashboard chart configurations (from ``DashboardGenerator``)
    into Plotly JSON figures that can be rendered or embedded in PDF/PPT.
    """

    @staticmethod
    def _is_plotly_available() -> bool:
        """Check if Plotly is installed."""
        return PLOTLY_AVAILABLE

    @staticmethod
    def generate_charts(dashboard_data: dict) -> list[dict]:
        """Convert dashboard chart configs to Plotly JSON figures.

        Parameters
        ----------
        dashboard_data : dict
            Dashboard configuration dictionary as returned by
            ``DashboardGenerator.generate()``.  Expected to contain a
            ``"charts"`` key with a list of chart config dicts.

        Each chart config dict should have:
            - ``type``: ``"bar"`` | ``"line"`` | ``"pie"``
            - ``title``: chart title
            - ``labels``: list of category labels (bar/pie) or x-values (line)
            - ``values``: list of numeric values
            - ``series``: (optional) list of dicts with ``name`` and ``values``
              for multi-series bar/line charts

        Returns
        -------
        list[dict] where each item has:
            - ``figure_json``: Plotly figure serialized to JSON dict
            - ``title``: str
            - ``type``: str
        """
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly tidak terinstall — tidak dapat membuat chart")
            return []

        charts = dashboard_data.get("charts", [])
        if not charts:
            logger.info("Tidak ada konfigurasi chart dalam dashboard_data")
            return []

        results: list[dict] = []

        for chart_cfg in charts:
            try:
                chart_type = chart_cfg.get("type", "bar").lower()
                title = chart_cfg.get("title", "Chart")
                labels = chart_cfg.get("labels", [])
                values = chart_cfg.get("values", [])
                series = chart_cfg.get("series", [])

                figure = None

                if chart_type == "bar":
                    figure = ChartGenerator._make_bar(title, labels, values, series)
                elif chart_type == "line":
                    figure = ChartGenerator._make_line(title, labels, values, series)
                elif chart_type == "pie":
                    figure = ChartGenerator._make_pie(title, labels, values)
                else:
                    logger.warning("Tipe chart tidak dikenal: %s", chart_type)
                    continue

                if figure is not None:
                    figure_json = figure.to_dict()
                    results.append({
                        "figure_json": figure_json,
                        "title": title,
                        "type": chart_type,
                    })

            except Exception as exc:
                logger.exception("Gagal membuat chart '%s'", chart_cfg.get("title", "untitled"))
                continue

        return results

    @staticmethod
    def _make_bar(title: str, labels: list, values: list, series: list) -> Any | None:
        """Create a bar chart figure."""
        fig = go.Figure()

        if series:
            for s in series:
                fig.add_trace(go.Bar(
                    name=s.get("name", ""),
                    x=labels,
                    y=s.get("values", []),
                ))
        else:
            fig.add_trace(go.Bar(
                x=labels,
                y=values,
                marker_color="rgba(54, 162, 235, 0.8)",
            ))

        fig.update_layout(
            title=title,
            xaxis_title="",
            yaxis_title="",
            template="plotly_white",
            hovermode="x unified",
            margin=dict(l=40, r=20, t=50, b=40),
            height=400,
        )
        return fig

    @staticmethod
    def _make_line(title: str, labels: list, values: list, series: list) -> Any | None:
        """Create a line chart figure."""
        fig = go.Figure()

        if series:
            for s in series:
                fig.add_trace(go.Scatter(
                    name=s.get("name", ""),
                    x=labels,
                    y=s.get("values", []),
                    mode="lines+markers",
                    line=dict(width=2),
                ))
        else:
            fig.add_trace(go.Scatter(
                x=labels,
                y=values,
                mode="lines+markers",
                line=dict(width=2, color="rgba(75, 192, 192, 1)"),
                marker=dict(size=6),
            ))

        fig.update_layout(
            title=title,
            xaxis_title="",
            yaxis_title="",
            template="plotly_white",
            hovermode="x unified",
            margin=dict(l=40, r=20, t=50, b=40),
            height=400,
        )
        return fig

    @staticmethod
    def _make_pie(title: str, labels: list, values: list) -> Any | None:
        """Create a pie chart figure."""
        fig = go.Figure()

        fig.add_trace(go.Pie(
            labels=labels,
            values=values,
            textinfo="label+percent",
            insidetextorientation="radial",
            marker=dict(
                colors=[
                    "rgba(54, 162, 235, 0.8)",
                    "rgba(255, 99, 132, 0.8)",
                    "rgba(255, 206, 86, 0.8)",
                    "rgba(75, 192, 192, 0.8)",
                    "rgba(153, 102, 255, 0.8)",
                    "rgba(255, 159, 64, 0.8)",
                ]
            ),
        ))

        fig.update_layout(
            title=title,
            template="plotly_white",
            margin=dict(l=20, r=20, t=50, b=20),
            height=400,
            showlegend=True,
        )
        return fig
