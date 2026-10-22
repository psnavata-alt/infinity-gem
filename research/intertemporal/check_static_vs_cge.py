"""The forward-looking CGE (Stage 2), step 3c (iii) (17 Oct 2026): cross-check of the forward-looking model's within-year block against
Infinity GEM's static CGE (infinity_gem/cge.py, itself validated against IFPRI's GAMS model, check V-series).

Same data (the condensed 2023 SAM), same elasticities (0.8, 2.0, 2.0), matched closures:
  - cge.py: closure='investment' (real investment fixed, saving rates adjust), capital='fixed' (each activity keeps its
    capital), labour and land fully employed and mobile, fixed real government consumption, foreign saving fixed in
    foreign currency, CPI numeraire, exchange rate flexible;
  - pf_cge9.CGE9.static_equilibrium: the same, with foreign currency as numeraire (exchange rate 1) instead of the CPI.
    A CGE's real results do not depend on the numeraire (homogeneity, check C3), so quantities and RELATIVE prices
    must agree; price levels are compared after dividing by the same CPI (cge.py's Laspeyres weights).
  - Households: (1) one household (cge.py run on the SAM with its ten groups aggregated, SAM.aggregate); (2) and (3)
    the ten groups on both sides (CGE9(households='groups') uses cge.py's institution formulas; its saving-rate
    factor mpsadj is cge.py's investment-closure variable). (3) also uses calib='pwt': within a year capital and the
    fixed factors are both fixed, so the static results must still equal cge.py's (capital rents are compared as
    capital plus fixed-factor income, cge.py's 'fcap').
Shocks: world price of chemical and petroleum imports +20%; agricultural productivity +5%; government consumption
+10%; world price of other-manufacturing exports -10%; foreign saving -10%; labour supply +2% (all three types);
remittances to households -10%.
Run:  py research/intertemporal/check_static_vs_cge.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
from infinity_gem.cge import CGE          # noqa: E402
from infinity_gem.sam import SAM          # noqa: E402
import pf_cge9 as P                   # noqa: E402

SECT = P.SECT


def ratio(a, b):
    """a / b, and 1 where the base value is 0 (e.g. utilities have no exports or imports)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    return np.where(np.abs(b) > 1e-12, a / np.where(np.abs(b) > 1e-12, b, 1.0), 1.0)


def condensed_sam(one_household):
    t = pd.read_csv(P.SAM_CSV, index_col=0)
    sam = SAM(t, {}, "condensed 2023 SAM (validation/ifpri/out)")
    return sam.aggregate({h: "hhd-all" for h in P.HH}) if one_household else sam


def cge_measures(m, sol):
    v = sol.v
    cpi = v["CPI"]
    ik = m.F.index("fcap")
    out = dict(
        X=ratio(v["QA"], m.QA0), E=ratio(v["QE"], m.QE0), M=ratio(v["QM"], m.QM0),
        Q=ratio(v["QQ"], m.QQ0), H=ratio(v["QH"].sum(axis=1), m.sam.table.loc[m.C, m.H].sum(axis=1).values),
        pq=v["PQ"] / cpi, w=v["WF"][:3] / cpi, rk=v["W"][ik] / cpi, exr=v["EXR"] / cpi, pd=v["PDS"] / cpi)
    if len(m.H) > 1:
        out["EH"] = v["EH"] / m.EH0 / cpi                 # real spending of each household group
    return out


def pf_measures(m, v, s):
    pq_rel = s["pq"][:, 0] / m.pq0
    cpi = float(m.shc @ pq_rel)                      # Laspeyres, household consumption weights (as cge.py's cwts)
    # capital rent by activity as cge.py sees it: capital AND the fixed factor (cge.py has one capital account, 'fcap')
    rent = (v["rk"][:, 0] * m.K0 + s["wff"][:, 0] * m.FF0) / (m.Rk * m.K0 + m.FF0)
    out = dict(
        X=ratio(v["X"][:, 0], m.X0), E=ratio(s["E"][:, 0], m.E0), M=ratio(s["M"][:, 0], m.M0),
        Q=ratio(s["Q"][:, 0], m.Q0), H=ratio(s["Cd"][:, 0], m.shc * m.C0 / m.pq0),
        pq=pq_rel / cpi, w=v["w"][:, 0] / cpi, rk=rent / cpi, exr=1.0 / cpi, pd=v["pd"][:, 0] / cpi)
    if m.households == "groups":
        out["EH"] = s["EH"][:, 0] / m.EH0 / cpi
    return out


CONFIGS = [  # (label, CGE9 options, cge.py on one household?)
    ("one household, SAM calibration (step 3b)", dict(), True),
    ("ten household groups, SAM calibration", dict(households="groups"), False),
    ("ten household groups, data calibration with fixed factors and growth", dict(households="groups", calib="pwt"), False),
]


