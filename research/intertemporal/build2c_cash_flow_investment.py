"""Build 2c: cash-flow (rule-of-thumb) investors, so that private investment can move with public works; the share
calibrated to the data's public-works multiplier (18 Oct 2026, about noon). NOT FOR CITATION (research code).

Why (Build 2b, outputs/dscge_build2b_rule_of_thumb_multiplier_grid_20261018_0231.md): the forward-looking model's first-year
public-works multiplier was 0.05-0.39 against about 1.1 in PSA's data (replication model 02; preshock/freeze_multiplier_lp.py),
because private investment ROSE when public works were cut: lower wages and an unchanged return on capital made investing more
attractive, financed by free foreign borrowing. Here a share rit of investment follows the current real return on capital
(pf_cge9 option rit): when demand falls, rental rates fall in the short run (capital is fixed), and so does that investment.
Shock: public works cut by 1% of GDP in 2026, not announced before; 2026-2027 are Keynesian short-run years (labour='wage_curve').
Tests: (a) no shock: stays on the steady state for any rit; (b) rit = 0 gives Build 2b's numbers (the code path is the original).
Run:  py research/intertemporal/build2c_cash_flow_investment.py    Output: outputs/dscge_build2c_cash_flow_investment_<date>.md
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
sys.path.insert(0, str(ROOT))
import pf_cge9 as P                                  # noqa: E402
from infinity_gem import paths                           # noqa: E402

T = 200
SR = lambda r: r.__setitem__((0, slice(0, 2)), 1.0)
DATA_MULTIPLIER = 1.1                                # PSA public construction, local projection after a year (model 02)


def shock_run(m, ss, share=0.01):
    cut = -share * m.GDP0
    X = m.path(T, sr=SR, dIG=lambda r: r.__setitem__((0, 0), cut))
    Y, y0, yT, info = m.run(X, y_start=ss)
    acc = m.accounts(Y, y0, X)
    base = m.accounts(np.repeat(ss[:, None], 2, 1), ss, np.repeat(m.x0[:, None], 3, 1))
    gdp0 = float(base["real_gdp"][0])
    i0 = float(base["v"]["I"].sum(0)[0])
    mult = (gdp0 - float(acc["real_gdp"][0])) / (share * m.GDP0)
    inv = (float(acc["v"]["I"].sum(0)[0]) / i0 - 1) * 100
    emp = float(np.average(acc["employment"][:, 0] - 1, weights=m.L0.sum(1))) * 100
    return dict(multiplier=mult, private_investment=inv, employment=emp, Y=Y)


def model(beta, rot, rit, phi=8.0):
    return P.CGE9(calib="pwt", households="groups", labour="wage_curve", beta_w=beta, rot=rot, rit=rit, phi=phi)


def main():
    out = [f"# Build 2c: cash-flow investors and the public-works multiplier ({datetime.now():%Y-%m-%d %H:%M})", "",
           "**NOT FOR CITATION** (research code; see the script's docstring). Data calibration (`calib=\"pwt\"`), ten household "
           "groups, Keynesian short run in 2026-2027, public works cut by 1% of GDP in 2026.", ""]
    checks = {}
    m0 = model(7.14, 0.5, 0.0)
    ss = m0.steady()[0]
    m5 = model(7.14, 0.5, 0.5)
    ss5 = m5.steady()[0]
    checks[f"(a0) the steady state does not depend on rit (gap {np.abs(ss5 - ss).max():.1e})"] = float(np.abs(ss5 - ss).max()) < 1e-9
    X = m5.path(T, sr=SR)
    Yn, _, _, _ = m5.run(X, y_start=ss5)
    drift = float(np.abs(Yn - ss5[:, None]).max() / np.abs(ss5).max())
    checks[f"(a) no shock with rit 0.5: stays on the steady state (drift {drift:.1e})"] = drift < 1e-10
    r0 = shock_run(m0, ss)
    checks[f"(b) rit 0 reproduces Build 2b (beta 7.14, rot 0.5, phi 8: multiplier {r0['multiplier']:.3f}, Build 2b 0.077)"] = abs(r0["multiplier"] - 0.077) < 0.002
    grid = []
    for beta in (7.14, 0.5):
        for rot in (0.0, 0.5):
            ssb = model(beta, rot, 0.0).steady()[0]
            for rit in (0.0, 0.25, 0.5, 0.75):
                r = shock_run(model(beta, rot, rit), ssb)
                grid.append((beta, rot, rit, r["multiplier"], r["private_investment"], r["employment"]))
                print(f"beta {beta} rot {rot} rit {rit}: multiplier {r['multiplier']:.3f}, private investment {r['private_investment']:+.2f}%, employment {r['employment']:+.3f}%", flush=True)
    # calibration: rit at which the first-year multiplier equals the data's, for the central beta and rot 0 / 0.5
    calib = []
    for rot in (0.0, 0.5):
        f = lambda rit: shock_run(model(7.14, rot, rit), ss if rot == 0.5 else model(7.14, 0.0, 0.0).steady()[0])["multiplier"] - DATA_MULTIPLIER
        lo, hi = 0.0, 0.95
        flo, fhi = f(lo), f(hi)
        if flo * fhi > 0:
            calib.append((rot, None, flo + DATA_MULTIPLIER, fhi + DATA_MULTIPLIER))
            continue
        for _ in range(14):
            mid = (lo + hi) / 2
            fm = f(mid)
            lo, hi, flo = (mid, hi, fm) if fm * flo > 0 else (lo, mid, flo)
        rit_star = (lo + hi) / 2
        rr = shock_run(model(7.14, rot, rit_star), ss if rot == 0.5 else model(7.14, 0.0, 0.0).steady()[0])
        calib.append((rot, rit_star, rr["multiplier"], rr["private_investment"]))
        print(f"calibrated: rot {rot}: rit {rit_star:.3f} -> multiplier {rr['multiplier']:.3f}, private investment {rr['private_investment']:+.2f}%", flush=True)
    out += ["## Tests", ""] + [f"- {k}: {'PASS' if v else 'FAIL'}" for k, v in checks.items()] + [""]
    out += ["## Grid: public works cut by 1% of GDP in 2026 (results for 2026)", "",
            "| Wage curve beta | Rule-of-thumb consumers (rot) | Cash-flow investors (rit) | First-year multiplier | Private investment (%) | Employment (%) |",
            "|---|---|---|---|---|---|"]
    out += [f"| {b:g} | {ro:g} | {ri:g} | {mu:.3f} | {pi:+.2f} | {em:+.3f} |" for b, ro, ri, mu, pi, em in grid]
    out += ["", f"## Calibration to the data's multiplier ({DATA_MULTIPLIER}), beta 7.14, phi 8", ""]
    for rot, rit_star, a, b in calib:
        if rit_star is None:
            out.append(f"- rot {rot:g}: no rit in [0, 0.95] reaches {DATA_MULTIPLIER} (multiplier {a:.3f} at rit 0, {b:.3f} at 0.95).")
        else:
            out.append(f"- rot {rot:g}: **rit = {rit_star:.3f}** gives a first-year multiplier of {a:.3f}; private investment {b:+.2f}% in 2026.")
    out += ["", "Reading: see guide 10 §3 (Limits) for what this does and does not settle."]
    f = paths.output_dir() / f"dscge_build2c_cash_flow_investment_{datetime.now():%Y%m%d_%H%M}.md"
    f.write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out[-12:])); print("saved", f)


if __name__ == "__main__":
    main()
