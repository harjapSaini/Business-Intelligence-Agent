"""
Tool 1 - Year-over-Year Comparison

Compares a chosen metric across 2023 vs 2024, grouped by the most
specific filter provided (or by division if none are given).
"""

import numpy as np
import pandas as pd
import plotly.express as px

from config import YOY_COLORS


def yoy_comparison(
    df: pd.DataFrame,
    group_by: str = "division",
    metric: str = "sales",
    division: str = None,
    region: str = None,
    category: str = None,
    brand: str = None,
    _is_dark_mode: bool = False,
) -> tuple:
    """
    Compare a metric year-over-year (2023 vs 2024).

    Args:
        df:       Full DataFrame with KPI columns.
        group_by: Column to group by ('division', 'region', 'category', 'brand').
        metric:   One of 'sales', 'margin', 'units', 'margin_rate'.
        division: Optional division filter.
        region:   Optional region filter.
        category: Optional category filter.
        brand:    Optional brand filter.

    Returns:
        (plotly.Figure, pd.DataFrame) - grouped bar chart + summary table.
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

    # Decide grouping axis from formal parameter
    group_col_map = {
        "division": "PRODUCT_DIVISION",
        "region": "REGION",
        "brand": "BRAND",
        "category": "PRODUCT_CATEGORY",
    }
    group_col = group_col_map.get(group_by.lower(), "PRODUCT_DIVISION")

    # Aggregate
    if metric == "margin_rate":
        agg = (
            filtered.groupby(["YEAR", group_col])
            .agg(total_margin=("MARGIN", "sum"), total_sales=("SALES", "sum"))
            .reset_index()
        )
        agg[col] = (agg["total_margin"] / agg["total_sales"]).fillna(0)
    else:
        agg = (
            filtered.groupby(["YEAR", group_col])[col]
            .sum()
            .reset_index()
        )

    # Build delta summary
    pivot = agg.pivot(index=group_col, columns="YEAR", values=col).fillna(0)
    if 2023 in pivot.columns and 2024 in pivot.columns:
        pivot["Change"] = pivot[2024] - pivot[2023]
        pivot["Change %"] = ((pivot["Change"] / pivot[2023].replace(0, np.nan)) * 100).fillna(0)
    summary_df = pivot.reset_index()

    # Chart
    agg["YEAR"] = agg["YEAR"].astype(str)
    metric_label = metric.replace("_", " ").title()
    
    # Build dynamic title
    title_text = f"YoY Comparison - {metric_label}"
    if active_filters:
        title_text += f" ({', '.join(active_filters)})"

    fig = px.bar(
        agg,
        x=group_col,
        y=col,
        color="YEAR",
        barmode="group",
        title=title_text,
        labels={col: metric_label, group_col: group_col.replace("_", " ").title()},
        color_discrete_map=YOY_COLORS,
    )
    fig.update_layout(
        template="plotly_dark" if _is_dark_mode else "plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_family="Inter, sans-serif",
        title_font_size=18,
        legend_title_text="Year",
    )

    return fig, summary_df
