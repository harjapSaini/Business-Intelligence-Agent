# Phase 5 - UI Polish & Performance

## Overview

Phase 5 applies visual polish: consistent chart colours, custom CSS styling, a polished welcome screen, and performance optimisations.

## Colour Palette

Defined centrally in `config.py` and used across all 5 tools:

| Constant              | Value                               | Usage                        |
| --------------------- | ----------------------------------- | ---------------------------- |
| `YOY_COLORS`          | Blue `#1976D2`, Red `#D32F2F`       | YoY bar chart (2023 vs 2024) |
| `ANOMALY_COLORS`      | Red `#D32F2F`, Light blue `#90CAF9` | Outlier vs normal scatter    |
| `FORECAST_HISTORICAL` | Blue `#1976D2`                      | Historical trendline         |
| `FORECAST_PREDICTED`  | Red `#D32F2F`                       | Forecast dotted line         |
| `FORECAST_CONFIDENCE` | `rgba(211,47,47,0.12)`              | Confidence band shading      |
| `HEATMAP_SCALE`       | `"RdYlGn"`                          | Brand × Region heatmap       |
| `CHART_COLORS`        | 10-colour palette                   | PVM categories               |

## Custom CSS

Injected via `inject_custom_css()` on every page load:

- **Font:** Inter (Google Fonts) for all text and charts
- **Sidebar:** Gradient background (`#fafbfc` → `#f0f4f8`)
- **Buttons:** Rounded, hover effect (red border + lift + shadow)
- **Tool badges:** Grey pill with tool name
- **Welcome card:** Gradient background with styled example questions

## Welcome Screen

`render_welcome()` displays:

- A gradient hero card with title and description
- 5 clickable example question buttons
- Clicking a button processes it as a real question

## Chart Consistency

All 5 tool charts use:

- `template="plotly_white"` for clean backgrounds
- `font_family="Inter, sans-serif"` matching the app
- `title_font_size=18` for readable titles

## Performance Optimisations

| Optimisation            | Mechanism                                               |
| ----------------------- | ------------------------------------------------------- |
| Data caching            | `@st.cache_data` on `load_data()`                       |
| Model warm-up           | `warmup_model()` pre-loads LLM into memory              |
| Once-per-session checks | Ollama verification and warm-up stored in session state |
| Sidebar sales delta     | Shows `+3.9% vs 2023` without extra computation         |
