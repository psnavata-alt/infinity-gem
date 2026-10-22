"""El Nino and Philippine palay and corn: a province panel, 1987-2026 (plan section 6 B1-B3).

NOT FOR CITATION. Run:  py preshock/agri_elnino.py   (about a minute)

Question (the El Nino concern): how much palay and corn does an El Nino of a given strength cost,
by ecosystem, and what does the 2026-27 event imply? Replaces judgement with an estimate; the DA-DRRM loss table of past
El Ninos (Table 3 of an earlier note) is the out-of-sample check.

Data (all public, data/raw/agri, downloaded 14 Oct 2026): PSA OpenSTAT 0012E4EVCP0 (production) and 0022E4EAHC0 (area
harvested) by province, semester and ecosystem, 1987-2026 S1; NOAA CPC Oceanic Nino Index (ONI).

Model (the panel weather-yield design of the climate-economics literature; e.g. Schlenker and Roberts 2009, to verify):
  ln Y[p,e,s,t] = a[p,s] + b[p,s] * t + c * t^2 + beta_plus * ONI+[s,t] + beta_minus * ONI-[s,t] + u
  Y = yield (t/ha), area harvested or production; p = province, e = ecosystem (irrigated palay, rainfed palay, corn,
  estimated separately), s = semester, t = year. ONI+ = max(ONI, 0) (El Nino), ONI- = min(ONI, 0) (La Nina).
  ONI for a semester = the mean ONI over its growing season: semester 1 (harvests January-June: dry-season crop) = the
  seasons SON of the year before to FMA; semester 2 (harvests July-December: wet-season crop) = AMJ to ASO.
  Weighted by the province's mean area; standard errors clustered by year (ENSO is one national shock a year, so the
  effective sample is the number of years, about 39, not the number of province-years).
  The province trends absorb irrigation expansion, varieties and reporting changes; year effects cannot be used
  because they would absorb ENSO itself.
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "agri"
OUT = ROOT / "outputs"
CROPS = ["Irrigated Palay", "Rainfed Palay", "Corn"]
S1_SEASONS = [("SON", -1), ("OND", -1), ("NDJ", -1), ("DJF", 0), ("JFM", 0), ("FMA", 0)]
S2_SEASONS = [("AMJ", 0), ("MJJ", 0), ("JJA", 0), ("JAS", 0), ("ASO", 0)]
# DA-DRRM losses of past El Ninos (earlier note, Table 3; source: DA Disaster Risk Reduction and Management Section):
# period, semesters covered, production loss (t), all crops as DA reports them
DA_EVENTS = [("Jun 2023-Mar 2024", [(2023, 2), (2024, 1)], 828_337), ("Sep 2018-May 2019", [(2018, 2), (2019, 1)], 632_487),
             ("Oct 2014-Apr 2016", [(2015, 1), (2015, 2), (2016, 1)], 1_480_672), ("Aug 2009-Mar 2010", [(2009, 2), (2010, 1)], 1_183_753),
             ("Aug 2006-Feb 2007", [(2006, 2), (2007, 1)], 321_164), ("Jun 2004-Feb 2005", [(2004, 2), (2005, 1)], 332_226),
             ("Jun 2002-Mar 2003", [(2002, 2), (2003, 1)], 340_938), ("Mar 1997-May 1998", [(1997, 2), (1998, 1)], 1_056_743)]


def load_psa(name: str) -> pd.DataFrame:
    f = next(RAW.glob(f"PSA_OpenSTAT_{name}_*.csv"))
    w = pd.read_csv(f, comment="#")
    w = w[w["Geolocation"].str.startswith("....")]                  # provinces only
    w = w.rename(columns={"Ecosystem/Croptype": "crop", "Geolocation": "province"})
    w["province"] = w["province"].str.strip(". ").str.replace(r"\s*[a-z0-9]/$", "", regex=True)
    cols = [c for c in w.columns if "Semester" in c]
    long = w.melt(id_vars=["crop", "province"], value_vars=cols, var_name="period", value_name="v")
    long["year"] = long["period"].str[:4].astype(int)
    long["sem"] = long["period"].str[-1].astype(int)
    long["v"] = pd.to_numeric(long["v"], errors="coerce")
    return long.drop(columns="period")


def oni_by_semester() -> pd.DataFrame:
    o = pd.read_csv(RAW / "NOAA_CPC_ONI_ElNino_index_1950-2026.csv", comment="#")
    o = o.set_index(["SEAS", "YR"])["ANOM"]
    rows = []
    for t in range(1987, 2028):
        for s, seasons in ((1, S1_SEASONS), (2, S2_SEASONS)):
            vals = [o.get((sea, t + lag)) for sea, lag in seasons]
            vals = [v for v in vals if v is not None and not pd.isna(v)]
            rows.append({"year": t, "sem": s, "oni": np.mean(vals) if vals else np.nan, "n_seasons": len(vals),
                         "complete": len(vals) == len(seasons)})
    return pd.DataFrame(rows)


def panel() -> pd.DataFrame:
    q, a = load_psa("0012E4EVCP0"), load_psa("0022E4EAHC0")
    d = q.merge(a, on=["crop", "province", "year", "sem"], suffixes=("_q", "_a"))
    d = d[d["crop"].isin(CROPS) & (d["v_a"] >= 100) & (d["v_q"] > 0)].copy()
    d["yield"] = d["v_q"] / d["v_a"]
    d = d.merge(oni_by_semester(), on=["year", "sem"])
    d["oni_plus"], d["oni_minus"] = d["oni"].clip(lower=0), d["oni"].clip(upper=0)
    n = d.groupby(["crop", "province", "sem"])["year"].transform("size")
    return d[n >= 20]                                              # at least 20 years per province-semester


def estimate(d: pd.DataFrame, crop: str, y: str):
    x = d[(d["crop"] == crop)].copy()
    x["ps"] = x["province"] + "|" + x["sem"].astype(str)
    x["t"] = x["year"] - 2000
    x["lhs"] = np.log(x[y] if y == "yield" else x["v_q" if y == "production" else "v_a"])
    x["w"] = x.groupby("ps")["v_a"].transform("mean")
    fe = pd.get_dummies(x["ps"], dtype=float)
    tr = fe.mul(x["t"], axis=0).add_suffix("_t")
    X = pd.concat([x[["oni_plus", "oni_minus"]], (x["t"] ** 2).rename("t2"), fe, tr], axis=1)
    r = sm.WLS(x["lhs"], X, weights=x["w"]).fit(cov_type="cluster", cov_kwds={"groups": x["year"]})
    return r, x


def main():
    d = panel()
    print(f"Panel: {len(d):,} province-semester-ecosystem observations, {d.province.nunique()} provinces, "
          f"{d.year.min()}-{d.year.max()} (2026: semester 1 only)")
    res, fits = {}, {}
    for crop in CROPS:
        for y in ("yield", "area", "production"):
            r, x = estimate(d, crop, y)
            res[(crop, y)] = {"El Nino: % per +1 ONI": (np.exp(r.params["oni_plus"]) - 1) * 100,
                              "95% low": (np.exp(r.params["oni_plus"] - 1.96 * r.bse["oni_plus"]) - 1) * 100,
                              "95% high": (np.exp(r.params["oni_plus"] + 1.96 * r.bse["oni_plus"]) - 1) * 100,
                              "p-value": r.pvalues["oni_plus"],
                              "La Nina: % per -1 ONI": (np.exp(-r.params["oni_minus"]) - 1) * 100,
                              "p-value (La Nina)": r.pvalues["oni_minus"], "obs": int(r.nobs), "years": x["year"].nunique()}
            fits[(crop, y)] = r
            print(f"  {crop:16s} {y:10s} El Nino {res[(crop, y)]['El Nino: % per +1 ONI']:+6.2f}% per +1 ONI "
                  f"[{res[(crop, y)]['95% low']:+.2f}, {res[(crop, y)]['95% high']:+.2f}], p={r.pvalues['oni_plus']:.3f}")
    tab = pd.DataFrame(res).T

    # ---- loss implied for past events and 2026-27: production elasticity applied to each province's production
    oni = oni_by_semester().set_index(["year", "sem"])
    def loss(year, sem, oni_value=None, draws=None):
        """Production lost to El Nino (t) in a semester: sum over crops and provinces of Q x (1 - exp(-beta x ONI+))."""
        o = max(oni.loc[(year, sem), "oni"] if oni_value is None else oni_value, 0.0)
        tot = np.zeros(1 if draws is None else len(draws[CROPS[0]]))
        for crop in CROPS:
            q = d[(d.crop == crop) & (d["sem"] == sem)]
            # production level: the semester's actual if published, else the mean of the last 3 years
            lvl = q[q.year == year].v_q.sum() if (q.year == year).any() else q[q.year >= year - 3].groupby("year").v_q.sum().mean()
            b = np.atleast_1d(fits[(crop, "production")].params["oni_plus"] if draws is None else draws[crop])
            # actual production already contains the loss: loss = actual x (1/exp(b o) - 1); a projection: level x (1 - exp(b o))
            tot += lvl * (np.exp(-b * o) - 1) if (q.year == year).any() else lvl * (1 - np.exp(b * o))
        return tot
    rng = np.random.default_rng(20261014)
    draws = {c: rng.normal(fits[(c, "production")].params["oni_plus"], fits[(c, "production")].bse["oni_plus"], 2000) for c in CROPS}
    ev = []
    for name, sems, da in DA_EVENTS:
        l = sum(loss(t, s) for t, s in sems)[0]
        ld = sum(loss(t, s, draws=draws) for t, s in sems)
        ev.append({"El Nino (DA period)": name, "semesters": ", ".join(f"{t} S{s}" for t, s in sems),
                   "peak ONI in window": max(oni.loc[(t, s), "oni"] for t, s in sems),
                   "model: palay + corn lost (t)": l, "90% range low": np.quantile(ld, 0.05), "90% range high": np.quantile(ld, 0.95),
                   "DA-DRRM reported loss, all crops (t)": da})
    ev = pd.DataFrame(ev)
    corr = np.corrcoef(ev["model: palay + corn lost (t)"], ev["DA-DRRM reported loss, all crops (t)"])[0, 1]

    # ---- 2026-27: semester 2 of 2026 (ONI known through JAS) and semester 1 of 2027 (scenarios for the dry-season ONI)
    s2 = oni.loc[(2026, 2)]
    out = [{"semester": "2026 S2 (wet-season crop)", "ONI used": s2["oni"], "basis": f"NOAA, {int(s2['n_seasons'])} of 5 seasons observed",
            "palay + corn lost (t)": loss(2026, 2, s2["oni"])[0],
            "90% low": np.quantile(loss(2026, 2, s2["oni"], draws), 0.05), "90% high": np.quantile(loss(2026, 2, s2["oni"], draws), 0.95)}]
    for v in (1.5, 2.0, 2.5, 3.0):
        ld = loss(2027, 1, v, draws)
        out.append({"semester": "2027 S1 (dry-season crop)", "ONI used": v, "basis": "scenario (IRI 21 Sept 2026: most models >= +3.0 in SON-DJF; strong-moderate to MAM 2027)" if v < 3 else "IRI plume majority (beyond the 1987-2026 sample: extrapolation)",
                    "palay + corn lost (t)": loss(2027, 1, v)[0], "90% low": np.quantile(ld, 0.05), "90% high": np.quantile(ld, 0.95)})
    outlook = pd.DataFrame(out)

    # ---- report
    OUT.mkdir(exist_ok=True)
    stamp = dt.date.today().strftime("%Y%m%d")
    tab.to_csv(OUT / f"elnino_panel_coefficients_{stamp}.csv")
    fmt = lambda df: df.to_markdown(index=False, floatfmt=",.2f") if hasattr(df, "to_markdown") else df.to_string(index=False)
    L = [f"# El Nino and palay and corn: province panel, 1987-2026 ({dt.date.today():%d %B %Y})", "",
         "**NOT FOR CITATION** until reviewed (Infinity GEM 0.3.5). Script: `preshock/agri_elnino.py`.", "",
         f"Panel: {len(d):,} province x semester x ecosystem observations, {d.province.nunique()} provinces, {d.year.min()}-{d.year.max()}. "
         "Effects in % of the semester's yield, area or production per +1 of the Oceanic Nino Index averaged over the growing season "
         "(El Nino: ONI > 0) or per -1 (La Nina). Province-semester effects and trends; standard errors clustered by year.", "",
         "## 1. Effect of El Nino", "", tab.reset_index().rename(columns={"level_0": "ecosystem", "level_1": "measure"}).pipe(
             lambda t: t.to_markdown(index=False, floatfmt=".3f") if hasattr(t, "to_markdown") else t.to_string(index=False)), "",
         "## 2. Check against past El Ninos (DA-DRRM losses, earlier note, Table 3)", "",
         "The model counts palay and corn only; DA's figures cover all crops and are field damage reports, so the model should be "
         f"of the same order and move with them, not equal them. Correlation across the eight events: {corr:.2f}; the model's loss is "
         f"{np.median(ev['model: palay + corn lost (t)'] / ev['DA-DRRM reported loss, all crops (t)']):.1f} times DA's (median). "
         "Reasons: the model measures the whole shortfall against each province's trend, including area not planted for lack of "
         "water, while DA counts field damage reports; and it applies a linear effect to every semester with ONI > 0. A rough "
         "check on PSA's national totals for 2015-16 (palay and corn against 2014) gives about 3 million t against the model's "
         "4.0 million: the model may lean high. Refinements listed in section 5.", "", fmt(ev), "",
         "## 3. 2026-27 (the current El Nino: ONI +2.16 in July-September 2026)", "", fmt(outlook), "",
         "Semester 2 of 2026 uses the ONI seasons observed so far. Semester 1 of 2027 is shown for dry-season ONI scenarios. **Official "
         "outlook:** the CCSR/IRI ENSO plume of 21 September 2026 (22 models) says El Nino 'will strengthen further during 2026 and continue "
         "into early 2027', with 'nearly all dynamical and several statistical models forecasting the Nino3.4 index above +3.0 C from fall into "
         "winter (SON-DJF)' and 'strong-to-moderate El Nino conditions' through MAM 2027 (iri.columbia.edu, ENSO forecast, read 14 Oct 2026; "
         "IRI's index is Nino3.4 on OISST, close to but not identical with NOAA's ONI). The dry-season window averages SON to FMA, so +2.5 to "
         "+3.0 is the plausible range. **+3.0 lies beyond every El Nino in the 1987-2026 sample (peaks about +2.6): the linear model "
         "extrapolates there.** PAGASA's advisory to be added. Production levels: the last three years' average. The 90% ranges come from the "
         "coefficient uncertainty only (2,000 draws).", "",
         "## 4. How it enters the CGE", "",
         "As a productivity loss on rice and corn (`tfp_scale` on `arice`, `amaiz`) equal to the production effect, for the semesters "
         "concerned, converted to a calendar-year share. Not as a demand cut.", "",
         "## 5. Refinements before citation", "",
         "- Non-linear El Nino effect (threshold at ONI 0.5, or squared) and a leave-one-event-out test;",
         "- province rainfall (CHIRPS, public) instead of the national ONI alone, and irrigation coverage;",
         "- PAGASA's or NOAA's official outlook for the 2027 dry season instead of scenarios;",
         "- PSA's 2026 semester 2 figures (January 2027) as a true out-of-sample test;",
         "- the literature checked against primary sources (e.g. Roberts, Dawe, Falcon and Naylor 2009 on ENSO and Luzon rice).", ""]
    rep = OUT / f"elnino_panel_{stamp}.md"
    rep.write_text("\n".join(L), encoding="utf-8")
    print(f"\nPast events: correlation with DA losses {corr:.2f}")
    print(ev.round(0).to_string(index=False))
    print(outlook.round(2).to_string(index=False))
    print("saved", rep)


if __name__ == "__main__":
    main()
