"""The peso's non-oil fall (inflation VAR, decision 2) entered in the combined revised run: a SENSITIVITY, not the central run.

NOT FOR CITATION. Run:  py scenarios/peso_sensitivity.py   (a few minutes; public capital 'low', central wage curve)

The inflation VAR (preshock/inflation_var.py) measures the peso against its pre-shock forecast: in 2026 it was about 2.0-2.5%
weaker, of which about 0.6% is not explained by oil and energy (90% band about -1.5 to +2.9: not different from zero) and
0.9% in 2027 (carry-over only). The CGE holds the peso at its baseline in the short-run years; dynamic.py's opt-in
'exr_scale' (check EX1) moves it. This script adds the VAR's non-oil peso gap, and as an upper case the whole 2026-27 gap
(oil and energy included), to the all-shocks path and reports the change in growth, prices and poverty.

Read with care: in the CGE, a weaker peso with sticky peso wages is expansionary (exports up, imports down, more hiring)
and passes fully into prices; in the VAR, the peso's own shocks barely move Philippine prices. The 2026 peso fall came
with geopolitical risk and capital outflows, which the CGE does not have.
"""
import sys

import pandas as pd

from _common import Report, ROOT
from combined_revised import Runs, SHOCKS

sys.path.insert(0, str(ROOT))
from infinity_gem import paths  # noqa: E402


def main():
    var = sorted(paths.output_dir().glob("inflation_var_*_headline_bands.csv"))[-1]
    b = pd.read_csv(var).set_index(["period", "statistic"])["estimate"]
    cal = pd.read_csv(__import__("_common").calibration_file(), index_col=0)
    beta = float(cal.loc["central (e)", "beta"])
    cases = {"VAR: non-oil peso gap": {2026: b[("2026", "peso: not oil (%)")], 2027: b[("2027", "peso: not oil (%)")]},
             "VAR: whole peso gap (oil and energy included)": {2026: b[("2026", "peso gap (%)")], 2027: b[("2027", "peso gap (%)")]}}
    R = Runs("low", wage_curve=beta)
    piece, src = R.pieces()
    pw = src["public works"]
    works = {2025: pw["2025"], 2026: pw["2026 central"], 2027: pw["2027 NEP x 2025 rate (central)"]}   # 17 Oct: third revision's 2027
    clean = R.run(set(), piece=piece)
    base, _ = R.measures(clean, R.run(set(SHOCKS), piece=piece), works=works)
    rows = {"all shocks (central run)": base}
    for name, gap in cases.items():
        p = {k: dict(v) for k, v in piece.items()}
        p["peso"] = {t: {"exr_scale": 1 + g / 100} for t, g in gap.items()}
        rows[f"all shocks + {name} ({gap[2026]:+.2f}% 2026, {gap[2027]:+.2f}% 2027)"] = \
            R.measures(clean, R.run(set(SHOCKS) | {"peso"}, piece=p), works=works)[0]
    t = pd.DataFrame(rows)
    keep = ["GDP gap 2026 (%)", "GDP gap 2027 (%)", "cumulative GDP loss 2025-2030 (% of 2025 GDP)", "consumer prices 2026 (%)",
            "inflation effect 2026 (pp)", "employment gap 2026 (pp of labour supply)", "new poor 2026 (M, own baskets)",
            "new poor 2027 (M, own baskets)"]
    rep = Report("The peso's non-oil fall in the CGE: sensitivity (Infinity GEM 0.3.7)", "peso_sensitivity")
    rep.p(f"**NOT FOR CITATION.** Peso gaps from `{var.name}` (inflation VAR); public capital low; wage curve beta {beta:.2f}. "
          "The central combined run holds the peso at its baseline. See the script's notes for how to read this.")
    rep.table(t.loc[keep], floatfmt=".3f")
    rep.save()
    print(t.loc[keep].round(3).to_string())


if __name__ == "__main__":
    main()
