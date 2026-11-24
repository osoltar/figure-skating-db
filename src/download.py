"""Download protocol PDFs and panel pages for the competitions in competitions.csv.

Usage (from the project root):
    python src/download.py                  all competitions with a results_url
    python src/download.py NHKTrophy        only the given event code(s)

Files already on disk are skipped, so running it again only fetches what's new.
"""
import csv
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

RAW_DIR = Path("data/raw")
PANEL_DIR = RAW_DIR / "judges"
COMPETITIONS_CSV = Path("data/reference/competitions.csv")

# Labels on the results page -> codes used in our filenames.
# Anything not listed (Pairs, Ice Dance, Junior Men...) is skipped.
CATEGORIES = {"Men": "M", "Women": "W"}
SEGMENTS = {"Short Program": "SP", "Free Skating": "FS"}

HEADERS = {"User-Agent": "skating-results-db (personal project)"}
TIMEOUT = 30           # seconds to wait for a server before giving up
PAUSE = 1.0            # seconds between downloads, to be polite to the servers

CATEGORY_LINK_RE = re.compile(r"CAT\d+(EN|RS)\.htm$", re.IGNORECASE)


def find_segments(html, page_url):
    """Read a results index page and list the segments we want.

    Returns a list of dictionaries:
      {"category": "M", "segment": "SP", "panel_url": "...", "pdf_url": "..."}
    """
    soup = BeautifulSoup(html, "html.parser")
    segments = []
    category = None   # the category of the rows that follow, None = skip them

    for row in soup.find_all("tr"):
        cells = row.find_all("td", class_="CellLeft", recursive=False)
        if not cells:
            continue
        # The label is the first cell with text (segment rows start with an empty cell)
        texts = [c.get_text(strip=True) for c in cells]
        label = next((t for t in texts if t), "")
        hrefs = [a.get("href", "") for a in row.find_all("a")]

        # Category row: "Men | Entries | Result" (links to CAT001EN.htm / CAT001RS.htm)
        if any(CATEGORY_LINK_RE.search(h) for h in hrefs):
            category = CATEGORIES.get(label)
            continue

        # Segment row: "Short Program | Panel of Judges | ... | Judges Scores (pdf)"
        panel = [h for h in hrefs if h.upper().endswith("OF.HTM")]
        pdf = [h for h in hrefs if h.lower().endswith(".pdf")]
        if category and label in SEGMENTS and panel and pdf:
            segments.append({
                "category": category,
                "segment": SEGMENTS[label],
                "panel_url": urljoin(page_url, panel[0]),
                "pdf_url": urljoin(page_url, pdf[0]),
            })
    return segments


def decode_html(response):
    """Turn a downloaded web page into text, guessing the encoding if the server didn't say."""
    content_type = response.headers.get("Content-Type", "").lower()
    encoding = response.encoding if "charset=" in content_type else response.apparent_encoding
    return response.content.decode(encoding or "utf-8", errors="replace")


def save(path, data):
    """Write a file safely: first to a temporary name, then rename.
    If the download is interrupted, no half-written file is left with the real name."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    if isinstance(data, str):
        tmp.write_text(data, encoding="utf-8")
    else:
        tmp.write_bytes(data)
    tmp.replace(path)


def expected_files(comp):
    """All files we want for a competition, built from the naming convention alone."""
    paths = []
    for category in CATEGORIES.values():
        for segment in SEGMENTS.values():
            stem = f"{comp['season']}_{comp['series']}_{comp['event_code']}_{category}_{segment}"
            paths += [RAW_DIR / f"{stem}.pdf", PANEL_DIR / f"{stem}.html"]
    return paths


def download_competition(session, comp):
    """Download the missing files of one competition.

    Returns (downloaded, skipped, problem), where problem is None if all went well,
    or a short explanation if this competition needs to be downloaded by hand.
    """
    code = comp["event_code"]
    url = (comp.get("results_url") or "").strip()

    problem = None
    if not url:
        problem = "no results_url in competitions.csv"
    else:
        try:
            response = session.get(url, timeout=TIMEOUT)
            response.raise_for_status()
        except requests.HTTPError as err:
            status = err.response.status_code
            problem = ("the site refuses scripts (403)" if status == 403
                       else f"could not open results page (HTTP {status})")
        except requests.RequestException as err:
            problem = f"could not reach results page ({err.__class__.__name__})"

    if problem:
        # The page can't be read, but the files may already have been saved by hand
        missing = [p for p in expected_files(comp) if not p.exists()]
        if not missing:
            return 0, len(expected_files(comp)), None
        print(f"{code}: {problem}")
        return 0, 0, f"{problem}, {len(missing)} files missing"

    segments = find_segments(decode_html(response), url)
    if len(segments) != len(CATEGORIES) * len(SEGMENTS):
        print(f"{code}: WARNING found {len(segments)} segments, "
              f"expected {len(CATEGORIES) * len(SEGMENTS)}")

    downloaded = skipped = failed = 0
    for seg in segments:
        stem = f"{comp['season']}_{comp['series']}_{code}_{seg['category']}_{seg['segment']}"
        targets = [
            (RAW_DIR / f"{stem}.pdf", seg["pdf_url"], "pdf"),
            (PANEL_DIR / f"{stem}.html", seg["panel_url"], "html"),
        ]
        for path, file_url, kind in targets:
            if path.exists():
                skipped += 1
                continue
            try:
                r = session.get(file_url, timeout=TIMEOUT)
                r.raise_for_status()
            except requests.RequestException as err:
                print(f"  {path.name}: FAILED ({err})")
                failed += 1
                continue
            save(path, decode_html(r) if kind == "html" else r.content)
            print(f"  {path.name}: downloaded")
            downloaded += 1
            time.sleep(PAUSE)

    problem = None
    if failed:
        problem = f"{failed} file(s) failed to download"
    elif len(segments) != len(CATEGORIES) * len(SEGMENTS):
        problem = f"found {len(segments)} segments instead of {len(CATEGORIES) * len(SEGMENTS)}"
    return downloaded, skipped, problem


def read_competitions():
    with open(COMPETITIONS_CSV, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main():
    wanted = set(sys.argv[1:])   # event codes given on the command line, if any
    competitions = [c for c in read_competitions()
                    if not wanted or c["event_code"] in wanted]
    if wanted - {c["event_code"] for c in competitions}:
        print("Unknown event code(s):", ", ".join(sorted(wanted - {c["event_code"] for c in competitions})))

    total_downloaded = total_skipped = 0
    to_check = []   # (event_code, problem) for the summary at the end
    with requests.Session() as session:
        session.headers.update(HEADERS)
        for comp in competitions:
            downloaded, skipped, problem = download_competition(session, comp)
            if downloaded or skipped:
                print(f"{comp['event_code']}: {downloaded} downloaded, {skipped} already there")
            if problem:
                to_check.append((comp["event_code"], problem))
            total_downloaded += downloaded
            total_skipped += skipped

    print(f"\nDone: {total_downloaded} files downloaded, {total_skipped} already there.")
    if to_check:
        print("\nDownload manually / check:")
        for code, problem in to_check:
            print(f"  - {code}: {problem}")


if __name__ == "__main__":
    main()
