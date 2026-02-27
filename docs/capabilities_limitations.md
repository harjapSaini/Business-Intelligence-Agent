# Capabilities & Limitations

## Capabilities

### What the Agent Can Do

| Capability                   | Description                                                                               |
| ---------------------------- | ----------------------------------------------------------------------------------------- |
| **Natural-language queries** | Ask questions in plain English - the AI picks the right tool                              |
| **5 analysis tools**         | YoY comparison, brand×region heatmap, forecasting, anomaly detection, price-volume-margin |
| **Interactive charts**       | Plotly charts with hover, zoom, and pan                                                   |
| **Follow-up conversations**  | Session memory tracks context for multi-turn conversations                                |
| **Suggestion buttons**       | 3 AI-generated follow-up questions after each response                                    |
| **Data tables**              | View raw numbers behind every chart                                                       |
| **Multiple filters**         | Filter by region, division, brand, category, year, and metric                             |
| **Anomaly callouts**         | Plain-English descriptions of statistical outliers                                        |
| **12-month forecasts**       | Linear regression projections with confidence bands                                       |
| **100% local**               | All data and AI processing stays on your machine                                          |

### Supported Metrics

| Metric        | Description             |
| ------------- | ----------------------- |
| `sales`       | Revenue (price × units) |
| `units`       | Units sold              |
| `margin`      | Profit (sales − COGS)   |
| `margin_rate` | Profit as % of sales    |
| `cogs`        | Cost of goods sold      |

### Supported Filters

| Filter   | Values                                                                 |
| -------- | ---------------------------------------------------------------------- |
| Region   | East, North, South, West                                               |
| Division | Apparel, Food, Gardening, Sports, Tools                                |
| Brand    | Dexon, Fynix, Kryta, Lumix, Novex, Quanta, Solvo, Trion, Vetra, Zentra |
| Category | 12 categories across divisions                                         |
| Year     | 2023, 2024                                                             |

---

## Limitations

### Model Limitations

| Limitation                 | Detail                                                                        |
| -------------------------- | ----------------------------------------------------------------------------- |
| **Response time**          | Each question takes 15–50 seconds (depends on hardware and model cache state) |
| **First query slower**     | ~50s on first query due to model loading; ~20s thereafter                     |
| **3B parameter model**     | May occasionally misinterpret complex or ambiguous questions                  |
| **English only**           | The system prompt and model are optimised for English                         |
| **No image understanding** | Cannot analyse uploaded images or screenshots                                 |

### Data Limitations

| Limitation            | Detail                                                                     |
| --------------------- | -------------------------------------------------------------------------- |
| **Static dataset**    | Uses a fixed Excel file; cannot connect to live databases                  |
| **2 years only**      | Data covers 2023–2024; limited historical depth for forecasting            |
| **Linear forecasts**  | Uses simple linear regression - does not account for seasonality or trends |
| **Z-score anomalies** | Assumes roughly normal distribution; may miss non-Gaussian outliers        |

### Tool Limitations

| Limitation         | Detail                                                                                    |
| ------------------ | ----------------------------------------------------------------------------------------- |
| **5 tools only**   | Cannot perform analyses outside the 5 built-in tools                                      |
| **No custom SQL**  | Cannot run arbitrary queries against the data                                             |
| **No export**      | Charts and tables cannot be downloaded directly (use Plotly's built-in screenshot button) |
| **Single dataset** | Cannot compare across multiple datasets                                                   |

### Session Limitations

| Limitation            | Detail                                                                           |
| --------------------- | -------------------------------------------------------------------------------- |
| **No persistence**    | Conversation is lost when the browser tab is closed                              |
| **Memory is shallow** | Tracks entities and last result only - not full conversation history for the LLM |
| **No authentication** | No user login or access control                                                  |

---

## Accuracy

The LLM chooses the correct tool approximately **90–95% of the time** for straightforward questions. Accuracy may drop for:

- Very vague questions ("Tell me something interesting")
- Questions requiring tools not in the toolkit
- Questions mixing multiple analysis types in one query

When the LLM picks the wrong tool, the fallback mechanisms ensure you still get a valid chart - just not the one you expected. Try rephrasing or being more specific.
