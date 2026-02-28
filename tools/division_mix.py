"""
Tool 8 - Market Basket / Division Mix Analysis

Shows how much each division contributes to total business and
whether the mix shifted between 2023 and 2024 using side-by-side
donut charts.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import CHART_COLORS


def division_mix(
    df: pd.DataFrame,
    metric: str = "sales",
    division: str = None,
    region: str = None,
    category: str = None,
    brand: str = None,
    _is_dark_mode: bool = False,
) -> tuple:
    """
    Side-by-side donut charts showing division revenue mix for each year.

    Args:
        df:       Full DataFrame with KPI columns.
        metric:   One of 'sales', 'margin', 'units'.
        division: Optional division filter.
        region:   Optional region filter.
        category: Optional category filter.
        brand:    Optional brand filter.

    Returns:
        (plotly.Figure, pd.DataFrame) - donut chart pair + mix summary table.
    """
    metric_col_map = {
        "sales": "SALES",
        "margin": "MARGIN",
        "units": "UNITS_SOLD",
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

    # Aggregate by year + division
    agg = (
        filtered.groupby(["YEAR", "PRODUCT_DIVISION"])[col]
        .sum()
        .reset_index()
    )

    years = sorted(agg["YEAR"].unique().tolist())
    divisions = sorted(agg["PRODUCT_DIVISION"].unique().tolist())

    # Build summary DataFrame
    records = []
    for div in divisions:
        row = {"Division": div}
        for yr in years:
            val = agg[(agg["YEAR"] == yr) & (agg["PRODUCT_DIVISION"] == div)][col].sum()
            yr_total = agg[agg["YEAR"] == yr][col].sum()
            share = (val / yr_total * 100) if yr_total > 0 else 0
            row[f"{yr}_Value"] = val
            row[f"{yr}_Share%"] = round(share, 1)
        if len(years) == 2:
            row["Shift_pp"] = round(row[f"{years[1]}_Share%"] - row[f"{years[0]}_Share%"], 1)
        records.append(row)
    summary_df = pd.DataFrame(records)

    # Build side-by-side donut charts
    metric_label = metric.replace("_", " ").title()
    filter_text = f" ({', '.join(active_filters)})" if active_filters else ""

    fig = make_subplots(
        rows=1, cols=len(years),
        specs=[[{"type": "pie"}] * len(years)],
        subplot_titles=[f"{yr}" for yr in years],
    )

    for i, yr in enumerate(years):
        yr_data = agg[agg["YEAR"] == yr].sort_values("PRODUCT_DIVISION")
        fig.add_trace(
            go.Pie(
                labels=yr_data["PRODUCT_DIVISION"],
                values=yr_data[col],
                hole=0.45,
                marker=dict(colors=CHART_COLORS[: len(yr_data)]),
                textinfo="label+percent",
                textposition="inside",
                name=str(yr),
            ),
            row=1, col=i + 1,
        )

    fig.update_layout(
        title=f"Division Mix - {metric_label}{filter_text}",
        template="plotly_dark" if _is_dark_mode else "plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_family="Inter, sans-serif",
        title_font_size=18,
        showlegend=True,
        height=500,
    )

    return fig, summary_df
