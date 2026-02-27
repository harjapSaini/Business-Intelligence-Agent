"""
Analysis tools package for the Retail Analytics Agent.

Each tool lives in its own module:
  - yoy_comparison
  - brand_region_crosstab
  - forecast_trendline
  - anomaly_detection
  - price_volume_margin

The router dispatches tool calls from the LLM.
"""

from tools.yoy_comparison import yoy_comparison
from tools.brand_region_crosstab import brand_region_crosstab
from tools.forecast_trendline import forecast_trendline
from tools.anomaly_detection import anomaly_detection
from tools.price_volume_margin import price_volume_margin
from tools.router import tool_router

__all__ = [
    "yoy_comparison",
    "brand_region_crosstab",
    "forecast_trendline",
    "anomaly_detection",
    "price_volume_margin",
    "tool_router",
]