def run_config(label, opts, one):
    g = CGE(condensed_sam(one), closure="investment", capital="fixed")
    base = g.solve()
    assert base.ok, base.message
    m = P.CGE9(**opts)
    ic, ia, io = SECT.index("chem"), SECT.index("agri"), SECT.index("oman")
    cases = [
        ("chemical and petroleum import price +20%", {"pwm_scale": {"cchem": 1.2}}, lambda x: x.__setitem__(9 + ic, 1.2)),
        ("agricultural productivity +5%", {"tfp_scale": {"aagri": 1.05}}, lambda x: x.__setitem__(ia, 1.05)),
        ("government consumption +10%", {"qg_scale": 1.1}, lambda x: x.__setitem__(27, 1.1)),
        ("other-manufacturing export price -10%", {"pwe_scale": {"coman": 0.9}}, lambda x: x.__setitem__(18 + io, 0.9)),
        ("foreign saving -10%", {"fsav_scale": 0.9}, lambda x: x.__setitem__(28, m.NF0 - 0.1 * m.FSAV0)),
        ("labour supply +2%", {"qfs_scale": {"flab-n": 1.02, "flab-p": 1.02, "flab-s": 1.02}}, lambda x: x.__setitem__(29, 1.02)),
        ("remittances -10%", {"remit_scale": 0.9}, lambda x: x.__setitem__(30, 0.9)),
    ]
    rows = []
    for name, spec, fn in cases:
        sol = g.solve(spec)
        assert sol.ok, (name, sol.message)
        x = m.x0.copy(); fn(x)
        v, s, res = m.static_equilibrium(x)
        a, b = cge_measures(g, sol), pf_measures(m, v, s)
        diffs = {k: float(np.abs((a[k] - b[k]) * 100).max()) for k in a}   # percentage points of the % change
        rows.append(dict(config=label, shock=name, **{f"{k} (pp)": diffs[k] for k in a}, largest=max(diffs.values()),
                         real_cons_cge=float((a["H"] @ (g.sam.table.loc[g.C, g.H].sum(axis=1).values)) / g.sam.table.loc[g.C, g.H].values.sum() * 100 - 100)))
    return rows


KEYNES_CONFIGS = [  # Build 2 (18 Oct 2026): the short-run closure. (label, CGE9 options)
    ("Keynesian year, ten groups, SAM calibration", dict(households="groups")),
    ("Keynesian year, ten groups, data calibration with fixed factors and growth", dict(households="groups", calib="pwt")),
]


def run_keynesian(label, opts):
    """cge.py closure='keynesian' (all three labour types unemployed at fixed peso wages, capital fixed, exchange rate fixed,
    foreign saving free) against CGE9.static_keynesian. Both use the exchange rate as numeraire, so employment is compared
    too ('emp', percentage points of the % change)."""
    g = CGE(condensed_sam(False), closure="keynesian", unemployed=tuple(P.LAB), capital="fixed", wage="nominal")
    base = g.solve()
    assert base.ok, base.message
    m = P.CGE9(**opts)
    ic, ia, io = SECT.index("chem"), SECT.index("agri"), SECT.index("oman")
    cases = [
        ("chemical and petroleum import price +20%", {"pwm_scale": {"cchem": 1.2}}, lambda x: x.__setitem__(9 + ic, 1.2)),
        ("agricultural productivity +5%", {"tfp_scale": {"aagri": 1.05}}, lambda x: x.__setitem__(ia, 1.05)),
        ("government consumption -10%", {"qg_scale": 0.9}, lambda x: x.__setitem__(27, 0.9)),
        ("other-manufacturing export price -10%", {"pwe_scale": {"coman": 0.9}}, lambda x: x.__setitem__(18 + io, 0.9)),
        ("remittances -10%", {"remit_scale": 0.9}, lambda x: x.__setitem__(30, 0.9)),
    ]
    rows = []
    for name, spec, fn in cases:
        sol = g.solve(spec)
        assert sol.ok, (name, sol.message)
        x = m.x0.copy(); fn(x)
        v, s, res = m.static_keynesian(x)
        a, b = cge_measures(g, sol), pf_measures(m, v, s)
        a["emp"] = np.array([sol.v["EMP"][g.F.index(f)] / base.v["EMP"][g.F.index(f)] for f in P.LAB])
        b["emp"] = s["employment"]
        diffs = {k: float(np.abs((a[k] - b[k]) * 100).max()) for k in a}
        rows.append(dict(config=label, shock=name, **{f"{k} (pp)": diffs[k] for k in a}, largest=max(diffs.values()),
                         real_cons_cge=float((a["H"] @ (g.sam.table.loc[g.C, g.H].sum(axis=1).values)) / g.sam.table.loc[g.C, g.H].values.sum() * 100 - 100)))
    return rows


def main(configs=CONFIGS, keynes=KEYNES_CONFIGS):
    rows = []
    for label, opts, one in configs:
        rows += run_config(label, opts, one)
    for label, opts in keynes:
        rows += run_keynesian(label, opts)
    df = pd.DataFrame(rows).set_index(["config", "shock"])
    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 30)
    print("Largest gap between cge.py and the forward-looking model's static block, in percentage points of the % change "
          "(X output, E exports, M imports, Q composite supply, H consumption by commodity, pq/pd relative prices, w wages, "
          "rk capital rents by activity, exr real exchange rate, EH real spending of each household group); real_cons_cge = "
          "cge.py's change in real consumption (%), for scale:")
    print(df.to_string(float_format=lambda z: f"{z:.1e}" if abs(z) < 1e-3 else f"{z:.3f}"))
    worst = float(df["largest"].max())
    ok = worst < 1e-6
    print(f"\nLargest gap over all configurations, shocks and variables: {worst:.2e} pp -> {'PASS' if ok else 'FAIL'} "
          f"(tolerance 1e-6 pp)")
    return df, ok


if __name__ == "__main__":
    main()
