-- queries/best_spinners.sql
SELECT s.category, sk.first_name, sk.last_name,
       COUNT(*)                                      AS spins,
       ROUND(AVG(e.panel_score), 2)                  AS avg_score,
       ROUND(AVG(e.base_value), 2)                   AS avg_base_value,
       ROUND(AVG(e.goe), 2)                          AS avg_goe,
       ROUND(100.0 * SUM(e.level = '4') / COUNT(*))  AS pct_level4
FROM elements e
JOIN performances p ON e.performance_id = p.id
JOIN segments s     ON p.segment_id = s.id
JOIN skaters sk     ON p.skater_id = sk.id
WHERE e.kind = 'spin' AND s.category = 'W'
GROUP BY s.category, sk.id
HAVING COUNT(*) >= 6
ORDER BY s.category, avg_score DESC;