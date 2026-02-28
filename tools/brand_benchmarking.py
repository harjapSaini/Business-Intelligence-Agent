"""
Tool 12 - Competitive Benchmarking Within Brands

100% stacked bar chart showing brand share within each category,
with margin-rate overlay — reveals which brands dominate which
categories and whether the dominant brand is also the most profitable.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config import CHART_COLORS


def brand_benchmarking(
    df: pd.DataFrame,
    metric: str = "sales",
    division: str = None,
    region: str = None,
    category: str = None,
    brand: str = None,
    _is_dark_mode: bool = False,
) -> tuple:
    """
    Brand share analysis within each product category.

    Args:
        df:       Full DataFrame with KPI columns.
        metric:   One of 'sales', 'margin', 'units'.
        division: Optional division filter.
        region:   Optional region filter.
        category: Optional category filter (drills into one category).
        brand:    Optional brand filter (highlights specific brand).

    Returns:
        (plotly.Figure, pd.DataFrame) - stacked bar + brand summary table.
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
        active_filters.append(f"Brand: {brand}")
        # Don't filter — we'll highlight instead

    # Aggregate: category × brand
    cat_brand = (
        filtered.groupby(["PRODUCT_CATEGORY", "BRAND"])
        .agg(
            metric_val=(col, "sum"),
            total_margin=("MARGIN", "sum"),
            total_sales=("SALES", "sum"),
        )
        .reset_index()
    )
    cat_brand["margin_rate"] = (
        cat_brand["total_margin"] / cat_brand["total_sales"]
    ).fillna(0)

    # Compute share % within each category
    cat_totals = cat_brand.groupby("PRODUCT_CATEGORY")["metric_val"].transform("sum")
    cat_brand["Share%"] = (cat_brand["metric_val"] / cat_totals * 100).round(1)

    metric_label = metric.replace("_", " ").title()
    filter_text = f" ({', '.join(active_filters)})" if active_filters else ""

    # Build 100% stacked bar chart
    fig = px.bar(
        cat_brand,
        x="PRODUCT_CATEGORY",
        y="metric_val",
        color="BRAND",
        barmode="relative",
        title=f"Brand Share by Category - {metric_label}{filter_text}",
        labels={
            "metric_val": metric_label,
            "PRODUCT_CATEGORY": "Category",
            "BRAND": "Brand",
        },
        color_discrete_sequence=CHART_COLORS,
    )

    # Normalise to 100%
    fig.update_layout(barnorm="percent", yaxis_title="Share %")

    # Add margin-rate overlay per category (weighted avg)
    cat_margin = (
        filtered.groupby("PRODUCT_CATEGORY")
        .agg(total_margin=("MARGIN", "sum"), total_sales=("SALES", "sum"))
        .reset_index()
    )
    cat_margin["margin_rate"] = (cat_margin["total_margin"] / cat_margin["total_sales"]).fillna(0)

    fig.add_trace(go.Scatter(
        x=cat_margin["PRODUCT_CATEGORY"],
        y=cat_margin["margin_rate"] * 100,  # scale to % for readability
        mode="lines+markers",
        name="Margin Rate %",
        yaxis="y2",
        line=dict(color="#FBC02D", width=2.5, dash="dot"),
        marker=dict(size=8, symbol="diamond"),
    ))

    fig.update_layout(
        yaxis2=dict(
            title="Margin Rate %",
            overlaying="y",
            side="right",
            showgrid=False,
            range=[0, 100],
        ),
        template="plotly_dark" if _is_dark_mode else "plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_family="Inter, sans-serif",
        title_font_size=18,
        xaxis_tickangle=-30,
        height=550,
        legend=dict(orientation="h", yanchor="bottom", y=-0.35),
    )

    # Summary table
    summary_df = (
        cat_brand[["PRODUCT_CATEGORY", "BRAND", "metric_val", "Share%", "margin_rate"]]
        .rename(columns={
            "PRODUCT_CATEGORY": "Category",
            "metric_val": metric_label,
            "margin_rate": "Margin_Rate",
        })
        .sort_values(["Category", metric_label], ascending=[True, False])
        .reset_index(drop=True)
    )

    return fig, summary_df
