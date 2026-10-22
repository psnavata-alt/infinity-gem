"""Review D6 (19 Oct 2026, about 2:10 AM): sensitivity of the central 2026 case to public capital's baseline share of GDP.

The dynamic model keeps public capital at its 2019 share of GDP on the baseline (kg_gdp = 0.397 with the low elasticity pair,
settings.py); review D6 (review, 17 Oct) asked how much the results depend on it. The low pair's share is set to 0.30, 0.397 (the central setting) and 0.50, everything else as the 2026 scenarios of 18 Oct 2026 (INFINITY_GEM_SCENARIO_SAM=own for Infinity GEM's own SAM).
Run (Git Bash):  export INFINITY_GEM_SCENARIO_SAM=own; py scenarios/d6_public_capital_share.py
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import _common                                                       # noqa: E402
import combined_revised as CR                                        # noqa: E402
from infinity_gem import paths                                           # noqa: E402
from infinity_gem.settings import dynamic_kwargs                         # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    beta = float(pd.read_csv(_common.calibration_file(), index_col=0).loc["central (e)", "beta"])
    base = dynamic_kwargs("0.3 recommended", public_capital="low", rice=True, land="fixed", sam_variant=CR.SAM_VARIANT)["public_capital"]
    rows = {}
    for kg in (0.30, float(base["kg_gdp"]), 0.50):
        R = CR.Runs("low", wage_curve=beta, public_capital=dict(base, kg_gdp=kg))
        piece, _ = R.pieces()
        M = R.measures(R.run(set(), piece=piece), R.run(set(CR.SHOCKS), piece=piece))[0]
        rows[f"kg_gdp {kg:.3f}"] = {k: M[k] for k in ("GDP gap 2026 (%)", "GDP gap 2027 (%)", "GDP gap 2030 (%)",
                                                      "cumulative GDP loss 2025-2030 (₱ bn)", "new poor 2026 (M, own baskets)",
                                                      "new poor 2027 (M, own baskets)")}
    t = pd.DataFrame(rows)
    out = paths.output_dir() / f"d6_public_capital_share_{dt.datetime.now():%Y%m%d_%H%M}{_common.out_tag()}.md"
    L = [f"# Review D6: public capital's baseline share of GDP ({dt.datetime.now():%d %B %Y, %H:%M})", "",
         f"**NOT FOR CITATION** (Infinity GEM 0.3.11). SAM `{CR.SAM_VARIANT}`; wage-curve beta {beta:.3f}; low elasticity pair "
         f"(phi {base['phi']}); the 2026 scenarios' share is {base['kg_gdp']}. Script `scenarios/d6_public_capital_share.py`.", "",
         t.to_markdown(floatfmt=".3f")]
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L)); print("saved", out)


if __name__ == "__main__":
    main()
