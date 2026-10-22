"""How palay and corn farmers respond to output and fertilizer prices: a Nerlovian supply response on a province panel
(plan section 6, A3). Replaces earlier assumed 25/50/75% production responses.

NOT FOR CITATION until reviewed. Run:  py preshock/agri_supply_response.py

Model (Nerlove 1958: adaptive expectations / partial adjustment; to verify), annual, province p, year t:
    ln Q[p,t] = a[p] + b[p] t + gamma ln Q[p,t-1] + beta ln( Pcrop[p,t-1] / Purea[p,t-1] ) + delta ONI+[t] + e
  Q = area harvested, yield, or production; Pcrop = farmgate price (palay 'other variety'; yellow corn), Purea = dealers'
  price of urea (the main nitrogen fertilizer); ONI+ = El Nino strength over the calendar year (NOAA). Short-run elasticity
  beta; long-run beta / (1 - gamma). A higher fertilizer price lowers the ratio, so the response to fertilizer is -beta.
  Variant with year effects (absorbing everything national, e.g. NFA prices, imports, weather) identifies beta from
  differences between provinces only.
Sample 1991-2019 (PSA's dealers' fertilizer prices end in 2019). Standard errors clustered by province.
Caveats: Nickell bias of the lagged term with province effects and T of about 28 (small); prices are provincial annual
averages; the ratio uses urea only.

Implication shown: the production change for the fertilizer price rise assumed earlier (+34.95%), with
crop prices unchanged (as in its table), set against its 25/50/75% scenarios (palay -3.5% / -6.9% / -10.4%).
In the CGE this is a YARDSTICK for the model's own farm supply response, not an extra shock (double counting).
"""
import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "agri"
FERT_RISE = 0.3495


def _prov(s: pd.Series) -> pd.Series:
    return s.str.strip(". ").str.replace(r"\s*[a-z0-9]/$", "", regex=True).str.strip().str.lower()


def annual_prices(file, item_col, item):
    w = pd.read_csv(RAW / file, comment="#")
    w = w[w["Geolocation"].str.startswith("....") & (w[item_col] == item)]
    cols = [c for c in w.columns if c.endswith("Annual")]
    l = w.melt(id_vars=["Geolocation"], value_vars=cols, var_name="k", value_name="v")
    l["year"] = l["k"].str[:4].astype(int)
    l["prov"] = _prov(l["Geolocation"])
    l["v"] = pd.to_numeric(l["v"], errors="coerce")
    return l.dropna(subset=["v"]).query("v > 0")[["prov", "year", "v"]]


def farmgate(item_old, item_new):
    a = annual_prices("PSA_OpenSTAT_0032M4AFP01_cereals_farmgate_prices_old_series.csv", "Commodity", item_old)
    b = annual_prices("PSA_OpenSTAT_0032M4AFN01_cereals_farmgate_prices_by_province_2010-2026.csv", "Commodity", item_new)
    return pd.concat([a[a.year < 2010], b]).drop_duplicates(["prov", "year"], keep="last")


def quantities(crop):
    out = {}
    for code, name in (("0012E4EVCP0", "q"), ("0022E4EAHC0", "a")):
        w = pd.read_csv(next(RAW.glob(f"PSA_OpenSTAT_{code}_*.csv")), comment="#")
        w = w[w["Geolocation"].str.startswith("....") & (w["Ecosystem/Croptype"] == crop)]
        cols = [c for c in w.columns if c.endswith("Annual")]
        l = w.melt(id_vars=["Geolocation"], value_vars=cols, var_name="k", value_name=name)
        l["year"] = l["k"].str[:4].astype(int)
        l["prov"] = _prov(l["Geolocation"])
        l[name] = pd.to_numeric(l[name], errors="coerce")
        out[name] = l[["prov", "year", name]]
    d = out["q"].merge(out["a"], on=["prov", "year"])
    return d[(d.a >= 100) & (d.q > 0)]


def oni_annual():
    o = pd.read_csv(RAW / "NOAA_CPC_ONI_ElNino_index_1950-2026.csv", comment="#")
    return o.groupby("YR")["ANOM"].mean().clip(lower=0).rename("oni_plus")


