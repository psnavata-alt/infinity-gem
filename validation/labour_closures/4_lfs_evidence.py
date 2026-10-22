"""Labour-market evidence from PSA's Labor Force Survey (OpenSTAT 0021B3FKEI2, 0161B3FADB2): slack, and do nominal wages fall?"""
import sys, pandas as pd, numpy as np
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
D = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).resolve().parents[2] / "data" / "raw" / "lfs")
r = pd.read_csv(D + "/PSA_OpenSTAT_0021B3FKEI2_LFS_key_employment_rates_2005-2026.csv", comment="#")
r = r.replace(".", np.nan)
cols = {"Unemployment Rate Both sexes": "unemployment %", "Underemployment Rate Both sexes": "underemployment %"}
a = r[r.Month == "Annual"].set_index("Year")[list(cols)].astype(float).rename(columns=cols)
print("1. Slack (LFS annual, both sexes):"); print(a.loc[2018:2025].to_string())
m = r[(r.Year == 2026) & (r.Month != "Annual")].dropna(subset=list(cols)).set_index("Month")[list(cols)].astype(float).rename(columns=cols)
print("   2026 so far:"); print(m.to_string())
p = pd.read_csv(D + "/PSA_OpenSTAT_0161B3FADB2_LFS_average_daily_basic_pay_by_industry_2016-2026.csv", comment="#").set_index("Major Industry Group")
p = p.replace(".", np.nan).astype(float)
ann = p[[c for c in p.columns if c.endswith("Annual")]]; ann.columns = [int(c.split()[0]) for c in ann.columns]
g = ann.pct_change(axis=1) * 100
print("\n2. Average daily basic pay, wage and salary workers (nominal pesos, annual):")
print(ann.loc["TOTAL"].round(2).to_string())
print("   growth %:", " ".join(f"{y}:{v:+.1f}" for y, v in g.loc["TOTAL"].dropna().items()))
ind = g[g.index.str.startswith("....")]
print(f"\n3. Industry-years with a nominal FALL in annual average pay, 2017-2025: {(ind < 0).sum().sum()} of {ind.notna().sum().sum()}")
print("   in 2020 (GDP -9.5%):", ", ".join(f"{i.strip('.')} {v:+.1f}%" for i, v in ind[2020].sort_values().items() if v < 0) or "none")
print("   2020 growth, all wage workers:", f"{g.loc['TOTAL', 2020]:+.1f}%", "| median industry:", f"{ind[2020].median():+.1f}%")
q = p.loc["TOTAL", [c for c in p.columns if not c.endswith("Annual")]].dropna()
print("\n4. Quarterly rounds (TOTAL):", " ".join(f"{k}:{v:.0f}" for k, v in q.loc["2019 January":].items()))
