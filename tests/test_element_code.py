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

# --- Pairs and ice dance (codes from the 2026/27 Scales of Values and real protocols) ---

def test_twist_keeps_rotations_and_level():
    result = split_code("3Tw3")
    assert (result["kind"], result["rotations"], result["level"]) == ("twist", 3, "3")


@pytest.mark.parametrize("code, rotations, jump, markers", [
    ("3FTh", 3, "F", ""),
    ("4STh", 4, "S", ""),
    ("3LoTh<", 3, "Lo", "<"),
])
def test_throw_keeps_type_and_rotations(code, rotations, jump, markers):
    result = split_code(code)
    assert result["kind"] == "throw"
    assert (result["rotations"], result["jump"], result["markers"]) == (rotations, jump, markers)
    assert result["parts"] == []      # throws are not stored as jumps


@pytest.mark.parametrize("code, kind, base, level", [
    ("5RLi4", "lift", "5RLi", "4"),
    ("RoLi4", "lift", "RoLi", "4"),
    ("CuLi4+RoLi4", "lift", "CuLi+RoLi", "4+4"),
    ("FiDs4", "death_spiral", "FiDs", "4"),
    ("BoDsB", "death_spiral", "BoDs", "B"),
    ("PCoSp4V", "spin", "PCoSp", "4"),
    ("PCoSp", "spin", "PCoSp", None),
    ("DSp4", "spin", "DSp", "4"),
    ("ChPSp1", "choreo", "ChPSp", "1"),
    ("ChPLi", "choreo", "ChPLi", None),
    ("CDE4", "choreo", "CDE", "4"),
    ("PiF1", "pivot", "PiF", "1"),
])
def test_pair_and_dance_elements(code, kind, base, level):
    result = split_code(code)
    assert (result["kind"], result["base"], result["level"]) == (kind, base, level)


@pytest.mark.parametrize("code, kind, level, level_partner", [
    ("CiStW2+CiStM3", "step", "2", "3"),
    ("SyTwWB+SyTwM4", "twizzles", "B", "4"),
    ("OFTW1+OFTM2", "turns", "1", "2"),
])
def test_dance_elements_with_a_level_per_partner(code, kind, level, level_partner):
    result = split_code(code)
    assert (result["kind"], result["level"], result["level_partner"]) == (kind, level, level_partner)


def test_pattern_dance_keeps_key_points():
    result = split_code("1GWB+kpNNNN")
    assert (result["kind"], result["base"], result["level"], result["markers"]) == (
        "pattern", "1GW", "B", "NNNN")


def test_novice_bonus_marker():
    assert split_code("3Lz!qb")["parts"][0]["markers"] == "!qb"
