"""
🏪 Private Business Intelligence Agent
Canadian Tire - Data Science Associate Case Study

A local, secure retail analytics web app powered by Streamlit and
Ollama (llama3.2:3b). All data stays on-device; no internet needed.

This is the main entry point - run with: streamlit run agent.py
"""

import streamlit as st

from config import DATA_PATH
from data_loader import load_data, get_dataset_summary
from ollama_client import verify_ollama, warmup_model, ask_llm, generate_insight
from tools import tool_router
from insight_builder import build_data_summary
from ui import (
    inject_custom_css,
    render_sidebar,
    render_chat_message,
    render_suggestions,
    render_welcome,
)


# =====================================================================
#  SESSION STATE INITIALISATION
# =====================================================================

def init_session_state() -> None:
    """Initialise all session state keys on first run."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "session_memory" not in st.session_state:
        st.session_state.session_memory = {
            "entities": {},
            "last_filters": {},
            "last_result": {},
        }

    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None

    if "ollama_ok" not in st.session_state:
        st.session_state.ollama_ok = None
        st.session_state.ollama_msg = ""

    if "model_warmed" not in st.session_state:
        st.session_state.model_warmed = False

    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False


# =====================================================================
#  MEMORY UPDATE
# =====================================================================

def update_memory(tool_name: str, filters: dict, insight: str, result_df=None) -> None:
    """
    Update session memory with entities and context from the latest
    LLM response and tool result.

    Merges new filter values into entities, stores last tool + filters,
    and captures a description of the result for follow-up context.
    """
    mem = st.session_state.session_memory

    # Update entities from filters (only non-None values)
    entity_keys = ["region", "brand", "division", "category"]
    for key in entity_keys:
        val = filters.get(key)
        if val and str(val).lower() not in ("null", "none", ""):
            mem["entities"][key] = val

    # Store last filters (include tool name)
    mem["last_filters"] = {"tool": tool_name}
    for k, v in filters.items():
        if v and str(v).lower() not in ("null", "none", ""):
            mem["last_filters"][k] = v

    # Store last result description
    mem["last_result"] = {
        "description": insight[:200],
    }

    # Try to extract the top item from the result dataframe
    if result_df is not None and len(result_df) > 0:
        # Use first column that isn't a numeric type as label
        for col_name in result_df.columns:
            if result_df[col_name].dtype == "object":
                mem["last_result"]["top_item"] = str(result_df[col_name].iloc[0])
                break


# =====================================================================
#  PROCESS A QUESTION (TWO-PASS LLM PIPELINE)
# =====================================================================

def process_question(question: str, df, summary: dict, is_dark_mode: bool = False) -> None:
    """
    Full pipeline:
      Pass 1: LLM picks tool + filters
      Tool runs: generates chart + data
      Pass 2: LLM writes data-driven insight from actual results

    Args:
        question: The user's natural-language question.
        df:       Full DataFrame with KPI columns.
        summary:  Dataset summary dict.
        is_dark_mode: Current theme setting for chart templates.
    """
    # Add user message
    st.session_state.messages.append({"role": "user", "content": question})

    # ── Pass 1: Pick the right tool + filters ───────────────
    llm_routing = ask_llm(
        question,
        st.session_state.session_memory,
        summary,
    )

    tool_name = llm_routing["tool"]
    filters = llm_routing["filters"]

    # Store theme info in filters so router can pass it to tools
    filters["_is_dark_mode"] = is_dark_mode

    # ── Run the tool ────────────────────────────────────────
    fig, result_df, callouts = tool_router(tool_name, filters, df)

    # ── Build compact data summary for Pass 2 ──────────────
    metric = filters.get("metric", "sales")
    data_summary = build_data_summary(tool_name, result_df, callouts, metric)

    # ── Pass 2: Generate data-driven insight ────────────────
    insight_response = generate_insight(question, tool_name, data_summary)

    # ── Update session memory ───────────────────────────────
    update_memory(tool_name, filters, insight_response["insight"], result_df)

    # Build assistant message
    assistant_msg = {
        "role": "assistant",
        "tool": tool_name,
        "insight": insight_response["insight"],
        "suggestions": insight_response["suggestions"],
        "figure": fig,
        "summary_df": result_df,
        "callouts": callouts,
    }
    st.session_state.messages.append(assistant_msg)


# =====================================================================
#  MAIN APP
# =====================================================================

def main():
    """Entry point - configure page, load data, run chat interface."""

    # ── Page config (must be first Streamlit call) ──────────
    st.set_page_config(
        page_title="Private Business Intelligence Agent",
        page_icon="🏪",
        layout="wide",
    )

    # ── Init session state ──────────────────────────────────
    init_session_state()

    # ── Inject custom CSS ───────────────────────────────────
    is_dark = st.session_state.get("dark_mode", False)
    inject_custom_css(is_dark)

    # ── Load data ───────────────────────────────────────────
    df = load_data(DATA_PATH)
    summary = get_dataset_summary(df)

    # ── Verify Ollama (once per session) ────────────────────
    if st.session_state.ollama_ok is None:
        ok, msg = verify_ollama()
        st.session_state.ollama_ok = ok
        st.session_state.ollama_msg = msg

    # ── Warm up the model (once per session) ────────────────
    if st.session_state.ollama_ok and not st.session_state.model_warmed:
        warmup_model()
        st.session_state.model_warmed = True

    # ── Sidebar ─────────────────────────────────────────────
    render_sidebar(
        summary,
        st.session_state.ollama_ok,
        st.session_state.ollama_msg,
    )

    # ── Process pending question (from suggestion click) ────
    if st.session_state.pending_question:
        question = st.session_state.pending_question
        st.session_state.pending_question = None
        with st.spinner("🔍 Analysing..."):
            process_question(question, df, summary, is_dark)

    # ── Render chat history ─────────────────────────────────
    if not st.session_state.messages:
        # Show polished welcome screen
        clicked = render_welcome()
        if clicked:
            st.session_state.pending_question = clicked
            st.rerun()
    else:
        for idx, msg in enumerate(st.session_state.messages):
            render_chat_message(msg, msg_idx=idx)

        # Show suggestions from last assistant message
        last_msg = st.session_state.messages[-1]
        if last_msg["role"] == "assistant":
            suggestions = last_msg.get("suggestions", [])
            clicked = render_suggestions(suggestions)
            if clicked:
                st.session_state.pending_question = clicked
                st.rerun()

    # ── Chat input ──────────────────────────────────────────
    if prompt := st.chat_input("Ask a question about the data..."):
        with st.spinner("🔍 Analysing..."):
            process_question(prompt, df, summary, is_dark)
        st.rerun()


if __name__ == "__main__":
    main()
