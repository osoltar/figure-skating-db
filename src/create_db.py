import sqlite3
from pathlib import Path

DB_PATH = Path("data/processed/skating.db")
SCHEMA_PATH = Path("src/schema.sql")


def create_db():
    """Delete the old database (if any) and create empty tables."""
    if DB_PATH.exists():
        DB_PATH.unlink()
    con = sqlite3.connect(DB_PATH)
    con.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    con.close()


if __name__ == "__main__":
    create_db()
    print("Created", DB_PATH)