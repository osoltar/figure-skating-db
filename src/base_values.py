"""Expected base value of an element, computed from the ISU Scale of Values.

The loader compares it with the base value printed in the protocol, like the
TES and PCS checks. Rules (2026/27):
  - jumps: sum of the jumps of the element, each looked up with its calls ("3Lz!<");
    a jump marked * and an attempted jump (no rotations) count 0
  - +REP (and +RFE, which the protocols value the same way): 80% (SOV 2026/27 notes)
  - x (second half): +10%
  - ice dance elements with a level per partner: woman's value + man's value
  - combined lifts: sum of the lifts
  - no level, or an invalid element (*): 0
Checked against the protocols:
  - the printed level is already the final one: "<", "<<" (pattern dance) and "S"
    don't lower it further
  - an extra element (+ExEl) keeps its base value (its points are removed elsewhere)
"""
REP_FACTOR = 0.8
REDUCED_FLAGS = {"REP", "RFE"}
SECOND_HALF_BONUS = 1.1

# Signs that are part of the code in the Scale of Values (everything else is ignored
# for the lookup): jump calls, reduced spin (V), novice bonus on death spirals (b)
JUMP_SIGNS = "<qe!b"
OTHER_SIGNS = {"spin": "V", "death_spiral": "b", "twist": "<q"}


class NotInScale(Exception):
    """A code that should be in the Scale of Values but isn't."""


def keep(signs, allowed):
    return "".join(c for c in (signs or "") if c in allowed)


def look_up(sov, code):
    if code not in sov:
        raise NotInScale(code)
    return sov[code]


def jump_value(part, sov):
    if "*" in part["markers"] or part["rotations"] == 0:
        return 0.0
    signs = keep(part["markers"], JUMP_SIGNS)
    if part["jump"] == "Eu":
        return look_up(sov, "Eu" + signs)
    return look_up(sov, f"{part['rotations']}{part['jump']}{signs}")


def leveled_value(sov, base, level, signs=""):
    """Value of an element that has a level, e.g. 'CCoSp' + '4' + 'V'. No level: 0."""
    if level is None:
        return 0.0
    return look_up(sov, f"{base}{level}{signs}")


def element_value(split, sov):
    """Base value before the second-half bonus. Raises NotInScale if a code is missing."""
    kind, markers = split["kind"], split.get("markers") or ""

    if kind == "empty":
        return 0.0

    if kind == "jump":
        total = sum(jump_value(part, sov) for part in split["parts"])
        return total * REP_FACTOR if REDUCED_FLAGS & set(split["flags"]) else total

    if "*" in markers:
        return 0.0

    if kind == "throw":
        return look_up(sov, f"{split['rotations']}{split['jump']}Th{keep(markers, JUMP_SIGNS)}")
    if kind == "twist":
        if split["level"] is None:
            return 0.0
        return look_up(sov, f"{split['rotations']}Tw{split['level']}{keep(markers, '<q')}")

    if kind == "lift":
        total = 0.0
        for base, level in zip(split["base"].split("+"), split["level"].split("+")):
            total += leveled_value(sov, base, level or None)
        return total

    if kind == "pattern":
        return leveled_value(sov, split["base"], split["level"])

    if split.get("level_partner") is not None or split.get("markers_partner") is not None:
        # ice dance element with one level per partner: woman + man
        total = 0.0
        for side, level, signs in [("W", split["level"], markers),
                                   ("M", split.get("level_partner"), split.get("markers_partner") or "")]:
            if "*" in signs:
                continue
            total += leveled_value(sov, split["base"] + side, level)
        return total

    # spins, step sequences, death spirals, pivot, choreographic and creative elements
    return leveled_value(sov, split["base"], split["level"], keep(markers, OTHER_SIGNS.get(kind, "")))


def expected_base_value(element, sov):
    """Expected base value of a parsed element (rounded like the protocols),
    or None if it can't be computed (unknown element or a code missing from the SOV)."""
    split = element["split"]
    if split["kind"] == "unknown":
        return None
    # Whole element invalid. For jumps, "*" in Info can concern only one jump of a
    # combination, so jumps use the * on each jump instead (see jump_value)
    if split["kind"] != "jump" and "*" in element.get("info", []):
        return 0.0
    try:
        value = element_value(split, sov)
    except NotInScale:
        return None
    if element.get("second_half"):
        value *= SECOND_HALF_BONUS
    return round(value + 1e-9, 2)
