"""DSGE research, milestone 24 tests (22 Oct 2026, afternoon): soe_htmk plus an investment-specific shock (soe_htmki.py).

T24a nesting: every one of soe_htmk's six shocks gives the same responses in soe_htmki, on every common variable (the new
     shock's state stays at zero).
T24b the MEI shock (a 1% innovation) raises investment on impact, with the capital stock rising from the next quarter, and
     raises output on impact (a demand shock in the short run).
T24c capital accumulation with the shock: k' = (1 - delta) k + delta inv + delta (1 + beta) phi_i ei along the response.
T24d persistence: with rho_ei 0.9 the shock's own path decays geometrically at 0.9, and investment stays above baseline longer
     than with rho_ei 0.3.
T24e determinacy at the soe_htmk posterior regions found on 22 Oct 2026 (Calvo 0.94 and 0.97; phi_i 7.8 and 4.9).
T24f estimation set-up: model=htmki adds rho_ei and sd_ei to model=htmk's parameters and "ei" to the shocks.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import soe_htmk as HK    # noqa: E402
import soe_htmki as HI   # noqa: E402

results = []


def check(name, ok, detail):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


base = dict(rule="output", sigma=1.5, theta=0.95, theta_F=0.6, hab=0.76, omega_H=0.22, omega_F=0.10, lam_h=0.61, kappa=0.71,
            phi_pi=1.34, phi_x=0.32, phi_e=0.13, rho_i=0.95, rho_a=0.71, rho_y=0.74, rho_ps=0.29, rho_v=0.5, rho_z=0.88, rho_u=0.42,
            alpha_k=0.5, i_y=0.24, delta=0.025, phi_i=4.0, psi_u=0.5)

gap = 0.0
for s in ("v", "a", "ystar", "pistar", "zeta", "u"):
    r1, r2 = HK.irf(HK.Params(**base), s, 0.01), HI.irf(HI.Params(**base, rho_ei=0.5), s, 0.01)
    for n in HK.STATES + HK.JUMPS:
        gap = max(gap, float(np.max(np.abs(r1[n] - r2[n]))))
check("T24a nesting: soe_htmk's six shocks give identical responses", gap < 1e-10, f"largest gap {gap:.1e}")

p = HI.Params(**base, rho_ei=0.5)
r = HI.irf(p, "ei", 0.01, T=12)
check("T24b the MEI shock raises investment and output on impact, capital from the next quarter",
      r["inv"][0] > 0 and r["y"][0] > 0 and r["k"][0] == 0 and r["k"][1] > 0,
      f"inv {100*r['inv'][0]:+.3f}%, y {100*r['y'][0]:+.3f}%, k(0) {r['k'][0]:.1e}, k(1) {100*r['k'][1]:+.4f}%")

b, dl, ph = p.beta, p.delta, p.phi_i
acc = max(abs(r["k"][t + 1] - ((1 - dl) * r["k"][t] + dl * r["inv"][t] + dl * (1 + b) * ph * r["ei"][t])) for t in range(10))
check("T24c capital accumulation includes delta (1 + beta) phi_i ei", acc < 1e-12, f"largest residual {acc:.1e}")

r9 = HI.irf(HI.Params(**base, rho_ei=0.9), "ei", 0.01, T=12)
r3 = HI.irf(HI.Params(**base, rho_ei=0.3), "ei", 0.01, T=12)
decay = max(abs(r9["ei"][t + 1] - 0.9 * r9["ei"][t]) for t in range(10))
check("T24d the shock decays at rho_ei; a persistent shock keeps investment up longer",
      decay < 1e-12 and r9["inv"][6] > r3["inv"][6],
      f"decay residual {decay:.1e}; inv at quarter 6: {100*r9['inv'][6]:+.3f}% (0.9) against {100*r3['inv'][6]:+.3f}% (0.3)")

ok, notes = True, []
for theta, phi_i in ((0.94, 7.8), (0.97, 4.9)):
    try:
        HI.solve(HI.Params(**{**base, "theta": theta, "phi_i": phi_i}, rho_ei=0.6))
        notes.append(f"theta {theta}, phi_i {phi_i}: solves")
    except Exception as exc:                                    # noqa: BLE001
        ok = False
        notes.append(f"theta {theta}, phi_i {phi_i}: {type(exc).__name__}")
check("T24e determinacy at the two posterior regions of 22 Oct 2026", ok, "; ".join(notes))

code = ("import sys; sys.argv=['x','model=htmk','prior=ratio2','sample=long','gdp=stl','obs=inv']; import estimate_rot as A; "
        "a=(list(A.NAMES), list(A.SHOCKS)); "
        "sys.argv=['x','model=htmki','prior=ratio2','sample=long','gdp=stl','obs=inv']; import importlib; B=importlib.reload(A); "
        "print(sorted(set(B.NAMES)-set(a[0])), B.SHOCKS==a[1]+['ei'], B.R.__name__, B.NAMES[-1])")
out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=str(HERE)).stdout.strip()
check("T24f model=htmki: model=htmk's parameters plus rho_ei and sd_ei; shocks plus ei; me_inv last",
      out == "['rho_ei', 'sd_ei'] True soe_htmki me_inv", f"set-up: {out or 'nothing printed'}")

n_pass = sum(ok for _, ok, _ in results)
print(f"\ntest_milestone24: {n_pass}/{len(results)} passed")
sys.exit(0 if n_pass == len(results) else 1)
