"""
UI components for the Private Business Intelligence Agent.
Sidebar, chat messages, suggestion buttons, and custom styling.
"""

import json

import streamlit as st
import streamlit.components.v1 as components
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
        is_dark_mode = st.toggle(
            "🌙 Dark Mode",
            value=st.session_state.get("dark_mode", False),
            key="dark_mode_toggle",
            disabled=st.session_state.get("processing", False),
        )
        
        # Immediate sync to session state to prevent lag
        if "dark_mode" not in st.session_state or st.session_state.dark_mode != is_dark_mode:
            st.session_state.dark_mode = is_dark_mode
            if not st.session_state.get("processing", False):
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

LOADING_MESSAGES = [
    "\U0001f50d Analysing your data...",
    "\U0001f4ca Crunching the numbers...",
    "\U0001f9ee Running calculations...",
    "\U0001f4a1 Generating insights...",
    "\U0001f4c8 Spotting trends...",
    "\U0001f50e Digging into the details...",
    "\u26a1 Processing your request...",
    "\U0001f3af Finding patterns...",
    "\U0001f4cb Preparing your report...",
    "\U0001f9e0 Thinking hard...",
    "\U0001f522 Counting every row...",
    "\U0001f4c9 Checking for anomalies...",
    "\U0001f5c2\ufe0f Sorting through records...",
    "\U0001f52c Examining the data closely...",
    "\U0001f4d0 Measuring performance...",
    "\U0001f3d7\ufe0f Building your chart...",
    "\U0001f3a8 Designing the visualization...",
    "\U0001f5c3\ufe0f Querying the dataset...",
    "\u23f3 Almost there...",
    "\U0001f504 Cross-referencing metrics...",
    "\U0001f4ca Comparing year over year...",
    "\U0001f9e9 Piecing it all together...",
    "\U0001f4bc Consulting the AI brain...",
    "\U0001f52e Predicting the outcome...",
    "\U0001f4dd Drafting the insight...",
    "\U0001f3b2 Running statistical checks...",
    "\U0001f30d Scanning all regions...",
    "\U0001f3f7\ufe0f Categorizing the results...",
    "\U0001f4e6 Unpacking the numbers...",
    "\U0001f527 Fine-tuning the analysis...",
    "\U0001f3af Zeroing in on answers...",
    "\U0001f4ca Aggregating totals...",
    "\U0001f9ea Testing hypotheses...",
    "\U0001f4c8 Evaluating growth rates...",
    "\U0001f50d Investigating further...",
    "\U0001f4b0 Tallying the figures...",
    "\U0001f4cb Compiling the summary...",
    "\U0001f504 Refreshing the view...",
    "\U0001f4d0 Calibrating the metrics...",
    "\U0001f9e0 Applying AI magic...",
    "\U0001f6e0\ufe0f Assembling your answer...",
    "\U0001f5c4\ufe0f Mining the database...",
    "\U0001f517 Connecting the dots...",
    "\U0001f4ca Benchmarking divisions...",
    "\U0001f3af Honing in on key data...",
    "\u2699\ufe0f Running the engine...",
    "\U0001f4dd Writing up findings...",
    "\U0001f52c Performing deep analysis...",
    "\U0001f4a1 Extracting key takeaways...",
    "\U0001f3c1 Finalizing the results...",
    "\U0001f31f Polishing the insights...",
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

    is_busy = st.session_state.get("processing", False)
    st.markdown("**Try one of these questions to get started:**")
    col1, col2 = st.columns(2)
    for i, q in enumerate(EXAMPLE_QUESTIONS):
        col = col1 if i % 2 == 0 else col2
        if col.button(f"💬  {q}", key=f"welcome_{i}", use_container_width=True, disabled=is_busy):
            return q
    return None


# =====================================================================
#  LOADING ANIMATION
# =====================================================================

def render_loading_animation(is_dark: bool = False) -> None:
    """Render a cycling loading animation with rotating status messages."""
    text_color = "#e0e0e0" if is_dark else "#263238"
    bg_color = "#1A1C23" if is_dark else "#f8f9fa"
    border_color = "#37474F" if is_dark else "#e0e0e0"
    spinner_track = "#37474F" if is_dark else "#e0e0e0"
    messages_js = json.dumps(LOADING_MESSAGES)

    html = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        body {{ margin: 0; padding: 0; background: transparent; }}
        .loader-box {{
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 14px 20px;
            background: {bg_color};
            border: 1px solid {border_color};
            border-radius: 12px;
            font-family: 'Inter', sans-serif;
        }}
        .loader-spin {{
            width: 20px; height: 20px;
            border: 3px solid {spinner_track};
            border-top: 3px solid #D32F2F;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            flex-shrink: 0;
        }}
        .loader-text {{
            font-size: 0.95rem;
            font-weight: 500;
            color: {text_color};
            transition: opacity 0.3s ease;
        }}
    </style>
    <div class="loader-box">
        <div class="loader-spin"></div>
        <span class="loader-text" id="loader-txt">{LOADING_MESSAGES[0]}</span>
    </div>
    <script>
        const msgs = {messages_js};
        let i = Math.floor(Math.random() * msgs.length);
        const el = document.getElementById('loader-txt');
        if (el) el.textContent = msgs[i];
        setInterval(() => {{
            i = (i + 1) % msgs.length;
            if (el) {{
                el.style.opacity = '0';
                setTimeout(() => {{
                    el.textContent = msgs[i];
                    el.style.opacity = '1';
                }}, 250);
            }}
        }}, 2500);
    </script>
    """
    components.html(html, height=70)


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

            # Tool badge (skip for out_of_scope)
            tool = msg.get("tool", "")
            if tool and tool != "out_of_scope":
                tool_label = tool.replace("_", " ").title()
                st.markdown(
                    f'<span class="tool-badge">📊 {tool_label}</span>',
                    unsafe_allow_html=True,
                )

            # Out-of-scope info box
            if tool == "out_of_scope":
                st.info("💡 This question requires data not available in the current dataset.")

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

    is_busy = st.session_state.get("processing", False)
    st.markdown("**💡 Follow-up questions:**")
    cols = st.columns(len(suggestions))
    for i, (col, text) in enumerate(zip(cols, suggestions)):
        if col.button(text, key=f"suggest_{i}", use_container_width=True, disabled=is_busy):
            return text
    return None
