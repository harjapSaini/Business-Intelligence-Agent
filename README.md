# 🏪 Retail Analytics Agent

A local, secure retail analytics web app for Canadian Tire — powered by **Streamlit** and **Ollama (llama3.2:3b)**.  
All data stays on your machine. No internet connection required during use.

---

## Prerequisites

| Tool   | Version | Purpose          |
| ------ | ------- | ---------------- |
| Python | 3.10+   | Runtime          |
| Ollama | latest  | Local LLM server |

---

## Setup

### 1. Clone the repo

```bash
git clone <repo-url>
cd Business-Intelligence-Agent
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install & start Ollama

Download from [ollama.com](https://ollama.com), then:

```bash
ollama serve          # start the server (runs on localhost:11434)
ollama pull llama3.2:3b   # download the model (~2 GB)
```

### 5. Run the app

```bash
streamlit run agent.py
```

The app opens at **http://localhost:8501**.

---

## Example Questions

1. "Which division grew the most year over year?"
2. "Show me margin rate by region for 2024"
3. "Which brands perform best in the West region?"
4. "Are there any anomalies in product pricing or margins?"
5. "Project Apparel division sales into 2025"
6. "What is the relationship between price and margin rate in the Tools division?"
7. "Which division has the worst margin rate and has it gotten worse?"
8. "Show me the top 5 brands by sales"
9. "Now break that down by region"
10. "What does the forecast look like for the top brand?"

---

## Tech Stack

- **UI**: Streamlit
- **LLM**: Ollama (llama3.2:3b) — runs 100% locally
- **Charts**: Plotly
- **Forecasting**: scikit-learn (LinearRegression)
- **Data**: Pandas + openpyxl
