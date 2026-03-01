# Testing & Verification

## Test Summary

All 7 phases and subsequent tool refinements have been verified for mathematical accuracy, UI robustness, and LLM reliability.

| Phase                     | Tests / Verification | Result |
| ------------------------- | -------------------- | ------ |
| Phase 1 - Foundation      | 20/20                | ✅     |
| Phase 2 - Analysis Tools  | 22/22                | ✅     |
| Phase 3 - LLM Integration | 47/47                | ✅     |
| Phase 4 - Session Memory  | 27/27                | ✅     |
| Phase 5 - UI Polish       | 30/30                | ✅     |
| Phase 6 - Dark / Light UI | Browser Subagent     | ✅     |
| Phase 7 - Two-Pass LLM    | Browser Subagent     | ✅     |
| Routing Hardening         | Manual + Unit        | ✅     |
| UX Polish                 | Manual               | ✅     |
| Tool Refinement           | Manual + Unit        | ✅     |

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
- PVM aggregates to category level (12 bubbles, not 200+ products) with sweet spot vrect annotation
- Store performance returns top/bottom N stores with size trendline
- Seasonality trends overlays 2023 vs 2024 by month and quarter
- Division mix produces side-by-side donut charts with share shift
- Margin waterfall decomposes YoY change into group-level deltas
- KPI scorecard returns RAG-status table for all divisions (no filters)
- Price elasticity computes arc elasticity and log-log regression per category
- Brand benchmarking generates 100% stacked bar with margin overlay
- Growth-margin matrix plots BCG-style 2×2 bubble chart with quadrant labels using mean-based MARGIN_RATE and rounded thresholds
- Tool router dispatches all 14 tools correctly (13 analysis + out_of_scope)
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

- Config has CHART_COLORS (10), YOY_COLORS, ANOMALY_COLORS, FORECAST_\*, HEATMAP_SCALE
- All 13 charts use correct config colours (including WATERFALL_COLORS, RAG_COLORS, QUADRANT_COLORS)
- All 13 charts use Inter font and title_font_size=18
- UI module exports: inject_custom_css, render_welcome, render_chat_message, render_suggestions, render_loading_animation
- Welcome screen has 10 example questions in a 2-column layout
- Custom CSS has: Inter font import, button hover, tool-badge class, sidebar gradient, Canadian Tire red
- Processing state disables chat input, welcome buttons, suggestion buttons, and dark mode toggle
- Cycling loading animation shows 51 rotating messages with CSS fade transition
- User prompt visible in chat history while response loads
- st.html() renders insight text (bypasses Streamlit markdown parser bugs)

## Phase 6 Tests

- Custom CSS blocks explicitly define Light and Dark mode variables.
- Streamlit Base theme logic overridden in `.streamlit/config.toml` to prevent OS-level bleeding.
- Dark mode toggle in sidebar switches `st.session_state.dark_mode`.
- Dark mode toggle is disabled during processing to prevent UI resets.
- Plotly templates dynamically swap between `plotly_white` and `plotly_dark`.
- Historical charts re-template at render time to match current theme.
- Text contrast passes legibility tests in both modes.

## Phase 7 Tests

- All 13 tool outputs successfully serialized into compact string summaries via `insight_builder.py`.
- LLM Router reliably fires immediately on prompt submission (Pass 1).
- Execution sequence verified: LLM Router -> Routing Safety Net -> Tool Processing -> Data Summarization -> LLM Insight (Pass 2).
- LLM narrations explicitly quote numbers, brands, and percentages from the tool output, eliminating generic hallucinations.
- `validate_routing()` correctly routes brand+YoY overlap questions (e.g., "Which brand grew the most year over year?" → `yoy_comparison`, not `brand_region_crosstab`).
- `validate_routing()` correctly identifies out-of-scope questions (AOV, customer count, inventory, competitor data) and routes to `out_of_scope`.
- Out-of-scope questions show explanatory text with no chart, no tool badge, and an info box.
- Normal in-scope questions (e.g., "Show me sales by division") are NOT false-positived into out_of_scope.
- `extract_missing_filters()` correctly infers `group_by` from keywords: "brand" → brand, "region" (without filter) → region, default → division.
- `clean_insight_text()` strips all markdown formatting; `validate_insight_format()` catches structured data leaks.
- `clean_insight_text()` safety net in `agent.py` strips residual markdown from all pre-computed insights before rendering.
- Insight text renders cleanly via `st.html()` with no backtick or code-span artifacts.
- Pre-computed insights bypass Pass 2 LLM correctly for forecast, PVM, growth matrix, and YoY brand/region tools.

## Tool Refinement Tests

- **Forecast Trendline**: Returns 3-tuple with pre-computed plain-text insight. Chart title uses deduplicated `filter_parts` (no more "Div: X, Division: X"). Scope-aware insight text verified (e.g., "The Sports division is projected to reach $354,846"). No markdown artifacts in insight text.
- **Price-Volume-Margin**: Category-level aggregation verified — 12 bubbles (one per product category, not 200+ individual products). Sweet spot vrect annotation ($80–$140) renders correctly. Pre-computed insight text correctly reports Snacks (55.5%) as top margin, Shirts (43.2%) as worst, and Decor/Safety Gear in the sweet spot.
- **Growth-Margin Matrix**: Quadrant classification verified — Sports = Question Mark, Food = Star, Gardening = Cash Cow, Apparel = Dog, Tools = Cash Cow. Tools correctly classified as Cash Cow (50.2% margin ≥ 50.2% threshold) after switching to unweighted mean `MARGIN_RATE` aggregation and rounding thresholds to 1 decimal. Food sales correctly shows "$83K in total sales" (both years combined, not just 2024).
- **YoY Comparison**: Bars sorted ascending by 2024 value — worst performers on the left, best on the right. Verified for all `group_by` values (brand, division, region, category).
- **Agent Pre-Computed Insight Safety Net**: `clean_insight_text()` imported from `ollama_client` and applied to all pre-computed insights in `agent.py` before rendering. Verified no markdown passes through.
- **Insight Builder (PVM)**: `summarize_price_volume()` rewritten for category-level schema (`PRODUCT_CATEGORY`, `avg_price`, `margin_rate`, `total_units`, `total_sales`, `margin_pct`). No KeyError on `PRODUCT_NAME`. Reports top/bottom 3 categories and sweet-spot analysis.

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
