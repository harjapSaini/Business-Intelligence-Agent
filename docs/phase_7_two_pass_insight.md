# Phase 7: Data-Driven Insights (Two-Pass Architecture)

## Overview

Phase 7 addressed a major flaw in the original design: the LLM was originally generating insights _before_ the tools processed the data, resulting in vague, generalized text ("Sales appear to be strong"). This phase implemented a revolutionary two-pass architecture to ground the AI strictly in the dataframe's actual math. Subsequent iterations hardened the routing layer with a 3-layer safety net and improved insight text quality.

## Key Implementations

### 1. Architecture Overhaul (`agent.py` & `ollama_client.py`)

Relocated the insight generation step _after_ the tool returns its results.
The new sequence within `process_question()`:

1. **Pass 1 (Routing):** LLM analyzes the prompt and returns strictly JSON (tool name + filters).
2. **Routing Safety Net:** `validate_routing()` keyword guard overrides incorrect tool selections. `extract_missing_filters()` fills any filter gaps the LLM missed (region, division, brand, metric, group_by, top_n, view).
3. **Execution:** The router runs the selected Python tool, returning a chart, a dataframe, and statistical callouts.
4. **Data Summarization:** A new module converts the dataframe into compact text.
5. **Pass 2 (Synthesis):** The LLM receives the compact text summary + the original question, returning a narrative insight packed with real numbers.

### 2. Data Summarizers (`insight_builder.py`)

- Wrote thirteen specialized summarizer functions (one for each tool output type).
- E.g., `summarize_yoy()` takes a grouped pandas dataframe and returns a directive format with BEST PERFORMER and KEY RISK labels.
- `summarize_crosstab()` handles both single-region (Brand/Value columns) and multi-region format.
- This approach feeds the LLM extreme density data without blowing out the token context window with massive raw CSV strings.

### 3. Prompt Re-Engineering (`ollama_client.py`)

- Created `build_insight_prompt()` specifically for Pass 2.
- Commanded the model to write professional, concise 2-3 sentence analyses highlighting _specific numbers_, _entity names_, and _percentage changes_ directly extracted from the provided text summary.
- Enforced strict formatting rules: no markdown, no backticks, no bullet points, no structured data dumps.
- Enforced a rule that the model must also generate contextually relevant follow-up questions tied to the actual identified data points.

### 4. Three-Layer Routing Safety Net

1. **System Prompt (Layer 1):** 4-section structured prompt with 13 tool definitions (each with 5 example questions and keywords), filter extraction rules, 13 worked JSON examples, and output format rules. Includes `group_by` documentation for YoY brand/region/category grouping.
2. **`validate_routing()` (Layer 2):** Priority-ordered keyword guard that runs before `tool_router`. Checks specialised tools first (brands, KPI, waterfall, BCG, etc.) and generic YoY last. Handles ambiguous overlap (e.g., brand + YoY signals → routes to YoY, not brand crosstab).
3. **`extract_missing_filters()` (Layer 3):** Post-routing gap filler that scans the question for filter values the LLM missed — region, division, brand, metric, top_n, view, and `group_by` (brand/category/region inference from keywords).

### 5. Insight Quality Hardening

- `clean_insight_text()` aggressively strips all markdown formatting (backticks via direct `text.replace()`, bold/italic/headers via regex).
- `validate_insight_format()` catches 9 red-flag patterns in insight text: "Best region: Value", bullet counts, structured data dumps, length > 600 chars, etc.
- `validate_insight_response()` chains clean → validate → suggestion validation.
- Exception fallback returns a clean generic sentence instead of raw data summaries.

## Verification

- Validated via automated browser testing.
- Before: _"This analysis likely shows that the top-performing brands are driving revenue."_
- After: _"Sports grew by +15.5% YoY, outpacing all other divisions, reaching $325,459 in 2024 compared to $281,746 in 2023."_
- Routing accuracy verified: "Which brand grew the most year over year?" correctly routes to `yoy_comparison` with `group_by: "brand"`.
- Insight text confirmed free of markdown artifacts, backticks, and structured data leaks.
