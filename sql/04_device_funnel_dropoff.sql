-- Business question: Where does mobile lose users vs desktop?
-- Concepts: multi-step CTE with one stage per funnel step, CASE WHEN
--
-- Tablet is in the data but the sample size is too small to draw conclusions —
-- I'm keeping it in the output but flagging it so nobody reads too much into it.

WITH user_events AS (
    SELECT
        user_id,
        device,
        MAX(CASE WHEN event_type = 'view'     THEN 1 ELSE 0 END) AS did_view,
        MAX(CASE WHEN event_type = 'cart'     THEN 1 ELSE 0 END) AS did_cart,
        MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS did_purchase
    FROM events
    GROUP BY user_id, device
),

device_agg AS (
    SELECT
        device,
        COUNT(*)           AS total_users,
        SUM(did_view)      AS viewers,
        SUM(did_cart)      AS carted,
        SUM(did_purchase)  AS purchasers
    FROM user_events
    GROUP BY device
)

SELECT
    device,
    viewers,
    carted,
    purchasers,
    ROUND(100.0 * carted     / NULLIF(viewers,   0), 2) AS view_to_cart_pct,
    ROUND(100.0 * purchasers / NULLIF(carted,    0), 2) AS cart_to_purchase_pct,
    ROUND(100.0 * purchasers / NULLIF(viewers,   0), 2) AS overall_cvr_pct,
    CASE
        WHEN total_users < 1000 THEN 'low_sample'
        ELSE 'ok'
    END AS sample_flag
FROM device_agg
ORDER BY overall_cvr_pct DESC
;
