PRAGMA foreign_keys = ON;

-- One row per competition, e.g. GP Grand Prix de France 26-27
CREATE TABLE competitions (
    id          INTEGER PRIMARY KEY,
    season      TEXT NOT NULL,              -- '26-27'
    series      TEXT NOT NULL,              -- 'GP', 'CS', ...
    event_code  TEXT NOT NULL,              -- 'GrandPrixDeFrance' (from the filename)
    name        TEXT,                       -- official name, filled in later
    city        TEXT,                       -- from the results index page, or the CSV
    country     TEXT,
    venue       TEXT,
    start_date  TEXT,                       -- 'YYYY-MM-DD'
    end_date    TEXT,
    UNIQUE (season, series, event_code)
);

-- One row per category + segment of a competition = one PDF
CREATE TABLE segments (
    id              INTEGER PRIMARY KEY,
    competition_id  INTEGER NOT NULL REFERENCES competitions(id),
    category        TEXT NOT NULL,          -- 'M', 'W', 'P' (pairs), 'ID' (ice dance)
    segment         TEXT NOT NULL,          -- 'SP', 'FS'; ice dance 'RD', 'FD'
    date            TEXT,                   -- 'YYYY-MM-DD', from the event's time schedule
    start_time      TEXT,                   -- 'HH:MM', local time
    utc_offset      TEXT,                   -- '+01:00', time zone of start_time
    source_file     TEXT NOT NULL,
    UNIQUE (competition_id, category, segment)
);

CREATE TABLE skaters (
    id          INTEGER PRIMARY KEY,
    first_name  TEXT NOT NULL,
    last_name   TEXT NOT NULL,
    birth_date  TEXT,                       -- 'YYYY-MM-DD', filled in later
    isu_slug    TEXT                        -- 'kevin-aymoz', filled in later
);

-- One skater (or one pair / ice dance team) skating one segment
CREATE TABLE performances (
    id               INTEGER PRIMARY KEY,
    segment_id       INTEGER NOT NULL REFERENCES segments(id),
    skater_id        INTEGER NOT NULL REFERENCES skaters(id),   -- singles skater, or the woman
    partner_id       INTEGER REFERENCES skaters(id),            -- the man in pairs / ice dance, NULL in singles
    nation           TEXT NOT NULL,         -- nation at the time of this event
    rank             INTEGER NOT NULL,
    starting_number  INTEGER NOT NULL,
    total            REAL NOT NULL,
    tes              REAL NOT NULL,
    pcs              REAL NOT NULL,
    deductions       REAL NOT NULL,
    UNIQUE (segment_id, skater_id)
);

CREATE TABLE elements (
    id              INTEGER PRIMARY KEY,
    performance_id  INTEGER NOT NULL REFERENCES performances(id),
    number          INTEGER NOT NULL,       -- order in the program
    code            TEXT NOT NULL,          -- as printed: '3F+3T<'
    kind            TEXT NOT NULL,          -- 'jump', 'spin', 'step', 'choreo', 'creative', 'twist', 'throw', 'lift',
                                            -- 'death_spiral', 'pivot', 'twizzles', 'turns', 'pattern',
                                            -- 'empty', 'unknown'
    info            TEXT NOT NULL DEFAULT '',  -- Info column as printed: 'F <'
    fall            INTEGER NOT NULL DEFAULT 0,   -- F or Fx (multiple falls) in Info
    invalid         INTEGER NOT NULL DEFAULT 0,
    flags           TEXT NOT NULL DEFAULT '',  -- 'COMBO', 'REP', 'SEQ', 'RFE', 'ExEl'
    base            TEXT,                   -- non-jumps: 'CCoSp', 'StSq', 'FiDs', '5RLi', 'CiSt', 'CuLi+RoLi'
    level           TEXT,                   -- '4', 'B'; ice dance: the woman's level; combined lifts: '4+4'
    level_partner   TEXT,                   -- ice dance: the man's level, when each partner has one
    markers_partner TEXT,                   -- ice dance: the man's signs ('S', '*'), same elements
    markers         TEXT,                   -- non-jumps: 'V', '<', '<<', '*'
    key_points      TEXT,                   -- pattern dance: one letter per key point, 'YNYY'
    rotations       INTEGER,                -- throws and twists: number of rotations
    jump            TEXT,                   -- throws: jump type ('S', 'Lo', 'F'...)
    base_value      REAL NOT NULL,
    second_half     INTEGER NOT NULL DEFAULT 0,
    goe             REAL,                   -- NULL if no GOE (element not validated)
    panel_score     REAL NOT NULL,
    UNIQUE (performance_id, number)
);

