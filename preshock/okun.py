"""Okun's law for the Philippines: how much employment moves with output (0.3.7, 16 Oct 2026, about 1 AM).

Why: the revised combined run (scenarios/combined_revised.py) lets every skill level lose work at a fixed real wage in the
short run, so all of the output fall lands on labour. Its 2026 labour input fell 8.75% for a 3.95% output gap, about two
to three times what PSA's Labor Force Survey shows. 16 Oct 2026: the jobs channel is calibrated to the data.
This script estimates the data's relation; dynamic.py's wage curve (option `wage_curve`, check WC1) is then set so the
model reproduces it (scenarios/calibrate_wage_curve.py).

Data (on file, PSA OpenSTAT):
  employment  LFS 0021B3FKEI2: labour-force participation rate x employment rate = employed per 100 people aged 15+ (the
              employment-to-population ratio). Survey rounds January, April, July and October (= quarters 1-4) so that
              the series is consistent before and after the monthly LFS of 2021.
  output      GDP at constant 2018 prices, quarterly (0012B5BEXQ1).
Model:  year-on-year change in ln(employment-to-population ratio) = a + e x year-on-year change in ln(real GDP) + u.
  e is the elasticity of employment (per person of working age) to output; the constant absorbs trend productivity
  growth. Newey-West standard errors (4 lags: the year-on-year changes overlap). Samples: 2006-2019 (before COVID and
  before the 2021 LFS redesign; central), 2006-2026 with 2020-2021 dropped, and 2006-2026 in full (check).
Literature (to open before citing): Okun (1962); Ball, Leigh and Loungani (2017, Journal of Money, Credit and Banking
49(7)) estimate Okun coefficients for 20 countries; developing Asia's are small, as the informal sector absorbs workers.
NOT FOR CITATION until reviewed. Run:  py preshock/okun.py
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

LFS = paths.DATA_RAW / "lfs" / "PSA_OpenSTAT_0021B3FKEI2_LFS_key_employment_rates_2005-2026.csv"
GDP = paths.DATA_RAW / "macro" / "PSA_OpenSTAT_GDP_by_expenditure_quarterly_2000-2026.csv"
ROUND = {"January": 1, "April": 2, "July": 3, "October": 4}


def data() -> pd.DataFrame:
    l = pd.read_csv(LFS, comment="#")
    l = l[l.Month.isin(ROUND)].replace(".", np.nan)
    l["q"] = l.Month.map(ROUND)
    l = l.set_index(["Year", "q"]).astype({c: float for c in l.columns if "Rate" in c})
    epop = l["Labor Force Participation Rate Both sexes"] * l["Employment Rate Both sexes"] / 100
    g = pd.read_csv(GDP, comment="#")
    g = g[(g.expenditure == "Gross Domestic Product") & g.valuation.str.contains("Constant")]
    g["q"] = g.quarter.str[1].astype(int)
    gdp = g.set_index(["year", "q"])["value_million_php"].astype(float)
    gdp.index.names = ["Year", "q"]
    d = pd.DataFrame({"epop": epop, "gdp": gdp}).dropna()
    d.index = pd.PeriodIndex([pd.Period(f"{y}Q{q}", freq="Q") for y, q in d.index])
    d = d.sort_index()
    d["d_epop"] = np.log(d.epop).diff(4) * 100
    d["d_gdp"] = np.log(d.gdp).diff(4) * 100
    return d.dropna()


def fit(d):
    import statsmodels.api as sm
    X = sm.add_constant(d["d_gdp"])
    r = sm.OLS(d["d_epop"], X).fit(cov_type="HAC", cov_kwds={"maxlags": 4})
    return {"elasticity e": r.params["d_gdp"], "s.e.": r.bse["d_gdp"], "constant": r.params["const"],
            "R2": r.rsquared, "quarters": int(r.nobs), "from": str(d.index.min()), "to": str(d.index.max())}


def estimates() -> pd.DataFrame:
    d = data()
    yr = d.index.year
    samples = {"2006-2019 (central)": d[yr <= 2019],
               "2006-2026, 2020-2021 dropped": d[(yr <= 2019) | (yr >= 2022)],
               "2006-2026, all quarters": d}
    return pd.DataFrame({k: fit(v) for k, v in samples.items()}).T


def central() -> float:
    return float(estimates().loc["2006-2019 (central)", "elasticity e"])


def main():
    t = estimates()
    print(t.to_string())
    d = data()
    L = [f"# Okun's law for the Philippines ({dt.date.today():%d %B %Y})", "",
         "**NOT FOR CITATION** (Infinity GEM 0.3.7). Script: `preshock/okun.py`. Year-on-year change in ln(employed per person "
         "aged 15+) on year-on-year change in ln(real GDP), quarterly (LFS rounds January/April/July/October; GDP at constant "
         "2018 prices); Newey-West standard errors, 4 lags.", "", t.to_markdown(floatfmt=".3f"), "",
         f"Latest quarters (year-on-year, %): " + "; ".join(f"{p}: employment-to-population {r.d_epop:+.2f}, GDP {r.d_gdp:+.2f}"
                                                           for p, r in d.tail(4).iterrows()), ""]
    out = paths.output_dir() / f"okun_{dt.date.today():%Y%m%d}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print("saved", out)


if __name__ == "__main__":
    main()
