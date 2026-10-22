"""Inflation and the peso in 2026: how much is oil and how much is not (16 Oct 2026).

NOT FOR CITATION until reviewed. Run:  py preshock/inflation_var.py        (several minutes; 500 bootstrap draws)
Writes outputs/inflation_var_<date>.md and outputs/inflation_var_<date>_*.csv.

Why. The combined CGE run puts 2026 consumer prices only +0.8 points above the pre-shock path, while the government's own
revision implies about +3.5 (DBCC 193rd, 8 Jul 2026: 6.0-7.0% for 2026, against 2.0-4.0% at the 192nd, 9 Dec 2025).
In its short-run years the CGE holds the peso at its baseline and has no money or wage-price round. This model measures
from data how much of 2026's inflation and of the peso's fall came from oil and how much from other shocks, so that
(a) the peso's non-oil movement can enter the CGE as an exchange-rate shock without counting oil twice, and
(b) one can say how much of the price rise the CGE's shocks do not explain.

What is reused from an earlier VAR (VAR) (8 Oct 2026; infinity_gem.svar reproduces it exactly, check V6):
the design (monthly; constant and month dummies; 3 lags; a world block that Philippine variables cannot affect, i.e.
block exogeneity as in Cushman and Zha 1997; Cholesky ordering), the estimation code, its GPR series, and, in robustness
run R9, its world-trade, FDI and remittance series. The reference VAR has no prices and no BSP rate, so it cannot answer the
inflation question by itself. Added: consumer prices (PSA), the BSP policy rate and the US rate (BIS), world food prices
(World Bank).

Main model ("split"):  [oil, world food, US rate, GPR | energy prices, rice prices, other prices, BSP rate, peso]
  The CPI is split into three fixed-weight parts (PSA 2018 weights): energy = fuels for vehicles (07.2.2), electricity
  (04.5.1) and LPG (04.5.2), 8.2% of the basket; rice (01.1.1.12), 8.9%; everything else, 82.9% (the residual index).
  Why the split: in 2026 pump fuels, LPG and power rose far more than crude (fuel-product margins widened: diesel import
  cost +97% and petrol +67% against Dubai +49%, Mar-Sep vs Jan-Feb; LPG +40% in April alone), and rice moved for its own
  reasons. With headline CPI only (model M1, kept for comparison), those moves look like 'Philippine price shocks' and
  oil looks small. With the split, energy-price shocks beyond crude get their own column.
  Ordering: world block first and exogenous (a small open economy); then energy (pump and LPG prices follow world prices
  within weeks), rice, other prices, the BSP rate (it can react to prices within the month), the peso last (it reacts to
  everything within the month). Alternative orderings are in the robustness table.
  oil_g, food_g: 100 x monthly log change of Dubai crude (US$/bbl) and of the World Bank food price index (US$);
  us_d, bsp_d: monthly change in the policy rate (percentage points; end of month);
  gpr: Caldara-Iacoviello geopolitical risk index for the Philippines (level, as in the reference VAR);
  energy, rice, other (and infl = headline, core = PSA core CPI in the comparison models): 100 x monthly log change,
  not seasonally adjusted (the month dummies take the seasons, as in the reference VAR);
  dfx: 100 x monthly log change of pesos per US$ (+ = weaker peso).
  BSP rate: the June 2016 fall from 4.0% to 3.0% was the reset of the overnight RRP rate when the interest rate corridor
  started (3 June 2016; Tetangco speech of 19 May 2016, BIS central bankers' review r160519g), not a policy move: its
  monthly change is set to zero.
  Sample: January 2002 (inflation targeting began in 2002) to the last month with every series (September 2026).

Decomposition (infinity_gem.svar.decomposition_since): for each month of 2026,
  actual = what the model forecast from data up to December 2025 (the pre-shock view; the DBCC's 192nd meeting was on
           9 Dec 2025) + the effect of each structural shock that hit from January 2026 on. Exact.
  After the last data month there are no new shocks: the shocks' effects carry on (this fills October-December 2026
  for the calendar-year averages, and gives the carry-over into 2027).
  Headline inflation (year on year, PSA's definition) = the three parts' year-on-year changes weighted by their shares a
  year earlier (Laspeyres arithmetic); the small difference from PSA's published rate is shown as 'index arithmetic'.
  Logs are converted to percent by sharing the (small) difference in proportion to each part.
Bands: residual bootstrap (recursive design), re-estimating with the same lags, terms and block, 500 draws; the
  decomposition is recomputed on the actual data with each draw's coefficients.
"""
from __future__ import annotations

