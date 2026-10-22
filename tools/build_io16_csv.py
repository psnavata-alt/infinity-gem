"""Copy PSA's 2018 16-industry input-output transactions table (Table A.1) from its Excel file to a CSV with the same
row and column layout as the 80-industry CSV, so infinity_gem.iomodel.IOTable can read either.

Source: PSA, 2018 Input-Output Accounts of the Philippines (as of December 2021), Table A.1 16-Industry Input-Output
Transaction Table, file data/raw/io/16-Industry20Table202018.xlsx (as downloaded from PSA). Values are copied
cell by cell; nothing is computed. Written 8 Oct 2026.
Run:  py tools/build_io16_csv.py
"""
import csv
import hashlib
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "io" / "16-Industry20Table202018.xlsx"
OUT = ROOT / "data" / "raw" / "io" / "16-Industry_Table_2018.csv"


def main():
    ws = openpyxl.load_workbook(SRC, data_only=True, read_only=True).worksheets[0]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    width = max(len(r) for r in rows)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for r in rows:
            w.writerow(["" if x is None else (repr(x) if isinstance(x, float) else str(x)) for x in r + [None] * (width - len(r))])
    sha = hashlib.sha256(SRC.read_bytes()).hexdigest()
    print(f"wrote {OUT.name}: {len(rows)} rows x {width} columns from {SRC.name} (SHA-256 {sha})")


if __name__ == "__main__":
    main()
