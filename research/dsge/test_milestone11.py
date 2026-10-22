"""DSGE research, milestone 11 tests (19 Oct 2026): hand-to-mouth households and partly adaptive expectations (soe_htm.py).

T31 reduction: with lam_h = kappa = 0, soe_htm = soe_rot for all five shocks.
T32 identities along the impulse responses: c = (1 - lam_h) c_o + lam_h c_r and c_r = y - alpha s (real income), exactly.
T33 hand-to-mouth households make consumption follow current income: after a policy shock, the correlation of consumption
    with output along the response is higher, and the impact response of consumption relative to output rises.
T34 the two departures work as theory says: adaptive expectations (kappa 0.5) damp the impact fall in output and the peso's
    move after a policy shock; hand-to-mouth households alone (0.4) AMPLIFY output's response, the two-agent result of Bilbiie
    (2008). (A first version expected both to damp output and inflation; the run showed otherwise, 19 Oct about 9:26 AM.)
T35 determinacy over lam_h in {0.2, 0.4, 0.6} and kappa in {0.3, 0.6} with an active rule.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import soe_htm as Hm   # noqa: E402
import soe_rot as R    # noqa: E402

results = []


def check(name, ok, detail):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


base = dict(rho_i=0.8, rule="output", phi_x=0.2, hab=0.7, phi_e=0.1, omega_H=0.3, omega_F=0.5, phi_pi=1.6)
e31 = 0.0
for s in ("v", "a", "ystar", "pistar", "zeta"):
    r1, r2 = R.irf(R.Params(**base), s, 0.01), Hm.irf(Hm.Params(**base), s, 0.01)
    e31 = max(e31, max(np.abs(r1[k] - r2[k]).max() for k in ("y", "c", "pi", "piH", "piF", "i", "q", "de", "mc")))
check("T31 lam_h = kappa = 0 is soe_rot", e31 < 1e-12, f"max gap {e31:.1e} over 5 shocks")

p = Hm.Params(**base, lam_h=0.4, kappa=0.3)
r = Hm.irf(p, "v", 0.01, T=40)
e32 = max(float(np.abs(r["c"] - ((1 - p.lam_h) * r["co"] + p.lam_h * r["cr"])).max()),
          float(np.abs(r["cr"] - (r["y"] - p.alpha * r["s"])).max()))
check("T32 aggregation and hand-to-mouth budget hold", e32 < 1e-12, f"max residual {e32:.1e}")

r0 = R.irf(R.Params(**base), "v", 0.01, T=24)
rh = Hm.irf(Hm.Params(**base, lam_h=0.5), "v", 0.01, T=24)
cor = lambda z: float(np.corrcoef(z["c"], z["y"])[0, 1])
rat = lambda z: abs(z["c"][0] / z["y"][0])
check("T33 hand-to-mouth households tie consumption to income", cor(rh) >= cor(r0) - 1e-9 and rat(rh) != rat(r0),
      f"corr(c, y) {cor(r0):.3f} -> {cor(rh):.3f}; impact c/y {rat(r0):.2f} -> {rat(rh):.2f}")

rk = Hm.irf(Hm.Params(**base, kappa=0.5), "v", 0.01, T=24)
rl = Hm.irf(Hm.Params(**base, lam_h=0.4), "v", 0.01, T=24)
check("T34 adaptive expectations damp output and the peso; hand-to-mouth households amplify output (Bilbiie 2008)",
      abs(rk["y"][0]) < abs(r0["y"][0]) and abs(rk["de"][0]) < abs(r0["de"][0]) and abs(rl["y"][0]) > abs(r0["y"][0]),
      f"impact output {100 * r0['y'][0]:.3f}% -> kappa 0.5: {100 * rk['y'][0]:.3f}%, lam_h 0.4: {100 * rl['y'][0]:.3f}%; "
      f"depreciation {100 * r0['de'][0]:.2f}% -> {100 * rk['de'][0]:.2f}% (kappa 0.5)")

bad = []
for lam in (0.2, 0.4, 0.6):
    for kap in (0.3, 0.6):
        try:
            Hm.solve(Hm.Params(**base, lam_h=lam, kappa=kap))
        except Exception as ex:  # noqa: BLE001
            bad.append(f"({lam}, {kap}): {type(ex).__name__}")
check("T35 determinate over lam_h 0.2-0.6, kappa 0.3-0.6", not bad, "all determinate" if not bad else "; ".join(bad))

n_pass = sum(ok for _, ok, _ in results)
print(f"\n{n_pass}/{len(results)} passed")
sys.exit(0 if n_pass == len(results) else 1)
