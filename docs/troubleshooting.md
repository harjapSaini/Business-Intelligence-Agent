# Troubleshooting

## Common Issues

### "Ollama Not Connected" (red badge in sidebar)

**Cause:** Ollama is not running or the model isn't downloaded.

**Fix:**

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running (Mac/Linux):
ollama serve

# If model is missing:
ollama pull llama3.2:3b
```

On Windows, Ollama should auto-start as a background service. If it doesn't, open the Ollama app from the Start menu.

---

### "ImportError: cannot import name 'TypeAlias' from 'typing'"

**Cause:** You're using Python 3.9 instead of 3.11+.

**Fix:**

```bash
rm -rf venv
py -3.11 -m venv venv
source venv/Scripts/activate    # Git Bash
pip install -r requirements.txt
```

---

### First question takes 50+ seconds

**Cause:** The LLM model needs to load into GPU/RAM on the first call.

**Fix:** This is normal. Subsequent questions should take 15–25 seconds. The app already calls `warmup_model()` on startup to pre-load the model, but the first real question may still be slower.

---

### LLM picks the wrong tool

**Cause:** The 3B model sometimes misinterprets ambiguous questions.

**Fix:** The app has a 3-layer routing safety net (system prompt → `validate_routing()` keyword guard → `extract_missing_filters()` gap filler), but you can also help by rephrasing:

- ❌ "Tell me about sales" (too vague)
- ✅ "Compare 2023 vs 2024 sales by division" (clear → YoY comparison)
- ✅ "What's the forecast for Apparel sales?" (clear → forecast)
- ✅ "Which brand grew the most year over year?" (clear → YoY by brand)

---

### Agent says my question is out of scope but it shouldn't be

**Cause:** The keyword guard in `validate_routing()` detected a word that overlaps with out-of-scope topics (e.g., "stock" in "stock level" vs. a brand name containing "stock").

**Fix:** Rephrase to avoid triggering keywords like "customer", "inventory", "stock level", "competitor", "market share", "retention", "churn", "AOV". For example:

- ❌ "What is the customer count?" → triggers out_of_scope
- ✅ "Show total units sold by region" → routes correctly

---

### "Mixed type column names" warning

**Cause:** Some DataFrames used for the heatmap have numeric year columns alongside string columns.

**Impact:** This is cosmetic only - the chart and data still display correctly. The warning appears in the terminal but not in the browser.

---

### Charts don't display / blank area

**Cause:** Usually a Plotly rendering issue on slow connections.

**Fix:** Refresh the page (`F5`). If persistent, try a different browser (Chrome works best with Plotly).

---

### Streamlit won't start on port 8501

**Cause:** Port is already in use from a previous session.

**Fix:**

```bash
# Use a different port
streamlit run agent.py --server.port 8502

# Or kill the existing process (Windows)
netstat -ano | findstr :8501
taskkill /PID <PID> /F
```

---

### Chat input / buttons seem stuck or disabled

**Cause:** The `processing` state flag may be stale if a previous response was interrupted (e.g., by a page refresh during loading).

**Fix:** The app auto-resets this flag on the next page load. If it persists, click "🗑️ Clear Conversation" in the sidebar or refresh the browser page.

---

### Dark mode toggle doesn't work while loading

**Cause:** This is intentional. The toggle is disabled during response processing to prevent the UI from resetting and cancelling the in-progress analysis.

**Fix:** Wait for the current response to finish, then toggle the theme.

---

### First forecast question is very slow

**Cause:** The `forecast_trendline` tool imports `sklearn.linear_model.LinearRegression`. On OneDrive-synced paths, this first import can take 20–40 seconds due to file I/O overhead. Subsequent forecast questions are fast because the module is already cached in memory.

**Fix:** This is a known limitation of running Python projects from OneDrive-synced directories. For faster performance, consider cloning the project to a local (non-synced) directory.

---

## Getting Help

If you encounter an issue not listed here:

1. Check the terminal output for error messages
2. Verify Ollama is running: `curl http://localhost:11434/api/tags`
3. Verify Python version: `python --version` (must be 3.11+)
4. Try clearing the conversation and asking again
