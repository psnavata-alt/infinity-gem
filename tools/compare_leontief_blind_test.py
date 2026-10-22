"""Compare Excel's MINVERSE with Python on the tester's edited table ("Test it yourself", test 1; 8 Oct 2026).

Reads the saved workbook docs/verification/test_it_yourself/Leontief_blind_test_PSA2018_80industries.xlsx:
  - 'A (edit me)': the coefficients as the tester left them;
  - 'Excel inverse': the inverse Excel computed with MINVERSE (the values Excel saved).
Python then computes inv(I - A) from the tester's numbers with NumPy (LAPACK, the standard library used by scientists
worldwide) and compares all cells. Writes test_it_yourself/RESULT_leontief_<date_time>.txt and prints it.
Run:  py tools/compare_leontief_blind_test.py [workbook]
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import openpyxl

ROOT = Path(__file__).resolve().parents[1]
WB = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs" / "verification" / "test_it_yourself" / "templates" / "Leontief_blind_test_PSA2018_80industries.xlsx"
R0, C0, N = 4, 3, 80


def block(ws):
    rows = ws.iter_rows(min_row=R0, max_row=R0 + N - 1, min_col=C0, max_col=C0 + N - 1, values_only=True)
    return np.array([[np.nan if v is None or isinstance(v, str) else float(v) for v in r] for r in rows])


def main():
    wb = openpyxl.load_workbook(WB, data_only=True, read_only=True)
    A, A0 = block(wb["A (edit me)"]), block(wb["A (PSA original)"])
    X = block(wb["Excel inverse"])
    names = [r[0] for r in wb["A (edit me)"].iter_rows(min_row=R0, max_row=R0 + N - 1, min_col=2, max_col=2, values_only=True)]
    lines = [f"Leontief blind test: Excel MINVERSE versus Python, {dt.datetime.now():%d %b %Y %H:%M}", f"Workbook: {WB.name}", ""]
    if np.isnan(X).all():
        lines += ["Excel's inverse has no saved values yet.",
                  "Open the workbook in Excel, let it calculate, make your changes, SAVE (Ctrl+S), close Excel, and run this again."]
    else:
        changed = np.argwhere(np.abs(A - A0) > 0)
        lines.append(f"You changed {len(changed)} of {N * N} coefficients.")
        for i, j in changed[:15]:
            lines.append(f"  row {i + 1} ({names[i][:30]}), column {j + 1}: {A0[i, j]:.6f} -> {A[i, j]:.6f}")
        if len(changed) > 15:
            lines.append(f"  ... and {len(changed) - 15} more")
        P = np.linalg.inv(np.eye(N) - A)                          # Python, from YOUR numbers
        d = np.abs(P - X)
        rel = d / np.maximum(np.abs(X), 1e-12)
        i, j = np.unravel_index(np.argmax(d), d.shape)
        ident = np.abs((np.eye(N) - A) @ P - np.eye(N)).max()
        lines += ["", f"Python computed the inverse from your edited table: (I - A) x inverse = identity to within {ident:.1e}.",
                  f"Largest difference between Python and Excel, over all {N * N} cells: {d.max():.2e}",
                  f"  (at row {i + 1}, column {j + 1}: Excel {X[i, j]:.12f}, Python {P[i, j]:.12f}); largest relative difference {rel.max():.2e}",
                  "",
                  ("RESULT: AGREE. Excel and Python give the same Leontief inverse for your numbers (differences are at the level of "
                   "computer rounding, about 15 significant digits)." if d.max() < 1e-8 else
                   "RESULT: DIFFERENT. Please report it (an issue on the repository), with this file and the workbook.")]
        if not len(changed):
            lines.append("Note: you changed nothing, so this run only repeats the untouched check. Edit some cells for a blind test.")
    out = WB.parent / f"RESULT_leontief_{dt.datetime.now():%Y%m%d_%H%M%S}.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print("\nSaved:", out)


if __name__ == "__main__":
    main()
