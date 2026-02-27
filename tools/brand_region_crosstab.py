"""
Tool 2 — Brand × Region Cross-Tab

Creates a heatmap of brands vs regions for a chosen metric.
"""

import pandas as pd
import plotly.express as px


def brand_region_crosstab(
    df: pd.DataFrame,
    metric: str = "sales",
) -> tuple:
    """
    Create a heatmap of brands vs regions for a chosen metric.

    Args:
        df:     Full DataFrame.
        metric: One of 'sales', 'margin', 'margin_rate', 'units'.

    Returns:
        (plotly.Figure, pd.DataFrame) — heatmap + pivot table.
    """
    metric_col_map = {
        "sales": "SALES",
        "margin": "MARGIN",
        "units": "UNITS_SOLD",
        "margin_rate": "MARGIN_RATE",
    }
    col = metric_col_map.get(metric, "SALES")

    if metric == "margin_rate":
        agg = (
            df.groupby(["BRAND", "REGION"])
            .agg(total_margin=("MARGIN", "sum"), total_sales=("SALES", "sum"))
            .reset_index()
        )
        agg[col] = (agg["total_margin"] / agg["total_sales"]).fillna(0)
    else:
        agg = (
            df.groupby(["BRAND", "REGION"])[col]
            .sum()
            .reset_index()
        )

    pivot = agg.pivot(index="BRAND", columns="REGION", values=col).fillna(0)
    summary_df = pivot.reset_index()

    metric_label = metric.replace("_", " ").title()
    fig = px.imshow(
        pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        labels={"x": "Region", "y": "Brand", "color": metric_label},
        title=f"Brand × Region — {metric_label}",
        color_continuous_scale="RdYlGn",
        aspect="auto",
    )
    fig.update_layout(template="plotly_white")

    return fig, summary_df
