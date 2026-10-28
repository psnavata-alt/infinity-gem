"""DSGE milestone 26 (24 Oct 2026; research, NOT FOR CITATION): scenarios/bsp_oil_response_netting.py with the BSP's
response to the oil shock taken from the sticky-wage capital DSGE with oil (research/dsge/soe_htmkwo.py, the Calvo parameter
ESTIMATED), instead of the oil DSGE soe_oilw with the Calvo parameter fixed at 0.73.

Nothing else changes: the same CGE (the central 2026 setting, the own SAM, labour hoarding h), the same link (real investment by
theta % per pp of the DSGE's real-rate gap; the peso by the DSGE's real exchange rate) and the same three poverty counts (incomes
and prices, incomes only, prices only). The only substitution is the DSGE input: bsp_oil_response_netting's QL.dsge_oil_annual is
replaced by research/dsge/oil_policy_htmkwo.annual_response (the estimated rule minus the rate held for a year, by year, at the
posterior mean of the newest soe_htmkwo SMC particles, or file= in outputs/). A new file, so the 20-23 Oct runs stay reproducible.
Run (Git Bash, repository root):
  export INFINITY_GEM_SCENARIO_SAM=own
  py -I -X utf8 scenarios/bsp_oil_response_netting_htmkwo.py oil=36 h=0.85 thetas=0.7,1.5,2 spec=_htmkwo_long_stl_inv [file=...]
Output: outputs/bsp_oil_response_netting_<stamp><tag>_oil36_htmkwo_long_stl_inv.md
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "research" / "dsge"))

import bsp_oil_response_netting as BN                               # noqa: E402
import oil_policy_htmkwo as OPW                                      # noqa: E402

FILE = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("file=")), None)
BN.QL.dsge_oil_annual = lambda oil_pct, spec="": OPW.annual_response(oil_pct, FILE)
sys.modules["oil_policy"] = types.SimpleNamespace(_M="htmkwo")      # the netting file's header names the DSGE by this

if __name__ == "__main__":
    BN.main()
