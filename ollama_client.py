"""
Ollama LLM client for the Private Business Intelligence Agent.

Handles all communication with the local Ollama server:
  - verify_ollama()              - check server + model availability
  - warmup_model()               - pre-load model into memory
  - build_system_prompt()        - construct the LLM system prompt
  - extract_json_from_response() - parse JSON from raw LLM output
  - validate_llm_response()      - fix/default missing keys
  - ask_llm()                    - single LLM call, returns structured dict
"""

import json
import re
import requests
import ollama

from config import OLLAMA_BASE_URL, OLLAMA_MODEL, VALID_TOOLS


# =====================================================================
#  OLLAMA SERVER VERIFICATION & WARMUP
# =====================================================================

def verify_ollama() -> tuple[bool, str]:
    """
    Ping the local Ollama server and check that the required model
    is available.

    Returns:
        (True, model_name)   if Ollama is reachable and model is found
        (False, error_msg)   otherwise
    """
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        resp.raise_for_status()
        models = resp.json().get("models", [])
        model_names = [m.get("name", "") for m in models]

        # The model tag may or may not include ':latest' so check prefix
        for name in model_names:
            if name.startswith(OLLAMA_MODEL):
                return True, name
        return False, (
            f"Model **{OLLAMA_MODEL}** not found. "
            f"Available models: {', '.join(model_names) or 'none'}.\n\n"
            f"Run `ollama pull {OLLAMA_MODEL}` to download it."
        )
    except requests.ConnectionError:
        return False, (
            "**Cannot reach Ollama** at "
            f"`{OLLAMA_BASE_URL}`.\n\n"
            "Make sure Ollama is installed and running:\n"
            "1. Install from [ollama.com](https://ollama.com)\n"
            "2. Start it with `ollama serve`\n"
            f"3. Pull the model: `ollama pull {OLLAMA_MODEL}`"
        )
    except Exception as e:
        return False, f"Unexpected error checking Ollama: {e}"


def warmup_model() -> None:
    """
    Send a tiny prompt to Ollama so the model is loaded into memory
    before the user asks their first question.

    Called once at app startup. This eliminates the ~60s cold-start
    delay on the first real query.
    """
    try:
        ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": "Hi"}],
            options={"num_predict": 1},  # generate only 1 token
        )
    except Exception:
        pass  # if it fails, we'll catch it in ask_llm later


# =====================================================================
#  SYSTEM PROMPT BUILDER
# =====================================================================

