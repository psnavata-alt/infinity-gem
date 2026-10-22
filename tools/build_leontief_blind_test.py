"""Build the Leontief blind-test workbook ("Test it yourself", test 1; 8 Oct 2026).

Purpose: settle "can Python compute a Leontief inverse, or was the AI's code rigged to reproduce PSA's numbers?" with a
test the doubter controls. The workbook holds PSA's 2018 80-industry input coefficients (A = transactions / output, from
PSA Table B.1, as Infinity GEM computes them). The tester changes ANY coefficients they like; Excel computes the Leontief
inverse (I - A)^-1 with its own built-in MINVERSE; the tester saves; then `COMPARE WITH PYTHON.bat` makes Python compute
the inverse from the tester's edited table and compares cell by cell. Python has never seen the edited numbers, so
agreement cannot come from memorised results.
Also in the workbook: PSA's own published inverse (Table B.3), so with nothing edited Excel can be compared with PSA.

Run:  py tools/build_leontief_blind_test.py [output_folder]     (default docs/verification/test_it_yourself)
Written 8 Oct 2026 with an AI coding assistant. The formulas in the workbook are the thing to audit, not this script.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter as L
from openpyxl.worksheet.formula import ArrayFormula

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from infinity_gem import paths                  # noqa: E402
from infinity_gem.iomodel import IOTable          # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs" / "verification" / "test_it_yourself" / "templates"
NAME = "Leontief_blind_test_PSA2018_80industries.xlsx"
R0, C0 = 4, 3                                  # first data row and column (C4)
BOLD, NOTE = Font(bold=True), Font(italic=True, color="555555")
EDIT = PatternFill("solid", fgColor="FFF2CC")


def grid(ws, n, names, title, note):
    ws["A1"] = title
    ws["A1"].font = Font(bold=True, size=12)
    ws["A2"] = note
    ws["A2"].font = NOTE
    ws.cell(R0 - 1, 1, "No.").font = BOLD
    ws.cell(R0 - 1, 2, "Industry (column = the industry that buys; row = the industry that sells)").font = BOLD
    for k in range(n):
        ws.cell(R0 - 1, C0 + k, k + 1).font = BOLD
        ws.cell(R0 + k, 1, k + 1).font = BOLD
        ws.cell(R0 + k, 2, names[k])
    ws.column_dimensions["B"].width = 42
    ws.freeze_panes = ws.cell(R0, C0)


def main():
    io = IOTable()
    n, names, A = io.n, io.names, io.A
    li = pd.read_excel(paths.IO_2018.parent / "80-Industry20Matrix202018.xlsx", header=None)
    r = next(i for i in range(len(li)) if str(li.iloc[i, 1]).strip() == "Palay")
    psa_inv = li.iloc[r:r + n, 2:2 + n].apply(pd.to_numeric, errors="coerce").values
    last = f"{L(C0 + n - 1)}{R0 + n - 1}"
    rng = f"{L(C0)}{R0}:{last}"

    wb = Workbook()
    rd = wb.active
    rd.title = "Read me"
    lines = [
        ("Test it yourself (1): the Leontief inverse, with numbers YOU choose", Font(bold=True, size=14)),
        ("PSA 2018 Input-Output Tables, 80 industries. Built 8 Oct 2026 for Infinity GEM's verification kit.", NOTE),
        ("", None),
        ("1. Go to sheet 'A (edit me)'. Change any yellow cells you like: one, ten, or a hundred. Write down what you changed if you wish.", None),
        ("   (Each cell is an input coefficient: pesos of the row industry's product used per peso of the column industry's output.", None),
        ("   Keep each column's total below 1, as in any real economy, or the inverse stops making economic sense.)", None),
        ("2. Excel recalculates by itself. Sheet 'Excel inverse' is Excel's own MINVERSE of (I - A): no Python, no AI.", None),
        ("3. Save the file (Ctrl+S) and close Excel.", None),
        ("4. Double-click 'COMPARE WITH PYTHON.bat' in the same folder. Python reads YOUR edited table, computes the inverse its own way,", None),
        ("   and compares all 6,400 cells with Excel's. A report opens in Notepad.", None),
        ("", None),
        ("Why this settles it: Python has never seen your numbers, so it cannot have been 'trained' or 'rigged' to give Excel's answers.", BOLD),
        ("If both agree to many decimal places, both are doing the same correct arithmetic.", None),
        ("", None),
        ("Untouched check: with nothing edited, 'Checks' compares Excel's inverse with PSA's own published inverse (Table B.3).", None),
        ("Sheet 'I minus A' shows the formula used for every cell: =IF(row=column,1,0) - A.", None),
    ]
    for t, f in lines:
        rd.append([t])
        if f:
            rd.cell(rd.max_row, 1).font = f
    rd.column_dimensions["A"].width = 150

    ck = wb.create_sheet("Checks")
    wa = wb.create_sheet("A (edit me)")
    grid(wa, n, names, "Input coefficients A (PSA 2018, Table B.1 transactions divided by total output): EDIT ANY YELLOW CELL",
         "Changing a cell here changes the economy. Excel's inverse (sheet 'Excel inverse') updates automatically.")
    wo = wb.create_sheet("A (PSA original)")
    grid(wo, n, names, "The same coefficients as delivered (do not edit): used only to count what you changed", "")
    wi = wb.create_sheet("I minus A")
    grid(wi, n, names, "I - A, computed by Excel from your edited table", "Formula in every cell: =IF(row = column, 1, 0) - A")
    we = wb.create_sheet("Excel inverse")
    grid(we, n, names, "Leontief inverse (I - A)^-1 computed by EXCEL's built-in MINVERSE function (one array formula)", "")
    wp = wb.create_sheet("PSA published inverse")
    grid(wp, n, names, "PSA's own published Leontief inverse, 2018 Table B.3 (80 industries), for the untouched check", "")
    for i in range(n):
        for j in range(n):
            c = wa.cell(R0 + i, C0 + j, float(A[i, j]))
            c.fill = EDIT
            wo.cell(R0 + i, C0 + j, float(A[i, j]))
            ref = f"{L(C0 + j)}{R0 + i}"
            wi.cell(R0 + i, C0 + j, f"={1 if i == j else 0}-'A (edit me)'!{ref}")
            wp.cell(R0 + i, C0 + j, float(psa_inv[i, j]))
    we[f"{L(C0)}{R0}"] = ArrayFormula(rng, f"=MINVERSE('I minus A'!{rng})")

    ck["A1"] = "Checks (Excel formulas only)"
    ck["A1"].font = Font(bold=True, size=13)
    rows = [
        ("Cells you changed in 'A (edit me)'", f"=SUMPRODUCT(--(ABS('A (edit me)'!{rng}-'A (PSA original)'!{rng})>0))"),
        ("Largest change you made to a coefficient", f"=MAX(ABS('A (edit me)'!{rng}-'A (PSA original)'!{rng}))"),
        ("Largest |Excel inverse - PSA published inverse| (about 0 only if you changed nothing)",
         f"=MAX(ABS('Excel inverse'!{rng}-'PSA published inverse'!{rng}))"),
        ("Largest column total of A (must stay below 1)", f"=MAX(INDEX(MMULT(TRANSPOSE(ROW('A (edit me)'!{rng})^0),'A (edit me)'!{rng}),0))"),
        ("Check: (I - A) x inverse = identity, largest error (should be about 0)",
         f"=MAX(ABS(MMULT('I minus A'!{rng},'Excel inverse'!{rng})-(ROW('I minus A'!{rng})-{R0 - 1}=COLUMN('I minus A'!{rng})-{C0 - 1})))"),
    ]
    for k, (t, f) in enumerate(rows, start=3):
        ck.cell(k, 1, t)
        if not f.startswith("=SUMPRODUCT"):
            ck[f"B{k}"] = ArrayFormula(f"B{k}", f)
        else:
            ck.cell(k, 2, f)
        ck.cell(k, 2).number_format = "0.000E+00" if k > 3 else "0"
    ck["A10"] = "Then save, close Excel and double-click 'COMPARE WITH PYTHON.bat'."
    ck["A10"].font = BOLD
    ck.column_dimensions["A"].width = 80
    ck.column_dimensions["B"].width = 18
    for c in ck["A"]:
        c.alignment = Alignment(wrap_text=True)
    wb.calculation.fullCalcOnLoad = True
    OUT.mkdir(parents=True, exist_ok=True)
    wb.save(OUT / NAME)
    print("wrote", OUT / NAME, f"({n} industries)")


if __name__ == "__main__":
    main()
