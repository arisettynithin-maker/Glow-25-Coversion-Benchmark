-- Business question: Which acquisition channel drives the highest purchase CVR?
-- Concepts: GROUP BY, RANK() window function within country partitions
--
-- Ranking within country matters here — paid_social might be #1 overall
-- but if it tanks in DE (our biggest market) that's a budget allocation problem.

WITH channel_country AS (
    SELECT
        country,
        channel,
        COUNT(DISTINCT user_id)                                                  AS sessions,
        COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN user_id END)       AS purchasers,
        ROUND(
            100.0 * COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN user_id END)
            / NULLIF(COUNT(DISTINCT user_id), 0),
            2
        )                                                                        AS cvr_pct
    FROM events
    GROUP BY country, channel
),

ranked AS (
    SELECT
        *,
        -- DENSE_RANK so tied channels don't skip positions
        DENSE_RANK() OVER (PARTITION BY country ORDER BY cvr_pct DESC) AS rank_in_country
    FROM channel_country
    -- filter noise: channels with < 50 sessions in a country aren't reliable
    WHERE sessions >= 50
)

SELECT
    country,
    channel,
    sessions,
    purchasers,
    cvr_pct,
    rank_in_country
FROM ranked
ORDER BY country, rank_in_country
;
