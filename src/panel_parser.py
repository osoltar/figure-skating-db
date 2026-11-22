import re
from bs4 import BeautifulSoup

JUDGE_RE = re.compile(r"^Judge No\.?\s*(\d+)$")   # "Judge No.1"
TITLE_RE = re.compile(r"^(Mr|Ms|Mrs|Dr)\.?\s+")    # "Ms. " at the start of a name


def parse_panel(path):
    """Read a 'Panel of Judges' HTML page into a list of dictionaries."""
    with open(path, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    panel = []
    for row in soup.find_all("tr"):
        cells = row.find_all("td", class_="CellLeft", recursive=False)
        if len(cells) != 2:
            continue
        function = cells[0].get_text(strip=True)
        full_name = cells[1].get_text(strip=True)
        nation = row.find_all("td")[-1].get_text(strip=True)

        match = JUDGE_RE.match(function)
        if match:
            role, judge_number = "Judge", int(match.group(1))
        else:
            role, judge_number = function, None

        name = TITLE_RE.sub("", full_name)          # remove "Mr. " / "Ms. "
        parts = name.split()
        panel.append({
            "role": role,
            "judge_number": judge_number,
            "first_name": " ".join(p for p in parts if not p.isupper()),
            "last_name": " ".join(p for p in parts if p.isupper()),
            "nation": nation,
        })
    return panel


if __name__ == "__main__":
    import sys
    for member in parse_panel(sys.argv[1]):
        print(member)