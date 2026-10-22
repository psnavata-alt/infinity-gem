"""Geopolitics across ASEAN and emerging economies: panel local projections (reactivated 16 Oct 2026).

NOT FOR CITATION until reviewed. Run:  py preshock/geopolitics_panel_lp.py  [--refresh]   (downloads BIS data the first time)

Why a panel: one country's geopolitical-risk index moves with world events (wars, oil), so a Philippines-only regression
cannot separate Philippine risk from world risk (the earlier local projections found no significant effect; an earlier VAR
found a borderline peso effect). With many countries and month fixed effects, everything common to all countries in a
month (oil, US rates, the world GPR, global risk appetite) drops out, and the effect is identified from each country's
OWN geopolitical risk relative to the others: the design of the cross-country literature (e.g. Caldara and Iacoviello
2022, section V, country-level panel; Jorda 2005 local projections; Driscoll-Kraay standard errors).

Model, for h = 0..12 months:
  y[i,t+h] - y[i,t-1] = b_h GPR[i,t] + sum_{l=1..3} (c_l dy[i,t-l] + d_l GPR[i,t-l]) + country effect + month effect + e
  GPR[i,t]: Caldara-Iacoviello recent country index GPRC (share of newspaper articles about the country with geopolitical
            terms), standardised within each country (its own 2000-2025 mean and standard deviation), so b_h is the effect
            of a one-standard-deviation rise in that country's own risk.
  y: 100 x log of local currency per US$ (BIS WS_XRU, monthly average; + = weaker) and of the CPI (BIS WS_LONG_CPI, 628).
  Standard errors: Driscoll and Kraay (1998), robust to correlation across countries and over time (statsmodels
  'hac-groupsum' by month, h + 1 lags).
Country sets: ASEAN-5 in the GPR file (Indonesia, Malaysia, Philippines, Thailand, Vietnam); emerging Asia (ASEAN-5 + India,
  Korea, Taiwan, China); all emerging economies with a floating or managed currency (adds Brazil, Mexico, Colombia, Chile,
  Peru, Turkey, South Africa, Poland, Hungary, Israel). Excluded: pegs (Hong Kong, Saudi Arabia) and hyperinflation or war
  cases (Argentina, Venezuela, Russia, Ukraine, Egypt, Tunisia).
Sample: January 2000 to the last month with data.
Then: the Philippines' own 2026 risk (GPRC_PHL, standardised) times the panel responses gives the implied 2026 effect on the
peso and prices, to compare with the earlier estimates and the inflation VAR (preshock/inflation_var.py).
"""
import datetime as dt
import io
import shutil
import sys
import tempfile
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parent.parent
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
MAC = ROOT / "data" / "raw" / "macro"
PAN = MAC / "panel_bis"
H, LAGS = 12, 3
ASEAN = {"IDN": ("ID", "IDR"), "MYS": ("MY", "MYR"), "PHL": ("PH", "PHP"), "THA": ("TH", "THB"), "VNM": ("VN", "VND")}
ASIA = {**ASEAN, "IND": ("IN", "INR"), "KOR": ("KR", "KRW"), "TWN": ("TW", "TWD"), "CHN": ("CN", "CNY")}
EM = {**ASIA, "BRA": ("BR", "BRL"), "MEX": ("MX", "MXN"), "COL": ("CO", "COP"), "CHL": ("CL", "CLP"), "PER": ("PE", "PEN"),
      "TUR": ("TR", "TRY"), "ZAF": ("ZA", "ZAR"), "POL": ("PL", "PLN"), "HUN": ("HU", "HUF"), "ISR": ("IL", "ILS")}
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36"}


