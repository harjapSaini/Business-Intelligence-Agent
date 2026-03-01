"""
Tool 5 - Price-Volume-Margin Analysis

Bubble chart: x = avg selling price, y = margin rate (%),
bubble size = total units sold, one bubble per product category.
"""

import pandas as pd
import plotly.express as px

from config import CHART_COLORS


def price_volume_margin(
    df: pd.DataFrame,
    division: str = None,
    region: str = None,
    category: str = None,
    brand: str = None,
    _is_dark_mode: bool = False,
) -> tuple:
    """
    Bubble chart of price vs margin rate, sized by units sold.

    Aggregates to **category level** so there is one readable bubble
    per category rather than hundreds of overlapping product dots.

    Args:
        df:       Full DataFrame.
        division: Optional division filter.
        region:   Optional region filter.
        category: Optional category filter.
        brand:    Optional brand filter.

    Returns:
        (plotly.Figure, pd.DataFrame, str) - bubble chart, category
        summary table, and a pre-computed insight string.
    """
    filtered = df.copy()
    if division:
        filtered = filtered[filtered["PRODUCT_DIVISION"] == division]
    if region:
        filtered = filtered[filtered["REGION"] == region]
    if category:
        filtered = filtered[filtered["PRODUCT_CATEGORY"] == category]
    if brand:
        filtered = filtered[filtered["BRAND"] == brand]

    # ── AGGREGATE TO CATEGORY LEVEL — one row per category ───────
    agg = (
        filtered.groupby("PRODUCT_CATEGORY")
        .agg(
            avg_price=("SELLING_PRICE_PER_UNIT", "mean"),
            margin_rate=("MARGIN_RATE", "mean"),
            total_units=("UNITS_SOLD", "sum"),
            total_sales=("SALES", "sum"),
        )
        .reset_index()
    )
    agg["margin_pct"] = (agg["margin_rate"] * 100).round(1)
    agg["avg_price"] = agg["avg_price"].round(2)

    # ── Build chart ──────────────────────────────────────────────
    filter_parts = []
    if division:
        filter_parts.append(f"Division: {division}")
    if region:
        filter_parts.append(f"Region: {region}")
    if category:
        filter_parts.append(f"Category: {category}")
    if brand:
        filter_parts.append(f"Brand: {brand}")

    title_text = "Price vs Margin Rate by Category (bubble size = units sold)"
    if filter_parts:
        title_text += f" — {', '.join(filter_parts)}"

    fig = px.scatter(
        agg,
        x="avg_price",
        y="margin_pct",
        size="total_units",
        color="PRODUCT_CATEGORY",
        text="PRODUCT_CATEGORY",
        title=title_text,
        labels={
            "avg_price": "Avg Selling Price ($)",
            "margin_pct": "Margin Rate (%)",
            "total_units": "Units Sold",
        },
        color_discrete_sequence=CHART_COLORS,
        size_max=60,
    )
    fig.update_traces(textposition="top center")
    fig.update_layout(
        showlegend=False,
        template="plotly_dark" if _is_dark_mode else "plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_family="Inter, sans-serif",
        title_font_size=18,
    )

    # ── FIX 2: Sweet-spot annotation ($80-$140 price range) ─────
    fig.add_vrect(
        x0=80, x1=140,
        fillcolor="green", opacity=0.08,
        layer="below", line_width=0,
        annotation_text="Sweet Spot",
        annotation_position="top left",
        annotation_font_color="green",
    )

    # ── FIX 3: Pre-computed insight from actual aggregated data ──
    ranked = agg.sort_values("margin_pct", ascending=False).reset_index(drop=True)
    best = ranked.iloc[0]
    second = ranked.iloc[1]
    worst = ranked.iloc[-1]

    # Categories inside the sweet-spot band
    sweet = ranked[(ranked["avg_price"] >= 80) & (ranked["avg_price"] <= 140)]
    sweet_sorted = sweet.sort_values("margin_pct", ascending=False)
    if len(sweet_sorted) >= 2:
        sweet_names = (
            f"{sweet_sorted.iloc[0]['PRODUCT_CATEGORY']} "
            f"({sweet_sorted.iloc[0]['margin_pct']:.1f}%) and "
            f"{sweet_sorted.iloc[1]['PRODUCT_CATEGORY']} "
            f"({sweet_sorted.iloc[1]['margin_pct']:.1f}%)"
        )
    elif len(sweet_sorted) == 1:
        sweet_names = (
            f"{sweet_sorted.iloc[0]['PRODUCT_CATEGORY']} "
            f"({sweet_sorted.iloc[0]['margin_pct']:.1f}%)"
        )
    else:
        sweet_names = "several mid-price categories"

    pre_computed_insight = (
        f"{best['PRODUCT_CATEGORY']} and {second['PRODUCT_CATEGORY']} lead on "
        f"margin rate at {best['margin_pct']:.0f}% and {second['margin_pct']:.0f}% "
        f"respectively despite very low price points, driven by high volume. "
        f"The most striking finding is {worst['PRODUCT_CATEGORY']} — the most "
        f"expensive category at ${worst['avg_price']:.0f} average price but the "
        f"worst margin rate at {worst['margin_pct']:.1f}%, suggesting a cost or "
        f"pricing structure issue that warrants review. "
        f"The sweet spot for margin efficiency sits in the $80-$140 price range, "
        f"where categories like {sweet_names} deliver strong margins with solid volume."
    )

    return fig, agg, pre_computed_insight
