"""
Insight Builder - generates compact data summaries for each tool's output.

Each function takes the result DataFrame (and optional extras like callouts)
and returns a plain-text summary string that gets fed to the LLM's
second pass so it can write data-grounded business insights.
"""

import pandas as pd
import numpy as np


def summarize_yoy(result_df: pd.DataFrame, metric: str = "sales") -> str:
    """
    Summarize YoY comparison results.

    Extracts top/bottom growers, percentage changes, and total values
    so the LLM can reference actual numbers in its insight.
    """
    if result_df is None or result_df.empty:
        return "No year-over-year data available."

    lines = []
    group_col = result_df.columns[0]  # first column is the grouping axis

    # Check if we have Change % column
    if "Change %" in result_df.columns and "Change" in result_df.columns:
        # Sort by Change % to find top and bottom growers
        sorted_df = result_df.sort_values("Change %", ascending=False)

        # Top grower
        top = sorted_df.iloc[0]
        lines.append(
            f"Strongest growth: {top[group_col]} at {top['Change %']:+.1f}% "
            f"(change of {top['Change']:+,.0f})"
        )

        # Bottom grower
        bottom = sorted_df.iloc[-1]
        lines.append(
            f"Weakest performance: {bottom[group_col]} at {bottom['Change %']:+.1f}% "
            f"(change of {bottom['Change']:+,.0f})"
        )

        # List all items with their values
        lines.append(f"\nAll {group_col.replace('_', ' ').lower()} results:")
        for _, row in sorted_df.iterrows():
            yr_2023 = row.get(2023, row.get("2023", 0))
            yr_2024 = row.get(2024, row.get("2024", 0))
            lines.append(
                f"  - {row[group_col]}: 2023=${yr_2023:,.0f}, 2024=${yr_2024:,.0f}, "
                f"change={row['Change %']:+.1f}%"
            )
    else:
        # No change columns, just list values
        lines.append(f"Results by {group_col.replace('_', ' ').lower()}:")
        for _, row in result_df.iterrows():
            vals = [f"{col}={row[col]:,.0f}" for col in result_df.columns[1:]
                    if pd.notna(row[col])]
            lines.append(f"  - {row[group_col]}: {', '.join(vals)}")

    return "\n".join(lines)


def summarize_crosstab(result_df: pd.DataFrame, metric: str = "sales") -> str:
    """
    Summarize Brand x Region crosstab results.

    Finds the top brands, strongest regions, and notable patterns.
    """
    if result_df is None or result_df.empty:
        return "No cross-tab data available."

    lines = []
    brand_col = result_df.columns[0]  # should be BRAND
    region_cols = [c for c in result_df.columns if c != brand_col]

    # Add totals per brand
    result_copy = result_df.copy()
    result_copy["Total"] = result_copy[region_cols].sum(axis=1)
    result_copy = result_copy.sort_values("Total", ascending=False)

    # Top 5 brands
    lines.append("Top 5 brands by total across all regions:")
    for _, row in result_copy.head(5).iterrows():
        lines.append(f"  - {row[brand_col]}: ${row['Total']:,.0f}")
        # Find their best region
        best_region = max(region_cols, key=lambda r: row[r])
        lines.append(f"    Best region: {best_region} (${row[best_region]:,.0f})")

    # Weakest brands
    lines.append("\nBottom 3 brands:")
    for _, row in result_copy.tail(3).iterrows():
        lines.append(f"  - {row[brand_col]}: ${row['Total']:,.0f}")

    # Regional totals
    lines.append("\nRegional totals:")
    for region in region_cols:
        total = result_df[region].sum()
        lines.append(f"  - {region}: ${total:,.0f}")

    return "\n".join(lines)


def summarize_forecast(result_df: pd.DataFrame, metric: str = "sales") -> str:
    """
    Summarize forecast trendline results.

    Shows the current trajectory, predicted end-of-forecast value,
    and projected growth rate.
    """
    if result_df is None or result_df.empty:
        return "No forecast data available."

    lines = []
    metric_col = None
    # Find the metric column (not DATE, YEAR, MONTH, type)
    skip_cols = {"DATE", "YEAR", "MONTH", "type", "month_idx"}
    for col in result_df.columns:
        if col not in skip_cols:
            metric_col = col
            break

    if metric_col is None:
        return "Could not identify the metric column in forecast data."

    # Split historical vs forecast
    hist = result_df[result_df["type"] == "historical"]
    forecast = result_df[result_df["type"] == "forecast"]

    if not hist.empty:
        # Recent historical values
        recent = hist.tail(3)
        lines.append("Recent historical monthly values:")
        for _, row in recent.iterrows():
            date_str = str(row["DATE"])[:7] if pd.notna(row["DATE"]) else "Unknown"
            lines.append(f"  - {date_str}: ${row[metric_col]:,.0f}")

        # Overall historical stats
        lines.append(f"\nHistorical average: ${hist[metric_col].mean():,.0f}")
        lines.append(f"Historical range: ${hist[metric_col].min():,.0f} to ${hist[metric_col].max():,.0f}")

    if not forecast.empty:
        lines.append(f"\nForecasted values (next 12 months):")
        first_forecast = forecast.iloc[0]
        last_forecast = forecast.iloc[-1]
        lines.append(f"  - Start: ${first_forecast[metric_col]:,.0f}")
        lines.append(f"  - End (12 months out): ${last_forecast[metric_col]:,.0f}")

        # Calculate projected growth
        if not hist.empty:
            last_hist = hist[metric_col].iloc[-1]
            if last_hist != 0:
                projected_change = ((last_forecast[metric_col] - last_hist) / last_hist) * 100
                lines.append(f"  - Projected growth from latest actual: {projected_change:+.1f}%")

    return "\n".join(lines)


