"""Home consumption: as a market purchase (Infinity GEM 0.2, every published result) or as own produce (0.3.1 option).

IFPRI's 2023 Philippine SAM records ₱363.7 bn of home consumption (households eating their own rice, fish, fruit, food):
1.8% of all household consumption, but 5.9% for the poorest rural quintile. Infinity GEM 0.2 treats it as if bought on the
market, so it carries trade margins and sales tax and competes with imports. CGE(home="separate") applies the IFPRI
book's treatment (Lofgren et al. 2002, eq. 18 and 34), validated against IFPRI's own GAMS model (check V4).
Question: does this change the September 2026 results, especially poverty?
Shocks: infrastructure freeze -₱238.3 bn; world oil prices +20% (petroleum 0.6 of chemical imports, as in the
Simulator); remittances -10%; world rice price +20%. Closures: short run (Keynesian) and long run.
Run:  py scenarios/home_consumption_sensitivity.py
"""
from _common import PSA_GDP, Report, to_sam_units
import pandas as pd

from infinity_gem.cge import CGE
from infinity_gem.microsim import Microsim

CLOSURES = {"short run": dict(closure="keynesian", unemployed=("flab-n", "flab-p"), capital="fixed"), "long run": {}}
HOME = {"market (0.2 default)": "market", "own produce (home='separate')": "separate"}
ms = Microsim()
rows = []
for cl, kw in CLOSURES.items():
    for hname, home in HOME.items():
        m = CGE.from_sam(home=home, **kw)
        b = m.solve()
        assert b.ok, (cl, hname)
        q0 = m.qinv[m.C.index("ccons")]
        shocks = {"Infrastructure freeze -₱238.3 bn": {"qinv_scale": {"ccons": 1 - to_sam_units(238.3, PSA_GDP[2025]) / q0}},
                  "World oil prices +20%": {"pwm_scale": {"cchem": 1 + 0.20 * 0.6}},
                  "Remittances -10%": {"remit_scale": 0.90},
                  "World rice price +20%": {"pwm_scale": {"crice": 1.20}}}
        for sh, spec in shocks.items():
            s = m.solve(spec)
            assert s.ok, (cl, hname, sh)
            pct = lambda a, z: (z / a - 1) * 100
            pov = ms.from_cge(m, b, s)
            gf = pov["group_factors"]
            rows.append({"closure": cl, "home consumption": hname, "shock": sh,
                         "real GDP (%)": pct(m.gdp(b)["real"], m.gdp(s)["real"]),
                         "CPI (%)": pct(b["CPI"], s["CPI"]),
                         "real household consumption (%)": pct(b["QH"].sum() + b["QHA"].sum(), s["QH"].sum() + s["QHA"].sum()),
                         "rural Q1 real consumption (%)": (gf["hhd-r1"] - 1) * 100,
                         "new poor (FIES 2023)": pov["new_poor"]})
df = pd.DataFrame(rows)
rep = Report("Home consumption: market purchase or own produce (Infinity GEM 0.3.1 option)", "home_consumption_sensitivity")
rep.p("**Development version 0.3.1; not for citation.** Option `CGE(home='separate')`: the IFPRI book's "
      "treatment of households' own produce (eq. 18 and 34), checked against IFPRI's own GAMS model with home consumption "
      "kept (check V4; `validation/ifpri_home/`). 'market' is what Infinity GEM 0.2 and every published result use. "
      "Note: with own produce separate, the CPI covers market purchases only (as in IFPRI's model); household price "
      "indices for poverty value own produce at producer prices.")
for sh in df.shock.unique():
    rep.h(sh)
    t = df[df.shock == sh].set_index(["closure", "home consumption"]).drop(columns="shock")
    rep.table(t, floatfmt=",.3f")
rep.save()
pd.set_option("display.width", 220)
print(df.round(3).to_string(index=False))
