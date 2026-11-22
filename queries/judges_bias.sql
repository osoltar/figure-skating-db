-- queries/home_judge_goe_delta.sql
WITH judged AS (
    SELECT ejs.element_id, ejs.goe,
           p.id AS performance_id, p.skater_id, p.segment_id,
           p.nation AS skater_nation, pa.nation AS judge_nation, pa.official_id,
           SUM(ejs.goe)   OVER (PARTITION BY ejs.element_id) AS panel_sum,
           COUNT(ejs.goe) OVER (PARTITION BY ejs.element_id) AS panel_count
    FROM element_judge_scores ejs
    JOIN elements e     ON e.id = ejs.element_id
    JOIN performances p ON p.id = e.performance_id
    JOIN panel pa       ON pa.segment_id = p.segment_id
                       AND pa.judge_number = ejs.judge
    WHERE ejs.goe IS NOT NULL
),
home AS (
    SELECT *,
           goe - 1.0 * (panel_sum - goe) / (panel_count - 1) AS delta
    FROM judged
    WHERE judge_nation = skater_nation
)
SELECT c.event_code, s.category, s.segment,
       sk.first_name || ' ' || sk.last_name AS skater,
       o.first_name  || ' ' || o.last_name  AS home_judge,
       h.skater_nation                      AS nation,
       COUNT(*)                             AS elements,
       ROUND(AVG(h.delta), 2)               AS avg_delta
FROM home h
JOIN skaters sk     ON sk.id = h.skater_id
JOIN officials o    ON o.id = h.official_id
JOIN segments s     ON s.id = h.segment_id
JOIN competitions c ON c.id = s.competition_id
GROUP BY h.performance_id, h.official_id
ORDER BY avg_delta DESC;