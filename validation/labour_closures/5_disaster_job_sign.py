"""Labour market, last open point: the disaster job sign (CGE +22.6k jobs vs I-O -49.3k on 14 Oct). Is it the wage rule, or how
capital destruction enters? Infinity GEM 0.3, static short-run CGE, 0.3 recommended settings. Read-only. 16 Oct 2026.

Shock: as in 3_wage_closure_sensitivity.py, PHP 47.44 bn of capital destroyed (agriculture 42.5%, construction 55.5%,
trade 2%), entered as lower capital stocks (`kscale`). Variants: wages indexed to the CPI ('real', the published rule) or
fixed in pesos ('nominal'); and the same damage with the reconstruction spending that follows a disaster (construction
investment raised by the damage to construction capital), the usual way disaster CGE studies add the rebuilding."""
import sys, warnings; warnings.filterwarnings("ignore"); sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scenarios"))
import pandas as pd
from app import engines as E
from infinity_gem.cge import CGE
from infinity_gem import settings as ST
from _common import PSA_GDP, to_sam_units

SR = E.CLOSURES["short run"]; GDP25 = PSA_GDP[2025]
AG = ["amaiz", "arice", "apuls", "aoils", "aroot", "avege", "asugr", "atoba", "acott", "afrui", "acoff", "aocrp", "acatt",
      "apoul", "aoliv", "afore", "afish"]
pct = lambda a, b: 100 * (a / b - 1)
RECOMMENDED_WAGE = [None]


def model(wage):
    kw = ST.cge_kwargs("0.3 recommended"); path = kw.pop("path")
    kw.update(SR); RECOMMENDED_WAGE[0] = kw.get("wage", "real"); kw["wage"] = wage
    return CGE.from_sam(path, **kw)


def disaster(m, rebuild=False):
    cap = {a: float(m.QF0[m.kcap, m.A.index(a)]) for a in m.A}
    d = to_sam_units(47.44, GDP25)
    k = {a: 1 - d * 0.425 / sum(cap[x] for x in AG if x in cap) for a in AG if a in cap}
    k["acons"] = 1 - d * 0.555 / cap["acons"]; k["atrad"] = 1 - d * 0.02 / cap["atrad"]
    spec = {"kscale": k}
    if rebuild:                                   # rebuilding: construction investment up by the damage (all of it)
        i = m.C.index("ccons"); spec["qinv_scale"] = {"ccons": 1 + d / m.qinv[i]}
    return spec


rows = []
for wage in ("real", "nominal"):
    m = model(wage); b = m.solve(); assert b.ok
    lab = [k for k, f in enumerate(m.F) if f.startswith("flab")]
    base_jobs = sum(float(b["EMP"][k]) for k in lab)
    for rebuild in (False, True):
        s = m.solve(disaster(m, rebuild)); assert s.ok, s.message
        jobs = sum(float(s["EMP"][k]) for k in lab)
        rows.append({"wage rule": "indexed to CPI (published)" if wage == "real" else "fixed in pesos",
                     "shock": "damage + rebuilding" if rebuild else "damage only",
                     "GDP %": pct(m.gdp(s)["real"], m.gdp(b)["real"]), "CPI %": pct(s["CPI"], b["CPI"]),
                     "low-skill jobs %": pct(s["EMP"][m.F.index("flab-n")], b["EMP"][m.F.index("flab-n")]),
                     "all labour %": pct(jobs, base_jobs)})
df = pd.DataFrame(rows)
print("0.3 recommended wage rule:", RECOMMENDED_WAGE[0])
print(df.round(3).to_string(index=False))
df.to_csv(Path(__file__).with_name("disaster_job_sign.csv"), index=False)
