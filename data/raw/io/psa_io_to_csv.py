"""Copy PSA's 2018 input-output transactions tables (Excel, as published by PSA) to the CSV layout Infinity GEM reads.

PSA's tables are included in this folder (README.md), together with the CSV copies the package reads. This script makes
the CSV copies again from the Excel files, so anyone can check that they hold PSA's values and nothing else. It writes to
outputs/psa_io_csv/ (the included copies are never overwritten: check D1 records their exact bytes). Run from the
repository root:

    python data/raw/io/psa_io_to_csv.py              # then compare the values with data/raw/io/*.csv

Values are copied cell by cell; nothing is computed. Files read (names as PSA publishes them):
    80-Industry20Table202018.xlsx   Table B.1, 80-industry transactions table   -> 80-Industry20Table202018.csv
    16-Industry20Table202018.xlsx   Table A.1, 16-industry transactions table   -> 16-Industry_Table_2018.csv
"""
import csv
import hashlib
import sys
from pathlib import Path

import openpyxl

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[2] / "outputs" / "psa_io_csv"
TABLES = {"80-Industry20Table202018.xlsx": "80-Industry20Table202018.csv",
          "16-Industry20Table202018.xlsx": "16-Industry_Table_2018.csv"}


def convert(src: Path, out: Path):
    ws = openpyxl.load_workbook(src, data_only=True, read_only=True).worksheets[0]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    width = max(len(r) for r in rows)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for r in rows:
            w.writerow(["" if x is None else (repr(x) if isinstance(x, float) else str(x)) for x in r + [None] * (width - len(r))])
    print(f"wrote {out}: {len(rows)} rows x {width} columns from {src.name} (SHA-256 {hashlib.sha256(src.read_bytes()).hexdigest()})")


if __name__ == "__main__":
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE
    OUT.mkdir(parents=True, exist_ok=True)
    found = False
    for src, out in TABLES.items():
        if (folder / src).exists():
            convert(folder / src, OUT / out)
            found = True
    if not found:
        sys.exit(f"No PSA table found in {folder} (README.md).")
