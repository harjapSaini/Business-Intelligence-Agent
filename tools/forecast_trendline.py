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
    division: str = None,
    region: str = None,
    category: str = None,
    brand: str = None,
    _is_dark_mode: bool = False,
) -> tuple:
    """
    Build a monthly trendline with a 12-month linear forecast into 2025.

    Args:
        df:          Full DataFrame.
        group_by:    One of 'division', 'region', 'brand', 'category'.
        group_value: The specific value to filter on (e.g. 'Apparel').
        metric:      One of 'sales', 'margin', 'units', 'margin_rate'.
        division:    Optional pre-filter for PRODUCT_DIVISION.
        region:      Optional pre-filter for REGION.
        category:    Optional pre-filter for PRODUCT_CATEGORY.
        brand:       Optional pre-filter for BRAND.

    Returns:
        (plotly.Figure, pd.DataFrame, str) - trend chart, monthly data table,
        and a pre-computed insight string built from the regression output.
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

    # Apply context pre-filters before grouping
    filtered = df.copy()
    if division:
        filtered = filtered[filtered["PRODUCT_DIVISION"] == division]
    if region:
        filtered = filtered[filtered["REGION"] == region]
    if category:
        filtered = filtered[filtered["PRODUCT_CATEGORY"] == category]
    if brand:
        filtered = filtered[filtered["BRAND"] == brand]

    # Then apply the group_value filter (existing logic)
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

    # ── Pre-computed insight from actual regression values ──────────
    metric_label = metric.replace("_", " ").title()
    forecast_values = forecast_df[col].values
    projected_annual = float(forecast_values.sum())
    jan_2025 = float(forecast_values[0])
    dec_2025 = float(forecast_values[-1])
    monthly_growth = (dec_2025 - jan_2025) / jan_2025 * 100 if jan_2025 else 0.0

    # Reference: total of historical months in 2024
    hist_2024 = monthly.loc[monthly["YEAR"] == 2024, col]
    ref_annual = float(hist_2024.sum()) if not hist_2024.empty else 0.0

    # Build the insight string — plain text only, no markdown
    # Determine a human-readable scope label (e.g. "Sports division")
    scope_parts = []
    if division:
        scope_parts.append(f"{division} division")
    if region:
        scope_parts.append(f"{region} region")
    if category:
        scope_parts.append(f"{category} category")
    if brand:
        scope_parts.append(f"brand {brand}")
    if group_value and not scope_parts:
        scope_parts.append(group_value)
    scope_label = ", ".join(scope_parts) if scope_parts else "the business"

    def _fmt(v: float) -> str:
        """Format large numbers with $, commas, no decimals."""
        if metric == "margin_rate":
            return f"{v:.1f}%"
        return f"${v:,.0f}"

    insight_parts = [
        f"{scope_label.capitalize()} is projected to reach {_fmt(projected_annual)} "
        f"in total 2025 {metric_label.lower()}",
    ]
    if ref_annual:
        yoy_change = (projected_annual - ref_annual) / ref_annual * 100
        direction = "up" if yoy_change >= 0 else "down"
        insight_parts[0] += (
            f", {direction} {abs(yoy_change):.1f}% from {_fmt(ref_annual)} in 2024."
        )
    else:
        insight_parts[0] += "."
    insight_parts.append(
        f"Monthly {metric_label.lower()} forecast grows from {_fmt(jan_2025)} in January "
        f"to {_fmt(dec_2025)} by December 2025 (+{monthly_growth:.1f}% within-year growth)."
    )
    insight_parts.append(
        f"The 95% confidence band is +/-{_fmt(1.96 * std_err)}/month, "
        f"so actual results could vary around these projections."
    )
    pre_computed_insight = " ".join(insight_parts)

    # ── Build chart ──────────────────────────────────────────────
    # Build a clean filter label — avoid duplicates between division & group_value
    filter_parts = []
    if division:
        filter_parts.append(f"Division: {division}")
    if region:
        filter_parts.append(f"Region: {region}")
    if category:
        filter_parts.append(f"Category: {category}")
    if brand:
        filter_parts.append(f"Brand: {brand}")
    # Only add group_value when it isn't already covered by the named filters
    if group_value:
        already = (
            (group_by == "division" and division == group_value)
            or (group_by == "region" and region == group_value)
            or (group_by == "category" and category == group_value)
            or (group_by == "brand" and brand == group_value)
        )
        if not already:
            filter_parts.append(f"{group_by.title()}: {group_value}")
    title_text = f"Forecast - {metric_label}"
    if filter_parts:
        title_text += f" ({', '.join(filter_parts)})"
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
        title=title_text,
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

    return fig, summary_df, pre_computed_insight
