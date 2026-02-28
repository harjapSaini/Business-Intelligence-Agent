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

    Produces a directive summary that ensures the LLM references both
    the top grower AND the worst performer (especially declines).
    """
    if result_df is None or result_df.empty:
        return "No year-over-year data available."

    lines = []
    group_col = result_df.columns[0]  # first column is the grouping axis
    metric_label = metric.replace("_", " ").title()

    # Check if we have Change % column
    if "Change %" in result_df.columns and "Change" in result_df.columns:
        sorted_df = result_df.sort_values("Change %", ascending=False)

        # Top grower
        top = sorted_df.iloc[0]
        yr_2023_top = top.get(2023, top.get("2023", 0))
        yr_2024_top = top.get(2024, top.get("2024", 0))
        lines.append(
            f"BEST PERFORMER: {top[group_col]} grew {top['Change %']:+.1f}% YoY, "
            f"from ${yr_2023_top:,.0f} in 2023 to ${yr_2024_top:,.0f} in 2024 "
            f"(+${top['Change']:,.0f} increase)."
        )

        # Bottom grower — flag declines prominently
        bottom = sorted_df.iloc[-1]
        yr_2023_bot = bottom.get(2023, bottom.get("2023", 0))
        yr_2024_bot = bottom.get(2024, bottom.get("2024", 0))
        if bottom["Change %"] < 0:
            lines.append(
                f"KEY RISK: {bottom[group_col]} DECLINED {bottom['Change %']:+.1f}% YoY, "
                f"falling from ${yr_2023_bot:,.0f} to ${yr_2024_bot:,.0f} "
                f"(lost ${abs(bottom['Change']):,.0f} in {metric_label.lower()}). "
                f"This decline MUST be mentioned in the insight."
            )
        else:
            lines.append(
                f"WEAKEST PERFORMER: {bottom[group_col]} at {bottom['Change %']:+.1f}% YoY, "
                f"from ${yr_2023_bot:,.0f} to ${yr_2024_bot:,.0f}."
            )

        # All items
        lines.append(f"\nFull {metric_label} results by {group_col.replace('_', ' ').lower()}:")
        for _, row in sorted_df.iterrows():
            yr_2023 = row.get(2023, row.get("2023", 0))
            yr_2024 = row.get(2024, row.get("2024", 0))
            lines.append(
                f"  {row[group_col]}: 2023=${yr_2023:,.0f}, 2024=${yr_2024:,.0f}, "
                f"change={row['Change %']:+.1f}%, dollar change=${row['Change']:+,.0f}"
            )

        lines.append(
            "\nINSTRUCTION: Your insight MUST mention both the best performer "
            "and the worst performer. If any declined, flag it as a risk. "
            "Use the exact percentages and dollar amounts above."
        )
    else:
        lines.append(f"Results by {group_col.replace('_', ' ').lower()}:")
        for _, row in result_df.iterrows():
            vals = [f"{col}=${row[col]:,.0f}" for col in result_df.columns[1:]
                    if pd.notna(row[col])]
            lines.append(f"  {row[group_col]}: {', '.join(vals)}")

    return "\n".join(lines)


def summarize_crosstab(result_df: pd.DataFrame, metric: str = "sales") -> str:
    """
    Summarize Brand x Region crosstab results.

    Handles two formats:
    - Single-region bar chart: columns are ['Brand', 'Value']
    - Multi-region heatmap:    columns are ['BRAND', 'East', 'West', ...]
    """
    if result_df is None or result_df.empty:
        return "No cross-tab data available."

    lines = []
    brand_col = result_df.columns[0]  # 'Brand' or 'BRAND'
    other_cols = [c for c in result_df.columns if c != brand_col]

    # Detect single-region bar chart format (columns: Brand, Value)
    if len(other_cols) == 1 and other_cols[0] == "Value":
        # Single-region ranked bar chart output
        metric_label = metric.replace("_", " ").title()
        sorted_df = result_df.sort_values("Value", ascending=False)
        lines.append(f"Brands ranked by {metric_label} (highest to lowest):")
        for rank, (_, row) in enumerate(sorted_df.iterrows(), 1):
            if metric == "margin_rate":
                lines.append(f"  {rank}. {row[brand_col]}: {row['Value']:.1%}")
            else:
                lines.append(f"  {rank}. {row[brand_col]}: ${row['Value']:,.0f}")

        # Highlight top and bottom
        top_row = sorted_df.iloc[0]
        bot_row = sorted_df.iloc[-1]
        if metric == "margin_rate":
            lines.append(f"\nTop brand: {top_row[brand_col]} at {top_row['Value']:.1%}")
            lines.append(f"Bottom brand: {bot_row[brand_col]} at {bot_row['Value']:.1%}")
        else:
            gap = top_row['Value'] - bot_row['Value']
            lines.append(f"\nTop brand: {top_row[brand_col]} at ${top_row['Value']:,.0f}")
            lines.append(f"Bottom brand: {bot_row[brand_col]} at ${bot_row['Value']:,.0f}")
            lines.append(f"Gap between top and bottom: ${gap:,.0f}")
    else:
        # Multi-region heatmap output
        region_cols = other_cols
        result_copy = result_df.copy()
        result_copy["Total"] = result_copy[region_cols].sum(axis=1)
        result_copy = result_copy.sort_values("Total", ascending=False)

        lines.append("Brands ranked by total across all regions:")
        for rank, (_, row) in enumerate(result_copy.iterrows(), 1):
            lines.append(f"  {rank}. {row[brand_col]}: ${row['Total']:,.0f}")
            best_region = max(region_cols, key=lambda r: row[r])
            lines.append(f"     Strongest region: {best_region} (${row[best_region]:,.0f})")

        lines.append("\nRegional totals:")
        for region in region_cols:
            total = result_df[region].sum()
            lines.append(f"  {region}: ${total:,.0f}")

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


# =====================================================================
#  SUMMARIZERS FOR NEW TOOLS (6–13)
# =====================================================================

def summarize_store_performance(result_df: pd.DataFrame, metric: str = "sales") -> str:
    """Summarize store performance results."""
    if result_df is None or result_df.empty:
        return "No store performance data available."

    metric_col_map = {
        "sales": "SALES", "margin": "MARGIN",
        "units": "UNITS_SOLD", "margin_rate": "MARGIN_RATE",
    }
    col = metric_col_map.get(metric, "SALES")

    lines = []
    lines.append(f"Total stores analyzed: {len(result_df)}")

    if col in result_df.columns:
        sorted_df = result_df.sort_values(col, ascending=False)
        top = sorted_df.iloc[0]
        bottom = sorted_df.iloc[-1]
        lines.append(f"\nTop store: {top['STORE_NAME']} ({col}: {top[col]:,.0f}, size: {top['STORE_SIZE']})")
        lines.append(f"Bottom store: {bottom['STORE_NAME']} ({col}: {bottom[col]:,.0f}, size: {bottom['STORE_SIZE']})")

        # Correlation between store size and metric
        if "STORE_SIZE" in result_df.columns:
            numeric_size = pd.to_numeric(result_df["STORE_SIZE"], errors="coerce")
            valid = result_df[numeric_size.notna()].copy()
            if len(valid) >= 3:
                corr = numeric_size[valid.index].corr(valid[col])
                direction = "positive" if corr > 0.2 else ("negative" if corr < -0.2 else "weak/no")
                lines.append(f"\nStore size vs {metric} correlation: {direction} (r={corr:.2f})")

    lines.append(f"\nAll stores by {metric}:")
    for _, row in result_df.head(10).iterrows():
        lines.append(f"  - {row['STORE_NAME']}: {col}={row.get(col, 0):,.0f}, size={row['STORE_SIZE']}")

    return "\n".join(lines)


def summarize_seasonality(result_df: pd.DataFrame, metric: str = "sales") -> str:
    """Summarize seasonality trends results."""
    if result_df is None or result_df.empty:
        return "No seasonality data available."

    lines = []
    time_col = result_df.columns[0]  # 'Month' or 'Quarter'
    year_cols = [c for c in result_df.columns if c not in (time_col, "Change %")]

    for yr in year_cols:
        if yr in result_df.columns:
            try:
                peak_idx = result_df[yr].idxmax()
                trough_idx = result_df[yr].idxmin()
                peak_period = result_df.loc[peak_idx, time_col]
                trough_period = result_df.loc[trough_idx, time_col]
                lines.append(f"{yr} peak: {time_col} {peak_period} (${result_df.loc[peak_idx, yr]:,.0f})")
                lines.append(f"{yr} trough: {time_col} {trough_period} (${result_df.loc[trough_idx, yr]:,.0f})")
            except (ValueError, TypeError):
                pass

    if "Change %" in result_df.columns:
        lines.append(f"\nYoY change by {time_col.lower()}:")
        for _, row in result_df.iterrows():
            lines.append(f"  - {time_col} {row[time_col]}: {row['Change %']:+.1f}%")

    return "\n".join(lines)


def summarize_division_mix(result_df: pd.DataFrame, metric: str = "sales") -> str:
    """Summarize division mix results."""
    if result_df is None or result_df.empty:
        return "No division mix data available."

    lines = []
    share_cols = [c for c in result_df.columns if "Share%" in c]
    value_cols = [c for c in result_df.columns if "Value" in c]

    lines.append("Division revenue mix:")
    for _, row in result_df.iterrows():
        parts = [f"{row['Division']}:"]
        for sc in share_cols:
            parts.append(f"{sc}={row[sc]:.1f}%")
        lines.append("  - " + " ".join(parts))

    if "Shift_pp" in result_df.columns:
        biggest_gain = result_df.loc[result_df["Shift_pp"].idxmax()]
        biggest_loss = result_df.loc[result_df["Shift_pp"].idxmin()]
        lines.append(f"\nBiggest share gain: {biggest_gain['Division']} ({biggest_gain['Shift_pp']:+.1f}pp)")
        lines.append(f"Biggest share loss: {biggest_loss['Division']} ({biggest_loss['Shift_pp']:+.1f}pp)")

        # HHI concentration check
        for sc in share_cols:
            hhi = (result_df[sc] ** 2).sum()
            lines.append(f"Concentration (HHI) for {sc}: {hhi:.0f}")

    return "\n".join(lines)


def summarize_waterfall(result_df: pd.DataFrame, metric: str = "margin") -> str:
    """Summarize margin waterfall results."""
    if result_df is None or result_df.empty:
        return "No waterfall data available."

    lines = []
    year_cols = [c for c in result_df.columns if c not in ("Group", "Change", "Change %")]

    if len(year_cols) >= 2:
        yr_start, yr_end = year_cols[0], year_cols[1]
        total_start = result_df[yr_start].sum()
        total_end = result_df[yr_end].sum()
        lines.append(f"Starting {metric} ({yr_start}): ${total_start:,.0f}")
        lines.append(f"Ending {metric} ({yr_end}): ${total_end:,.0f}")
        lines.append(f"Net change: ${total_end - total_start:,.0f}")

    if "Change" in result_df.columns:
        sorted_df = result_df.sort_values("Change", ascending=False)
        top_contributor = sorted_df.iloc[0]
        top_drag = sorted_df.iloc[-1]
        lines.append(f"\nTop positive contributor: {top_contributor['Group']} (${top_contributor['Change']:+,.0f})")
        lines.append(f"Top negative contributor: {top_drag['Group']} (${top_drag['Change']:+,.0f})")

        lines.append(f"\nAll contributions:")
        for _, row in sorted_df.iterrows():
            lines.append(f"  - {row['Group']}: ${row['Change']:+,.0f} ({row['Change %']:+.1f}%)")

    return "\n".join(lines)


def summarize_scorecard(result_df: pd.DataFrame) -> str:
    """Summarize KPI scorecard results."""
    if result_df is None or result_df.empty:
        return "No scorecard data available."

    lines = []

    # Count RAG statuses
    if "RAG" in result_df.columns:
        greens = result_df["RAG"].str.contains("🟢").sum()
        yellows = result_df["RAG"].str.contains("🟡").sum()
        reds = result_df["RAG"].str.contains("🔴").sum()
        lines.append(f"RAG status: {greens} 🟢, {yellows} 🟡, {reds} 🔴")

    # Total row
    total_row = result_df[result_df["Division"] == "TOTAL"]
    if not total_row.empty:
        tr = total_row.iloc[0]
        growth_col = "YoY_Growth%"
        if growth_col in tr:
            lines.append(f"Overall YoY growth: {tr[growth_col]:+.1f}%")

    # Division details
    div_rows = result_df[result_df["Division"] != "TOTAL"]
    if not div_rows.empty and "YoY_Growth%" in div_rows.columns:
        best = div_rows.loc[div_rows["YoY_Growth%"].idxmax()]
        worst = div_rows.loc[div_rows["YoY_Growth%"].idxmin()]
        lines.append(f"\nStrongest division: {best['Division']} ({best['YoY_Growth%']:+.1f}% growth)")
        lines.append(f"Weakest division: {worst['Division']} ({worst['YoY_Growth%']:+.1f}% growth)")

    lines.append(f"\nDivision details:")
    for _, row in div_rows.iterrows():
        rag = row.get("RAG", "")
        growth = row.get("YoY_Growth%", 0)
        margin_chg = row.get("Margin_Change_pp", 0)
        lines.append(f"  - {row['Division']}: {rag} growth={growth:+.1f}%, margin change={margin_chg:+.1f}pp")

    return "\n".join(lines)


def summarize_elasticity(result_df: pd.DataFrame) -> str:
    """Summarize price elasticity results."""
    if result_df is None or result_df.empty:
        return "No elasticity data available."

    lines = []
    group_col = result_df.columns[0]  # 'Category' or 'Product'

    # Get unique elasticity values per group (scenario table has many rows per group)
    if "Elasticity" in result_df.columns:
        unique_elas = result_df.drop_duplicates(subset=[group_col])[[group_col, "Elasticity"]]
        unique_elas = unique_elas.sort_values("Elasticity")

        lines.append("Price elasticity by category:")
        for _, row in unique_elas.iterrows():
            e = row["Elasticity"]
            label = "highly elastic" if abs(e) > 1.5 else ("elastic" if abs(e) > 0.8 else "inelastic")
            lines.append(f"  - {row[group_col]}: Ed={e:.2f} ({label})")

        most_sensitive = unique_elas.iloc[0]
        least_sensitive = unique_elas.iloc[-1] if len(unique_elas) > 1 else unique_elas.iloc[0]
        lines.append(f"\nMost price-sensitive: {most_sensitive[group_col]} (Ed={most_sensitive['Elasticity']:.2f})")
        lines.append(f"Least price-sensitive: {least_sensitive[group_col]} (Ed={least_sensitive['Elasticity']:.2f})")

    # Show a sample scenario
    if "Price_Change%" in result_df.columns and "Revenue_Impact%" in result_df.columns:
        sample = result_df[result_df["Price_Change%"] == 10]
        if not sample.empty:
            lines.append(f"\nImpact of +10% price increase:")
            for _, row in sample.iterrows():
                lines.append(f"  - {row[group_col]}: units {row.get('Projected_Units_Change%', 0):+.1f}%, revenue {row['Revenue_Impact%']:+.1f}%")

    return "\n".join(lines)


def summarize_brand_benchmarking(result_df: pd.DataFrame) -> str:
    """Summarize brand benchmarking results."""
    if result_df is None or result_df.empty:
        return "No brand benchmarking data available."

    lines = []

    if "Category" in result_df.columns and "Share%" in result_df.columns:
        categories = result_df["Category"].unique()
        lines.append(f"Brand share analysis across {len(categories)} categories:")

        for cat in categories:
            cat_data = result_df[result_df["Category"] == cat].sort_values("Share%", ascending=False)
            leader = cat_data.iloc[0]
            lines.append(
                f"\n  {cat}:"
                f"\n    Leader: {leader['Brand']} ({leader['Share%']:.1f}% share, margin: {leader['Margin_Rate']:.1%})"
            )
            if len(cat_data) > 1:
                runner_up = cat_data.iloc[1]
                lines.append(f"    Runner-up: {runner_up['Brand']} ({runner_up['Share%']:.1f}%)")

    return "\n".join(lines)


def summarize_growth_margin(result_df: pd.DataFrame) -> str:
    """Summarize growth-margin matrix results."""
    if result_df is None or result_df.empty:
        return "No growth-margin data available."

    lines = []

    if "Quadrant" in result_df.columns:
        for quadrant in ["Stars", "Cash Cows", "Question Marks", "Dogs"]:
            q_data = result_df[result_df["Quadrant"] == quadrant]
            if not q_data.empty:
                items = ", ".join(q_data["Group"].tolist())
                lines.append(f"{quadrant}: {items}")

        lines.append(f"\nDetailed positioning:")
        for _, row in result_df.iterrows():
            lines.append(
                f"  - {row['Group']}: margin={row['Margin_Rate']:.1f}%, "
                f"growth={row['YoY_Growth%']:+.1f}%, quadrant={row['Quadrant']}"
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
    elif tool_name == "store_performance":
        return summarize_store_performance(result_df, metric)
    elif tool_name == "seasonality_trends":
        return summarize_seasonality(result_df, metric)
    elif tool_name == "division_mix":
        return summarize_division_mix(result_df, metric)
    elif tool_name == "margin_waterfall":
        return summarize_waterfall(result_df, metric)
    elif tool_name == "kpi_scorecard":
        return summarize_scorecard(result_df)
    elif tool_name == "price_elasticity":
        return summarize_elasticity(result_df)
    elif tool_name == "brand_benchmarking":
        return summarize_brand_benchmarking(result_df)
    elif tool_name == "growth_margin_matrix":
        return summarize_growth_margin(result_df)
    else:
        return "Analysis complete. Data is displayed in the chart and table."
