# User Onboarding & How-To Guide

## Welcome to your Private Business Intelligence Agent!

This tool allows you to query your Canadian Tire mock retail dataset using natural English. **It requires zero internet connection** and all data processing stays securely on your local machine.

### Prerequisites & Launching

1. Ensure you have installed and started **Ollama** locally, and downloaded the required model (`llama3.2:3b`).
   - Run `ollama serve` in a background terminal if it isn't running.
   - Run `ollama run llama3.2:3b` to download the core weights.
2. Ensure you have installed the Python requirements via `pip install -r requirements.txt`.
3. Start the application:
   ```bash
   streamlit run agent.py
   ```

### Using the Interface

#### 1. Asking Questions

Use the chat bar at the bottom to query the data. Try specifically filtering by:

- **Regions:** West, East, Central, Atlantic
- **Divisions:** Sports, Tools, Apparel, Gardening, Food
- **Metrics:** Sales, Margin, Volume, Units
- **Time:** YoY (Year-over-Year), 2023, 2024, or projecting into 2025
- **Stores:** Top/bottom performers, store size analysis
- **Seasonality:** Monthly or quarterly patterns

_Example Queries:_

- "Which division grew the most year over year?"
- "Show me the top brands by sales in the West region"
- "Project Apparel division sales into 2025"
- "What is the pricing sweet spot for Tools?"
- "How is the business performing overall?" _(KPI Scorecard)_
- "Which stores are underperforming?" _(Store Performance)_
- "Is there a seasonal pattern in Gardening?" _(Seasonality Trends)_
- "What percentage of sales does each division represent?" _(Division Mix)_
- "Why did our margins change?" _(Margin Waterfall)_
- "Where are our stars and dogs?" _(Growth-Margin Matrix)_
- "Which categories are most price sensitive?" _(Price Elasticity)_
- "Which brand owns the Fitness category?" _(Brand Benchmarking)_

#### 2. Reading the Assistant's Response

When the agent responds, it provides:

- A text insight highlighting the most important numbers.
- A **badge** indicating which mathematical tool it selected to answer you.
- An interactive **Plotly Chart** (you can hover, zoom, and pan).
- A collapsable **View Data Table** to see the raw numbers backing the chart.
- 3 dynamic **Follow-Up Questions** you can click instantly to dive deeper.

#### 3. Session Memory

The agent **remembers your context**.
If you ask, _"How did Sports perform?"_ and then say _"What about in the West?"_, the agent remembers you are still talking about the Sports division and filters accordingly.

**To reset memory:** Click the "🗑️ Clear Conversation" button in the sidebar.

#### 4. UI Controls

- Use the **🌙 Dark Mode** switch in the sidebar to toggle themes.
- View the **📊 Dataset Overview** in the sidebar to understand the total scale and current KPIs of the loaded CSV.
