# Phase 2: Analysis Tools

## Overview

Phase 2 focused on building the mathematical and visual core of the agent: thirteen distinct analysis tools. Each tool is designed to answer specific types of retail business questions by processing the dataset and generating a Plotly chart alongside a structured data table.

## Key Implementations

### 1. Modular Tool Architecture (`tools/` Directory)

- Transitioned from a monolithic script to a modular `tools/` package.
- Each core analysis lives in its own file for maintainability (one file per tool).

### 2. The Thirteen Tools

#### Core Tools (1–5)

- **`yoy_comparison.py`**: Calculates year-over-year growth for specific regions, brands, or divisions. Generates grouped bar charts comparing 2023 vs 2024 metrics, sorted ascending by 2024 value (worst performers on the left, best on the right).
- **`brand_region_crosstab.py`**: Builds a matrix showing how different brands perform across different regions. Uses a grouped bar chart to highlight regional dominance.
- **`forecast_trendline.py`**: Identifies historical trends to project future performance. Specifically tailored to estimate 2025 sales based on 2023-2024 trajectories using sklearn linear regression, visualizing with line charts and a confidence band. Returns a pre-computed plain-text insight with scope-aware language (e.g., "The Sports division is projected to reach $354,846") that bypasses Pass 2 LLM entirely.
- **`anomaly_detection.py`**: Scans the dataset for outliers (e.g., unusual margins or massive pricing drops). Flags anomalous rows and highlights them visually using scatter plots.
- **`price_volume_margin.py`**: Visualizes the relationship between unit price, volume sold, and profit margin using a category-level bubble chart (12 product categories, not individual products). Includes a green "sweet spot" annotation band ($80–$140 price range) and returns a pre-computed insight highlighting top/bottom margin categories and which categories fall within the sweet spot.

#### Advanced Tools (6–13)

- **`store_performance.py`**: Analyses performance at the store level — horizontal bar chart of top/bottom stores by a chosen metric, plus a scatter plot of store size vs performance with a trendline to reveal whether larger stores drive better results.
- **`seasonality_trends.py`**: Overlays monthly or quarterly sales trends across 2023 and 2024 so within-year seasonal patterns become visible. Uses the previously unused QUARTER and MONTH columns.
- **`division_mix.py`**: Side-by-side donut charts showing how much each division contributes to total business and whether the mix shifted between 2023 and 2024.
- **`margin_waterfall.py`**: Waterfall chart decomposing the year-over-year change in margin (or sales) by division/region/brand/category, explaining what drove the change.
- **`kpi_scorecard.py`**: Executive summary table showing every division's Sales, YoY Growth %, Margin Rate, and a RAG status indicator (🟢🟡🔴). No filters — always shows the full business.
- **`price_elasticity.py`**: Estimates price elasticity per category using YoY arc elasticity and cross-sectional log-log regression. Produces a bar chart of elasticity coefficients and a scenario table projecting impact of ±5/10/15% price changes.
- **`brand_benchmarking.py`**: 100% stacked bar chart showing brand share within each category by sales, with a margin rate overlay. Reveals which brands dominate which categories.
- **`growth_margin_matrix.py`**: BCG-style 2×2 bubble chart plotting divisions or categories by YoY growth rate vs margin rate, with bubble size = total sales. Uses unweighted mean of `MARGIN_RATE` (not sales-weighted aggregate) and thresholds rounded to 1 decimal place for precise quadrant classification. Quadrants labelled Stars, Cash Cows, Question Marks, Dogs. Returns a pre-computed insight with quadrant assignments and caveats for low-volume divisions.

#### Out-of-Scope Handler (Tool 14)

- **`out_of_scope`**: Not a true analysis tool — this is a graceful rejection handler. When the user asks about data that does not exist in the dataset (customer-level data, inventory, competitor benchmarks, employee metrics, website traffic), the agent returns a clear explanation of *why* the question cannot be answered and suggests alternative queries the dataset *can* support. No chart or data table is shown. The handler has specific explanations for AOV, customer data, inventory, and competitor questions, with a generic fallback for other unsupported topics.

### 3. Tool Router (`router.py`)

- Implemented a central `tool_router` dispatcher.
- This function acts as the bridge between the LLM's tool selection and the actual Python code execution, safely handling dynamic filters and returning unified 3-tuple outputs (a figure, a dataframe, and a pre-computed insight string or list of text callouts). Tools that return pre-computed insights (forecast, PVM, growth matrix, YoY brand/region) are unpacked as 3-tuples; others are wrapped into 3-tuples by the router.

## Verification

- All 13 analysis tools were tested in isolation using hardcoded filter combinations to ensure mathematical accuracy and visual clarity without relying on the LLM.
- The out-of-scope handler (tool 14) was verified with 10 keyword-detection tests: 5 positives (AOV, customer count, competitors, retention, inventory) and 5 negatives (normal in-scope questions) — all passed.
