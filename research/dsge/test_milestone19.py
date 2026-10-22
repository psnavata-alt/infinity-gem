"""DSGE research, milestone 19 tests (20 Oct 2026, about 01:40): a domestic cost-push shock (soe_htmu.py).

T19a reduction: for each of soe_htm's five shocks, soe_htmu gives the same responses on every common variable (the cost-push
     shock never drawn), at a hand-to-mouth and adaptive-expectations setting.
T19b a cost-push shock is stagflationary: domestic and CPI inflation rise on impact, the policy rate rises, output falls; and it
     dies out (domestic inflation back near zero after five years).
T19c determinacy over rho_u in {0, 0.5, 0.9} with an active rule; and the estimation set-up (estimate_rot.py model=htmu) adds
     rho_u and sd_u and the shock u, nothing else.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import soe_htm as Hm    # noqa: E402
import soe_htmu as Hu   # noqa: E402

results = []


def check(name, ok, detail):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


base = dict(rho_i=0.8, rule="output", phi_x=0.2, hab=0.7, phi_e=0.1, omega_H=0.3, omega_F=0.5, phi_pi=1.6, lam_h=0.4, kappa=0.3)
gap = 0.0
for s in ("v", "a", "ystar", "pistar", "zeta"):
    r1, r2 = Hm.irf(Hm.Params(**base), s, 0.01), Hu.irf(Hu.Params(**base), s, 0.01)
    gap = max(gap, max(float(np.abs(r1[k] - r2[k]).max()) for k in r1))
check("T19a without the cost-push shock = soe_htm", gap < 1e-12, f"max gap {gap:.1e} over 5 shocks and every common variable")

r = Hu.irf(Hu.Params(**base, rho_u=0.5), "u", 0.01, T=24)
stag = r["piH"][0] > 0 and r["pi"][0] > 0 and r["i"][0] > 0 and r["y"][0] < 0
dies = abs(r["piH"][20]) < 0.05 * abs(r["piH"][0])
check("T19b a cost-push shock is stagflationary and dies out", stag and dies,
      f"impact: piH {100 * r['piH'][0]:+.3f}, pi {100 * r['pi'][0]:+.3f}, i {100 * r['i'][0]:+.3f}, y {100 * r['y'][0]:+.3f} "
      f"(pp, quarterly, per 1% shock); piH after 5 years {100 * r['piH'][20]:+.4f}")

det = []
for ru in (0.0, 0.5, 0.9):
    try:
        Hu.solve(Hu.Params(**base, rho_u=ru))
        det.append(True)
    except Exception:
        det.append(False)
code = ("import sys; sys.argv=['x','model=htm']; import estimate_rot as A; a=(A.NAMES, A.SHOCKS); "
        "sys.argv=['x','model=htmu']; import importlib; B=importlib.reload(A); "
        "print(sorted(set(B.NAMES)-set(a[0])), sorted(set(B.SHOCKS)-set(a[1])), sorted(set(a[0])-set(B.NAMES)))")
out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=str(HERE)).stdout.strip()
check("T19c determinate; estimation adds rho_u, sd_u and the shock u only", all(det) and out == "['rho_u', 'sd_u'] ['u'] []",
      f"determinate at rho_u 0 / 0.5 / 0.9: {det}; estimate_rot model=htmu adds: {out or 'nothing printed'}")

# T19d (20 Oct 2026, about 03:25): the oil model with the cost-push shock (soe_oilu.py) = soe_oil.py when u is never drawn,
# for all six of soe_oil's shocks, with oil switched on; and model=oilu adds only rho_u, sd_u and u to model=oil
import soe_oil as Oil    # noqa: E402
import soe_oilu as OilU  # noqa: E402
ob = dict(base, a_o=0.037, s_o=0.030, eps_o=0.2, rho_o=0.9)
gap_o = 0.0
for s in ("v", "a", "ystar", "pistar", "zeta", "o"):
    r1, r2 = Oil.irf(Oil.Params(**ob), s, 0.01), OilU.irf(OilU.Params(**ob), s, 0.01)
    gap_o = max(gap_o, max(float(np.abs(r1[k] - r2[k]).max()) for k in r1))
code_o = ("import sys; sys.argv=['x','model=oil']; import estimate_rot as A; a=(A.NAMES, A.SHOCKS); "
          "sys.argv=['x','model=oilu']; import importlib; B=importlib.reload(A); "
          "print(sorted(set(B.NAMES)-set(a[0])), sorted(set(B.SHOCKS)-set(a[1])), sorted(set(a[0])-set(B.NAMES)))")
out_o = subprocess.run([sys.executable, "-c", code_o], capture_output=True, text=True, cwd=str(HERE)).stdout.strip()
check("T19d oil model with the cost-push shock = soe_oil without it; estimation adds rho_u, sd_u, u only",
      gap_o < 1e-12 and out_o == "['rho_u', 'sd_u'] ['u'] []",
      f"max gap {gap_o:.1e} over 6 shocks and every common variable; model=oilu adds: {out_o or 'nothing printed'}")

n_pass = sum(ok for _, ok, _ in results)
print(f"\n{n_pass}/{len(results)} passed")
sys.exit(0 if n_pass == len(results) else 1)
