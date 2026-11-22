PRAGMA foreign_keys = ON;

-- One row per competition, e.g. GP Grand Prix de France 26-27
CREATE TABLE competitions (
    id          INTEGER PRIMARY KEY,
    season      TEXT NOT NULL,              -- '26-27'
    series      TEXT NOT NULL,              -- 'GP', 'CS', ...
    event_code  TEXT NOT NULL,              -- 'GrandPrixDeFrance' (from the filename)
    name        TEXT,                       -- official name, filled in later
    UNIQUE (season, series, event_code)
);

-- One row per category + segment of a competition = one PDF
CREATE TABLE segments (
    id              INTEGER PRIMARY KEY,
    competition_id  INTEGER NOT NULL REFERENCES competitions(id),
    category        TEXT NOT NULL,          -- 'M', 'W'
    segment         TEXT NOT NULL,          -- 'SP', 'FS'
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

-- One skater skating one segment
CREATE TABLE performances (
    id               INTEGER PRIMARY KEY,
    segment_id       INTEGER NOT NULL REFERENCES segments(id),
    skater_id        INTEGER NOT NULL REFERENCES skaters(id),
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
    kind            TEXT NOT NULL,          -- 'jump', 'spin', 'step', 'choreo', 'empty', 'unknown'
    info            TEXT NOT NULL DEFAULT '',  -- Info column as printed: 'F <'
    fall            INTEGER NOT NULL DEFAULT 0,
    invalid         INTEGER NOT NULL DEFAULT 0,
    flags           TEXT NOT NULL DEFAULT '',  -- 'COMBO', 'REP', 'SEQ'
    base            TEXT,                   -- spins/sequences: 'CCoSp', 'StSq'
    level           TEXT,                   -- spins/sequences: '4', 'B'
    markers         TEXT,                   -- spins/sequences: 'V'
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