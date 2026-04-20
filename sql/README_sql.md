# SQL Analysis — Glow25 Conversion Benchmarker

All queries run against a local SQLite database (`data/glow25.db`).
Load it first with:

```python
import sqlite3, pandas as pd
df = pd.read_csv('data/processed/events_clean.csv')
conn = sqlite3.connect('data/glow25.db')
df.to_sql('events', conn, if_exists='replace', index=False)
```

---

| # | File | Business Question | Key SQL Concepts |
|---|------|------------------|-----------------|
| 01 | `01_funnel_conversion_by_country.sql` | Which country has the worst checkout-to-purchase drop-off? | Multi-step CTE, conditional aggregation, conversion rate |
| 02 | `02_channel_roi_comparison.sql` | Which acquisition channel drives the highest purchase CVR? | GROUP BY, RANK() window function within country partitions |
| 03 | `03_weekly_conversion_trend.sql` | Is overall CVR trending up or down week over week? | strftime() week bucketing, LAG() for WoW delta |
| 04 | `04_device_funnel_dropoff.sql` | Where does mobile lose users vs desktop? | Multi-step CTE per funnel stage, CASE WHEN scoring |
| 05 | `05_cohort_first_purchase_retention.sql` | Of users who bought in month N, how many bought again within 60 days? | Cohort construction with MIN(), self-join, julianday() diff |
| 06 | `06_top_converting_channel_country_combos.sql` | Which channel × country combo has the highest CVR? | GROUP BY two dims, UNION ALL rollup simulation, HAVING |
| 07 | `07_checkout_abandonment_by_hour.sql` | What hour of day sees the most cart-to-purchase drop-off? | strftime() hour extraction, SUM() OVER running total |
| 08 | `08_country_aov_and_purchase_frequency.sql` | Which country has the highest AOV and repeat rate? | AVG, COUNT DISTINCT, HAVING, per-user subquery aggregation |
| 09 | `09_channel_country_interaction.sql` | Does paid_social perform differently in NL vs DE? | Self-join for cross-country comparison, correlated subquery |
| 10 | `10_session_quality_score.sql` | Which sessions are highest quality based on funnel depth? | CASE WHEN depth scoring, correlated subquery vs country avg, DENSE_RANK |
