"""
Tool 5 - Price-Volume-Margin Analysis

Scatter/bubble analysis: x = avg selling price, y = margin rate,
bubble size = total units sold, colour = product category.
"""

import pandas as pd
import plotly.express as px

from config import CHART_COLORS


def price_volume_margin(
    df: pd.DataFrame,
    division: str = None,
    category: str = None,
    _is_dark_mode: bool = False,
) -> tuple:
    """
    Bubble chart of price vs margin rate, sized by units sold.

    Args:
        df:       Full DataFrame.
        division: Optional division filter.
        category: Optional category filter.

    Returns:
        (plotly.Figure, pd.DataFrame) - bubble chart + product summary.
    """
    filtered = df.copy()
    if division:
        filtered = filtered[filtered["PRODUCT_DIVISION"] == division]
    if category:
        filtered = filtered[filtered["PRODUCT_CATEGORY"] == category]

    # Product-level aggregation
    product_agg = (
        filtered.groupby(["PRODUCT_NAME", "PRODUCT_CATEGORY", "PRODUCT_DIVISION"])
        .agg(
            avg_price=("SELLING_PRICE_PER_UNIT", "mean"),
            total_units=("UNITS_SOLD", "sum"),
            total_sales=("SALES", "sum"),
            total_margin=("MARGIN", "sum"),
        )
        .reset_index()
    )
    product_agg["margin_rate"] = (
        product_agg["total_margin"] / product_agg["total_sales"]
    ).fillna(0)

    # Build chart
    title_suffix = ""
    if division:
        title_suffix += f" - {division}"
    if category:
        title_suffix += f" / {category}"

    fig = px.scatter(
        product_agg,
        x="avg_price",
        y="margin_rate",
        size="total_units",
        color="PRODUCT_CATEGORY",
        hover_name="PRODUCT_NAME",
        hover_data=["total_sales", "total_margin", "total_units"],
        title=f"Price vs Margin Rate{title_suffix}",
        labels={
            "avg_price": "Avg Selling Price ($)",
            "margin_rate": "Margin Rate",
            "total_units": "Units Sold",
        },
        color_discrete_sequence=CHART_COLORS,
    )
    fig.update_layout(
        template="plotly_dark" if _is_dark_mode else "plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_family="Inter, sans-serif",
        title_font_size=18,
    )

    return fig, product_agg
