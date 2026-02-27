# Phase 2 - Analysis Tools

## Overview

Phase 2 implements 5 analysis tool functions, each producing a Plotly chart and a summary DataFrame. These tools are the core analytical engine that the LLM selects from based on user questions.

## Tool Architecture

Each tool lives in its own file within the `tools/` package:

```
tools/
├── __init__.py              # Re-exports for clean imports
├── yoy_comparison.py        # Tool 1
├── brand_region_crosstab.py # Tool 2
├── forecast_trendline.py    # Tool 3
├── anomaly_detection.py     # Tool 4
├── price_volume_margin.py   # Tool 5
└── router.py                # Dispatches LLM requests to tools
```

## Tool 1: Year-over-Year Comparison

**Function:** `yoy_comparison(df, metric, region, division, brand, category)`

**Purpose:** Compares a metric across 2023 vs 2024 using a grouped bar chart.

**Metrics:** `sales`, `units`, `margin`, `margin_rate`, `cogs`

**Output:**

- Grouped bar chart (one bar per year, grouped by division)
- Summary DataFrame with 2023, 2024, and Change % columns

**Example question:** _"Which division grew the most year over year?"_

## Tool 2: Brand × Region Cross-Tab

**Function:** `brand_region_crosstab(df, metric, division, year)`

**Purpose:** Shows performance of all 10 brands across all 4 regions as a heatmap.

**Output:**

- Plotly `imshow` heatmap (brands on Y-axis, regions on X-axis)
- Pivot table DataFrame

**Example question:** _"Which brands perform best in the West region?"_

## Tool 3: Forecast Trendline

**Function:** `forecast_trendline(df, group_by, group_value, metric)`

**Purpose:** Plots historical monthly trends and projects 12 months into the future using linear regression.

**Output:**

- Line chart with historical (solid) and forecast (dotted) lines
- Confidence band (±1 std dev shading)
- Combined DataFrame with `type` column ("historical" / "forecast")

**Example question:** _"Project Apparel division sales into 2025"_

## Tool 4: Anomaly Detection

**Function:** `anomaly_detection(df, metric, division, region)`

**Purpose:** Identifies statistical outliers at the product level using Z-scores (threshold: |Z| > 2).

**Output:**

- Scatter plot with outliers in red, normal points in blue
- Outlier DataFrame sorted by Z-score
- Human-readable callout strings (e.g., "Anomaly: ProductX has margin rate 0.85 (Z=3.2)")

**Example question:** _"Are there any anomalies in product margins?"_

## Tool 5: Price-Volume-Margin Analysis

**Function:** `price_volume_margin(df, division, category, brand)`

**Purpose:** Bubble chart showing the relationship between price, margin rate, and volume.

**Output:**

- Scatter plot (x=avg price, y=margin rate, size=units sold, colour=category)
- Product-level aggregation DataFrame

**Example question:** _"What is the pricing sweet spot for Tools division?"_

## Tool Router

**Function:** `tool_router(tool_name, filters, df) → (fig, summary_df, callouts)`

- Maps tool name strings to the correct function
- Cleans filter values (normalises `"None"`, `"null"` to `None`)
- Returns `(figure, summary_df, callouts)` - callouts is only non-None for anomaly detection
- Falls back to `yoy_comparison` for unknown tool names
