"""Okun's law on hours and on the informal margin (0.3.9, 18 Oct 2026).

Why: the wage curve's target, e = 0.713 (preshock/okun.py), is the elasticity of employed PERSONS per person aged 15+
to real GDP, and it rests on the 2020-2021 quarters (0.154 without them, not significant; no relation in 2006-2019).
The model's labour input is persons x hours, so the closer data counterpart is total HOURS per person aged 15+
(employment-to-population ratio x mean weekly hours). Two other margins are tested, because the Philippine literature
says demand shocks show up there rather than in open unemployment (Felipe and Estrada 2018, ADB EWP 542, Tables 1-4):
  - the visible underemployment rate (employed who worked under 40 hours and want more, % of employed);
  - the informal share (self-employed without paid employees + unpaid family workers, % of employed).

Data (PSA OpenSTAT, on file; download script data/raw/lfs/download_lfs_hours_data.py):
  LFS 0021B3FKEI2 (rates), 0191B3FHRS1 (mean hours worked in a week), 0011B3FKEI1 (levels), 0171B3FVIS1 (visibly
  underemployed), 0131B3FEMP5 (class of worker); GDP at constant 2018 prices, quarterly (0012B5BEXQ1).
  Survey rounds January, April, July and October (= quarters 1-4), as in okun.py.
Model: year-on-year change in the margin = a + b x year-on-year change in ln(real GDP) + u; Newey-West s.e., 4 lags.
  Elasticities for persons, hours per person and mean hours (log changes x 100); semi-elasticities (pp per 1% of GDP)
  for the two rates. Samples as okun.py: 2006-2019, 2006-2026 without 2020-2021, all quarters.
NOT FOR CITATION until reviewed. Run:  py preshock/okun_hours.py
"""
import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from infinity_gem import paths                                             # noqa: E402
from preshock import okun                                              # noqa: E402

L = paths.DATA_RAW / "lfs"
HOURS = L / "PSA_OpenSTAT_0191B3FHRS1_LFS_mean_hours_worked_2005-2026.csv"
LEVELS = L / "PSA_OpenSTAT_0011B3FKEI1_LFS_key_employment_levels_2005-2026.csv"
VIS = L / "PSA_OpenSTAT_0171B3FVIS1_LFS_visibly_underemployed_2005-2026.csv"
COW = L / "PSA_OpenSTAT_0131B3FEMP5_LFS_employed_by_class_of_worker_2005-2026.csv"


def rounds(path) -> pd.DataFrame:
    t = pd.read_csv(path, comment="#")
    t = t[t.Month.isin(okun.ROUND)].replace(".", np.nan)
    t["q"] = t.Month.map(okun.ROUND)
    t = t.set_index(["Year", "q"]).drop(columns="Month")
    t = t.apply(pd.to_numeric, errors="coerce")
    t.index = pd.PeriodIndex([pd.Period(f"{y}Q{q}", freq="Q") for y, q in t.index])
    return t.sort_index()


def total_col(t: pd.DataFrame) -> pd.Series:
    """The all-persons column of a by-sex-and-age table: 'Both sexes' and all ages, whatever PSA calls it."""
    cols = [c for c in t.columns if "both" in c.lower() and ("total" in c.lower() or "all" in c.lower())]
    if not cols:
        cols = [c for c in t.columns if "both" in c.lower()]
    return t[cols[0]]


def levels_epop_gdp() -> pd.DataFrame:
    """Employment-to-population ratio and real GDP in levels, built as okun.data() builds them (before its differencing)."""
    r = rounds(okun.LFS)
    epop = r["Labor Force Participation Rate Both sexes"] * r["Employment Rate Both sexes"] / 100
    g = pd.read_csv(okun.GDP, comment="#")
    g = g[(g.expenditure == "Gross Domestic Product") & g.valuation.str.contains("Constant")]
    gdp = pd.Series(g["value_million_php"].astype(float).values,
                    index=pd.PeriodIndex([pd.Period(f"{y}Q{q[1]}", freq="Q") for y, q in zip(g.year, g.quarter)]))
    return pd.DataFrame({"epop": epop, "gdp": gdp})


