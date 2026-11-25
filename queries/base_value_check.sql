-- Printed base values that differ from the value computed from the Scale of Values
-- (elements.expected_base_value, filled by the loader: see src/base_values.py for the rules).
-- No rows = every element matches. The loader also prints these as warnings.
SELECT c.event_code, s.category, s.segment,
       sk.last_name, e.number, e.code, e.info, e.second_half,
       e.base_value          AS printed,
       e.expected_base_value AS expected
FROM elements e
JOIN performances p ON e.performance_id = p.id
JOIN segments s     ON p.segment_id = s.id
JOIN competitions c ON s.competition_id = c.id
JOIN skaters sk     ON p.skater_id = sk.id
WHERE e.expected_base_value IS NULL
   OR ABS(e.base_value - e.expected_base_value) > 0.01
ORDER BY c.event_code, s.category, s.segment, sk.last_name, e.number;

-- Coverage: how many elements were checked
-- SELECT COUNT(expected_base_value) AS checked, COUNT(*) AS all_elements FROM elements;
