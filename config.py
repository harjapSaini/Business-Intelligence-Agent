"""
Configuration constants for the Private Business Intelligence Agent.
All settings in one place for easy modification.
"""

# ── Ollama LLM settings ──────────────────────────────────────
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:3b"

# ── Data settings ─────────────────────────────────────────────
DATA_PATH = "CaseStudy_DataExtractFromPowerBIFile.xlsx"

# ── App settings ──────────────────────────────────────────────
APP_TITLE = "🏪 Private Business Intelligence Agent"

# ── Valid tool names for the LLM router ───────────────────────
VALID_TOOLS = [
    "yoy_comparison",
    "brand_region_crosstab",
    "forecast_trendline",
    "anomaly_detection",
    "price_volume_margin",
]

# ── Chart colour palette (consistent across all tools) ────────
# A professional, accessible palette inspired by Canadian Tire red
CHART_COLORS = [
    "#D32F2F",  # Canadian Tire red
    "#1976D2",  # Confident blue
    "#2E7D32",  # Growth green
    "#F57C00",  # Warm orange
    "#7B1FA2",  # Royal purple
    "#00838F",  # Teal
    "#C2185B",  # Deep pink
    "#455A64",  # Slate grey
    "#FBC02D",  # Gold
    "#5D4037",  # Brown
]

# Two-colour palette for YoY (2023 vs 2024)
YOY_COLORS = {"2023": "#1976D2", "2024": "#D32F2F"}

# Anomaly colours
ANOMALY_COLORS = {"Outlier": "#D32F2F", "Normal": "#90CAF9"}

# Forecast colours
FORECAST_HISTORICAL = "#1976D2"
FORECAST_PREDICTED = "#D32F2F"
FORECAST_CONFIDENCE = "rgba(211,47,47,0.12)"

# Heatmap colour scale
HEATMAP_SCALE = "RdYlGn"
