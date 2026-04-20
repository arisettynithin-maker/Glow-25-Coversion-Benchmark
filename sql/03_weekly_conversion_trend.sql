-- Business question: Is overall CVR trending up or down week over week?
-- Concepts: strftime() for week bucketing, LAG() to calculate WoW change
--
-- Week-level granularity is the right call here — daily is too noisy for CVR,
-- monthly hides short-term regressions that matter operationally.

WITH weekly_events AS (
    SELECT
        -- SQLite week format: YYYY-WW
        strftime('%Y-%W', event_time) AS week,
        user_id,
        event_type
    FROM events
    WHERE event_time IS NOT NULL
),

weekly_funnel AS (
    SELECT
        week,
        COUNT(DISTINCT user_id)                                            AS sessions,
        COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN user_id END) AS purchasers,
        ROUND(
            100.0 * COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN user_id END)
            / NULLIF(COUNT(DISTINCT user_id), 0),
            2
        )                                                                  AS cvr_pct
    FROM weekly_events
    GROUP BY week
),

with_wow AS (
    SELECT
        week,
        sessions,
        purchasers,
        cvr_pct,
        LAG(cvr_pct) OVER (ORDER BY week) AS prev_week_cvr,
        ROUND(
            cvr_pct - LAG(cvr_pct) OVER (ORDER BY week),
            2
        )                                  AS wow_cvr_change_pp  -- pp = percentage points
    FROM weekly_funnel
)

SELECT *
FROM with_wow
ORDER BY week
;
