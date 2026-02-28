# Phase 5: UI Polish & Performance

## Overview

Phase 5 elevated the app's visual presentation from a default Streamlit dashboard to a customized, premium interface matching the Canadian Tire brand identity. Subsequent iterations added a processing state gate, cycling loading animations, a two-column welcome layout, and disabled-state protection on all interactive elements.

## Key Implementations

### 1. Custom CSS Styling

- Injected `CUSTOM_CSS_LIGHT` and `CUSTOM_CSS_DARK` via `inject_custom_css()` to apply the `Inter` font globally.
- Styled the sidebar with a subtle gradient and improved metric label contrast.
- Transformed the default Streamlit buttons into polished interactive elements with hover animations (`translateY(-1px)`, box-shadow) and color transitions.
- Rounded corners on chat messages and added a distinct "tool badge" to the assistant's replies.
- Full coverage of `.stApp`, sidebar, buttons, chat input, expanders, DataFrames, metrics, welcome card, and tool badges in both themes.

### 2. Plotly Theme Synchronization

- Standardized the color palette across all thirteen charts in the `tools/` directory.
- Mapped 2023 to Canadian Tire Red (`#D32F2F`) and 2024 to an Enterprise Blue (`#1976D2`) for consistent visual mapping.
- Charts dynamically switch between `plotly_white` and `plotly_dark` templates at render time, so historical charts in the chat history always match the current theme toggle.

### 3. Welcome Screen Experience

- Designed a custom welcome card in HTML/CSS with a friendly greeting and instructions.
- Rendered 10 default example queries in a **two-column layout** (`st.columns(2)`) as custom-styled, clickable "suggestion" buttons to guide new users on how to interact with the data immediately upon launch.
- Welcome buttons are disabled while a response is processing to prevent double-submissions.

### 4. Sidebar Polish

- Updated the dataset summary logic to compute the year-over-year sales delta percentage, displaying it dynamically alongside the raw total in the sidebar via `st.metric()`.
- Added clear security/privacy messaging throughout the UI.
- Dark mode toggle (`🌙 Dark Mode`) in the sidebar is disabled during processing to prevent UI resets.

### 5. Processing State & Input Locking

- Added `st.session_state.processing` flag that gates all interactive elements during the two-pass pipeline.
- **Chat input** is disabled while a response is loading (`st.chat_input(..., disabled=True)`).
- **Welcome buttons** and **follow-up suggestion buttons** are disabled during processing (`disabled=is_busy`).
- **Dark mode toggle** is disabled during processing to prevent theme switches from resetting the response.
- Stale processing flags are auto-reset if `pending_question` is `None` (handles interrupted runs).

### 6. Cycling Loading Animation

- Replaced the static `st.spinner("🔍 Analysing...")` with a custom HTML/JS loading animation via `streamlit.components.v1.html()`.
- 51 rotating status messages (e.g., "Crunching the numbers...", "Spotting trends...", "Applying AI magic...") cycle every 2.5 seconds with a smooth CSS fade transition.
- A red CSS spinner animates alongside the text.
- Theme-aware: background, border, and text colors adapt to light/dark mode.

### 7. Insight Text Rendering

- Insight text is rendered via `st.html()` instead of `st.markdown()` to bypass Streamlit's markdown parser, which misinterprets number/comma patterns (e.g., "1,234") as inline code spans.
- Text color adapts to the active theme (`#e0e0e0` for dark, `#1a1a1a` for light).

### 8. User Prompt Visibility

- User messages are appended to `st.session_state.messages` and rendered *before* the loading animation starts, so the user's question is always visible while the response loads.

## Verification

- Verified styling visually across all interactive components (buttons, chat inputs, graphs, and sidebars).
- Confirmed animations and hover states triggered correctly without causing Streamlit to unnecessarily re-run.
- Tested that all interactive elements (input, toggles, welcome buttons, suggestion buttons) are properly disabled during processing.
- Verified the loading animation cycles messages smoothly in both light and dark mode.
- Confirmed user prompts are visible in the chat history while the response loads.
