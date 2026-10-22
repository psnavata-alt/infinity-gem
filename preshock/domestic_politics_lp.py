"""Domestic politics: what Philippine uncertainty does to GDP, investment and the peso (16 Oct 2026).

NOT FOR CITATION until reviewed. Run:  py preshock/domestic_politics_lp.py

Shock: the World Uncertainty Index for the Philippines (WUI; Ahir, Bloom and Furceri 2022: the frequency of the word
"uncertainty" in the Economist Intelligence Unit's country reports). The index mixes domestic and world news, so every
regression holds constant, in the same period and with lags: world uncertainty (the average WUI of all other countries),
the Caldara-Iacoviello geopolitical risk index for the Philippines, world oil prices and the US policy rate. What is left
is Philippine-specific uncertainty: in 2025-26, chiefly the flood-control scandal, the protests and the impeachment cases.

Method: Jorda (2005) local projections (infinity_gem.svar.local_projection, check LP1). For h = 0..8 quarters,
  y[t+h] - y[t-1] = b_h WUI[t] + lags(2) of y, WUI and the world controls + same-period world controls + quarter dummies
                    + a COVID dummy (2020 Q2-Q3) + election-cycle dummies + e,   Newey-West standard errors with h + 1 lags.
  Election-cycle dummies (the quarter before, of and after each national election in May: 2001, 2004, ... 2025): elections raise
  the WUI (mean 0.27 in election Q1-Q2 against 0.17 otherwise) and also bring pre-election construction booms, so without them
  the WUI picks up the boom (version 1 of 16 Oct, kept as outputs/domestic_politics_lp_20261016_v1_without_election_controls.md).
  Responses (PSA, constant 2018 prices, 100 x log, not seasonally adjusted): GDP, household consumption, gross fixed capital
  formation, private construction (corporations + households, PSA table 0542B5BCNQ1), and the peso per US$ (BIS, quarterly
  average). Monthly version for the peso (WUI monthly, 2008 on; month dummies; 12 months).
  Effects are per one standard deviation of the WUI (2000-2025).
What 2025-26 cost: the WUI's surprises (residuals of the WUI on its own lags and the world controls) from 2025 Q1 on, times
  the response at each horizon, summed: an approximate effect of the 2025-26 Philippine uncertainty on the level of each
  variable in each quarter (no new surprises after the last data quarter). Indicative: the bands are those of the responses.
Comparison: BSP Discussion Paper 2025-19 (Canare, Maliwat and Nebres; reported by BusinessWorld, 22 Mar 2026): political
  instability (protests, impeachment) raises stock-market volatility but has no significant effect on the level of returns.

Data: data/raw/macro/ (WUI quarterly and monthly, GPR, BIS rates and peso, World Bank crude) and PSA OpenSTAT national
accounts on file. The latest WUI values can be zero when a report is short (2026 Q3; Aug-Sep 2026): those are dropped.
"""
import datetime as dt
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from infinity_gem.svar import local_projection  # noqa: E402

MAC = ROOT / "data" / "raw" / "macro"
H_Q, H_M = 8, 12


def _xl(name, sheet):
    if not (MAC / name).exists():               # public version: the WUI may not be redistributed
        raise SystemExit(f"{name} is not in data/raw/macro/: the World Uncertainty Index (Ahir, Bloom and Furceri) may "
                         "not be redistributed. Download the monthly and quarterly WUI workbooks from "
                         "https://worlduncertaintyindex.com/data/ and save them under these names (data/raw/macro/README.md).")
    tmp = Path(tempfile.gettempdir()) / f"infinity_gem_{name}"
    shutil.copy2(MAC / name, tmp)
    return pd.read_excel(tmp, sheet_name=sheet)


def _monthly(fname, col="value"):
    d = pd.read_csv(MAC / fname, comment="#")
    return pd.Series(pd.to_numeric(d[col], errors="coerce").to_numpy(), index=pd.PeriodIndex(d["month"], freq="M")).dropna()