import datetime as dt
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from infinity_gem import svar  # noqa: E402

MAC = ROOT / "data" / "raw" / "macro"
OUT = ROOT / "outputs"
TODAY = dt.date.today().strftime("%Y%m%d")

WORLD = ["oil_g", "food_g", "us_d", "gpr"]
SPLIT = WORLD + ["energy", "rice", "other", "bsp_d", "dfx"]
HEADLINE = WORLD + ["infl", "bsp_d", "dfx"]
PARTS = {"energy": ["07.2.2", "04.5.1", "04.5.2"], "rice": ["01.1.1.12"]}       # 'other' = the rest of the basket
LEVEL = {"energy": "lenergy", "rice": "lrice", "other": "lother", "infl": "lcpi", "core": "lcore", "dfx": "lfx"}
LABEL = {"oil_g": "Oil (crude)", "food_g": "World food prices", "us_d": "US interest rate", "gpr": "Geopolitical risk",
         "energy": "Energy beyond crude", "rice": "Rice", "other": "Other Philippine prices",
         "infl": "Philippine price shocks", "core": "Philippine price shocks (core)", "bsp_d": "BSP policy rate",
         "dfx": "Peso (own shocks)", "wtv_g": "World trade", "fdi": "FDI (own shocks)", "drem": "Remittances (own shocks)"}
START, END = "2002-01", "2026-09"
P_LAGS, REPS, SEED = 3, 500, 20261016
DBCC192 = {"infl": (2.0, 4.0), "peso": (58.0, 60.0)}      # 9 Dec 2025, for 2026 (data/raw/oil/forecasts/DBCC_192nd_...pdf)
DBCC193 = {"infl": {2026: (6.0, 7.0), 2027: (4.0, 5.0)}, "peso": {2026: (60.0, 62.0), 2027: (60.0, 62.0)}}  # 8 Jul 2026


# --------------------------------------------------------------------------------------------------- data
def _psa_items(*fnames):
    """PSA CPI tables laid out with 'YYYY Mon' columns -> DataFrame (rows = item code, columns = months)."""
    out = []
    for f in fnames:
        d = pd.read_csv(MAC / f, comment="#")
        d["code"] = d["Commodity Description"].astype(str).str.split(" - ").str[0].str.strip()
        cols = [c for c in d.columns if c[:4].isdigit() and not c.endswith("Ave")]
        x = d.set_index("code")[cols].apply(pd.to_numeric, errors="coerce")
        x.columns = pd.to_datetime(cols, format="%Y %b")
        out.append(x)
    return pd.concat(out, axis=1)


def _psa_core_backcast():
    d = pd.read_csv(MAC / "PSA_OpenSTAT_0012M4ACP33_core_CPI_2018base_1994-2017_backcast.csv", comment="#")
    d = d[d["Period"].isin(pd.date_range("2000-01", periods=12, freq="MS").strftime("%B"))]
    s = d.melt(id_vars="Period", var_name="year", value_name="v")
    s.index = pd.to_datetime(s["year"] + " " + s["Period"], format="%Y %B")
    return pd.to_numeric(s["v"], errors="coerce").sort_index().dropna()


def _monthly_csv(fname, col="value", month="month"):
    d = pd.read_csv(MAC / fname, comment="#")
    return pd.Series(pd.to_numeric(d[col], errors="coerce").to_numpy(), index=pd.to_datetime(d[month])).dropna()


def cpi_weights():
    w = pd.read_csv(MAC / "PSA_OpenSTAT_0012M4ACP25_CPI_weights_2018base.csv", comment="#")
    w["code"] = w["Commodity Description"].astype(str).str.split(" - ").str[0].str.strip()
    W = w.set_index("code")["Weights"].astype(float)
    wt = {g: float(W[c].sum()) for g, c in PARTS.items()}
    wt["other"] = 100.0 - sum(wt.values())
    return wt


