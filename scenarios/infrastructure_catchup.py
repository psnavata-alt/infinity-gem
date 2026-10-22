"""Scenario: catching up on the infrastructure spending lost in 2025-2026.

Question (28 Sept 2026): how much of the loss from the
infrastructure slowdown would the recommendation recover, compared with the baseline and with no action?

Recommendation modelled: in 2027, DPWH obligates and spends the 2025 carry-over that was still unobligated on
30 June 2026, ₱208.7 bn (DBM SAAODB FY 2026 Q2, DPWH continuing appropriations, unobligated allotments).
No action: the ₱238.3 bn fall in H2 2025 (DBM), as in
infrastructure_freeze.py. Sensitivity: the ₱202.2 bn fall in H1 2026 as well.

Conversion: shocks are shares of PSA 2025 GDP (the latest full year) applied to the 2023 SAM. 2027 GDP will be
larger, so the catch-up's share, and its effect, are slightly overstated.

Models run
  1. SAM multiplier (fixed prices): upper bound.
  2. I-O quantity model, domestic inverse (PSA 2018), with LFS job-equivalents.
  3. CGE short run (Keynesian closure; assumes slack labour remains in 2027) and long run.
  4. Poverty (FIES 2023) from the short-run CGE.
  5. Dynamic path 2023-2030 (long-run closure): baseline vs no action vs no action + catch-up.
Run:  py scenarios/infrastructure_catchup.py
"""
from _common import PSA_GDP, SAM_GDP_2023, Report, to_sam_units, SAM
import pandas as pd

from infinity_gem import paths
from infinity_gem.cge import CGE
from infinity_gem.dynamic import DynamicCGE
from infinity_gem.iomodel import IOTable
from infinity_gem.microsim import Microsim
from infinity_gem.multiplier import SAMMultiplier

FALL25, FALL26, CATCHUP = 238.3, 202.2, 208.7
cut25 = to_sam_units(FALL25, PSA_GDP[2025])
cut26 = to_sam_units(FALL26, PSA_GDP["H1_2025"])
catch = to_sam_units(CATCHUP, PSA_GDP[2025])
SHOCKS = {f"No action: 2025 fall (-₱{FALL25} bn)": -cut25, f"Catch-up in 2027 (+₱{CATCHUP} bn)": catch}
PESOS = {f"No action: 2025 fall (-₱{FALL25} bn)": -FALL25, f"Catch-up in 2027 (+₱{CATCHUP} bn)": CATCHUP}

rep = Report("Scenario: catch-up of infrastructure spending in 2027 vs no action", "infrastructure_catchup")
rep.p(f"Shocks in 2023 SAM units (share of PSA 2025 GDP): no action -₱{cut25:,.1f} bn; catch-up +₱{catch:,.1f} bn. "
      "Applied to real investment demand for construction (commodity 'ccons'). One-year static effects; the "
      "catch-up is compared with a 2027 in which nothing is done.")

sm = SAMMultiplier(SAM.load(paths.SAM_2023))
io = IOTable()
ms = Microsim()
cge = {"short": CGE.from_sam(closure="keynesian", unemployed=("flab-n", "flab-p"), capital="fixed"), "long": CGE.from_sam()}
base = {k: m.solve() for k, m in cge.items()}
assert all(b.ok for b in base.values()), "baseline solve failed"

