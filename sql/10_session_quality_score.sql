-- Business question: Which sessions are highest quality based on funnel depth reached?
-- Concepts: CASE WHEN to score funnel depth, correlated subquery to benchmark vs
--           country average, DENSE_RANK
--
-- "Session quality" is a composite signal: how far did the user get through the funnel?
-- This is useful for audience segmentation — high-quality non-converters are the
-- most valuable retargeting pool.

WITH user_depth AS (
    SELECT
        user_id,
        country,
        channel,
        device,
        -- score funnel depth: purchase > cart > view
        MAX(
            CASE event_type
                WHEN 'purchase' THEN 3
                WHEN 'cart'     THEN 2
                WHEN 'view'     THEN 1
                ELSE 0
            END
        ) AS depth_score,
        COUNT(*) AS total_events
    FROM events
    GROUP BY user_id, country, channel, device
),

scored AS (
    SELECT
        *,
        CASE depth_score
            WHEN 3 THEN 'converted'
            WHEN 2 THEN 'carted_no_purchase'
            WHEN 1 THEN 'view_only'
            ELSE 'unknown'
        END AS quality_label,
        -- how does this user's depth compare to the country average?
        -- correlated subquery — slightly expensive but clear
        (
            SELECT ROUND(AVG(ud2.depth_score), 2)
            FROM user_depth ud2
            WHERE ud2.country = user_depth.country
        ) AS country_avg_depth
    FROM user_depth
),

ranked AS (
    SELECT
        *,
        ROUND(depth_score - country_avg_depth, 2) AS vs_country_avg,
        -- DENSE_RANK within country so we can pull top-N per market
        DENSE_RANK() OVER (
            PARTITION BY country
            ORDER BY depth_score DESC, total_events DESC
        ) AS rank_in_country
    FROM scored
)

SELECT
    user_id,
    country,
    channel,
    device,
    depth_score,
    quality_label,
    total_events,
    country_avg_depth,
    vs_country_avg,
    rank_in_country
FROM ranked
ORDER BY country, rank_in_country
LIMIT 500  -- preview only; remove LIMIT to get the full set
;
