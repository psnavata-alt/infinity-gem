"""Joint ranges (MANAGE-WB blueprint, 19 Oct 2026, about 11:10 PM): joint uncertainty bands for the combined 2026 result (20 Oct 2026) by
Latin-hypercube sampling of the parameters that The one-at-a-time table varies.

Research output, NOT FOR CITATION. MANAGE-WB's own uncertainty tools: Latin-hypercube sensitivity and
stochastic runs (Beyene et al. 2025, PRWP 11258).

Setting: the 2026 scenarios of 20 Oct 2026 (Infinity GEM's own SAM; hoarding; the wage curve calibrated without hoarding; public capital low; Leontief fuel).
One model is calibrated once; each draw changes only parameters that do not move the no-shock baseline, and reruns the
no-shock path and the four shocks. Draw 0 is the central 2026 case (it must give the central row of the one-at-a-time table).

Parameters and distributions (the ranges are those of the one-at-a-time sensitivity table; the shapes are ASSUMPTIONS, stated in the output):
  hoarding           triangular 0.75 / 0.85 / 0.95       the labour-hoarding evidence: 75-95%
  Okun z             normal, truncated at +-2 s.e.        wage-curve slope interpolated between the three calibrated slopes
                                                          (e - 2 s.e., e, e + 2 s.e.; calibration file of the 2026 scenarios)
  public capital     triangular 0 / 0 / 1 between the    output elasticity 0.083 -> 0.122 and public capital/GDP 0.397 -> 0.296
  return u           'low' (central) and 'high' settings  (settings.PUBLIC_CAPITAL)
  efficiency e       triangular 0.60 / 0.77 / 0.77        IMF PIMA 0.77 (central, [35]); IMF base case 0.60 ([46])
  oil, no-conflict   uniform US$60-70                     the DBCC's range
  El Nino ONI        triangular 1.5 / 2.0 / 2.5           the sensitivity table
  job-gap carry-over triangular 0 / 0.5 / 1               none or all instead of half
  public works H2    triangular 0 / 0 / 1 between H2 2026 at H1's rate (central) and H2 2026 = H2 2025 (the sensitivity table)
Not sampled: price stickiness (needs a recalibrated wage curve per draw), the 2027 budget scenarios (policy, not
parameters), FIES sampling error (separate bootstrap), the energy bundle (moves the baseline).

Run:  INFINITY_GEM_SCENARIO_SAM=own  py scenarios/lhs_2026_ranges.py [N] [--resume]    (N draws after the central one; ~4 min each)
Output: outputs/lhs_2026_ranges_draws{tag}.csv (one row per draw, appended as it goes) and a dated summary .md.
"""
import functools
import sys
import time
import warnings

import numpy as np
import pandas as pd
from scipy.stats import qmc, truncnorm

import _common
import combined_revised as CR
from infinity_gem import paths
from infinity_gem.dynamic import PUBLIC_CAPITAL_DEFAULTS
from infinity_gem.settings import PUBLIC_CAPITAL

SEED = 20261019
PARAMS = ["hoarding", "okun_z", "pubcap_u", "efficiency_e", "oil_no_conflict", "oni", "gap_carry", "pw_h2_v"]
CENTRAL = dict(hoarding=0.85, okun_z=0.0, pubcap_u=0.0, efficiency_e=0.77, oil_no_conflict=65.0, oni=2.0, gap_carry=0.5, pw_h2_v=0.0)
KEYS = ("GDP gap 2026 (%)", "GDP gap 2027 (%)", "GDP gap 2030 (%)", "cumulative GDP loss 2025-2030 (₱ bn)",
        "new poor 2026 (M, own baskets)", "new poor 2027 (M, own baskets)", "consumer prices 2026 (%)")
COLS = PARAMS + list(KEYS) + ["wage-curve beta", "phi", "kg_gdp", "error", "seconds"]
CR.land_cuts = functools.lru_cache(maxsize=None)(CR.land_cuts)   # pieces() sizes the central El Nino once; each draw its own


