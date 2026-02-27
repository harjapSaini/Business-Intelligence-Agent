# Phase 1 - Foundation & Data Layer

## Overview

Phase 1 establishes the core infrastructure: loading the dataset, computing KPI columns, verifying the Ollama connection, and rendering the sidebar.

## Files Created

| File               | Purpose                                                             |
| ------------------ | ------------------------------------------------------------------- |
| `config.py`        | Centralised constants (Ollama URL, model, data path, valid tools)   |
| `data_loader.py`   | `load_data()` with `@st.cache_data`, `get_dataset_summary()`        |
| `ollama_client.py` | `verify_ollama()` - checks Ollama is running and model is available |
| `ui.py`            | `render_sidebar()` - security badge, dataset stats, privacy caption |
| `agent.py`         | Entry point - page config, data loading, sidebar rendering          |

## Dataset

- **Source:** `CaseStudy_DataExtractFromPowerBIFile.xlsx`
- **Rows:** 7,310 transaction records
- **Original columns (16):** YEAR, MONTH, SELLING_PRICE_PER_UNIT, COST_PER_UNIT, UNITS_SOLD, PRODUCT_NAME, PRODUCT_CATEGORY, PRODUCT_DIVISION, REGION, BRAND, etc.

## Computed KPI Columns

| Column        | Formula                               |
| ------------- | ------------------------------------- |
| `SALES`       | `SELLING_PRICE_PER_UNIT × UNITS_SOLD` |
| `COGS`        | `COST_PER_UNIT × UNITS_SOLD`          |
| `MARGIN`      | `SALES − COGS`                        |
| `MARGIN_RATE` | `MARGIN / SALES` (0 if SALES = 0)     |

## Data Summary

The `get_dataset_summary()` function returns:

```python
{
    "total_rows": 7310,
    "regions": ["East", "North", "South", "West"],
    "divisions": ["Apparel", "Food", "Gardening", "Sports", "Tools"],
    "categories": [...],  # 12 categories
    "brands": [...],       # 10 brands
    "years": [2023, 2024],
    "sales_by_year": {2023: 1023950, 2024: 1063778},
}
```

## Ollama Verification

`verify_ollama()` checks:

1. Ollama API is reachable at `http://localhost:11434`
2. The `llama3.2:3b` model is downloaded and available
3. Returns `(True, "llama3.2:3b")` on success or `(False, error_message)` on failure

The result drives the green/red security badge in the sidebar.

## Caching

`load_data()` uses Streamlit's `@st.cache_data` decorator so the Excel file is only read once per session, not on every rerun.
