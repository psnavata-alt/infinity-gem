"""How much do Infinity GEM's results depend on the elasticities? (added in 0.3)

Runs the main September 2026 policy shocks under four elasticity sets (infinity_gem/elasticities.py) and two closures:
  sets      default (0.8 / 2.0 / 2.0), gtap (GTAP 9 standard), ph (Philippine Armington estimates where valid, GTAP
            elsewhere), ph_pcgem_cet (ph with PCGEM's assumed CET values)
  closures  short run (Keynesian: low/medium-skill unemployment, fixed capital), long run (investment closure)
  shocks    infrastructure freeze -₱238.3 bn (2025 pesos, construction investment); world oil prices +20% (petroleum
            share of chemical imports 0.6, as in the Simulator); remittances -10%
NOT FOR CITATION until reviewed. Sources: docs/guides/08_PARAMETERS_AND_SOURCES.md.
Run:  py scenarios/elasticity_sensitivity.py
"""
from _common import PSA_GDP, Report, to_sam_units
import pandas as pd

from infinity_gem.cge import CGE
from infinity_gem.elasticities import elasticity_set
from infinity_gem.microsim import Microsim

SETS = ["default", "gtap", "ph", "ph_pcgem_cet"]
CLOSURES = {"short run": dict(closure="keynesian", unemployed=("flab-n", "flab-p"), capital="fixed"), "long run": {}}
ms = Microsim()

rows = []
for name in SETS:
    el = elasticity_set(name)
    for cl, kw in CLOSURES.items():
        m = CGE.from_sam(elasticities=el, **kw)
        b = m.solve()
        assert b.ok, (name, cl)
        q0 = m.qinv[m.C.index("ccons")]
        shocks = {"Infrastructure freeze -₱238.3 bn": {"qinv_scale": {"ccons": 1 - to_sam_units(238.3, PSA_GDP[2025]) / q0}},
                  "World oil prices +20%": {"pwm_scale": {"cchem": 1 + 0.20 * 0.6}},
                  "Remittances -10%": {"remit_scale": 0.90}}
        for sh, spec in shocks.items():
            s = m.solve(spec)
            assert s.ok, (name, cl, sh)
            pct = lambda a, z: (z / a - 1) * 100
            rows.append({"set": name, "closure": cl, "shock": sh,
                         "real GDP (%)": pct(m.gdp(b)["real"], m.gdp(s)["real"]),
                         "CPI (%)": pct(b["CPI"], s["CPI"]),
                         "real household consumption (%)": pct(b["QH"].sum(), s["QH"].sum()),
                         "low-skill employment (%)": pct(b["EMP"][0], s["EMP"][0]),
                         "new poor (FIES 2023)": ms.from_cge(m, b, s)["new_poor"]})
df = pd.DataFrame(rows)
rep = Report("Elasticity sensitivity of the main September 2026 results (Infinity GEM 0.3 options)", "elasticity_sensitivity")
rep.p("**Uses Infinity GEM 0.3 opt-in upgrades; not for citation.** Elasticity sets and sources: `infinity_gem/elasticities.py`, "
      "`docs/guides/08_PARAMETERS_AND_SOURCES.md` §3. 'default' is what Infinity GEM 0.2 (and every published result) uses.")
for sh in df.shock.unique():
    rep.h(sh)
    t = df[df.shock == sh].set_index(["closure", "set"]).drop(columns="shock")
    rep.table(t, floatfmt=",.3f")
rep.save()
pd.set_option("display.width", 200)
print(df.round(3).to_string(index=False))
