-- Printed base values compared with the Scale of Values, for elements whose code
-- is listed in the SOV exactly as printed (single jumps with their calls, spins,
-- step sequences, twists, throws, lifts, death spirals, choreo...).
-- Second-half jumps (x) get their 10% bonus.
-- Not covered yet: combinations/sequences (+), dance elements with a level per
-- partner, pattern dances, +REP, invalid elements (*).
--
-- Every row returned is a difference to look at. No rows = everything matches.
SELECT c.event_code, s.category, s.segment,
       sk.last_name, e.number, e.code, e.second_half,
       e.base_value AS printed,
       ROUND(sov.base_value * CASE WHEN e.second_half THEN 1.1 ELSE 1 END, 2) AS expected
FROM elements e
JOIN performances p     ON e.performance_id = p.id
JOIN segments s         ON p.segment_id = s.id
JOIN competitions c     ON s.competition_id = c.id
JOIN skaters sk         ON p.skater_id = sk.id
JOIN scale_of_values sov
     ON sov.season = c.season
    AND sov.code = e.code
    AND sov.discipline = CASE WHEN s.category = 'ID' THEN 'IceDance' ELSE 'SinglesPairs' END
WHERE ABS(e.base_value - ROUND(sov.base_value * CASE WHEN e.second_half THEN 1.1 ELSE 1 END, 2)) > 0.01
ORDER BY c.event_code, s.category, s.segment, sk.last_name, e.number;

-- How many elements this check covers, out of all elements:
-- SELECT COUNT(sov.code) AS checked, COUNT(*) AS all_elements
-- FROM elements e
-- JOIN performances p ON e.performance_id = p.id
-- JOIN segments s     ON p.segment_id = s.id
-- JOIN competitions c ON s.competition_id = c.id
-- LEFT JOIN scale_of_values sov
--      ON sov.season = c.season AND sov.code = e.code
--     AND sov.discipline = CASE WHEN s.category = 'ID' THEN 'IceDance' ELSE 'SinglesPairs' END;
