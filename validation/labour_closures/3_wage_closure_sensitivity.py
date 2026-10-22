"""Labour market: short-run results with wages indexed to the CPI ('real', the published assumption) vs fixed in pesos
('nominal', sticky pay). Infinity GEM 0.3 (option wage=); settings 0.2 published and 0.3 recommended. Read-only."""
import sys, warnings; warnings.filterwarnings("ignore"); sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scenarios"))
import numpy as np, pandas as pd
from app import engines as E
from infinity_gem.cge import CGE
from infinity_gem import settings as ST
from _common import PSA_GDP, to_sam_units
SR = E.CLOSURES["short run"]; GDP25 = PSA_GDP[2025]
pct = lambda a, b: 100 * (a / b - 1)
def model(setting, wage):
    kw = ST.cge_kwargs(setting); path = kw.pop("path")
    if setting == "0.2 published": kw["elasticities"] = dict(E.DEFAULT_ELASTICITIES)
    return CGE.from_sam(path, **kw, **SR, wage=wage)
def four_shocks(m):          # a development script (not in this repository), rebuilt (oil +40% on the composite, or sourced split)
    s = E.Shocks(oil_pct=40.0, construction_bn=-238.3); spec = E.cge_spec(m, s)
    q = m.qinv; inv = [c for i, c in enumerate(m.C) if q[i] > 1e-9]; tot = sum(q[m.C.index(c)] for c in inv)
    geo = to_sam_units((-0.06 * 190.933708 / 100 * 2483.932117 - 0.06 * 141.741254 / 100 * 1632.312645) * 59.97216 / 1000, GDP25)
    for c in inv:
        spec["qinv_scale"][c] = spec["qinv_scale"].get(c, 1.0) + geo * q[m.C.index(c)] / tot / q[m.C.index(c)]
    AG = ["amaiz","arice","apuls","aoils","aroot","avege","asugr","atoba","acott","afrui","acoff","aocrp","acatt","apoul","aoliv","afore","afish"]
    cap = {a: float(m.QF0[m.kcap, m.A.index(a)]) for a in m.A}; d = to_sam_units(47.44, GDP25)
    k = {a: 1 - d * 0.425 / sum(cap[x] for x in AG if x in cap) for a in AG if a in cap}
    k["acons"] = 1 - d * 0.555 / cap["acons"]; k["atrad"] = 1 - d * 0.02 / cap["atrad"]; spec["kscale"] = k
    return spec
SHOCKS = {"Infrastructure freeze -238.3 bn": lambda m: E.cge_spec(m, E.Shocks(construction_bn=-238.3)),
          "World oil +20%": lambda m: E.cge_spec(m, E.Shocks(oil_pct=20.0)),
          "Ayuda cut -90.21 bn": lambda m: E.cge_spec(m, E.Shocks(transfers_bn=-90.21)),
          "Remittances -10%": lambda m: E.cge_spec(m, E.Shocks(remit_pct=-10.0)),
          "Four shocks together": four_shocks}
rows = []
for setting in ("0.2 published", "0.3 recommended"):
    for wage in ("real", "nominal"):
        m = model(setting, wage); b = m.solve(); assert b.ok and b.residual_max < 1e-6
        for name, f in SHOCKS.items():
            sim = m.solve(f(m)); assert sim.ok, (setting, wage, name, sim.message)
            fn, fp = m.F.index("flab-n"), m.F.index("flab-p")
            pov = E.microsim().from_cge(m, b, sim)
            rows.append({"shock": name, "setting": setting, "wage": "indexed to CPI (published)" if wage == "real" else "fixed in pesos (sticky)",
                         "GDP %": pct(m.gdp(sim)["real"], m.gdp(b)["real"]), "CPI %": pct(sim["CPI"], b["CPI"]),
                         "low-skill jobs %": pct(sim["EMP"][fn], b["EMP"][fn]), "medium-skill jobs %": pct(sim["EMP"][fp], b["EMP"][fp]),
                         "real consumption %": pct(sim["QH"].sum(), b["QH"].sum()), "new poor": pov["new_poor"]})
        print(setting, wage, "done", flush=True)
df = pd.DataFrame(rows).set_index(["shock", "setting", "wage"]).sort_index(level=0, sort_remaining=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 20)
print(df.round(3).to_string())
df.to_csv(Path(__file__).with_name("wage_closure_sensitivity.csv"))
