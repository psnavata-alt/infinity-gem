"""DSGE research, milestone 20 (20 Oct 2026, about 02:40): how Philippine real investment responds to a BSP policy surprise,
for the DSGE-CGE link's investment semi-elasticity theta.

Why: the DSGE has no capital, so its output gap leaves out the investment channel. Linking the BSP's response to the 2026 oil
shock into the CGE gave about 0 new poor when matched to the DSGE's output gap, +93,000 at theta 0.55% of investment per pp of
real-rate gap and +439,000 at 3.0% (scenarios/qpm_cge_link.py mode=elastic). theta needs a data-based value.

Method, as milestone 12 (transmission_benchmarks.py) with investment added:
- policy surprises: the same residuals of a quarterly reaction function, 2002-2019;
- local projections (Jorda 2005) of log real gross fixed capital formation (PSA OpenSTAT 0012B5BEXQ1, constant 2018 prices,
  seasonally adjusted here by robust STL as for GDP in milestone 18b), the policy rate and log CPI, h = 0..8 quarters, with four
  lags of the changes in GDP, CPI, the policy rate, the peso and investment as controls; Newey-West errors (h + 1 lags);
- scaled to a +1 pp impact on the policy rate; real-rate path = policy rate minus the next quarter's annualized CPI inflation
  response; theta = minus the average investment response over a year divided by the average real-rate response that year.
The sample is short (about 70 quarters) and the bands wide: a benchmark for theta, not a precise estimate.
Run:  py investment_lp.py      (writes outputs/dsge_investment_lp_<stamp>.md)
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
import ph_data as D                     # noqa: E402
import transmission_benchmarks as TB    # noqa: E402

OUT = HERE.parents[1] / "outputs"
H = 8


def gfcf_q():
    d = pd.read_csv(D.RAW / "PSA_OpenSTAT_GDP_by_expenditure_quarterly_2000-2026.csv", comment="#")
    d = d[d["valuation"].str.contains("Constant", case=False) & (d["expenditure"].str.strip() == "Gross fixed capital formation")]
    s = pd.Series(d["value_million_php"].astype(float).values,
                  index=pd.PeriodIndex([f"{y}{q}" for y, q in zip(d["year"], d["quarter"])], freq="Q")).sort_index()
    return D._gdp_sa_stl(s)          # robust STL on logs, as for GDP (milestone 18b)


def main():
    L = TB.quarterly_levels()
    L["lgdp"] = 100 * np.log(D._gdp_sa_stl(D._gdp_q())).reindex(L.index)
    L["linv"] = 100 * np.log(gfcf_q()).reindex(L.index)
    L = L.dropna()
    shock, rf = TB.surprises(L[["lgdp", "lcpi", "i", "lfx"]])
    dL = L.diff()
    ctrl = pd.concat({f"{c}_l{k}": dL[c].shift(k) for c in dL.columns for k in range(1, 5)}, axis=1)
    res = {v: [] for v in ("i", "lcpi", "linv", "lgdp")}
    for h in range(H + 1):
        for v in res:
            y = (L[v].shift(-h) - L[v].shift(1)).rename("y")
            m = pd.concat([y, shock, ctrl], axis=1).dropna()
            r = sm.OLS(m["y"], sm.add_constant(m.drop(columns="y"))).fit(cov_type="HAC", cov_kwds={"maxlags": h + 1})
            res[v].append((float(r.params["shock"]), float(r.bse["shock"]), int(r.nobs)))
    b = {v: np.array([x[0] for x in res[v]]) for v in res}
    se = {v: np.array([x[1] for x in res[v]]) for v in res}
    s = 1.0 / b["i"][0]                                                   # +1 pp policy rate on impact
    infl_ann = 4 * np.diff(b["lcpi"], append=np.nan)                      # next quarter's annualized inflation response (pp)
    real = s * (b["i"] - infl_ann)
    rows = pd.DataFrame({"policy rate (pp)": s * b["i"], "real rate (pp)": real, "investment (%)": s * b["linv"],
                         "investment s.e.": abs(s) * se["linv"], "GDP (%)": s * b["lgdp"], "CPI (%)": s * b["lcpi"]},
                        index=pd.Index(range(H + 1), name="quarters after the surprise"))
    th = {}
    for yname, sl in (("year 1", slice(0, 4)), ("year 2", slice(4, 8))):
        inv, rr = rows["investment (%)"].iloc[sl].mean(), rows["real rate (pp)"].iloc[sl].mean()
        th[yname] = {"investment (%)": inv, "real rate (pp)": rr, "theta (% of investment per pp)": -inv / rr if abs(rr) > 1e-6 else np.nan}
    T = pd.DataFrame(th).T
    stamp = dt.datetime.now()
    lines = [f"# Investment's response to a BSP policy surprise (milestone 20; {stamp:%d %B %Y, %H:%M})", "",
             "**NOT FOR CITATION** (research code, `research/dsge/investment_lp.py`). Local projections on milestone 12's policy "
             f"surprises (2002-2019; reaction-function R-squared {rf.rsquared:.2f}); PSA real gross fixed capital formation and GDP, "
             f"seasonally adjusted by robust STL; {res['linv'][0][2]} quarters at h = 0. Scaled to +1 pp on the policy rate on impact. "
             "theta = minus the average investment response over the year divided by the average real-rate response.", "",
             "## Implied semi-elasticity theta", "", T.to_markdown(floatfmt=".3f"), "",
             "For comparison: milestone 14's implied theta 0.55; the QPM's (milestone 9) 3.0.", "",
             "## Responses", "", rows.to_markdown(floatfmt=".3f")]
    f = OUT / f"dsge_investment_lp_{stamp:%Y%m%d_%H%M}.md"
    f.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:12]))
    print(rows.round(3).to_string())
    print("saved", f)


if __name__ == "__main__":
    main()
