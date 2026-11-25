import re
import pdfplumber
from element_codes import split_code

PDF_PATH = "data/raw/26-27_GP_GrandPrixDeFrance_M_SP.pdf"

# --- Patterns ---------------------------------------------------------
# Skater line, e.g. "1 Adam SIAO HIM FA FRA 11 102.46 57.25 45.21 0.00"
# rank, name, nation, starting number, total, TES, PCS, deductions
SKATER_RE = re.compile(
    r"^(\d+)\s+(.+?)\s+([A-Z]{3}\d?)\s+(\d+)\s+"
    r"(\d+\.\d\d)\s+(\d+\.\d\d)\s+(\d+\.\d\d)\s+(-?\d+\.\d\d)$"
)
DECIMAL_RE = re.compile(r"^-?\d+\.\d+$")   # 8.80, -0.27
JUDGE_RE = re.compile(r"^(-?\d|-)$")       # one judge's GOE: -5..5, or "-" if missing
# Component line, e.g. "Composition 1.67 9.25 9.50 9.00 8.75 9.25 8.75 9.25 9.00 9.00 9.07"
COMPONENT_RE = re.compile(r"^(Composition|Presentation|Skating Skills)\s+(\d+\.\d\d)\s+(.+)$")
# One deduction in the deduction line: "Falls -2.00 (2)", "Time violation -1.00",
# "Illegal element/movement -2.00" (type, points, and a count for falls)
DEDUCTION_RE = re.compile(r"([A-Za-z][A-Za-z/ ]*?)\s+(-?\d+\.\d\d)(?:\s+\((\d+)\))?")


def read_lines(path):
    """Return every line of text in the PDF, all pages together."""
    lines = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            lines.extend(text.splitlines())
    return lines


def split_name(name):
    """'Anastasiia METELKINA' -> ('Anastasiia', 'METELKINA'): last name is in capitals."""
    parts = name.split()
    return (" ".join(p for p in parts if not p.isupper()),
            " ".join(p for p in parts if p.isupper()))


def parse_skater(match):
    """Turn a SKATER_RE match into a dictionary.

    Pairs and ice dance teams are printed as 'Firstname LASTNAME / Firstname LASTNAME':
    the first person goes in first_name/last_name, the second in partner_first_name/
    partner_last_name (None for singles)."""
    rank, name, nation, start_no, total, tes, pcs, ded = match.groups()
    people = [person.strip() for person in name.split(" / ")]
    first_name, last_name = split_name(people[0])
    partner_first, partner_last = split_name(people[1]) if len(people) > 1 else (None, None)
    return {
        "rank": int(rank),
        "name": name,
        "first_name": first_name,
        "last_name": last_name,
        "partner_first_name": partner_first,
        "partner_last_name": partner_last,
        "nation": nation,
        "starting_number": int(start_no),
        "total": float(total),
        "tes": float(tes),
        "pcs": float(pcs),
        "deductions": float(ded),
        "elements": [],
        "components": [],
        "deduction_items": [],      # from the "Deductions:" line
        "deduction_total": None,
    }


def parse_element(line):
    """Parse an element line, e.g. "4 3A 8.80 x 2.51 3 3 3 4 3 3 2 3 4 11.31".
    Returns a dictionary, or None if the line is not an element line."""
    tokens = line.split()
    if len(tokens) < 6 or not tokens[0].isdigit():
        return None

    number = int(tokens[0])
    if DECIMAL_RE.match(tokens[1]):
        code = ""        # empty slot: no element code, e.g. "12 0.00 0.00 - - ... 0.00"
        i = 1
    else:
        code = tokens[1]
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

    goe = None if tokens[i] == "-" else float(tokens[i])   # "-" = no GOE (not validated)
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


def parse_deductions(line):
    """Parse a deduction line, e.g.
        "Deductions: Time violation -1.00 Falls -2.00 (2) -3.00"
    into ([{"type": "Time violation", "points": -1.0, "count": None},
           {"type": "Falls", "points": -2.0, "count": 2}], -3.0).
    Returns None if the line is not a deduction line."""
    if not line.startswith("Deductions:"):
        return None
    rest = line[len("Deductions:"):].strip()
    *details, total = rest.rsplit(" ", 1) if " " in rest else ["", rest]
    items = [{"type": kind.strip(), "points": float(points), "count": int(count) if count else None}
             for kind, points, count in DEDUCTION_RE.findall(details[0] if details else "")]
    return items, float(total)


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
        try:
            element = parse_element(line)
        except ValueError as err:
            raise ValueError(f"{path}: could not parse line {line!r}") from err
        if element:
            current["elements"].append(element)
            continue
        component = parse_component(line)
        if component:
            current["components"].append(component)
            continue
        deductions = parse_deductions(line)
        if deductions:
            current["deduction_items"], current["deduction_total"] = deductions
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

    # The deduction line: its items add up to its total, which matches the header
    if s.get("deduction_total") is None:
        if abs(s["deductions"]) > 0.001:
            problems.append(f"deductions are {s['deductions']} but no deduction line found")
    else:
        items_sum = round(sum(item["points"] for item in s["deduction_items"]), 2)
        if abs(items_sum - s["deduction_total"]) > 0.001:
            problems.append(f"deduction line items add up to {items_sum}, "
                            f"line total is {s['deduction_total']}")
        if abs(abs(s["deduction_total"]) - abs(s["deductions"])) > 0.001:
            problems.append(f"deduction line total is {s['deduction_total']}, "
                            f"header says {s['deductions']}")

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