def load_panel() -> pd.DataFrame:
    items = _psa_items("PSA_OpenSTAT_0012M4ACP28_CPI_2018base_by_commodity_group_1994-2017_backcast.csv",
                       "PSA_OpenSTAT_0012M4ACP22_CPI_2018base_by_commodity_group_2018-latest.csv")
    W = pd.read_csv(MAC / "PSA_OpenSTAT_0012M4ACP25_CPI_weights_2018base.csv", comment="#")
    W["code"] = W["Commodity Description"].astype(str).str.split(" - ").str[0].str.strip()
    W = W.set_index("code")["Weights"].astype(float)
    wt = cpi_weights()
    cpi = items.loc["0"]
    parts = {g: items.loc[c].mul(W[c], axis=0).sum(min_count=len(c)) / wt[g] for g, c in PARTS.items()}
    parts["other"] = (100 * cpi - sum(wt[g] * parts[g] for g in PARTS)) / wt["other"]
    core = pd.concat([_psa_core_backcast(),
                      pd.Series(_psa_items("PSA_OpenSTAT_0012M4ACP30_core_CPI_2018base_by_group_2018-latest.csv").loc["0"])])
    p = pd.DataFrame({"cpi": cpi, "core_cpi": core, "energy_idx": parts["energy"], "rice_idx": parts["rice"],
                      "other_idx": parts["other"],
                      "oil": _monthly_csv("WorldBank_PinkSheet_crude_oil_monthly_1960-2026.csv", "crude_dubai_usd_bbl"),
                      "food": _monthly_csv("WorldBank_PinkSheet_price_indices_monthly_1960-latest.csv", "Food **"),
                      "us": _monthly_csv("BIS_WS_CBPOL_policy_rate_United_States_monthly.csv"),
                      "bsp": _monthly_csv("BIS_WS_CBPOL_policy_rate_Philippines_monthly.csv"),
                      "fx": _monthly_csv("BIS_WS_XRU_PHP_per_USD_monthly_average.csv"),
                      "gpr": _monthly_csv("Caldara_Iacoviello_GPR_Philippines_monthly.csv", "GPRHC_PHL")})
    p = p[~p.index.duplicated()].sort_index().asfreq("MS")
    lg = lambda s: 100 * np.log(s).diff()
    for v, s in {"infl": "cpi", "core": "core_cpi", "energy": "energy_idx", "rice": "rice_idx", "other": "other_idx",
                 "oil_g": "oil", "food_g": "food", "dfx": "fx"}.items():
        p[v] = lg(p[s])
    for v, s in {"lcpi": "cpi", "lcore": "core_cpi", "lenergy": "energy_idx", "lrice": "rice_idx", "lother": "other_idx",
                 "lfx": "fx"}.items():
        p[v] = 100 * np.log(p[s])
    p["us_d"], p["bsp_d"] = p.us.diff(), p.bsp.diff()
    p.loc["2016-06-01", "bsp_d"] = 0.0          # corridor start: RRP rate reset 4.0 -> 3.0, not a policy move
    # The reference VAR's own series (a compiled panel; used from 14 Oct) for robustness run R9
    ref = ROOT / "validation" / "var_task1" / "reference" / "Task1_LP_Global_20261008.xlsx"
    tmp = Path(tempfile.gettempdir()) / "infinity_gem_inflation_var_task1.xlsx"
    shutil.copy2(ref, tmp)
    t1 = pd.read_excel(tmp, sheet_name="Data monthly").set_index("month")
    t1.index = pd.DatetimeIndex(t1.index)
    for c in ("wtv_g", "fdi", "drem"):
        p[c] = t1[c].reindex(p.index)
    return p


def month_dummies(index) -> pd.DataFrame:
    return pd.DataFrame({f"m{k}": (index.month == k).astype(float) for k in range(2, 13)}, index=index)


# --------------------------------------------------------------------------------------------------- estimation
def fit_spec(panel, names, start=START, end=END, p=P_LAGS, world=WORLD, covid=False):
    df = panel.loc[start:end, names]
    df = df.loc[df.dropna().index.min():df.dropna().index.max()]
    if df.isna().any().any():
        raise ValueError(f"gaps in the sample: {df.columns[df.isna().any()].tolist()}")
    det = month_dummies(df.index)
    if covid:
        for mth in ("2020-03", "2020-04", "2020-05", "2020-06"):
            det[f"covid_{mth}"] = (df.index == pd.Timestamp(mth)).astype(float)
    m = svar.fit(df, p, deterministic=det, exog_block=[w for w in world if w in names], sigma_dof="ml")
    return m, det


