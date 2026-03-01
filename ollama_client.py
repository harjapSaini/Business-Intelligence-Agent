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

    prompt = f"""You are a Private Business Intelligence Agent.
You analyze a retail dataset with {df_summary['total_rows']:,} rows.

=== SECTION 1: TOOL DEFINITIONS ===

You have exactly 14 tools. You MUST pick the ONE best tool for each question.

TOOL 1: "yoy_comparison"
  Description: Year-over-year comparisons, growth analysis, performance by division/region/brand.
  Filters: metric (sales/margin/units/margin_rate), group_by (division/brand/region/category, default: division)
  Example questions:
    - "Which division grew the most year over year?"
    - "Which brand grew the most year over year?"  (group_by: brand)
    - "How did Apparel perform compared to last year?"
    - "What is the sales growth rate by region?"  (group_by: region)
    - "Show me 2023 vs 2024 performance"
    - "Which region had the worst decline?"
  Strong keywords: "grew", "growth", "year over year", "yoy", "vs last year", "2023 vs 2024", "change over time", "how did X perform"

TOOL 2: "brand_region_crosstab"
  Description: Compare brands across regions, rank brands by a metric, brand performance analysis.
  Example questions:
    - "Show me the top brands by sales in the West region"
    - "Which brands perform best in the North?"
    - "Show me Novex sales across all regions"
    - "What are the best-selling brands?"
    - "How do brands compare by region?"
  Strong keywords: "brand", "brands", "top brands", "best brands", "which brands", "brand performance", "Novex", "Vetra", "Trion", "Zentra", "Dexon", "Fynix", "Kryta", "Lumix", "Quanta", "Solvo"

TOOL 3: "forecast_trendline"
  Description: Project future performance, 2025 forecasts, trend analysis.
  Example questions:
    - "Project Apparel division sales into 2025"
    - "What will West region sales look like next year?"
    - "Forecast Sports division trajectory"
    - "Predict 2025 margin for Gardening"
    - "What is the sales trend for Tools?"
  Strong keywords: "project", "forecast", "2025", "future", "trajectory", "predict", "next year", "going forward"

TOOL 4: "anomaly_detection"
  Description: Find outliers, unusual patterns, data anomalies.
  Example questions:
    - "Are there any pricing anomalies in Sports?"
    - "Flag any unusual margin patterns"
    - "What looks off in the data?"
    - "Find outliers in the West region"
    - "Any weird sales patterns?"
  Strong keywords: "anomaly", "anomalies", "outlier", "unusual", "flag", "weird", "unexpected", "looks off", "strange"

TOOL 5: "price_volume_margin"
  Description: Price-margin-volume relationships, pricing sweet spot analysis.
  Example questions:
    - "What is the pricing sweet spot for Tools?"
    - "Show me price vs margin relationship in Apparel"
    - "How does price relate to volume in Sports?"
    - "Where is the optimal price point?"
    - "Visualize the price-volume-margin tradeoff"
  Strong keywords: "pricing", "sweet spot", "price vs margin", "price point", "price relationship", "price volume"

TOOL 6: "store_performance"
  Description: Store-level analysis — top/bottom stores, store size vs performance.
  Example questions:
    - "Which stores are underperforming?"
    - "Show me the top 10 stores by sales"
    - "Do larger stores perform better?"
    - "Which locations are the worst?"
    - "Bottom 5 stores by margin"
  Strong keywords: "store", "stores", "location", "underperforming", "top stores", "bottom stores", "store size"

TOOL 7: "seasonality_trends"
  Description: Monthly or quarterly seasonal patterns overlaid across years.
  Example questions:
    - "Is there a seasonal pattern in Gardening?"
    - "Which month has peak sales?"
    - "Show me quarterly trends for Sports"
    - "When do sales peak?"
    - "Compare monthly patterns 2023 vs 2024"
  Strong keywords: "season", "seasonal", "monthly", "quarterly", "peak", "which month", "which quarter", "time trend"

TOOL 8: "division_mix"
  Description: Revenue mix by division, portfolio share, how divisions split total business.
  Example questions:
    - "What percentage of sales does each division represent?"
    - "Show me the revenue mix"
    - "How is the portfolio balanced?"
    - "Which division has the biggest share?"
    - "Division proportion of total sales"
  Strong keywords: "mix", "percentage", "share", "proportion", "portfolio balance", "revenue mix", "each division represent"

TOOL 9: "margin_waterfall"
  Description: Decompose YoY margin/sales changes — what drove the change.
  Example questions:
    - "Why did our margins change?"
    - "What drove the sales increase?"
    - "Break down the margin change by division"
    - "Which divisions contributed to profit growth?"
    - "Show me a waterfall of margin changes"
  Strong keywords: "waterfall", "what drove", "why did margin", "margins change", "decomposition", "break down", "contributed"

TOOL 10: "kpi_scorecard"
  Description: Full-business executive overview, health check, KPI dashboard. NO filters needed.
  Example questions:
    - "How is the business performing overall?"
    - "Give me a KPI dashboard"
    - "Executive summary of the business"
    - "Show me the scorecard"
    - "Summarize everything"
  Strong keywords: "overall", "overview", "scorecard", "dashboard", "health", "kpi", "summarize everything", "how is the business"

TOOL 11: "price_elasticity"
  Description: Estimate price sensitivity, demand elasticity, impact of price changes.
  Example questions:
    - "Which categories are most price sensitive?"
    - "What is the price elasticity for Sports?"
    - "What happens if we raise prices?"
    - "How sensitive is demand to price?"
    - "Impact of price change on volume"
  Strong keywords: "elasticity", "price sensitive", "raise prices", "demand sensitivity", "impact of price change"

TOOL 12: "brand_benchmarking"
  Description: Head-to-head brand comparisons within categories, market share by brand.
  Example questions:
    - "Which brand owns the Fitness category?"
    - "Compare brands in Gardening"
    - "Who dominates Apparel by market share?"
    - "Brand head-to-head in Tools"
    - "Which brand leads in Sports?"
  Strong keywords: "who owns", "brand dominance", "head-to-head", "benchmarking", "which brand leads", "compare brands", "brand vs"

TOOL 13: "growth_margin_matrix"
  Description: BCG-style strategic 2x2 matrix — stars, cash cows, question marks, dogs.
  Example questions:
    - "Where are our stars and dogs?"
    - "Show me the BCG matrix"
    - "Which divisions should we invest in?"
    - "Strategic portfolio view"
    - "Growth vs margin quadrant analysis"
  Strong keywords: "stars", "dogs", "cash cows", "BCG", "quadrant", "portfolio strategy", "growth margin matrix", "invest"

TOOL 14: "out_of_scope"
  Description: Use this when the question asks for data or metrics that do not exist in this dataset.
  Use when question asks about:
    - Customer-level data (average order value, customer count, repeat purchases, customer lifetime value, churn)
    - Inventory or stock levels
    - Competitor data or external benchmarks
    - Employee or HR data
    - Website traffic or digital metrics
    - Any metric requiring data not in the available tables
  Example questions:
    - "What is the average order value?"
    - "How many customers do we have?"
    - "What is the customer retention rate?"
    - "How does our pricing compare to competitors?"
  Strong keywords: "average order value", "aov", "customer count", "number of customers", "retention", "churn", "inventory", "stock level", "competitor", "website traffic"

=== SECTION 2: FILTER EXTRACTION RULES ===

Extract ALL filters mentioned in the question. Never return an empty filters object. Always include at minimum the metric field.

Valid filter values — extract EXACTLY as written:
- region: ONLY one of {df_summary['regions']} — or null if not mentioned
- division: ONLY one of {df_summary['divisions']} — or null if not mentioned
- category: ONLY one of {df_summary['categories']} — or null if not mentioned
- brand: ONLY one of {df_summary['brands']} — or null if not mentioned
- metric: ONLY one of ["sales", "margin", "units", "margin_rate"] — DEFAULT to "sales" if not specified
- group_by: one of ["division", "region", "brand", "category"] — or null
- group_value: string matching a specific value for group_by — or null
- time_grain: "month" or "quarter" — or null
- top_n: integer if user says "top 5", "top 10" etc — or null
- view: "top" or "bottom" — or null

If the user says "West" → region: "West"
If the user says "Apparel" → division: "Apparel"
If the user says "Novex" → brand: "Novex"
If the user says "margin" → metric: "margin"

=== SECTION 3: WORKED EXAMPLES ===

Q: "Show me the top brands by sales in the West region"
A: {{{{"tool": "brand_region_crosstab", "filters": {{"region": "West", "metric": "sales"}}}}}}

Q: "Which division grew the most year over year?"
A: {{{{"tool": "yoy_comparison", "filters": {{"metric": "sales", "group_by": "division"}}}}}}

Q: "Which brand grew the most year over year?"
A: {{{{"tool": "yoy_comparison", "filters": {{"metric": "sales", "group_by": "brand"}}}}}}

Q: "How did Apparel perform compared to last year in the East?"
A: {{{{"tool": "yoy_comparison", "filters": {{"division": "Apparel", "region": "East", "metric": "sales"}}}}}}

Q: "Which brands perform best in the North region?"
A: {{{{"tool": "brand_region_crosstab", "filters": {{"region": "North", "metric": "sales"}}}}}}

Q: "Project West region sales into 2025"
A: {{{{"tool": "forecast_trendline", "filters": {{"group_by": "region", "group_value": "West", "metric": "sales"}}}}}}

Q: "Are there any pricing anomalies in the Sports division?"
A: {{{{"tool": "anomaly_detection", "filters": {{"division": "Sports", "metric": "margin_rate"}}}}}}

Q: "What is the relationship between price and margin in Apparel?"
A: {{{{"tool": "price_volume_margin", "filters": {{"division": "Apparel", "metric": "sales"}}}}}}

Q: "Show me Novex sales across all regions"
A: {{{{"tool": "brand_region_crosstab", "filters": {{"brand": "Novex", "metric": "sales"}}}}}}

Q: "Which stores are underperforming?"
A: {{{{"tool": "store_performance", "filters": {{"metric": "sales", "view": "bottom", "top_n": 10}}}}}}

Q: "How is the business performing overall?"
A: {{{{"tool": "kpi_scorecard", "filters": {{"metric": "sales"}}}}}}

Q: "Why did our margins change?"
A: {{{{"tool": "margin_waterfall", "filters": {{"metric": "margin", "group_by": "division"}}}}}}

Q: "Is there a seasonal pattern in Gardening?"
A: {{{{"tool": "seasonality_trends", "filters": {{"division": "Gardening", "metric": "sales", "time_grain": "month"}}}}}}

Q: "Where are our stars and dogs?"
A: {{{{"tool": "growth_margin_matrix", "filters": {{"metric": "sales", "group_by": "division"}}}}}}

Q: "Which brands are driving the Apparel decline?"
A: {{{{"tool": "yoy_comparison", "filters": {{"group_by": "brand", "division": "Apparel", "metric": "sales"}}}}}}

Q: "Which brands are underperforming in Sports?"
A: {{{{"tool": "yoy_comparison", "filters": {{"group_by": "brand", "division": "Sports", "metric": "sales"}}}}}}

Q: "What is causing the Tools decline?"
A: {{{{"tool": "yoy_comparison", "filters": {{"group_by": "brand", "division": "Tools", "metric": "sales"}}}}}}

Q: "Which region has the most growth opportunity and what is driving it?"
A: {{{{"tool": "yoy_comparison", "filters": {{"group_by": "region", "metric": "sales"}}}}}}

Q: "How are the different regions performing?"
A: {{{{"tool": "yoy_comparison", "filters": {{"group_by": "region", "metric": "sales"}}}}}}

Q: "Which region is growing fastest?"
A: {{{{"tool": "yoy_comparison", "filters": {{"group_by": "region", "metric": "sales"}}}}}}

=== SECTION 4: OUTPUT FORMAT RULES ===

Session memory (context from prior questions):
{memory_block}

- If the user references "that region", "the top brand", "it", etc., resolve from session memory above.
- Your ONLY job is to pick the tool and extract filters. Do NOT generate insights or suggestions.

You MUST always return valid JSON and nothing else. No explanation before or after the JSON. No markdown code blocks. No backticks. Raw JSON only.

The JSON must contain exactly these 2 keys:
- "tool" (string — one of the 13 tool names above)
- "filters" (object — never empty, always include metric)

If you are unsure which tool to pick:
- If the question mentions brands → use "brand_region_crosstab"
- If the question mentions growth or time periods → use "yoy_comparison"
- Otherwise default to "yoy_comparison"

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


# =====================================================================
#  ROUTING GUARD & FILTER EXTRACTION (Safety nets for the small LLM)
# =====================================================================

# Brand names from the dataset — used by keyword guard
_BRAND_NAMES = [
    "novex", "vetra", "trion", "zentra", "dexon",
    "fynix", "kryta", "lumix", "quanta", "solvo",
]

# Canonical filter values for extraction fallback
_REGIONS = ["East", "West", "North", "South"]
_DIVISIONS = ["Apparel", "Tools", "Sports", "Gardening", "Food"]
_CATEGORIES = [
    "Shirts", "Shoes", "Power Tools", "Team Sports", "Decor",
    "Beverages", "Plants", "Pantry", "Snacks", "Safety Gear",
    "Garden Tools", "Fitness",
]
_BRANDS_TITLE = ["Novex", "Vetra", "Trion", "Zentra", "Dexon",
                 "Fynix", "Kryta", "Lumix", "Quanta", "Solvo"]
_METRICS = ["sales", "margin", "margin_rate", "units"]
_GROUP_BY_VALUES = ["division", "brand", "region", "category"]
_TIME_GRAINS = ["month", "quarter"]


def validate_routing(question: str, llm_tool: str) -> str:
    """
    Safety net that overrides incorrect LLM tool selection
    based on keyword matching.  Runs before tool_router.

    Checks keywords in priority order — specialised tools first,
    generic yoy_comparison last.
    """
    q = question.lower()

    # ── Out-of-scope — highest priority ─────────────────────
    out_of_scope_kw = [
        "average order value", "aov", "customer count",
        "number of customers", "how many customers",
        "retention rate", "churn", "clv", "lifetime value",
        "inventory", "stock level", "reorder", "competitor",
        "market share", "website traffic", "digital", "online sales",
        "foot traffic", "employee", "headcount",
    ]
    if any(kw in q for kw in out_of_scope_kw):
        return "out_of_scope"

    # ── Brand keywords — highest tool priority ─────────────
    brand_keywords = [
        "brand", "brands", "top brands", "best brands", "which brands",
        "brand performance",
    ] + _BRAND_NAMES
    if any(kw in q for kw in brand_keywords):
        # But NOT if the question is really about YoY brand growth/decline
        yoy_signals = [
            "year over year", "yoy", "grew", "growth rate",
            "vs last year", "compared to last year",
            "2023 vs 2024", "change over time",
            "decline", "declining", "fell", "dropped",
            "decreased", "worst performing", "underperforming",
            "driving the", "causing the", "behind the",
        ]
        if any(yw in q for yw in yoy_signals):
            return "yoy_comparison"
        return "brand_region_crosstab"

    # ── KPI / overview ──────────────────────────────────────
    overview_kw = ["overall", "overview", "scorecard", "dashboard",
                   "health", "kpi", "summarize everything",
                   "how is the business"]
    if any(kw in q for kw in overview_kw):
        return "kpi_scorecard"

    # ── Waterfall / margin decomposition ────────────────────
    waterfall_kw = ["waterfall", "what drove", "why did margin",
                    "margins change", "decomposition", "break down",
                    "margin change", "contributed to"]
    if any(kw in q for kw in waterfall_kw):
        return "margin_waterfall"

    # ── Region analysis — before BCG to prevent "growth" collision ─
    region_analysis_kw = [
        "which region", "region has", "region with", "regions performing",
        "regional performance", "regional growth", "regional opportunity",
        "best region", "worst region", "region growing",
        "growth opportunity", "most opportunity", "where should we invest",
        "region comparison", "how are regions",
    ]
    if any(kw in q for kw in region_analysis_kw):
        return "yoy_comparison"

    # ── BCG / growth-margin matrix ──────────────────────────
    bcg_kw = ["stars", "dogs", "cash cow", "bcg", "quadrant",
              "growth margin matrix", "portfolio strategy"]
    if any(kw in q for kw in bcg_kw):
        return "growth_margin_matrix"

    # ── Elasticity ──────────────────────────────────────────
    elasticity_kw = ["elasticity", "price sensitive", "raise prices",
                     "demand sensitivity", "impact of price change"]
    if any(kw in q for kw in elasticity_kw):
        return "price_elasticity"

    # ── Seasonality ─────────────────────────────────────────
    season_kw = ["season", "seasonal", "monthly", "quarterly",
                 "peak", "which month", "which quarter", "time trend"]
    if any(kw in q for kw in season_kw):
        return "seasonality_trends"

    # ── Store performance ───────────────────────────────────
    store_kw = ["store", "stores", "location", "locations",
                "underperforming", "top stores", "bottom stores",
                "store size"]
    if any(kw in q for kw in store_kw):
        return "store_performance"

    # ── Division mix ────────────────────────────────────────
    mix_kw = ["mix", "percentage", "proportion", "portfolio balance",
              "revenue mix", "each division represent"]
    if any(kw in q for kw in mix_kw):
        # Exclude if it's about YoY share *change*
        yoy_signals = ["year over year", "yoy", "grew", "growth",
                       "vs last year", "change"]
        if not any(yw in q for yw in yoy_signals):
            return "division_mix"

    # ── Forecast ────────────────────────────────────────────
    forecast_kw = ["project", "forecast", "2025", "future",
                   "trajectory", "predict", "next year",
                   "going forward"]
    if any(kw in q for kw in forecast_kw):
        return "forecast_trendline"

    # ── Anomaly ─────────────────────────────────────────────
    anomaly_kw = ["anomal", "outlier", "unusual", "anything off",
                  "flag", "weird", "unexpected", "looks off",
                  "strange"]
    if any(kw in q for kw in anomaly_kw):
        return "anomaly_detection"

    # ── Price / PVM ─────────────────────────────────────────
    price_kw = ["pricing", "sweet spot", "price vs margin",
                "price point", "price sensitivity",
                "price volume", "price relationship"]
    if any(kw in q for kw in price_kw):
        return "price_volume_margin"

    # ── Brand benchmarking ──────────────────────────────────
    bench_kw = ["who owns", "brand dominance", "head-to-head",
                "benchmarking", "which brand leads",
                "compare brands", "brand vs"]
    if any(kw in q for kw in bench_kw):
        return "brand_benchmarking"

    # ── YoY (last resort explicit check) ────────────────────
    yoy_kw = ["year over year", "yoy", "grew", "growth rate",
              "vs last year", "compared to last year",
              "2023 vs 2024", "change over time", "perform last year"]
    if any(kw in q for kw in yoy_kw):
        return "yoy_comparison"

    # No keywords matched — trust LLM
    return llm_tool


def extract_missing_filters(question: str, existing_filters: dict) -> dict:
    """
    Scan the question for filter values the LLM missed.
    Fills gaps without overwriting correct LLM-extracted values.

    Covers ALL filters used across all 13 tools:
      region, division, category, brand, metric, group_by,
      group_value, time_grain, top_n, view, year
    """
    q = question.lower()
    filters = existing_filters.copy()

    # ── region ──────────────────────────────────────────────────────────
    if not filters.get("region") or str(filters["region"]).lower() in ("null", "none"):
        for region in _REGIONS:
            if region.lower() in q:
                filters["region"] = region
                break

    # ── division ─────────────────────────────────────────────────────────
    if not filters.get("division") or str(filters["division"]).lower() in ("null", "none"):
        for division in _DIVISIONS:
            if division.lower() in q:
                filters["division"] = division
                break

    # ── category ─────────────────────────────────────────────────────────
    if not filters.get("category") or str(filters["category"]).lower() in ("null", "none"):
        for cat in _CATEGORIES:
            if cat.lower() in q:
                filters["category"] = cat
                break

    # ── brand ─────────────────────────────────────────────────────────────
    if not filters.get("brand") or str(filters["brand"]).lower() in ("null", "none"):
        for brand in _BRANDS_TITLE:
            if brand.lower() in q:
                filters["brand"] = brand
                break

    # ── metric ───────────────────────────────────────────────────────────
    if not filters.get("metric") or str(filters["metric"]).lower() in ("null", "none"):
        if any(w in q for w in ["margin rate", "margin_rate"]):
            filters["metric"] = "margin_rate"
        elif "margin" in q:
            filters["metric"] = "margin"
        elif any(w in q for w in ["units", "unit sold", "units sold", "volume"]):
            filters["metric"] = "units"
        else:
            filters["metric"] = "sales"  # always default to sales

    # ── group_by ─────────────────────────────────────────────────────────
    # Used by: yoy_comparison, margin_waterfall, growth_margin_matrix, forecast_trendline
    if not filters.get("group_by") or str(filters["group_by"]).lower() in ("null", "none"):
        # Region-level analysis phrases → group by region
        region_analysis_kw = [
            "which region", "region has", "region with", "regions performing",
            "regional performance", "regional growth", "regional opportunity",
            "best region", "worst region", "region growing",
            "growth opportunity", "most opportunity", "where should we invest",
            "region comparison", "how are regions",
        ]
        if any(kw in q for kw in region_analysis_kw) and not filters.get("region"):
            filters["group_by"] = "region"
        elif any(w in q for w in ["brand", "brands"]):
            filters["group_by"] = "brand"
            # If a division is also mentioned, keep it as a filter
            # (division filter already extracted above — no change needed)
        elif any(w in q for w in ["category", "categories"]):
            filters["group_by"] = "category"
        elif any(w in q for w in ["region", "regions"]) and not filters.get("region"):
            # "Which region grew most?" → group by region
            # "How did East perform?" → filter by region (already set above), default group
            filters["group_by"] = "region"
        elif filters.get("division"):
            # If a division is already filtered, group within it by category
            filters["group_by"] = "category"
        else:
            filters["group_by"] = "division"  # safe default

    # ── group_value ──────────────────────────────────────────────────────
    # Used by forecast_trendline: e.g. "Project West region" → group_by=region, group_value=West
    if not filters.get("group_value") or str(filters["group_value"]).lower() in ("null", "none"):
        gb = filters.get("group_by", "")
        if gb == "region" and filters.get("region"):
            filters["group_value"] = filters["region"]
        elif gb == "division" and filters.get("division"):
            filters["group_value"] = filters["division"]
        elif gb == "brand" and filters.get("brand"):
            filters["group_value"] = filters["brand"]
        elif gb == "category" and filters.get("category"):
            filters["group_value"] = filters["category"]

    # ── time_grain ───────────────────────────────────────────────────────
    # Used by: seasonality_trends, forecast_trendline
    if not filters.get("time_grain") or str(filters["time_grain"]).lower() in ("null", "none"):
        if any(w in q for w in ["quarter", "quarterly", "q1", "q2", "q3", "q4"]):
            filters["time_grain"] = "quarter"
        elif any(w in q for w in ["month", "monthly", "january", "february", "march",
                                   "april", "may", "june", "july", "august",
                                   "september", "october", "november", "december"]):
            filters["time_grain"] = "month"
        # No default — tools handle null gracefully (default to month internally)

    # ── top_n ────────────────────────────────────────────────────────────
    # Used by: brand_region_crosstab, store_performance, yoy_comparison, brand_benchmarking
    if not filters.get("top_n") or str(filters["top_n"]).lower() in ("null", "none"):
        import re as _re
        match = _re.search(r"top\s+(\d+)", q)
        if match:
            filters["top_n"] = int(match.group(1))
        elif "bottom" in q:
            # "bottom 5" pattern
            match = _re.search(r"bottom\s+(\d+)", q)
            if match:
                filters["top_n"] = int(match.group(1))
        # No default — tools use their own defaults (usually 5 or 10)

    # ── view ─────────────────────────────────────────────────────────────
    # Used by: store_performance, yoy_comparison, brand_region_crosstab
    if not filters.get("view") or str(filters["view"]).lower() in ("null", "none"):
        if any(w in q for w in ["bottom", "worst", "underperform", "lowest",
                                  "weakest", "lagging"]):
            filters["view"] = "bottom"
        elif any(w in q for w in ["top", "best", "highest", "leading", "strongest"]):
            filters["view"] = "top"
        # No default — tools handle null (usually show both or top)

    # ── year ─────────────────────────────────────────────────────────────
    # Used by: yoy_comparison, brand_region_crosstab, store_performance
    if not filters.get("year") or str(filters["year"]).lower() in ("null", "none"):
        if "2023" in q:
            filters["year"] = 2023
        elif "2024" in q:
            filters["year"] = 2024
        # No default — null means use both years (correct for most YoY tools)

    return filters


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


def clean_insight_text(text: str) -> str:
    """
    Aggressively removes all markdown formatting from LLM insight text.
    Uses direct string replacement for backticks before regex runs
    to catch all possible backtick patterns the LLM may produce.
    """
    # STEP 1 — Direct string replacement for backticks (catches everything)
    # Remove triple backticks and any language hints (```python, ```json etc)
    while '```' in text:
        text = re.sub(r'```[a-zA-Z]*', '', text)
        text = text.replace('```', '')

    # Remove ALL remaining single backticks — just strip them entirely
    text = text.replace('`', '')

    # STEP 2 — Remove bold markdown
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)

    # STEP 3 — Remove italic markdown
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)

    # STEP 4 — Remove markdown headers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # STEP 5 — Normalize whitespace
    text = re.sub(r'  +', ' ', text)
    text = re.sub(r'\n+', ' ', text)

    return text.strip()


def validate_insight_format(insight: str, filters: dict) -> str:
    """
    Validate that the insight is proper narrative text.
    Returns a clean fallback if the insight looks like structured data.
    """
    # Red flags that indicate structured data leaked into insight
    red_flags = [
        "Best region: Value",
        "Regional totals:",
        "Bottom 3",
        "Top 5 brands:",
        "Top 10 brands:",
        "Here are the key findings",
        "_value",
        ": Value (",
        "\u2022",  # bullet •
    ]

    has_red_flag = any(flag in insight for flag in red_flags)
    too_long = len(insight) > 600
    too_many_bullets = insight.count("\u2022") > 2 or insight.count("- ") > 3

    if has_red_flag or too_long or too_many_bullets:
        region = filters.get("region", "all regions")
        metric = filters.get("metric", "sales")
        return (
            f"Analysis complete for {region}. "
            f"The chart above shows the full breakdown by brand and {metric}. "
            f"Use the follow-up questions below to drill deeper into specific brands or regions."
        )

    return insight


def validate_insight_response(parsed: dict) -> dict:
    """
    Validate and fix a parsed LLM JSON response (Pass 2 - insight generation).

    Ensures:
    - 'insight' is a non-empty string (markdown stripped)
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

    # Strip any markdown formatting the LLM may have added
    result["insight"] = clean_insight_text(result["insight"])

    # Validate insight is narrative text, not structured data
    result["insight"] = validate_insight_format(
        result["insight"], result.get("filters", {})
    )

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

        # Safety net: keyword guard overrides bad tool selection
        original_tool = validated["tool"]
        validated["tool"] = validate_routing(question, validated["tool"])

        # Safety net: fill any filters the LLM missed
        validated["filters"] = extract_missing_filters(question, validated["filters"])

        # Track whether we overrode for debug visibility
        if validated["tool"] != original_tool:
            validated["_routing_override"] = f"{original_tool} → {validated['tool']}"

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

