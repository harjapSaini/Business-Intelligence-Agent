# 🏪 Private Business Intelligence Agent

A local, secure retail analytics web app for Canadian Tire - powered by **Streamlit** and **Ollama (llama3.2:3b)**.  
All data stays on your machine. No internet connection required during use.

---

## Prerequisites

| Tool   | Version | Purpose          |
| ------ | ------- | ---------------- |
| Python | 3.11+   | Runtime          |
| Ollama | latest  | Local LLM server |

> **Note:** Python 3.9 will **not** work - Streamlit requires 3.10+ and this project uses 3.11 features.

---

## Setup

### 1. Clone the repo

```bash
git clone <repo-url>
cd Business-Intelligence-Agent
```

### 2. Create a virtual environment

```bash
# Use py launcher to ensure Python 3.11 (not a system default like 3.9)
py -3.11 -m venv venv

# Activate - pick the command for your shell:
# Git Bash (Windows)
source venv/Scripts/activate
# CMD
venv\Scripts\activate
# PowerShell
venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install & start Ollama

Download and install from [ollama.com](https://ollama.com), then pull the model:

```bash
ollama pull llama3.2:3b   # download the model (~2 GB)
```

> **Windows:** Ollama runs as a background service automatically after installation - no need to run `ollama serve`.  
> **macOS / Linux:** You may need to run `ollama serve` in a separate terminal first.

### 5. Run the app

```bash
streamlit run agent.py
```

The app opens at **http://localhost:8501**.

---

## Example Questions

1. "How is the business performing overall?"
2. "Which division grew the most year over year?"
3. "Which stores are underperforming?"
4. "Is there a seasonal pattern in Gardening?"
5. "What percentage of sales does each division represent?"
6. "Why did our margins change?"
7. "Where are our stars and dogs?"
8. "Which categories are most price sensitive?"
9. "Which brand owns the Fitness category?"
10. "Project Apparel division sales into 2025"
11. "Which brand grew the most year over year?"
12. "Show me the top 5 brands by sales in the West region"

---

## Tech Stack

- **UI**: Streamlit (with custom light/dark CSS themes, processing state gate, cycling loading animation)
- **LLM**: Ollama (llama3.2:3b) - runs 100% locally
- **Charts**: Plotly (theme-aware, dynamically re-templated)
- **Routing**: 3-layer safety net (system prompt + keyword guard + filter gap filler)
- **Forecasting**: scikit-learn (LinearRegression)
- **Data**: Pandas + openpyxl
