"""DSGE research, milestone 12 (19 Oct 2026): an independent, data-based benchmark for Philippine monetary transmission.

Why: on Philippine data alone the DSGE (milestones 4, 6, 10, 11) gives a policy shock 10-15 times the effect in the BSP's PAMPh;
imposing PAMPh's responses costs 92-119 log points of fit. Before choosing which transmission the DSGE should carry, a third,
model-free view on the same data:
1. policy surprises: residuals of a quarterly reaction function, the change in the BIS policy rate on the previous quarter's
   y/y CPI inflation, y/y real GDP growth, peso depreciation and the previous rate change (2002-2019; a Romer-Romer-style
   narrative-free version);
2. local projections (Jorda 2005): log CPI, log real GDP, log PHP/USD and the policy rate h = 0..12 quarters ahead, minus their
   level before the shock, on the surprise, with four lags of the four variables' changes as controls; Newey-West standard
   errors (h + 1 lags);
3. results in PAMPh's units, scaled to a +0.80 pp impact on the policy rate (pp y/y for CPI inflation and GDP growth: the
   level response minus its value four quarters earlier; 100 log for the peso), next to PAMPh, the BSP's 2009 DSGE and VAR note,
   and the DSGE estimates. The sample is short (about 70 quarters) and the bands wide: a benchmark, not a precise estimate.
Also: the standard deviation of quarterly changes in the policy rate, 2012-2021, to read the BSP VAR note (RN 2021-02), whose
shock is one standard deviation of that change.
Jorda, O. (2005). "Estimation and Inference of Impulse Responses by Local Projections." American Economic Review 95(1): 161-182.
Romer, C. D., and D. H. Romer (2004). "A New Measure of Monetary Shocks." American Economic Review 94(4): 1055-1084.
Run:  py transmission_benchmarks.py     (writes outputs/dsge_transmission_benchmarks_<stamp>.md)
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pamph_targets as T   # noqa: E402
import ph_data as D         # noqa: E402

OUT = HERE.parents[1] / "outputs"
H = 12


def quarterly_levels():
    gdp, cpi = D._gdp_q(), D._cpi_q()
    rate = D._q_from_month(pd.read_csv(D.RAW / "BIS_WS_CBPOL_policy_rate_Philippines_monthly.csv", comment="#"))
    fx = D._q_from_month(pd.read_csv(D.RAW / "BIS_WS_XRU_PHP_per_USD_monthly_average.csv", comment="#"))
    L = pd.DataFrame({"lgdp": 100 * np.log(gdp), "lcpi": 100 * np.log(cpi), "i": rate, "lfx": 100 * np.log(fx)}).dropna()
    return L


def surprises(L, start="2002Q1", end="2019Q4"):
    d = pd.DataFrame({"di": L["i"].diff(), "infl": L["lcpi"].diff(4), "gr": L["lgdp"].diff(4), "de": L["lfx"].diff()})
    X = pd.DataFrame({"infl": d["infl"].shift(1), "gr": d["gr"].shift(1), "de": d["de"].shift(1), "di_l1": d["di"].shift(1),
                      "infl2": d["infl"].shift(2), "gr2": d["gr"].shift(2)})
    m = pd.concat([d["di"], X], axis=1).dropna().loc[pd.Period(start, "Q"):pd.Period(end, "Q")]
    res = sm.OLS(m["di"], sm.add_constant(m.drop(columns="di"))).fit()
    return res.resid.rename("shock"), res


def local_projections(L, shock):
    dL = L.diff()
    ctrl = pd.concat({f"{c}_l{k}": dL[c].shift(k) for c in dL.columns for k in range(1, 5)}, axis=1)
    out = {v: [] for v in L.columns}
    for h in range(H + 1):
        for v in L.columns:
            y = (L[v].shift(-h) - L[v].shift(1)).rename("y")
            m = pd.concat([y, shock, ctrl], axis=1).dropna()
            r = sm.OLS(m["y"], sm.add_constant(m.drop(columns="y"))).fit(cov_type="HAC", cov_kwds={"maxlags": h + 1})
            out[v].append((r.params["shock"], r.bse["shock"], int(r.nobs)))
    return out


def pamph_units(lp, scale):
    """Responses at T.QUARTERS (quarter 1 = impact, h = 0), scaled so that the policy rate rises scale pp on impact."""
    b = {v: np.array([x[0] for x in lp[v]]) for v in lp}
    se = {v: np.array([x[1] for x in lp[v]]) for v in lp}
    s = scale / b["i"][0]
    yoy = lambda v, h: (b[v][h] - (b[v][h - 4] if h >= 4 else 0.0))
    yoy_se = lambda v, h: np.hypot(se[v][h], se[v][h - 4] if h >= 4 else 0.0)
    res = {"rate": {}, "growth": {}, "infl": {}, "fx": {}, "growth_se": {}, "infl_se": {}, "fx_se": {}}
    for q in T.QUARTERS:
        h = q - 1
        if h > H:
            continue
        res["rate"][q] = s * b["i"][h]
        res["growth"][q], res["growth_se"][q] = s * yoy("lgdp", h), abs(s) * yoy_se("lgdp", h)
        res["infl"][q], res["infl_se"][q] = s * yoy("lcpi", h), abs(s) * yoy_se("lcpi", h)
        res["fx"][q], res["fx_se"][q] = s * b["lfx"][h], abs(s) * se["lfx"][h]      # 100 log PHP per USD: - = appreciation, as in PAMPh
    return res, s


HTM_NAMES = ["sigma", "theta", "theta_F", "hab", "omega_H", "omega_F", "lam_h", "kappa", "phi_pi", "phi_x", "phi_e", "rho_i",
             "rho_a", "rho_y", "rho_ps", "rho_v", "rho_z", "sd_v", "sd_a", "sd_ystar", "sd_pistar", "sd_zeta"]


def model_paths():
    """Policy-rate and CPI y/y paths (per +0.80 pp on impact) of the estimated DSGEs at their posterior means."""
    import estimate_rot as ER
    import soe_htm
    import soe_rot
    out = {}
    for tag, mod, names in (("rot", soe_rot, ER.NAMES), ("htm", soe_htm, HTM_NAMES)):
        for w in ("0", "1"):
            files = sorted(OUT.glob(f"dsge_ph_{tag}_draws_*_w{w}.npy"))
            if not files:
                continue
            kw = {k: v for k, v in zip(names, np.load(files[-1]).mean(0)) if not k.startswith("sd_")}
            r = mod.irf(mod.Params(rule="output", **kw), "v", 0.001, T=24)
            s = 0.80 / (400 * r["i"][0])
            rate = 400 * s * r["i"]
            pi = 100 * s * np.concatenate([[0.0], r["pi"]])
            infl = np.array([pi[max(q - 3, 0):q + 1].sum() for q in range(1, 21)])
            out[f"soe_{tag}, w = {w}"] = (rate[:4].sum(), infl.min())
    return out


def main():
    L = quarterly_levels()
    sd_di = float(L["i"].diff().loc[pd.Period("2012Q1", "Q"):pd.Period("2021Q4", "Q")].std())
    shock, rule = surprises(L)
    lp = local_projections(L, shock)
    resp, s = pamph_units(lp, 0.80)
    qs = [q for q in T.QUARTERS if q - 1 <= H]
    tab = pd.DataFrame({
        ("policy rate (pp p.a.)", "PAMPh"): {q: T.POLICY_RATE_PA[q] for q in qs},
        ("policy rate (pp p.a.)", "the project's local projections"): resp["rate"],
        ("GDP growth (pp y/y)", "PAMPh"): {q: T.GDP_GROWTH_YOY[q] for q in qs},
        ("GDP growth (pp y/y)", "the project's local projections"): resp["growth"],
        ("GDP growth (pp y/y)", "  s.e."): resp["growth_se"],
        ("CPI inflation (pp y/y)", "PAMPh"): {q: T.CPI_INFLATION_YOY[q] for q in qs},
        ("CPI inflation (pp y/y)", "the project's local projections"): resp["infl"],
        ("CPI inflation (pp y/y)", "  s.e."): resp["infl_se"],
        ("nominal exchange rate (100 log, PAMPh's sign)", "PAMPh"): {q: T.NOMINAL_EXCHANGE_RATE_100LOG[q] for q in qs},
        ("nominal exchange rate (100 log, PAMPh's sign)", "the project's local projections"): resp["fx"],
        ("nominal exchange rate (100 log, PAMPh's sign)", "  s.e."): resp["fx_se"],
    }).T
    tab.columns = [f"q{q}" for q in qs]
    # transmission per unit of first-year tightening: CPI y/y trough / sum of the policy-rate path over quarters 1-4 (pp); the
    # first year, because later quarters reverse in some models (an 8-quarter sum can be near zero and the ratio meaningless)
    cum = {"PAMPh (BSP WPS 2020-12)": (sum(T.POLICY_RATE_PA[q] for q in range(1, 5)), min(T.CPI_INFLATION_YOY.values())),
           "the project's local projections (this file)": (sum(resp["rate"][q] for q in range(1, 5)), min(resp["infl"].values())),
           "BSP DSGE 2009 (WPS 2009-01, Fig. 3: 25 bp for 8 quarters; inflation peak about 0.45, read off the chart)": (0.25 * 4, -0.45)}
    cum.update(model_paths())
    ctab = pd.DataFrame({k: {"4-quarter sum of the policy-rate path (pp)": v[0], "CPI y/y trough (pp)": v[1],
                             "trough per pp of cumulative rate": v[1] / v[0] if abs(v[0]) > 1e-9 else np.nan}
                         for k, v in cum.items()}).T
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    Lines = [f"# DSGE research, milestone 12: a data-based benchmark for Philippine monetary transmission ({dt.datetime.now():%d %B %Y, %H:%M})", "",
             "**NOT FOR CITATION** (research code, `research/dsge/transmission_benchmarks.py`). Policy surprises = residuals of a "
             f"quarterly reaction function for the change in the BIS policy rate, 2002-2019 ({int(rule.nobs)} quarters, R2 {rule.rsquared:.2f}); "
             "local projections of log CPI, log real GDP, log PHP/USD and the policy rate on the surprise, four lags of each "
             "variable's change as controls, Newey-West standard errors; scaled to +0.80 pp on the policy rate on impact "
             f"(scale {s:.2f} per unit of surprise). Short sample: read the standard errors.", "",
             f"- Standard deviation of the quarterly change in the policy rate, 2012-2021 (the shock size in the BSP VAR note, "
             f"RN 2021-02): **{sd_di:.2f} pp**.", "",
             "## Responses in PAMPh's units", "", tab.to_markdown(floatfmt=".2f"), "",
             "## Transmission per unit of cumulative tightening", "",
             "Different models (and the data) follow a surprise with very different policy-rate paths, so responses 'per +0.80 pp "
             "on impact' compare different policies. Below: the CPI y/y trough divided by the sum of the policy-rate path over "
             "quarters 1-4 (the first year's tightening). The BSP DSGE row is a 25 bp cut held 8 quarters, signs flipped to a tightening; its chart was read "
             "by eye.", "", ctab.to_markdown(floatfmt=".2f")]
    path = OUT / f"dsge_transmission_benchmarks_{stamp}.md"
    path.write_text("\n".join(Lines) + "\n", encoding="utf-8")
    print("\n".join(Lines)); print("saved", path)


if __name__ == "__main__":
    main()
