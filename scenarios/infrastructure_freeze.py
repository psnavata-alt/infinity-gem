"""Scenario: the 2025-2026 fall in public infrastructure spending.

Question: how much output, employment and poverty did the
fall in infrastructure disbursements cost, in the short run and over time?

Shock data (DBM): infrastructure disbursements fell ₱238.3 bn in H2 2025 vs H2 2024 (DBM) and ₱202.2 bn in H1 2026 vs H1 2025 (NG Disbursement Performance, June 2026).
Converted to the 2023 SAM as shares of GDP (PSA): 2025 full-year GDP; H1 2025 GDP for the H1 2026 fall.
Modelled as lower real investment demand for construction (commodity 'ccons').

Models run
  1. SAM multiplier (fixed prices): upper bound.
  2. CGE short run: Keynesian closure (fixed exchange rate, unemployment of low/medium-skill labour,
     capital fixed by activity, investment and saving rates fixed).
  3. CGE long run: full employment, mobile capital, investment-driven.
  4. Poverty (FIES 2023) from the short-run CGE.
  5. Dynamic path 2023-2030 (long-run closure): the capital lost to lower investment.
Run:  py scenarios/infrastructure_freeze.py
"""
from _common import PSA_GDP, Report, to_sam_units, SAM
import pandas as pd

from infinity_gem import paths
from infinity_gem.cge import CGE
from infinity_gem.dynamic import DynamicCGE
from infinity_gem.microsim import Microsim
from infinity_gem.multiplier import SAMMultiplier

cut25 = to_sam_units(238.3, PSA_GDP[2025])          # H2 2025 fall, share of 2025 GDP
cut26 = to_sam_units(202.2, PSA_GDP["H1_2025"])    # H1 2026 fall, share of H1 2025 GDP (annualised by assumption)
rep = Report("Scenario: fall in public infrastructure spending, 2025-2026", "infrastructure_freeze")
rep.p(f"Shock in 2023 SAM units: 2025 ₱{cut25:,.1f} bn (= ₱238.3 bn / 2025 GDP); 2026 ₱{cut26:,.1f} bn "
      f"(= ₱202.2 bn / H1 2025 GDP, assumed to apply to the whole year). Applied to real investment demand for construction.")

# 1. SAM multiplier
sm = SAMMultiplier(SAM.load(paths.SAM_2023))
dy = sm.shock({"ccons": -cut25})
va = -sum(dy[f] for f in ("flab-n", "flab-p", "flab-s", "flnd", "fcap"))
hh = -sum(dy[h] for h in sm.endo if h.startswith("hhd"))

# 2-3. CGE, short and long run
rows, ms = [], Microsim()
for label, kw in [("CGE short run (Keynesian)", dict(closure="keynesian", unemployed=("flab-n", "flab-p"), capital="fixed")),
                  ("CGE long run (full employment)", {})]:
    m = CGE.from_sam(**kw)
    q0 = m.qinv[m.C.index("ccons")]
    spec = {"qinv_scale": {"ccons": 1 - cut25 / q0}}
    b, s = m.solve(), m.solve(spec)
    assert b.ok and s.ok, "solve failed"
    gb, gs = m.gdp(b), m.gdp(s)
    pov = ms.from_cge(m, b, s)
    rows.append({"model": label, "real GDP change (₱ bn)": gs["real"] - gb["real"],
                 "real GDP change (%)": (gs["real"] / gb["real"] - 1) * 100,
                 "low-skill employment (%)": (s["EMP"][0] / b["EMP"][0] - 1) * 100,
                 "medium-skill employment (%)": (s["EMP"][1] / b["EMP"][1] - 1) * 100,
                 "real household consumption (%)": (s["QH"].sum() / b["QH"].sum() - 1) * 100,
                 "new poor (FIES 2023)": pov["new_poor"], "Walras check": s["WALRAS"]})
rows.insert(0, {"model": "SAM multiplier (fixed prices, upper bound)", "real GDP change (₱ bn)": -va,
                "real GDP change (%)": -va / 26160.604 * 100, "low-skill employment (%)": float("nan"),
                "medium-skill employment (%)": float("nan"), "real household consumption (%)": float("nan"),
                "new poor (FIES 2023)": float("nan"), "Walras check": float("nan")})
rep.h("Static results for the 2025 fall (one year)")
rep.table(pd.DataFrame(rows).set_index("model"), floatfmt=",.3f")
rep.p(f"SAM multiplier: household income falls ₱{hh:,.1f} bn. Read the SAM figure as an upper bound (no price or "
      "export response) and the long-run CGE as a lower bound (everyone stays employed); the short-run CGE is the "
      "central case for a one-year freeze.")

# 5. dynamic
d = DynamicCGE()
base = d.baseline()
qs = lambda cut: {"qinv_scale": {"ccons": 1 - cut / d.m.qinv[d.m.C.index("ccons")]}}
sim = d.scenario({2025: qs(cut25), 2026: qs(cut26)})
rep.h("Dynamic path, 2023-2030 (long-run closure; baseline growth path in infinity_gem/dynamic.py)")
rep.table(d.compare(base, sim), floatfmt=",.3f")
rep.p("The dynamic model keeps everyone employed, so it misses the short-run demand loss above; its value is the "
      "persistent loss from a smaller capital stock after the shock ends. Growth path, depreciation, labour growth "
      "and initial capital growth are assumptions (see docs/guides/02_CGE_GUIDE.md).")
rep.save()
