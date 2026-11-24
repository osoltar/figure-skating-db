import re

# --- Singles (and side-by-side jumps in pairs) --------------------------------
# A single jump, e.g. "4T", "3Lz!", "3A<", "4Tq", "1Lz!*", "2A<<"
# ("b" = bonus, Advanced Novice only)
JUMP_RE = re.compile(
    r"^(?P<rotations>\d)?(?P<jump>Lz|Lo|Eu|A|F|S|T)(?P<markers>[<q!e*b]*)$"
)
# Spins and sequences, e.g. "CCoSp4", "FCSpB", "CSSp3V", "StSq4", "PCoSp4V", "DSp4", "PCoSp"
OTHER_RE = re.compile(
    r"^(?P<base>[A-Za-z]*?(?:Sp|Sq))(?P<level>B|\d)?(?P<markers>[V*]*)$"
)
# Choreographic elements, e.g. "ChSq1", "ChPLi1", "ChPSp1", "ChAJ1", "ChSl1", "ChPLi"
# CDE (rhythm dance): Choreographic Dance Element
CHOREO_RE = re.compile(r"^(?P<base>Ch[A-Za-z]+|CDE)(?P<level>[1-4B])?(?P<markers>[*]*)$")

# --- Pairs ---------------------------------------------------------------------
# Twist lift, e.g. "3Tw3": rotations, then level
TWIST_RE = re.compile(r"^(?P<rotations>\d)Tw(?P<level>[1-4B])?(?P<markers>[<q*]*)$")
# Throw jump, e.g. "3FTh", "4STh", "3LoTh<": rotations, jump type, "Th"
THROW_RE = re.compile(
    r"^(?P<rotations>\d)?(?P<jump>Lz|Lo|Eu|A|F|S|T)Th(?P<markers>[<q!e*]*)$"
)
# Death spiral, e.g. "FiDs4", "BiDs3", "BoDsB", "FoDs3"
DEATH_SPIRAL_RE = re.compile(r"^(?P<base>(?:Fi|Bi|Fo|Bo)Ds)(?P<level>[1-4B])?(?P<markers>[*b]*)$")
# Pivot figure (Advanced Novice pairs), e.g. "PiF1"
PIVOT_RE = re.compile(r"^(?P<base>PiF)(?P<level>[1-4B])?(?P<markers>[*]*)$")

# --- Pairs and ice dance -------------------------------------------------------
# Lift, e.g. pairs "3Li4", "5RLi4", "5ALi3"; dance "RoLi4", "StaLi4", "CuLi3"
LIFT_RE = re.compile(r"^(?P<base>\d?[A-Za-z]*Li)(?P<level>[1-4B])?(?P<markers>[*]*)$")

# --- Ice dance -----------------------------------------------------------------
# One level per partner, e.g. "CiStW2+CiStM3", "SyTwWB+SyTwM4", "OFTW1+OFTM2"
PARTNER_RE = re.compile(
    r"^(?P<base>[A-Za-z]+?)W(?P<level>[1-4B])\+(?P=base)M(?P<level_partner>[1-4B])(?P<markers>[*]*)$"
)
# Pattern dance with key points, e.g. "1GW3+kpYNYY" (Y/N per key point, kept in markers)
PATTERN_RE = re.compile(r"^(?P<base>\d[A-Za-z]+?)(?P<level>[1-4B])\+kp(?P<markers>[A-Z]+)$")

FLAGS = {"COMBO", "REP", "SEQ", "RFE"}   # RFE: meaning not documented yet, kept as printed


def element(kind, base=None, level=None, markers="", level_partner=None,
            rotations=None, jump=None, flags=None, parts=None):
    """The dictionary returned by split_code, with every key always present."""
    return {
        "kind": kind, "flags": flags or [], "parts": parts or [],
        "base": base, "level": level, "level_partner": level_partner,
        "markers": markers, "rotations": rotations, "jump": jump,
    }


def partner_kind(base):
    """Kind of an ice dance element with one level per partner."""
    if "Tw" in base:
        return "twizzles"
    if base == "OFT":
        return "turns"
    return "step"


