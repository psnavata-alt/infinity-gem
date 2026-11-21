"""DSGE research, milestone 29 (12 Nov 2026, morning; under of about 5:50 AM): an EMPIRICAL benchmark
for the sign question of milestones 26-28. Do Philippine real GDP, exports, prices and the peso rise or fall after an oil SUPPLY
shock? Research only; NOT FOR CITATION.

Why: soe_htmkwo (milestone 26) says an oil supply shock raises year-1 output (+0.39% for a 36% shock), through exports; dollar
pricing of exports (soe_htmkwod, milestone 28) turns it negative. Which is right is a question for the data, not for priors.
Shock: Känzig's (2021) oil supply news shock, identified from OPEC announcements with a high-frequency external instrument
(data/raw/oil/Kanzig_oil_supply_news_downloaded_2026-11-12/oilSupplyNewsShocks_2025M12.xlsx, sheet "Monthly", CC BY 4.0;
SHA-256 8aa80042...353de), summed to quarters. It is a WORLD supply shock, exogenous to the Philippines.
Method: local projections (Jorda 2005), quarterly,
    x_{t+h} - x_{t-1} = a_h + b_h shock_t + sum_{j=1..4} (c_j shock_{t-j} + d_j' dX_{t-j}) + e_{t+h},   h = 0..12,
with dX = the growth of x itself, of real GDP and of the Dubai price (at most 13 controls on about 70 quarters),
X = 100 x log levels of: real GDP (PSA, constant 2018 prices, robust STL seasonal adjustment as ph_data), real exports of goods
and services (same, STL), CPI (PSA, STL), Dubai crude in US dollars (World Bank Pink Sheet), PHP per USD (BIS); and the BIS
policy rate (% a year, in levels). Newey-West standard errors with h + 1 lags. Every response is SCALED to a 10% impact rise in
the Dubai price (the ratio b_h(x) / b_0(Dubai) x 10, i.e. an IV local projection with the shock as the instrument for the oil
price; Stock and Watson 2018), so that it compares with the DSGE's year-1 averages per 10% (the DSGE's 36% shock x 10/36).
Samples: 2002Q1-2019Q4 (inflation targeting, before COVID; Känzig's own pre-COVID shock sheet is used here) and 2002Q1-2025Q4
with the COVID quarters 2020Q1-2021Q4 dropped from the left-hand side (the full-sample sheet).
Känzig, D. R. (2021). "The Macroeconomic Effects of Oil Supply News: Evidence from OPEC Announcements." American Economic Review
111(4): 1092-1125. Jorda, O. (2005). American Economic Review 95(1): 161-182. Stock, J. H., and M. W. Watson (2018). Economic
Journal 128(610): 917-948.
Run (research/dsge):  py -I -X utf8 oil_supply_lp.py   (writes outputs/dsge_oil_supply_lp_<stamp>.md)
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
import ph_data  # noqa: E402

ROOT = HERE.parents[1]
OUT = ROOT / "outputs"
KFILE = ROOT / "data" / "raw" / "oil" / "Kanzig_oil_supply_news_downloaded_2026-11-12" / "oilSupplyNewsShocks_2025M12.xlsx"
H = 12
LAGS = 4


def shock_q(sheet: str) -> pd.Series:
    d = pd.read_excel(KFILE, sheet_name=sheet)
    s = pd.Series(d["Oil supply news shock"].astype(float).values,
                  index=pd.PeriodIndex([pd.Period(f"{m[:4]}-{m[5:]}", freq="M") for m in d["Date"]]))
    return s.groupby(s.index.asfreq("Q")).sum()


def _psa(expenditure: str) -> pd.Series:
    d = pd.read_csv(ph_data.RAW / "PSA_OpenSTAT_GDP_by_expenditure_quarterly_2000-2026.csv", comment="#")
    d = d[d["valuation"].str.contains("Constant", case=False) & (d["expenditure"].str.strip() == expenditure)]
    s = pd.Series(d["value_million_php"].astype(float).values,
                  index=pd.PeriodIndex([f"{y}{q}" for y, q in zip(d["year"], d["quarter"])], freq="Q"))
    return s.sort_index()


def data() -> pd.DataFrame:
    gdp = ph_data._gdp_sa_stl(ph_data._gdp_q())
    exp_ = ph_data._gdp_sa_stl(_psa("Exports of goods and services"))
    cpi = ph_data._gdp_sa_stl(ph_data._cpi_q().dropna())                 # the same robust STL on log CPI
    rate = ph_data._q_from_month(pd.read_csv(ph_data.RAW / "BIS_WS_CBPOL_policy_rate_Philippines_monthly.csv", comment="#"))
    fx = ph_data._q_from_month(pd.read_csv(ph_data.RAW / "BIS_WS_XRU_PHP_per_USD_monthly_average.csv", comment="#"))
    w = pd.read_csv(ph_data.RAW / "WorldBank_PinkSheet_crude_oil_monthly_1960-2026.csv", comment="#")
    o = w.set_index(pd.PeriodIndex(w["month"], freq="M"))["crude_dubai_usd_bbl"].astype(float)
    oil = o.groupby(o.index.asfreq("Q")).mean()
    return pd.DataFrame({"real GDP": 100 * np.log(gdp), "real exports": 100 * np.log(exp_), "CPI": 100 * np.log(cpi),
                         "Dubai crude (USD)": 100 * np.log(oil), "PHP per USD": 100 * np.log(fx), "policy rate": rate})


def lp(df: pd.DataFrame, shock: pd.Series, var: str, start: str, end: str, drop=None):
    """b_h and its Newey-West s.e., h = 0..H, for the cumulative change of `var` from t-1 to t+h."""
    x = df[var]
    dX = df[list(dict.fromkeys([var, "real GDP", "Dubai crude (USD)"]))].diff()   # controls: own, GDP and oil growth
    out = []
    for h in range(H + 1):
        lhs = x.shift(-h) - x.shift(1)
        R = pd.DataFrame({"lhs": lhs, "shock": shock.reindex(df.index)})
        for j in range(1, LAGS + 1):
            R[f"shock_l{j}"] = shock.reindex(df.index).shift(j)
            for c in dX.columns:
                R[f"d{c}_l{j}"] = dX[c].shift(j)
        R = R.loc[pd.Period(start, "Q"):pd.Period(end, "Q")]
        if drop is not None:                                  # drop the observations whose t..t+h window touches COVID
            t = R.index
            bad = np.array([(p <= pd.Period(drop[1], "Q")) and (p + h >= pd.Period(drop[0], "Q")) for p in t])
            R = R[~bad]
        R = R.dropna()
        m = sm.OLS(R["lhs"], sm.add_constant(R.drop(columns="lhs"))).fit(cov_type="HAC", cov_kwds={"maxlags": h + 1})
        out.append((m.params["shock"], m.bse["shock"], int(m.nobs)))
    return np.array(out)


def main():
    df = data()
    specs = {"2002Q1-2019Q4 (pre-COVID shock series)": (shock_q("Monthly (pre-Covid)"), "2002Q1", "2019Q4", None),
             "2002Q1-2025Q4, COVID windows dropped": (shock_q("Monthly"), "2002Q1", "2025Q4", ph_data.COVID)}
    stamp = dt.datetime.now()
    L = [f"# Philippine responses to an oil SUPPLY shock: local projections on Känzig's (2021) oil supply news shock "
         f"({stamp:%d %B %Y, %H:%M})", "",
         "**NOT FOR CITATION** (research code, `research/dsge/oil_supply_lp.py`, milestone 29). Every response is per 10% impact "
         "rise in Dubai crude (b_h(x) / b_0(Dubai) x 10); in brackets the plain 90% band of b_h(x) scaled the same way (the "
         "scaling factor's own uncertainty is not included, so the bands are narrower than an IV band). Year 1 = average of h 0-3.",
         ""]
    summary = {}
    for lab, (shk, a, b, drop) in specs.items():
        res = {v: lp(df, shk, v, a, b, drop) for v in df.columns}
        b0 = res["Dubai crude (USD)"][0, 0]
        sc = 10.0 / b0
        F = pd.DataFrame({"first-stage: impact on Dubai per unit shock (%)": [b0],
                          "its t-stat": [b0 / res["Dubai crude (USD)"][0, 1]], "obs (h=0)": [res["Dubai crude (USD)"][0, 2]]})
        rows = {}
        for v, r in res.items():
            rows[v] = [f"{sc * r[h, 0]:+.2f} [{sc * (r[h, 0] - 1.645 * r[h, 1]):+.2f}, {sc * (r[h, 0] + 1.645 * r[h, 1]):+.2f}]"
                       for h in (0, 2, 4, 8, 12)]
            summary[(lab, v)] = (sc * r[:4, 0].mean(), sc * r[4:8, 0].mean())
        T = pd.DataFrame(rows, index=["h0", "h2", "h4", "h8", "h12"]).T
        L += [f"## {lab}", "", F.to_markdown(index=False, floatfmt=".3f"), "",
              "Cumulative response (% or pp), per 10% impact oil price rise:", "", T.to_markdown(), ""]
    S = pd.DataFrame({k: {"year 1 (avg h0-3)": v[0], "year 2 (avg h4-7)": v[1]} for k, v in summary.items()}).T
    L += ["## Year averages (per 10% impact oil price rise)", "", S.to_markdown(floatfmt="+.3f"), "",
          "DSGE comparison (36% shock, year-1 output under the estimated rule, x 10/36): soe_htmkwo (milestone 26) +0.39% -> "
          "+0.11 per 10%; soe_htmkwod at milestone 26's parameters with theta_X 0.75 (milestone 28 profile, not estimated) "
          "-0.43% -> -0.12 per 10%."]
    path = OUT / f"dsge_oil_supply_lp_{stamp:%Y%m%d_%H%M}.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print("saved", path)


if __name__ == "__main__":
    main()
