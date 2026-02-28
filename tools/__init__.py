"""
Analysis tools package for the Private Business Intelligence Agent.

Each tool lives in its own module:
  - yoy_comparison
  - brand_region_crosstab
  - forecast_trendline
  - anomaly_detection
  - price_volume_margin
  - store_performance
  - seasonality_trends
  - division_mix
  - margin_waterfall
  - kpi_scorecard
  - price_elasticity
  - brand_benchmarking
  - growth_margin_matrix

The router dispatches tool calls from the LLM.
"""

from tools.yoy_comparison import yoy_comparison
from tools.brand_region_crosstab import brand_region_crosstab
from tools.forecast_trendline import forecast_trendline
from tools.anomaly_detection import anomaly_detection
from tools.price_volume_margin import price_volume_margin
from tools.store_performance import store_performance
from tools.seasonality_trends import seasonality_trends
from tools.division_mix import division_mix
from tools.margin_waterfall import margin_waterfall
from tools.kpi_scorecard import kpi_scorecard
from tools.price_elasticity import price_elasticity
from tools.brand_benchmarking import brand_benchmarking
from tools.growth_margin_matrix import growth_margin_matrix
from tools.router import tool_router

__all__ = [
    "yoy_comparison",
    "brand_region_crosstab",
    "forecast_trendline",
    "anomaly_detection",
    "price_volume_margin",
    "store_performance",
    "seasonality_trends",
    "division_mix",
    "margin_waterfall",
    "kpi_scorecard",
    "price_elasticity",
    "brand_benchmarking",
    "growth_margin_matrix",
    "tool_router",
]
