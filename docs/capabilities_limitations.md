# Agent Capabilities & Limitations

The Private Business Intelligence Agent is a powerful local analysis tool, but it operates under specific architectural constraints.

## Technical Capabilities

1. **Absolute Privacy:** The architecture explicitly prevents data exfiltration. The target data file never leaves your device. The LLM engine (Ollama) runs inside a local daemon process on your hardware.
2. **Intelligent Routing:** The agent translates natural language into 1 of 14 tools (13 analysis tools + 1 out-of-scope handler) via zero-shot JSON extraction, backed by a 3-layer routing safety net (system prompt + `validate_routing()` keyword guard + `extract_missing_filters()` gap filler) to eliminate misroutes.
3. **Multi-Turn Contextual Memory:** The agent successfully retains filter matrices (Region, Brand, Category, Division) across conversational turns until explicitly overwritten or cleared.
4. **Adaptive Insight Generation:** Through its Two-Pass Architecture, textual insights are written by the LLM only _after_ observing a highly compressed representation of actual DataFrame results, guaranteeing narrative accuracy correlated to the math. For tools with deterministic outputs (forecast, price-volume-margin, growth matrix, YoY brand/region), pre-computed plain-text insights bypass Pass 2 entirely — yielding faster responses with zero hallucination risk. Insight text is cleaned of all markdown artifacts and validated against 9 red-flag patterns.
5. **Theme-Aware Data Visualizations:** All Plotly charts and Pandas structures inherit explicitly declared light/dark cascading style sheets to guarantee contrast compliance visually. Historical charts dynamically re-template when the theme is toggled.
6. **Processing State Protection:** All interactive elements (chat input, suggestion buttons, welcome buttons, dark mode toggle) are disabled during response generation to prevent double-submissions, accidental cancellations, and UI resets.
7. **Engaging Loading Experience:** A cycling loading animation with 51 rotating status messages keeps users informed during the two-pass pipeline, replacing the static spinner.

## Known Limitations

1. **Pre-defined Analytics Tooling:** The agent cannot write arbitrary Python code on the fly to answer completely novel queries. It must map your question to one of the 14 predefined tools (13 analysis tools + 1 out-of-scope handler):
   - YoY Comparison
   - Brand x Region Crosstabulation
   - Single-Entity Multi-Year Forecasting
   - Macro Anomaly Detection
   - Price vs Volume vs Margin Clustering
   - Store Performance Analysis
   - Seasonality & Time Trend Analysis
   - Division Mix Analysis
   - Margin Waterfall / Profitability Decomposition
   - KPI Scorecard / Executive Summary
   - Price Elasticity Estimator
   - Competitive Brand Benchmarking
   - Growth-Margin Matrix (BCG-Style)
   - Out-of-Scope Handler (graceful rejection with suggestions)
     If a question falls totally outside these bounds, the out-of-scope handler provides a helpful explanation of why the data cannot answer the question and suggests alternative queries.
2. **Model Token Limits:** The default `llama3.2:3b` model is highly capable but operates on constrained hardware. Excessively long or hyper-complex queries might crash the prompt structure or result in a timeout/failure to generate valid JSON.
3. **Data Dependency:** The agent expects the input data structure to follow a specific schema with designated columns (`Region`, `Division`, `Category`, `Brand`, `Sales`, `Margin`, `Volume`, `Year`). Swapping the dataset for an entirely different schema will require codebase refactoring.
4. **LLM Insight Latency:** Because of the Two-Pass Architecture, processing a complex question requires two distinct sequential inferences from Ollama (Routing + Narration), meaning response times directly scale with local GPU/CPU hardware capabilities.
5. **Statistical Naivety in Forecasting:** The forecasting tool utilizes sklearn’s `LinearRegression` on monthly historical data (2023–2024) to project a 12-month trendline into 2025 with a confidence band. It does not account for seasonality, macro-economic factors, or complex time-series ARIMAs. The pre-computed insight reports the actual regression-derived projected total, monthly range, and annualized growth rate.