def build_system_prompt(df_summary: dict, session_memory: dict = None) -> str:
    """
    Construct the full system prompt for the LLM.

    Includes dataset schema, available tools with trigger phrases,
    valid filter values, JSON response format, and session memory.

    Args:
        df_summary:     Summary dict from get_dataset_summary().
        session_memory: Current session memory dict (may be None/empty).

    Returns:
        str - the complete system prompt.
    """
    # Build memory context block
    memory_block = "No prior context - this is the first question."
    if session_memory and any(session_memory.get(k) for k in ["entities", "last_filters", "last_result"]):
        parts = []
        entities = session_memory.get("entities", {})
        if entities:
            entity_str = ", ".join(f"{k}={v}" for k, v in entities.items() if v)
            if entity_str:
                parts.append(f"Current entities: {entity_str}")
        last_filters = session_memory.get("last_filters", {})
        if last_filters:
            parts.append(f"Last tool used: {last_filters.get('tool', 'unknown')}")
            filter_str = ", ".join(f"{k}={v}" for k, v in last_filters.items() if v and k != 'tool')
            if filter_str:
                parts.append(f"Last filters: {filter_str}")
        last_result = session_memory.get("last_result", {})
        if last_result:
            if last_result.get("description"):
                parts.append(f"Last analysis: {last_result['description']}")
            if last_result.get("top_item"):
                parts.append(f"Top item from last result: {last_result['top_item']}")
        if parts:
            memory_block = "\n".join(parts)

    prompt = f"""You are a Private Business Intelligence Agent for Canadian Tire.
You analyze a dataset with {df_summary['total_rows']:,} rows of retail transaction data.

Dataset columns: YEAR, QUARTER, MONTH, DATE, STORE_ID, STORE_NAME, STORE_SIZE, REGION, PRODUCT_ID, BRAND, PRODUCT_CATEGORY, PRODUCT_DIVISION, PRODUCT_NAME, SELLING_PRICE_PER_UNIT, UNITS_SOLD, COST_PER_UNIT
Derived KPI columns: SALES, COGS, MARGIN, MARGIN_RATE

Available filter values:
- divisions: {df_summary['divisions']}
- regions: {df_summary['regions']}
- categories: {df_summary['categories']}
- brands: {df_summary['brands']}
- metrics: ["sales", "margin", "units", "margin_rate"]
- years: {df_summary['years']}

You have exactly 5 analysis tools. Pick the ONE best tool for each question:

1. "yoy_comparison" - Use for year-over-year comparisons, growth analysis, performance trends.
   Filters: metric, division, region, category, brand (all optional, default metric="sales")
   Triggers: "grew", "vs last year", "year over year", "performance", "top/bottom by", "worst/best"

2. "brand_region_crosstab" - Use for comparing brands across regions, or regional performance by brand.
   Filters: metric (default "sales")
   Triggers: "brands in region", "regional performance", "cross-tab", "heatmap", "which brands"

3. "forecast_trendline" - Use for projections, trends, forecasts into 2025.
   Filters: group_by (one of "division","region","brand","category"), group_value, metric
   Triggers: "project", "forecast", "trend", "trajectory", "predict", "2025"

4. "anomaly_detection" - Use for finding outliers, unusual patterns, anomalies.
   Filters: metric (default "margin_rate"), division, region
   Triggers: "anomaly", "outlier", "unusual", "flag", "looks off", "weird"

5. "price_volume_margin" - Use for price-margin-volume relationships, pricing analysis.
   Filters: division, category
   Triggers: "price", "pricing", "sweet spot", "price vs margin", "relationship between price"

Session memory (context from prior questions):
{memory_block}

IMPORTANT RULES:
- If the user references "that region", "the top brand", "it", etc., resolve from session memory above.
- Always pick the MOST APPROPRIATE tool. When in doubt, use yoy_comparison.
- Your ONLY job is to pick the tool and filters. Do NOT generate insights.

You MUST respond with ONLY a valid JSON object in this EXACT format, nothing else:
{{{{
  "tool": "tool_name_here",
  "filters": {{{{
    "metric": "sales",
    "division": null,
    "region": null,
    "category": null,
    "brand": null,
    "group_by": null,
    "group_value": null
  }}}}
}}}}

Do NOT include any text, explanation, or markdown outside the JSON object.
Do NOT wrap the JSON in code fences.
Respond with ONLY the JSON object."""

    return prompt


# =====================================================================
#  JSON EXTRACTION & VALIDATION
# =====================================================================

def extract_json_from_response(raw_text: str) -> dict:
    """
    Extract a JSON object from raw LLM output.

    Tries multiple strategies:
    1. Direct JSON parse of the full text
    2. Extract from markdown code fences (```json ... ```)
    3. Find the outermost { ... } block via brace matching

    Args:
        raw_text: Raw string response from the LLM.

    Returns:
        dict - parsed JSON object.

    Raises:
        ValueError if no valid JSON can be extracted.
    """
    text = raw_text.strip()

    # Strategy 1: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: extract from markdown code fences
    fence_pattern = r"```(?:json)?\s*\n?(\{.*?\})\s*\n?```"
    fence_match = re.search(fence_pattern, text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 3: find outermost { ... } via brace matching
    start = text.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break

    raise ValueError(f"Could not extract valid JSON from LLM response: {text[:200]}")


def validate_llm_response(parsed: dict) -> dict:
    """
    Validate and fix a parsed LLM JSON response (Pass 1 - routing only).

    Ensures:
    - 'tool' is one of the valid tool names
    - 'filters' exists and has safe defaults

    Args:
        parsed: Dict from JSON parsing.

    Returns:
        dict - validated/corrected response.
    """
    result = dict(parsed)

    # Validate tool name
    if result.get("tool") not in VALID_TOOLS:
        result["tool"] = "yoy_comparison"

    # Ensure filters dict exists
    if not isinstance(result.get("filters"), dict):
        result["filters"] = {"metric": "sales"}

    # Ensure metric has a default
    if not result["filters"].get("metric"):
        result["filters"]["metric"] = "sales"

    return result


def validate_insight_response(parsed: dict) -> dict:
    """
    Validate and fix a parsed LLM JSON response (Pass 2 - insight generation).

    Ensures:
    - 'insight' is a non-empty string
    - 'suggestions' is a list of 3 strings

    Args:
        parsed: Dict from JSON parsing.

    Returns:
        dict - validated/corrected response.
    """
    result = dict(parsed)

    # Ensure insight is a string
    if not isinstance(result.get("insight"), str) or not result["insight"].strip():
        result["insight"] = "Here is the analysis based on the available data."

    # Ensure suggestions is a list of 3 strings
    if not isinstance(result.get("suggestions"), list) or len(result["suggestions"]) < 1:
        result["suggestions"] = [
            "Show me the overall sales trend",
            "Which division performs best?",
            "Are there any anomalies in the data?",
        ]
    # Pad to 3 if fewer
    while len(result["suggestions"]) < 3:
        result["suggestions"].append("Tell me more about this data")
    # Trim to 3 if more
    result["suggestions"] = result["suggestions"][:3]

    return result


# =====================================================================
#  PASS 1: ASK LLM (TOOL ROUTING)
# =====================================================================

def ask_llm(question: str, session_memory: dict, df_summary: dict) -> dict:
    """
    Pass 1: Send a user question to Ollama to pick the right tool + filters.

    Makes exactly ONE LLM call. Returns only tool routing info.
    The actual insight is generated in Pass 2 after the tool runs.

    Args:
        question:       The user's natural-language question.
        session_memory: Current session memory dict.
        df_summary:     Dataset summary from get_dataset_summary().

    Returns:
        dict with keys: 'tool', 'filters'
    """
    system_prompt = build_system_prompt(df_summary, session_memory)

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            options={"temperature": 0.1},  # Low temp for consistent JSON
        )

        raw_text = response["message"]["content"]

        # Try to extract and validate JSON
        parsed = extract_json_from_response(raw_text)
        validated = validate_llm_response(parsed)
        return validated

    except ValueError:
        # JSON extraction failed - return fallback
        return {
            "tool": "yoy_comparison",
            "filters": {"metric": "sales"},
        }
    except Exception as e:
        # Ollama connection or other error - return error fallback
        return {
            "tool": "yoy_comparison",
            "filters": {"metric": "sales"},
            "_error": str(e),
        }


