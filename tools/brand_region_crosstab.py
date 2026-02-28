"""
Tool 2 - Brand × Region Cross-Tab

Creates a heatmap of brands vs regions for a chosen metric.
"""

import pandas as pd
import plotly.express as px

from config import HEATMAP_SCALE


def brand_region_crosstab(
    df: pd.DataFrame,
    metric: str = "sales",
    division: str = None,
    region: str = None,
    category: str = None,
    brand: str = None,
    _is_dark_mode: bool = False,
) -> tuple:
    """
    Create a heatmap of brands vs regions for a chosen metric.

    Args:
        df:       Full DataFrame.
        metric:   One of 'sales', 'margin', 'margin_rate', 'units'.
        division: Optional filter for PRODUCT_DIVISION.
        region:   Optional filter for REGION.
        category: Optional filter for PRODUCT_CATEGORY.
        brand:    Optional filter for BRAND.

    Returns:
        (plotly.Figure, pd.DataFrame) - heatmap + pivot table.
    """
    # Apply filters before aggregation
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

    metric_col_map = {
        "sales": "SALES",
        "margin": "MARGIN",
        "units": "UNITS_SOLD",
        "margin_rate": "MARGIN_RATE",
    }
    col = metric_col_map.get(metric, "SALES")

    if metric == "margin_rate":
        agg = (
            filtered.groupby(["BRAND", "REGION"])
            .agg(total_margin=("MARGIN", "sum"), total_sales=("SALES", "sum"))
            .reset_index()
        )
        agg[col] = (agg["total_margin"] / agg["total_sales"]).fillna(0)
    else:
        agg = (
            filtered.groupby(["BRAND", "REGION"])[col]
            .sum()
            .reset_index()
        )

    pivot = agg.pivot(index="BRAND", columns="REGION", values=col).fillna(0)
    summary_df = pivot.reset_index()

    metric_label = metric.replace("_", " ").title()
    title_text = f"Brand × Region - {metric_label}"
    if active_filters:
        title_text += f" ({', '.join(active_filters)})"

    fig = px.imshow(
        pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        labels={"x": "Region", "y": "Brand", "color": metric_label},
        title=title_text,
        color_continuous_scale=HEATMAP_SCALE,
        aspect="auto",
    )
    fig.update_layout(
        template="plotly_dark" if _is_dark_mode else "plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_family="Inter, sans-serif",
        title_font_size=18,
    )

    return fig, summary_df
