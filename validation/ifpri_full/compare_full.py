"""Outside review, step 3: compare IFPRI's full-size results (gams_ph/ifpri_results.csv, written by the
partner's GAMS run of 1DMODEL_PH.GMS) with Infinity GEM's (out/infinity_gem_results_full.csv, written by
build_full_package.py). Needs only pandas: it does not run either model.
Writes out/comparison_full_infinity_gem_vs_ifpri.csv and prints the key results and the largest differences.
Run:  py validation/ifpri_full/compare_full.py
"""
from pathlib import Path
import sys

import pandas as pd

HERE = Path(__file__).resolve().parent
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f_ifp = HERE / "gams_ph" / "ifpri_results.csv"
if not f_ifp.exists():
    sys.exit(f"{f_ifp} not found: run GAMS first (gams ph_data.gms, then gams 1DMODEL_PH.GMS, in gams_ph/).")
ifp = pd.read_csv(f_ifp)
sep = pd.read_csv(HERE / "out" / "infinity_gem_results_full.csv")
for d in (ifp, sep):
    d["closure"] = d["closure"].str.upper(); d["shock"] = d["shock"].str.upper()
bad = ifp[(ifp.group == "STATUS") & (ifp["item"] == "MODEL") & (ifp.value.round() != 1)]
if not bad.empty:
    print("WARNING: IFPRI's model did not report an optimal solution (MODELSTAT 1) for:", bad[["closure", "shock"]].values.tolist())
key = ["closure", "group", "item"]
pct = lambda d: (d[d.shock != "BASE"].merge(d[d.shock == "BASE"][key + ["value"]], on=key, suffixes=("", "_base"))
                 .assign(pct=lambda x: (x.value / x.value_base - 1) * 100))
res = (pct(sep[sep.group != "STATUS"]).merge(pct(ifp[ifp.group != "STATUS"]), on=key + ["shock"], suffixes=("_own", "_ifpri"))
       [key + ["shock", "pct_own", "pct_ifpri"]].rename(columns={"pct_own": "infinity_gem_pct", "pct_ifpri": "ifpri_pct"}))
res["diff_pp"] = res.infinity_gem_pct - res.ifpri_pct
res.to_csv(HERE / "out" / "comparison_full_infinity_gem_vs_ifpri.csv", index=False)
pd.set_option("display.width", 200)
macro = res[(res.group == "MACRO") & res["item"].isin(["RGDP", "RCONS", "EXR"])]
print(macro.pivot_table(index=["closure", "shock"], columns="item", values=["infinity_gem_pct", "ifpri_pct"]).round(4).to_string())
print("\nLargest absolute difference (percentage points) by closure and shock:")
print(res.assign(absd=res.diff_pp.abs()).groupby(["closure", "shock"]).absd.max().round(4).to_string())
n = len(res)
print(f"\n{n} comparisons; within 0.01 pp: {(res.diff_pp.abs() < 0.01).sum()}; within 0.1 pp: {(res.diff_pp.abs() < 0.1).sum()}; "
      f"largest {res.diff_pp.abs().max():.4f} pp")
