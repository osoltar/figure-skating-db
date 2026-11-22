import re
import pdfplumber

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
        "info": " ".join(info),
        "base_value": base_value,
        "second_half": second_half,
        "goe": goe,
        "judges": [None if j == "-" else int(j) for j in judges],
        "panel_score": float(panel),
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
    return skaters


if __name__ == "__main__":
    skaters = parse(PDF_PATH)
    print(len(skaters), "skaters found\n")
    for s in skaters:
        total = round(sum(e["panel_score"] for e in s["elements"]), 2)
        status = "OK" if abs(total - s["tes"]) < 0.01 else "MISMATCH"
        print(f'{s["rank"]:>2} {s["name"]:<28} {s["nation"]} '
              f'elements={len(s["elements"])} TES={s["tes"]} sum={total} {status}')