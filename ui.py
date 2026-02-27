"""
UI components for the Retail Analytics Agent.
Sidebar, chat messages, suggestion buttons, and custom styling.
"""

import streamlit as st
from config import APP_TITLE


# =====================================================================
#  CUSTOM CSS STYLING
# =====================================================================

CUSTOM_CSS = """
<style>
/* ── Import Google Fonts ──────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Global font ──────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Chat message styling ─────────────────────────────────── */
.stChatMessage {
    border-radius: 12px;
    margin-bottom: 1rem;
    padding: 0.5rem;
}

/* ── Suggestion buttons ───────────────────────────────────── */
.stButton > button {
    border-radius: 8px;
    border: 1px solid #e0e0e0;
    font-size: 0.85rem;
    padding: 0.5rem 1rem;
    transition: all 0.2s ease;
    background: white;
    color: #333;
}
.stButton > button:hover {
    border-color: #D32F2F;
    color: #D32F2F;
    background: #fff5f5;
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(211,47,47,0.15);
}

/* ──  Tool badge ──────────────────────────────────────────── */
.tool-badge {
    display: inline-block;
    background: #f0f4f8;
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 0.78rem;
    color: #546e7a;
    margin-top: 4px;
}

/* ── Sidebar styling ──────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #fafbfc 0%, #f0f4f8 100%);
}
section[data-testid="stSidebar"] .stMetric label {
    font-size: 0.75rem;
    color: #78909c;
}

/* ── Welcome hero card ────────────────────────────────────── */
.welcome-card {
    background: linear-gradient(135deg, #fafbfc 0%, #e8f5e9 50%, #fff3e0 100%);
    border-radius: 16px;
    padding: 2.5rem 2rem;
    margin: 1rem 0 2rem 0;
    border: 1px solid #e0e0e0;
}
.welcome-card h2 {
    margin-top: 0;
    color: #263238;
}
.welcome-card .example-q {
    background: white;
    border-radius: 8px;
    padding: 0.6rem 1rem;
    margin: 0.4rem 0;
    border-left: 3px solid #D32F2F;
    font-size: 0.9rem;
    color: #455a64;
    cursor: default;
    transition: all 0.15s ease;
}
.welcome-card .example-q:hover {
    background: #fff5f5;
    border-left-color: #1976D2;
}

/* ── Expander styling ─────────────────────────────────────── */
.streamlit-expanderHeader {
    font-size: 0.85rem;
    color: #546e7a;
}

/* ── Spinner overlay ──────────────────────────────────────── */
.stSpinner > div {
    border-color: #D32F2F !important;
}
</style>
"""


def inject_custom_css() -> None:
    """Inject custom CSS into the Streamlit app."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# =====================================================================
#  SIDEBAR
# =====================================================================

def render_sidebar(summary: dict, ollama_ok: bool, ollama_msg: str) -> None:
    """
    Render the sidebar with:
      - App title
      - Security badge
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

        # Sales per year with delta
        years = sorted(summary["sales_by_year"].keys())
        for year in years:
            sales = summary["sales_by_year"][year]
            # Show delta for 2024
            if year == max(years) and len(years) > 1:
                prev = summary["sales_by_year"].get(min(years), 0)
                delta = sales - prev
                delta_pct = (delta / prev * 100) if prev else 0
                st.metric(
                    f"Sales {int(year)}",
                    f"${sales:,.0f}",
                    f"{delta_pct:+.1f}% vs {int(min(years))}",
                )
            else:
                st.metric(f"Sales {int(year)}", f"${sales:,.0f}")

        # Dimension counts
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


# =====================================================================
#  WELCOME SCREEN
# =====================================================================

EXAMPLE_QUESTIONS = [
    "Which division grew the most year over year?",
    "Show me the top brands by sales in the West region",
    "Project Apparel division sales into 2025",
    "Are there any anomalies in product margins?",
    "What is the pricing sweet spot for Tools division?",
]


def render_welcome() -> str | None:
    """
    Render a polished welcome screen with example question cards.
    Returns the clicked question text, or None.
    """
    st.markdown(
        """
        <div class="welcome-card">
            <h2>👋 Welcome to the Retail Analytics Agent!</h2>
            <p style="color: #546e7a; font-size: 1.05rem;">
                Ask me anything about your Canadian Tire retail data.
                I'll pick the right analysis tool, generate charts,
                and give you business insights — all running <strong>100% locally</strong>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("**Try one of these questions to get started:**")
    for i, q in enumerate(EXAMPLE_QUESTIONS):
        if st.button(f"💬  {q}", key=f"welcome_{i}", use_container_width=True):
            return q
    return None


# =====================================================================
#  CHAT MESSAGE RENDERING
# =====================================================================

def render_chat_message(msg: dict) -> None:
    """
    Render a single chat message (user or assistant).

    User messages display as text. Assistant messages display
    the insight text, chart, data table, callouts.
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
                tool_label = tool.replace("_", " ").title()
                st.markdown(
                    f'<span class="tool-badge">📊 {tool_label}</span>',
                    unsafe_allow_html=True,
                )

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


# =====================================================================
#  SUGGESTION BUTTONS
# =====================================================================

def render_suggestions(suggestions: list[str]) -> str | None:
    """
    Render 3 follow-up suggestion buttons.
    Returns the clicked suggestion text, or None.
    """
    if not suggestions:
        return None

    st.markdown("**💡 Follow-up questions:**")
    cols = st.columns(len(suggestions))
    for i, (col, text) in enumerate(zip(cols, suggestions)):
        if col.button(text, key=f"suggest_{i}", use_container_width=True):
            return text
    return None
