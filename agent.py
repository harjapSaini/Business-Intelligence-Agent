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
from ollama_client import verify_ollama, warmup_model, ask_llm, generate_insight, clean_insight_text
from tools import tool_router
from insight_builder import build_data_summary
from ui import (
    inject_custom_css,
    render_sidebar,
    render_chat_message,
    render_suggestions,
    render_welcome,
    render_loading_animation,
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

    if "processing" not in st.session_state:
        st.session_state.processing = False


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
#  OUT-OF-SCOPE HANDLER
# =====================================================================

def build_out_of_scope_message(question: str, filters: dict) -> str:
    """
    Generates a helpful explanation when the question cannot be
    answered with the available dataset.
    """
    q = question.lower()

    if any(w in q for w in ["average order value", "aov", "order value"]):
        return (
            "Average Order Value cannot be calculated from this dataset "
            "because there is no customer or order identifier — each row "
            "represents a product-store-date transaction, not a customer order. "
            "To calculate AOV, a customer transaction ID linking multiple "
            "products per purchase would be needed. "
            "I can show you average selling price per unit by division or "
            "region instead — would that be helpful?"
        )
    elif any(w in q for w in ["customer", "customers"]):
        return (
            "Customer-level data is not available in this dataset. "
            "The data contains product sales by store and date but does "
            "not include customer identifiers, loyalty data, or purchase "
            "frequency. I can analyze performance by store, region, or "
            "division instead."
        )
    elif any(w in q for w in ["inventory", "stock"]):
        return (
            "Inventory and stock level data is not included in this dataset. "
            "Only sales transactions and product costs are available. "
            "I can show sales trends or margin analysis that may indicate "
            "supply or demand patterns."
        )
    elif any(w in q for w in ["competitor", "market share"]):
        return (
            "Competitor and external market data is not available in this "
            "dataset. All analysis is limited to internal sales and margin "
            "data. I can show relative brand performance within this "
            "organization instead."
        )
    else:
        return (
            "This question cannot be answered with the available data. "
            "The dataset contains sales transactions, product costs, "
            "store information, and calendar data only. "
            "Try asking about sales, margins, brands, divisions, or regions."
        )


# =====================================================================
#  PROCESS A QUESTION (TWO-PASS LLM PIPELINE)
# =====================================================================

def process_question(question: str, df, summary: dict, is_dark_mode: bool = False, add_user_msg: bool = True) -> None:
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
        add_user_msg: Whether to append the user message to history.
    """
    # Add user message
    if add_user_msg:
        st.session_state.messages.append({"role": "user", "content": question})

    # ── Pass 1: Pick the right tool + filters ───────────────
    llm_routing = ask_llm(
        question,
        st.session_state.session_memory,
        summary,
    )

    tool_name = llm_routing["tool"]
    filters = llm_routing["filters"]

    # ── Debug: show LLM routing decision ────────────────────
    with st.expander("🔧 Debug: LLM Routing Decision", expanded=False):
        st.write(f"**Tool selected:** `{tool_name}`")
        if "_routing_override" in llm_routing:
            st.warning(f"⚠️ Routing override: {llm_routing['_routing_override']}")
        st.write("**Filters:**")
        st.json({k: v for k, v in filters.items() if k != '_is_dark_mode'})

    # Store theme info in filters so router can pass it to tools
    filters["_is_dark_mode"] = is_dark_mode

    # ── Handle out-of-scope questions ───────────────────────
    if tool_name == "out_of_scope":
        insight = build_out_of_scope_message(question, filters)
        suggestions = [
            "How is the business performing overall?",
            "Which division grew the most year over year?",
            "Show me the top brands by sales",
        ]
        assistant_msg = {
            "role": "assistant",
            "tool": "out_of_scope",
            "insight": insight,
            "suggestions": suggestions,
            "figure": None,
            "summary_df": None,
            "callouts": None,
        }
        st.session_state.messages.append(assistant_msg)
        return

    # ── Run the tool ────────────────────────────────────────
    fig, result_df, callouts = tool_router(tool_name, filters, df)

    # ── Check for pre-computed insight (bypasses Pass 2) ───
    pre_computed_insight = None
    if isinstance(callouts, str) and callouts.strip():
        pre_computed_insight = clean_insight_text(callouts)  # safety net
        callouts = None  # Reset so it's not treated as anomaly callouts

    # ── Build compact data summary for Pass 2 ──────────────
    metric = filters.get("metric", "sales")
    data_summary = build_data_summary(tool_name, result_df, callouts, metric)

    # ── Build filter context so LLM knows the data scope ───
    filter_labels = {
        "division": "Division", "region": "Region",
        "category": "Category", "brand": "Brand",
    }
    active = [
        f"{filter_labels[k]}={filters[k]}"
        for k in filter_labels
        if filters.get(k) and str(filters[k]).lower() not in ("null", "none", "")
    ]
    filter_context = ", ".join(active) if active else ""

    # ── Pass 2: Generate data-driven insight ────────────────
    if pre_computed_insight:
        # Tool provided its own insight — skip LLM Pass 2
        insight_response = {
            "insight": pre_computed_insight,
            "suggestions": [
                "Which division grew the most year over year?",
                "Show me the margin waterfall by division",
                "What does the forecast look like for Sports?",
            ],
        }
    else:
        insight_response = generate_insight(question, tool_name, data_summary, filter_context)

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
    # Reset stale processing flag (e.g. if previous run was interrupted)
    if st.session_state.processing and not st.session_state.pending_question:
        st.session_state.processing = False
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

    # ── Chat input (always visible, disabled while processing) ──
    prompt = st.chat_input(
        "Ask a question about the data...",
        disabled=st.session_state.processing,
    )
    if prompt:
        st.session_state.pending_question = prompt
        st.session_state.processing = True
        st.rerun()

    # ── Process pending question ────────────────────────────
    if st.session_state.pending_question:
        question = st.session_state.pending_question

        # Add user message to history (guard against duplicates)
        if (not st.session_state.messages
                or st.session_state.messages[-1].get("role") != "user"
                or st.session_state.messages[-1].get("content") != question):
            st.session_state.messages.append(
                {"role": "user", "content": question}
            )

        # Render chat history so the user sees their prompt
        for idx, msg in enumerate(st.session_state.messages):
            render_chat_message(msg, msg_idx=idx, is_dark=is_dark)

        # Show cycling loading animation
        loading = st.empty()
        with loading.container():
            render_loading_animation(is_dark)

        # Run the two-pass pipeline
        try:
            process_question(question, df, summary, is_dark, add_user_msg=False)
        finally:
            st.session_state.processing = False
            st.session_state.pending_question = None
        loading.empty()
        st.rerun()

    # ── Render chat history (normal, non-processing path) ───
    if not st.session_state.messages:
        # Show polished welcome screen
        clicked = render_welcome()
        if clicked:
            st.session_state.pending_question = clicked
            st.session_state.processing = True
            st.rerun()
    else:
        for idx, msg in enumerate(st.session_state.messages):
            render_chat_message(msg, msg_idx=idx, is_dark=is_dark)

        # Show suggestions from last assistant message
        last_msg = st.session_state.messages[-1]
        if last_msg["role"] == "assistant":
            suggestions = last_msg.get("suggestions", [])
            clicked = render_suggestions(suggestions)
            if clicked:
                st.session_state.pending_question = clicked
                st.session_state.processing = True
                st.rerun()


if __name__ == "__main__":
    main()
