"""
Tool 13 - Growth-Margin Matrix (BCG-Style)

A 2×2 bubble chart plotting each division/category by YoY growth rate
(y-axis) vs margin rate (x-axis), with bubble size = total sales.
Quadrants: Stars, Cash Cows, Question Marks, Dogs.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from config import QUADRANT_COLORS


def growth_margin_matrix(
    df: pd.DataFrame,
    group_by: str = "division",
    division: str = None,
    region: str = None,
    category: str = None,
    brand: str = None,
    _is_dark_mode: bool = False,
) -> tuple:
    """
    BCG-style strategic matrix of growth vs margin.

    Args:
        df:       Full DataFrame with KPI columns.
        group_by: 'division' or 'category'.
        division: Optional division filter.
        region:   Optional region filter.
        category: Optional category filter.
        brand:    Optional brand filter.

    Returns:
        (plotly.Figure, pd.DataFrame) - bubble chart + quadrant summary table.
    """
    group_col_map = {
        "division": "PRODUCT_DIVISION",
        "category": "PRODUCT_CATEGORY",
    }
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
        filtered.groupby(["YEAR", group_col])
        .agg(
            SALES=("SALES", "sum"),
            MARGIN=("MARGIN", "sum"),
        )
        .reset_index()
    )
    agg["MARGIN_RATE"] = (agg["MARGIN"] / agg["SALES"]).fillna(0)

    years = sorted(agg["YEAR"].unique().tolist())
    if len(years) < 2:
        empty_fig = go.Figure()
        empty_fig.add_annotation(text="Need 2 years of data for growth-margin analysis",
                                 xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return empty_fig, pd.DataFrame()

    yr_start, yr_end = years[0], years[-1]

    # Build matrix data per group
    groups = agg[group_col].unique()
    matrix_records = []
    for grp in groups:
        d1 = agg[(agg[group_col] == grp) & (agg["YEAR"] == yr_start)]
        d2 = agg[(agg[group_col] == grp) & (agg["YEAR"] == yr_end)]
        if d1.empty or d2.empty:
            continue

        s1, s2 = d1["SALES"].values[0], d2["SALES"].values[0]
        mr2 = d2["MARGIN_RATE"].values[0] * 100  # as %

        growth = ((s2 - s1) / s1 * 100) if s1 > 0 else 0

        matrix_records.append({
            "Group": grp,
            f"Sales_{yr_end}": s2,
            "Margin_Rate": round(mr2, 1),
            "YoY_Growth%": round(growth, 1),
        })

    matrix_df = pd.DataFrame(matrix_records)
    if matrix_df.empty:
        empty_fig = go.Figure()
        empty_fig.add_annotation(text="Not enough data for matrix",
                                 xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return empty_fig, pd.DataFrame()

    # Quadrant thresholds (data-driven medians)
    med_growth = matrix_df["YoY_Growth%"].median()
    med_margin = matrix_df["Margin_Rate"].median()

    # Assign quadrant
    def assign_quadrant(row):
        high_growth = row["YoY_Growth%"] >= med_growth
        high_margin = row["Margin_Rate"] >= med_margin
        if high_growth and high_margin:
            return "Stars"
        elif not high_growth and high_margin:
            return "Cash Cows"
        elif high_growth and not high_margin:
            return "Question Marks"
        else:
            return "Dogs"

    matrix_df["Quadrant"] = matrix_df.apply(assign_quadrant, axis=1)

    # Build bubble chart
    filter_text = f" ({', '.join(active_filters)})" if active_filters else ""

    fig = go.Figure()

    for quadrant, color in QUADRANT_COLORS.items():
        q_data = matrix_df[matrix_df["Quadrant"] == quadrant]
        if q_data.empty:
            continue
        # Scale bubble sizes for readability
        max_sales = matrix_df[f"Sales_{yr_end}"].max()
        sizes = (q_data[f"Sales_{yr_end}"] / max_sales * 60).clip(lower=10)

        fig.add_trace(go.Scatter(
            x=q_data["Margin_Rate"],
            y=q_data["YoY_Growth%"],
            mode="markers+text",
            marker=dict(
                size=sizes,
                color=color,
                opacity=0.75,
                line=dict(width=1, color="white"),
            ),
            text=q_data["Group"],
            textposition="top center",
            textfont=dict(size=10),
            name=quadrant,
            hovertemplate=(
                "%{text}<br>"
                "Margin Rate: %{x:.1f}%<br>"
                "YoY Growth: %{y:.1f}%<br>"
                "<extra></extra>"
            ),
        ))

    # Quadrant lines
    fig.add_hline(y=med_growth, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=med_margin, line_dash="dash", line_color="gray", opacity=0.5)

    # Quadrant labels in corners
    annotations = [
        dict(x=0.98, y=0.98, text="⭐ STARS", font=dict(color=QUADRANT_COLORS["Stars"], size=13)),
        dict(x=0.02, y=0.98, text="❓ QUESTION MARKS", font=dict(color=QUADRANT_COLORS["Question Marks"], size=13)),
        dict(x=0.98, y=0.02, text="🐄 CASH COWS", font=dict(color=QUADRANT_COLORS["Cash Cows"], size=13)),
        dict(x=0.02, y=0.02, text="🐕 DOGS", font=dict(color=QUADRANT_COLORS["Dogs"], size=13)),
    ]
    for ann in annotations:
        fig.add_annotation(
            xref="paper", yref="paper",
            x=ann["x"], y=ann["y"],
            text=ann["text"],
            font=ann["font"],
            showarrow=False,
            xanchor="right" if ann["x"] > 0.5 else "left",
            yanchor="top" if ann["y"] > 0.5 else "bottom",
        )

    fig.update_layout(
        title=f"Growth-Margin Matrix ({group_by.title()}){filter_text}",
        xaxis_title="Margin Rate %",
        yaxis_title="YoY Growth %",
        template="plotly_dark" if _is_dark_mode else "plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_family="Inter, sans-serif",
        title_font_size=18,
        height=550,
        legend_title_text="Quadrant",
    )

    # Summary table
    summary_df = matrix_df[["Group", f"Sales_{yr_end}", "Margin_Rate", "YoY_Growth%", "Quadrant"]]
    summary_df = summary_df.sort_values("Quadrant").reset_index(drop=True)

    return fig, summary_df
