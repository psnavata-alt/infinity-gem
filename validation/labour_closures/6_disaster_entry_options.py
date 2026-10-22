"""How should disaster damage enter the CGE? Three ways compared on the same damage. 17 Oct 2026.

Same shock as 5_disaster_job_sign.py: PHP 47.44 bn of capital destroyed (agriculture 42.5%, construction 55.5%, trade 2%), static
short-run CGE, 0.3 recommended settings, peso wages fixed (the 0.3 rule). Read-only (writes only its own output files).
  (a) lost capital (`kscale`), as now: firms replace lost capital with idle labour at the GTAP substitution elasticities;
  (b) lost productivity (`tfp_scale`) in the hit industries, at the AVERAGE productivity of capital: an industry that loses x% of
      its capital loses x% of its output capacity (Hallegatte and Vogt-Schilb 2016, World Bank WPS 7885: average, not
      marginal, productivity; a reference copy (not distributed));
  (c) lost capital with little capital-labour substitution in the hit industries for the damage year (sigma_va 0.1 instead of
      0.26-1.4), as Rose and Liao (2005, J. Regional Science 45(1)) recalibrate production functions to emergency conditions.
Each with and without rebuilding spending (construction investment up by the damage). Benchmark: the I-O sign on 14 Oct,
-49,300 jobs. Run:  py validation/labour_closures/6_disaster_entry_options.py
"""
import importlib.util
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
spec_ = importlib.util.spec_from_file_location("djs", HERE / "5_disaster_job_sign.py")
import pandas as pd                                                     # noqa: E402

ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scenarios"))
from app import engines as E                                            # noqa: E402
from infinity_gem.cge import CGE                                            # noqa: E402
from infinity_gem import settings as ST                                     # noqa: E402
from _common import PSA_GDP, to_sam_units                               # noqa: E402

AG = ["amaiz", "arice", "apuls", "aoils", "aroot", "avege", "asugr", "atoba", "acott", "afrui", "acoff", "aocrp", "acatt",
      "apoul", "aoliv", "afore", "afish"]
pct = lambda a, b: 100 * (a / b - 1)


def model(low_sub=None):
    kw = ST.cge_kwargs("0.3 recommended"); path = kw.pop("path")
    kw.update(E.CLOSURES["short run"]); kw["wage"] = "nominal"
    if low_sub:                                   # (c): sigma_va 0.1 in the hit activities, the rest as in the 0.3 set
        el = dict(kw["elasticities"])
        sv = el["sigma_va"]
        sv = dict(sv) if isinstance(sv, dict) else {}
        el["sigma_va"] = {**sv, **{a: 0.1 for a in low_sub}}
        kw["elasticities"] = el
    return CGE.from_sam(path, **kw)


def kfactors(m):
    cap = {a: float(m.QF0[m.kcap, m.A.index(a)]) for a in m.A}
    d = to_sam_units(47.44, PSA_GDP[2025])
    k = {a: 1 - d * 0.425 / sum(cap[x] for x in AG if x in cap) for a in AG if a in cap}
    k["acons"] = 1 - d * 0.555 / cap["acons"]
    k["atrad"] = 1 - d * 0.02 / cap["atrad"]
    return k, d


def shock(m, how, rebuild):
    k, d = kfactors(m)
    sp = {"tfp_scale": dict(k)} if how == "b" else {"kscale": k}
    if rebuild:
        sp["qinv_scale"] = {"ccons": 1 + d / m.qinv[m.C.index("ccons")]}
    return sp


rows = []
hit = list(kfactors(model())[0])
for how, label in (("a", "(a) lost capital, GTAP substitution (now)"), ("b", "(b) lost productivity, average product of capital"),
                   ("c", "(c) lost capital, little substitution (sigma_va 0.1 in hit industries)")):
    m = model(hit if how == "c" else None)
    b = m.solve(); assert b.ok
    lab = [i for i, f in enumerate(m.F) if f.startswith("flab")]
    base_jobs = sum(float(b["EMP"][i]) for i in lab)
    for rebuild in (False, True):
        s = m.solve(shock(m, how, rebuild)); assert s.ok, (label, s.message)
        jobs = sum(float(s["EMP"][i]) for i in lab)
        rows.append({"how damage enters": label, "shock": "damage + rebuilding" if rebuild else "damage only",
                     "GDP %": pct(m.gdp(s)["real"], m.gdp(b)["real"]), "CPI %": pct(s["CPI"], b["CPI"]),
                     "low-skill jobs %": pct(s["EMP"][m.F.index("flab-n")], b["EMP"][m.F.index("flab-n")]),
                     "all labour %": pct(jobs, base_jobs)})
df = pd.DataFrame(rows)
print(df.round(3).to_string(index=False))
df.to_csv(HERE / "disaster_entry_options.csv", index=False)
(HERE / "out_6_disaster_entry_options.txt").write_text(df.round(3).to_string(index=False), encoding="utf-8")
