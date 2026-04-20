# Glow25 Conversion Benchmarker

## The problem I noticed

Glow25 sells collagen products across four European markets — Germany, Netherlands, Belgium, and France. They were scaling fast but had no consistent way to see where the purchase funnel behaved differently by country, device, or traffic channel. The headline CVR number tells you something is wrong. It doesn't tell you whether the problem is on the product page, in the cart, or at checkout, and it definitely doesn't tell you whether that problem is worse in France than in Germany.

That's the gap I wanted to close.

Live Link: https://glow-25-coversion-benchmark.streamlit.app/

<img width="2508" height="1263" alt="image" src="https://github.com/user-attachments/assets/64da7929-1670-4718-b475-77d117203da9" />

<img width="2501" height="1180" alt="image" src="https://github.com/user-attachments/assets/defdd3af-f288-4a47-8ff0-4f5ce16dfd7c" />

<img width="2485" height="1162" alt="image" src="https://github.com/user-attachments/assets/8785ce76-7ae4-434e-a9ef-8a2800422820" />

<img width="2518" height="1107" alt="image" src="https://github.com/user-attachments/assets/c236a831-59b8-4fd9-9d6e-f3d2ef8bd942" />


## What I built and why

A full analytics stack around a multi-country DTC purchase funnel:

- **Data ingestion** (`data/ingest.py`) — downloads real e-commerce clickstream data via the Kaggle API, standardises the schema, and overlays Glow25-specific dimensions (country, device, channel). Falls back across three dataset options if the first fails.
- **Jupyter notebook** (`notebooks/glow25_funnel_analysis.ipynb`) — funnel construction, country CVR comparison, device and channel breakdown, channel×country interaction heatmap, and a findings section written as analyst notes.
- **10 SQL files** (`sql/`) — covering funnel conversion by country, channel ROI, weekly WoW trends, device drop-off, cohort retention, checkout abandonment by hour, AOV by country, and session quality scoring. All SQLite-compatible with analyst-style comments.
- **Streamlit app** (`app/streamlit_app.py`) — four pages: funnel overview, country deep-dive with filters, channel performance scatter, and a CRO simulator with sliders that estimates the revenue impact of improving a specific funnel step.

I built this as a portfolio project to show how I think about conversion problems — not just as a reporting exercise but as something that should lead to specific product decisions.

## Key findings

- The view→cart drop is the biggest volume loss, but the country differences are more visible at cart→purchase — which points to checkout trust and payment method issues rather than product-page problems.
- Email converts significantly higher than paid social — it's talking to warm audiences. That doesn't mean you should cut paid social; it means you shouldn't compare their CVRs directly when making budget decisions.
- Mobile CVR lags desktop, which is expected, but the gap suggests the mobile checkout hasn't been properly optimised for one-thumb UX.
- Belgium and France underperform relative to Germany and NL — likely a combination of brand awareness and localised payment method coverage.

## How to run it

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Set up Kaggle credentials**

Go to [kaggle.com/settings](https://www.kaggle.com/settings) → API → Create New Token. Save the downloaded `kaggle.json` to `~/.kaggle/kaggle.json`.

**3. Run data ingestion**
```bash
python data/ingest.py
```

This downloads the dataset, standardises the schema, and saves `data/processed/events_clean.csv`. Takes a couple of minutes on first run.

**4. Run the Streamlit app**
```bash
streamlit run app/streamlit_app.py
```

**5. Open the notebook**
```bash
jupyter notebook notebooks/glow25_funnel_analysis.ipynb
```

**6. Run SQL queries**

Load the SQLite database in Python first (see `sql/README_sql.md`), then run any `.sql` file from the `sql/` folder.

## Live demo

*Coming soon — deploy instructions in `docs/deployment.md`*