def lag_criteria(panel, names, pmax=6):
    rows = []
    df = panel.loc[START:END, names].dropna()
    for p in range(1, pmax + 1):
        sub = df.iloc[pmax - p:]                       # same effective sample for every p
        m = svar.fit(sub, p, deterministic=month_dummies(sub.index), exog_block=WORLD, sigma_dof="ml")
        T = len(m.U)
        nparam = int(np.count_nonzero(m.A)) + m.C.size
        ld = np.log(np.linalg.det(m.Sigma))
        rows.append({"lags": p, "AIC": ld + 2 * nparam / T, "BIC": ld + np.log(T) * nparam / T,
                     "HQ": ld + 2 * np.log(np.log(T)) * nparam / T})
    return pd.DataFrame(rows).set_index("lags")


def decompose(m, det, until="2027-12", from_month="2026-01", B0=None):
    """Decomposition since `from_month` with the model's Cholesky factor (or B0); monthly frames to `until`."""
    B0 = svar.cholesky(m) if B0 is None else B0
    idx = m.index
    fut = pd.date_range(idx[-1] + pd.offsets.MonthBegin(1), until, freq="MS")
    Dfut = np.hstack([np.ones((len(fut), 1)), month_dummies(fut).to_numpy(), np.zeros((len(fut), det.shape[1] - 11))])
    start = int(np.where(idx == pd.Timestamp(from_month))[0][0])
    r = svar.decomposition_since(m, B0, start, D_after=Dfut)
    months = idx[start:].append(fut)
    return {"months": months, "forecast": pd.DataFrame(r["forecast"], index=months, columns=m.names),
            "contrib": {j: pd.DataFrame(r["contribution"][:, :, jj], index=months, columns=m.names)
                        for jj, j in enumerate(m.names)}}


def level_paths(dec, panel, var):
    """100 x log level of `var`'s index: actual (NaN after the data), the pre-shock forecast and each shock's part,
    by cumulating the monthly changes from the last pre-shock month's actual level."""
    level = LEVEL[var]
    base = panel.loc[dec["months"][0] - pd.offsets.MonthBegin(1), level]
    f = base + dec["forecast"][var].cumsum()
    c = pd.DataFrame({j: dec["contrib"][j][var].cumsum() for j in dec["contrib"]})
    a = panel[level].reindex(dec["months"])
    return a, f, c


def _pct(x):
    return 100 * (np.exp(x / 100) - 1)


def yoy_parts(dec, panel, var):
    """Year-on-year % change of var's index by month: total (actual, or model after the data), the pre-shock forecast,
    each shock's part (log parts scaled so they add up to the percent gap), and the index level for weighting."""
    a, f, c = level_paths(dec, panel, var)
    months = dec["months"]
    lev = a.fillna(f + c.sum(axis=1))
    ago = months - pd.DateOffset(years=1)
    pre = ago < months[0]                                   # year-ago month is before the shocks: actual data
    lag_tot = pd.Series(np.where(pre, panel[LEVEL[var]].reindex(ago).to_numpy(), lev.reindex(ago).to_numpy()), index=months)
    lag_fc = pd.Series(np.where(pre, panel[LEVEL[var]].reindex(ago).to_numpy(), f.reindex(ago).to_numpy()), index=months)
    lag_c = c.reindex(ago).fillna(0.0)
    lag_c.index = months
    lag_c.loc[pre] = 0.0
    tot, fc = _pct(lev - lag_tot), _pct(f - lag_fc)
    parts_log = c - lag_c
    gap_log = (lev - lag_tot) - (f - lag_fc)
    scale = (tot - fc) / gap_log.where(gap_log.abs() > 1e-9, np.nan)
    parts = parts_log.mul(scale.fillna(1.0), axis=0)
    return tot, fc, parts, np.exp(lag_tot / 100), a.notna()


