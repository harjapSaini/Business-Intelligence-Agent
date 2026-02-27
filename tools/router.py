"""
Tool Router — dispatches LLM tool calls to the correct analysis function.
"""

import pandas as pd

from tools.yoy_comparison import yoy_comparison
from tools.brand_region_crosstab import brand_region_crosstab
from tools.forecast_trendline import forecast_trendline
from tools.anomaly_detection import anomaly_detection
from tools.price_volume_margin import price_volume_margin


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

    if tool_name == "yoy_comparison":
        fig, summary = yoy_comparison(
            df,
            metric=clean.get("metric", "sales"),
            division=clean.get("division"),
            region=clean.get("region"),
            category=clean.get("category"),
            brand=clean.get("brand"),
        )
        return fig, summary, None

    elif tool_name == "brand_region_crosstab":
        fig, summary = brand_region_crosstab(
            df,
            metric=clean.get("metric", "sales"),
        )
        return fig, summary, None

    elif tool_name == "forecast_trendline":
        fig, summary = forecast_trendline(
            df,
            group_by=clean.get("group_by", "division"),
            group_value=clean.get("group_value"),
            metric=clean.get("metric", "sales"),
        )
        return fig, summary, None

    elif tool_name == "anomaly_detection":
        fig, outlier_df, callouts = anomaly_detection(
            df,
            metric=clean.get("metric", "margin_rate"),
            division=clean.get("division"),
            region=clean.get("region"),
        )
        return fig, outlier_df, callouts

    elif tool_name == "price_volume_margin":
        fig, summary = price_volume_margin(
            df,
            division=clean.get("division"),
            category=clean.get("category"),
        )
        return fig, summary, None

    else:
        # Fallback to YoY comparison with defaults
        fig, summary = yoy_comparison(df, metric="sales")
        return fig, summary, None
