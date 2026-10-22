"""DSGE research, milestone 4b (19 Oct 2026): Philippine quarterly observables for the small open economy, from data already
on disk (no download). Sample 2002Q1-2019Q4: BSP inflation targeting from 2002, before COVID.

- output growth: real GDP (PSA OpenSTAT, quarterly, constant 2018 prices, not seasonally adjusted), 100 x log change, with the
  quarter-specific means removed (deterministic seasonality);
- CPI inflation: PSA's all-items CPI (2018 = 100; 1994-2017 backcast table 0012M4ACP28 and 2018-latest 0012M4ACP22), quarterly
  average, 100 x log change, quarter means removed;
- policy rate: BIS central bank policy rate (WS_CBPOL), quarterly average, % a quarter (annual / 4), demeaned;
- depreciation: BIS PHP per USD (WS_XRU), quarterly average, 100 x log change, demeaned.
"""
from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path(__file__).resolve().parents[2] / "data" / "raw" / "macro"     # Infinity GEM root / data / raw / macro
START, END = "2002Q1", "2019Q4"
LONG_END = "2026Q2"                  # milestone 18 (19 Oct 2026, night): the last quarter with all four series (PSA GDP to 2026Q2)
COVID = ("2020Q1", "2021Q4")         # milestone 18: quarters set to missing with covid="missing"


def _q_from_month(df, col="value"):
    s = df.set_index(pd.PeriodIndex(df["month"], freq="M"))[col].astype(float)
    return s.groupby(s.index.asfreq("Q")).mean()


