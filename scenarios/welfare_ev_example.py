"""Example: equivalent variation (EV) by household group for the 2026 oil shock at its measured size (0.4.3, 21 Nov 2026;
infinity_gem/welfare.py, check EV1).

Shock: crude (Dubai) and imported fuel products at their measured changes, central window "conflict period (Mar 2026 to
latest)" (preshock/oil_shock_size.py, as in scenarios/oil_2026_measured.py; no typed-in shock). Model: '0.3 recommended' on
Infinity GEM's own SAM v1.0 (rice=True; LES demand), the static model; short run = settings.short_run_closure, long run = the default
closure. The table sets the EV beside the change in real consumption that the poverty microsimulation applies to each group
(infinity_gem/microsim.py, group_factors_from_cge: spending deflated by the group's own budget-share (Laspeyres) price index).
ILLUSTRATION OF THE MEASURE, NOT FOR CITATION: the static model on the 2023 economy, not the default dynamic setting's 2026 path.
Run:  py -X utf8 scenarios/welfare_ev_example.py
"""
import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "preshock"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from infinity_gem import paths                                         # noqa: E402
from infinity_gem.oil import cge_oil_shock                             # noqa: E402
from infinity_gem.settings import cge_model, short_run_closure         # noqa: E402
from infinity_gem.welfare import TOTAL, UNITS, equivalent_variation    # noqa: E402
from oil_shock_size import shock_sizes                             # noqa: E402

CENTRAL = "conflict period (Mar 2026 to latest)"
NAMES = {f"hhd-{a}{q}": f"{'Rural' if a == 'r' else 'Urban'} Q{q}" for a in "ru" for q in range(1, 6)}


def laspeyres_real_change(m, b, s) -> pd.Series:
    """The microsimulation's group factor (microsim.py): (EH_S / EH_R) / (beta.PQ_S / beta.PQ_R), as % change."""
    out = {}
    for i, h in enumerate(m.H):
        w = m.beta[:, i]
        out[h] = ((s["EH"][i] / b["EH"][i]) / (float(w @ s["PQ"]) / float(w @ b["PQ"])) - 1) * 100
    return pd.Series(out)


def main():
    z = shock_sizes().loc[CENTRAL]
    crude, prod = float(z["crude (Dubai)"]), float(z["fuel products, weighted"])
    blocks = []
    for horizon, closure in (("short run", short_run_closure("0.3 recommended")), ("long run", {})):
        m = cge_model("0.3 recommended", rice=True, **closure)
        b = m.solve({})
        spec = cge_oil_shock(m, crude / 100)
        spec["pwm_scale"]["cpetr"] = 1 + prod / 100
        s = m.solve(spec)
        assert b.ok and s.ok, f"{horizon}: solve failed"
        t = equivalent_variation(m, b, s)
        las = laspeyres_real_change(m, b, s)
        wt = m.beta @ np.asarray(b["EH"], float)                     # all households' basket (groups weighted by spending)
        tot = (float(np.asarray(s["EH"]).sum()) / float(np.asarray(b["EH"]).sum())
               / (float(wt @ s["PQ"]) / float(wt @ b["PQ"])) - 1) * 100
        t["real consumption change, microsimulation (%)"] = list(las) + [tot]
        t.index = [NAMES.get(h, h) for h in t.index]
        t.insert(0, "horizon", horizon)
        blocks.append(t)
    out = pd.concat(blocks)
    pd.set_option("display.width", 250)
    print(out.round(3).to_string())
    stamp = dt.datetime.now()
    L = [f"# Equivalent variation by household group: the 2026 oil shock at its measured size ({stamp:%d %B %Y, %H:%M})", "",
         "**ILLUSTRATION OF THE MEASURE, NOT FOR CITATION** (Infinity GEM 0.4.3; `infinity_gem/welfare.py`, "
         "check EV1). Script: `scenarios/welfare_ev_example.py`.", "",
         f"Shock: crude (Dubai) +{crude:.2f}% and imported fuel products +{prod:.2f}% ({CENTRAL}; `preshock/oil_shock_size.py`). "
         "Model: '0.3 recommended', Infinity GEM's own SAM v1.0, static; short run = `settings.short_run_closure`, long run = the default closure. "
         f"Peso columns: {UNITS} (the 2023 SAM's prices: the reference run is the benchmark). ev_pct: EV as % of the group's "
         "reference consumption spending. Last column: the change in real consumption that the poverty microsimulation applies "
         "(spending deflated by the group's budget-share price index).", "",
         (out.round(3).to_markdown() if hasattr(out, "to_markdown") else out.round(3).to_string()), "",
         f"Total row: '{TOTAL}'. EV = spending change + price effect; the price effect values the scenario's price change at the "
         "scenario's living standard, so it counts the households' substitution away from dearer goods (which a fixed-basket index "
         "does not)."]
    f = paths.output_dir() / f"welfare_ev_example_{stamp:%Y%m%d_%H%M}.md"
    f.write_text(chr(10).join(L) + chr(10), encoding="utf-8")
    print("saved", f)


if __name__ == "__main__":
    main()
