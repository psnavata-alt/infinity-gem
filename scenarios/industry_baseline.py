"""Industry baseline, PSA labour growth and LES demand: the 2027 catch-up on each baseline.

Baselines (all: documented baseline = DBCC growth, PWT depreciation and capital, PSA labour growth by skill; capital by
industry (putty-clay); hybrid closure):
  A  one productivity rate for all industries (as in infrastructure_full_dynamic.py, step D, now with PSA labour)
  B  + industry baseline: each PSA industry grows as PSA reports for 2024 and 2025 (contains the 2025 construction slump)
  C  + LES household demand (Briones et al. 2023)
Scenario: catch-up, +₱208.7 bn construction investment in 2027 (2025 pesos, same share of GDP). The 2025 freeze is NOT
added on top of B or C: their baseline already contains the actual slump.
NOT FOR CITATION until reviewed. Sources: docs/guides/08_PARAMETERS_AND_SOURCES.md.
Run:  py scenarios/industry_baseline.py
"""
from _common import PSA_GDP, SAM_GDP_2023, Report, to_sam_units
import numpy as np
import pandas as pd

from infinity_gem.demand import les_briones2023
from infinity_gem.dynamic import DynamicCGE, documented_baseline, psa_industry_growth, psa_labour_growth, PSA_INDUSTRIES

TO_2025 = PSA_GDP[2025] / SAM_GDP_2023
catch = to_sam_units(208.7, PSA_GDP[2025])
common = dict(capital_allocation="putty-clay", hybrid=True, **documented_baseline())
STEPS = {"A  one productivity rate": dict(common),
         "B  + industry baseline (PSA 2024-2025)": dict(common, industry_targets=psa_industry_growth()),
         "C  + LES household demand": dict(common, industry_targets=psa_industry_growth(), les=les_briones2023())}

rows, base_tabs, models = [], {}, {}
for label, kw in STEPS.items():
    d = DynamicCGE(**kw)
    b = d.baseline()
    q0 = d.m.qinv[d.m.C.index("ccons")]
    sim = d.scenario({2027: {"qinv_scale": {"ccons": 1 + catch / q0}}})
    c = d.compare(b, sim)
    ia = d.m.A.index("acons")
    rows.append({"baseline": label,
                 "real GDP growth 2024 / 2025 (%)": f"{b.table.loc[2024, 'real_gdp_growth_pct']:.2f} / {b.table.loc[2025, 'real_gdp_growth_pct']:.2f}",
                 "catch-up: GDP gain 2027 (%)": c.loc[2027, "gdp_gap_pct"],
                 "catch-up: GDP gain 2030 (%)": c.loc[2030, "gdp_gap_pct"],
                 "catch-up: cumulative GDP gain 2027-2030 (₱ bn, 2025 pesos)": c.loc[2027:2030, "gdp_gap_bn"].sum() * TO_2025,
                 "catch-up: construction output 2027 (%)": (sim.solutions[2027]["QA"][ia] / b.solutions[2027]["QA"][ia] - 1) * 100})
    base_tabs[label], models[label] = b, d

tab = pd.DataFrame(rows).set_index("baseline")
dB, bB = models["B  + industry baseline (PSA 2024-2025)"], base_tabs["B  + industry baseline (PSA 2024-2025)"]
tg = psa_industry_growth()
ind = []
for n, acts in PSA_INDUSTRIES.items():
    ix = [dB.m.A.index(a) for a in acts if a in dB.m.A]
    r = {"industry": n}
    for t in (2024, 2025):
        prev = np.asarray(bB.tfp[t - 1], float) if np.ndim(bB.tfp[t - 1]) else np.full(len(dB.m.A), float(bB.tfp[t - 1]))
        r[f"PSA real GVA growth {t} (%)"] = tg[t][n]
        r[f"TFP change {t} (%)"] = (float(np.asarray(bB.tfp[t])[ix[0]] / prev[ix[0]]) - 1) * 100
    ind.append(r)
ind = pd.DataFrame(ind).set_index("industry")
levers = pd.DataFrame({t: bB.demand[t] for t in (2024, 2025)})
lab = pd.DataFrame(psa_labour_growth()).T * 100

rep = Report("Industry baseline, PSA labour growth and LES demand (Infinity GEM 0.3 options)", "industry_baseline")
rep.p("**Uses Infinity GEM 0.3 opt-in upgrades; not for citation.** Baseline B and C contain the actual 2025 construction slump, so "
      "the 2025 freeze is not added on top; the catch-up is the policy shock. 2025 pesos (same share of GDP).")
rep.h("Catch-up (+₱208.7 bn in 2027) on each baseline")
rep.table(tab, floatfmt=",.3f")
rep.h("Industry baseline: PSA growth reproduced, and the productivity change it requires")
rep.p("Construction, public administration, trade and finance are moved by their demand lever (table below), so their "
      "TFP change is zero.")
rep.table(ind, floatfmt=",.2f")
rep.h("Demand and intensity levers (relative to the economy-wide path)")
rep.p("qinv:ccons = real construction investment; qg:cpadm = real government consumption of public administration; "
      "use:ctrad / use:cfsrv = trade and financial services used per unit of output (input-intensity twist).")
rep.table(levers, floatfmt=",.4f")
rep.h("Labour growth by skill (%), PSA LFS 2024-2026 and population projections 2027-2030")
rep.table(lab, floatfmt=",.2f")
rep.save()
pd.set_option("display.width", 220)
print(tab.round(3).to_string())
print(ind.round(2).to_string())
print(levers.round(4).to_string())
