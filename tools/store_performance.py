"""
Tool 6 - Store Performance Analysis

Analyses performance at the store level — bar chart of top/bottom stores
by a chosen metric, plus a scatter plot of store size vs performance
to reveal whether larger stores drive better results.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import CHART_COLORS


def store_performance(
    df: pd.DataFrame,
    metric: str = "sales",
    top_n: int = 10,
    view: str = "top",
    division: str = None,
    region: str = None,
    category: str = None,
    brand: str = None,
    _is_dark_mode: bool = False,
) -> tuple:
    """
    Analyse store-level performance.

    Args:
        df:       Full DataFrame with KPI columns.
        metric:   One of 'sales', 'margin', 'units', 'margin_rate'.
        top_n:    Number of stores to show (default 10).
        view:     'top' or 'bottom' performers.
        division: Optional division filter.
        region:   Optional region filter.
        category: Optional category filter.
        brand:    Optional brand filter.

    Returns:
        (plotly.Figure, pd.DataFrame) - dual chart + store summary table.
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

    # Store-level aggregation
    if metric == "margin_rate":
        store_agg = (
            filtered.groupby(["STORE_NAME", "STORE_SIZE"])
            .agg(total_margin=("MARGIN", "sum"), total_sales=("SALES", "sum"),
                 total_units=("UNITS_SOLD", "sum"))
            .reset_index()
        )
        store_agg["MARGIN_RATE"] = (
            store_agg["total_margin"] / store_agg["total_sales"]
        ).fillna(0)
        store_agg["SALES"] = store_agg["total_sales"]
        store_agg["MARGIN"] = store_agg["total_margin"]
        store_agg["UNITS_SOLD"] = store_agg["total_units"]
    else:
        store_agg = (
            filtered.groupby(["STORE_NAME", "STORE_SIZE"])
            .agg(
                SALES=("SALES", "sum"),
                MARGIN=("MARGIN", "sum"),
                UNITS_SOLD=("UNITS_SOLD", "sum"),
            )
            .reset_index()
        )
        store_agg["MARGIN_RATE"] = (
            store_agg["MARGIN"] / store_agg["SALES"]
        ).fillna(0)

    # Ensure STORE_SIZE is numeric for the scatter plot
    store_agg["STORE_SIZE_NUM"] = pd.to_numeric(store_agg["STORE_SIZE"], errors="coerce").fillna(0)

    # Sort and slice for bar chart
    ascending = view.lower() == "bottom"
    sorted_stores = store_agg.sort_values(col, ascending=ascending)
    top_stores = sorted_stores.head(int(top_n))

    # Build dual chart
    metric_label = metric.replace("_", " ").title()
    filter_text = f" ({', '.join(active_filters)})" if active_filters else ""
    view_label = "Bottom" if ascending else "Top"

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            f"{view_label} {top_n} Stores by {metric_label}",
            f"Store Size vs {metric_label}",
        ),
        column_widths=[0.55, 0.45],
        horizontal_spacing=0.12,
    )

    # Left: horizontal bar chart of top/bottom stores
    bar_stores = top_stores.sort_values(col, ascending=True)  # ascending for horizontal bar
    fig.add_trace(
        go.Bar(
            y=bar_stores["STORE_NAME"],
            x=bar_stores[col],
            orientation="h",
            marker_color=CHART_COLORS[0],
            name=metric_label,
            hovertemplate="%{y}<br>" + metric_label + ": %{x:,.0f}<extra></extra>",
        ),
        row=1, col=1,
    )

    # Right: scatter of store size vs metric with trendline
    fig.add_trace(
        go.Scatter(
            x=store_agg["STORE_SIZE_NUM"],
            y=store_agg[col],
            mode="markers",
            marker=dict(
                color=CHART_COLORS[1],
                size=8,
                opacity=0.7,
            ),
            text=store_agg["STORE_NAME"],
            hovertemplate="%{text}<br>Size: %{x}<br>" + metric_label + ": %{y:,.0f}<extra></extra>",
            name="Stores",
        ),
        row=1, col=2,
    )

    # Add numpy polyfit trendline
    valid = store_agg[store_agg["STORE_SIZE_NUM"] > 0]
    if len(valid) >= 2:
        coeffs = np.polyfit(valid["STORE_SIZE_NUM"], valid[col], 1)
        x_range = np.linspace(valid["STORE_SIZE_NUM"].min(), valid["STORE_SIZE_NUM"].max(), 50)
        y_trend = np.polyval(coeffs, x_range)
        corr = valid["STORE_SIZE_NUM"].corr(valid[col])
        fig.add_trace(
            go.Scatter(
                x=x_range,
                y=y_trend,
                mode="lines",
                line=dict(color=CHART_COLORS[2], width=2, dash="dash"),
                name=f"Trend (r={corr:.2f})",
            ),
            row=1, col=2,
        )

    fig.update_layout(
        title=f"Store Performance - {metric_label}{filter_text}",
        template="plotly_dark" if _is_dark_mode else "plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_family="Inter, sans-serif",
        title_font_size=18,
        showlegend=False,
        height=500,
    )
    fig.update_xaxes(title_text=metric_label, row=1, col=1)
    fig.update_xaxes(title_text="Store Size", row=1, col=2)
    fig.update_yaxes(title_text="", row=1, col=1)
    fig.update_yaxes(title_text=metric_label, row=1, col=2)

    # Summary DataFrame
    summary_df = store_agg[["STORE_NAME", "STORE_SIZE", "SALES", "MARGIN", "MARGIN_RATE", "UNITS_SOLD"]].copy()
    summary_df = summary_df.sort_values(col, ascending=ascending).reset_index(drop=True)

    return fig, summary_df