def build_insight_prompt(question: str, tool_name: str, data_summary: str, filter_context: str = "") -> str:
    """
    Build the system prompt for the second LLM call.

    This prompt gives the LLM the actual data results and asks it to
    write a specific, number-backed business insight.

    Args:
        question:       The user's original question.
        tool_name:      The tool that was used.
        data_summary:   Compact text summary of the tool's output.
        filter_context: Description of the active filters applied.

    Returns:
        str - the system prompt for Pass 2.
    """
    scope_line = ""
    if filter_context:
        scope_line = f"\nDATA SCOPE: {filter_context} (this is NOT company-wide data)\n"

    return f"""You are a senior Business Intelligence analyst.
You have just run the "{tool_name.replace('_', ' ')}" analysis tool and received real data results.
{scope_line}
Here are the ACTUAL DATA RESULTS from the analysis:
---
{data_summary}
---

Based on these real numbers, write a business insight and suggest follow-up questions.

RULES FOR YOUR INSIGHT:
CRITICAL: Never use backtick characters anywhere in your response. Not for numbers, not for brand names, not for code, not for anything. The backtick character is completely forbidden in all fields including insight and suggestions.
The insight field must be exactly 2-3 complete English sentences. Write it as a business analyst summarizing findings for a VP or senior leader. Rules:
- Never use bullet points or lists of any kind
- Never use raw column names (never write 'Value', '_value', 'metric')
- Never include structured data sections like 'Top 5:' or 'Bottom 3:'
- Always reference specific brand names, dollar amounts, and regions
- Always include one business implication or recommendation
- Write in third person present tense
- Do NOT say "likely shows" or "may indicate" - you have the real data, so state facts
- Never use markdown formatting. No asterisks, no underscores, no backticks, no bold, no italics. Plain sentences only.
- Never wrap numbers, brand names, or any words in backticks. Never use inline code formatting. Write all numbers as plain text with commas and dollar signs only. Example: write $59,363 not `59,363`.

Good example:
"Lumix leads West region sales at $59,363, followed closely by Zentra at $57,292 and Novex at $52,362. The top 3 brands account for over half of total West region revenue, indicating high brand concentration. Brands like Dexon and Trion are significantly underperforming and may warrant a regional assortment review."

Bad example (NEVER do this):
"Top 5 brands: Lumix: 59,363. Best region: Value (59,363). Bottom 3 brands: Solvo: $34,854. Regional totals: Value: $417,516"

STRICT CONSTRAINTS:
- Do NOT reference specific external companies, retailers, or brand names (e.g. 'Canadian Tire', 'Walmart', 'Amazon') unless they appear in the data results above.
- Do NOT invent highly specific external events or campaigns that are not in the data.
- Only mention brand names, product names, divisions, and regions that appear in the DATA RESULTS section above.
- When speculating on causes, keep it general (e.g. 'may be driven by seasonality' is OK, 'driven by their Q3 marketing campaign' is NOT OK unless the data shows it).

RULES FOR SUGGESTIONS:
- Suggest 3 follow-up questions that reference specific entities from the data.
- Each question should help the user dig deeper into interesting findings.

Here is a complete WORKED EXAMPLE of what a correct JSON response looks like:

Q: "Show me the top brands by sales in the West region"
A:
{{{{
  "insight": "Lumix leads West region sales at $59,363, followed by Zentra at $57,292 and Novex at $52,362. The top 3 brands control the majority of West region revenue, suggesting strong brand loyalty in this market. Underperforming brands like Dexon and Trion may benefit from targeted promotions or regional assortment changes.",
  "suggestions": [
    "How do these brands perform in the East region?",
    "Show me the margin rate for top brands in the West",
    "Which categories drive Lumix sales in the West?"
  ]
}}}}

You MUST respond with ONLY a valid JSON object in this EXACT format:
{{{{
  "insight": "Your 2-3 sentence data-driven business insight here.",
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
    filter_context: str = "",
) -> dict:
    """
    Pass 2: Generate a data-driven insight using the actual tool results.

    Args:
        question:       The user's original question.
        tool_name:      The tool that produced the results.
        data_summary:   Compact text summary of the tool's DataFrame output.
        filter_context: Description of the active filters applied.

    Returns:
        dict with keys: 'insight', 'suggestions'
    """
    system_prompt = build_insight_prompt(question, tool_name, data_summary, filter_context)

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
        # If Pass 2 fails, return a clean generic fallback
        return {
            "insight": (
                "Analysis complete. The chart above shows the full breakdown. "
                "Use the follow-up questions below to drill deeper into the data."
            ),
            "suggestions": [
                "Show me the overall sales trend",
                "Which division performs best?",
                "Are there any anomalies in the data?",
            ],
        }
