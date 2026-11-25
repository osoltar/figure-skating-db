import pytest

from base_values import expected_base_value
from element_codes import split_code

# A few real 2026/27 Scale of Values entries
SOV = {
    "3A": 8.00, "3T": 4.20, "2T": 1.30, "3Lz": 5.90, "3Lz!<": 4.72, "2A": 3.30, "3S": 4.30,
    "Eu": 0.50, "1A": 1.10,
    "CCoSp4": 3.50, "CCoSp4V": 2.63, "StSq4": 3.90, "ChSq1": 3.00,
    "3Tw3": 5.70, "3FTh": 5.30, "3LoTh<": 3.75, "5RLi4": 7.00, "FiDs4": 3.80,
    "CiStW2": 3.36, "CiStM3": 4.10, "RoLi4": 5.45, "CuLi4": 5.45, "1GW3": 8.70, "CDE4": 5.75,
}


def element(code, info=(), second_half=False):
    return {"split": split_code(code), "info": list(info), "second_half": second_half}


@pytest.mark.parametrize("code, expected", [
    ("3A", 8.00),
    ("3Lz!<", 4.72),                 # calls are part of the SOV code
    ("3A+3T", 12.20),                # combination: sum of the jumps
    ("3A+Eu+3S+SEQ", 12.80),         # sequence with an Euler
    ("CCoSp4V", 2.63),               # reduced spin
    ("3Tw3", 5.70), ("3FTh", 5.30), ("3LoTh<", 3.75), ("5RLi4", 7.00), ("FiDs4", 3.80),
    ("CiStW2+CiStM3", 7.46),         # ice dance: woman + man
    ("CuLi4+RoLi4", 10.90),          # combined lift: sum
    ("1GW3+kpYNYY", 8.70),
    ("1GW3+kpYYYY<", 8.70),          # printed level is already the final one
    ("CDE4+ExEl", 5.75),             # extra element keeps its base value
])
def test_expected_base_value(code, expected):
    assert expected_base_value(element(code), SOV) == expected


def test_second_half_bonus():
    assert expected_base_value(element("3A+3T", second_half=True), SOV) == 13.42


def test_repeated_jump_gets_80_percent():
    assert expected_base_value(element("3Lz+REP"), SOV) == 4.72


def test_rfe_is_valued_like_rep():
    # real protocol line: 1A+2A*+Eu*+3S<*+SEQ+RFE, x, printed 0.97 = 1.10 x 0.8 x 1.1
    assert expected_base_value(element("1A+2A*+Eu*+3S<*+SEQ+RFE", second_half=True), SOV) == 0.97


@pytest.mark.parametrize("code, info", [
    ("2T*", ["*"]),            # invalid jump
    ("A", []),                 # attempted jump
    ("CCoSp4", ["*"]),         # invalid spin
    ("PCoSp", []),             # no level
    ("", []),                  # empty slot
])
def test_worth_nothing(code, info):
    assert expected_base_value(element(code, info), SOV) == 0.0


def test_code_missing_from_scale_cannot_be_checked():
    assert expected_base_value(element("4A"), SOV) is None
