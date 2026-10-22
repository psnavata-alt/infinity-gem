"""Regression reference (check R0): the default results must stay those of Infinity GEM 0.2.

The reference values are FROZEN: they were computed with version 0.2 on 1 Oct 2026 (checks/reference_live.json).

`compute()` runs a fixed set of results with DEFAULT settings: the SAM multiplier, the I-O model, the static CGE in
its three closures, the dynamic CGE (infrastructure freeze) and the Simulator's short-run CGE with poverty. Check R0
recomputes them with this version and requires every value to match, so an upgrade cannot change earlier results
unless it is switched on by name. Public version: the Simulator's poverty result needs the FIES microdata (not
distributed) and the I-O results PSA's input-output tables (included); without those files they are not computed
(R0 names them).
"""
from __future__ import annotations

import importlib
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
REF = HERE / "reference_live.json"


def compute(root: Path) -> dict:
    for p in (str(root), str(root / "scenarios")):
        if p not in sys.path:
            sys.path.insert(0, p)
    import numpy as np
    from infinity_gem.sam import SAM
    from infinity_gem import paths
    from infinity_gem.multiplier import SAMMultiplier
    from infinity_gem.cge import CGE
    from infinity_gem.dynamic import DynamicCGE
    from infinity_gem.iomodel import IOTable
    out = {}
    mult = SAMMultiplier(SAM.load(paths.SAM_2023))
    out["sam_hh_mult_503020"] = mult.household_income_multiplier({"hhd-r1": .5, "hhd-r2": .3, "hhd-u1": .2})
    if paths.IO_2018.exists() and (paths.DATA_RAW / "lfs" / "LFS_2025_employed_by_major_industry.csv").exists():
        io = IOTable()
        q = io.quantity({"Construction": -238.3}, "domestic", gdp_other_year=28009.93)
        out["io_va_bn"], out["io_va_pct"] = q["va_bn"], q["va_pct_gdp"]
        out["io_jobs"] = float(io.jobs(q["industries"]["output (%)"])["job-equivalents"].sum())
        out["io_cpi_petrol10"] = io.price_summary({"Coke and refined petroleum products": 0.10})["cpi"]
    shock = {"pwm_scale": {"cchem": 1.3}, "remit_scale": 0.8, "qinv_scale": {"ccons": 0.8}}
    for name, kw in {"lr": {}, "sav": {"closure": "savings"},
                     "sr": {"closure": "keynesian", "unemployed": ("flab-n", "flab-p"), "capital": "fixed"}}.items():
        m = CGE.from_sam(**kw)
        b, s = m.solve(), m.solve(shock)
        out[f"cge_{name}_real_gdp_pct"] = (m.gdp(s)["real"] / m.gdp(b)["real"] - 1) * 100
        out[f"cge_{name}_cpi"] = float(s["CPI"])
        out[f"cge_{name}_emp"] = [float(x) for x in s["EMP"]]
        out[f"cge_{name}_eh"] = [float(x) for x in s["EH"]]
    d = DynamicCGE()
    base = d.baseline()
    cut = 1 - 238.3 / 28009.93 * 26160.604 / d.m.qinv[d.m.C.index("ccons")]
    sim = d.scenario({2025: {"qinv_scale": {"ccons": cut}}})
    cmp_ = d.compare(base, sim)
    out["dyn_gap_pct"] = [float(x) for x in cmp_["gdp_gap_pct"].iloc[:-1].values]
    out["dyn_cum_bn"] = float(cmp_.loc["cumulative", "gdp_gap_bn"])
    if paths.FIES_PUF.exists() and paths.FIES_POVLINES.exists():
        engines = importlib.import_module("app.engines")
        sr = engines.run_cge(engines.Shocks(construction_bn=-238.3), "short run")["summary"]
        out["sim_sr_gdp_pct"] = float(sr["Real GDP (%)"])
        out["sim_sr_new_poor"] = float(sr["New poor (persons, FIES 2023 base)"])
    return out


def compare(a: dict, b: dict, tol=1e-9):
    import numpy as np
    bad = []
    for k, v in a.items():
        x, y = np.asarray(v, float), np.asarray(b.get(k, np.nan), float)
        if x.shape != y.shape or not np.allclose(x, y, rtol=tol, atol=tol):
            bad.append(k)
    return bad


