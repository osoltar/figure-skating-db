-- queries/women_most_used_jumps.sql
SELECT ep.rotations || ep.jump                               AS jump,
       COUNT(*)                                              AS times,
       SUM(e.code LIKE '%+%')                                AS in_combos,
       ROUND(AVG(e.goe), 2)                                  AS avg_goe
FROM element_parts ep
JOIN elements e     ON ep.element_id = e.id
JOIN performances p ON e.performance_id = p.id
JOIN segments s     ON p.segment_id = s.id
WHERE s.category = 'W'
GROUP BY ep.rotations, ep.jump
ORDER BY times DESC;