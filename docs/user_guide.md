# User Guide - Private Business Intelligence Agent

## Getting Started

### Prerequisites

| Tool   | Version | Download                         |
| ------ | ------- | -------------------------------- |
| Python | 3.11+   | [python.org](https://python.org) |
| Ollama | latest  | [ollama.com](https://ollama.com) |

### Installation

```bash
# 1. Clone the repo
git clone <repo-url>
cd Business-Intelligence-Agent

# 2. Create virtual environment (use Python 3.11 specifically)
py -3.11 -m venv venv

# 3. Activate it
source venv/Scripts/activate    # Git Bash
venv\Scripts\activate           # CMD
venv\Scripts\Activate.ps1       # PowerShell

# 4. Install dependencies
pip install -r requirements.txt

# 5. Pull the LLM model (~2 GB download)
ollama pull llama3.2:3b

# 6. Launch the app
streamlit run agent.py
```

The app opens at **http://localhost:8501**.

> **Note:** On Windows, Ollama runs as a background service automatically. On Mac/Linux, you may need to run `ollama serve` in a separate terminal first.

---

## Using the App

### Welcome Screen

When you first open the app, you'll see a welcome card with 5 example questions. Click any of them to get started, or type your own question in the chat input at the bottom.

### Asking Questions

Type a question in natural language. The AI agent will:

1. **Understand** your question using the LLM
2. **Select** the right analysis tool
3. **Generate** a chart and business insight
4. **Suggest** 3 follow-up questions

### Follow-Up Questions

After each response, you'll see 3 suggestion buttons. Click one to ask a follow-up - the agent remembers context from previous questions.

You can also type your own follow-up. The agent tracks:

- Entities you've mentioned (region, brand, division)
- The last tool and filters used
- Key results from the previous analysis

**Example conversation:**

1. _"Which division grew the most year over year?"_ → YoY bar chart
2. Click suggestion: _"How does that compare across regions?"_ → Brand × Region heatmap
3. Type: _"Now forecast it"_ → Trendline with 12-month forecast

### Viewing Data

Each response includes a **"📋 View Data Table"** expander. Click it to see the underlying numbers behind the chart.

### Clearing the Conversation

Click **"🗑️ Clear Conversation"** in the sidebar to reset the chat and start fresh.

---

## Example Questions by Tool

| Tool                    | Example Questions                                                |
| ----------------------- | ---------------------------------------------------------------- |
| **YoY Comparison**      | "Which division grew the most?" / "Compare 2023 vs 2024 sales"   |
| **Brand × Region**      | "Top brands in the West?" / "Show me margin by brand and region" |
| **Forecast**            | "Project Apparel into 2025" / "What's the trend for Sports?"     |
| **Anomaly Detection**   | "Any anomalies in margins?" / "Which products are outliers?"     |
| **Price-Volume-Margin** | "Pricing sweet spot for Tools?" / "Price vs margin relationship" |

---

## Sidebar

The sidebar shows:

- **🔒 Security badge** - green if Ollama is running locally
- **Dataset stats** - total rows, sales by year (with YoY delta), region/division/category/brand counts
- **Clear conversation** button
- **Privacy caption** - reminding that data never leaves the device
