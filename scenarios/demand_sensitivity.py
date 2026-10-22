"""Household demand: Cobb-Douglas against the Linear Expenditure System (added in 0.3).

Runs the main September 2026 policy shocks under three household demand settings and two closures:
  demand    Cobb-Douglas (Infinity GEM 0.2, every published result); LES with Briones et al. (2023) income elasticities and
            the Frisch parameter fitted to all their own-price elasticities ("LES, fit all", central) or to the food
            ones only ("LES, fit food"; the econometric estimates); benchmark: USDA ERS income elasticities and Frisch
            for the Philippines (Muhammad et al. 2011, 2005 ICP; "LES, USDA ERS"); and GTAP 10 (2014, CDE elasticities,
            Frisch fitted to its own-price elasticities; "LES, GTAP 10"). infinity_gem/demand.py.
  closures  short run (Keynesian: low/medium-skill unemployment, fixed capital), long run (investment closure)
  shocks    infrastructure freeze -₱238.3 bn (2025 pesos, construction investment); world oil prices +20% (petroleum
            share of chemical imports 0.6, as in the Simulator); remittances -10%
NOT FOR CITATION until reviewed. Sources: docs/guides/08_PARAMETERS_AND_SOURCES.md.
Run:  py scenarios/demand_sensitivity.py
"""
from _common import PSA_GDP, Report, to_sam_units
import pandas as pd

from infinity_gem.cge import CGE
from infinity_gem.demand import les_briones2023, les_gtap10, les_usda2011
from infinity_gem.microsim import Microsim

DEMAND = {"Cobb-Douglas": None, "LES, fit all": les_briones2023("all"), "LES, fit food": les_briones2023("food"),
          "LES, USDA ERS (benchmark)": les_usda2011(), "LES, GTAP 10 (benchmark)": les_gtap10()}
CLOSURES = {"short run": dict(closure="keynesian", unemployed=("flab-n", "flab-p"), capital="fixed"), "long run": {}}
ms = Microsim()

rows, frisch = [], {}
for name, les in DEMAND.items():
    for cl, kw in CLOSURES.items():
        m = CGE.from_sam(les=les, **kw)
        b = m.solve()
        assert b.ok, (name, cl)
        if les is not None and cl == "long run":
            frisch[name] = dict(zip(m.H, m.les["frisch"].round(2)))
        q0 = m.qinv[m.C.index("ccons")]
        shocks = {"Infrastructure freeze -₱238.3 bn": {"qinv_scale": {"ccons": 1 - to_sam_units(238.3, PSA_GDP[2025]) / q0}},
                  "World oil prices +20%": {"pwm_scale": {"cchem": 1 + 0.20 * 0.6}},
                  "Remittances -10%": {"remit_scale": 0.90}}
        for sh, spec in shocks.items():
            s = m.solve(spec)
            assert s.ok, (name, cl, sh)
            pct = lambda a, z: (z / a - 1) * 100
            ifood = m.C.index("cfood")
            rows.append({"demand": name, "closure": cl, "shock": sh,
                         "real GDP (%)": pct(m.gdp(b)["real"], m.gdp(s)["real"]),
                         "CPI (%)": pct(b["CPI"], s["CPI"]),
                         "real household consumption (%)": pct(b["QH"].sum(), s["QH"].sum()),
                         "processed food consumed (%)": pct(b["QH"][ifood].sum(), s["QH"][ifood].sum()),
                         "low-skill employment (%)": pct(b["EMP"][0], s["EMP"][0]),
                         "new poor (FIES 2023)": ms.from_cge(m, b, s)["new_poor"]})
df = pd.DataFrame(rows)
rep = Report("Household demand: Cobb-Douglas and LES (Infinity GEM 0.3 options)", "demand_sensitivity")
rep.p("**Uses Infinity GEM 0.3 opt-in upgrades; not for citation.** LES parameters and sources: `infinity_gem/demand.py`, "
      "`docs/guides/08_PARAMETERS_AND_SOURCES.md` §3. 'Cobb-Douglas' is what Infinity GEM 0.2 (and every published result) uses.")
rep.h("Fitted Frisch parameters by household group (long-run calibration; identical in the short run)")
rep.table(pd.DataFrame(frisch), floatfmt=".2f")
for sh in df.shock.unique():
    rep.h(sh)
    t = df[df.shock == sh].set_index(["closure", "demand"]).drop(columns="shock")
    rep.table(t, floatfmt=",.3f")
rep.save()
pd.set_option("display.width", 220)
print(pd.DataFrame(frisch))
print(df.round(3).to_string(index=False))
