# Figure Skating Database

A SQLite database of detailed figure skating scores, built from the official ISU judges' protocols (PDF) and panel of judges pages. Every element, every judge's GOE and every program component mark is stored, together with who sat on each panel, so results can be ranked and compared across competitions, skaters, judges and seasons.

A personal side project to learn git and to build a real data pipeline from start to finish: web pages and messy PDFs → download → parser → validated relational database → queries and charts.

## Current scope

- Season 2026/27: men, women, pairs and ice dance (short program / rhythm dance and free skating / free dance)
- ISU Grand Prix: Skate America, Skate Canada International, Cup of China, Grand Prix de France, Finlandia Trophy
- ISU Challenger Series: Cranberry Cup International, Kinoshita Group Cup, Lombardia Trophy, Nebelhorn Trophy, Trialeti Trophy, Denis Ten Memorial, Budapest Trophy, Tallinn Trophy
- Next: NHK Trophy, Grand Prix Final, remaining Challenger Series events

## How it works

```
results pages ──► download ──► PDFs + panel pages ──► parsers ──► validation ──► SQLite ──► SQL queries
(competitions.csv)            (data/raw)            (pdfplumber,  (TES, PCS,     database    + notebook
                                                     BeautifulSoup) totals, ranks, (data/processed)
                                                                    judges)
```

1. **Download**: `src/download.py` reads each competition's results page (listed in `data/reference/competitions.csv`), finds the senior segments (men, women, pairs, ice dance), and saves the protocol PDF and the panel of judges page for each, using the naming convention below. The index page itself is kept too: its header gives the event's city, country, venue and dates, and its time schedule gives each segment's date and start time. Files already on disk are skipped; events that can't be downloaded automatically are listed at the end.
2. **Parse protocols**: `src/parser.py` reads each protocol line by line and extracts skaters, elements, judges' GOEs and program components.
3. **Split element codes**: `src/element_codes.py` breaks codes like `3Lz!+2T` or `3A+Eu+2S+2A+SEQ` into individual jumps (rotations, jump type, calls such as `<`, `<<`, `q`, `e`, `!`, `*`), and recognises spins, step and choreographic sequences, attempted jumps and empty element slots, plus the pairs and ice dance elements: twists and throws (with rotations and jump type), lifts, death spirals, twizzles, step sequences with a level per partner, and the pattern dance with its key points.
4. **Parse panels**: `src/panel_parser.py` reads the panel of judges page: referee, technical panel, judges 1–9 and operators.
5. **Validate**: for every skater, the element scores must add up to the TES, the factored components to the PCS, and TES + PCS − deductions to the total. The deduction line must add up to the deductions in the header. Ranks must run 1..N without gaps, and the panel must list as many judges as there are judge columns in the scores. Every element's printed base value must match the value computed from the ISU Scale of Values (`src/base_values.py`: calls, combinations, +REP, second-half bonus, levels per partner in ice dance...), and every GOE and component score must match the trimmed mean of the judges' marks (`src/goe.py`). Every number in a protocol is thus recomputed from the raw judges' marks. Anything that doesn't match is reported.
6. **Load**: `src/load.py` rebuilds the database from scratch from all downloaded files plus the hand-curated reference files.

The downloaded files are the source of truth: the database is never edited by hand and can be rebuilt at any time.

## Database

