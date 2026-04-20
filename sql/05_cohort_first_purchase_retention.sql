-- Business question: Of users who bought in month N, how many bought again within 60 days?
-- Concepts: cohort construction with MIN(event_time), self-join, date diff
--
-- This is the repeat purchase signal — for a collagen brand that wants LTV,
-- this matters more than first-time CVR. 60-day window because collagen
-- supplements typically run out around then, which is the natural repurchase moment.

WITH first_purchase AS (
    -- anchor each user to their first purchase month
    SELECT
        user_id,
        MIN(event_time) AS first_purchase_time,
        strftime('%Y-%m', MIN(event_time)) AS cohort_month
    FROM events
    WHERE event_type = 'purchase'
    GROUP BY user_id
),

repeat_purchase AS (
    -- find any subsequent purchase within 60 days of the first
    SELECT
        fp.user_id,
        fp.cohort_month,
        fp.first_purchase_time,
        MIN(e.event_time) AS repeat_purchase_time
    FROM first_purchase fp
    JOIN events e
        ON e.user_id = fp.user_id
       AND e.event_type = 'purchase'
       -- must be after the first purchase, not the same event
       AND e.event_time > fp.first_purchase_time
       -- 60-day window — using Julian day diff which SQLite supports natively
       AND (julianday(e.event_time) - julianday(fp.first_purchase_time)) <= 60
    GROUP BY fp.user_id, fp.cohort_month, fp.first_purchase_time
)

SELECT
    fp.cohort_month,
    COUNT(DISTINCT fp.user_id)                    AS cohort_size,
    COUNT(DISTINCT rp.user_id)                    AS repeat_buyers,
    ROUND(
        100.0 * COUNT(DISTINCT rp.user_id)
        / NULLIF(COUNT(DISTINCT fp.user_id), 0),
        2
    )                                             AS retention_60d_pct
FROM first_purchase fp
LEFT JOIN repeat_purchase rp ON fp.user_id = rp.user_id
GROUP BY fp.cohort_month
HAVING cohort_size >= 10  -- need at least 10 buyers to call it a cohort
ORDER BY fp.cohort_month
;
