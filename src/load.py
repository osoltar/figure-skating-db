import csv
import hashlib
import json
import sqlite3
import time
from pathlib import Path

from create_db import create_db, DB_PATH
from parser import parse, check_skater
from panel_parser import parse_panel

RAW_DIR = Path("data/raw")
REFERENCE_DIR = Path("data/reference")
CACHE_DIR = Path("data/processed/parsed")
# If any of these files change, every cached result is outdated
PARSER_FILES = [Path("src/parser.py"), Path("src/element_codes.py")]


def parser_fingerprint():
    """A short code that changes whenever the parser's source code changes."""
    h = hashlib.sha256()
    for path in PARSER_FILES:
        h.update(path.read_bytes())
    return h.hexdigest()[:16]


def parse_cached(path, fingerprint):
    """Parse a PDF, or reuse the saved result from a previous run.

    The saved result is reused only if it was made by the same parser code
    and is newer than the PDF. Returns (skaters, came_from_cache).
    """
    cache = CACHE_DIR / (path.stem + ".json")
    if cache.exists() and cache.stat().st_mtime >= path.stat().st_mtime:
        data = json.loads(cache.read_text(encoding="utf-8"))
        if data.get("parser") == fingerprint:
            return data["skaters"], True

    skaters = parse(path)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"parser": fingerprint, "skaters": skaters}), encoding="utf-8")
    return skaters, False

def read_competitions():
    """Read competitions.csv into a dictionary keyed by (season, series, event_code)."""
    path = REFERENCE_DIR / "competitions.csv"
    with open(path, newline="", encoding="utf-8-sig") as f:
        return {
            (row["season"], row["series"], row["event_code"]):
                {k: (v or None) for k, v in row.items()}
            for row in csv.DictReader(f)
        }


def parse_filename(path):
    """'26-27_GP_GrandPrixDeFrance_M_SP.pdf' -> its five pieces of info."""
    season, series, event_code, category, segment = path.stem.split("_")
    return {
        "season": season,
        "series": series,
        "event_code": event_code,
        "category": category,
        "segment": segment,
    }


def get_or_create(con, table, **values):
    """Return the id of the row matching `values`, inserting it first if needed."""
    where = " AND ".join(f"{col} IS ?" for col in values)
    row = con.execute(f"SELECT id FROM {table} WHERE {where}",
                      tuple(values.values())).fetchone()
    if row:
        return row[0]
    cols = ", ".join(values)
    placeholders = ", ".join("?" for _ in values)
    cur = con.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})",
                      tuple(values.values()))
    return cur.lastrowid