rows = {}
for label, dq in SHOCKS.items():
    dy = sm.shock({"ccons": dq})
    sam_va = sum(dy[f] for f in ("flab-n", "flab-p", "flab-s", "flnd", "fcap"))
    q = io.quantity({"Construction": PESOS[label]}, "domestic", gdp_other_year=PSA_GDP[2025])
    jobs = io.jobs(q["industries"]["output (%)"])["job-equivalents"].sum()
    r = {"SAM multiplier: GDP (% of GDP, upper bound)": sam_va / SAM_GDP_2023 * 100,
         "I-O domestic: GDP (% of GDP)": q["va_pct_gdp"],
         "I-O domestic: GDP (₱ bn, 2025 pesos)": q["va_bn"],
         "I-O: job-equivalents": jobs}
    for k, m in cge.items():
        b = base[k]
        s = m.solve({"qinv_scale": {"ccons": 1 + dq / m.qinv[m.C.index("ccons")]}})
        assert s.ok, f"{label} {k}-run solve failed"
        gb, gs = m.gdp(b), m.gdp(s)
        tag = "CGE short run" if k == "short" else "CGE long run"
        r[f"{tag}: GDP (% of GDP)"] = (gs["real"] / gb["real"] - 1) * 100
        if k == "short":
            r[f"{tag}: low-skill employment (%)"] = (s["EMP"][0] / b["EMP"][0] - 1) * 100
            r[f"{tag}: medium-skill employment (%)"] = (s["EMP"][1] / b["EMP"][1] - 1) * 100
            r[f"{tag}: real household consumption (%)"] = (s["QH"].sum() / b["QH"].sum() - 1) * 100
            r[f"{tag}: change in poor (FIES 2023)"] = ms.from_cge(m, b, s)["new_poor"]
        r[f"{tag}: Walras check"] = s["WALRAS"]
    rows[label] = r

tab = pd.DataFrame(rows)
tab["catch-up ÷ no action (%)"] = tab.iloc[:, 1] / tab.iloc[:, 0].abs() * 100
rep.h("Static effects, one year each")
rep.table(tab, floatfmt=",.3f")
rep.p("Range for the slide: SAM multiplier (upper bound), I-O domestic, short-run CGE (central), long-run CGE "
      "(lower bound: full employment). A negative 'change in poor' means people lifted out of poverty relative to "
      "the same year without the catch-up. The catch-up recovers the loss almost in proportion to its size "
      f"({CATCHUP / FALL25 * 100:.0f}% of ₱{FALL25} bn) because the models are close to linear at this scale.")

d = DynamicCGE()
b = d.baseline()
qs = lambda x: {"qinv_scale": {"ccons": 1 + x / d.m.qinv[d.m.C.index("ccons")]}}
paths_ = {
    "A. No action (2025 fall only)": {2025: qs(-cut25)},
    "A + catch-up in 2027": {2025: qs(-cut25), 2027: qs(catch)},
    "B. No action (2025 and 2026 falls)": {2025: qs(-cut25), 2026: qs(-cut26)},
    "B + catch-up in 2027": {2025: qs(-cut25), 2026: qs(-cut26), 2027: qs(catch)},
}
summary = []
for name, sh in paths_.items():
    cmp = d.compare(b, d.scenario(sh))
    rep.h(f"Dynamic path vs baseline: {name}")
    rep.table(cmp, floatfmt=",.3f")
    summary.append({"path": name,
                    "cumulative GDP gap 2025-2030 (₱ bn, 2023 SAM prices)": cmp.loc["cumulative", "gdp_gap_bn"],
                    "as % of 2023 SAM GDP": cmp.loc["cumulative", "gdp_gap_bn"] / SAM_GDP_2023 * 100,
                    "GDP gap in 2030 (%)": cmp.loc[2030, "gdp_gap_pct"],
                    "capital gap in 2030 (%)": cmp.loc[2030, "capital_gap_pct"]})
rep.h("Dynamic summary, 2025-2030")
rep.table(pd.DataFrame(summary).set_index("path"), floatfmt=",.3f")
rep.p("The dynamic model keeps everyone employed (long-run closure every year) and has no separate public capital "
      "stock, so it shows only the capital channel: the investment lost, and then restored by the catch-up, and "
      "the capacity it leaves. Growth path, depreciation (5%) and labour growth (1.5%) are placeholder "
      "assumptions (infinity_gem/dynamic.py; docs/guides/02_CGE_GUIDE.md).")
rep.save()
