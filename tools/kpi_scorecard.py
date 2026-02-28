"""
Tool 10 - KPI Scorecard / Executive Summary

Single-page business health check: a structured table showing every
division's Sales, YoY Growth %, Margin Rate, and a RAG status indicator.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from config import RAG_COLORS


def kpi_scorecard(
    df: pd.DataFrame,
    _is_dark_mode: bool = False,
) -> tuple:
    """
    Executive KPI scorecard across all divisions.

    No filters — this is always a full-business overview.

    Args:
        df:           Full DataFrame with KPI columns.
        _is_dark_mode: Dark-mode toggle for chart styling.

    Returns:
        (plotly.Figure, pd.DataFrame) - styled table + summary DataFrame.
    """
    # Aggregate by year + division
    div_agg = (
        df.groupby(["YEAR", "PRODUCT_DIVISION"])
        .agg(
            SALES=("SALES", "sum"),
            MARGIN=("MARGIN", "sum"),
            UNITS_SOLD=("UNITS_SOLD", "sum"),
        )
        .reset_index()
    )
    div_agg["MARGIN_RATE"] = (div_agg["MARGIN"] / div_agg["SALES"]).fillna(0)

    years = sorted(div_agg["YEAR"].unique().tolist())
    if len(years) < 2:
        yr_start, yr_end = years[0], years[0]
    else:
        yr_start, yr_end = years[0], years[-1]

    # Pivot per division
    divisions = sorted(div_agg["PRODUCT_DIVISION"].unique().tolist())
    records = []
    for div in divisions:
        d_start = div_agg[(div_agg["YEAR"] == yr_start) & (div_agg["PRODUCT_DIVISION"] == div)]
        d_end = div_agg[(div_agg["YEAR"] == yr_end) & (div_agg["PRODUCT_DIVISION"] == div)]

        s_start = d_start["SALES"].sum() if not d_start.empty else 0
        s_end = d_end["SALES"].sum() if not d_end.empty else 0
        m_start = d_start["MARGIN_RATE"].values[0] if not d_start.empty else 0
        m_end = d_end["MARGIN_RATE"].values[0] if not d_end.empty else 0
        u_end = d_end["UNITS_SOLD"].sum() if not d_end.empty else 0

        growth = ((s_end - s_start) / s_start * 100) if s_start > 0 else 0
        margin_change = (m_end - m_start) * 100  # in percentage points

        records.append({
            "Division": div,
            f"Sales_{yr_start}": s_start,
            f"Sales_{yr_end}": s_end,
            "YoY_Growth%": round(growth, 1),
            f"Margin_Rate_{yr_start}": round(m_start * 100, 1),
            f"Margin_Rate_{yr_end}": round(m_end * 100, 1),
            "Margin_Change_pp": round(margin_change, 1),
            f"Units_{yr_end}": u_end,
        })

    summary_df = pd.DataFrame(records)

    # Compute median margin rate for RAG threshold
    median_margin = summary_df[f"Margin_Rate_{yr_end}"].median()

    # Assign RAG status
    def assign_rag(row):
        if row["YoY_Growth%"] < 0 or row["Margin_Change_pp"] < -2:
            return "🔴"
        elif row["YoY_Growth%"] > 5 and row[f"Margin_Rate_{yr_end}"] > median_margin:
            return "🟢"
        else:
            return "🟡"

    summary_df["RAG"] = summary_df.apply(assign_rag, axis=1)

    # Add a Total row
    total_s_start = summary_df[f"Sales_{yr_start}"].sum()
    total_s_end = summary_df[f"Sales_{yr_end}"].sum()
    total_growth = ((total_s_end - total_s_start) / total_s_start * 100) if total_s_start > 0 else 0
    total_m_start = (div_agg[div_agg["YEAR"] == yr_start]["MARGIN"].sum() /
                     div_agg[div_agg["YEAR"] == yr_start]["SALES"].sum() * 100) if total_s_start > 0 else 0
    total_m_end = (div_agg[div_agg["YEAR"] == yr_end]["MARGIN"].sum() /
                   div_agg[div_agg["YEAR"] == yr_end]["SALES"].sum() * 100) if total_s_end > 0 else 0
    total_units = summary_df[f"Units_{yr_end}"].sum()

    total_row = pd.DataFrame([{
        "Division": "TOTAL",
        f"Sales_{yr_start}": total_s_start,
        f"Sales_{yr_end}": total_s_end,
        "YoY_Growth%": round(total_growth, 1),
        f"Margin_Rate_{yr_start}": round(total_m_start, 1),
        f"Margin_Rate_{yr_end}": round(total_m_end, 1),
        "Margin_Change_pp": round(total_m_end - total_m_start, 1),
        f"Units_{yr_end}": total_units,
        "RAG": "🟢" if total_growth > 5 else ("🔴" if total_growth < 0 else "🟡"),
    }])
    summary_df = pd.concat([summary_df, total_row], ignore_index=True)

    # Build Plotly Table
    # Colour cells by RAG status
    rag_col = summary_df["RAG"].tolist()
    rag_bg = []
    for r in rag_col:
        if "🟢" in r:
            rag_bg.append(RAG_COLORS["green"])
        elif "🔴" in r:
            rag_bg.append(RAG_COLORS["red"])
        else:
            rag_bg.append(RAG_COLORS["yellow"])

    # Format sales as currency strings
    def fmt_currency(vals):
        return [f"${v:,.0f}" for v in vals]

    def fmt_pct(vals):
        return [f"{v:+.1f}%" for v in vals]

    def fmt_rate(vals):
        return [f"{v:.1f}%" for v in vals]

    header_labels = [
        "Division",
        f"Sales {yr_start}", f"Sales {yr_end}",
        "YoY Growth",
        f"Margin% {yr_start}", f"Margin% {yr_end}",
        "Margin Chg",
        f"Units {yr_end}",
        "Status",
    ]

    text_color = "white" if _is_dark_mode else "#1a1a2e"
    header_bg = "#1a1a2e" if _is_dark_mode else "#1976D2"

    fig = go.Figure(data=[go.Table(
        header=dict(
            values=header_labels,
            fill_color=header_bg,
            font=dict(color="white", size=13, family="Inter, sans-serif"),
            align="center",
            height=35,
        ),
        cells=dict(
            values=[
                summary_df["Division"].tolist(),
                fmt_currency(summary_df[f"Sales_{yr_start}"]),
                fmt_currency(summary_df[f"Sales_{yr_end}"]),
                fmt_pct(summary_df["YoY_Growth%"]),
                fmt_rate(summary_df[f"Margin_Rate_{yr_start}"]),
                fmt_rate(summary_df[f"Margin_Rate_{yr_end}"]),
                fmt_pct(summary_df["Margin_Change_pp"]),
                [f"{v:,.0f}" for v in summary_df[f"Units_{yr_end}"]],
                rag_col,
            ],
            fill_color=[
                ["rgba(0,0,0,0)"] * len(summary_df),  # Division
                ["rgba(0,0,0,0)"] * len(summary_df),
                ["rgba(0,0,0,0)"] * len(summary_df),
                ["rgba(0,0,0,0)"] * len(summary_df),
                ["rgba(0,0,0,0)"] * len(summary_df),
                ["rgba(0,0,0,0)"] * len(summary_df),
                ["rgba(0,0,0,0)"] * len(summary_df),
                ["rgba(0,0,0,0)"] * len(summary_df),
                rag_bg,  # Status column gets RAG colours
            ],
            font=dict(color=text_color, size=12, family="Inter, sans-serif"),
            align=["left"] + ["right"] * 7 + ["center"],
            height=30,
        ),
    )])

    fig.update_layout(
        title="KPI Scorecard — Executive Summary",
        template="plotly_dark" if _is_dark_mode else "plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        font_family="Inter, sans-serif",
        title_font_size=18,
        height=max(350, 80 + 35 * len(summary_df)),
        margin=dict(l=20, r=20, t=60, b=20),
    )

    return fig, summary_df
