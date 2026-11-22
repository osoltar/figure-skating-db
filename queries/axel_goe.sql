-- queries/men_3A_goe_ranking.sql
SELECT RANK() OVER (ORDER BY e.goe DESC) AS rank,
       sk.first_name, sk.last_name, c.event_code, s.segment,e.base_value, e.goe, e.panel_score
FROM element_parts ep
JOIN elements e     ON ep.element_id = e.id
JOIN performances p ON e.performance_id = p.id
JOIN segments s     ON p.segment_id = s.id
JOIN competitions c ON s.competition_id = c.id
JOIN skaters sk     ON p.skater_id = sk.id
WHERE s.category = 'M'
  AND ep.jump = 'A' AND ep.rotations = 3
  AND e.code NOT LIKE '%+%'
ORDER BY e.goe DESC
LIMIT 20;