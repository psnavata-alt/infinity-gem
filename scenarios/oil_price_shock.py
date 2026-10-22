"""Scenario: higher world oil prices (20%, 40%, 60%).

The 2023 SAM combines petroleum with chemicals in one commodity ('cchem'); about 48% of its
supply is imported (IFPRI 2023 data paper). A rise in the world price of crude and refined petroleum is
therefore approximated by raising the world import price of 'cchem' by the oil-price change times the
petroleum share of cchem imports. That share is an ASSUMPTION (default 0.6, to be replaced with
PSA/BOC import data by HS chapter 27 vs 28-38).

Outputs: real GDP, household real consumption by group, CPI, and poverty (FIES 2023), for the long-run
and short-run closures. Compare with the September 2026 FIES price-channel simulation (Table 4 of the 24 Sept 2026 analysis), which holds incomes fixed.
Run:  py scenarios/oil_price_shock.py
"""
from _common import Report
import pandas as pd

from infinity_gem.cge import CGE
from infinity_gem.microsim import Microsim

PETROLEUM_SHARE_OF_CCHEM_IMPORTS = 0.6
rep = Report("Scenario: higher world oil prices", "oil_price_shock")
rep.p(f"Shock: world import price of 'cchem' (chemicals and petroleum) raised by the oil-price change x "
      f"{PETROLEUM_SHARE_OF_CCHEM_IMPORTS} (assumed petroleum share of cchem imports).")
ms = Microsim()
rows = []
for label, kw in [("long run", {}), ("short run (Keynesian)", dict(closure="keynesian", unemployed=("flab-n", "flab-p"), capital="fixed"))]:
    m = CGE.from_sam(**kw)
    b = m.solve()
    for oil in (0.2, 0.4, 0.6):
        s = m.solve({"pwm_scale": {"cchem": 1 + oil * PETROLEUM_SHARE_OF_CCHEM_IMPORTS}})
        assert s.ok
        pov = ms.from_cge(m, b, s)
        rows.append({"closure": label, "oil price": f"+{oil:.0%}",
                     "real GDP (%)": (m.gdp(s)["real"] / m.gdp(b)["real"] - 1) * 100,
                     "CPI (%)": (s["CPI"] / b["CPI"] - 1) * 100,
                     "real consumption, rural Q1 (%)": (pov["group_factors"]["hhd-r1"] - 1) * 100,
                     "real consumption, urban Q5 (%)": (pov["group_factors"]["hhd-u5"] - 1) * 100,
                     "new poor": pov["new_poor"]})
rep.table(pd.DataFrame(rows).set_index(["closure", "oil price"]), floatfmt=",.2f")
rep.p("In the short-run closure the exchange rate is the numeraire, so the CPI shows the price-level effect; in the "
      "long-run closure the CPI is the numeraire (fixed) and real effects show up in relative prices and incomes.")
rep.save()
