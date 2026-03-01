# Architecture Overview

## Module Diagram

```
┌─────────────────────────────────────────────────┐
│                   agent.py                       │
│         Entry point & chat orchestration         │
│                                                  │
│  init_session_state()                            │
│  update_memory()                                 │
│  process_question() ────────────────────┐        │
│  main()                                 │        │
└─────────┬───────┬───────┬───────┬───────┼────────┘
          │       │       │       │       │
          ▼       ▼       ▼       ▼       ▼
     config   data_    ollama_   ui    tools/
      .py    loader    client   .py   package
              .py       .py               │
                                          ▼
                                     insight_
                                     builder.py
```

## Module Responsibilities

| Module               | Responsibility                                               |
| -------------------- | ------------------------------------------------------------ |
| `agent.py`           | Page config, session state, processing gate, chat loop, 2-pass orchestration, pre_computed_insight bypass with `clean_insight_text()` safety net |
| `config.py`          | Constants: URLs, model, paths, tool names, colour palettes   |
| `data_loader.py`     | Load Excel/CSV, compute KPIs, build dataset summary          |
| `ollama_client.py`   | Pass 1 (Router Prompt), Pass 2 (Insight Prompt), API calls, `validate_routing()`, `extract_missing_filters()` |
| `insight_builder.py` | Summarizes raw DataFrame outputs into dense text for the LLM |
| `ui.py`              | CSS injection, dark/light mode toggle, sidebars, loading animation, chat rendering, suggestion buttons |
| `tools/`             | 13 analysis functions + out-of-scope handler + tool router dispatcher; select tools return pre-computed plain-text insights (3-tuple) to bypass Pass 2 LLM |

## Data Flow (Two-Pass LLM Architecture)

```
User Question
    │
    ▼
┌──────────────────┐
│     agent.py     │
│  (chat loop)     │
└────────┬─────────┘
         │
         ▼
[PASS 1: ROUTING] ───────────────▶ Ollama API (localhost:11434)
         │                              │
         │                              ▼
         │                        {tool, filters}
         ▼
┌──────────────────┐
│  tool_router()   │
│   (in tools/)    │
└────────┬─────────┘
         │
         ▼
  Returns: fig, df, pre_computed_insight (optional)
         │
         ├── Has pre_computed_insight? ──▶ YES ──▶ clean_insight_text()
         │                                             │
         │                                             ▼
         │                                      Skip Pass 2
         │                                      Use pre-computed text
         │                                             │
         └── NO (pre_computed is empty)                │
                  │                                    │
                  ▼                                    │
         ┌──────────────────┐                          │
         │insight_builder.py│                          │
         │  (summarize_*)   │                          │
         └────────┬─────────┘                          │
                  │                                    │
                  ▼                                    │
         [PASS 2: INSIGHT] ──▶ Ollama API              │
                  │                │                   │
                  │                ▼                   │
                  │         Narrative insight &        │
                  │         Follow-up questions        │
                  ▼                                    ▼
         ┌─────────────────────────────────────────────┐
         │                  ui.py                       │
         │          (Render charts and text)            │
         └─────────────────────────────────────────────┘
```

## Key Design Decisions

| Decision                       | Rationale                                                                                        |
| ------------------------------ | ------------------------------------------------------------------------------------------------ |
| **Modular files**              | Each concern in its own file for readability and testability                                     |
| **tools/ as package**          | One file per tool - easy to add new tools without touching other files                           |
| **Config centralisation**      | All constants in one place - change model, colours, etc. without hunting through code            |
| **Session state for memory**   | Streamlit reruns the script on every interaction; session state persists across reruns           |
| **JSON over function calling** | The 3B model doesn't support native function calling; structured JSON prompting is more reliable |
| **Multi-layer fallback**       | LLM may fail → JSON parsing may fail → validation catches everything → always a valid response   |
| **Local-first**                | Ollama runs locally; no data leaves the device; satisfies enterprise security requirements       |
| **3-layer routing safety**     | System prompt + `validate_routing()` keyword guard + `extract_missing_filters()` gap filler ensures the right tool runs with correct filters |
| **Processing state gate**      | `st.session_state.processing` disables all interactive elements (input, toggles, buttons) during pipeline execution to prevent double-submissions and UI resets |
| **st.html() for insights**     | Bypasses Streamlit's markdown parser which misinterprets number/comma patterns as code spans     |
| **Pre-computed insights**      | Tools with deterministic outputs (forecast, PVM, growth matrix, YoY) return plain-text insights directly, skipping Pass 2 LLM entirely for faster, more accurate responses |

## Adding a New Tool

1. Create `tools/new_tool_name.py` with:
   ```python
   def new_tool_name(df, **filters):
       # your analysis logic
       # Return 2-tuple (LLM generates insight via Pass 2):
       return fig, summary_df
       # OR return 3-tuple with pre-computed insight (skips Pass 2):
       return fig, summary_df, pre_computed_insight_string
   ```
2. Add the function to `tools/__init__.py`
3. Add `"new_tool_name"` to `VALID_TOOLS` in `config.py`
4. Add a case in `tools/router.py` — unpack 2-tuple or 3-tuple accordingly
5. Update the system prompt in `ollama_client.py` with tool description and trigger phrases
6. Add a `summarize_*()` function + `elif` branch in `insight_builder.py` (only needed if using Pass 2; pre-computed insights bypass this)
