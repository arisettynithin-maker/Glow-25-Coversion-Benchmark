-- Business question: What hour of day sees the most cart-to-purchase drop-off?
-- Concepts: strftime() hour extraction, running total with SUM() OVER, abandonment rate
--
-- Knowing the peak abandonment hour helps target checkout recovery emails
-- or push notifications at the right time. This is Berlin time (UTC+1/+2)
-- but the data is stored in UTC — keeping it as UTC here, conversion is a
-- presentation-layer concern.

WITH hourly AS (
    SELECT
        CAST(strftime('%H', event_time) AS INTEGER) AS hour_of_day,
        user_id,
        event_type
    FROM events
    WHERE event_time IS NOT NULL
),

hour_agg AS (
    SELECT
        hour_of_day,
        COUNT(DISTINCT CASE WHEN event_type = 'cart'     THEN user_id END) AS cart_users,
        COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN user_id END) AS purchase_users
    FROM hourly
    GROUP BY hour_of_day
),

with_rates AS (
    SELECT
        hour_of_day,
        cart_users,
        purchase_users,
        -- abandonment = users who carted but didn't purchase in that hour
        cart_users - purchase_users                                              AS abandoned,
        ROUND(
            100.0 * (cart_users - purchase_users) / NULLIF(cart_users, 0),
            2
        )                                                                        AS abandonment_rate_pct,
        -- running total of carts across the day — useful for context
        SUM(cart_users) OVER (ORDER BY hour_of_day ROWS UNBOUNDED PRECEDING)    AS running_carts
    FROM hour_agg
)

SELECT *
FROM with_rates
ORDER BY hour_of_day
;
