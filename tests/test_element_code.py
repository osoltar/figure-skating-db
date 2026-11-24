import pytest

from element_codes import split_code


def test_single_jump():
    result = split_code("4T")
    assert result["kind"] == "jump"
    assert result["parts"] == [{"position": 1, "rotations": 4, "jump": "T", "markers": ""}]


def test_marker_on_second_jump_of_combination():
    parts = split_code("3F+3T<")["parts"]
    assert [p["jump"] for p in parts] == ["F", "T"]
    assert parts[0]["markers"] == ""
    assert parts[1]["markers"] == "<"


def test_combo_flag_with_single_jump():
    result = split_code("4Lz+COMBO")
    assert result["flags"] == ["COMBO"]
    assert len(result["parts"]) == 1


def test_euler_without_rotation_number():
    parts = split_code("3Lz!<+Eu+2S")["parts"]
    assert parts[0]["markers"] == "!<"
    assert parts[1]["jump"] == "Eu"
    assert parts[1]["rotations"] == 1


def test_sequence_with_four_jumps():
    result = split_code("2A+Eu+3F+2A+SEQ")
    assert result["flags"] == ["SEQ"]
    assert len(result["parts"]) == 4


@pytest.mark.parametrize("code, kind, base, level", [
    ("CCoSp4", "spin", "CCoSp", "4"),
    ("FCSpB", "spin", "FCSp", "B"),
    ("StSq3", "step", "StSq", "3"),
    ("ChSq1", "choreo", "ChSq", "1"),
])
def test_spins_and_sequences(code, kind, base, level):
    result = split_code(code)
    assert result["kind"] == kind
    assert result["base"] == base
    assert result["level"] == level


def test_empty_slot():
    assert split_code("")["kind"] == "empty"


@pytest.mark.parametrize("code", ["XYZ", "3X", "5"])
def test_unrecognised_codes(code):
    assert split_code(code)["kind"] == "unknown"


# Attempted jumps (TP Handbook 2026/27, p. 31): printed without a number of
# revolutions, no value. Stored as 0 rotations.
@pytest.mark.parametrize("code, jump, markers", [
    ("A", "A", ""),
    ("T", "T", ""),
    ("A*", "A", "*"),
    ("Lo*", "Lo", "*"),
])
def test_attempted_jump(code, jump, markers):
    result = split_code(code)
    assert result["kind"] == "jump"
    assert result["parts"] == [{"position": 1, "rotations": 0, "jump": jump, "markers": markers}]


def test_attempted_jump_inside_sequence():
    result = split_code("3Lo<+1A+A+SEQ")
    assert result["flags"] == ["SEQ"]
    assert [(p["rotations"], p["jump"]) for p in result["parts"]] == [(3, "Lo"), (1, "A"), (0, "A")]


def test_euler_still_counts_as_one_rotation():
    parts = split_code("3S+Eu+2S+A+SEQ")["parts"]
    assert [(p["rotations"], p["jump"]) for p in parts] == [(3, "S"), (1, "Eu"), (2, "S"), (0, "A")]


def test_rfe_flag():
    result = split_code("1A+2A*+Eu*+3S<*+SEQ+RFE")
    assert result["kind"] == "jump"
    assert result["flags"] == ["SEQ", "RFE"]
    assert [p["markers"] for p in result["parts"]] == ["", "*", "*", "<*"]