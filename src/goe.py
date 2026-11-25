"""Panel GOE and component scores, recomputed from the judges' marks (2026/27 rules).

Checked against every element and component of the 2026/27 protocols:
  - each judge's GOE (-5..+5) is converted to points with the element's own row of the
    Scale of Values (goe_m5 .. goe_p5), WITHOUT the second-half bonus;
    a jump combination/sequence uses its most valuable jump, an ice dance element with a
    level per partner or a combined lift adds up the rows of its parts
  - the highest and the lowest judge are dropped (trimmed mean), the rest is averaged
    and rounded to 2 decimals
  - components: trimmed mean of the judges' marks, rounded to 2 decimals
"""
from base_values import JUMP_SIGNS, OTHER_SIGNS, keep


def trimmed_mean(values):
    """Average without the highest and the lowest value, rounded to 2 decimals."""
    values = sorted(values)
    if len(values) > 2:
        values = values[1:-1]
    return round(sum(values) / len(values) + 1e-9, 2)


def goe_rows(split, sov_rows):
    """The Scale of Values rows whose GOE values apply to this element.
    Raises KeyError if a code is missing; [] if the element has no value (no level...)."""
    kind, markers = split["kind"], split.get("markers") or ""

    if kind == "jump":
        rows = []
        for part in split["parts"]:
            if part["rotations"] == 0 or "*" in part["markers"]:
                continue
            signs = keep(part["markers"], JUMP_SIGNS)
            code = "Eu" + signs if part["jump"] == "Eu" else f"{part['rotations']}{part['jump']}{signs}"
            rows.append(sov_rows[code])
        # combinations and sequences: the most valuable jump
        return [max(rows, key=lambda r: r["base_value"])] if rows else []

    if kind == "throw":
        return [sov_rows[f"{split['rotations']}{split['jump']}Th{keep(markers, JUMP_SIGNS)}"]]
    if kind == "twist":
        if split["level"] is None:
            return []
        return [sov_rows[f"{split['rotations']}Tw{split['level']}{keep(markers, '<q')}"]]
    if kind == "lift":
        return [sov_rows[base + level]
                for base, level in zip(split["base"].split("+"), split["level"].split("+")) if level]
    if split.get("level_partner") is not None or split.get("markers_partner") is not None:
        return [sov_rows[split["base"] + side + level]
                for side, level in [("W", split["level"]), ("M", split.get("level_partner"))] if level]
    if split.get("level") is None:
        return []
    return [sov_rows[split["base"] + split["level"] + keep(markers, OTHER_SIGNS.get(kind, ""))]]


def goe_points(rows, step):
    """Points for one judge's GOE step (e.g. +3), from the Scale of Values rows."""
    if step == 0 or not rows:
        return 0.0
    column = f"goe_{'p' if step > 0 else 'm'}{abs(step)}"
    return round(sum(row[column] for row in rows), 2)


def panel_goe(element, sov_rows):
    """Recompute an element's GOE from its judges.

    Returns (panel GOE in points, [points of each judge, None for a missing mark]),
    or (None, [None, ...]) when it can't be computed (no marks, unknown element,
    code missing from the Scale of Values).
    """
    judges = element["judges"]
    nothing = (None, [None] * len(judges))
    if element["split"]["kind"] in ("unknown", "empty") or all(j is None for j in judges):
        return nothing
    try:
        rows = goe_rows(element["split"], sov_rows)
    except KeyError:
        return nothing
    points = [None if j is None else goe_points(rows, j) for j in judges]
    return trimmed_mean([p for p in points if p is not None]), points


def component_score(marks):
    """Panel score of a component: trimmed mean of the judges' marks (None if no marks)."""
    marks = [m for m in marks if m is not None]
    return trimmed_mean(marks) if marks else None
