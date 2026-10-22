"""DSGE research, milestone 22 tests (21 Oct 2026, about 1:25 AM): oil pass-through through a flexible-price, energy-intensive
part of the consumption basket (soe_oilf.py).

T22a reduction: with a_f = 0, soe_oilf gives soe_oilw's responses to all seven shocks on every common variable (any s_f).
T22b identities (a_f = 0.091, s_f = 0.19): along every response path, pi = (1 - a_o - a_f) pi_c + a_o pi_o + a_f pi_f;
     pi_f = piH + r_f - r_f(-1); r_f = (1 - s_f)(wr + X - a) + s_f (q + o + X); and X = (psi + (1 - alpha) s) + alpha s - q
     (the CPI wedge is consistent with the real exchange rate).
T22c pass-through: after an oil supply shock, impact CPI inflation is higher with the flexible component than without it, by
     about a_f x s_f x the shock (the direct effect; the general-equilibrium part is small on impact).
T22d estimation set-up: model=oilf adds no parameter to model=oilw (same names and shocks), calibrates a_f and s_f, and uses the
     same six observables; estimate_rot.state_space runs on the larger state vector and its oil observation row matches the
     impulse response.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import soe_oilf as OF   # noqa: E402
import soe_oilw as OW   # noqa: E402

results = []


def check(name, ok, detail):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


base = dict(rho_i=0.8, rule="output", phi_x=0.2, hab=0.7, phi_e=0.1, omega_H=0.3, omega_F=0.5, phi_pi=1.6, lam_h=0.4, kappa=0.3,
            a_o=0.037, s_o=0.030, eps_o=0.2, rho_o=0.9, rho_u=0.4, chi_o=6.0)
gap = 0.0
for s in ("v", "a", "ystar", "pistar", "zeta", "o", "u"):
    r1, r2 = OW.irf(OW.Params(**base), s, 0.01), OF.irf(OF.Params(**base, a_f=0.0, s_f=0.19), s, 0.01)
    gap = max(gap, max(float(np.abs(r1[k] - r2[k]).max()) for k in r1))
check("T22a a_f = 0 gives soe_oilw", gap < 1e-10, f"max gap {gap:.1e} over 7 shocks and every common variable")

p = OF.Params(**base, a_f=0.091, s_f=0.19)
worst = 0.0
for s in ("v", "o", "a", "ystar"):
    r = OF.irf(p, s, 0.05, T=30)
    rlag = np.r_[0.0, r["r_f"][:-1]]
    e1 = r["pi"] - ((1 - p.a_o - p.a_f) * r["pi_c"] + p.a_o * r["pi_o"] + p.a_f * r["pi_f"])
    e2 = r["pi_f"] - (r["piH"] + r["r_f"] - rlag)
    e3 = r["r_f"] - ((1 - p.s_f) * (r["wr"] + r["X"] - r["a"]) + p.s_f * (r["q"] + r["o"] + r["X"]))
    e4 = r["X"] - ((r["psi"] + (1 - p.alpha) * r["s"]) + p.alpha * r["s"] - r["q"])
    worst = max(worst, *(float(np.abs(e).max()) for e in (e1, e2, e3, e4)))
check("T22b identities: CPI, pi_f, r_f, and the wedge X consistent with q", worst < 1e-10, f"largest residual {worst:.1e} on 4 shocks")

size = 0.10
r0 = OF.irf(OF.Params(**base, a_f=0.0, s_f=0.0), "o", size, T=8)
r1 = OF.irf(p, "o", size, T=8)
extra = float(r1["pi"][0] - r0["pi"][0])
direct = p.a_f * p.s_f * size
check("T22c flexible energy-intensive prices raise impact CPI inflation after an oil supply shock, by about a_f s_f x shock",
      0.5 * direct < extra < 1.5 * direct and r1["pi_f"][0] > 0,
      f"extra impact inflation {400 * extra:.3f} pp a year against the direct a_f s_f x shock {400 * direct:.3f}; pi_f on impact "
      f"{400 * r1['pi_f'][0]:.2f} pp a year; year-1 output with/without the component {100 * r1['y'][:4].mean():+.3f} / "
      f"{100 * r0['y'][:4].mean():+.3f}%")

code = ("import sys; sys.argv=['x','model=oilw','sample=long','gdp=stl']; import estimate_rot as A; a=(list(A.NAMES), list(A.SHOCKS)); "
        "sys.argv=['x','model=oilf','sample=long','gdp=stl']; import importlib; B=importlib.reload(A); Z=B.observables(); "
        "print(B.NAMES==a[0], B.SHOCKS==a[1], sorted(k for k in B.FIXED if k in ('a_f','s_f')), Z.shape[1], B.R.__name__)")
out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=str(HERE)).stdout.strip()
sys.argv = [sys.argv[0], "model=oilf"]
import estimate_rot as ER   # noqa: E402
sol, _ = OF.solve(p)
sds = np.ones(len(ER.SHOCKS))
Pbig, Rbig, Q, H = ER.state_space(sol, sds, base["chi_o"])
x = Rbig[:, ER.SHOCKS.index("o")] * 0.01
obs = []
for t in range(6):
    obs.append(H @ x)
    x = Pbig @ x
obs = np.array(obs)
ri = OF.irf(p, "o", 0.01, T=6)
olag = np.r_[0.0, ri["o"][:-1]]
want = 100 * (ri["o"] - olag + ri["pistar"])
dev_ss = float(np.abs(obs[:, 4] - want).max())
check("T22d model=oilf: oilw's parameters and shocks, a_f and s_f calibrated, six observables; state space = impulse response",
      out == "True True ['a_f', 's_f'] 6 soe_oilf" and dev_ss < 1e-12 and H.shape[1] == 2 * len(OF.STATES),
      f"set-up: {out or 'nothing printed'}; Dubai crude row max gap {dev_ss:.1e}")

n_pass = sum(ok for _, ok, _ in results)
print(f"\n{n_pass}/{len(results)} passed")
sys.exit(0 if n_pass == len(results) else 1)
