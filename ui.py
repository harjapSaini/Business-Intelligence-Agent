"""
UI components for the Private Business Intelligence Agent.
Sidebar, chat messages, suggestion buttons, and custom styling.
"""

import streamlit as st
from config import APP_TITLE


# =====================================================================
#  CUSTOM CSS STYLING
# =====================================================================

COMMON_CSS = """
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

/* ── Expander styling ─────────────────────────────────────── */
.streamlit-expanderHeader {
    font-size: 0.85rem;
}

/* ── Spinner overlay ──────────────────────────────────────── */
.stSpinner > div {
    border-color: #D32F2F !important;
}
"""

CUSTOM_CSS_LIGHT = """
<style>
""" + COMMON_CSS + """
/* ── LIGHT MODE STYLES ────────────────────────────────────── */
/* Force absolute light background */
.stApp {
    background-color: #FFFFFF !important;
}
[data-testid="stAppViewBlockContainer"] {
    background-color: #FFFFFF !important;
    padding-bottom: 2rem;
}
header[data-testid="stHeader"] {
    background-color: transparent !important;
}

/* Force text colors to dark */
.stMarkdown p, .stMarkdown li, h1, h2, h3, h4, h5, h6 {
    color: #263238 !important;
}
.stMetric label {
    color: #78909C !important;
}
.stMetric [data-testid="stMetricValue"] {
    color: #263238 !important;
}

.stButton > button {
    border-radius: 8px;
    border: 1px solid #e0e0e0 !important;
    font-size: 0.85rem;
    padding: 0.5rem 1rem;
    transition: all 0.2s ease;
    background: #FFFFFF !important;
    color: #263238 !important;
}
.stButton > button:hover {
    border-color: #D32F2F !important;
    color: #D32F2F !important;
    background: #fff5f5 !important;
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(211,47,47,0.15);
}
.stButton > button p {
    color: inherit !important;
}

.tool-badge {
    display: inline-block;
    background: #f0f4f8;
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 0.78rem;
    color: #546e7a;
    margin-top: 4px;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #fafbfc 0%, #edf1f5 100%) !important;
}
section[data-testid="stSidebar"] p {
    color: #263238 !important;
}

.welcome-card {
    background: linear-gradient(135deg, #fafbfc 0%, #e8f5e9 50%, #fff3e0 100%);
    border-radius: 16px;
    padding: 2.5rem 2rem;
    margin: 1rem 0 2rem 0;
    border: 1px solid #e0e0e0;
}
.welcome-card h2 {
    margin-top: 0;
    color: #263238 !important;
}
.welcome-card-desc {
    color: #546e7a !important;
    font-size: 1.05rem;
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

/* ── Chat input styling (Light) ── */
[data-testid="stBottomBlockContainer"] {
    background-color: #FFFFFF !important;
}
.stChatInput {
    background-color: transparent !important;
}
[data-testid="stChatInput"] > div {
    background-color: #FAFAFA !important;
    border: 1px solid #E0E0E0 !important;
}
[data-testid="stChatInput"] textarea {
    color: #263238 !important;
    background-color: #FAFAFA !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #78909C !important;
}
[data-testid="stChatInputSubmitButton"] {
    background-color: transparent !important;
}
[data-testid="stChatInputSubmitButton"] svg {
    fill: #D32F2F !important;
}

/* ── Expander & DataFrame (Light) ── */
.streamlit-expanderHeader {
    color: #546e7a !important;
    background-color: #FAFAFA !important;
    border-radius: 8px;
}
div[data-testid="stExpander"] div[role="button"] p {
    color: #546e7a !important;
}
[data-testid="stDataFrame"] {
    background-color: #FFFFFF !important;
}
[data-testid="stDataFrame"] div, [data-testid="stDataFrame"] span {
    color: #263238 !important;
    background-color: transparent !important;
}
[data-testid="stDataFrame"] th {
    background-color: #F8F9FA !important;
    color: #263238 !important;
}
</style>
"""

