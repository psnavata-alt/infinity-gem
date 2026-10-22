"""Your own test shock. Change ONLY the lines in the box below, save (Ctrl+S), then run from the Infinity GEM folder:

    py scenarios/my_test_shock.py

The report goes to outputs/<REPORT_NAME>_<date>.md. It uses the same engines as the Simulator (app/engines.py,
checked by A1), so the numbers match what the Simulator gives for the same inputs.

To keep a test, first save a copy of this file under a new name (e.g. scenarios/test_oil_30.py) and change
REPORT_NAME, so the next test does not overwrite it. 
If you cannot write to the repository folder, copy this file to your Documents folder, under "Infinity GEM - my runs", and set the environment variable Infinity_GEM_ROOT to the repository folder; your reports are saved there too.
"""
# ================================ CHANGE ONLY THESE LINES ================================
REPORT_NAME = "my_test_shock"          # file name of the report: letters, numbers and _ only
TITLE = "Test: world oil prices +30%"  # title printed at the top of the report
OIL_PCT = 30.0                         # world oil prices, % change (0 = no oil shock)
PETROLEUM_SHARE = 0.6                  # assumed petroleum share of 'chemicals and petroleum' imports (0.2 to 1.0)
CONSTRUCTION_BN = 0.0                  # construction spending, ₱ bn (negative = cut), e.g. -238.3
GOVCONS_BN = 0.0                       # government consumption, ₱ bn (negative = cut)
TRANSFERS_BN = 0.0                     # cash transfers to households (Ayuda), ₱ bn (negative = cut), e.g. -90.21
TRANSFERS_TO = "bottom40"              # who receives them: "bottom40", "bottom20" or "all" (split by population)
REMIT_PCT = 0.0                        # remittances, % change
PESOS_OF = "2025"                      # the year the ₱ amounts belong to: "2025" or "H1_2025"
ELASTICITIES = {"sigma_va": 0.8, "sigma_q": 2.0, "omega_t": 2.0}   # CGE defaults; change to test sensitivity
SOURCES = "Illustrative test. Give a dated source for every number before any use."
# =========================================================================================

import os
import re
import sys
from pathlib import Path

# 0.3.2: a copy in "Documents\Infinity GEM - my runs" (for users who cannot write to the repository folder) finds Infinity GEM through Infinity_GEM_ROOT (set it yourself); in the scenarios folder itself, Infinity GEM is the folder above.
ROOT = Path(os.environ.get("Infinity_GEM_ROOT") or Path(__file__).resolve().parent.parent)
sys.path[:0] = [str(ROOT), str(ROOT / "scenarios")]
from _common import PSA_GDP, Report                  # noqa: E402
from app import engines as E                        # noqa: E402

if not re.fullmatch(r"[A-Za-z0-9_]+", REPORT_NAME):
    sys.exit("REPORT_NAME may use only letters, numbers and _ (no spaces).")
TO = {"bottom40": "Bottom 40% (rural and urban Q1-Q2, by population)",
      "bottom20": "Bottom 20% (rural and urban Q1, by population)",
      "all": "All households (by population)"}
if TRANSFERS_TO not in TO:
    sys.exit('TRANSFERS_TO must be "bottom40", "bottom20" or "all".')
if PESOS_OF not in ("2025", "H1_2025"):
    sys.exit('PESOS_OF must be "2025" or "H1_2025".')

shocks = E.Shocks(construction_bn=CONSTRUCTION_BN, govcons_bn=GOVCONS_BN, transfers_bn=TRANSFERS_BN, transfers_to=TO[TRANSFERS_TO],
                  remit_pct=REMIT_PCT, oil_pct=OIL_PCT, petroleum_share=PETROLEUM_SHARE,
                  gdp_bn=PSA_GDP[2025] if PESOS_OF == "2025" else PSA_GDP["H1_2025"])
print("Running:", "; ".join(shocks.describe()))
table, results, notes = E.compare_all(shocks, ELASTICITIES)

rep = Report(TITLE, REPORT_NAME)
rep.p("**Shocks:** " + "; ".join(shocks.describe()) + f". Peso amounts are in {PESOS_OF} pesos, converted by GDP share.")
rep.p(f"**Elasticities (CGE):** {ELASTICITIES}. **Sources:** {SOURCES}")
rep.h("Same shock, different models")
shown = table.apply(lambda col: [("–" if v != v else (f"{v:,.0f}" if "persons" in i else f"{v:,.2f}")) for i, v in col.items()])
shown.index = table.index
rep.table(shown)
rep.p("The SAM multiplier holds prices fixed (upper bound for demand shocks); the long-run CGE keeps everyone employed (lower "
      "bound); the short-run CGE is the usual central case for a one-year shock. Report the range, not one number.")
for n in notes:
    rep.p("Note: " + n)
for r in results:
    if not r.get("ok"):
        rep.p(f"**{r.get('engine', 'CGE')} did not solve:** {r.get('message')}")
        continue
    if r["engine"] == "CGE" and r["variant"] == "short run":
        rep.h("Short-run CGE: household groups")
        rep.table(r["households"], floatfmt=",.3f")
        rep.h("Short-run CGE: industries with the largest output changes")
        ind = r["industries"]
        rep.table(ind.reindex(ind["Output (%)"].abs().sort_values(ascending=False).index).head(12), floatfmt=",.3f")
        rep.p(f"Model check: Walras slack {r['walras']:.1e}, largest equation error {r['residual']:.1e} (both should be about zero).")
rep.save()