def _cpi_q():
    out = []
    for f in ("PSA_OpenSTAT_0012M4ACP28_CPI_2018base_by_commodity_group_1994-2017_backcast.csv",
              "PSA_OpenSTAT_0012M4ACP22_CPI_2018base_by_commodity_group_2018-latest.csv"):
        d = pd.read_csv(RAW / f, comment="#")
        row = d[(d["Geolocation"].str.upper().str.strip() == "PHILIPPINES") & d["Commodity Description"].str.contains("ALL ITEMS")].iloc[0]
        cols = [c for c in d.columns if len(c.split()) == 2 and c.split()[1][:3] in
                ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")]
        s = pd.Series(pd.to_numeric(row[cols], errors="coerce").values,
                      index=pd.PeriodIndex([pd.Period(f"{c.split()[0]}-{c.split()[1][:3]}", freq="M") for c in cols]))
        out.append(s.dropna())
    s = pd.concat(out)
    s = s[~s.index.duplicated(keep="last")].sort_index()
    return s.groupby(s.index.asfreq("Q")).mean()


def _gdp_q():
    d = pd.read_csv(RAW / "PSA_OpenSTAT_GDP_by_expenditure_quarterly_2000-2026.csv", comment="#")
    d = d[d["valuation"].str.contains("Constant", case=False) & d["expenditure"].str.contains("Gross Domestic Product", case=False)]
    s = pd.Series(d["value_million_php"].astype(float).values,
                  index=pd.PeriodIndex([f"{y}{q}" for y, q in zip(d["year"], d["quarter"])], freq="Q"))
    return s.sort_index()


def _deseason(x):
    return x - x.groupby(x.index.quarter).transform("mean")


def _gdp_sa_stl(gdp):
    """Milestone 18b (19 Oct 2026, about 11:35 PM): log real GDP less a robust STL seasonal component (Cleveland et al. 1990;
    statsmodels STL, period 4, robust), over all quarters on file. Why: removing fixed quarter means leaves a drifting seasonal
    pattern in PSA's unadjusted GDP: on 2002-2019 the growth rate kept a lag-4 autocorrelation of 0.75 (lag 8: 0.55) and an
    s.d. of 1.63% a quarter, against 0.94% after STL; the extra variance fell on the productivity shock, whose s.d. sat at its
    upper bound (milestone 13). PSA's own seasonally adjusted GDP is not in OpenSTAT (DB/2B/NA/QT checked, 19 Oct 2026)."""
    from statsmodels.tsa.seasonal import STL
    lg = np.log(gdp.dropna())
    seas = STL(lg.to_numpy(), period=4, robust=True).fit().seasonal
    return np.exp(lg - seas)


def observables(start=START, end=END, covid=None, gdp_sa=None, adjust_end=None) -> pd.DataFrame:
    """covid='missing' (milestone 18, 19 Oct 2026, night): the quarters COVID[0]-COVID[1] become NaN after the growth rates are taken,
    so the Kalman filter skips them (estimate.kalman_loglik); seasonal and overall means come from the other quarters. A
    pandemic's lockdown quarters are not draws from the model's shock distribution; dropping them is the simplest of the
    treatments in the literature (others: rescaled shock variances, Lenza and Primiceri 2022, JAE 37(4)).
    adjust_end (21 Oct 2026, the pseudo-out-of-sample check, forecast_check.py): the quarter means and the overall means are
    taken over start..adjust_end only, so that the quarters after it are in the units of an estimation sample that ends there
    (None = the whole sample, as before; the STL seasonal adjustment of GDP still uses all quarters on file)."""
    gdp, cpi = _gdp_q(), _cpi_q()
    if gdp_sa == "stl":
        gdp = _gdp_sa_stl(gdp)
    elif gdp_sa is not None:
        raise ValueError("gdp_sa must be None or 'stl'")
    rate = _q_from_month(pd.read_csv(RAW / "BIS_WS_CBPOL_policy_rate_Philippines_monthly.csv", comment="#"))
    fx = _q_from_month(pd.read_csv(RAW / "BIS_WS_XRU_PHP_per_USD_monthly_average.csv", comment="#"))
    df = pd.DataFrame({"dy": 100 * np.log(gdp).diff(), "pi": 100 * np.log(cpi).diff(), "i": rate / 4, "de": 100 * np.log(fx).diff()})
    df = df.loc[pd.Period(start, "Q"):pd.Period(end, "Q")].dropna()
    if covid == "missing":
        df.loc[pd.Period(COVID[0], "Q"):pd.Period(COVID[1], "Q")] = np.nan
    elif covid is not None:
        raise ValueError("covid must be None or 'missing'")
    sub = df.loc[:pd.Period(adjust_end, "Q")] if adjust_end else df
    raw_means = sub.mean()
    for c in ("dy", "pi"):                       # quarter means of the adjustment sample (= _deseason when it is the whole sample)
        qm = sub[c].groupby(sub.index.quarter).mean()
        df[c] = df[c] - pd.Series(df.index.quarter, index=df.index).map(qm)
    df = df - (df.loc[:pd.Period(adjust_end, "Q")] if adjust_end else df).mean()
    df.attrs["means"] = raw_means.to_dict()
    df.attrs["adjust_end"] = adjust_end
    return df


def gfcf_q():
    """PSA real gross fixed capital formation, quarterly (constant 2018 prices; OpenSTAT 0012B5BEXQ1, the same file as GDP)."""
    d = pd.read_csv(RAW / "PSA_OpenSTAT_GDP_by_expenditure_quarterly_2000-2026.csv", comment="#")
    d = d[d["valuation"].str.contains("Constant", case=False) & (d["expenditure"].str.strip() == "Gross fixed capital formation")]
    s = pd.Series(d["value_million_php"].astype(float).values,
                  index=pd.PeriodIndex([f"{y}{q}" for y, q in zip(d["year"], d["quarter"])], freq="Q"))
    return s.sort_index()


def observables_inv(start=START, end=END, covid=None, gdp_sa=None, adjust_end=None) -> pd.DataFrame:
    """observables() plus 'dinv' (milestone 23c, 21 Oct 2026, night): 100 x the quarterly log change of PSA real gross fixed
    capital formation, seasonally adjusted by robust STL on logs (as GDP, milestone 18b; investment_lp.py uses the same
    series), quarter means and the overall mean removed over the adjustment sample, missing where the other series are (the
    COVID quarters). Its quarterly s.d. is about 4.7% against GDP's 0.9% (2002-2026 without COVID): public construction and
    lumpy projects that soe_htmk's investment does not model, so estimate_rot.py obs=inv gives it a measurement error."""
    df = observables(start, end, covid, gdp_sa, adjust_end)
    dinv = (100 * np.log(_gdp_sa_stl(gfcf_q())).diff()).reindex(df.index)
    dinv[df["dy"].isna()] = np.nan
    sub = dinv.loc[:pd.Period(adjust_end, "Q")] if adjust_end else dinv
    df.attrs["means"]["dinv"] = float(sub.mean())              # the raw mean growth, as for the other series
    qm = sub.groupby(sub.index.quarter).mean()
    dinv = dinv - pd.Series(dinv.index.quarter, index=dinv.index).map(qm)
    sub = dinv.loc[:pd.Period(adjust_end, "Q")] if adjust_end else dinv
    df["dinv"] = dinv - sub.mean()
    return df


def observables_oil(start=START, end=END, covid=None, gdp_sa=None, adjust_end=None) -> pd.DataFrame:
    """observables() plus 'doil': 100 x the quarterly log change of the Dubai crude price in US dollars (World Bank Pink Sheet,
    monthly averages; data/raw/macro/WorldBank_PinkSheet_crude_oil_monthly_1960-2026.csv), demeaned. In soe_oil.py it equals
    o - o_lag + pistar (the real oil price's change plus world inflation), so no US CPI is needed (milestone 16, 19 Oct 2026)."""
    df = observables(start, end, covid, gdp_sa, adjust_end)
    d = pd.read_csv(RAW / "WorldBank_PinkSheet_crude_oil_monthly_1960-2026.csv", comment="#")
    s = d.set_index(pd.PeriodIndex(d["month"], freq="M"))["crude_dubai_usd_bbl"].astype(float)
    q = s.groupby(s.index.asfreq("Q")).mean()
    doil = (100 * np.log(q).diff()).loc[df.index]
    doil[df["dy"].isna()] = np.nan                   # milestone 18: missing with the other series
    sub = doil.loc[:pd.Period(adjust_end, "Q")] if adjust_end else doil      # 21 Oct 2026: adjust_end as in observables()
    df.attrs["means"]["doil"] = float(sub.mean())
    df["doil"] = doil - sub.mean()
    return df


WORLD = Path(__file__).resolve().parents[2] / "data" / "raw" / "world" / "FRED_world_activity_downloaded_2026-10-20"
WORLD_GDP = ("FRED_GDPC1_US_real_GDP_quarterly_2000Q1-2026Q2.csv",
             "FRED_CLVMNACSCAB1GQEA19_euro_area_real_GDP_quarterly_2000Q1-2026Q2.csv",
             "FRED_JPNRGDPEXP_Japan_real_GDP_quarterly_2000Q1-2026Q2.csv")
# 22 Oct 2026: the same three series from the OECD's Quarterly National Accounts (tools/download_oecd_g3_gdp.py), read
# when the FRED copies are absent (FRED's terms do not allow stored FRED content to be passed on, so a public copy of
# the code carries these instead); G3 growth differs from the FRED copies' by 0.005 point on average (SOURCE_NOTE.md)
WORLD_OECD = Path(__file__).resolve().parents[2] / "data" / "raw" / "world" / "OECD_QNA_G3_real_GDP_downloaded_2026-10-22"
WORLD_GDP_OECD = ("OECD_QNA_USA_real_GDP_quarterly_2000Q1-2026Q2.csv",
                  "OECD_QNA_EA20_euro_area_real_GDP_quarterly_2000Q1-2026Q2.csv",
                  "OECD_QNA_JPN_real_GDP_quarterly_2000Q1-2026Q2.csv")


IGREA_FILE = "FRED_IGREA_Kilian_global_real_activity_monthly_2000-01_2026-08.csv"


def world_growth(source="g3") -> pd.Series:
    """Milestone 21 (20 Oct 2026): world output growth = the simple average of the quarterly log growth (x 100) of seasonally
    adjusted real GDP in the United States, the euro area (19) and Japan (FRED, 20 Oct 2026; this repository carries
    the same series from the OECD's Quarterly National Accounts instead: WORLD_OECD, read when the FRED copies are absent). Equal weights are an assumption; China, the Philippines' other large market, has no current
    quarterly real GDP series on FRED.
    source="igrea" (robustness, 20 Oct 2026): the quarterly change of Kilian's index of global real economic
    activity (IGREA, Federal Reserve Bank of Dallas via FRED; monthly, averaged by quarter; percent deviation from trend);
    observables_oilw rescales it to the standard deviation of G3 growth over the estimation quarters, so that chi_o keeps the
    same units (oil price % per 1% of world activity) and the same prior. Kilian (2009), "Not All Oil Price Shocks Are Alike", American Economic Review 99(3)."""
    if source == "igrea":
        if not (WORLD / IGREA_FILE).exists():     # public version: FRED content may not be redistributed
            raise FileNotFoundError(
                "source='igrea' needs Kilian's index of global real economic activity (IGREA), which is not distributed: "
                "download it from the Federal Reserve Bank of Dallas (Index of Global Real Economic Activity) and save it "
                f"as {WORLD / IGREA_FILE}, with the columns observation_date (monthly) and IGREA")
        d = pd.read_csv(WORLD / IGREA_FILE)
        s = pd.Series(d["IGREA"].astype(float).values, index=pd.PeriodIndex(pd.to_datetime(d["observation_date"]), freq="M"))
        return s.groupby(s.index.asfreq("Q")).mean().diff()      # index points a quarter; rescaled in observables_oilw
    if source != "g3":
        raise ValueError("source must be 'g3' or 'igrea'")
    g = []
    folder, names = (WORLD, WORLD_GDP) if (WORLD / WORLD_GDP[0]).exists() else (WORLD_OECD, WORLD_GDP_OECD)
    for f in names:
        d = pd.read_csv(folder / f)
        s = pd.Series(d.iloc[:, 1].astype(float).values, index=pd.PeriodIndex(pd.to_datetime(d["observation_date"]), freq="Q"))
        g.append(100 * np.log(s).diff())
    return pd.concat(g, axis=1).mean(axis=1)


def observables_oilw(start=START, end=END, covid=None, gdp_sa=None, world="g3", adjust_end=None) -> pd.DataFrame:
    """observables_oil() plus 'dystar': world output growth (world_growth), demeaned, missing where the other series are (the
    COVID quarters with covid='missing'). In soe_oilw.py it equals 100 (ystar - ystar_lag) (milestone 21, 20 Oct 2026)."""
    df = observables_oil(start, end, covid, gdp_sa, adjust_end)
    w = world_growth(world).reindex(df.index)
    w[df["dy"].isna()] = np.nan
    cut = (lambda x: x.loc[:pd.Period(adjust_end, "Q")]) if adjust_end else (lambda x: x)   # 21 Oct 2026: adjust_end
    if world == "igrea":                                 # the same spread as G3 growth over the quarters actually used
        g3 = world_growth("g3").reindex(df.index)
        g3[df["dy"].isna()] = np.nan
        w = w * float(cut(g3).std() / cut(w).std())
    df.attrs["means"]["dystar"] = float(cut(w).mean())
    df["dystar"] = w - cut(w).mean()
    return df


if __name__ == "__main__":
    o = observables()
    print(o.shape, o.index[0], o.index[-1]); print(o.describe().round(2).loc[["mean", "std", "min", "max"]])
    print("raw means (% a quarter):", {k: round(v, 2) for k, v in o.attrs["means"].items()})