def inflation_table(m, dec, panel, kind):
    """Headline year-on-year inflation by month, its pre-shock forecast and each shock's part.
    kind 'split': the three CPI parts weighted by their shares a year earlier; 'headline' or 'core': that index."""
    if kind == "split":
        wt = cpi_weights()
        tot = fc = 0.0
        parts = None
        lagidx = {}
        res = {g: yoy_parts(dec, panel, g) for g in ("energy", "rice", "other")}
        for g in res:
            lagidx[g] = wt[g] * res[g][3]
        den = sum(lagidx.values())
        for g, (t_, f_, p_, _, known) in res.items():
            s = lagidx[g] / den
            tot = tot + s * t_
            fc = fc + s * f_
            parts = p_.mul(s, axis=0) if parts is None else parts + p_.mul(s, axis=0)
        known = res["other"][4]
        # PSA's published headline for the data months (the residual is index arithmetic)
        months = dec["months"]
        pub = _pct(panel["lcpi"].reindex(months) - panel["lcpi"].reindex(months - pd.DateOffset(years=1)).to_numpy())
        resid = (pub - tot).where(known, 0.0)
        tot = tot + resid
    else:
        tot, fc, parts, _, known = yoy_parts(dec, panel, kind)
        resid = pd.Series(0.0, index=dec["months"])
    out = pd.DataFrame({"inflation (%)": tot, "pre-shock forecast (%)": fc, "data": np.where(known, "actual", "no new shocks")})
    for j in parts.columns:
        out[LABEL[j]] = parts[j]
    out["index arithmetic"] = resid
    return out


def peso_table(dec, panel):
    """Pesos per US$, its pre-shock forecast, and each shock's part in % of the forecast level."""
    a, f, c = level_paths(dec, panel, "dfx")
    lev = a.fillna(f + c.sum(axis=1))
    out = pd.DataFrame({"pesos per US$": np.exp(lev / 100), "pre-shock forecast": np.exp(f / 100),
                        "gap (% of forecast)": _pct(lev - f)})
    out["data"] = np.where(a.notna(), "actual", "no new shocks")
    gl = lev - f
    scale = (out["gap (% of forecast)"] / gl.where(gl.abs() > 1e-9, np.nan)).fillna(1.0)
    for j in c.columns:
        out[LABEL[j]] = c[j] * scale
    return out


OIL_GROUP = ("Oil (crude)", "Energy beyond crude")


def headline_stats(m, det, panel, kind="split"):
    """Numbers for the summary and the robustness table: the 2026 inflation gap over the pre-shock forecast and its
    oil part; the 2026 peso gap and its oil part. 'Jan-<last data month>' averages and the calendar year (no new
    shocks after the data), plus 2027 (carry-over only)."""
    dec = decompose(m, det)
    it, pt = inflation_table(m, dec, panel, kind), peso_table(dec, panel)
    cols = [LABEL[j] for j in m.names]
    oil = [c for c in cols if c in OIL_GROUP]
    last = int(m.index[-1].month) if m.index[-1].year == 2026 else 12
    res = {}
    for tag, yr, mon in ((f"2026 Jan-{m.index[-1]:%b}", 2026, last), ("2026", 2026, 12), ("2027", 2027, 12)):
        sel = (it.index.year == yr) & (it.index.month <= mon)
        ii, pp = it.loc[sel], pt.loc[sel]
        res[tag] = {"inflation": ii["inflation (%)"].mean(), "inflation, pre-shock forecast": ii["pre-shock forecast (%)"].mean(),
                    "inflation gap": (ii["inflation (%)"] - ii["pre-shock forecast (%)"]).mean(),
                    "of which oil and energy": ii[oil].sum(axis=1).mean(),
                    "pesos per US$": pp["pesos per US$"].mean(), "peso, pre-shock forecast": pp["pre-shock forecast"].mean(),
                    "peso gap (%)": _pct(np.log(pp["pesos per US$"] / pp["pre-shock forecast"]).mean() * 100),
                    "peso: oil and energy (%)": pp[oil].sum(axis=1).mean(),
                    "peso: not oil (%)": (pp["gap (% of forecast)"] - pp[oil].sum(axis=1)).mean()}
    return res, dec, it, pt


def irf_summary(m, B0, H=24):
    """Pass-through in the model: consumer prices and the peso after 12 and 24 months for (i) a 10% rise in crude,
    (ii) a 1% fall of the peso from its own shock. In the split model, consumer prices = the three parts at 2025 weights."""
    R = np.cumsum(svar.irf(m, B0, H), axis=0)
    io, ifx = m.names.index("oil_g"), m.names.index("dfx")
    if "energy" in m.names:
        wt = cpi_weights()
        cpi = sum(wt[g] / 100 * R[:, m.names.index(g), :] for g in ("energy", "rice", "other"))
    else:
        cpi = R[:, m.names.index([n for n in m.names if n in ("infl", "core")][0]), :]
    imp = svar.irf(m, B0, 0)[0]
    o10, f1 = 10.0 / imp[io, io], 1.0 / imp[ifx, ifx]
    return {"crude +10%: consumer prices after 12 months (%)": cpi[12, io] * o10,
            "crude +10%: consumer prices after 24 months (%)": cpi[24, io] * o10,
            "crude +10%: peso after 12 months (% weaker)": R[12, ifx, io] * o10,
            "peso 1% weaker (own shock): consumer prices after 12 months (%)": cpi[12, ifx] * f1,
            "peso 1% weaker (own shock): consumer prices after 24 months (%)": cpi[24, ifx] * f1}


