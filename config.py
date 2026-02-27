"""
Configuration constants for the Retail Analytics Agent.
All settings in one place for easy modification.
"""

# ── Ollama LLM settings ──────────────────────────────────────
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:3b"

# ── Data settings ─────────────────────────────────────────────
DATA_PATH = "CaseStudy_DataExtractFromPowerBIFile.xlsx"

# ── App settings ──────────────────────────────────────────────
APP_TITLE = "🏪 Retail Analytics Agent"

# ── Valid tool names for the LLM router ───────────────────────
VALID_TOOLS = [
    "yoy_comparison",
    "brand_region_crosstab",
    "forecast_trendline",
    "anomaly_detection",
    "price_volume_margin",
]
