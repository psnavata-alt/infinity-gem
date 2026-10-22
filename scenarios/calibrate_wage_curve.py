"""Calibrate the short-run wage curve to PSA's output-employment relation (0.3.7, 16 Oct 2026; target changed 17 Oct 2026).

Target (17 Oct 2026, code review finding C1): in the
combined 2025-2027 shocks run (scenarios/combined_revised.py, public capital low), the 2026 change in labour input (all skill
levels, weighted by the baseline wage bill) equals e x the model's OWN effect on 2026 growth, with e the elasticity of
employment to output estimated from PSA data (preshock/okun.py). This is a fixed point, because the model's growth effect
itself moves with beta: solved by bisection on beta.
  Why not the observed shortfall: the 16 Oct version targeted e x (PSA H1 2026 growth 2.6% - pre-shock 5.5%), the job loss of
  the WHOLE growth shortfall, although the 2026 scenarios themselves say the four shocks explain only part of it (the rest: confidence,
  private investment, the peso, tighter money). That made the four shocks carry 1.7 times the job loss Okun's law attaches to
  their own output effect. That calibration is kept as the UPPER BOUND ("observed shortfall" row).
  The Okun coefficient: okun.py's all-quarters estimate (2006-2026, e = 0.71) is identified by the COVID quarters; without
  2020-2021 the estimate is 0.15 (not significant) and in 2006-2019 it is -0.23 (no relation). The no-COVID value is run as a
  sensitivity ("no-COVID Okun" row); a report must say that e rests on 2020-21.
Range: e +- 2 standard errors (all-quarters estimate). Labour input in the model is persons x hours; the LFS series on file gives
persons only, so the target is a lower bound for the hours-inclusive response (stated in the report).
Method: bisection on beta (dynamic.py option wage_curve). NOT FOR CITATION until reviewed.
Run:  py scenarios/calibrate_wage_curve.py   (about 15 minutes: five calibrations)
"""
import sys

from _common import ROOT
import numpy as np
import pandas as pd

sys.path.insert(0, str(ROOT / "preshock"))
from infinity_gem import paths                                                     # noqa: E402
import combined_revised as CR                                                   # noqa: E402
import okun                                                                     # noqa: E402

YEAR = 2026
ACTUAL_2026, PRE_SHOCK_2026 = 2.6, 5.5            # PSA H1 2026 growth; DBCC 192nd (9 Dec 2025) midpoint (upper-bound target only)


def stats(R, piece, beta):
    """(labour input 2026 %, GDP gap 2026 %, GDP gap 2025 %, growth effect 2026 pp) at a given beta."""
    R.d.a["wage_curve"] = beta if beta > 0 else None
    clean = R.run(set(), piece=piece)
    adv = R.run(set(CR.SHOCKS), piece=piece)
    m = R.d.m
    b, s = clean.solutions[YEAR], adv.solutions[YEAR]
    lab = [k for k, f in enumerate(m.F) if f.startswith("flab")]
    wb = np.array([float(b["WF"][k] * b["EMP"][k]) for k in lab])
    emp = np.array([float(s["EMP"][k] / b["EMP"][k] - 1) for k in lab]) * 100
    g26 = float(adv.table.real_gdp[YEAR] / clean.table.real_gdp[YEAR] - 1) * 100
    g25 = float(adv.table.real_gdp[YEAR - 1] / clean.table.real_gdp[YEAR - 1] - 1) * 100
    growth_eff = ((1 + g26 / 100) / (1 + g25 / 100) - 1) * 100
    return float(np.average(emp, weights=wb)), g26, g25, growth_eff


