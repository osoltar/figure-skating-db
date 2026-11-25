import pytest

from parser import SKATER_RE, check_skater, parse_component, parse_element, parse_skater

SKATER_LINE = "1 Adam SIAO HIM FA FRA 11 102.46 57.25 45.21 0.00"
ELEMENT_LINES = [
    "1 4T+3T 13.70 -0.27 -2 -1 0 1 0 -1 0 -1 1 13.43",
    "2 4S 9.70 2.91 3 3 4 3 3 3 2 3 3 12.61",
    "3 FCSp4 3.80 0.98 2 3 3 3 2 2 2 3 3 4.78",
    "4 3A 8.80 x 2.51 3 3 3 4 3 3 2 3 4 11.31",
    "5 StSq4 4.10 1.82 5 5 4 5 4 4 4 5 4 5.92",
    "6 CCoSp3 3.60 0.87 1 2 3 3 3 2 2 2 3 4.47",
    "7 CSSp4 3.60 1.13 2 4 4 4 3 3 2 3 3 4.73",
]
COMPONENT_LINES = [
    "Composition 1.67 9.25 9.50 9.00 8.75 9.25 8.75 9.25 9.00 9.00 9.07",
    "Presentation 1.67 9.25 9.25 9.25 8.75 9.00 9.25 9.00 9.25 9.25 9.18",
    "Skating Skills 1.67 9.00 9.00 8.75 9.00 8.75 8.75 8.75 8.75 8.75 8.82",
]


@pytest.fixture
def skater():
    """A complete, valid skater built from real protocol lines."""
    s = parse_skater(SKATER_RE.match(SKATER_LINE))
    s["elements"] = [parse_element(line) for line in ELEMENT_LINES]
    s["components"] = [parse_component(line) for line in COMPONENT_LINES]
    return s


def test_skater_line():
    s = parse_skater(SKATER_RE.match(SKATER_LINE))
    assert s["first_name"] == "Adam"
    assert s["last_name"] == "SIAO HIM FA"
    assert s["nation"] == "FRA"
    assert s["total"] == 102.46


def test_neutral_athlete_keeps_digit():
    match = SKATER_RE.match("2 Petr IVANOV AIN2 8 85.00 45.00 40.00 0.00")
    assert match is not None
    assert parse_skater(match)["nation"] == "AIN2"


def test_second_half_bonus():
    e = parse_element("4 3A 8.80 x 2.51 3 3 3 4 3 3 2 3 4 11.31")
    assert e["second_half"] is True
    assert e["base_value"] == 8.80
    assert e["goe"] == 2.51
    assert len(e["judges"]) == 9


def test_info_markers_are_split():
    e = parse_element("2 4S< F < 7.76 -3.88 -5 -5 -5 -5 -5 -5 -5 -5 -5 3.88")
    assert e["code"] == "4S<"
    assert e["info"] == ["F", "<"]


def test_empty_slot():
    e = parse_element("12 0.00 0.00 - - - - - - - - - 0.00")
    assert e["code"] == ""
    assert e["split"]["kind"] == "empty"
    assert e["goe"] == 0.0
    assert e["judges"] == [None] * 9


@pytest.mark.parametrize("line", [
    SKATER_LINE,
    "47.30 57.25",
    "Program Components Factor",
    "printed: 24.10.2026 14:04 report created by",
])
def test_other_lines_are_not_elements(line):
    assert parse_element(line) is None


def test_component_line():
    c = parse_component(COMPONENT_LINES[0])
    assert c["name"] == "Composition"
    assert c["factor"] == 1.67
    assert len(c["judges"]) == 9
    assert c["panel_score"] == 9.07


def test_valid_skater_has_no_problems(skater):
    assert check_skater(skater) == []


def test_wrong_tes_is_reported(skater):
    skater["tes"] = 50.00
    problems = check_skater(skater)
    assert any("TES" in p for p in problems)

def test_pair_team_is_split_into_two_people():
    s = parse_skater(SKATER_RE.match(
        "1 Anastasiia METELKINA / Luka BERULAVA GEO 8 127.31 59.95 68.36 -1.00"))
    assert (s["first_name"], s["last_name"]) == ("Anastasiia", "METELKINA")
    assert (s["partner_first_name"], s["partner_last_name"]) == ("Luka", "BERULAVA")
    assert s["deductions"] == -1.00


def test_singles_skater_has_no_partner():
    s = parse_skater(SKATER_RE.match(SKATER_LINE))
    assert s["partner_first_name"] is None and s["partner_last_name"] is None


# --- Deduction line (all shapes found in the 2026/27 protocols) ---
from parser import parse_deductions


@pytest.mark.parametrize("line, items, total", [
    ("Deductions: 0.00", [], 0.0),
    ("Deductions: Falls -1.00 (1) -1.00", [("Falls", -1.0, 1)], -1.0),
    ("Deductions: Time violation -1.00 Falls -2.00 (2) -3.00",
     [("Time violation", -1.0, None), ("Falls", -2.0, 2)], -3.0),
    ("Deductions: Illegal element/movement -2.00 Extended lifts -1.00 -3.00",
     [("Illegal element/movement", -2.0, None), ("Extended lifts", -1.0, None)], -3.0),
    ("Deductions: Interruption in excess -1.00 Falls -2.00 (2) -3.00",
     [("Interruption in excess", -1.0, None), ("Falls", -2.0, 2)], -3.0),
])
def test_deduction_line(line, items, total):
    parsed, parsed_total = parse_deductions(line)
    assert [(d["type"], d["points"], d["count"]) for d in parsed] == items
    assert parsed_total == total


def test_other_lines_are_not_deductions():
    assert parse_deductions("Judges Total Program Component Score (factored) 45.21") is None


def test_deductions_must_match_the_header(skater):
    skater["deduction_items"], skater["deduction_total"] = [], 0.0
    assert check_skater(skater) == []
    skater["deduction_items"] = [{"type": "Falls", "points": -1.0, "count": 1}]
    skater["deduction_total"] = -1.0
    assert any("header" in p for p in check_skater(skater))
