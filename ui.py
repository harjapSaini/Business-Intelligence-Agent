"""
UI components for the Retail Analytics Agent.
Sidebar, chat messages, and follow-up suggestion buttons.
"""

import streamlit as st
from config import APP_TITLE


def render_sidebar(summary: dict, ollama_ok: bool, ollama_msg: str) -> None:
    """
    Render the sidebar with:
      - App title
      - Security badge (green if Ollama OK, red if not)
      - Dataset summary stats
      - Clear conversation button
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

        # ── Clear conversation button ───────────────────────
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.session_memory = {
                "entities": {},
                "last_filters": {},
                "last_result": {},
            }
            st.session_state.pending_question = None
            st.rerun()

        st.caption("🔒 Data never leaves this device")


def render_chat_message(msg: dict) -> None:
    """
    Render a single chat message (user or assistant).

    User messages display as text. Assistant messages display
    the insight text, chart (if any), data table, callouts,
    and follow-up suggestions.
    """
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])

    elif msg["role"] == "assistant":
        with st.chat_message("assistant", avatar="🏪"):
            # Insight text
            st.markdown(msg.get("insight", ""))

            # Tool badge
            tool = msg.get("tool", "")
            if tool:
                st.caption(f"📊 Tool: `{tool}`")

            # Anomaly callouts (before chart for context)
            callouts = msg.get("callouts")
            if callouts:
                for c in callouts:
                    st.markdown(f"- {c}")

            # Chart
            fig = msg.get("figure")
            if fig is not None:
                st.plotly_chart(fig, width="stretch")

            # Data table (collapsed)
            summary_df = msg.get("summary_df")
            if summary_df is not None:
                with st.expander("📋 View Data Table"):
                    st.dataframe(summary_df, width="stretch")


def render_suggestions(suggestions: list[str]) -> str | None:
    """
    Render 3 follow-up suggestion buttons.

    Returns the clicked suggestion text, or None if nothing clicked.
    """
    if not suggestions:
        return None

    st.markdown("**💡 Follow-up questions:**")
    cols = st.columns(len(suggestions))
    for i, (col, text) in enumerate(zip(cols, suggestions)):
        if col.button(text, key=f"suggest_{i}", use_container_width=True):
            return text
    return None
