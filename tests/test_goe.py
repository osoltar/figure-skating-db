from element_codes import split_code
from goe import component_score, goe_points, panel_goe, trimmed_mean

STEPS = ["m5", "m4", "m3", "m2", "m1", "p1", "p2", "p3", "p4", "p5"]


def row(base, step):
    """A Scale of Values row where one GOE step is worth `step` points (as for jumps)."""
    values = [-5, -4, -3, -2, -1, 1, 2, 3, 4, 5]
    return {"base_value": base, **{f"goe_{s}": round(v * step, 2) for s, v in zip(STEPS, values)}}


SOV = {"3A": row(8.00, 0.80), "4T": row(9.50, 0.95), "3T": row(4.20, 0.42),
       "CiStW2": row(3.36, 0.34), "CiStM3": row(4.10, 0.41)}


def element(code, judges):
    return {"split": split_code(code), "judges": judges}


def test_trimmed_mean_drops_highest_and_lowest():
    assert trimmed_mean([9.25, 9.50, 9.00, 8.75, 9.25, 8.75, 9.25, 9.00, 9.00]) == 9.07


def test_real_triple_axel():
    # Adam SIAO HIM FA, GP de France SP: 3A x, printed GOE 2.51
    goe, points = panel_goe(element("3A", [3, 3, 3, 4, 3, 3, 2, 3, 4]), SOV)
    assert goe == 2.51
    assert points[0] == 2.40          # judge 1: +3 x 0.80


def test_combination_uses_most_valuable_jump():
    # same skater: 4T+3T, printed GOE -0.27 (steps of the 4T, 0.95)
    goe, _ = panel_goe(element("4T+3T", [-2, -1, 0, 1, 0, -1, 0, -1, 1]), SOV)
    assert goe == -0.27


def test_dance_partner_element_adds_both_rows():
    # +2 for everyone: 2 x (0.34 + 0.41)
    goe, _ = panel_goe(element("CiStW2+CiStM3", [2] * 9), SOV)
    assert goe == 1.50


def test_missing_judge_mark_is_ignored():
    goe, points = panel_goe(element("3A", [3, None, 3, 3, 3, 3, 3, 3, 3]), SOV)
    assert goe == 2.40 and points[1] is None


def test_not_computable():
    assert panel_goe(element("4A", [3] * 9), SOV)[0] is None          # not in this SOV
    assert panel_goe(element("", [None] * 9), SOV)[0] is None         # empty slot


def test_goe_points_zero_step():
    assert goe_points([SOV["3A"]], 0) == 0.0


def test_component_score():
    assert component_score([8.00, 8.25, 8.50, 8.25, 7.75, 9.00, 8.50, 8.00, 8.25]) == 8.25
    assert component_score([None] * 9) is None
