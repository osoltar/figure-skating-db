# Figure Skating Database

A SQLite database of detailed figure skating scores, built from the official ISU judges' protocols (PDF). Every element, every judge's GOE and every program component mark is stored, so results can be ranked and compared across competitions, skaters and seasons.

A personal side project to learn git and to build a real data pipeline from start to finish: messy source files → parser → validated relational database → queries.

## Current scope

- Season 2026/27, singles (men and women), short program and free skating
- ISU Grand Prix: Skate America, Skate Canada International, Cup of China, Grand Prix de France, Finlandia Trophy
- Next:NHK Trophy, Grand Prix Final, Challenger Series

## How it works

```
ISU protocol PDFs ──► parser ──► validation ──► SQLite database ──► SQL queries
   (data/raw)       (pdfplumber)  (TES, PCS,     (data/processed)    (queries/)
                                  totals, ranks)
```

1. **Parse**: `src/parser.py` reads each protocol line by line and extracts skaters, elements, judges' GOEs and program components.
2. **Split element codes**: `src/element_codes.py` breaks codes like `3Lz!+2T` or `3A+Eu+2S+2A+SEQ` into individual jumps (rotations, jump type, calls such as `<`, `<<`, `q`, `e`, `!`, `*`), and recognises spins, step and choreographic sequences.
3. **Validate**: for every skater, the element scores must add up to the TES, the factored components to the PCS, and TES + PCS − deductions to the total. Ranks must run 1..N without gaps. Anything that doesn't match is reported.
4. **Load**: `src/load.py` rebuilds the database from scratch from all PDFs plus the hand-curated reference files.

The PDFs are the source of truth: the database is never edited by hand and can be rebuilt at any time.

## Database

| Table | One row per |
|---|---|
| `competitions` | competition (season, series, event, official name, dates) |
| `segments` | category + segment of a competition (one protocol PDF) |
| `skaters` | skater |
| `performances` | skater in a segment: rank, nation, TES, PCS, deductions, total |
| `elements` | executed element: code, base value, GOE, panel score, fall, second half |
| `element_parts` | single jump inside an element, with its rotation and edge calls |
| `element_judge_scores` | judge's GOE for an element |
| `components` | program component of a performance |
| `component_judge_scores` | judge's mark for a component |

The view `competition_results` combines short program and free skating into overall results with ranks.

Design choices:
- Skaters get their own ID; their **nation is stored per performance**, since skaters can change countries.
- Neutral athletes keep their protocol code (`AIN1`, `AIN2`).
- Empty element slots are kept (`kind = 'empty'`) so element numbers match the protocol.

## Example queries

Saved in [`queries/`](queries/):
- best spinners (average spin panel score, base value, GOE and level 4 rate per skater)
- men's triple Axel GOE ranking
- most used jumps in women's programs

## Setup

Requirements: Python 3.12, see `requirements.txt`.

```
pip install -r requirements.txt
```

1. Download the "Judges details per skater" PDFs from the ISU results pages into `data/raw/`, named as described below.
2. Add each competition to `data/reference/competitions.csv`.
3. Build the database:
   ```
   python src/load.py
   ```
4. Open `data/processed/skating.db` with any SQLite tool (e.g. DB Browser for SQLite) or run the queries in `queries/`.

The PDFs and the database are not stored in the repository (see `.gitignore`).

## File naming

`season_series_event_category_segment.pdf`, e.g. `26-27_GP_GrandPrixDeFrance_M_SP.pdf`

- Season: `26-27`
- Series: `GP`, `CS`, `GPF`, `EC`, `4CC`, `WC`
- Event: official name in CamelCase, same spelling every time
- Category: `M`, `W` (later `P`, `ID`)
- Segment: `SP`, `FS`

## Project structure

```
data/
  raw/          protocol PDFs (not in git)
  processed/    skating.db (not in git)
  reference/    hand-curated data, e.g. competitions.csv
queries/        saved SQL queries
src/
  parser.py         PDF → Python data
  element_codes.py  element code splitting
  schema.sql        tables and views
  create_db.py      creates an empty database
  load.py           builds the database from all PDFs
IDEAS.md        planned improvements
```

## Data source

Scores come from the official protocols published by the International Skating Union (ISU). This project is not affiliated with the ISU.
