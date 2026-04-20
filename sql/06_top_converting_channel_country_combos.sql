-- Business question: Which channel × country combination has the highest CVR?
-- Concepts: GROUP BY two dimensions, ROLLUP for subtotals, HAVING to filter noise
--
-- ROLLUP gives subtotals per channel AND a grand total row — useful for
-- spotting whether a channel's strong overall number is driven by one country.
-- SQLite doesn't support ROLLUP natively, so I'm simulating it with UNION ALL.

WITH base AS (
    SELECT
        country,
        channel,
        COUNT(DISTINCT user_id)                                            AS sessions,
        COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN user_id END) AS purchasers,
        ROUND(
            100.0 * COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN user_id END)
            / NULLIF(COUNT(DISTINCT user_id), 0),
            2
        )                                                                  AS cvr_pct
    FROM events
    GROUP BY country, channel
    HAVING sessions >= 30  -- filter combos with too little data to be meaningful
),

-- channel subtotals (collapsed across country)
channel_totals AS (
    SELECT
        'ALL'    AS country,
        channel,
        SUM(sessions)    AS sessions,
        SUM(purchasers)  AS purchasers,
        ROUND(100.0 * SUM(purchasers) / NULLIF(SUM(sessions), 0), 2) AS cvr_pct
    FROM base
    GROUP BY channel
),

-- grand total
grand_total AS (
    SELECT
        'ALL' AS country,
        'ALL' AS channel,
        SUM(sessions)   AS sessions,
        SUM(purchasers) AS purchasers,
        ROUND(100.0 * SUM(purchasers) / NULLIF(SUM(sessions), 0), 2) AS cvr_pct
    FROM base
)

SELECT country, channel, sessions, purchasers, cvr_pct, 'detail'  AS row_type FROM base
UNION ALL
SELECT country, channel, sessions, purchasers, cvr_pct, 'channel_total' FROM channel_totals
UNION ALL
SELECT country, channel, sessions, purchasers, cvr_pct, 'grand_total'   FROM grand_total
ORDER BY row_type, cvr_pct DESC
;
