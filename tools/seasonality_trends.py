"""
Tool 7 - Seasonality & Time Trend Analysis

Overlays monthly (or quarterly) sales trends across 2023 and 2024
so within-year seasonal patterns become visible.
"""

import pandas as pd
import plotly.graph_objects as go
import numpy as np

from config import YOY_COLORS

MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]
QUARTER_NAMES = ["Q1", "Q2", "Q3", "Q4"]


def seasonality_trends(
    df: pd.DataFrame,
    time_grain: str = "month",
    metric: str = "sales",
    division: str = None,
    region: str = None,
    category: str = None,
    brand: str = None,
    _is_dark_mode: bool = False,
) -> tuple:
    """
    Overlay monthly/quarterly trends across years to reveal seasonality.

    Args:
        df:         Full DataFrame with KPI columns.
        time_grain: 'month' or 'quarter'.
        metric:     One of 'sales', 'margin', 'units', 'margin_rate'.
        division:   Optional division filter.
        region:     Optional region filter.
        category:   Optional category filter.
        brand:      Optional brand filter.

    Returns:
        (plotly.Figure, pd.DataFrame) - overlay line chart + summary table.
    """
    metric_col_map = {
        "sales": "SALES",
        "margin": "MARGIN",
        "units": "UNITS_SOLD",
        "margin_rate": "MARGIN_RATE",
    }
    col = metric_col_map.get(metric, "SALES")

    # Apply filters
    filtered = df.copy()
    active_filters = []
    if division:
        filtered = filtered[filtered["PRODUCT_DIVISION"] == division]
        active_filters.append(f"Div: {division}")
    if region:
        filtered = filtered[filtered["REGION"] == region]
        active_filters.append(f"Reg: {region}")
    if category:
        filtered = filtered[filtered["PRODUCT_CATEGORY"] == category]
        active_filters.append(f"Cat: {category}")
    if brand:
        filtered = filtered[filtered["BRAND"] == brand]
        active_filters.append(f"Brand: {brand}")

    # Determine time column
    if time_grain == "quarter":
        time_col = "QUARTER"
        time_labels = QUARTER_NAMES
    else:
        time_col = "MONTH"
        time_labels = MONTH_NAMES

    # Aggregate
    if metric == "margin_rate":
        agg = (
            filtered.groupby(["YEAR", time_col])
            .agg(total_margin=("MARGIN", "sum"), total_sales=("SALES", "sum"))
            .reset_index()
        )
        agg[col] = (agg["total_margin"] / agg["total_sales"]).fillna(0)
    else:
        agg = (
            filtered.groupby(["YEAR", time_col])[col]
            .sum()
            .reset_index()
        )

    # Pivot: rows = time period, columns = year
    pivot = agg.pivot(index=time_col, columns="YEAR", values=col).fillna(0)
    pivot = pivot.sort_index()

    # Compute Change %
    years = sorted(pivot.columns.tolist())
    if len(years) == 2:
        pivot["Change %"] = (
            (pivot[years[1]] - pivot[years[0]]) / pivot[years[0]].replace(0, np.nan) * 100
        ).fillna(0)

    # Build chart
    metric_label = metric.replace("_", " ").title()
    grain_label = "Monthly" if time_grain != "quarter" else "Quarterly"
    filter_text = f" ({', '.join(active_filters)})" if active_filters else ""

    fig = go.Figure()
    for yr in years:
        yr_str = str(yr)
        x_vals = pivot.index.tolist()
        # Map numeric index to labels
        if time_grain == "quarter":
            x_display = [QUARTER_NAMES[int(q) - 1] if 1 <= int(q) <= 4 else str(q) for q in x_vals]
        else:
            x_display = [MONTH_NAMES[int(m) - 1] if 1 <= int(m) <= 12 else str(m) for m in x_vals]

        fig.add_trace(go.Scatter(
            x=x_display,
            y=pivot[yr].values,
            mode="lines+markers",
            name=yr_str,
            line=dict(color=YOY_COLORS.get(yr_str, "#888"), width=2.5),
            marker=dict(size=7),
        ))

    fig.update_layout(
        title=f"{grain_label} Seasonality - {metric_label}{filter_text}",
        xaxis_title="Quarter" if time_grain == "quarter" else "Month",
        yaxis_title=metric_label,
        template="plotly_dark" if _is_dark_mode else "plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_family="Inter, sans-serif",
        title_font_size=18,
        legend_title_text="Year",
    )

    # Summary table
    summary_df = pivot.reset_index()
    label_col = "Quarter" if time_grain == "quarter" else "Month"
    summary_df = summary_df.rename(columns={time_col: label_col})

    return fig, summary_df
