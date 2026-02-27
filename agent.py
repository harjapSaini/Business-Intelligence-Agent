"""
🏪 Retail Analytics Agent
Canadian Tire — Data Science Associate Case Study

A local, secure retail analytics web app powered by Streamlit and
Ollama (llama3.2:3b). All data stays on-device; no internet needed.
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression

# ── CONFIG ────────────────────────────────────────────────────
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:3b"
DATA_PATH = "CaseStudy_DataExtractFromPowerBIFile.xlsx"
APP_TITLE = "🏪 Retail Analytics Agent"
# ──────────────────────────────────────────────────────────────


# =====================================================================
#  DATA LOADING & KPI CALCULATIONS
# =====================================================================

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    """
    Read the Excel dataset and compute derived KPI columns.

    Columns added:
        SALES       = SELLING_PRICE_PER_UNIT × UNITS_SOLD
        COGS        = COST_PER_UNIT × UNITS_SOLD
        MARGIN      = SALES − COGS
        MARGIN_RATE = MARGIN / SALES   (0‒1 scale)

    Returns the full DataFrame with KPI columns appended.
    """
    df = pd.read_excel(path)

    # Derived KPIs
    df["SALES"] = df["SELLING_PRICE_PER_UNIT"] * df["UNITS_SOLD"]
    df["COGS"] = df["COST_PER_UNIT"] * df["UNITS_SOLD"]
    df["MARGIN"] = df["SALES"] - df["COGS"]
    # Avoid division by zero — fill with 0 where SALES == 0
    df["MARGIN_RATE"] = (df["MARGIN"] / df["SALES"]).fillna(0)

    return df


def get_dataset_summary(df: pd.DataFrame) -> dict:
    """
    Build a summary dict used to populate the sidebar stats
    and to give the LLM context about the dataset.

    Returns dict with keys:
        total_rows, years, regions, divisions, categories, brands,
        sales_by_year  (dict {year: total_sales})
    """
    sales_by_year = (
        df.groupby("YEAR")["SALES"]
        .sum()
        .to_dict()
    )

    summary = {
        "total_rows": len(df),
        "years": sorted(df["YEAR"].unique().tolist()),
        "regions": sorted(df["REGION"].unique().tolist()),
        "divisions": sorted(df["PRODUCT_DIVISION"].unique().tolist()),
        "categories": sorted(df["PRODUCT_CATEGORY"].unique().tolist()),
        "brands": sorted(df["BRAND"].unique().tolist()),
        "sales_by_year": sales_by_year,
    }
    return summary


# =====================================================================
#  OLLAMA LOCAL SECURITY VERIFICATION
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


# =====================================================================
#  SIDEBAR
# =====================================================================

def render_sidebar(summary: dict, ollama_ok: bool, ollama_msg: str) -> None:
    """
    Render the sidebar with:
      - App title
      - Security badge (green if Ollama OK, red if not)
      - Dataset summary stats
      - Privacy message
    """
    with st.sidebar:
        st.title(APP_TITLE)
        st.divider()

        # ── Security badge ──────────────────────────────────
        if ollama_ok:
            st.success("🔒 AI Running Locally — Data Secure")
        else:
            st.error("⚠️ Ollama Not Connected")
            st.markdown(ollama_msg)

        st.divider()

        # ── Dataset stats ───────────────────────────────────
        st.subheader("📊 Dataset Overview")
        st.metric("Total Rows", f"{summary['total_rows']:,}")

        # Sales per year
        for year, sales in sorted(summary["sales_by_year"].items()):
            st.metric(f"Total Sales {int(year)}", f"${sales:,.0f}")

        # Quick counts
        col1, col2 = st.columns(2)
        col1.metric("Regions", len(summary["regions"]))
        col2.metric("Divisions", len(summary["divisions"]))

        col3, col4 = st.columns(2)
        col3.metric("Categories", len(summary["categories"]))
        col4.metric("Brands", len(summary["brands"]))

        st.divider()
        st.caption("🔒 Data never leaves this device")


# =====================================================================
#  ANALYSIS TOOL 1 — YoY COMPARISON
# =====================================================================

def yoy_comparison(
    df: pd.DataFrame,
    metric: str = "sales",
    division: str = None,
    region: str = None,
    category: str = None,
    brand: str = None,
) -> tuple:
    """
    Compare a metric year-over-year (2023 vs 2024).

    Groups by the most specific filter provided, or by PRODUCT_DIVISION
    if none are given.  Returns a grouped bar chart and a delta summary.

    Args:
        df:       Full DataFrame with KPI columns.
        metric:   One of 'sales', 'margin', 'units', 'margin_rate'.
        division: Optional division filter.
        region:   Optional region filter.
        category: Optional category filter.
        brand:    Optional brand filter.

    Returns:
        (plotly.Figure, pd.DataFrame) — grouped bar chart + summary table.
    """
    # Map friendly metric name to column
    metric_col_map = {
        "sales": "SALES",
        "margin": "MARGIN",
        "units": "UNITS_SOLD",
        "margin_rate": "MARGIN_RATE",
    }
    col = metric_col_map.get(metric, "SALES")

    # Apply filters
    filtered = df.copy()
    if division:
        filtered = filtered[filtered["PRODUCT_DIVISION"] == division]
    if region:
        filtered = filtered[filtered["REGION"] == region]
    if category:
        filtered = filtered[filtered["PRODUCT_CATEGORY"] == category]
    if brand:
        filtered = filtered[filtered["BRAND"] == brand]

    # Decide grouping axis: most granular non-None filter determines the "next level" of detail
    if brand:
        group_col = "PRODUCT_CATEGORY"
    elif category:
        group_col = "BRAND"
    elif division:
        group_col = "PRODUCT_CATEGORY"
    elif region:
        group_col = "PRODUCT_DIVISION"
    else:
        group_col = "PRODUCT_DIVISION"

    # Aggregate
    if metric == "margin_rate":
        # Weighted margin rate: total_margin / total_sales
        agg = (
            filtered.groupby(["YEAR", group_col])
            .agg(total_margin=("MARGIN", "sum"), total_sales=("SALES", "sum"))
            .reset_index()
        )
        agg[col] = (agg["total_margin"] / agg["total_sales"]).fillna(0)
    else:
        agg = (
            filtered.groupby(["YEAR", group_col])[col]
            .sum()
            .reset_index()
        )

    # Build delta summary
    pivot = agg.pivot(index=group_col, columns="YEAR", values=col).fillna(0)
    if 2023 in pivot.columns and 2024 in pivot.columns:
        pivot["Change"] = pivot[2024] - pivot[2023]
        pivot["Change %"] = ((pivot["Change"] / pivot[2023].replace(0, np.nan)) * 100).fillna(0)
    summary_df = pivot.reset_index()

    # Chart
    agg["YEAR"] = agg["YEAR"].astype(str)
    metric_label = metric.replace("_", " ").title()
    fig = px.bar(
        agg,
        x=group_col,
        y=col,
        color="YEAR",
        barmode="group",
        title=f"YoY Comparison — {metric_label}",
        labels={col: metric_label, group_col: group_col.replace("_", " ").title()},
    )
    fig.update_layout(template="plotly_white")

    return fig, summary_df


# =====================================================================
#  ANALYSIS TOOL 2 — BRAND × REGION CROSS-TAB
# =====================================================================

def brand_region_crosstab(
    df: pd.DataFrame,
    metric: str = "sales",
) -> tuple:
    """
    Create a heatmap of brands vs regions for a chosen metric.

    Args:
        df:     Full DataFrame.
        metric: One of 'sales', 'margin', 'margin_rate', 'units'.

    Returns:
        (plotly.Figure, pd.DataFrame) — heatmap + pivot table.
    """
    metric_col_map = {
        "sales": "SALES",
        "margin": "MARGIN",
        "units": "UNITS_SOLD",
        "margin_rate": "MARGIN_RATE",
    }
    col = metric_col_map.get(metric, "SALES")

    if metric == "margin_rate":
        agg = (
            df.groupby(["BRAND", "REGION"])
            .agg(total_margin=("MARGIN", "sum"), total_sales=("SALES", "sum"))
            .reset_index()
        )
        agg[col] = (agg["total_margin"] / agg["total_sales"]).fillna(0)
    else:
        agg = (
            df.groupby(["BRAND", "REGION"])[col]
            .sum()
            .reset_index()
        )

    pivot = agg.pivot(index="BRAND", columns="REGION", values=col).fillna(0)
    summary_df = pivot.reset_index()

    metric_label = metric.replace("_", " ").title()
    fig = px.imshow(
        pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        labels={"x": "Region", "y": "Brand", "color": metric_label},
        title=f"Brand × Region — {metric_label}",
        color_continuous_scale="RdYlGn",
        aspect="auto",
    )
    fig.update_layout(template="plotly_white")

    return fig, summary_df


# =====================================================================
#  ANALYSIS TOOL 3 — FORECAST / TRENDLINES
# =====================================================================

def forecast_trendline(
    df: pd.DataFrame,
    group_by: str = "division",
    group_value: str = None,
    metric: str = "sales",
) -> tuple:
    """
    Build a monthly trendline with a 12-month linear forecast into 2025.

    Uses sklearn LinearRegression on monthly aggregates.
    Returns a line chart with solid historical + dotted forecast with
    confidence shading.

    Args:
        df:          Full DataFrame.
        group_by:    One of 'division', 'region', 'brand', 'category'.
        group_value: The specific value to filter on (e.g. 'Apparel').
        metric:      One of 'sales', 'margin', 'units', 'margin_rate'.

    Returns:
        (plotly.Figure, pd.DataFrame) — trend chart + monthly data table.
    """
    group_col_map = {
        "division": "PRODUCT_DIVISION",
        "region": "REGION",
        "brand": "BRAND",
        "category": "PRODUCT_CATEGORY",
    }
    metric_col_map = {
        "sales": "SALES",
        "margin": "MARGIN",
        "units": "UNITS_SOLD",
        "margin_rate": "MARGIN_RATE",
    }

    group_col = group_col_map.get(group_by, "PRODUCT_DIVISION")
    col = metric_col_map.get(metric, "SALES")

    # Filter to the selected group
    filtered = df.copy()
    if group_value:
        filtered = filtered[filtered[group_col] == group_value]

    # Monthly aggregation
    if metric == "margin_rate":
        monthly = (
            filtered.groupby(["YEAR", "MONTH"])
            .agg(total_margin=("MARGIN", "sum"), total_sales=("SALES", "sum"))
            .reset_index()
        )
        monthly[col] = (monthly["total_margin"] / monthly["total_sales"]).fillna(0)
    else:
        monthly = (
            filtered.groupby(["YEAR", "MONTH"])[col]
            .sum()
            .reset_index()
        )

    # Create a sequential month index for regression
    monthly = monthly.sort_values(["YEAR", "MONTH"]).reset_index(drop=True)
    monthly["month_idx"] = range(len(monthly))

    # Create proper date column for charting
    monthly["DATE"] = pd.to_datetime(
        monthly["YEAR"].astype(int).astype(str) + "-" + monthly["MONTH"].astype(int).astype(str) + "-01"
    )

    # Fit linear regression
    X = monthly[["month_idx"]].values
    y = monthly[col].values
    model = LinearRegression().fit(X, y)

    # Forecast 12 months into 2025
    last_idx = monthly["month_idx"].max()
    last_date = monthly["DATE"].max()
    forecast_months = []
    for i in range(1, 13):
        future_date = last_date + pd.DateOffset(months=i)
        forecast_months.append({
            "month_idx": last_idx + i,
            "DATE": future_date,
            "YEAR": future_date.year,
            "MONTH": future_date.month,
        })
    forecast_df = pd.DataFrame(forecast_months)

    # Predict
    forecast_X = forecast_df[["month_idx"]].values
    forecast_df[col] = model.predict(forecast_X)

    # Confidence band (using residual std error)
    residuals = y - model.predict(X)
    std_err = np.std(residuals)
    forecast_df["upper"] = forecast_df[col] + 1.96 * std_err
    forecast_df["lower"] = forecast_df[col] - 1.96 * std_err

    # Build chart
    metric_label = metric.replace("_", " ").title()
    title_suffix = f" — {group_value}" if group_value else ""
    fig = go.Figure()

    # Historical line
    fig.add_trace(go.Scatter(
        x=monthly["DATE"], y=monthly[col],
        mode="lines+markers", name="Historical",
        line=dict(color="#1976D2", width=2),
    ))

    # Forecast line (dotted)
    fig.add_trace(go.Scatter(
        x=forecast_df["DATE"], y=forecast_df[col],
        mode="lines+markers", name="Forecast",
        line=dict(color="#D32F2F", width=2, dash="dot"),
    ))

    # Confidence shading
    fig.add_trace(go.Scatter(
        x=pd.concat([forecast_df["DATE"], forecast_df["DATE"][::-1]]),
        y=pd.concat([forecast_df["upper"], forecast_df["lower"][::-1]]),
        fill="toself", fillcolor="rgba(211,47,47,0.15)",
        line=dict(color="rgba(255,255,255,0)"),
        showlegend=False, name="Confidence",
    ))

    fig.update_layout(
        title=f"Forecast — {metric_label}{title_suffix}",
        xaxis_title="Date",
        yaxis_title=metric_label,
        template="plotly_white",
    )

    # Combine for summary table
    monthly["type"] = "historical"
    forecast_df["type"] = "forecast"
    common_cols = ["DATE", "YEAR", "MONTH", col, "type"]
    summary_df = pd.concat(
        [monthly[common_cols], forecast_df[common_cols]],
        ignore_index=True,
    )

    return fig, summary_df


# =====================================================================
#  ANALYSIS TOOL 4 — ANOMALY & OUTLIER DETECTION
# =====================================================================

def anomaly_detection(
    df: pd.DataFrame,
    metric: str = "margin_rate",
    division: str = None,
    region: str = None,
) -> tuple:
    """
    Detect anomalous products using Z-score analysis.

    Aggregates to product-level, computes Z-scores, and flags
    outliers beyond ±2 standard deviations.

    Args:
        df:       Full DataFrame.
        metric:   One of 'sales', 'margin', 'margin_rate'.
        division: Optional division filter.
        region:   Optional region filter.

    Returns:
        (plotly.Figure, pd.DataFrame, list[str]) — scatter plot with
        outliers in red, outlier table, plain-English callout strings.
    """
    metric_col_map = {
        "sales": "SALES",
        "margin": "MARGIN",
        "margin_rate": "MARGIN_RATE",
    }
    col = metric_col_map.get(metric, "MARGIN_RATE")

    # Apply filters
    filtered = df.copy()
    if division:
        filtered = filtered[filtered["PRODUCT_DIVISION"] == division]
    if region:
        filtered = filtered[filtered["REGION"] == region]

    # Product-level aggregation
    if metric == "margin_rate":
        product_agg = (
            filtered.groupby(["PRODUCT_NAME", "PRODUCT_CATEGORY", "PRODUCT_DIVISION"])
            .agg(total_margin=("MARGIN", "sum"), total_sales=("SALES", "sum"),
                 avg_price=("SELLING_PRICE_PER_UNIT", "mean"), total_units=("UNITS_SOLD", "sum"))
            .reset_index()
        )
        product_agg[col] = (product_agg["total_margin"] / product_agg["total_sales"]).fillna(0)
    else:
        product_agg = (
            filtered.groupby(["PRODUCT_NAME", "PRODUCT_CATEGORY", "PRODUCT_DIVISION"])
            .agg(**{col: (col, "sum"),
                    "avg_price": ("SELLING_PRICE_PER_UNIT", "mean"),
                    "total_units": ("UNITS_SOLD", "sum")})
            .reset_index()
        )

    # Z-score calculation
    mean_val = product_agg[col].mean()
    std_val = product_agg[col].std()
    if std_val == 0:
        product_agg["z_score"] = 0.0
    else:
        product_agg["z_score"] = (product_agg[col] - mean_val) / std_val

    product_agg["is_outlier"] = product_agg["z_score"].abs() > 2
    product_agg["label"] = product_agg["is_outlier"].map({True: "Outlier", False: "Normal"})

    # Build chart
    metric_label = metric.replace("_", " ").title()
    fig = px.scatter(
        product_agg,
        x="PRODUCT_NAME",
        y=col,
        color="label",
        color_discrete_map={"Outlier": "#D32F2F", "Normal": "#1976D2"},
        hover_data=["PRODUCT_CATEGORY", "PRODUCT_DIVISION", "z_score"],
        title=f"Anomaly Detection — {metric_label}",
        labels={col: metric_label},
    )
    fig.update_layout(template="plotly_white", xaxis_tickangle=-45)

    # Outlier table
    outlier_df = product_agg[product_agg["is_outlier"]].sort_values("z_score", key=abs, ascending=False)

    # Plain-English callout strings
    callouts = []
    for _, row in outlier_df.head(5).iterrows():
        direction = "unusually high" if row["z_score"] > 0 else "unusually low"
        callouts.append(
            f"**{row['PRODUCT_NAME']}** ({row['PRODUCT_CATEGORY']}) has {direction} "
            f"{metric_label.lower()} (z-score: {row['z_score']:.1f})."
        )
    if not callouts:
        callouts.append("No significant outliers detected in this data slice.")

    return fig, outlier_df, callouts


# =====================================================================
#  ANALYSIS TOOL 5 — PRICE-VOLUME-MARGIN ANALYSIS
# =====================================================================

def price_volume_margin(
    df: pd.DataFrame,
    division: str = None,
    category: str = None,
) -> tuple:
    """
    Scatter/bubble analysis: x = avg selling price, y = margin rate,
    bubble size = total units sold, colour = product category.

    Args:
        df:       Full DataFrame.
        division: Optional division filter.
        category: Optional category filter.

    Returns:
        (plotly.Figure, pd.DataFrame) — bubble chart + product summary.
    """
    filtered = df.copy()
    if division:
        filtered = filtered[filtered["PRODUCT_DIVISION"] == division]
    if category:
        filtered = filtered[filtered["PRODUCT_CATEGORY"] == category]

    # Product-level aggregation
    product_agg = (
        filtered.groupby(["PRODUCT_NAME", "PRODUCT_CATEGORY", "PRODUCT_DIVISION"])
        .agg(
            avg_price=("SELLING_PRICE_PER_UNIT", "mean"),
            total_units=("UNITS_SOLD", "sum"),
            total_sales=("SALES", "sum"),
            total_margin=("MARGIN", "sum"),
        )
        .reset_index()
    )
    product_agg["margin_rate"] = (
        product_agg["total_margin"] / product_agg["total_sales"]
    ).fillna(0)

    # Build chart
    title_suffix = ""
    if division:
        title_suffix += f" — {division}"
    if category:
        title_suffix += f" / {category}"

    fig = px.scatter(
        product_agg,
        x="avg_price",
        y="margin_rate",
        size="total_units",
        color="PRODUCT_CATEGORY",
        hover_name="PRODUCT_NAME",
        hover_data=["total_sales", "total_margin", "total_units"],
        title=f"Price vs Margin Rate{title_suffix}",
        labels={
            "avg_price": "Avg Selling Price ($)",
            "margin_rate": "Margin Rate",
            "total_units": "Units Sold",
        },
    )
    fig.update_layout(template="plotly_white")

    return fig, product_agg


# =====================================================================
#  TOOL ROUTER / DISPATCHER
# =====================================================================

def tool_router(tool_name: str, filters: dict, df: pd.DataFrame) -> tuple:
    """
    Route a tool name + filters dict to the correct analysis function.

    Args:
        tool_name: One of 'yoy_comparison', 'brand_region_crosstab',
                   'forecast_trendline', 'anomaly_detection',
                   'price_volume_margin'.
        filters:   Dict of filter parameters (keys depend on the tool).
        df:        Full DataFrame with KPI columns.

    Returns:
        (plotly.Figure, pd.DataFrame, list[str] | None)
        The third element (callouts) is only present for anomaly_detection.
    """
    # Normalise None-string values from LLM
    clean = {}
    for k, v in filters.items():
        if v is None or (isinstance(v, str) and v.lower() in ("null", "none", "")):
            clean[k] = None
        else:
            clean[k] = v

    if tool_name == "yoy_comparison":
        fig, summary = yoy_comparison(
            df,
            metric=clean.get("metric", "sales"),
            division=clean.get("division"),
            region=clean.get("region"),
            category=clean.get("category"),
            brand=clean.get("brand"),
        )
        return fig, summary, None

    elif tool_name == "brand_region_crosstab":
        fig, summary = brand_region_crosstab(
            df,
            metric=clean.get("metric", "sales"),
        )
        return fig, summary, None

    elif tool_name == "forecast_trendline":
        fig, summary = forecast_trendline(
            df,
            group_by=clean.get("group_by", "division"),
            group_value=clean.get("group_value"),
            metric=clean.get("metric", "sales"),
        )
        return fig, summary, None

    elif tool_name == "anomaly_detection":
        fig, outlier_df, callouts = anomaly_detection(
            df,
            metric=clean.get("metric", "margin_rate"),
            division=clean.get("division"),
            region=clean.get("region"),
        )
        return fig, outlier_df, callouts

    elif tool_name == "price_volume_margin":
        fig, summary = price_volume_margin(
            df,
            division=clean.get("division"),
            category=clean.get("category"),
        )
        return fig, summary, None

    else:
        # Fallback to YoY comparison with defaults
        fig, summary = yoy_comparison(df, metric="sales")
        return fig, summary, None


# =====================================================================
#  MAIN APP
# =====================================================================

def main():
    """Entry point — configure page, load data, render Phase 1 shell."""

    # ── Page config (must be first Streamlit call) ──────────
    st.set_page_config(
        page_title="Retail Analytics Agent",
        page_icon="🏪",
        layout="wide",
    )

    # ── Load data ───────────────────────────────────────────
    df = load_data(DATA_PATH)
    summary = get_dataset_summary(df)

    # ── Verify Ollama ───────────────────────────────────────
    ollama_ok, ollama_msg = verify_ollama()

    # ── Sidebar ─────────────────────────────────────────────
    render_sidebar(summary, ollama_ok, ollama_msg)

    # ── Main area (Phase 1: data preview) ───────────────────
    st.header("📋 Data Preview")
    st.dataframe(df.head(20), width="stretch")

    # Show KPI column check
    st.subheader("✅ KPI Columns")
    kpi_cols = ["SALES", "COGS", "MARGIN", "MARGIN_RATE"]
    cols = st.columns(len(kpi_cols))
    for col, kpi in zip(cols, kpi_cols):
        col.metric(kpi, f"{'✔' if kpi in df.columns else '✘'}")

    # Quick sanity: total sales by year
    st.subheader("💰 Total Sales by Year")
    for year in sorted(df["YEAR"].unique()):
        year_sales = df[df["YEAR"] == year]["SALES"].sum()
        st.write(f"**{int(year)}:** ${year_sales:,.2f}")


if __name__ == "__main__":
    main()
