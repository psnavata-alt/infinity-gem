"""Which part of the Philippine elasticity set flips the sign: sigma_va (labour-capital), sigma_q (Armington), omega_t (CET)?
Also: where do the extra low-skill jobs come from (by activity)?"""
import sys, warnings; warnings.filterwarnings("ignore"); sys.stdout.reconfigure(encoding="utf-8")
GEM = str(__import__("pathlib").Path(__file__).resolve().parents[2]); sys.path.insert(0, GEM)
import numpy as np, pandas as pd
from app import engines as E
from infinity_gem.cge import CGE
from infinity_gem.elasticities import elasticity_set
SR = E.CLOSURES["short run"]; ph = elasticity_set("ph"); d = dict(E.DEFAULT_ELASTICITIES)
pct = lambda a, b: 100 * (a / b - 1)
sets = {"default (0.2)": d,
        "PH sigma_va only": dict(d, sigma_va=ph["sigma_va"]),
        "PH sigma_q only": dict(d, sigma_q=ph["sigma_q"]),
        "PH omega_t only": dict(d, omega_t=ph["omega_t"]),
        "PH trade (sigma_q + omega_t)": dict(d, sigma_q=ph["sigma_q"], omega_t=ph["omega_t"]),
        "full PH set": ph}
s = E.Shocks(transfers_bn=-90.21); keep = {}
for name, el in sets.items():
    m = CGE.from_sam(None, elasticities=el, **SR); b = m.solve(); sim = m.solve(E.cge_spec(m, s)); assert sim.ok
    fn = m.F.index("flab-n")
    print(f"{name:<30} low-skill emp {pct(sim['EMP'][fn], b['EMP'][fn]):+.3f}%  GDP {pct(m.gdp(sim)['real'], m.gdp(b)['real']):+.3f}%  exports {pct(sim['QE'].sum(), b['QE'].sum()):+.3f}%")
    keep[name] = (m, b, sim)
# activity decomposition of low-skill job change, default vs full PH
for name in ("default (0.2)", "full PH set"):
    m, b, sim = keep[name]; fn = m.F.index("flab-n")
    dq = pd.Series(sim["QF"][fn] - b["QF"][fn], index=[m.sam.labels.get(a, a).replace("Activities - ", "")[:28] for a in m.A])
    tot = b["QF"][fn].sum()
    print(f"--- {name}: low-skill job change by activity (% of all low-skill employment); top gains and losses")
    s_ = (100 * dq / tot).sort_values()
    print("   losses:", "; ".join(f"{k} {v:+.3f}" for k, v in s_.head(5).items()))
    print("   gains: ", "; ".join(f"{k} {v:+.3f}" for k, v in s_.tail(5).items()))
