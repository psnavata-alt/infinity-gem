"""DSGE research, milestone 6 tests (19 Oct 2026): habits, indexation, risk-premium shock, Lubik-Schorfheide rule.

T22 reduction: with no habits, no indexation, rule='gap_gm' and phi_e = 0, soe_med = soe_lcp for every shock they share.
T23 habits and indexation damp and delay transmission: the impact response of output and CPI inflation to a policy shock is
    smaller, and inflation's peak comes later.
T24 a risk-premium shock depreciates the peso and raises CPI inflation on impact (signs).
T25 determinacy with a response to depreciation (phi_e = 0.2).
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import soe_lcp as L   # noqa: E402
import soe_med as M   # noqa: E402

results = []


def check(name, ok, detail):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


e22 = 0.0                      # soe_lcp: CPI rule on the GM gap (rule='cpi'); soe_med: the same with rule='gap_gm'
for s in ("v", "a", "ystar", "pistar"):
    r1, r2 = L.irf(L.Params(rho_i=0.5, rule="cpi"), s, 1.0), M.irf(M.Params(rho_i=0.5, rule="gap_gm"), s, 1.0)
    e22 = max(e22, max(np.abs(r1[k] - r2[k]).max() for k in ("y", "pi", "i", "q", "de", "psi")))
check("T22 no rigidities = milestone 3 (soe_lcp)", e22 < 1e-10, f"max gap {e22:.1e} over 4 shocks")

base = dict(rho_i=0.8, rule="output", phi_x=0.2)
r0, rr = M.irf(M.Params(**base), "v", 0.01), M.irf(M.Params(**base, hab=0.7, gH=0.5, gF=0.5), "v", 0.01)
peak = lambda x: int(np.argmax(np.abs(x)))
check("T23 habits and indexation damp and delay transmission",
      abs(rr["y"][0]) < abs(r0["y"][0]) and abs(rr["pi"][0]) < abs(r0["pi"][0]) and peak(rr["pi"]) >= peak(r0["pi"]),
      f"impact output {100 * r0['y'][0]:.2f}% -> {100 * rr['y'][0]:.2f}%; CPI inflation {400 * r0['pi'][0]:.2f} -> {400 * rr['pi'][0]:.2f} pp "
      f"annualized; inflation peak quarter {peak(r0['pi'])} -> {peak(rr['pi'])}")

rz = M.irf(M.Params(**base, hab=0.7, gH=0.5, gF=0.5), "zeta", 0.01)
check("T24 risk-premium shock: peso depreciates, CPI inflation rises", rz["de"][0] > 0 and rz["pi"][0] > 0,
      f"depreciation {100 * rz['de'][0]:.2f}%, CPI inflation {400 * rz['pi'][0]:.2f} pp annualized, policy rate {400 * rz['i'][0]:.2f} pp")
try:
    M.solve(M.Params(**base, hab=0.7, gH=0.5, gF=0.5, phi_e=0.2))
    check("T25 determinate with a response to depreciation", True, "phi_e 0.2")
except Exception as ex:  # noqa: BLE001
    check("T25 determinate with a response to depreciation", False, str(ex))
n_pass = sum(ok for _, ok, _ in results)
print(f"\n{n_pass}/{len(results)} passed")
sys.exit(0 if n_pass == len(results) else 1)