def calibrate(resid, R, piece, lo=0.0, hi=40.0, tol=2e-3):
    """beta at which resid(stats) crosses zero (resid rises with beta: more wage flexibility, smaller job loss).
    Returns hi when the root lies above it (the wage curve is then close to flexible wages: labour input within 0.2%)."""
    r_lo, r_hi = resid(stats(R, piece, lo)), resid(stats(R, piece, hi))
    if r_lo > 0:
        raise RuntimeError(f"no root: residual {r_lo:.3f} at beta {lo}")
    if r_hi < 0:
        print(f"root above beta {hi} (residual {r_hi:.4f}): reported as {hi}")
        return hi
    while hi - lo > tol:
        mid = (lo + hi) / 2
        if resid(stats(R, piece, mid)) < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def main():
    est = okun.estimates()
    row = est.loc["2006-2026, all quarters"]
    e, se = float(row["elasticity e"]), float(row["s.e."])
    e_nocovid = float(est.loc["2006-2026, 2020-2021 dropped", "elasticity e"])
    import okun_hours                                     # 0.3.10: the hours-inclusive target (18 Oct 2026)
    eh = okun_hours.estimates().set_index(["margin", "sample"])
    e_hours = float(eh.loc[("total hours per person 15+", "2006-2026 without 2020-2021"), "b"])
    R = CR.Runs("low")
    piece, _ = R.pieces()
    cols = ("labour input 2026 (%)", "GDP gap 2026 (%)", "GDP gap 2025 (%)", "growth effect 2026 (pp)")

    def record(beta, target_note):
        l, g26, g25, ge = stats(R, piece, beta)
        return {"beta": beta, "employment / GDP": l / g26, **dict(zip(cols, (l, g26, g25, ge))), "target": target_note}

    out = {"no wage curve (beta 0)": record(0.0, "none")}
    # central and range: labour input = e x the model's own growth effect (fixed point)
    for name, ee in (("central (e)", e), ("smaller job loss (e - 2 s.e.)", e - 2 * se), ("larger job loss (e + 2 s.e.)", e + 2 * se),
                     ("no-COVID Okun (2020-2021 dropped)", e_nocovid),
                     ("hours-inclusive Okun (2020-2021 dropped)", e_hours)):
        bt = calibrate(lambda s, ee=ee: s[0] - ee * s[3], R, piece)
        out[name] = record(bt, f"{ee:.3f} x model growth effect")
    # upper bound: the 16 Oct target, the job loss of the whole observed shortfall
    tgt = e * (ACTUAL_2026 - PRE_SHOCK_2026)
    bt = calibrate(lambda s: s[0] - tgt, R, piece)
    out["observed shortfall (previous central; upper bound)"] = record(bt, f"{tgt:.3f} = {e:.3f} x ({ACTUAL_2026} - {PRE_SHOCK_2026})")
    t = pd.DataFrame(out).T
    u0 = 0.039                                           # unemployment rate, August 2025 (PSA LFS)
    t["implied pay elasticity to the unemployment rate"] = -t["beta"].astype(float) * u0 / (1 - u0)
    print(t.to_string())
    L = [f"# Wage curve calibrated to PSA's output-employment relation ({pd.Timestamp.today():%d %B %Y})", "",
         "**NOT FOR CITATION** (Infinity GEM 0.3.8). Script: `scenarios/calibrate_wage_curve.py`; data relation: "
         f"`preshock/okun.py` (all quarters 2006-2026: e = {e:.3f}, s.e. {se:.3f}; without 2020-2021: e = {e_nocovid:.3f}, not "
         "significant; 2006-2019: no relation). **Target (17 Oct 2026, code review C1):** 2026 labour input = e x the model's OWN "
         "effect on 2026 growth (a fixed point in beta). The 16 Oct target, e x the whole observed shortfall (H1 2026 growth "
         f"{ACTUAL_2026}% - pre-shock {PRE_SHOCK_2026}%), is kept as the upper bound. Combined 2025-27 shocks, public capital low, "
         "2026. 'Implied pay elasticity': the slope of pay on the unemployment rate the beta implies at 3.9% unemployment "
         "(Blanchflower and Oswald 1994: about -0.1 internationally).", "", t.to_markdown(floatfmt=".4f"),
         "", "Labour input in the model is persons x hours; the LFS series on file gives persons only, so the target is a lower "
         "bound for the hours-inclusive response. The Okun elasticity used for the central row is identified by the COVID "
         "quarters (okun.py): the no-COVID row shows what the 2006-2026 relation without 2020-2021 would give."]
    out_f = paths.output_dir() / f"wage_curve_calibration_{pd.Timestamp.today():%Y%m%d}{__import__('_common').out_tag()}.md"   # 0.3.10: SAM tag
    out_f.write_text("\n".join(L), encoding="utf-8")
    t.to_csv(out_f.with_suffix(".csv"))
    print("saved", out_f)


if __name__ == "__main__":
    main()
