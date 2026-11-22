import re
import pdfplumber
from element_codes import split_code

PDF_PATH = "data/raw/26-27_GP_GrandPrixDeFrance_M_SP.pdf"

# --- Patterns ---------------------------------------------------------
# Skater line, e.g. "1 Adam SIAO HIM FA FRA 11 102.46 57.25 45.21 0.00"
# rank, name, nation, starting number, total, TES, PCS, deductions
SKATER_RE = re.compile(
    r"^(\d+)\s+(.+?)\s+([A-Z]{3})\s+(\d+)\s+"
    r"(\d+\.\d\d)\s+(\d+\.\d\d)\s+(\d+\.\d\d)\s+(-?\d+\.\d\d)$"
)
DECIMAL_RE = re.compile(r"^-?\d+\.\d+$")   # 8.80, -0.27
JUDGE_RE = re.compile(r"^(-?\d|-)$")       # one judge's GOE: -5..5, or "-" if missing
# Component line, e.g. "Composition 1.67 9.25 9.50 9.00 8.75 9.25 8.75 9.25 9.00 9.00 9.07"
COMPONENT_RE = re.compile(r"^(Composition|Presentation|Skating Skills)\s+(\d+\.\d\d)\s+(.+)$")


def read_lines(path):
    """Return every line of text in the PDF, all pages together."""
    lines = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            lines.extend(text.splitlines())
    return lines


def parse_skater(match):
    """Turn a SKATER_RE match into a dictionary."""
    rank, name, nation, start_no, total, tes, pcs, ded = match.groups()
    parts = name.split()
    return {
        "rank": int(rank),
        "name": name,
        "first_name": " ".join(p for p in parts if not p.isupper()),
        "last_name": " ".join(p for p in parts if p.isupper()),
        "nation": nation,
        "starting_number": int(start_no),
        "total": float(total),
        "tes": float(tes),
        "pcs": float(pcs),
        "deductions": float(ded),
        "elements": [],
        "components": [],
    }


def parse_element(line):
    """Parse an element line, e.g. "4 3A 8.80 x 2.51 3 3 3 4 3 3 2 3 4 11.31".
    Returns a dictionary, or None if the line is not an element line."""
    tokens = line.split()
    if len(tokens) < 6 or not tokens[0].isdigit():
        return None

    number, code = int(tokens[0]), tokens[1]
    i = 2

    # Info markers (<, q, e, !, *) sit between the code and the base value
    info = []
    while i < len(tokens) and not DECIMAL_RE.match(tokens[i]):
        info.append(tokens[i])
        i += 1
    if i + 2 >= len(tokens):
        return None

    base_value = float(tokens[i])
    i += 1

    second_half = False
    if tokens[i] == "x":
        second_half = True
        i += 1

    goe = float(tokens[i])
    i += 1

    # What's left: the judges' GOEs, then the panel score at the end
    rest = tokens[i:]
    if len(rest) < 2:
        return None
    judges, panel = rest[:-1], rest[-1]
    if not all(JUDGE_RE.match(j) for j in judges) or not DECIMAL_RE.match(panel):
        return None

    return {
        "number": number,
        "code": code,
        "info": [m for token in info for m in token.split(",") if m],
        "split": split_code(code),
        "base_value": base_value,
        "second_half": second_half,
        "goe": goe,
        "judges": [None if j == "-" else int(j) for j in judges],
        "panel_score": float(panel),
    }


def parse_component(line):
    """Parse a component line. Returns a dictionary, or None."""
    match = COMPONENT_RE.match(line)
    if not match:
        return None
    name, factor, rest = match.groups()
    marks = rest.split()
    return {
        "name": name,
        "factor": float(factor),
        "judges": [None if m == "-" else float(m) for m in marks[:-1]],
        "panel_score": float(marks[-1]),
    }


def parse(path):
    """Go through the PDF line by line and build a list of skaters."""
    skaters = []
    current = None
    for line in read_lines(path):
        match = SKATER_RE.match(line)
        if match:
            current = parse_skater(match)
            skaters.append(current)
            continue
        if current is None:
            continue
        element = parse_element(line)
        if element:
            current["elements"].append(element)
            continue
        component = parse_component(line)
        if component:
            current["components"].append(component)
    return skaters

def check_skater(s):
    """Return a list of problems found for one skater (empty list = all good)."""
    problems = []

    if not s["elements"]:
        problems.append("no elements found")
    if len(s["components"]) != 3:
        problems.append(f"{len(s['components'])} components found instead of 3")

    tes = round(sum(e["panel_score"] for e in s["elements"]), 2)
    if abs(tes - s["tes"]) >= 0.01:
        problems.append(f"TES is {s['tes']} but elements add up to {tes}")

    pcs = round(sum(c["panel_score"] * c["factor"] for c in s["components"]), 2)
    if abs(pcs - s["pcs"]) >= 0.02:
        problems.append(f"PCS is {s['pcs']} but components give {pcs}")

    total = round(s["tes"] + s["pcs"] - abs(s["deductions"]), 2)
    if abs(total - s["total"]) >= 0.01:
        problems.append(f"total is {s['total']} but TES + PCS - deductions = {total}")

    for e in s["elements"]:
        if e["split"]["kind"] == "unknown":
            problems.append(f"unrecognised element code {e['code']}")

    return problems

if __name__ == "__main__":
    skaters = parse(PDF_PATH)
    print(len(skaters), "skaters found\n")
    for s in skaters:
        problems = check_skater(s)
        status = "OK" if not problems else "; ".join(problems)
        print(f'{s["rank"]:>2} {s["name"]:<28} {s["nation"]} {status}')