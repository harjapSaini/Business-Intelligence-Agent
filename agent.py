"""
🏪 Retail Analytics Agent
Canadian Tire — Data Science Associate Case Study

A local, secure retail analytics web app powered by Streamlit and
Ollama (llama3.2:3b). All data stays on-device; no internet needed.
"""

import streamlit as st
import pandas as pd
import requests

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