-- One row per jump inside a jump element
CREATE TABLE element_parts (
    id             INTEGER PRIMARY KEY,
    element_id     INTEGER NOT NULL REFERENCES elements(id),
    position       INTEGER NOT NULL,        -- 1st, 2nd, 3rd jump
    rotations      INTEGER NOT NULL,
    jump           TEXT NOT NULL,           -- 'T', 'S', 'Lo', 'Eu', 'F', 'Lz', 'A'
    markers        TEXT NOT NULL DEFAULT '',   -- as printed: '<', 'q', '!*'
    under_rotated  INTEGER NOT NULL DEFAULT 0, -- <
    downgraded     INTEGER NOT NULL DEFAULT 0, -- <<
    quarter        INTEGER NOT NULL DEFAULT 0, -- q
    wrong_edge     INTEGER NOT NULL DEFAULT 0, -- e
    unclear_edge   INTEGER NOT NULL DEFAULT 0, -- !
    invalid        INTEGER NOT NULL DEFAULT 0, -- *
    UNIQUE (element_id, position)
);

CREATE TABLE element_judge_scores (
    element_id  INTEGER NOT NULL REFERENCES elements(id),
    judge       INTEGER NOT NULL,           -- 1..9
    goe         INTEGER,                    -- NULL if '-'
    PRIMARY KEY (element_id, judge)
);

CREATE TABLE components (
    id              INTEGER PRIMARY KEY,
    performance_id  INTEGER NOT NULL REFERENCES performances(id),
    name            TEXT NOT NULL,          -- 'Composition', 'Presentation', 'Skating Skills'
    factor          REAL NOT NULL,
    panel_score     REAL NOT NULL,
    UNIQUE (performance_id, name)
);

CREATE TABLE component_judge_scores (
    component_id  INTEGER NOT NULL REFERENCES components(id),
    judge         INTEGER NOT NULL,
    mark          REAL,
    PRIMARY KEY (component_id, judge)
);

-- People on officials' panels (judges, technical panel, referee...)
CREATE TABLE officials (
    id          INTEGER PRIMARY KEY,
    first_name  TEXT NOT NULL,
    last_name   TEXT NOT NULL
);

-- Who sat where for each segment
CREATE TABLE panel (
    segment_id    INTEGER NOT NULL REFERENCES segments(id),
    role          TEXT NOT NULL,     -- 'Judge', 'Referee', 'Technical Controller', 'Technical Specialist', ...
    judge_number  INTEGER,           -- 1..9 for judges, NULL for other roles
    official_id   INTEGER NOT NULL REFERENCES officials(id),
    nation        TEXT NOT NULL,     -- nation at that event ('ISU' for the technical panel)
    UNIQUE (segment_id, role, official_id),
    UNIQUE (segment_id, judge_number)
);

-- ISU Scale of Values: base value and GOE in points for every element code, per season.
-- One document for singles + pairs and one for ice dance; a code can be in both with
-- different values (e.g. ChSp1), hence the discipline in the key.
CREATE TABLE scale_of_values (
    season      TEXT NOT NULL,              -- '26-27'
    discipline  TEXT NOT NULL,              -- 'SinglesPairs' or 'IceDance'
    code        TEXT NOT NULL,              -- as in the SOV: '3Lz', '2F!<', 'CCoSp4V', 'CiStW3'
    base_value  REAL NOT NULL,
    goe_m5 REAL, goe_m4 REAL, goe_m3 REAL, goe_m2 REAL, goe_m1 REAL,   -- GOE -5 .. -1 in points
    goe_p1 REAL, goe_p2 REAL, goe_p3 REAL, goe_p4 REAL, goe_p5 REAL,   -- GOE +1 .. +5 in points
    source_file TEXT NOT NULL,
    PRIMARY KEY (season, discipline, code)
);

-- Overall results per competition and category: SP + FS combined, with rank
CREATE VIEW competition_results AS
WITH totals AS (
    SELECT c.id AS competition_id, c.season, c.event_code, c.name AS competition,
           s.category, sk.id AS skater_id, sk.first_name, sk.last_name,
           pa.id AS partner_id, pa.first_name AS partner_first_name,
           pa.last_name AS partner_last_name,
           MAX(p.nation) AS nation,
           SUM(CASE WHEN s.segment IN ('SP', 'RD') THEN p.total END) AS sp,   -- short program / rhythm dance
           SUM(CASE WHEN s.segment IN ('FS', 'FD') THEN p.total END) AS fs,   -- free skating / free dance
           ROUND(SUM(p.total), 2) AS total
    FROM performances p
    JOIN segments s     ON p.segment_id = s.id
    JOIN competitions c ON s.competition_id = c.id
    JOIN skaters sk     ON p.skater_id = sk.id
    LEFT JOIN skaters pa ON p.partner_id = pa.id
    GROUP BY c.id, s.category, sk.id, pa.id
)
SELECT *,
       CASE WHEN fs IS NULL THEN NULL
            ELSE RANK() OVER (PARTITION BY competition_id, category
                              ORDER BY fs IS NULL, total DESC, fs DESC)
       END AS rank
FROM totals;