def world_monthly():
    oil = pd.read_csv(MAC / "WorldBank_PinkSheet_crude_oil_monthly_1960-2026.csv", comment="#")
    oil = pd.Series(oil["crude_dubai_usd_bbl"].to_numpy(), index=pd.PeriodIndex(oil["month"], freq="M"))
    return pd.DataFrame({"oil": oil, "us": _monthly("BIS_WS_CBPOL_policy_rate_United_States_monthly.csv"),
                         "fx": _monthly("BIS_WS_XRU_PHP_per_USD_monthly_average.csv"),
                         "gpr": _monthly("Caldara_Iacoviello_GPR_Philippines_monthly.csv", "GPRHC_PHL")})


def quarterly_panel():
    w = _xl("WUI_Ahir_Bloom_Furceri_quarterly_2026-10_downloaded_2026-10-15.xlsx", "T2")
    w.index = pd.PeriodIndex(w["year"].astype(str).str.upper().str.replace("Q", "Q"), freq="Q")
    others = w.drop(columns=["year", "PHL"]).apply(pd.to_numeric, errors="coerce")
    q = pd.DataFrame({"wui": pd.to_numeric(w["PHL"], errors="coerce"), "wui_world": others.mean(axis=1)})
    q.loc[q.index >= pd.Period("2026Q3", "Q"), "wui"] = np.nan          # short report: count 0 (see WUI_SOURCE_NOTE.md)
    m = world_monthly()
    mq = m.groupby(m.index.asfreq("Q")).mean()
    q = q.join(mq, how="left")
    na = pd.read_csv(MAC / "PSA_OpenSTAT_GDP_by_expenditure_quarterly_2000-2026.csv", comment="#")
    na = na[na.valuation == "At Constant 2018 Prices"]
    na.index = pd.PeriodIndex(na["year"].astype(str) + na["quarter"], freq="Q")
    for e, k in {"Gross Domestic Product": "gdp", "Household final consumption expenditure": "cons",
                 "Gross fixed capital formation": "gfcf"}.items():
        q[k] = na.loc[na.expenditure == e, "value_million_php"].astype(float)
    c = pd.read_csv(MAC / "PSA_OpenSTAT_0542B5BCNQ1_construction_GFCF_by_sector_quarterly_2000-2026.csv", comment="#")
    c = c.set_index("Institutional Sector")
    cols = [x for x in c.columns if x.startswith("At Constant 2018 Prices")]
    priv = c.loc[["..Financial and non-financial corporations", "..Households and NPISHs"], cols].apply(pd.to_numeric, errors="coerce").sum(min_count=2)
    priv.index = pd.PeriodIndex([x.replace("At Constant 2018 Prices ", "").replace(" ", "") for x in cols], freq="Q")
    q["privcons"] = priv
    return q.loc["2000Q1":]


def run_lp(y, shock, ctrl, extra, H):
    """Local projection with the world controls as lags (controls) and same-period terms (extra)."""
    return local_projection(y, shock, controls=ctrl, H=H, lags=2, cumulative=True, extra=extra)


