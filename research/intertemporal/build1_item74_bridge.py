"""The forward-looking CGE (Stage 2), Build 1 (18 Oct 2026, about 2:10 AM): the foreign-saving bridge in the forward-looking CGE. NOT FOR CITATION.

17 Oct 2026. Spec: a design note (not included)
pf_cge9.CGE9.bridge_baseline(): of the SAM's foreign saving, the national-accounts bridge (a) and the sustainable borrowing (b)
stay permanent inflows; the temporary excess (c) is borrowed in 2023 through a decaying saving wedge and repaid.
Tests:
  (a) defaults unchanged: with the wedge at 1 and the SAM's inflows, a no-shock path stays on the SAM's steady state;
  (b) calibration: 2023 (year 1) borrowing equals the excess (c);
  (c) the debt is repaid: foreign assets stay bounded and return toward zero (below a tenth of the trough after 150 years:
      the debt-elastic premium, psi 0.02, repays slowly; half the trough in about 35 years);
  (d) GDP by expenditure = GDP by income on the base path;
  (e) 2023 is close to the SAM: its trade balance is the SAM's (exact, by (b)); consumption, investment and output are
      reported against the SAM.
Run:  py research/intertemporal/build1_item74_bridge.py
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import pf_cge9 as P                                   # noqa: E402


def main():
    checks = {}
    m = P.CGE9(calib="pwt", households="groups")
    ss = m.steady()[0]
    Y0, *_ = m.run(m.path(200), y_start=ss)
    checks["(a) defaults unchanged: no-shock path stays on the SAM's steady state"] = float(np.abs(Y0 - ss[:, None]).max() / np.abs(ss).max()) < 1e-10
    X, Y, y0, info = m.bridge_baseline(200)
    v = m.split(Y)
    b = v["b"]
    gdp0 = m.GDP0
    checks[f"(b) 2023 borrowing equals the excess (₱{info['temporary']:,.1f} bn): gap {b[0] + info['temporary']:.1e}"] = abs(b[0] + info["temporary"]) < 1e-6 * gdp0
    tro = int(np.argmin(b))
    checks[f"(c) bounded and repaid: lowest {b.min() / gdp0 * 100:+.2f}% of GDP in year {tro + 1}; {b[49] / gdp0 * 100:+.2f}% after 50 "
           f"years, {b[149] / gdp0 * 100:+.2f}% after 150 (the debt-elastic premium psi {m.psi} repays slowly)"] = (
        b.min() > -0.5 * gdp0 and abs(b[149]) < 0.1 * abs(b.min()))
    acc = m.accounts(Y, y0, X)
    checks[f"(d) GDP identity (gap {acc['gap']:.1e})"] = acc["gap"] < 1e-8
    vs = m.split(ss[:, None])
    s0 = acc["s"]
    tb1 = float(m.trade_balance(s0)[0])
    sam_tb = -float(m.NF0)
    checks[f"(e) 2023 trade balance = the SAM's (₱{tb1:,.1f} bn vs ₱{sam_tb:,.1f} bn)"] = abs(tb1 - sam_tb) < 1e-6 * gdp0
    years = list(range(2023, 2033))
    lag = np.concatenate([[0.0], b[:-1]])
    new_borrow = (lag / (1 + m.g) - b) / gdp0 * 100                 # % of base GDP, detrended
    bop = info["sustainable"] / gdp0 * 100 + new_borrow
    rows = []
    for i, yr in enumerate(years):
        rows.append(f"| {yr} | {-bop[i]:+.2f} | {P.IMF_CA.get(yr, float('nan')):+.1f} | {b[i] / gdp0 * 100:+.2f} | "
                    f"{(v['C'][i] / float(vs['C'][0]) - 1) * 100:+.2f} | {(v['I'][:, i].sum() / float(vs['I'].sum()) - 1) * 100:+.2f} | "
                    f"{(acc['real_gdp'][i] / gdp0 - 1) * 100:+.2f} | {X[33, i]:.4f} |")
    out = [f"# Build 1: the foreign-saving bridge in the forward-looking CGE ({datetime.now():%Y-%m-%d %H:%M})", "",
           "**NOT FOR CITATION** (research code; `pf_cge9.CGE9.bridge_baseline()`; data calibration, ten household groups).", "",
           f"The SAM's foreign saving, ₱{m.FSAV0:,.1f} bn (2023-SAM units), split as the evidence note's section 5:", "",
           f"- **(a) bridge, ₱{info['bridge']:,.1f} bn:** the national-accounts-vs-BOP trade definition; a permanent inflow.",
           f"- **(b) sustainable borrowing, ₱{info['sustainable']:,.1f} bn:** keeps the NIIP ratio stable at trend growth; a permanent inflow.",
           f"- **(c) temporary excess, ₱{info['temporary']:,.1f} bn:** borrowed in 2023 and repaid.", "",
           f"Saving wedge: omega = 1 − {info['kappa']:.4f} × {info['lam']:.3f}^t. lambda is the decay of the IMF's projected excess over its norm, 2024-2028; kappa is set so that 2023 borrows the excess.", "",
           "| Year | Model BOP current account (% of GDP) | IMF CR 25/333 (% of GDP) | Foreign assets b (% of GDP) | Consumption vs SAM steady state (%) | Private investment (%) | Real GDP (%) | omega |",
           "|---|---|---|---|---|---|---|---|"] + rows + [
           "", "## Checks", ""] + [f"- {k}: {'PASS' if ok else 'FAIL'}" for k, ok in checks.items()] + [
           "", f"{sum(checks.values())} of {len(checks)} checks pass", "",
           "## Reading", "",
           "- **The base path no longer treats the SAM's excess foreign saving as a gift.** Households borrow it in 2023 and repay it, so consumption is lower than on the SAM's steady state in later years, and investment adjusts.",
           "- **The 2023 BOP deficit is matched** (sustainable borrowing plus the excess), in shares of the SAM's GDP, which is 7.6% above PSA's.",
           "- **The IMF's 2024 rise (4.0%) is not reproduced.** A geometric decay cannot rise first.",
           "- **Next:** shocks and measure C on this base path (deviations from it), with the Keynesian short run (Build 2)."]
    txt = "\n".join(out) + "\n"
    p = ROOT / "outputs" / f"dscge_build1_item74_bridge_{datetime.now():%Y%m%d_%H%M}.md"
    p.write_text(txt, encoding="utf-8")
    print(txt); print(f"wrote {p}")
    return checks


if __name__ == "__main__":
    main()
