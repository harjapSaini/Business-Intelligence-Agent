# Phase 4 - Session Memory & Follow-Up Questions

## Overview

Phase 4 adds conversational memory so the agent can understand follow-up questions like _"Now break that down by region"_ or _"What does the forecast look like for that division?"_

## Memory Structure

Stored in `st.session_state.session_memory`:

```python
{
    "entities": {
        "region": "West",
        "brand": "Lumix",
        "division": "Apparel"
    },
    "last_filters": {
        "tool": "yoy_comparison",
        "metric": "sales",
        "division": "Apparel"
    },
    "last_result": {
        "description": "Apparel saw the strongest YoY growth...",
        "top_item": "Novex"
    }
}
```

## How Memory Updates

After each question, `update_memory(llm_response, result_df)`:

1. **Entities merge** - new filter values (region, brand, division, category) are added without overwriting existing ones
2. **Null strings ignored** - `"None"`, `"null"`, `""` are skipped
3. **Last filters stored** - tool name + active filters from the most recent query
4. **Last result captured** - truncated insight text + top item from the result DataFrame

## Chat Interface

### Message Flow

1. User types in `st.chat_input` or clicks a suggestion button
2. `process_question()` runs the full pipeline: LLM → tool router → memory update
3. Message is stored in `st.session_state.messages`
4. Page reruns and renders all messages via `render_chat_message()`

### Message Format

```python
# User message
{"role": "user", "content": "Which division grew the most?"}

# Assistant message
{
    "role": "assistant",
    "tool": "yoy_comparison",
    "insight": "Sports division showed the largest...",
    "suggestions": ["a", "b", "c"],
    "figure": <plotly.Figure>,
    "summary_df": <pandas.DataFrame>,
    "callouts": None,  # only set for anomaly_detection
}
```

## Suggestion Buttons

After each response, 3 follow-up suggestion buttons appear. Clicking one:

1. Sets `st.session_state.pending_question = clicked_text`
2. Triggers `st.rerun()`
3. On rerun, the pending question is processed as a new query

## Clear Conversation

The sidebar "🗑️ Clear Conversation" button resets:

- `messages` → empty list
- `session_memory` → empty dicts
- `pending_question` → None
