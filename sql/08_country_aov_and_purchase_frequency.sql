-- Business question: Which country has the highest average order value and repeat rate?
-- Concepts: AVG, COUNT DISTINCT, HAVING, subquery for per-user aggregation
--
-- AOV is only available in the Option A dataset (which has a price column).
-- If price is null for all rows, the AOV columns will show NULL — that's fine,
-- the purchase frequency columns still work regardless.

WITH user_purchases AS (
    -- aggregate to per-user level first, then average — avoids Simpson's paradox
    -- where countries with more purchases per user would skew a naive AVG(price)
    SELECT
        user_id,
        country,
        COUNT(*)        AS purchase_count,
        SUM(price)      AS total_spend
    FROM events
    WHERE event_type = 'purchase'
    GROUP BY user_id, country
)

SELECT
    country,
    COUNT(DISTINCT user_id)                              AS buyers,
    ROUND(AVG(purchase_count), 2)                        AS avg_orders_per_buyer,
    ROUND(AVG(total_spend), 2)                           AS avg_spend_per_buyer,
    -- AOV: average revenue per order (not per user)
    ROUND(SUM(total_spend) / NULLIF(SUM(purchase_count), 0), 2) AS aov,
    -- repeat buyer rate: users with more than 1 purchase
    ROUND(
        100.0 * COUNT(DISTINCT CASE WHEN purchase_count > 1 THEN user_id END)
        / NULLIF(COUNT(DISTINCT user_id), 0),
        2
    )                                                    AS repeat_buyer_rate_pct
FROM user_purchases
GROUP BY country
HAVING buyers >= 20
ORDER BY avg_spend_per_buyer DESC NULLS LAST
;
