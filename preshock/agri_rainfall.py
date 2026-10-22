"""El Nino through local rainfall: CHIRPS province rainfall x PSA palay and corn, 1987-2026 (upgrade
of preshock/agri_elnino.py; 14 Oct 2026).

NOT FOR CITATION until reviewed. Run:  py preshock/agri_rainfall.py   (about two minutes)

Why better than the national index alone: rainfall differs by province in the same year, so the yield equation can carry
YEAR x SEMESTER fixed effects. They absorb everything national in a season (prices, policy, technology, imports), and the
rainfall effect is identified from provinces that were drier or wetter than usual in the same season.

Step 1 (yield equation, by ecosystem: irrigated palay, rainfed palay, corn):
    ln Q[p,s,t] = a[p,s] + b[p,s] * t + g[s,t] + beta_dry * D[p,s,t] + beta_wet * W[p,s,t] + u
  Q = production (also yield and area); z = the season's rainfall as a z-score against the province's own 1987-2025 record
  for that season; D = min(z, 0) (drought), W = max(z, 0) (excess rain: floods, typhoons). Weighted by mean area;
  standard errors clustered by year (conservative: rainfall shocks are spatially correlated within a season).
Step 2 (El Nino -> local rainfall, per province and season):  z[p,s,t] = c + theta+ ONI+ + theta- ONI- + e
Step 3 (El Nino -> production): for a given ONI, z ~ Normal(theta x ONI, sigma_e), so the expected drought and wet terms
  have closed forms; the province's production effect = beta_dry x dE[D] + beta_wet x dE[W] against ONI = 0.
Nowcast: 2026 semester 2 from the rainfall already observed (CHIRPS to August 2026: June-August of June-October).
Check: losses implied by the ACTUAL rainfall of past El Nino seasons vs the DA-DRRM loss table.

Growing seasons (months of rainfall): semester 1 (dry-season crop, harvested January-June) = November of the year before
to April; semester 2 (wet-season crop, harvested July-December) = June to October.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from matplotlib.path import Path as MPath
from scipy.io import netcdf_file
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import agri_elnino as A  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "agri"
OUT = ROOT / "outputs"
SEASON_MONTHS = {1: [(-1, 11), (-1, 12), (0, 1), (0, 2), (0, 3), (0, 4)], 2: [(0, 6), (0, 7), (0, 8), (0, 9), (0, 10)]}
# PSA province name -> geoBoundaries outline (cities inside a province take the province's rainfall)
TO_GB = {"Bacolod City": "Negros Occidental", "Butuan City": "Agusan del Norte", "City of Davao": "Davao del Sur",
         "Cotabato (North Cotabato)": "Cotabato", "Davao de Oro (Compostela Valley)": "Compostela Valley",
         "Maguindanao del Norte": "Maguindanao", "Maguindanao del Sur": "Maguindanao", "Puerto Princesa City": "Palawan",
         "Tawi-tawi": "Tawi-Tawi", "Zamboanga City": "Zamboanga del Sur"}


def province_monthly_rain() -> pd.DataFrame:
    """Mean CHIRPS rainfall (mm/month) of the 0.25-degree cells whose centres fall in each province (nearest cell if none)."""
    f = netcdf_file(RAW / "CHIRPS_v2_monthly_Philippines_0.25deg_1986-2026.nc", "r", mmap=False)
    v = f.variables
    P = np.array(v["precipitation"][:], float)
    mv = getattr(v["precipitation"], "missing_value", None)
    P[(P < 0) | (P > 1e5) | (P == mv if mv is not None else False)] = np.nan
    X, Y, T = np.array(v["X"][:]), np.array(v["Y"][:]), np.array(v["T"][:])
    f.close()
    months = [(1960 + int(t) // 12, int(t) % 12 + 1) for t in np.floor(T)]
    gx, gy = np.meshgrid(X, Y)
    pts = np.column_stack([gx.ravel(), gy.ravel()])
    land = ~np.isnan(P).all(axis=0).ravel()
    gj = json.loads((RAW / "geoBoundaries-PHL-ADM2_simplified.geojson").read_text(encoding="utf-8"))
    out = {}
    for feat in gj["features"]:
        name, geom = feat["properties"]["shapeName"], feat["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        inside = np.zeros(len(pts), bool)
        for poly in polys:
            inside |= MPath(np.array(poly[0])).contains_points(pts)     # outer ring
        inside &= land
        if not inside.any():                                             # small province: nearest land cell to its centre
            c = np.vstack([np.array(p[0]) for p in polys]).mean(axis=0)
            d = np.where(land, ((pts - c) ** 2).sum(axis=1), np.inf)
            inside[np.argmin(d)] = True
        out[name] = np.nanmean(P.reshape(len(T), -1)[:, inside], axis=1)
    r = pd.DataFrame(out, index=pd.MultiIndex.from_tuples(months, names=["year", "month"]))
    return r


def season_rain(r: pd.DataFrame) -> pd.DataFrame:
    """Rainfall by province, semester and year (season total, mm), the share of the season's months observed, and z-scores."""
    rows = []
    for t in range(1987, 2027):
        for s, ms in SEASON_MONTHS.items():
            keys = [(t + dy, m) for dy, m in ms]
            have = [k for k in keys if k in r.index]
            if not have:
                continue
            tot = r.loc[have].sum() * len(keys) / len(have)              # scaled to a full season if months are missing
            for p, val in tot.items():
                rows.append({"gb": p, "year": t, "sem": s, "rain": val, "months_observed": len(have), "months_season": len(keys)})
    d = pd.DataFrame(rows)
    ref = d[(d["year"] <= 2025) & (d["months_observed"] == d["months_season"])]
    st = ref.groupby(["gb", "sem"])["rain"].agg(["mean", "std"])
    d = d.join(st, on=["gb", "sem"])
    d["z"] = (d["rain"] - d["mean"]) / d["std"]
    return d.drop(columns=["mean", "std"])


