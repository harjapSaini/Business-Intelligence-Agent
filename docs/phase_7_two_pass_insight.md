# Phase 7: Data-Driven Insights (Two-Pass Architecture)

## Overview

Phase 7 addressed a major flaw in the original design: the LLM was originally generating insights _before_ the tools processed the data, resulting in vague, generalized text ("Sales appear to be strong"). This phase implemented a revolutionary two-pass architecture to ground the AI strictly in the dataframe's actual math.

## Key Implementations

### 1. Architecture Overhaul (`agent.py` & `ollama_client.py`)

Relocated the insight generation step _after_ the tool returns its results.
The new sequence within `process_question()`:

1. **Pass 1 (Routing):** LLM analyzes the prompt and returns strictly JSON (tool name + filters).
2. **Execution:** The router runs the selected Python tool, returning a chart, a dataframe, and statistical callouts.
3. **Data Summarization:** A new module converts the dataframe into compact text.
4. **Pass 2 (Synthesis):** The LLM receives the compact text summary + the original question, returning a narrative insight packed with real numbers.

### 2. Data Summarizers (`insight_builder.py`)

- Wrote five specialized summarizer functions (one for each tool output type).
- E.g., `summarize_yoy()` takes a grouped pandas dataframe and returns a concise string: "Apparel hit 250k in 2023 vs 275k in 2024 (10% growth)."
- This approach feeds the LLM extreme density data without blowing out the token context window with massive raw CSV strings.

### 3. Prompt Re-Engineering (`ollama_client.py`)

- Created `build_insight_prompt()` specifically for Pass 2.
- Commanded the model to write professional, concise analyses highlighting _specific numbers_, _entity names_, and _percentage changes_ directly extracted from the provided text summary.
- Enforced a rule that the model must also generate contextually relevant follow-up questions tied to the actual identified data points.

## Verification

- Validated via automated browser testing.
- Before: _"This analysis likely shows that the top-performing brands are driving revenue."_
- After: _"Sports grew by +15.5% YoY, outpacing all other divisions, reaching $325,459 in 2024 compared to $281,746 in 2023."_
