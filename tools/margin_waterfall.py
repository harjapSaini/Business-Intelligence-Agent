"""
Tool 9 - Margin Waterfall / Profitability Decomposition

Waterfall chart showing 2023 total → per-division contribution → 2024 total,
explaining what drove the change in margin (or sales) between years.
"""

import pandas as pd
import plotly.graph_objects as go

from config import WATERFALL_COLORS


def margin_waterfall(
    df: pd.DataFrame,
    metric: str = "margin",
    group_by: str = "division",
    division: str = None,
    region: str = None,
    category: str = None,
    brand: str = None,
    _is_dark_mode: bool = False,
) -> tuple:
    """
    Waterfall chart decomposing year-over-year change by group.

    Args:
        df:       Full DataFrame with KPI columns.
        metric:   One of 'margin', 'sales', 'units'.
        group_by: Grouping dimension ('division', 'region', 'brand', 'category').
        division: Optional division filter.
        region:   Optional region filter.
        category: Optional category filter.
        brand:    Optional brand filter.

    Returns:
        (plotly.Figure, pd.DataFrame) - waterfall chart + contribution table.
    """
    metric_col_map = {
        "sales": "SALES",
        "margin": "MARGIN",
        "units": "UNITS_SOLD",
    }
    group_col_map = {
        "division": "PRODUCT_DIVISION",
        "region": "REGION",
        "brand": "BRAND",
        "category": "PRODUCT_CATEGORY",
    }
    col = metric_col_map.get(metric, "MARGIN")
    group_col = group_col_map.get(group_by, "PRODUCT_DIVISION")

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

    # Aggregate by year + group
    agg = (
        filtered.groupby(["YEAR", group_col])[col]
        .sum()
        .reset_index()
    )
    pivot = agg.pivot(index=group_col, columns="YEAR", values=col).fillna(0)

    years = sorted(pivot.columns.tolist())
    if len(years) < 2:
        # Fallback: need two years for a waterfall
        years = [years[0], years[0]]

    yr_start, yr_end = years[0], years[-1]

    # Compute deltas
    pivot["Change"] = pivot[yr_end] - pivot[yr_start]
    pivot["Change %"] = ((pivot["Change"] / pivot[yr_start].replace(0, 1)) * 100).round(1)
    pivot = pivot.sort_values("Change", ascending=False)

    total_start = pivot[yr_start].sum()
    total_end = pivot[yr_end].sum()

    # Build waterfall data
    labels = [f"{yr_start} Total"] + pivot.index.tolist() + [f"{yr_end} Total"]
    measures = ["absolute"] + ["relative"] * len(pivot) + ["total"]
    values = [total_start] + pivot["Change"].tolist() + [total_end]

    # Colour mapping
    colors = [WATERFALL_COLORS["total"]]
    for v in pivot["Change"]:
        colors.append(WATERFALL_COLORS["increase"] if v >= 0 else WATERFALL_COLORS["decrease"])
    colors.append(WATERFALL_COLORS["total"])

    metric_label = metric.replace("_", " ").title()
    filter_text = f" ({', '.join(active_filters)})" if active_filters else ""

    fig = go.Figure(go.Waterfall(
        x=labels,
        y=values,
        measure=measures,
        connector=dict(line=dict(color="rgba(128,128,128,0.4)")),
        increasing=dict(marker=dict(color=WATERFALL_COLORS["increase"])),
        decreasing=dict(marker=dict(color=WATERFALL_COLORS["decrease"])),
        totals=dict(marker=dict(color=WATERFALL_COLORS["total"])),
        textposition="outside",
        text=[f"${v:,.0f}" for v in values],
    ))

    fig.update_layout(
        title=f"{metric_label} Waterfall by {group_by.title()}{filter_text}",
        yaxis_title=metric_label,
        template="plotly_dark" if _is_dark_mode else "plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_family="Inter, sans-serif",
        title_font_size=18,
        showlegend=False,
        height=500,
    )

    # Summary table
    summary_df = pivot.reset_index().rename(columns={group_col: "Group"})
    summary_df = summary_df[["Group", yr_start, yr_end, "Change", "Change %"]]

    return fig, summary_df