def summarize_anomalies(
    result_df: pd.DataFrame,
    callouts: list,
    metric: str = "margin_rate",
) -> str:
    """
    Summarize anomaly detection results.

    Lists outlier count, most extreme outliers, and their z-scores.
    """
    if result_df is None or result_df.empty:
        return "No anomalies detected in this data slice."

    lines = []
    lines.append(f"Total outliers flagged: {len(result_df)}")

    if callouts:
        lines.append("\nKey outliers:")
        for c in callouts[:5]:
            lines.append(f"  - {c}")

    # Additional stats
    if "z_score" in result_df.columns:
        high_outliers = result_df[result_df["z_score"] > 0]
        low_outliers = result_df[result_df["z_score"] < 0]
        lines.append(f"\nOutliers above average: {len(high_outliers)}")
        lines.append(f"Outliers below average: {len(low_outliers)}")

    # Show top outlier details
    if not result_df.empty and "PRODUCT_NAME" in result_df.columns:
        lines.append("\nMost extreme outliers:")
        for _, row in result_df.head(3).iterrows():
            name = row.get("PRODUCT_NAME", "Unknown")
            cat = row.get("PRODUCT_CATEGORY", "")
            z = row.get("z_score", 0)
            direction = "above" if z > 0 else "below"
            lines.append(f"  - {name} ({cat}): {abs(z):.1f} std devs {direction} average")

    return "\n".join(lines)


def summarize_price_volume(result_df: pd.DataFrame) -> str:
    """
    Summarize price-volume-margin results.

    Identifies pricing sweet spots, highest margin products,
    and volume leaders.
    """
    if result_df is None or result_df.empty:
        return "No price-volume data available."

    lines = []

    # Overall stats
    lines.append(f"Total products analyzed: {len(result_df)}")
    lines.append(f"Price range: ${result_df['avg_price'].min():.2f} to ${result_df['avg_price'].max():.2f}")
    lines.append(f"Average margin rate: {result_df['margin_rate'].mean():.1%}")

    # Highest margin product
    best_margin = result_df.loc[result_df["margin_rate"].idxmax()]
    lines.append(
        f"\nHighest margin: {best_margin['PRODUCT_NAME']} "
        f"(margin rate: {best_margin['margin_rate']:.1%}, "
        f"price: ${best_margin['avg_price']:.2f})"
    )

    # Lowest margin product
    worst_margin = result_df.loc[result_df["margin_rate"].idxmin()]
    lines.append(
        f"Lowest margin: {worst_margin['PRODUCT_NAME']} "
        f"(margin rate: {worst_margin['margin_rate']:.1%}, "
        f"price: ${worst_margin['avg_price']:.2f})"
    )

    # Highest volume product
    top_volume = result_df.loc[result_df["total_units"].idxmax()]
    lines.append(
        f"\nVolume leader: {top_volume['PRODUCT_NAME']} "
        f"({top_volume['total_units']:,.0f} units, "
        f"price: ${top_volume['avg_price']:.2f}, "
        f"margin: {top_volume['margin_rate']:.1%})"
    )

    # Revenue leader
    top_revenue = result_df.loc[result_df["total_sales"].idxmax()]
    lines.append(
        f"Revenue leader: {top_revenue['PRODUCT_NAME']} "
        f"(${top_revenue['total_sales']:,.0f} in sales)"
    )

    # Sweet spot analysis - products with above-average margin AND above-average volume
    avg_margin = result_df["margin_rate"].mean()
    avg_units = result_df["total_units"].mean()
    sweet_spot = result_df[
        (result_df["margin_rate"] > avg_margin) &
        (result_df["total_units"] > avg_units)
    ]
    if not sweet_spot.empty:
        lines.append(f"\nSweet spot products (above-avg margin AND volume): {len(sweet_spot)}")
        for _, row in sweet_spot.head(3).iterrows():
            lines.append(
                f"  - {row['PRODUCT_NAME']}: margin {row['margin_rate']:.1%}, "
                f"{row['total_units']:,.0f} units, ${row['avg_price']:.2f}"
            )

    return "\n".join(lines)


def build_data_summary(tool_name: str, result_df, callouts=None, metric="sales") -> str:
    """
    Route to the correct summarizer based on tool name.

    Args:
        tool_name:  Name of the tool that produced the results.
        result_df:  The pandas DataFrame returned by the tool.
        callouts:   Optional list of callout strings (for anomaly_detection).
        metric:     The metric used in the analysis.

    Returns:
        str - compact data summary for the LLM's second pass.
    """
    if tool_name == "yoy_comparison":
        return summarize_yoy(result_df, metric)
    elif tool_name == "brand_region_crosstab":
        return summarize_crosstab(result_df, metric)
    elif tool_name == "forecast_trendline":
        return summarize_forecast(result_df, metric)
    elif tool_name == "anomaly_detection":
        return summarize_anomalies(result_df, callouts or [], metric)
    elif tool_name == "price_volume_margin":
        return summarize_price_volume(result_df)
    else:
        return "Analysis complete. Data is displayed in the chart and table."