def split_code(code):
    """Split an element code into its parts.

    Returns a dictionary (see element()):
      kind:  "jump", "spin", "step", "choreo", "twist", "throw", "lift",
             "death_spiral", "pivot", "twizzles", "turns", "pattern", "empty" or "unknown"
      flags: e.g. ["COMBO"]
      parts: for jumps, one entry per jump in the element
      base / level / markers: for everything else
      level_partner: ice dance, the man's level when each partner has one
      rotations / jump: throws (rotations + jump type) and twists (rotations)
    """
    # Empty slot: no element performed
    if code == "":
        return element("empty", markers="")

    # Choreographic elements (checked first: "ChPSp1" must not count as a spin)
    match = CHOREO_RE.match(code)
    if match:
        return element("choreo", match["base"], match["level"], match["markers"])

    # Spins and step sequences: a single piece, no "+"
    match = OTHER_RE.match(code)
    if match:
        kind = "spin" if match["base"].endswith("Sp") else "step"
        return element(kind, match["base"], match["level"], match["markers"])

    for kind, pattern in [("twist", TWIST_RE), ("throw", THROW_RE)]:
        match = pattern.match(code)
        if match:
            rotations = int(match["rotations"]) if match["rotations"] else 0
            return element(kind, base="Tw" if kind == "twist" else "Th",
                           level=match.groupdict().get("level"), markers=match["markers"],
                           rotations=rotations, jump=match.groupdict().get("jump"))

    for kind, pattern in [("death_spiral", DEATH_SPIRAL_RE), ("pivot", PIVOT_RE)]:
        match = pattern.match(code)
        if match:
            return element(kind, match["base"], match["level"], match["markers"])

    match = PARTNER_RE.match(code)
    if match:
        return element(partner_kind(match["base"]), match["base"], match["level"],
                       match["markers"], level_partner=match["level_partner"])

    match = PATTERN_RE.match(code)
    if match:
        return element("pattern", match["base"], match["level"], match["markers"])

    # Lifts: a single lift, or a combined lift like "CuLi4+RoLi4" (levels joined with "+")
    lifts = [LIFT_RE.match(piece) for piece in code.split("+")]
    if all(lifts):
        return element("lift", "+".join(m["base"] for m in lifts),
                       "+".join(m["level"] or "" for m in lifts),
                       "".join(m["markers"] for m in lifts))

    # Jumps: split combinations on "+", separate the flags
    pieces = code.split("+")
    flags = [p for p in pieces if p in FLAGS]
    jumps = [p for p in pieces if p not in FLAGS]
    if not jumps:
        return {**element("unknown", flags=flags), "code": code}

    parts = []
    for position, piece in enumerate(jumps, start=1):
        match = JUMP_RE.match(piece)
        if not match:
            return {**element("unknown", flags=flags), "code": code}
        rotations = match.group("rotations")
        if rotations is None:
            if match.group("jump") == "Eu":
                rotations = 1   # Euler is printed without a number
            else:
                rotations = 0   # attempted jump: no value (TP Handbook 2026/27, p. 31)
        parts.append({
            "position": position,
            "rotations": int(rotations),
            "jump": match.group("jump"),
            "markers": match.group("markers"),
        })

    return element("jump", flags=flags, parts=parts)


if __name__ == "__main__":
    # Quick look at a few codes of each discipline
    tests = ["4T+3T", "3F+3T<", "4Lz+COMBO", "1Lz!*", "CCoSp4", "StSq4", "ChSq1",
             "3Tw3", "3FTh", "4STh", "3Li4", "5RLi4", "FiDs4", "PCoSp4V", "ChPLi1",
             "CiStW2+CiStM3", "SyTwWB+SyTwM4", "OFTW1+OFTM2", "1GWB+kpNNNN",
             "RoLi4", "CuLi4+RoLi4", "DSp4", "CDE4", "XYZ"]
    for code in tests:
        print(f"{code:<16} {split_code(code)}")
