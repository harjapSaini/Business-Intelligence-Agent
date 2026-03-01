"""
Tool Router - dispatches LLM tool calls to the correct analysis function.
"""

import pandas as pd

from tools.yoy_comparison import yoy_comparison
from tools.brand_region_crosstab import brand_region_crosstab
from tools.forecast_trendline import forecast_trendline
from tools.anomaly_detection import anomaly_detection
from tools.price_volume_margin import price_volume_margin
from tools.store_performance import store_performance
from tools.seasonality_trends import seasonality_trends
from tools.division_mix import division_mix
from tools.margin_waterfall import margin_waterfall
from tools.kpi_scorecard import kpi_scorecard
from tools.price_elasticity import price_elasticity
from tools.brand_benchmarking import brand_benchmarking
from tools.growth_margin_matrix import growth_margin_matrix


def _build_yoy_brand_insight(summary_df: pd.DataFrame, division: str, metric: str) -> str:
    """
    Build a pre-computed insight for brand-level YoY within a division.

    Uses the summary pivot table from yoy_comparison which has columns:
    BRAND, 2023, 2024, Change, Change %
    """
    if summary_df.empty or "Change %" not in summary_df.columns:
        return ""

    # Identify the group column (first column is the group)
    group_col = summary_df.columns[0]
    metric_label = metric.replace("_", " ").title()

    # Sort by Change % to find worst and best performers
    sorted_df = summary_df.sort_values("Change %", ascending=True)

    worst = sorted_df.head(3)
    best = sorted_df.tail(3).iloc[::-1]  # reverse to get best first

    parts = []

    # Worst performer lead
    w1 = worst.iloc[0]
    w1_name = w1[group_col]
    w1_pct = w1["Change %"]
    w1_abs = abs(w1["Change"])
    parts.append(
        f"{w1_name} is the primary driver of {division}'s decline, "
        f"falling {w1_pct:+.1f}% YoY and losing ${w1_abs:,.0f} in {metric_label.lower()}."
    )

    # 2nd and 3rd worst
    if len(worst) >= 3:
        w2 = worst.iloc[1]
        w3 = worst.iloc[2]
        combined_loss = abs(w2["Change"]) + abs(w3["Change"])
        parts.append(
            f"{w2[group_col]} ({w2['Change %']:+.1f}%) and "
            f"{w3[group_col]} ({w3['Change %']:+.1f}%) compound the problem "
            f"with combined losses of ${combined_loss:,.0f}."
        )

    # Best performers
    if len(best) >= 2:
        b1 = best.iloc[0]
        b2 = best.iloc[1]
        parts.append(
            f"{b1[group_col]} and {b2[group_col]} are bright spots at "
            f"{b1['Change %']:+.1f}% and {b2['Change %']:+.1f}% respectively, "
            f"proving the {division} category can grow with the right brands."
        )

    return " ".join(parts)