def tri(u, a, c, b):
    """Inverse CDF of the triangular distribution (min a, mode c, max b)."""
    if b == a:
        return a
    f = (c - a) / (b - a)
    return np.where(u < f, a + np.sqrt(u * (b - a) * (c - a)), b - np.sqrt((1 - u) * (b - a) * (b - c)))


def draws(n):
    u = qmc.LatinHypercube(d=len(PARAMS), seed=SEED).random(n)
    d = pd.DataFrame({
        "hoarding": tri(u[:, 0], 0.75, 0.85, 0.95),
        "okun_z": truncnorm.ppf(u[:, 1], -2, 2),
        "pubcap_u": tri(u[:, 2], 0.0, 0.0, 1.0),
        "efficiency_e": tri(u[:, 3], 0.60, 0.77, 0.77),
        "oil_no_conflict": 60 + 10 * u[:, 4],
        "oni": tri(u[:, 5], 1.5, 2.0, 2.5),
        "gap_carry": tri(u[:, 6], 0.0, 0.5, 1.0),
        "pw_h2_v": tri(u[:, 7], 0.0, 0.0, 1.0)})
    return pd.concat([pd.DataFrame([CENTRAL]), d], ignore_index=True)


class CentralModel:
    """The central 2026 model (20 Oct 2026), calibrated once; parameters set in place for each draw."""

    def __init__(self):
        cal = pd.read_csv(_common.calibration_file(), index_col=0)
        self.beta = {-2.0: float(cal.loc["smaller job loss (e - 2 s.e.)", "beta"]), 0.0: float(cal.loc["central (e)", "beta"]),
                     2.0: float(cal.loc["larger job loss (e + 2 s.e.)", "beta"])}
        self.R = CR.Runs("low", wage_curve=self.beta[0.0], hoarding=0.85)
        self.carry0 = float(self.R.d.a["gap_persistence"])
        if abs(self.carry0 - CENTRAL["gap_carry"]) > 1e-12:
            raise SystemExit(f"the 2026 scenarios' job-gap carry-over is {self.carry0}, not {CENTRAL['gap_carry']}: update CENTRAL")
        self.pw = None

    def set(self, p):
        d = self.R.d
        d.a["hoarding"] = d._kw_sr["hoarding"] = float(p["hoarding"])   # _kw_sr: short-run models built later (employment cap)
        for m in {id(d.ms): d.ms, **{id(x): x for x in d._ms_cache.values()}}.values():
            m.hoarding = float(p["hoarding"])
        z = float(p["okun_z"])
        d.a["wage_curve"] = float(np.interp(z, [-2.0, 0.0, 2.0], [self.beta[-2.0], self.beta[0.0], self.beta[2.0]]))
        lo, hi, u = PUBLIC_CAPITAL["low"], PUBLIC_CAPITAL["high"], float(p["pubcap_u"])
        pc = dict(phi=lo["phi"] + u * (hi["phi"] - lo["phi"]), kg_gdp=lo["kg_gdp"] + u * (hi["kg_gdp"] - lo["kg_gdp"]),
                  general_stock=False, e=float(p["efficiency_e"]))
        d.a["public_capital"], d.pc = pc, dict(PUBLIC_CAPITAL_DEFAULTS, **pc)
        d.a["gap_persistence"] = float(p["gap_carry"])
        CR.SP.DBCC_192["lhs"] = float(p["oil_no_conflict"])
        piece, src = self.R.pieces(oil_nc="lhs")
        _, cuts = CR.land_cuts(float(p["oni"]))
        piece["El Nino"] = {2026: {"lscale": cuts[2026]}, 2027: {"lscale": cuts[2027]}}
        pw = src["public works"]
        bn26 = pw["2026 central"] + float(p["pw_h2_v"]) * (pw["2026 low"] - pw["2026 central"])
        piece["public works"][2026] = {"qinv_scale": {"ccons": 1 + CR.to_sam_units(bn26, CR.PSA_GDP[2026]) / self.R.q0}}
        works = {2025: pw["2025"], 2026: bn26, 2027: pw["2027 NEP x 2025 rate (central)"]}
        return piece, works, d.a["wage_curve"], pc

    def run(self, p):
        piece, works, beta, pc = self.set(p)
        clean = self.R.run(set(), piece=piece)
        out = self.R.measures(clean, self.R.run(set(CR.SHOCKS), piece=piece), works=works, poor=True)[0]
        return {**{k: out[k] for k in KEYS}, "wage-curve beta": beta, "phi": pc["phi"], "kg_gdp": pc["kg_gdp"], "error": ""}


