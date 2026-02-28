# Phase 6: Dark and Light Mode Configuration

## Overview

Phase 6 introduced a true, high-quality Dark Mode theme switch, allowing the user to seamlessly toggle between entirely separate light and dark CSS configurations locally, bypassing Streamlit's default constraints. The toggle is protected during response loading to prevent UI resets.

## Key Implementations

### 1. Distinct CSS Overrides (`ui.py`)

- Split the CSS injection into `CUSTOM_CSS_LIGHT` and `CUSTOM_CSS_DARK`.
- Applied extremely aggressive explicit styling to Streamlit base classes (`.stApp`, `.stMarkdown`, `.stChatInput`) using `!important` to force our custom colors over any default OS/Browser inheritance.
- Dark mode utilizes a soft `#0E1117` background, `#262730` containers, and `#FAFAFA` text for maximum legibility and reduced eye strain.
- Full coverage includes: sidebar, buttons, chat input, expanders, DataFrames, metrics, welcome card, tool badges, and the loading animation.

### 2. OS/Theme Isolation (`.streamlit/config.toml`)

- Discovered that Streamlit dynamically fights CSS if the host OS is in Dark Mode while the app toggle is off.
- Solved this by explicitly defining `base="light"` inside a global configuration file, ensuring the app's foundational DOM remains static so our CSS controls the active view exclusively.

### 3. Plotly Dynamic Templating

- Passed the active boolean `is_dark_mode` down from the global session state in `agent.py` through the router and into all 13 target tool scripts.
- Configured Plotly to switch its base template from `plotly_white` to `plotly_dark` dynamically to match the active UI shell.
- Historical charts in chat history are re-templated at render time (`fig.update_layout(template=...)`) so they always match the current toggle state.

### 4. Toggle Protection During Processing

- The dark mode toggle is disabled (`disabled=True`) while `st.session_state.processing` is `True`.
- The `st.rerun()` call after toggle change is guarded: it only fires when the app is not processing a response.
- This prevents the known issue where toggling dark/light mode during response generation would reset the screen and cancel the response.

## Verification

- Extensively tested via an automated browser subagent to ensure zero "color-bleeding" between OS themes and the explicit app toggle. Screen captures confirmed complete edge-to-edge coverage.
- Verified that toggling dark/light mode during response loading does not interrupt the pipeline.
