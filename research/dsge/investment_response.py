"""DSGE research, milestone 20b (20 Oct 2026, about 9:30 AM): investment's response to monetary policy, better identified.

Why: the DSGE-CGE link needs theta, the % fall in real investment per pp of real-rate gap (scenarios/qpm_cge_link.py
mode=elastic). Milestone 20 (investment_lp.py; reaction-function surprises, 2002-2019) bracketed it between about 0.2 and 2.3
with nothing significant, so the poverty effect of the BSP's oil response stayed between about 0 and 0.4 M. Two improvements:
1. SAMPLE: 2002Q1-2026Q2, the COVID quarters 2020Q1-2021Q4 excluded (no projection window touches them): about a third more
   quarters.
2. IDENTIFICATION: besides the reaction-function residuals (milestone 12's method, re-estimated on the long sample), the monetary
   policy shocks of the converged DSGE (soe_htmu, milestone 19: cost-push shock, 2002-2026, STL GDP), recovered by a
   Kalman (Rauch-Tung-Striebel) smoother at the posterior mean: e_v,t = v_t|T - rho_v v_t-1|T. The DSGE has no investment, so
   investment plays no part in identifying these shocks; and the cost-push shock keeps supply-driven inflation from being
   read as policy.
Local projections (Jorda 2005) of log real GFCF (PSA, STL-adjusted), GDP, CPI and the policy rate on each shock, h = 0..8,
controls four lags of the changes of the five variables, Newey-West errors; scaled to +1 pp on the policy rate on impact.
theta: minus the average investment response divided by the average real-rate response (policy rate minus next quarter's
annualized CPI-inflation response), for year 1, year 2 and both years together.
Run:  py investment_response.py      (writes outputs/dsge_investment_response_<stamp>.md)
Jorda, O. (2005). "Estimation and Inference of Impulse Responses by Local Projections." American Economic Review 95(1): 161-182.
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
sys.argv = [sys.argv[0], "model=htmu", "sample=long", "gdp=stl"]
import estimate_rot as ER               # noqa: E402  (soe_htmu, its observables and state space)
import ph_data as D                     # noqa: E402
import transmission_benchmarks as TB    # noqa: E402
from investment_lp import gfcf_q        # noqa: E402

OUT = HERE.parents[1] / "outputs"
H = 8
COVID = (pd.Period(D.COVID[0], "Q"), pd.Period(D.COVID[1], "Q"))


def smoothed_policy_shocks():
    """Posterior-mean soe_htmu (pooled converged chains); RTS smoother on 2002Q1-2026Q2 (COVID quarters missing)."""
    files = sorted(OUT.glob("dsge_ph_htmu_draws_*_w1_ratio_long_stl_seed*.npy"))
    theta = np.vstack([np.load(f) for f in files]).mean(0)
    kw, sds = ER.split(theta)
    sol, _ = ER.R.solve(ER.R.Params(rule="output", **kw))
    Pm, Rm, Q, Hm = ER.state_space(sol, sds)
    Z = ER.observables()
    idx = D.observables(end=D.LONG_END, covid="missing", gdp_sa="stl").index
    n = Pm.shape[0]
    RQR = Rm @ Q @ Rm.T
    from scipy import linalg
    S = linalg.solve_discrete_lyapunov(Pm, RQR)
    x = np.zeros(n)
    Me = np.eye(Hm.shape[0]) * 1e-4                         # as estimate.kalman_loglik
    xp, Sp, xf, Sf = [], [], [], []
    for z in Z:
        xp.append(x); Sp.append(S)
        ok = np.isfinite(z)
        if ok.any():
            Hk, Mk = Hm[ok], Me[np.ix_(ok, ok)]
            F = Hk @ S @ Hk.T + Mk
            G = S @ Hk.T @ np.linalg.inv(F)
            x, S = x + G @ (z[ok] - Hk @ x), S - G @ Hk @ S
        xf.append(x); Sf.append(S)
        x, S = Pm @ x, Pm @ S @ Pm.T + RQR
    xs = [None] * len(Z)
    xs[-1] = xf[-1]
    for t in range(len(Z) - 2, -1, -1):
        J = Sf[t] @ Pm.T @ np.linalg.pinv(Sp[t + 1])
        xs[t] = xf[t] + J @ (xs[t + 1] - xp[t + 1])
    ixv = ER.R.STATES.index("v")
    nk = len(ER.R.STATES)
    v = np.array([s_[ixv] for s_ in xs])
    v_lag = np.array([s_[nk + ixv] for s_ in xs])
    e = pd.Series(400 * (v - kw["rho_v"] * v_lag), index=idx, name="shock")     # pp a year
    return e, files


def covid_free(index, lo, hi):
    """True where no quarter in [t + lo, t + hi] falls in the COVID quarters."""
    return pd.Series([not any(COVID[0] <= t + k <= COVID[1] for k in range(lo, hi + 1)) for t in index], index=index)


def lp(L, shock):
    dL = L.diff()
    ctrl = pd.concat({f"{c}_l{k}": dL[c].shift(k) for c in dL.columns for k in range(1, 5)}, axis=1)
    out = {v: [] for v in L.columns}
    for h in range(H + 1):
        keep = covid_free(L.index, -5, h)
        for v in L.columns:
            y = (L[v].shift(-h) - L[v].shift(1)).rename("y")
            m = pd.concat([y, shock, ctrl], axis=1)[keep].dropna()
            r = sm.OLS(m["y"], sm.add_constant(m.drop(columns="y"))).fit(cov_type="HAC", cov_kwds={"maxlags": h + 1})
            out[v].append((float(r.params["shock"]), float(r.bse["shock"]), int(r.nobs)))
    return out


def summarize(res):
    b = {v: np.array([x[0] for x in res[v]]) for v in res}
    se = {v: np.array([x[1] for x in res[v]]) for v in res}
    s = 1.0 / b["i"][0]
    infl_ann = 4 * np.diff(b["lcpi"], append=np.nan)
    real = s * (b["i"] - infl_ann)
    rows = pd.DataFrame({"policy rate (pp)": s * b["i"], "real rate (pp)": real, "investment (%)": s * b["linv"],
                         "investment s.e.": abs(s) * se["linv"], "GDP (%)": s * b["lgdp"], "GDP s.e.": abs(s) * se["lgdp"],
                         "CPI (%)": s * b["lcpi"], "CPI s.e.": abs(s) * se["lcpi"]},
                        index=pd.Index(range(H + 1), name="quarters after the shock"))
    th = {}
    for name, sl in (("year 1", slice(0, 4)), ("year 2", slice(4, 8)), ("years 1-2", slice(0, 8))):
        inv, rr = rows["investment (%)"].iloc[sl].mean(), rows["real rate (pp)"].iloc[sl].mean()
        inv_se = rows["investment s.e."].iloc[sl].mean()                # conservative: s.e.s averaged, not combined
        th[name] = {"investment (%)": inv, "investment s.e. (avg)": inv_se, "real rate (pp)": rr,
                    "theta (% per pp)": -inv / rr if abs(rr) > 1e-6 else np.nan,
                    "theta, +/- 1 s.e. of investment": f"{-(inv + inv_se) / rr:.2f} to {-(inv - inv_se) / rr:.2f}" if abs(rr) > 1e-6 else ""}
    out = pd.DataFrame(th).T
    return rows, out, s, res["linv"][0][2]


def main():
    L = TB.quarterly_levels()
    L["lgdp"] = 100 * np.log(D._gdp_sa_stl(D._gdp_q())).reindex(L.index)
    L["linv"] = 100 * np.log(gfcf_q()).reindex(L.index)
    L = L.loc[pd.Period("2000Q1", "Q"):pd.Period(D.LONG_END, "Q")].dropna()
    # (1) reaction-function surprises re-estimated on 2002-2026 without the COVID quarters
    d = pd.DataFrame({"di": L["i"].diff(), "infl": L["lcpi"].diff(4), "gr": L["lgdp"].diff(4), "de": L["lfx"].diff()})
    X = pd.DataFrame({"infl": d["infl"].shift(1), "gr": d["gr"].shift(1), "de": d["de"].shift(1), "di_l1": d["di"].shift(1),
                      "infl2": d["infl"].shift(2), "gr2": d["gr"].shift(2)})
    m = pd.concat([d["di"], X], axis=1).loc[pd.Period("2002Q1", "Q"):pd.Period(D.LONG_END, "Q")]
    m = m[covid_free(m.index, -2, 0)].dropna()
    rf = sm.OLS(m["di"], sm.add_constant(m.drop(columns="di"))).fit()
    shocks = {"reaction-function surprises, 2002-2026": rf.resid.rename("shock")}
    # (2) the DSGE's smoothed monetary-policy shocks
    e, files = smoothed_policy_shocks()
    e = e[covid_free(e.index, 0, 0)]
    shocks["the project's DSGE (soe_htmu) smoothed policy shocks, 2002-2026"] = e
    corr = float(pd.concat([shocks["reaction-function surprises, 2002-2026"], e], axis=1).dropna().corr().iloc[0, 1])
    blocks, summary = [], {}
    for name, sh in shocks.items():
        rows, th, s, nobs = summarize(lp(L[["i", "lcpi", "lgdp", "linv", "lfx"]], sh))
        summary[name] = {"quarters (h = 0)": nobs, "theta year 1": th.loc["year 1", "theta (% per pp)"],
                         "theta year 2": th.loc["year 2", "theta (% per pp)"], "theta years 1-2": th.loc["years 1-2", "theta (% per pp)"],
                         "GDP year 1 (%)": rows["GDP (%)"].iloc[0:4].mean(), "GDP year 2 (%)": rows["GDP (%)"].iloc[4:8].mean(),
                         "CPI after 8 quarters (%)": rows["CPI (%)"].iloc[8]}
        blocks += [f"## {name}", "", f"Scale: {s:.2f} per unit of shock (+1 pp on the policy rate on impact).", "",
                   th.to_markdown(floatfmt=".3f"), "", rows.to_markdown(floatfmt=".3f"), ""]
    S = pd.DataFrame(summary).T
    stamp = dt.datetime.now()
    lines = [f"# Investment's response to monetary policy, better identified (milestone 20b; {stamp:%d %B %Y, %H:%M})", "",
             "**NOT FOR CITATION** (research code, `research/dsge/investment_response.py`). Local projections, 2002Q1-2026Q2 with "
             "no window touching the COVID quarters 2020Q1-2021Q4; PSA real GFCF and GDP STL-adjusted; Newey-West errors. Shocks: "
             f"(1) reaction-function residuals (R-squared {rf.rsquared:.2f}, {int(rf.nobs)} quarters); (2) the project's DSGE (soe_htmu, "
             f"posterior mean of {len(files)} converged chains) smoothed policy shocks. Correlation of the two shock series: {corr:.2f}.", "",
             "For comparison: theta in the CGE link 0.55 (milestone 14), 1.9 (QPM, held for a year), 2.7-3.3 (soe_htmu); milestone 20 "
             "(2002-2019): 0.2 (year 1), 2.3 (year 2).", "",
             "## Summary", "", S.to_markdown(floatfmt=".2f"), ""] + blocks
    f = OUT / f"dsge_investment_response_{stamp:%Y%m%d_%H%M}.md"
    f.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:9])); print(S.round(2).to_string()); print("saved", f)


if __name__ == "__main__":
    main()
