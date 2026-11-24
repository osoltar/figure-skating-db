"""Read an event's results index page (index.htm): its segments and its time schedule.

Used by download.py (to find the files to download) and load.py (for segment dates).
"""
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

# Labels on the results page -> codes used in our filenames.
# Anything not listed (Pairs, Ice Dance, Junior Men...) is skipped.
CATEGORIES = {"Men": "M", "Women": "W"}
SEGMENTS = {"Short Program": "SP", "Free Skating": "FS"}

CATEGORY_LINK_RE = re.compile(r"CAT\d+(EN|RS)\.htm$", re.IGNORECASE)
SEG_ID_RE = re.compile(r"(SEG\d+)", re.IGNORECASE)        # "SEG003OF.htm" -> "SEG003"
DATE_RE = re.compile(r"^(\d{2})\.(\d{2})\.(\d{4})$")        # "24.10.2026"
TIME_RE = re.compile(r"^(\d{1,2}:\d{2})(:\d{2})?$")         # "12:30:00"
UTC_RE = re.compile(r"UTC\s*([+-]\d{2}:\d{2})")             # "(Local Time, UTC +01:00)"
LOCATION_RE = re.compile(r"^(.+?)\s*/\s*([A-Z]{3})$")       # "Angers / FRA", "Norwood, MA / USA"
DATE_RANGE_RE = re.compile(r"^(\d{2})\.(\d{2})\.(\d{4})\s*-\s*(\d{2})\.(\d{2})\.(\d{4})$")


def seg_id(href):
    """The segment number in a link, e.g. 'SEG003OF.htm' -> 'SEG003' (None if absent)."""
    match = SEG_ID_RE.search(href or "")
    return match.group(1).upper() if match else None


def find_event_info(html):
    """Read the header of a results index page: where and when the event took place.

    Returns {"city": "Angers", "country": "FRA", "venue": "Angers Ice Parc",
             "start_date": "2026-10-23", "end_date": "2026-10-25"}
    (a value is None if the page doesn't show it).
    """
    soup = BeautifulSoup(html, "html.parser")
    info = dict.fromkeys(["city", "country", "venue", "start_date", "end_date"])

    # Location and venue: two "caption3" cells side by side, "Angers / FRA" | "Angers Ice Parc"
    captions = [" ".join(td.get_text(" ", strip=True).split())
                for td in soup.find_all("td", class_="caption3")]
    for i, text in enumerate(captions):
        match = LOCATION_RE.match(text)
        if match:
            info["city"], info["country"] = match.group(1), match.group(2)
            if i + 1 < len(captions) and captions[i + 1] and not DATE_RANGE_RE.match(captions[i + 1]):
                info["venue"] = captions[i + 1]
            break

    # Dates: a cell with "23.10.2026 - 25.10.2026"
    for td in soup.find_all("td"):
        match = DATE_RANGE_RE.match(td.get_text(strip=True))
        if match:
            d1, m1, y1, d2, m2, y2 = match.groups()
            info["start_date"], info["end_date"] = f"{y1}-{m1}-{d1}", f"{y2}-{m2}-{d2}"
            break
    return info


def find_segments(html, page_url):
    """List the segments we want from a results index page.

    Returns a list of dictionaries:
      {"category": "M", "segment": "SP", "seg_id": "SEG001",
       "panel_url": "...", "pdf_url": "..."}
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
                "seg_id": seg_id(panel[0]),
                "panel_url": urljoin(page_url, panel[0]),
                "pdf_url": urljoin(page_url, pdf[0]),
            })
    return segments


def find_schedule(html):
    """Read the time schedule of a results index page.

    Returns a dictionary keyed by segment number:
      {"SEG001": {"date": "2026-10-24", "time": "12:30", "utc_offset": "+01:00"}, ...}
    """
    soup = BeautifulSoup(html, "html.parser")
    utc = UTC_RE.search(soup.get_text(" "))
    utc_offset = utc.group(1) if utc else None

    schedule = {}
    date = None   # the date of the rows that follow
    for row in soup.find_all("tr"):
        cells = row.find_all("td", recursive=False)
        if not cells:
            continue

        # Date row: "24.10.2026" in the first cell
        day = DATE_RE.match(cells[0].get_text(strip=True))
        if day:
            date = f"{day.group(3)}-{day.group(2)}-{day.group(1)}"   # -> "2026-10-24"
            continue

        # Segment row: (empty) | time | category | link to SEGnnn.htm
        if date is None or len(cells) < 4:
            continue
        time_match = TIME_RE.match(cells[1].get_text(strip=True))
        link = cells[3].find("a")
        if time_match and link and seg_id(link.get("href")):
            schedule[seg_id(link.get("href"))] = {
                "date": date,
                "time": time_match.group(1).zfill(5),   # "9:30" -> "09:30"
                "utc_offset": utc_offset,
            }
    return schedule
