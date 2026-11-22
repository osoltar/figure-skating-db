import sqlite3
from pathlib import Path

from create_db import create_db, DB_PATH
from parser import parse, check_skater

RAW_DIR = Path("data/raw")


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
    where = " AND ".join(f"{col} = ?" for col in values)
    row = con.execute(f"SELECT id FROM {table} WHERE {where}",
                      tuple(values.values())).fetchone()
    if row:
        return row[0]
    cols = ", ".join(values)
    placeholders = ", ".join("?" for _ in values)
    cur = con.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})",
                      tuple(values.values()))
    return cur.lastrowid


def load_file(con, path):
    """Parse one PDF and insert everything into the database."""
    meta = parse_filename(path)

    competition_id = get_or_create(
        con, "competitions",
        season=meta["season"], series=meta["series"], event_code=meta["event_code"],
    )
    segment_id = con.execute(
        "INSERT INTO segments (competition_id, category, segment, source_file) "
        "VALUES (?, ?, ?, ?)",
        (competition_id, meta["category"], meta["segment"], path.name),
    ).lastrowid

    skaters = parse(path)
    for s in skaters:
        for problem in check_skater(s):
            print(f"  WARNING {path.name} | {s['name']}: {problem}")
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

    return len(skaters)


def main():
    create_db()
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON")
    for path in sorted(RAW_DIR.glob("*.pdf")):
        with con:
            n = load_file(con, path)
        print(f"{path.name}: {n} skaters loaded")
    con.close()


if __name__ == "__main__":
    main()