| Table | One row per |
|---|---|
| `competitions` | competition (season, series, event, official name, city, country, venue, dates) |
| `segments` | category + segment of a competition (one protocol PDF), with date and local start time |
| `skaters` | skater |
| `performances` | skater (or pair / ice dance team: `skater_id` + `partner_id`) in a segment: rank, nation, TES, PCS, deductions, total |
| `elements` | executed element: code, kind, level (and partner's level in ice dance), rotations and jump type for throws and twists, base value, GOE, panel score, fall, second half |
| `element_parts` | single jump inside an element, with its rotation and edge calls |
| `element_judge_scores` | judge's GOE for an element, as a grade (−5..+5) and in points |
| `deductions` | deduction of a performance by type (falls with their count, time violation, extended lifts...) |
| `components` | program component of a performance |
| `component_judge_scores` | judge's mark for a component |
| `officials` | judge, technical panel member or referee |
| `panel` | official's role in a segment (judge number 1–9 for judges) and nation at that event |
| `scale_of_values` | element code in the ISU Scale of Values of a season: base value and GOE −5..+5 in points |

The view `competition_results` combines short program and free skating (or rhythm and free dance) into overall results with ranks.

Judge marks are linked to people through the segment and the judge number: J1 in the scores is Judge No. 1 on that segment's panel.

Design choices:
- Skaters and officials get their own ID; their **nation is stored per event**, since people can change countries.
- Pairs and ice dance teams are stored as two skaters on the performance (`skater_id` and `partner_id`), so each person's career can be followed across partners: `WHERE skater_id = X OR partner_id = X`.
- Throws and twists keep their rotations (and jump type for throws) on the element; they are not mixed into the jump tables.
- Neutral athletes keep their protocol code (`AIN1`, `AIN2`).
- Attempted jumps (printed without a number of revolutions, e.g. `A`, `Lo*`) are stored with 0 rotations; the Euler (`Eu`) counts as 1.
- Empty element slots are kept (`kind = 'empty'`) so element numbers match the protocol.

## Example queries

Saved in [`queries/`](queries/):
- best spinners (average spin panel score, base value, GOE and level 4 rate per skater)
- men's triple Axel GOE ranking
- most used jumps in women's programs
- judges' GOE compared with the rest of the panel, including for skaters from their own country
- elements whose printed base value differs from the Scale of Values (none in the 2026/27 data so far)
- points each judge's GOE marks are worth compared with the panel, overall and for their own nation

Charts are in [`notebooks/exploration.ipynb`](notebooks/exploration.ipynb).

## Setup

Requirements: Python 3.12, see `requirements.txt`.

```
pip install -r requirements.txt
```

1. Add each competition to `data/reference/competitions.csv`: season, series, event code, name and the address of its results page (`index.htm`) in `results_url`. City, country, venue and dates are copied from the results page into the empty CSV cells by `download.py`, so the CSV always shows them; values you type yourself are never replaced. Fill them in by hand only when the page can't be downloaded (the loader lists anything still missing).
2. Download the protocols and panel pages:
   ```
   python src/download.py
   ```
   or a single event: `python src/download.py NHKTrophy`. A few result sites refuse automated downloads; their files have to be saved by hand with the same names.
3. Build the database:
   ```
   python src/load.py
   ```
   The ISU Scales of Values of the season go in `data/raw/sov/` as `<season>_SOV_SinglesPairs.pdf` and `<season>_SOV_IceDance.pdf` (ISU Communications, e.g. 2786 and 2803 for 2026/27; US Figure Skating's rules pages host copies).
4. Open `data/processed/skating.db` with any SQLite tool (e.g. DB Browser for SQLite), run the queries in `queries/`, or open the notebook.

Run the tests with:
```
pytest
```

The downloaded files and the database are not stored in the repository (see `.gitignore`).

## File naming

Protocols: `data/raw/season_series_event_category_segment.pdf`, e.g. `26-27_GP_GrandPrixDeFrance_M_SP.pdf`
Panel pages: same name with `.html`, in `data/raw/judges/`

- Season: `26-27`
- Series: `GP`, `CS`, `GPF`, `EC`, `4CC`, `WC`
- Event: official name in CamelCase, same spelling every time (the `event_code` in `competitions.csv`)
- Category: `M`, `W`, `P` (pairs), `ID` (ice dance)
- Segment: `SP`, `FS`; ice dance `RD`, `FD`

## Project structure

```
data/
  raw/          protocol PDFs (not in git)
    judges/     panel of judges pages (not in git)
    index/      results index pages, for the time schedule (not in git)
    sov/        ISU Scales of Values, e.g. 26-27_SOV_SinglesPairs.pdf (not in git)
  processed/    skating.db (not in git)
  reference/    hand-curated data: competitions.csv, sov_additions.csv (SOV codes missing from the PDFs)
notebooks/      exploration notebook with charts
queries/        saved SQL queries
src/
  download.py       downloads protocols, panel pages and index pages
  index_parser.py   results index page → segments and time schedule
  parser.py         protocol PDF → Python data
  element_codes.py  element code splitting
  panel_parser.py   panel of judges page → Python data
  sov_parser.py     Scale of Values PDF → base value and GOE per element code
  base_values.py    expected base value of an element, from the Scale of Values
  goe.py            panel GOE and component scores recomputed from the judges' marks
  schema.sql        tables and views
  create_db.py      creates an empty database
  load.py           builds the database from all files
  explore_pdf.py    prints a PDF's text, for looking at new formats
tests/          pytest tests for the parsers and the downloader
IDEAS.md        planned improvements
```

## Data source

Scores and panels come from the official results published for each event: by the International Skating Union (ISU) for the Grand Prix, and by the organising federations for the Challenger Series. This project is not affiliated with the ISU.
