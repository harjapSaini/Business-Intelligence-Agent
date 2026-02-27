# Phase 3 - LLM Integration & JSON Router

## Overview

Phase 3 connects the Ollama LLM to the analysis tools. The user asks a natural-language question, the LLM selects the right tool and filters, and returns a structured JSON response.

## Flow

```
User question
    ↓
build_system_prompt(summary, memory)
    ↓
Ollama API (llama3.2:3b)
    ↓
extract_json_from_response(raw_text)
    ↓
validate_llm_response(parsed_json)
    ↓
{ tool, filters, insight, suggestions }
```

## System Prompt

`build_system_prompt(summary, session_memory)` creates a detailed prompt containing:

1. **Role definition** - "You are a retail analytics assistant for Canadian Tire"
2. **Dataset schema** - column names, KPIs, dimensions
3. **Tool descriptions** - what each tool does and when to use it
4. **Trigger phrases** - keywords that hint at each tool
5. **Filter values** - valid regions, divisions, brands, categories, years
6. **JSON format** - exact structure the LLM must output
7. **Session memory** - previous entities, filters, and results for context

## JSON Response Format

The LLM must return:

```json
{
  "tool": "yoy_comparison",
  "filters": {
    "metric": "sales",
    "region": null,
    "division": "Apparel"
  },
  "insight": "Apparel saw the strongest YoY growth at 12%...",
  "suggestions": [
    "How does Apparel compare across regions?",
    "What brands drive Apparel growth?",
    "Project Apparel sales into 2025"
  ]
}
```

## JSON Extraction

`extract_json_from_response(text)` handles messy LLM output:

1. Tries `json.loads(text)` directly
2. Looks for ```json fenced blocks
3. Searches for `{...}` patterns via regex
4. Raises `ValueError` if no valid JSON found

## Validation & Fallback

`validate_llm_response(data)` ensures the response is always usable:

| Field                      | Fix                              |
| -------------------------- | -------------------------------- |
| `tool` not in VALID_TOOLS  | Default to `"yoy_comparison"`    |
| `filters` missing          | Default to `{"metric": "sales"}` |
| `insight` missing/empty    | Default message                  |
| `suggestions` wrong length | Pad to 3 or trim to 3            |

## Model Warm-up

`warmup_model()` sends a tiny prompt to Ollama on app startup so the model is loaded into GPU/RAM before the first real question. This reduces the first-query latency from ~60s to ~20s.

## Error Handling

If the Ollama API call fails entirely (network error, timeout), `ask_llm()` returns a valid fallback response with:

- `tool: "yoy_comparison"`
- A generic insight
- 3 generic suggestion questions