def build():
    q = A.panel()                                                # PSA production/area/yield, ONI
    q["gb"] = q["province"].map(lambda p: TO_GB.get(p, p))
    sr = season_rain(province_monthly_rain())
    d = q.merge(sr, on=["gb", "year", "sem"], how="inner")
    d["D"], d["W"] = d["z"].clip(upper=0), d["z"].clip(lower=0)
    return d, sr


def estimate(d, crop, y="production"):
    x = d[d["crop"] == crop].copy()
    x["ps"] = x["province"] + "|" + x["sem"].astype(str)
    x["st"] = x["year"].astype(str) + "|" + x["sem"].astype(str)
    x["t"] = x["year"] - 2000
    x["lhs"] = np.log({"production": x["v_q"], "yield": x["yield"], "area": x["v_a"]}[y])
    w = x.groupby("ps")["v_a"].transform("mean")
    fe = pd.get_dummies(x["ps"], dtype=float)
    X = pd.concat([x[["D", "W"]], fe, fe.mul(x["t"], axis=0).add_suffix("_t"),
                   pd.get_dummies(x["st"], dtype=float, drop_first=True)], axis=1)
    return sm.WLS(x["lhs"], X, weights=w).fit(cov_type="cluster", cov_kwds={"groups": x["year"]}), x


def first_stage(sr):
    """Per province and semester: z on ONI+ and ONI- (1987-2025 full seasons). Returns theta+, theta-, sigma."""
    oni = A.oni_by_semester()
    x = sr.merge(oni, on=["year", "sem"])
    x = x[(x["year"] <= 2025) & (x["months_observed"] == x["months_season"])]
    rows = []
    for (p, s), g in x.groupby(["gb", "sem"]):
        Xm = sm.add_constant(np.column_stack([g["oni"].clip(lower=0), g["oni"].clip(upper=0)]))
        r = sm.OLS(g["z"].values, Xm).fit()
        rows.append({"gb": p, "sem": s, "theta_plus": r.params[1], "theta_minus": r.params[2], "sigma": np.sqrt(r.scale),
                     "const": r.params[0]})
    return pd.DataFrame(rows)