def download():
    PAN.mkdir(exist_ok=True)
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    areas = "+".join(v[0] for v in EM.values())
    curs = "+".join(v[1] for v in EM.values())
    for name, url, what in (
            ("BIS_WS_XRU_panel_monthly_average.csv", f"https://stats.bis.org/api/v1/data/WS_XRU/M.{areas}.{curs}.A/all?format=csv&startPeriod=1995-01",
             "local currency per US dollar, monthly average of observations"),
            ("BIS_WS_LONG_CPI_panel_index.csv", f"https://stats.bis.org/api/v1/data/WS_LONG_CPI/M.{areas}.628/all?format=csv&startPeriod=1995-01",
             "consumer prices, index (unit 628)")):
        raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180).read()
        d = pd.read_csv(io.BytesIO(raw))
        keep = [c for c in ("REF_AREA", "CURRENCY", "UNIT_MEASURE", "TIME_PERIOD", "OBS_VALUE") if c in d.columns]
        with open(PAN / name, "w", encoding="utf-8", newline="") as f:
            f.write(f"# Source: Bank for International Settlements statistics API: {what}. {url}\n")
            f.write(f"# Downloaded {now} for preshock/geopolitics_panel_lp.py. Columns as published.\n")
            d[keep].to_csv(f, index=False)
        print("saved", name, d.shape)


def gpr_panel():
    tmp = Path(tempfile.gettempdir()) / "infinity_gem_gpr_export.xls"
    shutil.copy2(MAC / "Caldara_Iacoviello_data_gpr_export_downloaded_2026-10-14.xls", tmp)
    d = pd.read_excel(tmp)
    d.index = pd.PeriodIndex(pd.to_datetime(d["month"]), freq="M")
    g = d[[f"GPRC_{c}" for c in EM]].rename(columns=lambda c: c[5:])
    return g


def bis_panel(fname, key_col):
    d = pd.read_csv(PAN / fname, comment="#")
    inv = {v[0]: k for k, v in EM.items()}
    d["iso3"] = d["REF_AREA"].map(inv)
    d = d.dropna(subset=["iso3"])
    d["t"] = pd.PeriodIndex(d["TIME_PERIOD"], freq="M")
    return d.pivot_table(index="t", columns="iso3", values="OBS_VALUE", aggfunc="first")


def panel_lp(y, shock, countries, start="2000-01"):
    """y, shock: DataFrames (month x country). Returns b_h, se_h, n by h for the stacked panel."""
    rows = []
    ly = 100 * np.log(y[countries].loc[start:])
    s = shock[countries].loc[start:]
    for h in range(H + 1):
        parts = []
        for c in countries:
            d = pd.DataFrame({"lhs": ly[c].shift(-h) - ly[c].shift(1), "shock": s[c]})
            dy = ly[c].diff()
            for l in range(1, LAGS + 1):
                d[f"dy{l}"] = dy.shift(l)
                d[f"s{l}"] = s[c].shift(l)
            d["country"], d["t"] = c, d.index.astype(str)
            parts.append(d)
        z = pd.concat(parts).replace([np.inf, -np.inf], np.nan).dropna()
        X = pd.concat([z.drop(columns=["lhs", "country", "t"]),
                       pd.get_dummies(z["country"], prefix="c", drop_first=True, dtype=float),
                       pd.get_dummies(z["t"], prefix="t", drop_first=True, dtype=float)], axis=1)
        X = sm.add_constant(X, has_constant="add")
        tcode = pd.factorize(z["t"])[0]
        r = sm.OLS(z["lhs"].to_numpy(), X.to_numpy(dtype=float)).fit(cov_type="hac-groupsum", cov_kwds={"time": tcode, "maxlags": h + 1})
        j = list(X.columns).index("shock")
        b, se = float(r.params[j]), float(r.bse[j])
        rows.append({"h": h, "beta": b, "se": se, "low90": b - 1.645 * se, "high90": b + 1.645 * se, "n": int(r.nobs),
                     "countries": z["country"].nunique()})
    return pd.DataFrame(rows).set_index("h")