# --------------------------------------------------------------------------------------------------- report
def fmt(df, nd=2):
    return df.to_markdown(floatfmt=f".{nd}f")


def main(reps=REPS):
    panel = load_panel()
    lines = []
    L = lines.append
    L(f"# Inflation and the peso in 2026: oil and the rest (structural VAR; Infinity GEM 0.3.7, {dt.date.today():%d %b %Y})")
    L("")
    L("**NOT FOR CITATION until reviewed.** Script: `preshock/inflation_var.py` (its notes give the model and the reasons); "
      "data: `data/raw/macro/` (`download_inflation_var_data.py`: PSA CPI and core CPI with weights, BIS policy rates and "
      "peso, World Bank food index; Dubai crude and the GPR file were already on file; the reference VAR's world trade, FDI and "
      "remittances for R9). Builds on an earlier VAR (VAR) (design, code and some series reused).")
    L("")

    m, det = fit_spec(panel, SPLIT)
    B0 = svar.cholesky(m)
    crit = lag_criteria(panel, SPLIT)
    res, dec, it, pt = headline_stats(m, det, panel)
    m1, d1 = fit_spec(panel, HEADLINE)
    res1, _, it1, pt1 = headline_stats(m1, d1, panel, "infl")
    pick = {c: int(crit[c].idxmin()) for c in crit.columns}
    wt = cpi_weights()

    # ---- bootstrap bands
    def stat(mb, Bb):
        r, *_ = headline_stats(svar.on_data(mb, m), det, panel)
        return r, irf_summary(mb, Bb)
    boot = svar.bootstrap_irf(m, 24, reps=reps, seed=SEED, extra=stat)
    band = []
    for tag in res:
        for k, v in res[tag].items():
            dr = np.array([e[0][tag][k] for e in boot["extra"]])
            band.append({"period": tag, "statistic": k, "estimate": v, "90% low": np.nanpercentile(dr, 5),
                         "90% high": np.nanpercentile(dr, 95)})
    band = pd.DataFrame(band)
    pt_est = irf_summary(m, B0)
    pt_band = pd.DataFrame({"estimate": pt_est,
                            "90% low": {k: np.percentile([e[1][k] for e in boot["extra"]], 5) for k in pt_est},
                            "90% high": {k: np.percentile([e[1][k] for e in boot["extra"]], 95) for k in pt_est}})

    # ---- summary
    a, b = res[f"2026 Jan-{m.index[-1]:%b}"], res["2026"]
    bb = band.set_index(["period", "statistic"])
    lo = lambda t, s: bb.loc[(t, s), "90% low"]
    hi = lambda t, s: bb.loc[(t, s), "90% high"]
    t0 = f"2026 Jan-{m.index[-1]:%b}"
    L("## Summary")
    L("")
    L(f"- **Inflation, January-{m.index[-1]:%B} 2026:** {a['inflation']:.1f}% (PSA), against the model's pre-shock forecast of "
      f"{a['inflation, pre-shock forecast']:.1f}% (DBCC 192nd: 2.0-4.0%). The gap, **{a['inflation gap']:.1f} points**, is "
      f"**{a['of which oil and energy']:.1f} points oil and energy** (crude plus energy prices beyond crude; 90% band "
      f"{lo(t0, 'of which oil and energy'):.1f} to {hi(t0, 'of which oil and energy'):.1f}) and "
      f"{a['inflation gap'] - a['of which oil and energy']:.1f} points other shocks (rice, other Philippine prices, the peso, "
      f"world food, rates, geopolitics; table 2).")
    L(f"- **Calendar 2026** (no new shocks after {m.index[-1]:%B}): inflation {b['inflation']:.1f}% against "
      f"{b['inflation, pre-shock forecast']:.1f}% pre-shock; gap {b['inflation gap']:.1f} points, of which oil and energy "
      f"{b['of which oil and energy']:.1f}. DBCC 193rd (8 Jul 2026): 6.0-7.0%.")
    L(f"- **The peso, January-{m.index[-1]:%B} 2026:** {a['pesos per US$']:.2f} per US$ on average against a pre-shock forecast of "
      f"{a['peso, pre-shock forecast']:.2f} (DBCC 192nd: 58-60): **{a['peso gap (%)']:.1f}% weaker**, of which oil and energy "
      f"{a['peso: oil and energy (%)']:.1f}% and **not oil {a['peso: not oil (%)']:.1f}%** (90% band "
      f"{lo(t0, 'peso: not oil (%)'):.1f} to {hi(t0, 'peso: not oil (%)'):.1f}).")
    L(f"- **Calendar 2026:** peso {b['pesos per US$']:.2f} against {b['peso, pre-shock forecast']:.2f}: {b['peso gap (%)']:.1f}% weaker; "
      f"not oil {b['peso: not oil (%)']:.1f}% (band {lo('2026', 'peso: not oil (%)'):.1f} to {hi('2026', 'peso: not oil (%)'):.1f}). "
      f"**2027** (carry-over only, no new shocks): not oil {res['2027']['peso: not oil (%)']:.1f}%. DBCC 193rd: 60-62 in 2026 and 2027.")
    L(f"- **Headline-only model (M1, the reference VAR's design with headline CPI):** oil and energy {res1[t0]['of which oil and energy']:.1f} points "
      f"of a {res1[t0]['inflation gap']:.1f}-point gap. It misses the fuel-product, LPG and power premia, which it books as "
      "'Philippine price shocks'; that is why the main model splits the CPI.")
    L("")

    L("## 1. Model")
    L("")
    L(f"Monthly VAR, {m.index[0]:%b %Y} to {m.index[-1]:%b %Y} ({len(m.U)} months used), {m.p} lags, constant and month dummies; "
      f"order {', '.join(SPLIT)}; the first four form a world block the Philippine variables cannot affect. Stable: {m.stable()}. "
      f"CPI parts (PSA 2018 weights): energy {wt['energy']:.2f}% (fuels for vehicles, electricity, LPG), rice {wt['rice']:.2f}%, "
      f"other {wt['other']:.2f}%.")
    L("")
    L("Lag-length criteria (lower is better; same sample for every lag length):")
    L("")
    L(fmt(crit, 3))
    L("")
    L(f"Chosen by AIC {pick['AIC']}, BIC {pick['BIC']}, HQ {pick['HQ']}. The main model keeps the reference VAR's 3 lags; R2 uses the BIC choice.")
    L("")
    sc = [LABEL[j] for j in SPLIT]
    L("## 2. Inflation, 2026: actual against the pre-shock forecast, and each shock's part (year on year, %; points)")
    L("")
    L("Pre-shock forecast = the model's forecast from data to December 2025. 'no new shocks' = after the last data month, "
      "the shocks of January on carry on and nothing new hits. The parts add up to inflation minus the forecast.")
    L("")
    show = it.loc["2026-01":"2026-12"].copy()
    show.index = show.index.strftime("%b %Y")
    L(fmt(show[["inflation (%)", "pre-shock forecast (%)", "data"] + sc + ["index arithmetic"]]))
    L("")
    L("## 3. The peso, 2026: pesos per US$ against the pre-shock forecast, and each shock's part (% of the forecast level)")
    L("")
    show = pt.loc["2026-01":"2026-12"].copy()
    show.index = show.index.strftime("%b %Y")
    L(fmt(show[["pesos per US$", "pre-shock forecast", "gap (% of forecast)", "data"] + sc]))
    L("")
    L("## 4. Headline numbers with 90% bootstrap bands")
    L("")
    L(f"Residual bootstrap, {reps} draws, seed {SEED}; each draw re-estimates the model and recomputes the decomposition "
      "on the actual data. '2026' = the calendar year with no new shocks after the last data month; '2027' = carry-over only.")
    L("")
    L(bb.to_markdown(floatfmt=".2f"))
    L("")
    L("## 5. Pass-through in the model (impulse responses, with 90% bootstrap bands)")
    L("")
    L(fmt(pt_band))
    L("")

    # ---- robustness
    specs = {
        "R1 main (split CPI)": dict(names=SPLIT),
        f"R2 BIC lags ({pick['BIC']})": dict(names=SPLIT, p=pick["BIC"]),
        "R3 the reference VAR's sample (from Feb 2014)": dict(names=SPLIT, start="2014-02"),
        "R4 COVID months as dummies (Mar-Jun 2020)": dict(names=SPLIT, covid=True),
        "R5 peso before the BSP rate": dict(names=WORLD + ["energy", "rice", "other", "dfx", "bsp_d"]),
        "R6 peso first in the Philippine block": dict(names=WORLD + ["dfx", "energy", "rice", "other", "bsp_d"]),
        "R7 rice before energy": dict(names=WORLD + ["rice", "energy", "other", "bsp_d", "dfx"]),
        "R8 the reference VAR's variables + split CPI + BSP rate (to Jun 2026)": dict(
            names=["oil_g", "us_d", "wtv_g", "gpr", "energy", "rice", "other", "bsp_d", "dfx", "fdi", "drem"],
            world=["oil_g", "us_d", "wtv_g", "gpr"]),
        "M1 headline CPI only (the reference VAR's design + CPI + BSP rate)": dict(names=HEADLINE, kind="infl"),
        "M2 core CPI only": dict(names=WORLD + ["core", "bsp_d", "dfx"], kind="core"),
    }
    rob = []
    for name, s in specs.items():
        s = dict(s)
        kind = s.pop("kind", "split")
        try:
            mm, dd = fit_spec(panel, s.pop("names"), **s)
            r, *_ = headline_stats(mm, dd, panel, kind)
            for tag, v in r.items():
                if tag == "2027":
                    continue
                rob.append({"model": name, "period": tag, **{k: v[k] for k in
                            ("inflation gap", "of which oil and energy", "peso gap (%)", "peso: not oil (%)")},
                            "months": f"{mm.index[0]:%b %Y}-{mm.index[-1]:%b %Y}", "stable": mm.stable()})
        except Exception as e:  # report, do not hide
            rob.append({"model": name, "period": "failed", "months": str(e)[:100]})
    rob = pd.DataFrame(rob)
    L("## 6. Robustness: the same numbers under other specifications")
    L("")
    L("Inflation gap = inflation minus the model's pre-shock forecast (points); peso gap = % weaker than the pre-shock "
      "forecast. M2's inflation is core inflation. R8 ends in June 2026 (FDI), so its first row covers January-June.")
    L("")
    L(rob.set_index(["model", "period"]).to_markdown(floatfmt=".2f"))
    L("")
    L("## 7. Against the government's assumptions")
    L("")
    L(f"- Pre-shock forecast for 2026 (model, data to Dec 2025): inflation {b['inflation, pre-shock forecast']:.1f}%, peso "
      f"{b['peso, pre-shock forecast']:.2f}. DBCC 192nd (9 Dec 2025): inflation 2.0-4.0%, peso 58-60.")
    L(f"- 2026 with no new shocks after {m.index[-1]:%B}: inflation {b['inflation']:.1f}%, peso {b['pesos per US$']:.2f}. "
      "DBCC 193rd (8 Jul 2026): inflation 6.0-7.0%, peso 60-62.")
    L("")
    L("## 8. What this means for the CGE")
    L("")
    L("- **Peso:** the CGE holds the peso at its baseline in short-run years. The not-oil part of the peso gap (above) is "
      "the candidate exchange-rate shock. The oil-and-energy part of the peso's fall is a channel of the oil shock that the "
      "CGE also lacks; it is small, and is reported separately so that it can be attributed to oil, not to the peso.")
    L("- **Inflation:** the oil-and-energy part is the yardstick for the CGE's oil shock. Rice and the other Philippine "
      "price shocks are not oil: part is El Nino and the rice market (which the CGE has in part), part is domestic.")
    L("")

    OUT.mkdir(exist_ok=True)
    it.to_csv(OUT / f"inflation_var_{TODAY}_inflation_by_shock.csv")
    pt.to_csv(OUT / f"inflation_var_{TODAY}_peso_by_shock.csv")
    it1.to_csv(OUT / f"inflation_var_{TODAY}_M1_headline_inflation_by_shock.csv")
    band.to_csv(OUT / f"inflation_var_{TODAY}_headline_bands.csv", index=False)
    pt_band.to_csv(OUT / f"inflation_var_{TODAY}_passthrough.csv")
    rob.to_csv(OUT / f"inflation_var_{TODAY}_robustness.csv", index=False)
    (OUT / f"inflation_var_{TODAY}.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return res


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else REPS)
