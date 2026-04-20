-- Business question: Which country has the worst checkout-to-purchase drop-off?
-- Concepts: multi-step CTE, conditional aggregation, conversion rate calculation
--
-- I'm building a stage-by-stage funnel so I can see exactly where each market
-- loses users, not just the overall CVR. The cart→purchase step is usually where
-- the real differences show up (payment trust, shipping cost, etc.)

WITH base AS (
    -- one row per user-country-event so we don't double-count users
    -- who triggered the same event multiple times in a session
    SELECT
        user_id,
        country,
        MAX(CASE WHEN event_type = 'view'     THEN 1 ELSE 0 END) AS did_view,
        MAX(CASE WHEN event_type = 'cart'     THEN 1 ELSE 0 END) AS did_cart,
        MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS did_purchase
    FROM events
    GROUP BY user_id, country
),

country_funnel AS (
    SELECT
        country,
        COUNT(*)                                        AS total_users,
        SUM(did_view)                                   AS viewers,
        SUM(did_cart)                                   AS carted,
        SUM(did_purchase)                               AS purchasers
    FROM base
    GROUP BY country
)

SELECT
    country,
    viewers,
    carted,
    purchasers,
    -- view-to-cart rate: where does intent drop off?
    ROUND(100.0 * carted    / NULLIF(viewers,    0), 2) AS view_to_cart_pct,
    -- cart-to-purchase rate: the critical checkout conversion
    ROUND(100.0 * purchasers / NULLIF(carted,   0), 2) AS cart_to_purchase_pct,
    -- overall funnel CVR
    ROUND(100.0 * purchasers / NULLIF(viewers,  0), 2) AS overall_cvr_pct
FROM country_funnel
ORDER BY overall_cvr_pct ASC  -- worst performers at the top
;
