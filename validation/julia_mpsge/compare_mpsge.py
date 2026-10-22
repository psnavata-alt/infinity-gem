"""Julia/MPSGE comparison, step 3: Infinity GEM against the Julia port of Rutherford's MPSGE IFPRI model, same SAM, same
experiment (all tariffs abolished), quantities and relative prices.

Matched variables (both are % changes from the benchmark; quantities do not depend on the numeraire):
  Y[s]   activity level                      <-> QA
  A[g]   Armington (composite) supply         <-> QQ
  X[g]   marketed output (CET aggregate)      <-> QX
  CD[h]  household utility (Cobb-Douglas)     <-> prod(QH ** beta) per household
  ID     real investment                      <-> sum(QINV) (fixed proportions)
  PFX / CPI  real exchange rate               <-> EXR / CPI (CPI weights = household consumption shares)
  PF[f] / CPI factor prices                   <-> WF / CPI
Run:  py validation/julia_mpsge/compare_mpsge.py <mpsge_results.csv> [closure]
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
B = runpy.run_path(str(HERE / "build_mpsge_inputs.py"), run_name="b")


def mpsge_table(path, run_prefix="savings_fixedGS"):
    d = pd.read_csv(path)
    b = d[d.run == f"{run_prefix}|benchmark"].set_index("var").value
    s = d[d.run == f"{run_prefix}|no_tariffs"].set_index("var").value
    return b, s


def ours(closure="savings", omega_t=2.0, matched=False):
    m = B["comparison_model"](closure=closure, elasticities={"sigma_va": 0.8, "sigma_q": 2.0, "omega_t": omega_t})
    spec = {"tm_scale": 0.0}
    if matched:
        spec, resid = matched_spec(m, spec)
        print("matched closure:", {k: round(v, 6) for k, v in spec.items() if k != "tm_scale"}, "residuals", resid)
    b, s = m.solve(), m.solve(spec)
    nm = lambda c: c[1:]
    r = {}
    for i, a in enumerate(m.A):
        r[f"Y[{nm(a)}]"] = s["QA"][i] / b["QA"][i]
    for i, c in enumerate(m.C):
        if b["QQ"][i] > 0:
            r[f"A[{nm(c)}]"] = s["QQ"][i] / b["QQ"][i]
        if b["QX"][i] > 0:
            r[f"X[{nm(c)}]"] = s["QX"][i] / b["QX"][i]
    beta = m.beta                                    # budget shares (commodity x household)
    for j, h in enumerate(m.H):
        u = lambda sol: np.exp((beta[:, j] * np.log(np.maximum(sol["QH"][:, j], 1e-300))).sum())
        r[f"CD[{h}]"] = u(s) / u(b)
    r["ID"] = s["QINV"].sum() / b["QINV"].sum()
    cpi = lambda sol: float(np.ravel(sol["CPI"])[0]) if "CPI" in sol.keys() else 1.0
    exr = lambda sol: float(np.ravel(sol["EXR"])[0])
    r["PFX/CPI"] = (exr(s) / exr(b))
    for k, f in enumerate(m.F):
        r[f"PF[{f}]/CPI"] = float(np.atleast_1d(s["WF"])[k] / np.atleast_1d(b["WF"])[k]) if np.ndim(s["WF"]) == 1 else np.nan
    return pd.Series(r) * 100 - 100, m


def matched_spec(m, spec):
    """Rutherford's closure (eqyield=0, fixedGS=1) holds each household's saving and direct tax fixed in REAL terms
    (hs0*DEMAND in investment goods, dtax0*DTAX in government goods). Infinity GEM's savings closure holds the RATES fixed.
    To test whether that explains the remaining gaps, choose a common saving-rate adjuster (mpsadj) and a common
    direct-tax-rate scale (tins_scale) so that total real household saving and total real household direct taxes stay
    at the benchmark (aggregate match; enterprise saving stays rate-based)."""
    from scipy.optimize import fsolve
    b = m.solve()
    pinv = lambda s: float(s["PQ"] @ m.qinv) / m.qinv.sum()
    pg = lambda s: float(s["PQ"] @ m.qg) / m.qg.sum()
    tins = m.tins
    hs_b, dt_b = b["HSAV"].sum() / pinv(b), (tins * b["YH"]).sum() / pg(b)
    def f(z):
        s = m.solve({**spec, "mpsadj": z[0], "tins_scale": z[1]})
        return [s["HSAV"].sum() / pinv(s) / hs_b - 1, (tins * z[1] * s["YH"]).sum() / pg(s) / dt_b - 1]
    z = fsolve(f, [0.0, 1.0], xtol=1e-12)
    return {**spec, "mpsadj": float(z[0]), "tins_scale": float(z[1])}, f(z)


def compare(path, closure="savings", omega_t=2.0, matched=False):
    mb, ms = mpsge_table(path)
    o, m = ours(closure, omega_t, matched)
    q = (ms / mb * 100 - 100)
    # real exchange rate and factor prices relative to a CPI built from household consumption shares
    w = pd.Series(m.beta.sum(axis=1) if False else (m.sam.table.loc[m.C, m.H].sum(axis=1)), index=m.C)
    w = w / w.sum()
    pa = lambda v: sum(w[c] * v[f"PA[{c[1:]}]"] for c in m.C if f"PA[{c[1:]}]" in v.index)
    cpi_b, cpi_s = pa(mb), pa(ms)
    q["PFX/CPI"] = (ms["PFX"] / cpi_s) / (mb["PFX"] / cpi_b) * 100 - 100
    for f in m.F:
        q[f"PF[{f}]/CPI"] = (ms[f"PF[{f}]"] / cpi_s) / (mb[f"PF[{f}]"] / cpi_b) * 100 - 100
    keys = [k for k in o.index if k in q.index and np.isfinite(o[k])]
    t = pd.DataFrame({"infinity_gem_pct": o[keys], "mpsge_pct": q[keys]})
    t["diff_pp"] = t.infinity_gem_pct - t.mpsge_pct
    return t


if __name__ == "__main__":
    path = sys.argv[1]
    cl = sys.argv[2] if len(sys.argv) > 2 else "savings"
    om = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0
    mt = len(sys.argv) > 4 and sys.argv[4] == "matched"
    t = compare(path, cl, om, mt)
    (HERE / "out").mkdir(exist_ok=True)
    t.to_csv(HERE / "out" / f"comparison_no_tariffs_{cl}_omega{om:g}{'_matched' if mt else ''}.csv")
    grp = t.index.str.extract(r"^([A-Za-z]+)", expand=False)
    print(t.groupby(grp.values).diff_pp.agg(lambda x: x.abs().max()).rename("largest |gap| pp").round(4).to_string())
    print(t.loc[[k for k in ("ID", "PFX/CPI") if k in t.index]].round(4).to_string())
    print(t[t.index.str.startswith("CD")].round(4).to_string())
