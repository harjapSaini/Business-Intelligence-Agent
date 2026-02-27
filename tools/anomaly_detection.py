"""
Tool 4 — Anomaly & Outlier Detection

Detects anomalous products using Z-score analysis on a chosen metric.
Flags outliers beyond ±2 standard deviations.
"""

import pandas as pd
import plotly.express as px

from config import ANOMALY_COLORS


def anomaly_detection(
    df: pd.DataFrame,
    metric: str = "margin_rate",
    division: str = None,
    region: str = None,
) -> tuple:
    """
    Detect anomalous products using Z-score analysis.

    Args:
        df:       Full DataFrame.
        metric:   One of 'sales', 'margin', 'margin_rate'.
        division: Optional division filter.
        region:   Optional region filter.

    Returns:
        (plotly.Figure, pd.DataFrame, list[str]) — scatter plot with
        outliers in red, outlier table, plain-English callout strings.
    """
    metric_col_map = {
        "sales": "SALES",
        "margin": "MARGIN",
        "margin_rate": "MARGIN_RATE",
    }
    col = metric_col_map.get(metric, "MARGIN_RATE")

    # Apply filters
    filtered = df.copy()
    if division:
        filtered = filtered[filtered["PRODUCT_DIVISION"] == division]
    if region:
        filtered = filtered[filtered["REGION"] == region]

    # Product-level aggregation
    if metric == "margin_rate":
        product_agg = (
            filtered.groupby(["PRODUCT_NAME", "PRODUCT_CATEGORY", "PRODUCT_DIVISION"])
            .agg(total_margin=("MARGIN", "sum"), total_sales=("SALES", "sum"),
                 avg_price=("SELLING_PRICE_PER_UNIT", "mean"), total_units=("UNITS_SOLD", "sum"))
            .reset_index()
        )
        product_agg[col] = (product_agg["total_margin"] / product_agg["total_sales"]).fillna(0)
    else:
        product_agg = (
            filtered.groupby(["PRODUCT_NAME", "PRODUCT_CATEGORY", "PRODUCT_DIVISION"])
            .agg(**{col: (col, "sum"),
                    "avg_price": ("SELLING_PRICE_PER_UNIT", "mean"),
                    "total_units": ("UNITS_SOLD", "sum")})
            .reset_index()
        )

    # Z-score calculation
    mean_val = product_agg[col].mean()
    std_val = product_agg[col].std()
    if std_val == 0:
        product_agg["z_score"] = 0.0
    else:
        product_agg["z_score"] = (product_agg[col] - mean_val) / std_val

    product_agg["is_outlier"] = product_agg["z_score"].abs() > 2
    product_agg["label"] = product_agg["is_outlier"].map({True: "Outlier", False: "Normal"})

    # Build chart
    metric_label = metric.replace("_", " ").title()
    fig = px.scatter(
        product_agg,
        x="PRODUCT_NAME",
        y=col,
        color="label",
        color_discrete_map=ANOMALY_COLORS,
        hover_data=["PRODUCT_CATEGORY", "PRODUCT_DIVISION", "z_score"],
        title=f"Anomaly Detection — {metric_label}",
        labels={col: metric_label},
    )
    fig.update_layout(
        template="plotly_white",
        xaxis_tickangle=-45,
        font_family="Inter, sans-serif",
        title_font_size=18,
    )

    # Outlier table
    outlier_df = product_agg[product_agg["is_outlier"]].sort_values(
        "z_score", key=abs, ascending=False
    )

    # Plain-English callout strings
    callouts = []
    for _, row in outlier_df.head(5).iterrows():
        direction = "unusually high" if row["z_score"] > 0 else "unusually low"
        callouts.append(
            f"**{row['PRODUCT_NAME']}** ({row['PRODUCT_CATEGORY']}) has {direction} "
            f"{metric_label.lower()} (z-score: {row['z_score']:.1f})."
        )
    if not callouts:
        callouts.append("No significant outliers detected in this data slice.")

    return fig, outlier_df, callouts
