# Phase 6: Dark and Light Mode Configuration

## Overview

Phase 6 introduced a true, high-quality Dark Mode theme switch, allowing the user to seamlessly toggle between entirely separate light and dark CSS configurations locally, bypassing Streamlit's default constraints.

## Key Implementations

### 1. Distinct CSS Overrides (`ui.py`)

- Split the CSS injection into `CUSTOM_CSS_LIGHT` and `CUSTOM_CSS_DARK`.
- Applied extremely aggressive explicit styling to Streamlit base classes (`.stApp`, `.stMarkdown`, `.stChatInput`) using `!important` to force our custom colors over any default OS/Browser inheritance.
- Dark mode utilizes a soft `#0E1117` background, `#262730` containers, and `#FAFAFA` text for maximum legibility and reduced eye strain.

### 2. OS/Theme Isolation (`.streamlit/config.toml`)

- Discovered that Streamlit dynamically fights CSS if the host OS is in Dark Mode while the app toggle is off.
- Solved this by explicitly defining `base="light"` inside a global configuration file, ensuring the app's foundational DOM remains static so our CSS controls the active view exclusively.

### 3. Plotly Dynamic Templating

- Passed the active boolean `is_dark_mode` down from the global session state in `agent.py` through the router and into all 13 target tool scripts.
- Configured Plotly to switch its base template from `plotly_white` to `plotly_dark` dynamically to match the active UI shell.

## Verification

- Extensively tested via an automated browser subagent to ensure zero "color-bleeding" between OS themes and the explicit app toggle. Screen captures confirmed complete edge-to-edge coverage.
