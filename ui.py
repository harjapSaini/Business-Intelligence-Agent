"""
UI components for the Retail Analytics Agent.
Sidebar rendering and future chat / suggestion UI elements.
"""

import streamlit as st
from config import APP_TITLE


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