def _build_yoy_region_insight(summary_df: pd.DataFrame, full_df: pd.DataFrame, metric: str) -> str:
    """
    Build a pre-computed insight for region-level YoY comparison.

    Uses the summary pivot table from yoy_comparison (columns: REGION, 2023, 2024, Change, Change %)
    and drills into the full DataFrame to identify divisional drivers.
    """
    if summary_df.empty or "Change %" not in summary_df.columns:
        return ""

    group_col = summary_df.columns[0]
    sorted_df = summary_df.sort_values("Change %", ascending=False)

    parts = []

    # Best region
    best = sorted_df.iloc[0]
    best_name = best[group_col]
    best_pct = best["Change %"]
    best_abs = abs(best["Change"])
    parts.append(
        f"{best_name} is the fastest growing region at {best_pct:+.1f}% YoY, "
        f"adding ${best_abs:,.0f} in revenue"
    )

    # Drill into best region's divisional drivers
    metric_col_map = {"sales": "SALES", "margin": "MARGIN", "units": "UNITS_SOLD", "margin_rate": "MARGIN_RATE"}
    col = metric_col_map.get(metric, "SALES")
    region_data = full_df[full_df["REGION"] == best_name]
    if not region_data.empty:
        div_agg = (
            region_data.groupby(["YEAR", "PRODUCT_DIVISION"])[col]
            .sum()
            .reset_index()
        )
        div_pivot = div_agg.pivot(index="PRODUCT_DIVISION", columns="YEAR", values=col).fillna(0)
        if 2023 in div_pivot.columns and 2024 in div_pivot.columns:
            div_pivot["pct"] = ((div_pivot[2024] - div_pivot[2023]) / div_pivot[2023].replace(0, float("nan")) * 100).fillna(0)
            top_drivers = div_pivot.sort_values("pct", ascending=False).head(2)
            driver_strs = [f"{name} ({row['pct']:+.1f}%)" for name, row in top_drivers.iterrows()]
            if driver_strs:
                parts[-1] += f" driven primarily by {' and '.join(driver_strs)} in that region."
            else:
                parts[-1] += "."
        else:
            parts[-1] += "."
    else:
        parts[-1] += "."

    # Second best region (expansion opportunity if small)
    if len(sorted_df) >= 2:
        second = sorted_df.iloc[1]
        s_name = second[group_col]
        s_pct = second["Change %"]
        # Check if it's the smallest region by 2024 revenue
        if 2024 in summary_df.columns:
            smallest = summary_df.loc[summary_df[2024].idxmin(), group_col]
            if s_name == smallest:
                parts.append(
                    f"{s_name} shows strong momentum at {s_pct:+.1f}% despite being "
                    f"the smallest region, representing an expansion opportunity."
                )
            else:
                parts.append(f"{s_name} follows at {s_pct:+.1f}% YoY.")

    # Worst / declining region
    worst = sorted_df.iloc[-1]
    w_name = worst[group_col]
    w_pct = worst["Change %"]
    if w_pct < 0:
        # Find biggest divisional drag
        w_region_data = full_df[full_df["REGION"] == w_name]
        drag_str = ""
        if not w_region_data.empty:
            w_div_agg = (
                w_region_data.groupby(["YEAR", "PRODUCT_DIVISION"])[col]
                .sum()
                .reset_index()
            )
            w_div_pivot = w_div_agg.pivot(index="PRODUCT_DIVISION", columns="YEAR", values=col).fillna(0)
            if 2023 in w_div_pivot.columns and 2024 in w_div_pivot.columns:
                w_div_pivot["pct"] = ((w_div_pivot[2024] - w_div_pivot[2023]) / w_div_pivot[2023].replace(0, float("nan")) * 100).fillna(0)
                worst_div = w_div_pivot.sort_values("pct").iloc[0]
                drag_str = f", dragged down by {worst_div.name} ({worst_div['pct']:+.1f}%)"

        parts.append(
            f"{w_name} is the only declining region at {w_pct:+.1f}%{drag_str} "
            f"— a targeted divisional review for the {w_name} is recommended."
        )
    else:
        parts.append(f"All regions are growing, with {w_name} being the slowest at {w_pct:+.1f}%.")

    return " ".join(parts)


