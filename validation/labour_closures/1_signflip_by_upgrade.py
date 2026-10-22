"""Labour market: why does a demand cut (Ayuda, remittances) raise low-skill jobs under '0.3 recommended' (short run)?
Switch the four 0.3 upgrades on one at a time. Read-only on Infinity GEM 0.3.3."""
import sys, warnings, itertools; warnings.filterwarnings("ignore"); sys.stdout.reconfigure(encoding="utf-8")
GEM = str(__import__("pathlib").Path(__file__).resolve().parents[2])
sys.path.insert(0, GEM)
import numpy as np, pandas as pd
from app import engines as E
from infinity_gem.cge import CGE
from infinity_gem import paths
from infinity_gem.demand import les_briones2023
from infinity_gem.elasticities import elasticity_set
SR = E.CLOSURES["short run"]
UP = {"petroleum SAM": lambda kw: kw.update(path=paths.SAM_2023_PETR),
      "PH elasticities": lambda kw: kw.update(elasticities=elasticity_set("ph")),
      "LES demand": lambda kw: kw.update(les=les_briones2023()),
      "split margins": lambda kw: kw.update(margins="split")}
def build(on):
    kw = dict(path=None, elasticities=dict(E.DEFAULT_ELASTICITIES))
    for u in on: UP[u](kw)
    return CGE.from_sam(kw.pop("path"), **kw, **SR)
SHOCKS = {"Ayuda -90.21 bn": E.Shocks(transfers_bn=-90.21), "Remittances -10%": E.Shocks(remit_pct=-10.0),
          "Freeze -238.3 bn": E.Shocks(construction_bn=-238.3)}
pct = lambda a, b: 100 * (a / b - 1)
combos = [()] + [(u,) for u in UP] + [tuple(u for u in UP if u != x) for x in UP] + [tuple(UP)]
rows = []
for on in combos:
    m = build(on); b = m.solve()
    for name, s in SHOCKS.items():
        sim = m.solve(E.cge_spec(m, s)); assert sim.ok, (on, name, sim.message)
        fn = m.F.index("flab-n"); fp = m.F.index("flab-p")
        rows.append({"upgrades on": "+".join(on) or "none (0.2)", "shock": name,
                     "GDP %": pct(m.gdp(sim)["real"], m.gdp(b)["real"]), "low-skill emp %": pct(sim["EMP"][fn], b["EMP"][fn]),
                     "med-skill emp %": pct(sim["EMP"][fp], b["EMP"][fp]), "exports %": pct(sim["QE"].sum(), b["QE"].sum()),
                     "CPI %": pct(sim["CPI"], b["CPI"]), "real cons %": pct(sim["QH"].sum(), b["QH"].sum())})
df = pd.DataFrame(rows)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 20)
for sh in SHOCKS:
    print("=====", sh); print(df[df.shock == sh].drop(columns="shock").round(3).to_string(index=False))
df.to_csv("signflip_table.csv", index=False)
