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

**Fix:** Rephrase your question to be more specific:

- ❌ "Tell me about sales" (too vague)
- ✅ "Compare 2023 vs 2024 sales by division" (clear → YoY comparison)
- ✅ "What's the forecast for Apparel sales?" (clear → forecast)

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

## Getting Help

If you encounter an issue not listed here:

1. Check the terminal output for error messages
2. Verify Ollama is running: `curl http://localhost:11434/api/tags`
3. Verify Python version: `python --version` (must be 3.11+)
4. Try clearing the conversation and asking again
