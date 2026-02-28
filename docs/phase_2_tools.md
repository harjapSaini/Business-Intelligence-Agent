# Phase 2: Analysis Tools

## Overview

Phase 2 focused on building the mathematical and visual core of the agent: the five distinct analysis tools. Each tool is designed to answer specific types of retail business questions by processing the dataset and generating a Plotly chart alongside a structured data table.

## Key Implementations

### 1. Modular Tool Architecture (`tools/` Directory)

- Transitioned from a monolithic script to a modular `tools/` package.
- Each core analysis was sequestered into its own file for maintainability.

### 2. The Five Tools

- **`yoy_comparison.py`**: Calculates year-over-year growth for specific regions, brands, or divisions. Generates grouped bar charts comparing 2023 vs 2024 metrics.
- **`brand_region_crosstab.py`**: Builds a matrix showing how different brands perform across different regions. Uses a grouped bar chart to highlight regional dominance.
- **`forecast_trendline.py`**: Identifies historical trends to project future performance. Specifically tailored to estimate 2025 sales based on 2023-2024 trajectories, visualizing with line charts.
- **`anomaly_detection.py`**: Scans the dataset for outliers (e.g., unusual margins or massive pricing drops). Flags anomalous rows and highlights them visually using scatter plots.
- **`price_volume_margin.py`**: Visualizes the delicate balance between unit price, volume sold, and profit margin using a bubble chart, helping users identify the "sweet spot" for pricing.

### 3. Tool Router (`router.py`)

- Implemented a central `tool_router` dispatcher.
- This function acts as the bridge between the LLM's tool selection and the actual Python code execution, safely handling dynamic filters and returning unified outputs (a figure, a dataframe, and a list of text callouts).

## Verification

- All 5 tools were tested in isolation using hardcoded filter combinations to ensure mathematical accuracy and visual clarity without relying on the LLM.