def panel(crop, item_old, item_new):
    d = quantities(crop)
    d["yld"] = d.q / d.a
    pc = farmgate(item_old, item_new).rename(columns={"v": "pc"})
    pu = annual_prices("PSA_OpenSTAT_0062M4AFER1_fertilizer_dealers_prices_1990-2019.csv", "Fertilizer Grade", "Urea (45-0-0)").rename(columns={"v": "pu"})
    x = d.merge(pc, on=["prov", "year"]).merge(pu, on=["prov", "year"]).sort_values(["prov", "year"])
    x = x.join(oni_annual(), on="year")
    for v in ("a", "yld", "q"):
        x[f"l{v}"] = np.log(x[v])
        x[f"l{v}_lag"] = x.groupby("prov")[f"l{v}"].shift(1)
    x["lratio_lag"] = np.log(x.pc / x.pu).groupby(x.prov).shift(1)
    x["t"] = x.year - 2000
    x = x.dropna(subset=["la_lag", "lratio_lag"])
    n = x.groupby("prov").year.transform("size")
    return x[n >= 15]


def estimate(x, v, year_fe):
    f = f"l{v} ~ l{v}_lag + lratio_lag + C(prov) + C(prov):t" + (" + C(year)" if year_fe else " + oni_plus + I(t**2)")
    r = smf.ols(f, data=x).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(x.prov)[0]})
    b, g = r.params["lratio_lag"], r.params[f"l{v}_lag"]
    return {"short-run elasticity (beta)": b, "s.e.": r.bse["lratio_lag"], "p": r.pvalues["lratio_lag"],
            "adjustment (gamma)": g, "long-run elasticity": b / (1 - g) if g < 1 else np.nan,
            "El Nino (per +1 ONI, %)": (np.exp(r.params["oni_plus"]) - 1) * 100 if not year_fe else np.nan,
            "obs": int(r.nobs), "provinces": x.prov.nunique(), "years": f"{x.year.min()}-{x.year.max()}"}


def main():
    specs = {"Palay": ("Palay", "Palay [Paddy] Other Variety, dry (conv. to 14% mc)", "Palay [Paddy] Other Variety, dry (conv. to 14% mc)"),
             "Corn": ("Corn", "Corngrain [Maize] Yellow, matured", "Corngrain [Maize] Yellow, matured")}
    rows = {}
    for name, (crop, io, inew) in specs.items():
        x = panel(crop, io, inew)
        for v, lab in (("a", "area"), ("yld", "yield"), ("q", "production")):
            for fe in (False, True):
                rows[(name, lab, "year effects" if fe else "province trends + El Nino")] = estimate(x, v, fe)
    t = pd.DataFrame(rows).T
    print(t.to_string())
    imp = []
    for name in specs:
        for fe in ("province trends + El Nino", "year effects"):
            r = t.loc[(name, "production", fe)]
            d_sr = (np.exp(-r["short-run elasticity (beta)"] * np.log(1 + FERT_RISE)) - 1) * 100
            d_lr = (np.exp(-r["long-run elasticity"] * np.log(1 + FERT_RISE)) - 1) * 100
            imp.append({"crop": name, "specification": fe, "production change, first year (%)": d_sr, "production change, long run (%)": d_lr})
    imp = pd.DataFrame(imp)
    print(imp.round(2).to_string(index=False))
    stamp = dt.date.today().strftime("%Y%m%d")
    md = lambda df, idx=False: (df.to_markdown(index=idx, floatfmt=".3f") if hasattr(df, "to_markdown") else df.to_string(index=idx))
    L = [f"# Palay and corn supply response to output and fertilizer prices: Nerlovian province panel ({dt.date.today():%d %B %Y})", "",
         "**NOT FOR CITATION** until reviewed (Infinity GEM 0.3.5). Script: `preshock/agri_supply_response.py`. Data: PSA "
         "OpenSTAT (area harvested, production, farmgate prices, dealers' urea prices), NOAA ONI; annual, by province, 1991-2019.", "",
         "Elasticities with respect to last year's crop-to-urea price ratio. Long run = short run / (1 - adjustment). Standard errors clustered "
         "by province.", "", md(t.reset_index().rename(columns={"level_0": "crop", "level_1": "measure", "level_2": "specification"})), "",
         f"## The fertilizer price rise assumed earlier (+{FERT_RISE*100:.2f}%), crop prices unchanged", "", md(imp), "",
         "Compare with its scenarios: palay -3.5% (low, 25% response), -6.9% (moderate), -10.4% (high); corn about -2.8 / -5.6 / -8.4%. "
         "**In the CGE this is the yardstick for the model's own farm response, not an extra shock** (the CGE already passes fertilizer and fuel "
         "prices to farms).", "",
         "**Caveats:** urea only; provincial annual averages; Nickell bias of the lagged term (small with T about 28); the year-effects variant "
         "uses only differences between provinces, which may be partly measurement noise.", ""]
    rep = ROOT / "outputs" / f"agri_supply_response_{stamp}.md"
    rep.write_text("\n".join(L), encoding="utf-8")
    print("saved", rep)


if __name__ == "__main__":
    main()
