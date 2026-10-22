"""DSGE research, milestone 10 tests (19 Oct 2026): rule-of-thumb price setters (soe_rot.py).

T26 reduction: with omega_H = omega_F = 0, soe_rot = soe_med without indexation, for all five shocks.
T27 the solved paths obey Gali and Gertler's hybrid curve: along the impulse responses (perfect foresight after impact),
    piH_t = gamma_b piH_{t-1} + gamma_f piH_{t+1} + lambda mc_t, and the same for import inflation with psi.
T28 the coefficients are Gali and Gertler's (1999, eqs. 25-27) at their own illustrative values, and
    gamma_b + gamma_f -> 1 as beta -> 1.
T29 rule-of-thumb setters make inflation more persistent: after a policy shock, inflation's response four quarters on is a
    larger share of its impact response, and its peak comes no earlier.
T30 determinacy over omega in {0.2, 0.5, 0.8} with the estimated rule's smoothing.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import soe_med as M   # noqa: E402
import soe_rot as R   # noqa: E402

results = []


def check(name, ok, detail):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


base = dict(rho_i=0.8, rule="output", phi_x=0.2, hab=0.7, phi_e=0.1)
e26 = 0.0
for s in ("v", "a", "ystar", "pistar", "zeta"):
    r1, r2 = M.irf(M.Params(**base), s, 0.01), R.irf(R.Params(**base), s, 0.01)
    e26 = max(e26, max(np.abs(r1[k] - r2[k]).max() for k in ("y", "c", "pi", "piH", "piF", "i", "q", "de", "mc")))
check("T26 omega = 0 is soe_med without indexation", e26 < 1e-12, f"max gap {e26:.1e} over 5 shocks")

p = R.Params(**base, omega_H=0.5, omega_F=0.3)
r = R.irf(p, "v", 0.01, T=60)
e27 = 0.0
for pi_, cost, (th, om) in (("piH", "mc", (p.theta, p.omega_H)), ("piF", "psi", (p.theta_F, p.omega_F))):
    gb, gf, lam = p.gg(th, om)
    x, c = r[pi_], r[cost]
    lag = np.concatenate([[0.0], x[:-1]])
    res = x[:-1] - (gb * lag[:-1] + gf * x[1:] + lam * c[:-1])
    e27 = max(e27, float(np.abs(res).max()))
check("T27 solved paths obey the hybrid Phillips curves", e27 < 1e-12, f"max residual {e27:.1e} (home and imports)")

gg = R.Params(beta=0.99).gg(0.75, 0.25)       # an illustrative case: theta 0.75, omega 0.25
phi = 0.75 + 0.25 * (1 - 0.75 * 0.01)
ok28 = np.allclose(gg, (0.25 / phi, 0.99 * 0.75 / phi, 0.75 * 0.25 * (1 - 0.99 * 0.75) / phi), atol=1e-15)
s1 = sum(R.Params(beta=1.0).gg(0.75, 0.4)[:2])
check("T28 Gali-Gertler coefficients", ok28 and abs(s1 - 1) < 1e-15,
      f"gamma_b {gg[0]:.4f}, gamma_f {gg[1]:.4f}, lambda {gg[2]:.4f}; beta = 1: gamma_b + gamma_f = {s1:.15f}")

r0 = R.irf(R.Params(**base), "v", 0.01, T=24)
rr = R.irf(R.Params(**base, omega_H=0.6, omega_F=0.6), "v", 0.01, T=24)
pers = lambda z: abs(z[4]) / abs(z[0])
peak = lambda z: int(np.argmax(np.abs(z)))
check("T29 rule-of-thumb setters make inflation more persistent",
      pers(rr["pi"]) > pers(r0["pi"]) and peak(rr["pi"]) >= peak(r0["pi"]),
      f"CPI inflation q4/impact {pers(r0['pi']):.2f} -> {pers(rr['pi']):.2f}; peak quarter {peak(r0['pi'])} -> {peak(rr['pi'])}")

bad = []
for om in (0.2, 0.5, 0.8):
    try:
        R.solve(R.Params(**{**base, "rho_i": 0.81, "phi_pi": 1.72}, omega_H=om, omega_F=om))
    except Exception as ex:  # noqa: BLE001
        bad.append(f"{om}: {ex}")
check("T30 determinate for omega 0.2-0.8", not bad, "all determinate" if not bad else "; ".join(bad))

n_pass = sum(ok for _, ok, _ in results)
print(f"\n{n_pass}/{len(results)} passed")
sys.exit(0 if n_pass == len(results) else 1)
