"""
Tool 2 - Brand × Region Cross-Tab

Generates a brand performance chart filtered by region and/or brand.
Automatically switches between chart types:
  - Single region in filtered data → horizontal ranked bar chart
  - Multiple regions             → heatmap
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
    top_n: int = None,
    _is_dark_mode: bool = False,
) -> tuple:
    """
    Create a brand performance chart — bar chart for single region,
    heatmap for multiple regions.

    Args:
        df:       Full DataFrame (must have SALES, MARGIN, MARGIN_RATE, UNITS_SOLD cols).
        metric:   One of 'sales', 'margin', 'margin_rate', 'units'.
        division: Optional filter for PRODUCT_DIVISION.
        region:   Optional filter for REGION.
        category: Optional filter for PRODUCT_CATEGORY.
        brand:    Optional filter for BRAND.
        top_n:    Number of brands to show (default 10).
        _is_dark_mode: Current theme toggle.

    Returns:
        (plotly.Figure, pd.DataFrame) - chart + summary table.
    """
    if top_n is None:
        top_n = 10

    # ── Column mapping ──────────────────────────────────────
    metric_col_map = {
        "sales": "SALES",
        "margin": "MARGIN",
        "units": "UNITS_SOLD",
        "margin_rate": "MARGIN_RATE",
    }
    col = metric_col_map.get(metric, "SALES")

    metric_label_map = {
        "sales": "Sales ($)",
        "margin": "Margin ($)",
        "margin_rate": "Margin Rate (%)",
        "units": "Units Sold",
    }
    metric_label = metric_label_map.get(metric, metric.replace("_", " ").title())

    # ── Apply filters ───────────────────────────────────────
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

    # ── Common theme settings ───────────────────────────────
    template = "plotly_dark" if _is_dark_mode else "plotly_white"
    common_layout = dict(
        template=template,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_family="Inter, sans-serif",
        title_font_size=18,
    )

    # ── Decide chart type based on regions in filtered data ─
    regions_in_data = filtered["REGION"].nunique()

    if regions_in_data <= 1:
        # ═══ SINGLE REGION → horizontal bar chart, ranked best→worst ═══
        if metric == "margin_rate":
            grouped = (
                filtered.groupby("BRAND")
                .agg(total_margin=("MARGIN", "sum"), total_sales=("SALES", "sum"))
                .assign(Value=lambda x: (x["total_margin"] / x["total_sales"]).fillna(0))
                .drop(columns=["total_margin", "total_sales"])
                .sort_values("Value", ascending=False)
                .head(top_n)
                .reset_index()
            )
            grouped.columns = ["Brand", "Value"]
        else:
            grouped = (
                filtered.groupby("BRAND")[col]
                .sum()
                .sort_values(ascending=False)
                .head(top_n)
                .reset_index()
            )
            grouped.columns = ["Brand", "Value"]

        region_label = region if region else filtered["REGION"].iloc[0] if len(filtered) > 0 else "All Regions"
        filter_suffix = f" ({', '.join(active_filters)})" if active_filters else f" (Reg: {region_label})"

        fig = px.bar(
            grouped,
            x="Value",
            y="Brand",
            orientation="h",
            title=f"Top {top_n} Brands by {metric_label}{filter_suffix}",
            color="Value",
            color_continuous_scale="Teal",
            text="Value",
        )

        # Format text labels
        if metric == "margin_rate":
            fig.update_traces(texttemplate="%{text:.1%}", textposition="outside")
        elif metric == "units":
            fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        else:
            fig.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")

        fig.update_layout(
            yaxis={"categoryorder": "total ascending"},
            coloraxis_showscale=False,
            xaxis_title=metric_label,
            yaxis_title="Brand",
            **common_layout,
        )

        summary_df = grouped.copy()

    else:
        # ═══ MULTIPLE REGIONS → heatmap ════════════════════════
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

        # Rank brands by total across all regions, keep top_n
        pivot["_total"] = pivot.sum(axis=1)
        pivot = pivot.nlargest(top_n, "_total").drop(columns="_total")

        # Sort columns (regions) alphabetically for consistency
        pivot = pivot.reindex(sorted(pivot.columns), axis=1)

        summary_df = pivot.reset_index()

        title_text = f"Top {top_n} Brands × Region — {metric_label}"
        if active_filters:
            title_text += f" ({', '.join(active_filters)})"

        text_fmt = ".2%" if metric == "margin_rate" else ",.0f"

        fig = px.imshow(
            pivot.values,
            x=pivot.columns.tolist(),
            y=pivot.index.tolist(),
            labels={"x": "Region", "y": "Brand", "color": metric_label},
            title=title_text,
            color_continuous_scale=HEATMAP_SCALE,
            aspect="auto",
            text_auto=text_fmt,
        )
        fig.update_layout(
            xaxis_title="Region",
            yaxis_title="Brand",
            **common_layout,
        )

    return fig, summary_df
