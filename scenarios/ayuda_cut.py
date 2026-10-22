"""Scenario: the FY 2027 Ayuda (cash transfer) cut of ₱90.21 bn (DBM D.3: FY 2027 NEP vs FY 2026 GAA).

Converted to the 2023 SAM as a share of 2025 GDP and applied as a cut in real government transfers to
households ('trg_h_add', ₱ bn), allocated to the bottom 40% by population (rural and urban Q1-Q2), the
same allocation as the September 2026 SAM-multiplier estimate. The government saves the money in the long-run
and short-run closures (its savings are flexible), so the cut is contractionary in the short run.

Compare with the September 2026 SAM-multiplier result (household income -₱195-199 bn; 0.78-1.69 million more poor).
Run:  py scenarios/ayuda_cut.py
"""
from _common import PSA_GDP, Report, bottom40_allocation, to_sam_units, SAM
import pandas as pd

from infinity_gem import paths
from infinity_gem.cge import CGE
from infinity_gem.microsim import Microsim
from infinity_gem.multiplier import SAMMultiplier

cut = to_sam_units(90.21, PSA_GDP[2025])
alloc = bottom40_allocation()
rep = Report("Scenario: FY 2027 Ayuda cut (₱90.21 bn)", "ayuda_cut")
rep.p(f"Cut in 2023 SAM units: ₱{cut:,.1f} bn, allocated to the bottom 40% by population: "
      + ", ".join(f"{h} {w:.1%}" for h, w in alloc.items()) + ".")
ms = Microsim()
rows = []
sm = SAMMultiplier(SAM.load(paths.SAM_2023))
dy = sm.shock({h: -cut * w for h, w in alloc.items()})
hh_loss = -sum(dy[h] for h in sm.endo if h.startswith("hhd"))
pct = {h: dy[h] / sm.sam.table.loc[h].sum() for h in sm.endo if h.startswith("hhd")}
pov = ms.simulate(pd.Series({h: 1 + v for h, v in pct.items()}))
rows.append({"model": "SAM multiplier (fixed prices)", "household income change (₱ bn)": -hh_loss,
             "real GDP (%)": float("nan"), "new poor": pov["new_poor"]})
for label, kw in [("CGE short run (Keynesian)", dict(closure="keynesian", unemployed=("flab-n", "flab-p"), capital="fixed")),
                  ("CGE long run", {})]:
    m = CGE.from_sam(**kw)
    b = m.solve()
    s = m.solve({"trg_h_add": {h: -cut * w for h, w in alloc.items()}})
    assert s.ok
    p = ms.from_cge(m, b, s)
    rows.append({"model": label, "household income change (₱ bn)": float((s["YH"] - b["YH"]).sum()),
                 "real GDP (%)": (m.gdp(s)["real"] / m.gdp(b)["real"] - 1) * 100, "new poor": p["new_poor"]})
rep.table(pd.DataFrame(rows).set_index("model"), floatfmt=",.2f")
rep.p("Household income changes are nominal. The SAM multiplier counts every round of spending at fixed prices; the "
      "CGE lets prices and employment adjust. Poverty uses the group-level income (SAM) or real-consumption (CGE) change.")
rep.save()