def data() -> pd.DataFrame:
    d = levels_epop_gdp()
    d = d.reindex(pd.period_range(d.index.min(), d.index.max(), freq="Q"))   # full quarterly range: diff(4) = year on year
    h = rounds(HOURS)["Mean Hours"]
    lev = rounds(LEVELS)
    emp = lev["Employed Persons Both sexes"]
    vis = total_col(rounds(VIS))
    cow = rounds(COW)
    informal = (cow["Self-employed without any paid employee"]
                + cow["Worked without pay in own family-operated farm or business (Unpaid family worker)"])
    d = d.join(pd.DataFrame({"hours": h, "emp": emp, "vis": vis, "informal": informal, "cow_total": cow["Total"]}), how="left")
    d["hours_pp"] = d.epop * d.hours                       # weekly hours per 100 people aged 15+
    d["vis_rate"] = 100 * d.vis / d.emp                    # % of employed
    d["inf_share"] = 100 * d.informal / d.cow_total        # % of employed
    out = pd.DataFrame(index=d.index)
    out["d_gdp"] = np.log(d.gdp).diff(4) * 100
    out["persons (employment-to-population)"] = np.log(d.epop).diff(4) * 100
    out["total hours per person 15+"] = np.log(d.hours_pp).diff(4) * 100
    out["mean hours of the employed"] = np.log(d.hours).diff(4) * 100
    out["visible underemployment rate (pp)"] = d.vis_rate.diff(4)
    out["informal share of employment (pp)"] = d.inf_share.diff(4)
    return out, d


def fit(y, x):
    import statsmodels.api as sm
    m = pd.concat([y, x], axis=1).dropna()
    if len(m) < 12:
        return {"b": np.nan, "s.e.": np.nan, "t": np.nan, "R2": np.nan, "quarters": len(m)}
    r = sm.OLS(m.iloc[:, 0], sm.add_constant(m.iloc[:, 1])).fit(cov_type="HAC", cov_kwds={"maxlags": 4})
    return {"b": r.params.iloc[1], "s.e.": r.bse.iloc[1], "t": r.tvalues.iloc[1], "R2": r.rsquared, "quarters": int(r.nobs)}


def estimates() -> pd.DataFrame:
    out, _ = data()
    out = out[out.index >= pd.Period("2006Q1", freq="Q")]
    yr = out.index.year
    samples = {"2006-2019": out[yr <= 2019],
               "2006-2026 without 2020-2021": out[(yr <= 2019) | (yr >= 2022)],
               "2006-2024 without 2020-2021": out[(yr <= 2019) | ((yr >= 2022) & (yr <= 2024))],
               "2006-2026, all quarters": out}
    rows = []
    for margin in [c for c in out.columns if c != "d_gdp"]:
        for s, df in samples.items():
            rows.append({"margin": margin, "sample": s, **fit(df[margin], df["d_gdp"])})
    return pd.DataFrame(rows)


def main():
    est = estimates()
    _, levels = data()
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    out = paths.ROOT / "outputs" / f"okun_hours_{stamp}.md"
    fmt = est.copy()
    for c in ["b", "s.e.", "t", "R2"]:
        fmt[c] = fmt[c].map(lambda v: f"{v:.3f}")
    recent = levels.loc[levels.index >= pd.Period("2023Q1", freq="Q"), ["epop", "hours", "vis_rate", "inf_share"]].round(2)
    lines = [f"# Okun's law on hours and the informal margin ({dt.date.today():%d %B %Y})", "",
             "**NOT FOR CITATION** (Infinity GEM 0.3.9). Script: `preshock/okun_hours.py`. Year-on-year changes, LFS rounds "
             "January/April/July/October; GDP at constant 2018 prices; Newey-West s.e., 4 lags. b is an elasticity for the "
             "three log margins and percentage points per 1% of GDP for the two rates.", "",
             fmt.to_markdown(index=False), "",
             "Levels in recent rounds (employment-to-population %, mean weekly hours, visible underemployment % of employed, "
             "informal % of employed):", "", recent.to_markdown(), ""]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(fmt.to_string(index=False))
    print("\nrecent levels:\n", recent.tail(8).to_string())
    print("\nwritten:", out)


if __name__ == "__main__":
    main()