# =====================================================================
#  PASS 2: GENERATE DATA-DRIVEN INSIGHT
# =====================================================================

def build_insight_prompt(question: str, tool_name: str, data_summary: str) -> str:
    """
    Build the system prompt for the second LLM call.

    This prompt gives the LLM the actual data results and asks it to
    write a specific, number-backed business insight.

    Args:
        question:     The user's original question.
        tool_name:    The tool that was used.
        data_summary: Compact text summary of the tool's output.

    Returns:
        str - the system prompt for Pass 2.
    """
    return f"""You are a senior Business Intelligence analyst at Canadian Tire.
You have just run the "{tool_name.replace('_', ' ')}" analysis tool and received real data results.

Here are the ACTUAL DATA RESULTS from the analysis:
---
{data_summary}
---

Based on these real numbers, write a business insight and suggest follow-up questions.

RULES FOR YOUR INSIGHT:
- Reference SPECIFIC numbers, percentages, and entity names from the data above.
- Explain what the numbers MEAN for the business (e.g. "Sports grew 15.5% YoY, outpacing all other divisions, likely driven by seasonal demand.").
- Include business reasoning: WHY might these patterns exist? What should a business leader do about it?
- If there are notable outliers or surprises in the data, call them out.
- Write 3-5 sentences. Be specific and analytical, not vague.
- Do NOT say "likely shows" or "may indicate" - you have the real data, so state facts.

RULES FOR SUGGESTIONS:
- Suggest 3 follow-up questions that reference specific entities from the data.
- Each question should help the user dig deeper into interesting findings.

You MUST respond with ONLY a valid JSON object in this EXACT format:
{{{{
  "insight": "Your 3-5 sentence data-driven business insight here.",
  "suggestions": [
    "Follow-up question 1",
    "Follow-up question 2",
    "Follow-up question 3"
  ]
}}}}

Do NOT include any text outside the JSON object.
Respond with ONLY the JSON object."""


def generate_insight(
    question: str,
    tool_name: str,
    data_summary: str,
) -> dict:
    """
    Pass 2: Generate a data-driven insight using the actual tool results.

    Args:
        question:     The user's original question.
        tool_name:    The tool that produced the results.
        data_summary: Compact text summary of the tool's DataFrame output.

    Returns:
        dict with keys: 'insight', 'suggestions'
    """
    system_prompt = build_insight_prompt(question, tool_name, data_summary)

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            options={"temperature": 0.3},  # Slightly higher for natural writing
        )

        raw_text = response["message"]["content"]
        parsed = extract_json_from_response(raw_text)
        validated = validate_insight_response(parsed)
        return validated

    except Exception:
        # If Pass 2 fails, use the data summary directly as the insight
        return {
            "insight": (
                f"Here are the key findings from the analysis:\n\n{data_summary}"
            ),
            "suggestions": [
                "Show me the overall sales trend",
                "Which division performs best?",
                "Are there any anomalies in the data?",
            ],
        }
