"""The central 2026 case with the wage curve set to the HOURS-inclusive Okun elasticity (0.3.9, 18 Oct 2026).

Why: the wage curve's target, e = 0.713 (preshock/okun.py, employed persons per person aged 15+), rests on the 2020-2021
quarters. The model's labour input is persons x hours; preshock/okun_hours.py estimates the hours-inclusive elasticity
(employment-to-population x mean weekly hours) at 0.600 (s.e. 0.297) without 2020-2021, and 0.233 (not significant) in
2006-2019. This script calibrates beta to those targets exactly as scenarios/calibrate_wage_curve.py does (2026 labour input
= e x the model's own 2026 growth effect, public capital low) and reruns the combined 2025-27 shocks with poverty.
It writes its own output and does NOT write a wage_curve_calibration_*.csv (combined_revised.py reads the latest of those).
MicroLink uses the current default (fuel_split_map=True, 18 Oct), so the central row reads 3.16 M, not the 17 Oct 2026 scenarios' 3.14 M.
NOT FOR CITATION. Run:  py scenarios/okun_hours_sensitivity.py
"""
import datetime as dt
import sys

from _common import ROOT
import pandas as pd

sys.path.insert(0, str(ROOT / "preshock"))
from infinity_gem import paths                                                     # noqa: E402
import combined_revised as CR                                                   # noqa: E402
import calibrate_wage_curve as CW                                               # noqa: E402
import okun_hours                                                               # noqa: E402

KEYS = ["GDP gap 2026 (%)", "GDP gap 2027 (%)", "consumer prices 2026 (%)", "employment gap 2026 (pp of labour supply)",
        "new poor 2026 (M, own baskets)", "new poor 2027 (M, own baskets)"]


def main():
    est = okun_hours.estimates().set_index(["margin", "sample"])
    hrs = "total hours per person 15+"
    targets = {"hours, 2006-2026 without 2020-2021": float(est.loc[(hrs, "2006-2026 without 2020-2021"), "b"]),
               "hours, 2006-2019 (not significant)": float(est.loc[(hrs, "2006-2019"), "b"])}
    cal = pd.read_csv(paths.output_dir() / "wage_curve_calibration_20261017.csv", index_col=0)
    betas = {"central (persons, all quarters, e 0.713; 17 Oct 2026)": float(cal.loc["central (e)", "beta"])}
    R = CR.Runs("low")
    piece, _ = R.pieces()
    for name, ee in targets.items():
        bt = CW.calibrate(lambda s, ee=ee: s[0] - ee * s[3], R, piece)
        betas[f"{name}, e {ee:.3f}"] = bt
        print(name, "e", round(ee, 3), "beta", round(bt, 3), flush=True)
    rows = {}
    for name, b in betas.items():
        Rw = CR.Runs("low", wage_curve=b)
        pw, sw = Rw.pieces()
        works = {2025: sw["public works"]["2025"], 2026: sw["public works"]["2026 central"],
                 2027: sw["public works"]["2027 NEP x 2025 rate (central)"]}
        m = Rw.measures(Rw.run(set(), piece=pw), Rw.run(set(CR.SHOCKS), piece=pw), works=works, poor=True)[0]
        rows[name] = {"beta": b, "implied pay elasticity": -b * 0.039 / (1 - 0.039), **{k: m.get(k) for k in KEYS}}
        print(name, {k: round(v, 3) for k, v in rows[name].items() if isinstance(v, float)}, flush=True)
    t = pd.DataFrame(rows).T
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    out = paths.output_dir() / f"okun_hours_sensitivity_{stamp}.md"
    L = [f"# The central 2026 case with an hours-inclusive Okun target ({dt.date.today():%d %B %Y})", "",
         "**NOT FOR CITATION** (Infinity GEM 0.3.9). Script: `scenarios/okun_hours_sensitivity.py`; elasticities from "
         "`preshock/okun_hours.py`. Combined 2025-27 shocks, public capital low; beta calibrated as in "
         "`scenarios/calibrate_wage_curve.py` (2026 labour input = e x the model's own 2026 growth effect). MicroLink with the "
         "default fuel_split_map=True (the scenarios of 17 Oct 2026 used False: 3.14 M). 'Implied pay elasticity' as in the calibration report.", "",
         t.to_markdown(floatfmt=".3f")]
    out.write_text("\n".join(L), encoding="utf-8")
    t.to_csv(out.with_suffix(".csv"))
    print("saved", out)


if __name__ == "__main__":
    main()
