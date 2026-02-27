"""
Tool 3 - Forecast / Trendlines

Builds a monthly trendline with a 12-month linear forecast into 2025
using sklearn LinearRegression.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression

from config import FORECAST_HISTORICAL, FORECAST_PREDICTED, FORECAST_CONFIDENCE


def forecast_trendline(
    df: pd.DataFrame,
    group_by: str = "division",
    group_value: str = None,
    metric: str = "sales",
    _is_dark_mode: bool = False,
) -> tuple:
    """
    Build a monthly trendline with a 12-month linear forecast into 2025.

    Args:
        df:          Full DataFrame.
        group_by:    One of 'division', 'region', 'brand', 'category'.
        group_value: The specific value to filter on (e.g. 'Apparel').
        metric:      One of 'sales', 'margin', 'units', 'margin_rate'.

    Returns:
        (plotly.Figure, pd.DataFrame) - trend chart + monthly data table.
    """
    group_col_map = {
        "division": "PRODUCT_DIVISION",
        "region": "REGION",
        "brand": "BRAND",
        "category": "PRODUCT_CATEGORY",
    }
    metric_col_map = {
        "sales": "SALES",
        "margin": "MARGIN",
        "units": "UNITS_SOLD",
        "margin_rate": "MARGIN_RATE",
    }

    group_col = group_col_map.get(group_by, "PRODUCT_DIVISION")
    col = metric_col_map.get(metric, "SALES")

    # Filter to the selected group
    filtered = df.copy()
    if group_value:
        filtered = filtered[filtered[group_col] == group_value]

    # Monthly aggregation
    if metric == "margin_rate":
        monthly = (
            filtered.groupby(["YEAR", "MONTH"])
            .agg(total_margin=("MARGIN", "sum"), total_sales=("SALES", "sum"))
            .reset_index()
        )
        monthly[col] = (monthly["total_margin"] / monthly["total_sales"]).fillna(0)
    else:
        monthly = (
            filtered.groupby(["YEAR", "MONTH"])[col]
            .sum()
            .reset_index()
        )

    # Create a sequential month index for regression
    monthly = monthly.sort_values(["YEAR", "MONTH"]).reset_index(drop=True)
    monthly["month_idx"] = range(len(monthly))

    # Create proper date column for charting
    monthly["DATE"] = pd.to_datetime(
        monthly["YEAR"].astype(int).astype(str) + "-" +
        monthly["MONTH"].astype(int).astype(str) + "-01"
    )

    # Fit linear regression
    X = monthly[["month_idx"]].values
    y = monthly[col].values
    model = LinearRegression().fit(X, y)

    # Forecast 12 months into 2025
    last_idx = monthly["month_idx"].max()
    last_date = monthly["DATE"].max()
    forecast_months = []
    for i in range(1, 13):
        future_date = last_date + pd.DateOffset(months=i)
        forecast_months.append({
            "month_idx": last_idx + i,
            "DATE": future_date,
            "YEAR": future_date.year,
            "MONTH": future_date.month,
        })
    forecast_df = pd.DataFrame(forecast_months)

    # Predict
    forecast_X = forecast_df[["month_idx"]].values
    forecast_df[col] = model.predict(forecast_X)

    # Confidence band (using residual std error)
    residuals = y - model.predict(X)
    std_err = np.std(residuals)
    forecast_df["upper"] = forecast_df[col] + 1.96 * std_err
    forecast_df["lower"] = forecast_df[col] - 1.96 * std_err

    # Build chart
    metric_label = metric.replace("_", " ").title()
    title_suffix = f" - {group_value}" if group_value else ""
    fig = go.Figure()

    # Historical line
    fig.add_trace(go.Scatter(
        x=monthly["DATE"], y=monthly[col],
        mode="lines+markers", name="Historical",
        line=dict(color=FORECAST_HISTORICAL, width=2),
    ))

    # Forecast line (dotted)
    fig.add_trace(go.Scatter(
        x=forecast_df["DATE"], y=forecast_df[col],
        mode="lines+markers", name="Forecast",
        line=dict(color=FORECAST_PREDICTED, width=2, dash="dot"),
    ))

    # Confidence shading
    fig.add_trace(go.Scatter(
        x=pd.concat([forecast_df["DATE"], forecast_df["DATE"][::-1]]),
        y=pd.concat([forecast_df["upper"], forecast_df["lower"][::-1]]),
        fill="toself", fillcolor=FORECAST_CONFIDENCE,
        line=dict(color="rgba(255,255,255,0)"),
        showlegend=False, name="Confidence",
    ))

    fig.update_layout(
        title=f"Forecast - {metric_label}{title_suffix}",
        xaxis_title="Date",
        yaxis_title=metric_label,
        template="plotly_dark" if _is_dark_mode else "plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_family="Inter, sans-serif",
        title_font_size=18,
    )

    # Combine for summary table
    monthly["type"] = "historical"
    forecast_df["type"] = "forecast"
    common_cols = ["DATE", "YEAR", "MONTH", col, "type"]
    summary_df = pd.concat(
        [monthly[common_cols], forecast_df[common_cols]],
        ignore_index=True,
    )

    return fig, summary_df