def load_file(con, path, competitions, fingerprint):
    """Parse one PDF and insert everything into the database."""
    meta = parse_filename(path)

    key = (meta["season"], meta["series"], meta["event_code"])
    info = competitions.get(key)
    if info is None:
        print(f"  WARNING {path.name}: {key} not found in competitions.csv")
        info = {}
    competition_id = get_or_create(
        con, "competitions",
        season=meta["season"], series=meta["series"], event_code=meta["event_code"],
        name=info.get("name"), city=info.get("city"), country=info.get("country"),
        start_date=info.get("start_date"), end_date=info.get("end_date"),
    )
    segment_id = con.execute(
        "INSERT INTO segments (competition_id, category, segment, source_file) "
        "VALUES (?, ?, ?, ?)",
        (competition_id, meta["category"], meta["segment"], path.name),
    ).lastrowid
    panel_path = RAW_DIR / "judges" / (path.stem + ".html")
    panel_judges = None   # judge numbers on the panel page, if there is one
    if panel_path.exists():
        panel = parse_panel(panel_path)
        panel_judges = sorted(m["judge_number"] for m in panel if m["role"] == "Judge")
        for member in panel:
            official_id = get_or_create(
                con, "officials",
                first_name=member["first_name"], last_name=member["last_name"],
            )
            con.execute(
                "INSERT INTO panel (segment_id, role, judge_number, official_id, nation) "
                "VALUES (?, ?, ?, ?, ?)",
                (segment_id, member["role"], member["judge_number"], official_id,
                 member["nation"]),
            )
    else:
        print(f"  WARNING {path.name}: no panel file {panel_path.name}")
    skaters, cached = parse_cached(path, fingerprint)
    for s in skaters:
        for problem in check_skater(s):
            print(f"  WARNING {path.name} | {s['name']}: {problem}")
    ranks = sorted(s["rank"] for s in skaters)
    if ranks != list(range(1, len(skaters) + 1)):
        print(f"  WARNING {path.name}: ranks are not 1..{len(skaters)}: {ranks}")

    # Judge count: panel page vs judge columns in the scores
    if panel_judges is not None:
        score_columns = {len(x["judges"]) for s in skaters
                         for x in s["elements"] + s["components"]}
        if len(score_columns) != 1:
            print(f"  WARNING {path.name}: score lines have different numbers "
                  f"of judges: {sorted(score_columns)}")
        n_scores = max(score_columns, default=0)
        if panel_judges != list(range(1, n_scores + 1)):
            print(f"  WARNING {path.name}: panel lists judges {panel_judges} "
                  f"but scores have {n_scores} judge columns")

    for s in skaters:
        skater_id = get_or_create(
            con, "skaters", first_name=s["first_name"], last_name=s["last_name"],
        )
        performance_id = con.execute(
            "INSERT INTO performances (segment_id, skater_id, nation, rank, "
            "starting_number, total, tes, pcs, deductions) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (segment_id, skater_id, s["nation"], s["rank"], s["starting_number"],
             s["total"], s["tes"], s["pcs"], s["deductions"]),
        ).lastrowid

        for e in s["elements"]:
            split = e["split"]
            element_id = con.execute(
                "INSERT INTO elements (performance_id, number, code, kind, info, fall, "
                "invalid, flags, base, level, markers, base_value, second_half, goe, "
                "panel_score) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (performance_id, e["number"], e["code"], split["kind"],
                 " ".join(e["info"]), "F" in e["info"], "*" in e["info"],
                 "+".join(split["flags"]), split.get("base"), split.get("level"),
                 split.get("markers"), e["base_value"], e["second_half"], e["goe"],
                 e["panel_score"]),
            ).lastrowid

            for p in split["parts"]:
                m = p["markers"]
                con.execute(
                    "INSERT INTO element_parts (element_id, position, rotations, jump, "
                    "markers, under_rotated, downgraded, quarter, wrong_edge, "
                    "unclear_edge, invalid) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (element_id, p["position"], p["rotations"], p["jump"], m,
                     "<" in m and "<<" not in m, "<<" in m, "q" in m, "e" in m,
                     "!" in m, "*" in m),
                )

            con.executemany(
                "INSERT INTO element_judge_scores (element_id, judge, goe) VALUES (?, ?, ?)",
                [(element_id, j, goe) for j, goe in enumerate(e["judges"], start=1)],
            )

        for c in s["components"]:
            component_id = con.execute(
                "INSERT INTO components (performance_id, name, factor, panel_score) "
                "VALUES (?, ?, ?, ?)",
                (performance_id, c["name"], c["factor"], c["panel_score"]),
            ).lastrowid
            con.executemany(
                "INSERT INTO component_judge_scores (component_id, judge, mark) "
                "VALUES (?, ?, ?)",
                [(component_id, j, mark) for j, mark in enumerate(c["judges"], start=1)],
            )

    return len(skaters), cached


def main():
    start_all = time.perf_counter()
    create_db()
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    competitions = read_competitions()
    fingerprint = parser_fingerprint()
    n_cached = n_parsed = 0
    for path in sorted(RAW_DIR.glob("*.pdf")):
        start = time.perf_counter()
        with con:
            n, cached = load_file(con, path, competitions, fingerprint)
        seconds = time.perf_counter() - start
        source = "cache" if cached else "parsed"
        print(f"{path.name}: {n} skaters loaded ({source}, {seconds:.2f}s)")
        if cached:
            n_cached += 1
        else:
            n_parsed += 1
    con.close()
    print(f"\n{n_parsed} PDFs parsed, {n_cached} from cache, "
          f"total {time.perf_counter() - start_all:.1f}s")


if __name__ == "__main__":
    main()