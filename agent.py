"""
🏪 Retail Analytics Agent
Canadian Tire — Data Science Associate Case Study

A local, secure retail analytics web app powered by Streamlit and
Ollama (llama3.2:3b). All data stays on-device; no internet needed.

This is the main entry point — run with: streamlit run agent.py
"""

import streamlit as st

from config import DATA_PATH
from data_loader import load_data, get_dataset_summary
from ollama_client import verify_ollama, warmup_model
from ui import render_sidebar


def main():
    """Entry point — configure page, load data, render app shell."""

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

    # ── Warm up the model (pre-load into memory) ───────────
    if ollama_ok:
        warmup_model()

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