def main(refresh=False):
    if refresh or not (PAN / "BIS_WS_XRU_panel_monthly_average.csv").exists():
        download()
    g = gpr_panel()
    base = g.loc["2000-01":"2025-12"]
    gz = (g - base.mean()) / base.std()
    fx, cpi = bis_panel("BIS_WS_XRU_panel_monthly_average.csv", "CURRENCY"), bis_panel("BIS_WS_LONG_CPI_panel_index.csv", "UNIT_MEASURE")
    sets = {"ASEAN-5": list(ASEAN), "Emerging Asia (9)": list(ASIA), "Emerging economies (19)": list(EM)}
    res = {}
    for sname, cs in sets.items():
        for vname, y in (("Currency per US$ (+ = weaker)", fx), ("Consumer prices", cpi)):
            cs_ok = [c for c in cs if c in y.columns]
            res[(sname, vname)] = panel_lp(y, gz, cs_ok)
            print(sname, vname, res[(sname, vname)].loc[[0, 3, 6, 12], ["beta", "low90", "high90"]].round(2).to_dict("index"))
    # Philippine 2026 risk, standardised, and the implied effect (ASEAN-5 responses; no new shocks after the last month)
    ph = gz["PHL"].loc["2025-01":]
    surpr = ph - gz["PHL"].loc["2015-01":"2025-12"].mean()
    impl = {}
    for vname in ("Currency per US$ (+ = weaker)", "Consumer prices"):
        b = res[("ASEAN-5", vname)]["beta"]
        path = {}
        for t in pd.period_range("2026-01", "2026-12", freq="M"):
            path[str(t)] = sum(b.loc[(t - s).n] * v for s, v in surpr.loc["2026-01":].items() if 0 <= (t - s).n <= H)
        impl[vname] = pd.Series(path)
    stamp = dt.date.today().strftime("%Y%m%d")
    L = [f"# Geopolitics across ASEAN and emerging economies: panel local projections ({dt.date.today():%d %b %Y})", "",
         "**NOT FOR CITATION until reviewed** (Infinity GEM 0.3.7). Script: `preshock/geopolitics_panel_lp.py` "
         "(method and sources in its notes). Effect of a one-standard-deviation rise in a country's OWN geopolitical risk "
         "(Caldara-Iacoviello country index, standardised within country), with country and month fixed effects (so oil, US rates "
         "and world risk drop out); cumulative % change from the month before; 90% bands (Driscoll-Kraay).", ""]
    for (sname, vname), t in res.items():
        tt = t.loc[[0, 1, 3, 6, 9, 12]].reset_index()[["h", "beta", "low90", "high90", "n", "countries"]]
        tt.columns = ["months after", "effect (%)", "90% low", "90% high", "observations", "countries"]
        L += [f"## {sname}: {vname}", "", tt.to_markdown(index=False, floatfmt=".2f"), ""]
    L += ["## The Philippines in 2026 (ASEAN-5 responses)", "",
          "Philippine geopolitical risk, standardised (0 = its 2015-2025 average): "
          + ", ".join(f"{p.strftime('%b %Y')} {v:+.1f}" for p, v in surpr.loc["2026-01":].items()) + ".", "",
          pd.DataFrame(impl).to_markdown(floatfmt=".2f"), "",
          "Implied effect of the Philippines' own 2026 geopolitical risk on the peso and prices (%, level; no new shocks after the "
          "last month). Compare with the inflation VAR's geopolitical-risk column (`outputs/inflation_var_*.md`, table 3).", ""]
    out = ROOT / "outputs" / f"geopolitics_panel_lp_{stamp}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    pd.concat({f"{a} | {b}": v for (a, b), v in res.items()}, axis=1).to_csv(ROOT / "outputs" / f"geopolitics_panel_lp_{stamp}.csv")
    print("\n".join(L[-8:]))
    print("saved", out)


if __name__ == "__main__":
    main("--refresh" in sys.argv)
