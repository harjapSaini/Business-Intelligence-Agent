# Testing & Verification

## Test Summary

All 7 phases have been verified for mathematical accuracy, UI robustness, and LLM reliability.

| Phase                     | Tests / Verification | Result |
| ------------------------- | -------------------- | ------ |
| Phase 1 - Foundation      | 20/20                | ✅     |
| Phase 2 - Analysis Tools  | 22/22                | ✅     |
| Phase 3 - LLM Integration | 47/47                | ✅     |
| Phase 4 - Session Memory  | 27/27                | ✅     |
| Phase 5 - UI Polish       | 30/30                | ✅     |
| Phase 6 - Dark / Light UI | Browser Subagent     | ✅     |
| Phase 7 - Two-Pass LLM    | Browser Subagent     | ✅     |

## Phase 1 Tests

- Config imports and constant values
- DataFrame loads 7,310 rows with 16 original columns
- 4 KPI columns computed (SALES, COGS, MARGIN, MARGIN_RATE)
- Dataset summary: correct counts for regions (4), divisions (5), categories (12), brands (10), years (2)
- Sales figures: 2023 ≈ $1,023,950, 2024 ≈ $1,063,778
- Ollama reachable and model available
- UI sidebar function imports

## Phase 2 Tests

- All 13 tool functions return (figure, summary_df) or (figure, summary_df, callouts)
- Filters work: region, division, brand, category
- YoY summary has Change % column
- Forecast produces 12 forecast rows
- Anomaly detection generates callout strings
- PVM handles multi-filter (division + category)
- Store performance returns top/bottom N stores with size trendline
- Seasonality trends overlays 2023 vs 2024 by month and quarter
- Division mix produces side-by-side donut charts with share shift
- Margin waterfall decomposes YoY change into group-level deltas
- KPI scorecard returns RAG-status table for all divisions (no filters)
- Price elasticity computes arc elasticity and log-log regression per category
- Brand benchmarking generates 100% stacked bar with margin overlay
- Growth-margin matrix plots BCG-style 2×2 bubble chart with quadrant labels
- Tool router dispatches all 13 tools correctly
- Router handles unknown tools (fallback)
- Router normalises `"None"` and `"null"` filter strings

## Phase 3 Tests

- System prompt contains all tool names, filter values, and JSON format
- System prompt includes memory context when provided
- JSON extraction handles: clean, markdown-fenced, embedded, and garbage input
- Validation fixes: bad tool names, missing filters, missing insight, wrong suggestion count
- Live LLM: 5/5 correct tool selections
- All LLM responses have valid insight and 3 suggestions
- LLM → tool router → chart generation works end-to-end

## Phase 4 Tests

- Memory captures entities from filters
- Null strings (`"None"`, `"null"`) are ignored
- Entities merge across multiple questions (not overwritten)
- Last filters and last result are tracked
- Top item extracted from result DataFrame
- Live 3-round conversation: Q1 → Q2 (follow-up) → Q3 (context-dependent)
- All 3 rounds produce valid tools, charts, and memory updates

## Phase 5 Tests

- Config has CHART*COLORS (10), YOY_COLORS, ANOMALY_COLORS, FORECAST*\*, HEATMAP_SCALE
- All 13 charts use correct config colours (including WATERFALL_COLORS, RAG_COLORS, QUADRANT_COLORS)
- All 13 charts use Inter font and title_font_size=18
- UI module exports: inject_custom_css, render_welcome, render_chat_message, render_suggestions
- Welcome screen has 5 example questions
- Custom CSS has: Inter font import, button hover, tool-badge class, sidebar gradient, Canadian Tire red

## Phase 6 Tests

- Custom CSS blocks explicitly define Light and Dark mode variables.
- Streamlit Base theme logic overridden in `.streamlit/config.toml` to prevent OS-level bleeding.
- Dark mode toggle in sidebar switches `st.session_state.dark_mode`.
- Plotly templates dynamically swap between `plotly_white` and `plotly_dark`.
- Text contrast passes legibility tests in both modes.

## Phase 7 Tests

- All 13 tool outputs successfully serialized into compact string summaries via `insight_builder.py`.
- LLM Router reliably fires immediately on prompt submission (Pass 1).
- Execution sequence verified: LLM Router -> Tool Processing -> Data Summarization -> LLM Insight (Pass 2).
- LLM narrations explicitly quote numbers, brands, and percentages from the tool output, eliminating generic hallucinations.

## Running Tests

Tests were run via standalone Python scripts. To re-run:

```bash
# Activate virtual environment
source venv/Scripts/activate

# Run individual test files (if they exist)
python test_modular.py
python test_full.py
python test_phase4_5.py
```

> **Note:** Live LLM tests require Ollama to be running with the `llama3.2:3b` model loaded.
