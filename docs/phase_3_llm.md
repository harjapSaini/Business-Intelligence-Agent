# Phase 3: LLM Integration & JSON Routing

## Overview

Phase 3 transformed the application from a static dashboard into an AI-powered agent. The goal was to connect the local `llama3.2:3b` model to the app, enabling it to understand natural language questions and map them to the correct Phase 2 analysis tools.

## Key Implementations

### 1. The Local AI Connection (`ollama_client.py`)

- Hardcoded the `OLLAMA_BASE_URL` and model name into `config.py`.
- Developed the `ask_llm()` function to send HTTP POST requests directly to the local Ollama API, avoiding any external API dependencies and preserving 100% data privacy.
- Implemented `warmup_model()` to silently boot the LLM into RAM on app startup, reducing latency for the user's first question.

### 2. System Prompt Engineering

- Crafted a strict, heavily guided `build_system_prompt()`.
- The prompt explicitly lists all 13 available tools and their required parameters.
- It provides rules on how to interpret ambiguous user queries (e.g., mapping "West Coast" to "West").

### 3. Guaranteed JSON Extraction

- To prevent the LLM from surrounding its JSON payload with markdown (like `json ... `) or conversational filler, `extract_json_from_response()` was written.
- It uses regex parsing to reliably strip out anything that isn't the core JSON payload.

### 4. Schema Validation

- Created `validate_llm_response()` to ensure the returned JSON matches our expected schema (`{'tool': str, 'filters': dict}`).
- Added a fallback mechanism that defaults to the `yoy_comparison` tool if the LLM completely fails to produce valid JSON after processing.

## Verification

- Unit tested the LLM integration by sending various natural language questions and asserting that the returned tool name and filters matched the expected routing logic.