def tool_router(tool_name: str, filters: dict, df: pd.DataFrame) -> tuple:
    """
    Route a tool name + filters dict to the correct analysis function.

    Args:
        tool_name: One of 'yoy_comparison', 'brand_region_crosstab',
                   'forecast_trendline', 'anomaly_detection',
                   'price_volume_margin'.
        filters:   Dict of filter parameters (keys depend on the tool).
        df:        Full DataFrame with KPI columns.

    Returns:
        (plotly.Figure, pd.DataFrame, list[str] | None)
        The third element (callouts) is only present for anomaly_detection.
    """
    # Normalise None-string values from LLM
    clean = {}
    for k, v in filters.items():
        if v is None or (isinstance(v, str) and v.lower() in ("null", "none", "")):
            clean[k] = None
        else:
            clean[k] = v

    is_dark = clean.get("_is_dark_mode", False)

    # Common filter kwargs that every tool now accepts
    common_filters = {
        "division": clean.get("division"),
        "region": clean.get("region"),
        "category": clean.get("category"),
        "brand": clean.get("brand"),
        "_is_dark_mode": is_dark,
    }

    if tool_name == "yoy_comparison":
        fig, summary = yoy_comparison(
            df,
            group_by=clean.get("group_by", "division"),
            metric=clean.get("metric", "sales"),
            **common_filters,
        )

        # Pre-computed insight for brand-level YoY within a division
        pre_computed = None
        division_filter = clean.get("division")
        group_by_val = clean.get("group_by", "division")
        if division_filter and group_by_val == "brand" and not summary.empty:
            metric_name = clean.get("metric", "sales")
            pre_computed = _build_yoy_brand_insight(summary, division_filter, metric_name)
        elif group_by_val == "region" and not division_filter and not summary.empty:
            metric_name = clean.get("metric", "sales")
            pre_computed = _build_yoy_region_insight(summary, df, metric_name)

        return fig, summary, pre_computed

    elif tool_name == "brand_region_crosstab":
        top_n_val = clean.get("top_n")
        if top_n_val is not None:
            try:
                top_n_val = int(top_n_val)
            except (ValueError, TypeError):
                top_n_val = None
        fig, summary = brand_region_crosstab(
            df,
            metric=clean.get("metric", "sales"),
            top_n=top_n_val,
            **common_filters,
        )
        return fig, summary, None

    elif tool_name == "forecast_trendline":
        fig, summary, pre_computed = forecast_trendline(
            df,
            group_by=clean.get("group_by", "division"),
            group_value=clean.get("group_value"),
            metric=clean.get("metric", "sales"),
            **common_filters,
        )
        return fig, summary, pre_computed

    elif tool_name == "anomaly_detection":
        fig, outlier_df, callouts = anomaly_detection(
            df,
            metric=clean.get("metric", "margin_rate"),
            **common_filters,
        )
        return fig, outlier_df, callouts

    elif tool_name == "price_volume_margin":
        fig, summary, pre_computed = price_volume_margin(
            df,
            **common_filters,
        )
        return fig, summary, pre_computed

    elif tool_name == "store_performance":
        fig, summary = store_performance(
            df,
            metric=clean.get("metric", "sales"),
            top_n=int(clean.get("top_n", 10)),
            view=clean.get("view", "top"),
            **common_filters,
        )
        return fig, summary, None

    elif tool_name == "seasonality_trends":
        fig, summary = seasonality_trends(
            df,
            time_grain=clean.get("time_grain", "month"),
            metric=clean.get("metric", "sales"),
            **common_filters,
        )
        return fig, summary, None

    elif tool_name == "division_mix":
        fig, summary = division_mix(
            df,
            metric=clean.get("metric", "sales"),
            **common_filters,
        )
        return fig, summary, None

    elif tool_name == "margin_waterfall":
        fig, summary = margin_waterfall(
            df,
            metric=clean.get("metric", "margin"),
            group_by=clean.get("group_by", "division"),
            **common_filters,
        )
        return fig, summary, None

    elif tool_name == "kpi_scorecard":
        fig, summary = kpi_scorecard(
            df,
            _is_dark_mode=is_dark,
        )
        return fig, summary, None

    elif tool_name == "price_elasticity":
        fig, summary = price_elasticity(
            df,
            **common_filters,
        )
        return fig, summary, None

    elif tool_name == "brand_benchmarking":
        fig, summary = brand_benchmarking(
            df,
            metric=clean.get("metric", "sales"),
            **common_filters,
        )
        return fig, summary, None

    elif tool_name == "growth_margin_matrix":
        fig, summary, pre_computed_insight = growth_margin_matrix(
            df,
            group_by=clean.get("group_by", "division"),
            **common_filters,
        )
        return fig, summary, pre_computed_insight

    else:
        # Fallback to YoY comparison with defaults
        fig, summary = yoy_comparison(df, metric="sales", _is_dark_mode=is_dark)
        return fig, summary, None
