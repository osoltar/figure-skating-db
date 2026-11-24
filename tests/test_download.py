from download import fill_from_page
from index_parser import find_event_info, find_schedule, find_segments

# A cut-down results index page with the same structure as the real ones:
# a category row (with Entries/Result links), then one row per segment.
INDEX_HTML = """
<table>
  <tr><td class="CellLeft">Men</td>
      <td><a href=CAT001EN.htm>Entries</a></td><td><a href=CAT001RS.htm>Result</a></td></tr>
  <tr><td class="CellLeft" valign="top"></td><td class="CellLeft">Short Program</td>
      <td><a href=SEG001OF.htm>Panel of Judges</a></td>
      <td><a href=SEG001.htm>Starting Order / Detailed Classification</a></td>
      <td><a href=FSKMSINGLES-QUAL_JudgesDetailsperSkater.pdf>Judges Scores (pdf)</a></td></tr>
  <tr><td class="CellLeft" valign="top"></td><td class="CellLeft">Free Skating</td>
      <td><a href=SEG002OF.htm>Panel of Judges</a></td>
      <td><a href=FSKMSINGLES-FNL_JudgesDetailsperSkater.pdf>Judges Scores (pdf)</a></td></tr>
  <tr><td class="CellLeft">Women</td>
      <td><a href=CAT002EN.htm>Entries</a></td></tr>
  <tr><td class="CellLeft" valign="top"></td><td class="CellLeft">Short Program</td>
      <td><a href=SEG003OF.htm>Panel of Judges</a></td>
      <td><a href=FSKWSINGLES-QUAL_JudgesDetailsperSkater.pdf>Judges Scores (pdf)</a></td></tr>
  <tr><td class="CellLeft" valign="top"></td><td class="CellLeft">Free Skating</td>
      <td><a href=SEG004OF.htm>Panel of Judges</a></td>
      <td><a href=FSKWSINGLES-FNL_JudgesDetailsperSkater.pdf>Judges Scores (pdf)</a></td></tr>
  <tr><td class="CellLeft">Junior Men</td>
      <td><a href=CAT005EN.htm>Entries</a></td></tr>
  <tr><td class="CellLeft" valign="top"></td><td class="CellLeft">Short Program</td>
      <td><a href=SEG009OF.htm>Panel of Judges</a></td>
      <td><a href=FSKMJUNIOR-QUAL_JudgesDetailsperSkater.pdf>Judges Scores (pdf)</a></td></tr>
  <tr><td class="CellLeft">Ice Dance</td>
      <td><a href=CAT004EN.htm>Entries</a></td></tr>
  <tr><td class="CellLeft" valign="top"></td><td class="CellLeft">Rhythm Dance</td>
      <td><a href=SEG007OF.htm>Panel of Judges</a></td>
      <td><a href=FSKXICEDANCE-QUAL_JudgesDetailsperSkater.pdf>Judges Scores (pdf)</a></td></tr>
  <tr><td></td><td class="CellLeft">19:10:00</td><td class="CellLeft">Men</td>
      <td class="CellLeft"><a href=SEG001.htm>Short Program</a></td></tr>
</table>
"""


def test_finds_senior_segments_and_skips_junior():
    segments = find_segments(INDEX_HTML, "https://example.org/event/index.htm")
    assert [(s["category"], s["segment"]) for s in segments] == [
        ("M", "SP"), ("M", "FS"), ("W", "SP"), ("W", "FS"), ("ID", "RD"),
    ]


def test_links_become_full_urls():
    first = find_segments(INDEX_HTML, "https://example.org/event/index.htm")[0]
    assert first["panel_url"] == "https://example.org/event/SEG001OF.htm"
    assert first["pdf_url"] == "https://example.org/event/FSKMSINGLES-QUAL_JudgesDetailsperSkater.pdf"


def test_results_url_ending_with_slash():
    first = find_segments(INDEX_HTML, "https://example.org/results/")[0]
    assert first["panel_url"] == "https://example.org/results/SEG001OF.htm"


def test_page_without_segments():
    assert find_segments("<html><body>No results yet</body></html>", "https://example.org/") == []


def test_segments_know_their_number():
    segments = find_segments(INDEX_HTML, "https://example.org/event/index.htm")
    assert [s["seg_id"] for s in segments] == ["SEG001", "SEG002", "SEG003", "SEG004", "SEG007"]


# The time schedule part of a real index page (same structure, fewer rows)
SCHEDULE_HTML = """
<table>
  <tr class="caption5"><td>(Local Time, UTC &#x2B;01:00)</td></tr>
  <tr><td>23.10.2026 - 25.10.2026</td></tr>
  <tr class="TabHeadWhite"><th>Date</th><th>Time</th><th>Category</th><th>Segment</th></tr>
  <tr class="TabHeadWhite"><td>23.10.2026</td><td> </td><td> </td><td> </td></tr>
  <tr class=Line1Yellow><td></td><td class="CellLeft">18:00:00</td><td class="CellLeft">Ice Dance</td>
      <td class="CellLeft"><a href=SEG007.htm>Rhythm Dance</a></td></tr>
  <tr class=Line1Red><td></td><td class="CellLeft">19:50:00</td><td class="CellLeft">Women</td>
      <td class="CellLeft"><a href=SEG003.htm>Short Program</a></td></tr>
  <tr class="TabHeadWhite"><td>24.10.2026</td><td> </td><td> </td><td> </td></tr>
  <tr class=Line1Blue><td></td><td class="CellLeft">9:30:00</td><td class="CellLeft">Men</td>
      <td class="CellLeft"><a href=SEG001.htm>Short Program</a></td></tr>
</table>
"""


def test_schedule_dates_and_times():
    schedule = find_schedule(SCHEDULE_HTML)
    assert schedule["SEG003"] == {"date": "2026-10-23", "time": "19:50", "utc_offset": "+01:00"}
    assert schedule["SEG001"] == {"date": "2026-10-24", "time": "09:30", "utc_offset": "+01:00"}


def test_schedule_ignores_event_date_range():
    # "23.10.2026 - 25.10.2026" is the event's dates, not a schedule day
    assert set(find_schedule(SCHEDULE_HTML)) == {"SEG001", "SEG003", "SEG007"}


def test_page_without_schedule():
    assert find_schedule("<html><body>No results yet</body></html>") == {}



HEADER_HTML = """
<table>
  <tr><td class="caption3" width="50%">Norwood,  MA / USA</td>
      <td class="caption3" width="50%">The Skating Club of Boston</td></tr>
  <tr class="caption3"><td>06.08.2026 - 09.08.2026</td></tr>
</table>
"""


def test_event_info_from_header():
    assert find_event_info(HEADER_HTML) == {
        "city": "Norwood, MA", "country": "USA", "venue": "The Skating Club of Boston",
        "start_date": "2026-08-06", "end_date": "2026-08-09",
    }


def test_event_info_missing():
    info = find_event_info("<html><body>Nothing here</body></html>")
    assert all(value is None for value in info.values())




def test_fill_from_page_fills_only_empty_cells():
    comp = {"event_code": "X", "city": "", "country": "FRA", "venue": "", "start_date": "", "end_date": ""}
    info = {"city": "Angers", "country": "ITA", "venue": "Angers Ice Parc",
            "start_date": "2026-10-23", "end_date": None}
    filled = fill_from_page(comp, info)
    assert filled == ["city", "venue", "start_date"]
    assert comp["city"] == "Angers"
    assert comp["country"] == "FRA"      # a value already in the CSV is kept
    assert comp["end_date"] == ""        # nothing found on the page: left empty
