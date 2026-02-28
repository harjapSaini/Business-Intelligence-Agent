# Agent Capabilities & Limitations

The Private Business Intelligence Agent is a powerful local analysis tool, but it operates under specific architectural constraints.

## Technical Capabilities

1. **Absolute Privacy:** The architecture explicitly prevents data exfiltration. The target CSV file never leaves your device. The LLM engine (Ollama) runs inside a local daemon process on your hardware.
2. **Intelligent Routing:** The agent translates natural language into 1 of 5 explicit mathematical Python paradigms via zero-shot JSON extraction, eliminating hallucinations in mathematical logic.
3. **Multi-Turn Contextual Memory:** The agent successfully retains filter matrices (Region, Brand, Category, Division) across conversational turns until explicitly overwritten or cleared.
4. **Adaptive Insight Generation:** Through its Two-Pass Architecture, textual insights are written by the LLM only _after_ observing a highly compressed representation of actual DataFrame results, guaranteeing narrative accuracy correlated to the math.
5. **Theme-Aware Data Visualizations:** All Plotly charts and Pandas structures inherit explicitly declared light/dark cascading style sheets to guarantee contrast compliance visually.

## Known Limitations

1. **Pre-defined Analytics Tooling:** The agent cannot write arbitrary Python code on the fly to answer completely novel queries. It must map your question to one of the 5 predefined tools:
   - YoY Comparison
   - Brand x Region Crosstabulation
   - Single-Entity Multi-Year Forecasting
   - Macro Anomaly Detection
   - Price vs Volume vs Margin Clustering
     If a question falls totally outside these bounds, it will attempt to default to a basic YoY comparison.
2. **Model Token Limits:** The default `llama3.2:3b` model is highly capable but operates on constrained hardware. Excessively long or hyper-complex queries might crash the prompt structure or result in a timeout/failure to generate valid JSON.
3. **Data Dependency:** The agent expects the input data structure (`data/mock_retail_data.csv`) to follow a specific schema with designated columns (`Region`, `Division`, `Category`, `Brand`, `Sales`, `Margin`, `Volume`, `Year`). Swapping the dataset for an entirely different schema will require codebase refactoring.
4. **LLM Insight Latency:** Because of the Two-Pass Architecture, processing a complex question requires two distinct sequential inferences from Ollama (Routing + Narration), meaning response times directly scale with local GPU/CPU hardware capabilities.
5. **Statistical Naivety in Forecasting:** The forecasting tool utilizes a simplistic linear regression slope calculated between 2023 and 2024. It does not account for seasonality, macro-economic factors, or complex time-series ARIMAs.
