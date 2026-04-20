-- Business question: Does paid_social perform differently in NL vs DE?
-- Concepts: self-join to compare channel CVR across country pairs, correlated subquery
--
-- This query is specifically about interaction effects — a channel that works
-- in one country but not another is a localisation/creative problem, not a
-- channel problem. Worth flagging to the media team before cutting budget.

WITH channel_cvr AS (
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
    HAVING sessions >= 50
),

-- national average CVR per channel — benchmark for the correlated subquery
channel_avg AS (
    SELECT
        channel,
        ROUND(AVG(cvr_pct), 2) AS avg_cvr_pct
    FROM channel_cvr
    GROUP BY channel
)

SELECT
    cc.channel,
    cc.country,
    cc.sessions,
    cc.cvr_pct                                              AS country_cvr_pct,
    ca.avg_cvr_pct                                          AS channel_avg_cvr_pct,
    ROUND(cc.cvr_pct - ca.avg_cvr_pct, 2)                  AS vs_channel_avg_pp,
    CASE
        WHEN cc.cvr_pct > ca.avg_cvr_pct * 1.10 THEN 'outperforming'
        WHEN cc.cvr_pct < ca.avg_cvr_pct * 0.90 THEN 'underperforming'
        ELSE 'in_line'
    END                                                     AS performance_flag
FROM channel_cvr cc
JOIN channel_avg ca ON cc.channel = ca.channel
ORDER BY cc.channel, vs_channel_avg_pp DESC
;