def main():
    q = quarterly_panel()
    q["loil"], q["lfx"] = 100 * np.log(q.oil), 100 * np.log(q.fx)
    for k in ("gdp", "cons", "gfcf", "privcons"):
        q["l" + k] = 100 * np.log(q[k])
    idx = q.index
    qd = pd.get_dummies(pd.Series(idx.quarter, index=idx), prefix="q", drop_first=True, dtype=float)
    covid = pd.Series(((idx >= pd.Period("2020Q2", "Q")) & (idx <= pd.Period("2020Q3", "Q"))).astype(float), index=idx, name="covid")
    ey = (2001, 2004, 2007, 2010, 2013, 2016, 2019, 2022, 2025)            # national elections, May
    elec = pd.DataFrame({f"elec_q{k}": [float(p.year in ey and p.quarter == k) for p in idx] for k in (1, 2, 3)}, index=idx)
    world = q[["wui_world", "gpr", "loil", "us"]]
    extra = pd.concat([world.add_suffix("_0"), qd, covid, elec], axis=1)
    sd = float(q.loc["2000Q1":"2025Q4", "wui"].std())
    resp = {"GDP": "lgdp", "Household consumption": "lcons", "Fixed investment (GFCF)": "lgfcf",
            "Private construction": "lprivcons", "Peso per US$ (+ = weaker)": "lfx"}
    tabs = {}
    for name, v in resp.items():
        lp = run_lp(q[v], q["wui"], world, extra, H_Q)
        tabs[name] = (lp[["beta", "low90", "high90"]] * sd).assign(n=lp["n"])
    # robustness: no COVID dummy; sample from 2010
    rob = {}
    for tag, (ex, sub) in {"no election dummies (version 1)": (pd.concat([world.add_suffix("_0"), qd, covid], axis=1), slice(None)),
                           "no COVID dummy": (pd.concat([world.add_suffix("_0"), qd, elec], axis=1), slice(None)),
                           "from 2010": (extra, slice("2010Q1", None))}.items():
        for name in ("GDP", "Private construction"):
            v = resp[name]
            lp = run_lp(q[v].loc[sub], q["wui"].loc[sub], world.loc[sub], ex.loc[sub], H_Q)
            rob[(tag, name)] = (lp[["beta", "low90", "high90"]] * sd)

    # WUI surprises: residual of WUI on two lags of itself and of the world controls, plus same-period world controls
    import statsmodels.api as sm
    X = pd.concat([q["wui"].shift(1).rename("w1"), q["wui"].shift(2).rename("w2"), world.add_suffix("_0"),
                   world.shift(1).add_suffix("_1"), world.shift(2).add_suffix("_2"), qd, covid, elec], axis=1)
    z = pd.concat([q["wui"].rename("y"), X], axis=1).dropna()
    r = sm.OLS(z["y"], sm.add_constant(z.drop(columns="y"))).fit()
    surprise = (z["y"] - r.fittedvalues).rename("surprise")
    s25 = surprise.loc["2025Q1":]
    horizon_q = pd.period_range("2025Q1", "2026Q4", freq="Q")
    contrib = {}
    for name, t in tabs.items():
        b = t["beta"] / sd
        lo, hi = t["low90"] / sd, t["high90"] / sd
        row = {}
        for tq in horizon_q:
            parts = [(int((tq - s).n), e) for s, e in s25.items() if 0 <= (tq - s).n <= H_Q]
            row[str(tq)] = (sum(b.loc[h] * e for h, e in parts), sum(min(lo.loc[h] * e, hi.loc[h] * e) for h, e in parts),
                            sum(max(lo.loc[h] * e, hi.loc[h] * e) for h, e in parts))
        contrib[name] = row

    # monthly peso
    wm = _xl("WUI_Ahir_Bloom_Furceri_monthly_2026-09_downloaded_2026-10-15.xlsx", "T1")
    wm.index = pd.PeriodIndex(pd.to_datetime(wm["date"]), freq="M")
    m = world_monthly()
    m["wui"] = pd.to_numeric(wm["PHL"], errors="coerce")
    m.loc[m.index >= pd.Period("2026-08", "M"), "wui"] = np.nan        # zero counts from short reports
    m["wui_world"] = wm.drop(columns=["date", "PHL"]).apply(pd.to_numeric, errors="coerce").mean(axis=1)
    m = m.loc["2008-01":]
    m["loil"], m["lfx"] = 100 * np.log(m.oil), 100 * np.log(m.fx)
    mw = m[["wui_world", "gpr", "loil", "us"]]
    md = pd.get_dummies(pd.Series(m.index.month, index=m.index), prefix="m", drop_first=True, dtype=float)
    sdm = float(m.loc[:"2025-12", "wui"].std())
    lpm = local_projection(m["lfx"], m["wui"], controls=mw, H=H_M, lags=3, cumulative=True,
                           extra=pd.concat([mw.add_suffix("_0"), md], axis=1))
    peso_m = lpm[["beta", "low90", "high90"]] * sdm

    # ---- report
    stamp = dt.date.today().strftime("%Y%m%d")
    L = [f"# Domestic politics: Philippine uncertainty and GDP, investment and the peso (local projections; {dt.date.today():%d %b %Y})", "",
         "**NOT FOR CITATION until reviewed** (Infinity GEM 0.3.7). Script: `preshock/domestic_politics_lp.py` "
         "(its notes give the method). Shock: the World Uncertainty Index for the Philippines, holding world uncertainty, "
         "geopolitical risk, oil, US rates and the election cycle constant. Effects of a one-standard-deviation rise "
         f"(quarterly s.d. {sd:.3f}; monthly s.d. {sdm:.3f}), cumulated from the quarter before, % (100 x log); 90% bands (Newey-West).", "",
         f"Quarterly sample: {q['wui'].dropna().index.min()}-{q['lgdp'].dropna().index.max()}; WUI values in 2025-26: "
         + ", ".join(f"{p} {v:.2f}" for p, v in q.loc["2025Q1":"2026Q2", "wui"].items())
         + f" (2000-2025 mean {q.loc['2000Q1':'2025Q4','wui'].mean():.2f}).", ""]
    L += ["## 1. Responses to a one-standard-deviation rise in Philippine uncertainty (quarters after)", ""]
    for name, t in tabs.items():
        tt = t.loc[[0, 1, 2, 4, 6, 8]].reset_index().rename(columns={"h": "quarters after", "beta": "effect (%)", "low90": "90% low", "high90": "90% high"})
        L += [f"**{name}**", "", tt.to_markdown(index=False, floatfmt=".2f"), ""]
    L += ["## 2. Robustness (effect on the level, % per one s.d.)", ""]
    rr = pd.DataFrame({f"{a} / {b}": v["beta"] for (a, b), v in rob.items()}).loc[[0, 2, 4, 8]]
    L += [rr.to_markdown(floatfmt=".2f"), ""]
    L += ["## 3. Monthly: the peso (per one s.d. of the monthly WUI, 2008 on)", "",
          peso_m.loc[[0, 1, 3, 6, 9, 12]].reset_index().rename(columns={"h": "months after", "beta": "effect (%)", "low90": "90% low", "high90": "90% high"}).to_markdown(index=False, floatfmt=".2f"), ""]
    L += ["## 4. What the 2025-26 Philippine uncertainty cost (approximate; level effect, %)", "",
          "WUI surprises (index points; residual on its own lags and the world controls): "
          + ", ".join(f"{p} {v:+.2f}" for p, v in s25.items()) + ". Each cell: point estimate [range from the 90% bands of the responses]. "
          "No new surprises after the last data quarter.", ""]
    ct = pd.DataFrame({name: {k: f"{v[0]:+.2f} [{v[1]:+.2f}, {v[2]:+.2f}]" for k, v in row.items()} for name, row in contrib.items()})
    L += [ct.to_markdown(), ""]
    g26 = np.mean([contrib["GDP"][f"2026Q{i}"][0] for i in range(1, 5)])
    g25 = np.mean([contrib["GDP"][f"2025Q{i}"][0] for i in range(1, 5)])
    L += [f"**GDP, annual average level effect:** 2025 {g25:+.2f}%, 2026 {g26:+.2f}% (point estimates).", "",
          "## 5. Reading", "",
          "- **No evidence that Philippine uncertainty lowers GDP or investment** in these data: the responses are near zero or positive "
          "and mostly not significant. **It does weaken the peso** (about 1.3% a year after a one-s.d. rise, significant), quarterly and monthly.",
          "- Compare with BSP DP 2025-19: political instability raises stock-market volatility but not the level of returns. Same pattern: "
          "financial prices move, measured activity does not.",
          "- Caution: the WUI is a coarse, report-based index; a negative effect on investment could be hidden by events that raise both "
          "uncertainty and spending. The finding is 'not detected', not 'proven zero'.",
          "- These effects are separate from the four CGE shocks only if Philippine uncertainty is not itself caused by them; the "
          "public-works collapse and the uncertainty share a cause (the flood-control scandal), so adding both to the CGE could count "
          "part of the same event twice. Into the CGE (if at all): as a private-investment shock in 2025-26.", ""]
    out = ROOT / "outputs" / f"domestic_politics_lp_{stamp}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    pd.concat({k: v for k, v in tabs.items()}, axis=1).to_csv(ROOT / "outputs" / f"domestic_politics_lp_{stamp}_responses.csv")
    print("\n".join(L))
    print("saved", out)


if __name__ == "__main__":
    main()
