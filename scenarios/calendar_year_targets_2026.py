"""The short-run calibration's 2026 targets (0.3.13, 24 Oct 2026): the 2026 growth and investment targets on a calendar-year basis, against the
model's calendar-year results; the gap only. RESEARCH, NOT FOR CITATION; nothing else reads this.

Data: PSA OpenSTAT 0012B5BEXQ1 (data/raw/macro/PSA_OpenSTAT_GDP_by_expenditure_quarterly_2000-2026.csv), constant 2018 prices, to
Q2 2026. The calibration's targets (as a development script computed them) are H1 2026 y/y less the pre-shock trend (mean of H1 2024
and H1 2025 y/y). The model's growth effect is calendar-year: (1 + gap 2026) / (1 + gap 2025) - 1, and its 2025 gap carries the
public-works cut that in the data fell in H2 2025. Restated here on the model's basis:
  gap H1 2025 = 0 (H1 2025 on trend, as the H1 target assumes);
  gap H2 2025 = H2 2025 y/y less its pre-shock trend (mean of H2 2023 and H2 2024 y/y), H2 2024 on trend;
  gap H1 2026 = (1 + H1 2026 y/y) / (1 + H1 trend) - 1 (= the H1 target, to second order);
  gap H2 2026 = gap H1 2026 (ASSUMPTION: no H2 2026 data yet; variant: the H2 2025 gap persists);
  calendar gap Y = half-year gaps weighted by the trend levels of the halves (H1, H2 shares of 2025);
  calendar growth effect 2026 = (1 + gap 2026) / (1 + gap 2025) - 1.
Model: the columns given (CSV outputs of the development copy's short-run calibration scripts, one column each, rows
'GDP 2025 (%)', 'GDP 2026 (%)', 'growth effect 2026 (pp)', 'I 2026 (%)', 'I growth effect 2026 (pp)', 'C ...').
Run:  py -I -X utf8 scenarios/calendar_year_targets_2026.py [model csv ...]
Output: outputs/calendar_year_targets_2026_<YYYYMMDD_HHMM>.csv and _model_gaps.csv.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from infinity_gem import paths                                                      # noqa: E402

EXP = paths.DATA_RAW / "macro" / "PSA_OpenSTAT_GDP_by_expenditure_quarterly_2000-2026.csv"
ITEMS = {"Gross Domestic Product": "GDP", "Household final consumption expenditure": "C",
         "Gross capital formation": "I", "Gross fixed capital formation": "GFCF", "Construction": "construction",
         "Exports of goods and services": "X"}


def data_table() -> pd.DataFrame:
    d = pd.read_csv(EXP, comment="#")
    d = d[d["valuation"] == "At Constant 2018 Prices"]
    d["half"] = np.where(d["quarter"].isin(["Q1", "Q2"]), "H1", "H2")
    h = d.groupby(["expenditure", "year", "half"])["value_million_php"].sum()
    rows = {}
    for k, nm in ITEMS.items():
        g = lambda y, hf: float(h[(k, y, hf)] / h[(k, y - 1, hf)] - 1)
        tr1 = (g(2024, "H1") + g(2025, "H1")) / 2
        tr2 = (g(2023, "H2") + g(2024, "H2")) / 2
        gap_h2_25 = (1 + g(2025, "H2")) / (1 + tr2) - 1
        gap_h1_26 = (1 + g(2026, "H1")) / (1 + tr1) - 1
        w1 = float(h[(k, 2025, "H1")] / (h[(k, 2025, "H1")] + h[(k, 2025, "H2")]))
        gap25 = w1 * 0.0 + (1 - w1) * gap_h2_25
        gap26 = gap_h1_26                                            # H2 2026 = H1 2026 (assumption)
        gap26_b = w1 * gap_h1_26 + (1 - w1) * gap_h2_25              # variant: H2 2026 gap = H2 2025's
        rows[nm] = {"H1 2026 y/y (%)": g(2026, "H1") * 100, "H1 trend (%)": tr1 * 100,
                    "H1 target: H1 2026 less trend (pp)": (g(2026, "H1") - tr1) * 100,
                    "H2 2025 y/y (%)": g(2025, "H2") * 100, "H2 trend (%)": tr2 * 100, "gap H2 2025 (%)": gap_h2_25 * 100,
                    "gap H1 2026 (%)": gap_h1_26 * 100, "H1 share of 2025": w1,
                    "calendar gap 2025 (%)": gap25 * 100, "calendar gap 2026 (%; H2 2026 = H1 2026)": gap26 * 100,
                    "calendar growth effect 2026 (pp; H2 2026 = H1 2026)": ((1 + gap26) / (1 + gap25) - 1) * 100,
                    "calendar growth effect 2026 (pp; variant H2 2026 = H2 2025 gap)": ((1 + gap26_b) / (1 + gap25) - 1) * 100}
    return pd.DataFrame(rows)


def main(files):
    stamp = pd.Timestamp.today()
    t = data_table()
    head = "# NOT FOR CITATION (research; Infinity GEM 0.3.13). scenarios/calendar_year_targets_2026.py; PSA 0012B5BEXQ1 constant 2018 prices"
    out = paths.output_dir() / f"calendar_year_targets_2026_{stamp:%Y%m%d_%H%M}"
    Path(str(out) + ".csv").write_text(head + "\n" + t.to_csv(), encoding="utf-8")
    print(t.round(3).to_string())
    if not files:
        return
    rows = {}
    for f in files:
        s = pd.read_csv(f, index_col=0, comment="#").iloc[:, 0]
        num = lambda k: float(pd.to_numeric(s.get(k), errors="coerce"))
        r = {}
        for nm, gk, k in (("GDP", "growth effect 2026 (pp)", "GDP"), ("I", "I growth effect 2026 (pp)", "I"),
                          ("C", "C growth effect 2026 (pp)", "C")):
            lvl26 = num("GDP 2026 (%)") if nm == "GDP" else num(f"{k} 2026 (%)")
            r[f"{nm}: model calendar growth effect 2026 (pp)"] = num(gk)
            r[f"{nm}: data, calendar basis (pp)"] = float(t.loc["calendar growth effect 2026 (pp; H2 2026 = H1 2026)", nm])
            r[f"{nm}: GAP model less data, calendar basis (pp)"] = num(gk) - r[f"{nm}: data, calendar basis (pp)"]
            r[f"{nm}: data, H1 target (pp)"] = float(t.loc["H1 target: H1 2026 less trend (pp)", nm])
            r[f"{nm}: GAP model calendar less H1 target (pp; the basis mismatch included)"] = num(gk) - r[f"{nm}: data, H1 target (pp)"]
            r[f"{nm}: model 2026 level gap (%; = H1 basis if H1 2025 is unshocked)"] = lvl26
            r[f"{nm}: GAP model 2026 level gap less H1 target (pp)"] = lvl26 - r[f"{nm}: data, H1 target (pp)"]
        rows[Path(f).name] = r
    m = pd.DataFrame(rows)
    Path(str(out) + "_model_gaps.csv").write_text(head + "\n" + m.to_csv(), encoding="utf-8")
    print(m.round(3).to_string())
    print("saved", out)


if __name__ == "__main__":
    main(sys.argv[1:])
