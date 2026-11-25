-- How many GOE points each judge's marks are worth compared to the panel.
-- For every element: the judge's GOE converted to points (goe_points) minus the
-- panel's GOE (the trimmed mean). Summed per performance, it is the number of
-- points a judge "gave" or "took" compared with the panel, in real score points.
-- Own nation = the judge and the skater (or team) have the same nation at that event.
WITH per_performance AS (
    SELECT pa.official_id, p.id AS performance_id,
           pa.nation = p.nation AS own_nation,
           SUM(ejs.goe_points - e.goe) AS points_vs_panel
    FROM element_judge_scores ejs
    JOIN elements e     ON e.id = ejs.element_id
    JOIN performances p ON p.id = e.performance_id
    JOIN panel pa       ON pa.segment_id = p.segment_id AND pa.judge_number = ejs.judge
    WHERE ejs.goe_points IS NOT NULL AND e.goe IS NOT NULL
    GROUP BY pa.official_id, p.id
)
SELECT o.first_name, o.last_name,
       COUNT(*)                                                        AS performances,
       ROUND(AVG(points_vs_panel), 2)                                  AS avg_points_vs_panel,
       SUM(own_nation)                                                 AS own_nation_performances,
       ROUND(AVG(CASE WHEN own_nation THEN points_vs_panel END), 2)    AS own_nation_avg,
       ROUND(AVG(CASE WHEN NOT own_nation THEN points_vs_panel END), 2) AS other_avg
FROM per_performance pp
JOIN officials o ON o.id = pp.official_id
GROUP BY pp.official_id
HAVING COUNT(*) >= 20
ORDER BY avg_points_vs_panel DESC;
