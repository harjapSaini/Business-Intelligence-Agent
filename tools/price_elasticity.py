"""
Tool 11 - Price Elasticity Estimator

Estimates how sensitive demand is to price changes per category using
YoY arc elasticity and cross-sectional log-log regression.  Produces
a bar chart of elasticity coefficients and a scenario table.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.linear_model import LinearRegression

from config import CHART_COLORS


def price_elasticity(
    df: pd.DataFrame,
    division: str = None,
    region: str = None,
    category: str = None,
    brand: str = None,
    _is_dark_mode: bool = False,
) -> tuple:
    """
    Estimate price elasticity per category and project impact scenarios.

    Args:
        df:       Full DataFrame with KPI columns.
        division: Optional division filter.
        region:   Optional region filter.
        category: Optional category filter (drills to product level).
        brand:    Optional brand filter.

    Returns:
        (plotly.Figure, pd.DataFrame) - elasticity chart + scenario table.
    """
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

    # Decide granularity: if category filter is active, drill to product
    group_col = "PRODUCT_NAME" if category else "PRODUCT_CATEGORY"
    group_label = "Product" if category else "Category"

    # Aggregate per year per group
    yearly = (
        filtered.groupby(["YEAR", group_col])
        .agg(
            avg_price=("SELLING_PRICE_PER_UNIT", "mean"),
            total_units=("UNITS_SOLD", "sum"),
            total_sales=("SALES", "sum"),
            total_margin=("MARGIN", "sum"),
        )
        .reset_index()
    )

    years = sorted(yearly["YEAR"].unique().tolist())
    if len(years) < 2:
        # Cannot compute elasticity with only one year
        empty_fig = go.Figure()
        empty_fig.add_annotation(text="Need 2 years of data to estimate elasticity",
                                 xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return empty_fig, pd.DataFrame()

    yr_start, yr_end = years[0], years[-1]

    # Arc elasticity: Ed = (%ΔQ / %ΔP)
    groups = yearly[group_col].unique()
    elasticity_records = []
    for grp in groups:
        d1 = yearly[(yearly[group_col] == grp) & (yearly["YEAR"] == yr_start)]
        d2 = yearly[(yearly[group_col] == grp) & (yearly["YEAR"] == yr_end)]
        if d1.empty or d2.empty:
            continue

        p1, p2 = d1["avg_price"].values[0], d2["avg_price"].values[0]
        q1, q2 = d1["total_units"].values[0], d2["total_units"].values[0]
        s2 = d2["total_sales"].values[0]
        m2 = d2["total_margin"].values[0]

        pct_dp = (p2 - p1) / p1 * 100 if p1 > 0 else 0
        pct_dq = (q2 - q1) / q1 * 100 if q1 > 0 else 0
        elasticity = pct_dq / pct_dp if abs(pct_dp) > 0.5 else 0  # avoid noise

        elasticity_records.append({
            group_label: grp,
            "Elasticity": round(elasticity, 2),
            "Price_Change%": round(pct_dp, 1),
            "Units_Change%": round(pct_dq, 1),
            f"Sales_{yr_end}": s2,
            f"Margin_{yr_end}": m2,
            f"Avg_Price_{yr_end}": round(p2, 2),
        })

    if not elasticity_records:
        empty_fig = go.Figure()
        empty_fig.add_annotation(text="Not enough data for elasticity estimation",
                                 xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return empty_fig, pd.DataFrame()

    elas_df = pd.DataFrame(elasticity_records).sort_values("Elasticity")

    # Cross-sectional log-log regression as validation
    # (across all products pooled, not per-group)
    product_agg = (
        filtered.groupby("PRODUCT_NAME")
        .agg(avg_price=("SELLING_PRICE_PER_UNIT", "mean"),
             total_units=("UNITS_SOLD", "sum"))
        .reset_index()
    )
    product_agg = product_agg[(product_agg["avg_price"] > 0) & (product_agg["total_units"] > 0)]
    cross_elasticity = None
    if len(product_agg) >= 5:
        X_log = np.log(product_agg["avg_price"].values).reshape(-1, 1)
        y_log = np.log(product_agg["total_units"].values)
        model = LinearRegression().fit(X_log, y_log)
        cross_elasticity = round(model.coef_[0], 2)

    # Build scenario table — ±5%, ±10%, ±15% price changes
    scenario_rows = []
    for _, row in elas_df.iterrows():
        for pct in [-15, -10, -5, 5, 10, 15]:
            e = row["Elasticity"]
            projected_unit_chg = e * pct  # % change in units
            base_sales = row[f"Sales_{yr_end}"]
            base_margin = row[f"Margin_{yr_end}"]
            # Revenue impact: (1 + price_chg%) * (1 + unit_chg%) - 1
            revenue_multiplier = (1 + pct / 100) * (1 + projected_unit_chg / 100)
            revenue_impact = (revenue_multiplier - 1) * 100

            scenario_rows.append({
                group_label: row[group_label],
                "Elasticity": row["Elasticity"],
                "Price_Change%": pct,
                "Projected_Units_Change%": round(projected_unit_chg, 1),
                "Revenue_Impact%": round(revenue_impact, 1),
                "Projected_Revenue": round(base_sales * revenue_multiplier),
            })
    scenario_df = pd.DataFrame(scenario_rows)

    # Build chart: bar chart of elasticity coefficients
    filter_text = f" ({', '.join(active_filters)})" if active_filters else ""

    colors = [
        "#D32F2F" if abs(e) > 1.5 else ("#F57C00" if abs(e) > 0.8 else "#2E7D32")
        for e in elas_df["Elasticity"]
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=elas_df[group_label],
        y=elas_df["Elasticity"],
        marker_color=colors,
        hovertemplate="%{x}<br>Elasticity: %{y:.2f}<extra></extra>",
    ))

    # Add zero line and elastic/inelastic zones
    fig.add_hline(y=-1, line_dash="dash", line_color="gray",
                  annotation_text="Unit Elastic (-1)", annotation_position="bottom right")
    fig.add_hline(y=0, line_color="gray", line_width=0.5)

    if cross_elasticity is not None:
        fig.add_annotation(
            text=f"Cross-sectional elasticity (log-log): {cross_elasticity}",
            xref="paper", yref="paper", x=1, y=1.05,
            showarrow=False, font=dict(size=11, color="gray"),
        )

    fig.update_layout(
        title=f"Price Elasticity by {group_label}{filter_text}",
        yaxis_title="Elasticity Coefficient (Ed)",
        xaxis_title=group_label,
        template="plotly_dark" if _is_dark_mode else "plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_family="Inter, sans-serif",
        title_font_size=18,
        showlegend=False,
        xaxis_tickangle=-30,
        height=500,
    )

    return fig, scenario_df