def expected_parts(mu, sig):
    """E[min(z,0)] and E[max(z,0)] for z ~ Normal(mu, sig)."""
    a = mu / sig
    return mu * norm.cdf(-a) - sig * norm.pdf(a), mu * norm.cdf(a) + sig * norm.pdf(a)


def main():
    d, sr = build()
    print(f"Panel with rainfall: {len(d):,} observations, {d['province'].nunique()} provinces, {d['year'].min()}-{d['year'].max()}")
    fits, tab = {}, {}
    for crop in A.CROPS:
        for y in ("production", "yield", "area"):
            r, _ = estimate(d, crop, y)
            fits[(crop, y)] = r
            tab[(crop, y)] = {"drought: % per -1 SD of season rain": (np.exp(-r.params["D"]) - 1) * 100,
                              "95% low": (np.exp(-(r.params["D"] + 1.96 * r.bse["D"])) - 1) * 100,
                              "95% high": (np.exp(-(r.params["D"] - 1.96 * r.bse["D"])) - 1) * 100,
                              "p (drought)": r.pvalues["D"],
                              "excess rain: % per +1 SD": (np.exp(r.params["W"]) - 1) * 100, "p (excess)": r.pvalues["W"],
                              "obs": int(r.nobs)}
            print(f"  {crop:16s} {y:10s} drought {tab[(crop, y)]['drought: % per -1 SD of season rain']:+6.2f}% per -1 SD "
                  f"(p={r.pvalues['D']:.3f}); excess rain {tab[(crop, y)]['excess rain: % per +1 SD']:+6.2f}% per +1 SD (p={r.pvalues['W']:.3f})")
    tab = pd.DataFrame(tab).T
    fs = first_stage(sr)
    fs_s = fs.groupby("sem")[["theta_plus", "sigma"]].describe().round(2)

    # ---- production effect of a given ONI, province by province (expected rainfall terms vs ONI = 0)
    def elnino_loss(year, sem, oni_value, levels):
        f = fs[fs["sem"] == sem].set_index("gb")
        tot = 0.0
        by_crop = {}
        for crop in A.CROPS:
            b = fits[(crop, "production")].params
            lv = levels[crop]
            g = lv.index.map(lambda p: TO_GB.get(p, p))
            ok = [k for k in g if k in f.index]
            th, si, c0 = (f.loc[g[g.isin(ok)], k].values for k in ("theta_plus", "sigma", "const"))
            mu1, mu0 = c0 + th * max(oni_value, 0), c0
            d1, w1 = expected_parts(mu1, si)
            d0, w0 = expected_parts(mu0, si)
            eff = b["D"] * (d1 - d0) + b["W"] * (w1 - w0)
            loss = float((lv[g.isin(ok)].values * (1 - np.exp(eff))).sum())
            by_crop[crop] = loss
            tot += loss
        return tot, by_crop

    def levels_for(sem, years):
        q = d[(d["sem"] == sem) & d["year"].isin(years)]
        return {c: q[q["crop"] == c].groupby("province")["v_q"].sum() / len(years) for c in A.CROPS}

    # ---- past El Ninos: losses implied by the ACTUAL rainfall of each season (province by province)
    def actual_rain_loss(year, sem):
        tot = 0.0
        for crop in A.CROPS:
            b = fits[(crop, "production")].params
            x = d[(d["crop"] == crop) & (d["year"] == year) & (d["sem"] == sem)]
            eff = b["D"] * x["D"] + b["W"] * x["W"]
            tot += float((x["v_q"] * (np.exp(-eff) - 1)).sum())    # actual production already contains the effect
        return tot
    ev = []
    for name, sems, da in A.DA_EVENTS:
        ev.append({"El Nino (DA period)": name, "rainfall model: palay + corn lost (t)": sum(actual_rain_loss(t, s) for t, s in sems),
                   "DA-DRRM reported loss, all crops (t)": da})
    ev = pd.DataFrame(ev)
    corr = np.corrcoef(ev.iloc[:, 1], ev.iloc[:, 2])[0, 1]

    # ---- 2026 semester 2 nowcast from observed rainfall (June-August), and El Nino scenarios for 2027 semester 1
    lv2 = levels_for(2, [2023, 2024, 2025])
    obs = sr[(sr["year"] == 2026) & (sr["sem"] == 2)].set_index("gb")
    now = 0.0
    for crop in A.CROPS:
        b = fits[(crop, "production")].params
        g = lv2[crop].index.map(lambda p: TO_GB.get(p, p))
        z = obs["z"].reindex(g).fillna(0).values
        now += float((lv2[crop].values * (1 - np.exp(b["D"] * np.minimum(z, 0) + b["W"] * np.maximum(z, 0)))).sum())
    months_obs = int(obs["months_observed"].iloc[0]) if len(obs) else 0
    lv1 = levels_for(1, [2024, 2025, 2026])
    out = [{"semester": "2026 S2 (wet-season crop)", "basis": f"CHIRPS rainfall observed June-August ({months_obs} of 5 months)",
            "palay + corn lost (t)": now},
           {"semester": "2026 S2 (wet-season crop)", "basis": "El Nino expectation at ONI 1.58 (NOAA, observed so far)",
            "palay + corn lost (t)": elnino_loss(2026, 2, 1.58, lv2)[0]}]
    for v in (2.0, 2.5, 3.0):
        out.append({"semester": "2027 S1 (dry-season crop)", "basis": f"El Nino expectation at ONI {v:.1f}" + (" (IRI plume majority; beyond the sample)" if v >= 3 else ""),
                    "palay + corn lost (t)": elnino_loss(2027, 1, v, lv1)[0]})
    outlook = pd.DataFrame(out)

    stamp = dt.date.today().strftime("%Y%m%d")
    tab.to_csv(OUT / f"elnino_rainfall_coefficients_{stamp}.csv")
    fs.to_csv(OUT / f"elnino_rainfall_first_stage_by_province_{stamp}.csv", index=False)
    md = lambda df: df.to_markdown(index=False, floatfmt=",.2f") if hasattr(df, "to_markdown") else df.to_string(index=False)
    tt = tab.reset_index().rename(columns={"level_0": "ecosystem", "level_1": "measure"})
    L = [f"# El Nino through local rainfall: CHIRPS x PSA palay and corn, 1987-2026 ({dt.date.today():%d %B %Y})", "",
         "**NOT FOR CITATION** until reviewed (Infinity GEM 0.3.5). Script: `preshock/agri_rainfall.py`. Upgrade of "
         "`agri_elnino.py` (national El Nino index only).", "",
         f"Panel: {len(d):,} province x semester x ecosystem observations with CHIRPS season rainfall. Year x semester fixed effects "
         "absorb everything national in a season; the rainfall effect comes from provinces drier or wetter than usual in the same season.", "",
         "## 1. Drought and excess rain: effect on production, yield and area", "", md(tt), "",
         "## 2. El Nino and local rainfall (first stage, per province and semester; theta+ = SDs of season rain per +1 ONI)", "",
         "```", fs_s.to_string(), "```", "",
         "## 3. Check: past El Ninos, losses implied by the actual rainfall vs DA-DRRM", "",
         f"Correlation across the eight events: {corr:.2f}. Same caveats as the national-index model: palay and corn only vs all crops; "
         "shortfall vs trend vs field damage reports. The year effects now absorb part of a nationwide El Nino (the part common to all "
         "provinces), so this model's past-event losses are a lower bound of the El Nino effect.", "", md(ev), "",
         "## 4. 2026-27", "", md(outlook), "",
         "The El Nino expectations add the national component back through the first stage (local rainfall shifts with the ONI), but "
         "not any purely national channel (e.g. a nationwide water-allocation cut): read them as lower bounds next to the national-index "
         "model (`elnino_panel_*.md`). The pair brackets the effect.", ""]
    rep = OUT / f"elnino_rainfall_panel_{stamp}.md"
    rep.write_text("\n".join(L), encoding="utf-8")
    print(f"\nPast events, correlation with DA: {corr:.2f}")
    print(ev.round(0).to_string(index=False))
    print(outlook.round(0).to_string(index=False))
    print(fs_s.to_string())
    print("saved", rep)


if __name__ == "__main__":
    main()
