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
        return fig, summary, None

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
        fig, summary = forecast_trendline(
            df,
            group_by=clean.get("group_by", "division"),
            group_value=clean.get("group_value"),
            metric=clean.get("metric", "sales"),
            **common_filters,
        )
        return fig, summary, None

    elif tool_name == "anomaly_detection":
        fig, outlier_df, callouts = anomaly_detection(
            df,
            metric=clean.get("metric", "margin_rate"),
            **common_filters,
        )
        return fig, outlier_df, callouts

    elif tool_name == "price_volume_margin":
        fig, summary = price_volume_margin(
            df,
            **common_filters,
        )
        return fig, summary, None

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
        fig, summary = growth_margin_matrix(
            df,
            group_by=clean.get("group_by", "division"),
            **common_filters,
        )
        return fig, summary, None

    else:
        # Fallback to YoY comparison with defaults
        fig, summary = yoy_comparison(df, metric="sales", _is_dark_mode=is_dark)
        return fig, summary, None
