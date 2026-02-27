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
              .py       .py
```

## Module Responsibilities

| Module             | Lines | Responsibility                                                      |
| ------------------ | ----- | ------------------------------------------------------------------- |
| `agent.py`         | ~210  | Page config, session state, chat loop, memory updates               |
| `config.py`        | ~55   | Constants: URLs, model, paths, tool names, colour palette           |
| `data_loader.py`   | ~63   | Load Excel, compute KPIs, build dataset summary                     |
| `ollama_client.py` | ~310  | LLM prompt building, API calls, JSON parsing, validation            |
| `ui.py`            | ~260  | CSS injection, sidebar, welcome screen, chat rendering, suggestions |
| `tools/`           | ~530  | 5 analysis functions + tool router dispatcher                       |

## Data Flow

```
User Question
    │
    ▼
┌────────────┐     ┌─────────────────┐
│  agent.py  │────▶│ ollama_client   │
│ (chat loop)│     │  ask_llm()      │
└─────┬──────┘     └───────┬─────────┘
      │                    │
      │              Ollama API
      │              (localhost:11434)
      │                    │
      │              JSON response
      │              {tool, filters,
      │               insight, suggestions}
      │                    │
      ▼                    ▼
┌────────────┐     ┌─────────────────┐
│   tools/   │◀────│  tool_router()  │
│ (5 tools)  │     └─────────────────┘
└─────┬──────┘
      │
      ▼
  (fig, df, callouts)
      │
      ▼
┌────────────┐
│   ui.py    │
│ (render)   │
└────────────┘
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

## Adding a New Tool

1. Create `tools/new_tool_name.py` with:
   ```python
   def new_tool_name(df, **filters):
       # your analysis logic
       return fig, summary_df
   ```
2. Add the function to `tools/__init__.py`
3. Add `"new_tool_name"` to `VALID_TOOLS` in `config.py`
4. Add a case in `tools/router.py`
5. Update the system prompt in `ollama_client.py` with tool description and trigger phrases
