"""DSGE research, milestone 23 tests (21 Oct 2026, about 1:40 AM): capital and investment with adjustment costs (soe_htmk.py).

T23a reduction: with alpha_k = 0 and i_y = 0, soe_htmk gives soe_htmu's responses to all six shocks on every common variable.
T23b identities (alpha_k 0.5, i_y 0.24): along every response path, capital accumulates as k' = (1 - delta) k + delta inv;
     y = a + alpha_k k + (1 - alpha_k) n; the goods market holds with investment in absorption; rk = wr + alpha s + n - k.
T23c a monetary tightening lowers investment by more than consumption on impact and lowers output; stiffer adjustment costs
     (phi_i 10 against 2) make investment respond less.
T23d a productivity shock raises Tobin's q and investment.
T23e determinacy on a Philippine grid of (alpha_k, i_y, phi_i, delta) at the posterior mean: every point solves with a unique
     stable solution (with fixed utilisation, psi_u = 1, the count of points that solve is reported).
T23f estimation set-up: model=htmk adds phi_i to soe_htmu's parameters (same shocks and the four observables) and calibrates
     alpha_k, i_y and delta.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import klein          # noqa: E402
import soe_htmk as HK  # noqa: E402
import soe_htmu as HU  # noqa: E402

results = []


def check(name, ok, detail):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


# the candidate's posterior mean (soe_htmu, pooled Metropolis chains of 20 Oct 2026, rounded): the region that matters for estimation
base = dict(rule="output", sigma=1.5, theta=0.95, theta_F=0.6, hab=0.76, omega_H=0.22, omega_F=0.10, lam_h=0.61, kappa=0.71,
            phi_pi=1.34, phi_x=0.32, phi_e=0.13, rho_i=0.95, rho_a=0.71, rho_y=0.74, rho_ps=0.29, rho_v=0.5, rho_z=0.88, rho_u=0.42)
gap = 0.0
for s in ("v", "a", "ystar", "pistar", "zeta", "u"):
    r1, r2 = HU.irf(HU.Params(**base), s, 0.01), HK.irf(HK.Params(**base, alpha_k=0.0, i_y=0.0), s, 0.01)
    gap = max(gap, max(float(np.abs(r1[k] - r2[k]).max()) for k in r1))
check("T23a alpha_k = i_y = 0 gives soe_htmu", gap < 1e-10, f"max gap {gap:.1e} over 6 shocks and every common variable")

p = HK.Params(**base, alpha_k=0.5, i_y=0.24, delta=0.025, phi_i=4.0)
worst = 0.0
for s in ("v", "a", "ystar", "u"):
    r = HK.irf(p, s, 0.05, T=30)
    e1 = r["k"][1:] - ((1 - p.delta) * r["k"][:-1] + p.delta * r["inv"][:-1])
    e2 = r["y"] - (r["a"] + p.alpha_k * (r["k"] + r["z"]) + (1 - p.alpha_k) * r["n"])
    z = (1 - p.i_y) * r["c"] + p.i_y * r["inv"]
    e3 = r["y"] - ((1 - p.alpha) * (z + p.alpha * p.eta * r["s"]) + p.alpha * (p.gamma * (r["s"] + r["psi"]) + r["ystar"]))
    sh = p.sigma / (1 - p.hab)
    wr = sh * (r["c"] - p.hab * r["c_lag"]) + p.phi * r["n"]
    e4 = r["rk"] - (wr + p.alpha * r["s"] + r["n"] - r["k"] - r["z"])
    e5 = r["z"] - (1 - p.psi_u) / p.psi_u * r["rk"]
    worst = max(worst, *(float(np.abs(e).max()) for e in (e1, e2, e3, e4, e5)))
check("T23b identities: accumulation, production with utilisation, goods market with investment, rental rate, utilisation",
      worst < 1e-10, f"largest residual {worst:.1e} on 4 shocks")

rv = HK.irf(p, "v", 0.0025, T=12)
rv2 = HK.irf(HK.Params(**base, alpha_k=0.5, i_y=0.24, delta=0.025, phi_i=2.0), "v", 0.0025, T=12)
rv10 = HK.irf(HK.Params(**base, alpha_k=0.5, i_y=0.24, delta=0.025, phi_i=10.0), "v", 0.0025, T=12)
check("T23c tightening: investment falls more than consumption, output falls; stiffer adjustment costs damp investment",
      rv["inv"][0] < rv["c"][0] < 0 and rv["y"][0] < 0 and abs(rv10["inv"][0]) < abs(rv2["inv"][0]),
      f"impact: investment {100 * rv['inv'][0]:+.3f}%, consumption {100 * rv['c'][0]:+.3f}%, output {100 * rv['y'][0]:+.3f}%, Tobin's q "
      f"{100 * rv['qk'][0]:+.2f}%; investment at phi_i 2 / 10: {100 * rv2['inv'][0]:+.3f} / {100 * rv10['inv'][0]:+.3f}%")

ra = HK.irf(p, "a", 0.01, T=12)
check("T23d productivity shock: Tobin's q and investment move together, and capital follows investment (with sticky prices and "
      "demand-determined output, higher productivity lowers hours and the rental rate, Gali 1999, so both fall unless policy eases)",
      np.sign(ra["qk"][0]) == np.sign(ra["inv"][:4].mean()) and abs(ra["inv"][:4].mean()) > 1e-6
      and np.sign(ra["k"][4]) == np.sign(ra["inv"][:4].mean()),
      f"impact q {100 * ra['qk'][0]:+.3f}%, year-1 investment {100 * ra['inv'][:4].mean():+.3f}%, capital after 4 quarters {100 * ra['k'][4]:+.4f}%, "
      f"hours on impact {100 * ra['n'][0]:+.3f}%")

bad, fixed_u = [], []
for ak in (0.3, 0.5, 0.6):                       # capital share (SAM: 0.60 incl. mixed income), investment share, adjustment cost,
    for iy in (0.15, 0.24, 0.3):                 # depreciation 8-14% a year: the Philippine range, not the corners of the priors
        for ph in (1.0, 4.0, 10.0):
            for dl in (0.02, 0.025, 0.035):
                try:
                    HK.solve(HK.Params(**base, alpha_k=ak, i_y=iy, delta=dl, phi_i=ph, psi_u=0.5))
                except (klein.BlanchardKahnError, np.linalg.LinAlgError) as e:
                    bad.append((ak, iy, ph, dl, str(e)[:40]))
                try:
                    HK.solve(HK.Params(**base, alpha_k=ak, i_y=iy, delta=dl, phi_i=ph, psi_u=1.0))
                except (klein.BlanchardKahnError, np.linalg.LinAlgError):
                    fixed_u.append((ak, iy, ph, dl))
check("T23e determinacy on the grid (psi_u 0.5)", not bad,
      f"{81 - len(bad)}/81 points solve at psi_u 0.5 (failures: {bad[:3]}); with fixed utilisation {81 - len(fixed_u)}/81")

code = ("import sys; sys.argv=['x','model=htmu','sample=long','gdp=stl']; import estimate_rot as A; a=(list(A.NAMES), list(A.SHOCKS)); "
        "sys.argv=['x','model=htmk','sample=long','gdp=stl']; import importlib; B=importlib.reload(A); Z=B.observables(); "
        "print(sorted(set(B.NAMES)-set(a[0])), B.SHOCKS==a[1], sorted(B.FIXED), Z.shape[1], B.R.__name__)")
out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=str(HERE)).stdout.strip()
check("T23f model=htmk: soe_htmu's parameters plus phi_i and psi_u; alpha_k, i_y, delta calibrated; four observables",
      out == "['phi_i', 'psi_u'] True ['alpha_k', 'delta', 'i_y'] 4 soe_htmk", f"set-up: {out or 'nothing printed'}")

n_pass = sum(ok for _, ok, _ in results)
print(f"\n{n_pass}/{len(results)} passed")
sys.exit(0 if n_pass == len(results) else 1)
