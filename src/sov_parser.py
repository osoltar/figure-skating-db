"""Read an ISU Scale of Values PDF: every element code with its base value and GOE values.

Each value line looks like
    3Lz -2,95 -2,36 -1,77 -1,18 -0,59 5,90 0,59 1,18 1,77 2,36 2,95
i.e. the code, then 11 numbers with decimal commas: GOE -5 to -1, base value, GOE +1 to +5.
Ice dance lines can start with a label: "1st Sequence FO1SqB -1,88 ...".
"""
import re

import pdfplumber

NUMBER_RE = re.compile(r"^-?\d+,\d\d$")                 # "-2,95", "5,90"
CODE_RE = re.compile(r"^(?=.*[A-Za-z])[A-Za-z0-9<!*]+$")  # "3Lz", "2F!<", "CCoSp4V", "1GW3"
GOE_STEPS = ["m5", "m4", "m3", "m2", "m1", "p1", "p2", "p3", "p4", "p5"]


def to_number(text):
    """'-2,95' -> -2.95"""
    return float(text.replace(",", "."))


def parse_sov_line(line):
    """One row of the Scale of Values, or None if the line isn't a value line."""
    tokens = line.split()
    positions = [i for i, t in enumerate(tokens) if NUMBER_RE.match(t)]
    if len(positions) != 11:
        return None
    first = positions[0]
    # the 11 numbers must follow each other, right after the code
    if first == 0 or positions != list(range(first, first + 11)):
        return None
    code = tokens[first - 1]
    if not CODE_RE.match(code):
        return None
    values = [to_number(tokens[i]) for i in positions]
    row = {"code": code, "base_value": values[5]}
    row.update({f"goe_{step}": value for step, value in zip(GOE_STEPS, values[:5] + values[6:])})
    return row


def parse_sov(path):
    """All rows of a Scale of Values PDF. If a code appears twice (e.g. pattern dances
    with and without key points), the first occurrence is kept."""
    rows, seen = [], set()
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for line in (page.extract_text() or "").splitlines():
                row = parse_sov_line(line)
                if row and row["code"] not in seen:
                    seen.add(row["code"])
                    rows.append(row)
    return rows


if __name__ == "__main__":
    import sys
    result = parse_sov(sys.argv[1])
    print(len(result), "codes")
    for row in result[:5]:
        print(row)
