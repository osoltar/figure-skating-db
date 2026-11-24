# Figure Skating Database

A SQLite database of detailed figure skating scores, built from the official ISU judges' protocols (PDF) and panel of judges pages. Every element, every judge's GOE and every program component mark is stored, together with who sat on each panel, so results can be ranked and compared across competitions, skaters, judges and seasons.

A personal side project to learn git and to build a real data pipeline from start to finish: web pages and messy PDFs → download → parser → validated relational database → queries and charts.

## Current scope

- Season 2026/27, singles (men and women), short program and free skating
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

1. **Download**: `src/download.py` reads each competition's results page (listed in `data/reference/competitions.csv`), finds the senior singles segments, and saves the protocol PDF and the panel of judges page for each, using the naming convention below. Files already on disk are skipped; events that can't be downloaded automatically are listed at the end.
2. **Parse protocols**: `src/parser.py` reads each protocol line by line and extracts skaters, elements, judges' GOEs and program components.
3. **Split element codes**: `src/element_codes.py` breaks codes like `3Lz!+2T` or `3A+Eu+2S+2A+SEQ` into individual jumps (rotations, jump type, calls such as `<`, `<<`, `q`, `e`, `!`, `*`), and recognises spins, step and choreographic sequences, attempted jumps and empty element slots.
4. **Parse panels**: `src/panel_parser.py` reads the panel of judges page: referee, technical panel, judges 1–9 and operators.
5. **Validate**: for every skater, the element scores must add up to the TES, the factored components to the PCS, and TES + PCS − deductions to the total. Ranks must run 1..N without gaps, and the panel must list as many judges as there are judge columns in the scores. Anything that doesn't match is reported.
6. **Load**: `src/load.py` rebuilds the database from scratch from all downloaded files plus the hand-curated reference files.

The downloaded files are the source of truth: the database is never edited by hand and can be rebuilt at any time.

## Database

| Table | One row per |
|---|---|
| `competitions` | competition (season, series, event, official name, city, country, dates) |
| `segments` | category + segment of a competition (one protocol PDF) |
| `skaters` | skater |
| `performances` | skater in a segment: rank, nation, TES, PCS, deductions, total |
| `elements` | executed element: code, base value, GOE, panel score, fall, second half |
| `element_parts` | single jump inside an element, with its rotation and edge calls |
| `element_judge_scores` | judge's GOE for an element |
| `components` | program component of a performance |
| `component_judge_scores` | judge's mark for a component |
| `officials` | judge, technical panel member or referee |
| `panel` | official's role in a segment (judge number 1–9 for judges) and nation at that event |

The view `competition_results` combines short program and free skating into overall results with ranks.

Judge marks are linked to people through the segment and the judge number: J1 in the scores is Judge No. 1 on that segment's panel.

Design choices:
- Skaters and officials get their own ID; their **nation is stored per event**, since people can change countries.
- Neutral athletes keep their protocol code (`AIN1`, `AIN2`).
- Attempted jumps (printed without a number of revolutions, e.g. `A`, `Lo*`) are stored with 0 rotations; the Euler (`Eu`) counts as 1.
- Empty element slots are kept (`kind = 'empty'`) so element numbers match the protocol.

## Example queries

Saved in [`queries/`](queries/):
- best spinners (average spin panel score, base value, GOE and level 4 rate per skater)
- men's triple Axel GOE ranking
- most used jumps in women's programs
- judges' GOE compared with the rest of the panel, including for skaters from their own country

Charts are in [`notebooks/exploration.ipynb`](notebooks/exploration.ipynb).

## Setup

Requirements: Python 3.12, see `requirements.txt`.

```
pip install -r requirements.txt
```

1. Add each competition to `data/reference/competitions.csv`, with the address of its results page (`index.htm`) in `results_url`.
2. Download the protocols and panel pages:
   ```
   python src/download.py
   ```
   or a single event: `python src/download.py NHKTrophy`. A few result sites refuse automated downloads; their files have to be saved by hand with the same names.
3. Build the database:
   ```
   python src/load.py
   ```
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
- Category: `M`, `W` (later `P`, `ID`)
- Segment: `SP`, `FS`

## Project structure

```
data/
  raw/          protocol PDFs (not in git)
    judges/     panel of judges pages (not in git)
  processed/    skating.db (not in git)
  reference/    hand-curated data: competitions.csv
notebooks/      exploration notebook with charts
queries/        saved SQL queries
src/
  download.py       downloads protocols and panel pages
  parser.py         protocol PDF → Python data
  element_codes.py  element code splitting
  panel_parser.py   panel of judges page → Python data
  schema.sql        tables and views
  create_db.py      creates an empty database
  load.py           builds the database from all files
  explore_pdf.py    prints a PDF's text, for looking at new formats
tests/          pytest tests for the parsers and the downloader
IDEAS.md        planned improvements
```

## Data source

Scores and panels come from the official results published for each event: by the International Skating Union (ISU) for the Grand Prix, and by the organising federations for the Challenger Series. This project is not affiliated with the ISU.
