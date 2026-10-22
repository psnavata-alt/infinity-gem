"""Scenario (Infinity GEM 0.3 options): the infrastructure freeze and the 2027 catch-up with the new dynamic options.

Question: how much do the two 0.3 upgrades change the long-run cost of the 2025 infrastructure slowdown and the gain
from the 2027 catch-up (scenarios/infrastructure_catchup.py)?
  1. Hybrid closure: short run in shock years, job gap halving each year afterwards (assumption).
  2. Public capital: lost or restored construction investment changes a public capital stock that raises
     productivity in all industries.

Parameters, each from a source opened on 1-2 Oct 2026:
  phi     0.083 (short run) and 0.122 (long run): Bom and Ligthart (2014), J. Economic Surveys 28(5): 889-916.
  kg_gdp  Philippine general government capital stock / GDP, 2019, IMF ICSD (published 1 July 2025;
          the IMF ICSD download (not distributed: IMF terms)): constant 2017 PPP dollars (IMF's own ratio) and current pesos.
  delta_g 3.52% (IMF ICSD 2021 Manual, Table 1, middle income);  e 0.77 (IMF CR 19/137, PIMA).
Shocks: -₱238.3 bn in 2025 (DBM), +₱208.7 bn in 2027 (DBM SAAODB), both as shares of PSA
2025 GDP applied to the 2023 SAM, as in infrastructure_catchup.py.

NOT FOR CITATION.
Run:  py scenarios/infrastructure_public_capital.py
"""
from _common import PSA_GDP, SAM_GDP_2023, Report, to_sam_units
import pandas as pd

from infinity_gem import paths
from infinity_gem.dynamic import DynamicCGE, PUBLIC_CAPITAL_DEFAULTS

ICSD = paths.DATA_RAW / "macro" / "IMF_ICSD_2025-07_all_countries_downloaded_2026-10-02.csv"
icsd = pd.read_csv(ICSD)
ph = icsd[icsd["COUNTRY"] == "Philippines"].set_index("SERIES_CODE")
KG = {"IMF ratio, constant 2017 PPP (2019)": float(ph.loc["PHL.CAPSTCK_S13_Q_POGDP_PT.A", "2019"]) / 100,
      "current pesos (2019)": float(ph.loc["PHL.CAPSTCK_S13_V_XDC.A", "2019"] / ph.loc["PHL.B1GQ_V_XDC.A", "2019"])}
PHI = {"short-run elasticity 0.083": 0.083, "long-run elasticity 0.122": 0.122}

FALL25, CATCHUP = 238.3, 208.7
cut25, catch = to_sam_units(FALL25, PSA_GDP[2025]), to_sam_units(CATCHUP, PSA_GDP[2025])
TO_2025 = PSA_GDP[2025] / SAM_GDP_2023

rep = Report("Infrastructure freeze and catch-up with the 0.3 dynamic upgrades (Infinity GEM 0.3 options)", "infrastructure_public_capital")
rep.p("**Uses Infinity GEM 0.3 opt-in upgrades; not for citation.** Shocks in 2023 SAM units: freeze "
      f"-₱{cut25:,.1f} bn (2025), catch-up +₱{catch:,.1f} bn (2027). Pesos below are 2025 pesos (same share of GDP).")
rep.p("Public capital stock / GDP, Philippines, 2019 (IMF ICSD): " + "; ".join(f"{k}: {v:.1%}" for k, v in KG.items()) + ".")

rows = []


def run(d, label, closure, pc):
    q0 = d.m.qinv[d.m.C.index("ccons")]
    qs = lambda x: {"qinv_scale": {"ccons": 1 + x / q0}}
    d.a["public_capital"] = pc
    if pc is not None:
        d.pc = dict(PUBLIC_CAPITAL_DEFAULTS, **pc)
    out = {}
    for name, sh in {"Freeze only (no action)": {2025: qs(-cut25)},
                     "Freeze + catch-up in 2027": {2025: qs(-cut25), 2027: qs(catch)}}.items():
        c = d.compare(d.base, d.scenario(sh))
        out[name] = c
        rows.append({"model": label, "closure": closure, "path": name,
                     "cumulative GDP gap 2025-2030 (₱ bn, 2025 pesos)": c.loc["cumulative", "gdp_gap_bn"] * TO_2025,
                     "GDP gap 2027 (%)": c.loc[2027, "gdp_gap_pct"], "GDP gap 2030 (%)": c.loc[2030, "gdp_gap_pct"]})
    return out


lr = DynamicCGE()
lr.baseline()
run(lr, "0.2 method: no public capital", "long run every year", None)
hy = DynamicCGE(hybrid=True)
hy.baseline()
run(hy, "Hybrid, no public capital", "hybrid", None)
paths_kept = {}
for kn, kg in KG.items():
    for pn, phi in PHI.items():
        paths_kept[(kn, pn)] = run(hy, f"Hybrid + public capital ({pn}; KG/GDP {kn})", "hybrid", {"phi": phi, "kg_gdp": kg})

tab = pd.DataFrame(rows)
rep.h("Summary")
rep.table(tab.set_index(["model", "path"]).drop(columns="closure"), floatfmt=",.3f")
freeze = tab[tab.path.str.startswith("Freeze only")].set_index("model")["cumulative GDP gap 2025-2030 (₱ bn, 2025 pesos)"]
both = tab[tab.path.str.startswith("Freeze +")].set_index("model")["cumulative GDP gap 2025-2030 (₱ bn, 2025 pesos)"]
rec = ((both - freeze) / -freeze * 100).rename("share of the freeze's cumulative loss recovered by the catch-up (%)")
rep.h("What the catch-up recovers")
rep.table(pd.DataFrame({"freeze only (₱ bn)": freeze, "freeze + catch-up (₱ bn)": both, rec.name: rec}), floatfmt=",.1f")
k0 = next(iter(paths_kept))
rep.h(f"Year by year: freeze only, {k0[1]}, KG/GDP {k0[0]}")
rep.table(paths_kept[k0]["Freeze only (no action)"], floatfmt=",.3f")
rep.p("Reading: the 0.2 method (long-run closure, no public capital) is the lower bound used in the 1 Oct slides. The "
      "hybrid closure adds the 2025 job and demand loss and its fading; public capital adds the productivity lost while "
      "roads and flood control are missing, which decays slowly (3.52% a year). A lower KG/GDP makes each peso of public "
      "investment a larger share of the stock, so the effect is larger. Assumptions to review: gap persistence 0.5 "
      "; the elasticities are mostly OECD estimates; e = 0.77 rests on perceived quality.")
rep.save()
print(tab.round(3).to_string())
print(rec.round(1).to_string())