CUSTOM_CSS_DARK = """
<style>
""" + COMMON_CSS + """
/* ── DARK MODE STYLES ─────────────────────────────────────── */
/* Force absolute dark background */
.stApp {
    background-color: #0E1117 !important;
}
[data-testid="stAppViewBlockContainer"] {
    background-color: #0E1117 !important;
    padding-bottom: 2rem;
}
header[data-testid="stHeader"] {
    background-color: transparent !important;
}

/* Force text colors to soft white */
.stMarkdown p, .stMarkdown li, h1, h2, h3, h4, h5, h6 {
    color: #FAFAFA !important;
}
.stMarkdown code {
    background-color: #262730 !important;
    color: #FAFAFA !important;
}
.stMetric label {
    color: #B0BEC5 !important;
}
.stMetric [data-testid="stMetricValue"] {
    color: #FAFAFA !important;
}

.stButton > button {
    border-radius: 8px;
    border: 1px solid #37474F !important;
    font-size: 0.85rem;
    padding: 0.5rem 1rem;
    transition: all 0.2s ease;
    background: #262730 !important;
    color: #FAFAFA !important;
}
.stButton > button:hover {
    border-color: #D32F2F !important;
    color: #FAFAFA !important;
    background: #3c2424 !important;
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(211,47,47,0.3);
}
.stButton > button p {
    color: inherit !important;
}

.tool-badge {
    display: inline-block;
    background: #262730;
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 0.78rem;
    color: #B0BEC5;
    margin-top: 4px;
    border: 1px solid #37474F;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1A1C23 0%, #101216 100%) !important;
}
section[data-testid="stSidebar"] p {
    color: #FAFAFA !important;
}

.welcome-card {
    background: linear-gradient(135deg, #1E1E1E 0%, #1A2520 50%, #2A2015 100%);
    border-radius: 16px;
    padding: 2.5rem 2rem;
    margin: 1rem 0 2rem 0;
    border: 1px solid #37474F;
}
.welcome-card h2 {
    margin-top: 0;
    color: #FAFAFA !important;
}
.welcome-card-desc {
    color: #B0BEC5 !important;
    font-size: 1.05rem;
}
.welcome-card .example-q {
    background: #262730;
    border-radius: 8px;
    padding: 0.6rem 1rem;
    margin: 0.4rem 0;
    border-left: 3px solid #D32F2F;
    font-size: 0.9rem;
    color: #B0BEC5;
    cursor: default;
    transition: all 0.15s ease;
}

/* ── Chat input styling (Dark) ── */
[data-testid="stBottomBlockContainer"] {
    background-color: #0E1117 !important;
}
.stChatInput {
    background-color: transparent !important;
}
[data-testid="stChatInput"] > div {
    background-color: #1A1C23 !important;
    border: 1px solid #37474F !important;
}
[data-testid="stChatInput"] textarea {
    color: #FAFAFA !important;
    background-color: #1A1C23 !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #B0BEC5 !important;
}
[data-testid="stChatInputSubmitButton"] {
    background-color: transparent !important;
}
[data-testid="stChatInputSubmitButton"] svg {
    fill: #FAFAFA !important;
}

/* ── Expander & DataFrame (Dark) ── */
.streamlit-expanderHeader {
    color: #B0BEC5 !important;
    background-color: #1E1E1E !important;
    border-radius: 8px;
}
div[data-testid="stExpander"] div[role="button"] p {
    color: #B0BEC5 !important;
}
[data-testid="stDataFrame"] {
    background-color: #1A1C23 !important;
}
[data-testid="stDataFrame"] div, [data-testid="stDataFrame"] span {
    color: #B0BEC5 !important;
    background-color: transparent !important;
}
[data-testid="stDataFrame"] th {
    background-color: #262730 !important;
    color: #FAFAFA !important;
}
</style>
"""


def inject_custom_css(is_dark_mode: bool = False) -> None:
    """Inject custom CSS into the Streamlit app based on the active theme."""
    css = CUSTOM_CSS_DARK if is_dark_mode else CUSTOM_CSS_LIGHT
    st.markdown(css, unsafe_allow_html=True)


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
            st.success("🔒 AI Running Locally - Data Secure")
        else:
            st.error("⚠️ Ollama Not Connected")
            st.markdown(ollama_msg)

        st.divider()

        # ── Theme Toggle ────────────────────────────────────
        is_dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.get("dark_mode", False), key="dark_mode_toggle")
        
        # Immediate sync to session state to prevent lag
        if "dark_mode" not in st.session_state or st.session_state.dark_mode != is_dark_mode:
            st.session_state.dark_mode = is_dark_mode
            st.rerun()

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
    "How is the business performing overall?",
    "Which division grew the most year over year?",
    "Which stores are underperforming?",
    "Is there a seasonal pattern in Gardening?",
    "What percentage of sales does each division represent?",
    "Why did our margins change?",
    "Where are our stars and dogs?",
    "Which categories are most price sensitive?",
    "Which brand owns the Fitness category?",
    "Project Apparel division sales into 2025",
]


def render_welcome() -> str | None:
    """
    Render a polished welcome screen with example question cards.
    Returns the clicked question text, or None.
    """
    st.markdown(
        """
        <div class="welcome-card">
            <h2>👋 Welcome to the Private Business Intelligence Agent!</h2>
            <p class="welcome-card-desc">
                Ask me anything about your Canadian Tire retail data.
                I'll pick the right analysis tool, generate charts,
                and give you business insights - all running <strong>100% locally</strong>.
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

def render_chat_message(msg: dict, msg_idx: int = 0, is_dark: bool = False) -> None:
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
            # Insight text — use st.html() to bypass Streamlit's markdown
            # parser which misinterprets number/comma patterns as code spans
            insight = msg.get("insight", "")
            text_color = "#e0e0e0" if is_dark else "#1a1a1a"
            if insight:
                st.html(
                    f"<p style='font-size: 16px; line-height: 1.6; "
                    f"color: {text_color}; margin: 0 0 12px 0;'>"
                    f"{insight}</p>"
                )

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
                # Force update the template right before rendering 
                # so older session_state charts match the active theme toggle
                fig.update_layout(template="plotly_dark" if is_dark else "plotly_white")
                st.plotly_chart(fig, use_container_width=True, theme=None, key=f"chart_{msg_idx}")

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
