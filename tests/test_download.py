from download import find_segments

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


def test_finds_senior_singles_segments_only():
    segments = find_segments(INDEX_HTML, "https://example.org/event/index.htm")
    assert [(s["category"], s["segment"]) for s in segments] == [
        ("M", "SP"), ("M", "FS"), ("W", "SP"), ("W", "FS"),
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
