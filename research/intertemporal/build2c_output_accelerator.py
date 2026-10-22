"""Build 2c, second part: an output accelerator instead of cash flow (18 Oct 2026, about 11:40 AM). NOT FOR CITATION.

The first part (build2c_cash_flow_investment.py) found that cash-flow investors keyed to the real return on capital do not
stop private investment rising after a public-works cut: the cut lowers construction prices, so the price of capital goods
falls and the real return RISES. Here the rule-of-thumb share follows its sector's OUTPUT relative to the steady state
(pf_cge9 rit_basis='output', an accelerator), and the share is calibrated to the data's multiplier where it can be.
Run:  py research/intertemporal/build2c_output_accelerator.py     Output: outputs/dscge_build2c_output_accelerator_<date>.md
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pf_cge9 as P                                  # noqa: E402
import build2c_cash_flow_investment as B             # noqa: E402
from infinity_gem import paths                           # noqa: E402


def model(beta, rot, rit, ss):
    m = P.CGE9(calib="pwt", households="groups", labour="wage_curve", beta_w=beta, rot=rot, rit=rit, rit_basis="output")
    m.set_output_base(ss)
    return m


def main():
    ss = P.CGE9(calib="pwt", households="groups", labour="wage_curve", rot=0.5).steady()[0]
    rows = []
    for rit in (0.05, 0.1, 0.15, 0.2, 0.25):           # 0.25: the solver does not converge (accelerator feedback too strong)
        try:
            r = B.shock_run(model(7.14, 0.5, rit, ss), ss)
        except Exception as e:                          # recorded, not hidden
            rows.append((rit, float("nan"), float("nan"), float("nan")))
            print(f"rit {rit}: no solution ({str(e)[:70]})", flush=True)
            continue
        rows.append((rit, r["multiplier"], r["private_investment"], r["employment"]))
        print(f"output basis, beta 7.14, rot 0.5, rit {rit}: multiplier {r['multiplier']:.3f}, private investment "
              f"{r['private_investment']:+.2f}%, employment {r['employment']:+.3f}%", flush=True)
    out = [f"# Build 2c (second part): an output accelerator ({datetime.now():%Y-%m-%d %H:%M})", "",
           "**NOT FOR CITATION** (research code). Same shock and settings as the first part (public works cut by 1% of GDP in "
           "2026, Keynesian short run 2026-2027, beta 7.14, rule-of-thumb consumers 0.5, phi 8); the rule-of-thumb share of "
           "investment follows its sector's output relative to the steady state.", "",
           "| Accelerator share (rit) | First-year multiplier | Private investment (%) | Employment (%) |", "|---|---|---|---|"]
    out += [(f"| {a:g} | {b:.3f} | {c:+.2f} | {d:+.3f} |" if b == b else f"| {a:g} | no solution (the solver diverges) | | |") for a, b, c, d in rows]
    f = paths.output_dir() / f"dscge_build2c_output_accelerator_{datetime.now():%Y%m%d_%H%M}.md"
    f.write_text("\n".join(out), encoding="utf-8")
    print("saved", f)


if __name__ == "__main__":
    main()