def summarise(t, f_md, n_planned):
    c = t.iloc[0]
    s = t.iloc[1:].dropna(subset=list(KEYS))         # draws that did not solve are listed below, not in the ranges
    rows = {}
    for k in KEYS:
        q = s[k].quantile([0.05, 0.5, 0.95])
        rows[k] = {"central (draw 0)": c[k], "mean": s[k].mean(), "5th pct": q[0.05], "median": q[0.5], "95th pct": q[0.95],
                   "min": s[k].min(), "max": s[k].max()}
    band = pd.DataFrame(rows).T
    corr = pd.DataFrame({k: {p_: s[p_].corr(s[k], method="spearman") for p_ in PARAMS} for k in KEYS})
    stamp = pd.Timestamp.today()
    f_md.write_text("\n".join([
        f"# The central 2026 setting (20 Oct 2026): joint ranges by Latin-hypercube sampling ({stamp:%d %B %Y, %H:%M})", "",
        "**NOT FOR CITATION** (Infinity GEM 0.3.11 step 2). "
        f"{len(s)} Latin-hypercube draws (of {n_planned} planned; seed {SEED}) over the parameters The one-at-a-time table varies; "
        "draw 0 = the central 2026 case. Distribution shapes are ASSUMPTIONS (script docstring). Infinity GEM's own SAM; Leontief fuel. "
        "Script `scenarios/lhs_2026_ranges.py`.", "",
        "## Joint ranges", "", band.to_markdown(floatfmt=".3f"), "",
        "## Which parameter moves each result (Spearman rank correlation across draws)", "", corr.to_markdown(floatfmt=".2f"), "",
        "## Draws", "", t.to_markdown(floatfmt=".3f")]), encoding="utf-8")


def main():
    if _common.SCENARIO_SAM != "own":
        raise SystemExit("run with INFINITY_GEM_SCENARIO_SAM=own (the SAM of the central 2026 setting)")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    n = int(args[0]) if args else 40
    tag = _common.sam_tag()
    f_csv = paths.output_dir() / f"lhs_2026_ranges_draws{tag}.csv"
    plan = draws(n)
    done = pd.read_csv(f_csv, index_col=0) if ("--resume" in sys.argv and f_csv.exists()) else None
    if done is None and f_csv.exists():
        f_csv.rename(f_csv.with_name(f"{f_csv.stem}_before_{pd.Timestamp.today():%Y%m%d_%H%M}.csv"))
    B = CentralModel()
    for i, p in plan.iterrows():
        if done is not None and i in done.index:
            continue
        t0 = time.time()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                res = B.run(p)
            except Exception as e:                       # a draw that does not solve is recorded, not hidden
                res = {k: np.nan for k in KEYS} | {"error": repr(e)[:200]}
        row = pd.DataFrame([{**p.to_dict(), **res, "seconds": round(time.time() - t0)}], index=[i]).reindex(columns=COLS)
        row.to_csv(f_csv, mode="a", header=not f_csv.exists())
        print(f"draw {i}: GDP 2026 {res.get('GDP gap 2026 (%)', np.nan):.3f}%, new poor 2026 "
              f"{res.get('new poor 2026 (M, own baskets)', np.nan):.3f} M ({time.time() - t0:.0f} s)", flush=True)
    t = pd.read_csv(f_csv, index_col=0).sort_index()
    f_md = paths.output_dir() / f"lhs_2026_ranges_{pd.Timestamp.today():%Y%m%d_%H%M}{tag}.md"
    summarise(t, f_md, n)
    print("saved", f_md)


if __name__ == "__main__":
    main()
