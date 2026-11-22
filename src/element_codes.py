import re

# A single jump, e.g. "4T", "3Lz!", "3A<", "4Tq", "1Lz!*", "2A<<"
JUMP_RE = re.compile(
    r"^(?P<rotations>\d)?(?P<jump>Lz|Lo|Eu|A|F|S|T)(?P<markers>[<q!e*]*)$"
)
# Spins and sequences, e.g. "CCoSp4", "FCSpB", "CSSp3V", "StSq4", "ChSq1"
OTHER_RE = re.compile(
    r"^(?P<base>[A-Za-z]*?(?:Sp|Sq))(?P<level>B|\d)?(?P<markers>[V*]*)$"
)
FLAGS = {"COMBO", "REP", "SEQ"}


def split_code(code):
    """Split an element code into its parts.

    Returns a dictionary:
      kind:  "jump", "spin", "step", "choreo" or "unknown"
      flags: e.g. ["COMBO"]
      parts: for jumps, one entry per jump in the element
      base / level / markers: for spins and sequences
    """
    # Spins and sequences: a single piece, no "+"
    other = OTHER_RE.match(code)
    if other:
        base = other.group("base")
        if base.endswith("Sp"):
            kind = "spin"
        elif base == "StSq":
            kind = "step"
        else:
            kind = "choreo"
        return {
            "kind": kind,
            "flags": [],
            "parts": [],
            "base": base,
            "level": other.group("level"),
            "markers": other.group("markers"),
        }

    # Jumps: split combinations on "+", separate the flags
    pieces = code.split("+")
    flags = [p for p in pieces if p in FLAGS]
    jumps = [p for p in pieces if p not in FLAGS]

    parts = []
    for position, piece in enumerate(jumps, start=1):
        match = JUMP_RE.match(piece)
        if not match:
            return {"kind": "unknown", "flags": flags, "parts": [], "code": code}
        rotations = match.group("rotations")
        if rotations is None:
            if match.group("jump") != "Eu":
                return {"kind": "unknown", "flags": flags, "parts": [], "code": code}
            rotations = 1   # Euler is printed without a number
        parts.append({
            "position": position,
            "rotations": int(rotations),
            "jump": match.group("jump"),
            "markers": match.group("markers"),
        })

    return {"kind": "jump", "flags": flags, "parts": parts}


if __name__ == "__main__":
    # Quick test on codes from the Grand Prix de France PDF
    tests = ["4T+3T", "4S<", "3F+3T<", "4Lz+COMBO", "4Tq", "1Lz!*",
             "3Lz!+2T", "2Lz*", "CCoSp4", "FCSpB", "StSq4", "ChSq1", "XYZ",
             "3Lz!<+Eu+2S", "2A+Eu+3F+2A+SEQ", "T"]
    for code in tests:
        print(f"{code:<12} {split_code(code)}")