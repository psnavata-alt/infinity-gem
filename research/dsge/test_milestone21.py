"""DSGE research, milestone 21 tests (20 Oct 2026, about 9:20 AM): oil supply and world oil demand (soe_oilw.py).

T21a reduction: with chi_o = 0, soe_oilw gives soe_oilu's responses to all seven shocks on every variable.
T21b decomposition: with chi_o > 0, after a world-output shock the oil price is exactly chi_o x world output at every horizon
     (o = o_s + chi_o ystar with o_s = 0), and a pure oil supply shock leaves world output at zero.
T21c estimation set-up: model=oilw adds the parameter chi_o and nothing else to model=oilu (same shocks), and the data gain the
     observable dystar (G3 GDP growth), missing exactly where GDP is (the COVID quarters on the long sample).
T21d state space = impulse responses: the Kalman filter's shock loading and observation rows (estimate_rot.state_space) give,
     after a world-output shock, the same observable paths (Dubai crude change, world output growth, GDP growth) as soe_oilw.irf.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import soe_oilu as OU   # noqa: E402
import soe_oilw as OW   # noqa: E402

results = []


def check(name, ok, detail):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


base = dict(rho_i=0.8, rule="output", phi_x=0.2, hab=0.7, phi_e=0.1, omega_H=0.3, omega_F=0.5, phi_pi=1.6, lam_h=0.4, kappa=0.3,
            a_o=0.037, s_o=0.030, eps_o=0.2, rho_o=0.9, rho_u=0.4)
gap = 0.0
for s in ("v", "a", "ystar", "pistar", "zeta", "o", "u"):
    r1, r2 = OU.irf(OU.Params(**base), s, 0.01), OW.irf(OW.Params(**base, chi_o=0.0), s, 0.01)
    gap = max(gap, max(float(np.abs(r1[k] - r2[k]).max()) for k in r1))
check("T21a chi_o = 0 gives soe_oilu", gap < 1e-12, f"max gap {gap:.1e} over 7 shocks and every variable")

chi = 6.0
r = OW.irf(OW.Params(**base, chi_o=chi), "ystar", 0.01, T=30)
dev = float(np.abs(r["o"] - chi * r["ystar"]).max())
rs = OW.irf(OW.Params(**base, chi_o=chi), "o", 0.10, T=30)
check("T21b oil price = chi_o x world output after a demand shock; a supply shock leaves world output at zero",
      dev < 1e-12 and float(np.abs(rs["ystar"]).max()) == 0.0 and abs(rs["o"][0] - 0.10) < 1e-15,
      f"max |o - chi ystar| {dev:.1e}; supply shock: world output max {float(np.abs(rs['ystar']).max()):.1e}, o on impact {rs['o'][0]:.3f}")

code = ("import sys; sys.argv=['x','model=oilu','sample=long','gdp=stl']; import estimate_rot as A; a=(A.NAMES, A.SHOCKS); "
        "sys.argv=['x','model=oilw','sample=long','gdp=stl']; import importlib; B=importlib.reload(A); Z=B.observables(); "
        "import numpy as np; print(sorted(set(B.NAMES)-set(a[0])), sorted(set(B.SHOCKS)-set(a[1])), sorted(set(a[0])-set(B.NAMES)), "
        "Z.shape[1], bool((np.isnan(Z[:,5])==np.isnan(Z[:,0])).all()), int(np.isnan(Z[:,5]).sum()))")
out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=str(HERE)).stdout.strip()
check("T21c model=oilw adds chi_o only; data gain dystar, missing where GDP is", out == "['chi_o'] [] [] 6 True 8",
      f"added names, shocks, removed names, columns, same missing pattern, missing quarters: {out or 'nothing printed'}")

sys.argv = [sys.argv[0], "model=oilw"]
import estimate_rot as ER   # noqa: E402
p = OW.Params(**base, chi_o=chi)
sol, _ = OW.solve(p)
sds = np.ones(len(ER.SHOCKS))
Pbig, Rbig, Q, H = ER.state_space(sol, sds, chi)
x = Rbig[:, ER.SHOCKS.index("ystar")] * 0.01
obs = []
for t in range(6):
    obs.append(H @ x)
    x = Pbig @ x
obs = np.array(obs)
ri = OW.irf(p, "ystar", 0.01, T=6)
ylag = np.r_[0.0, ri["y"][:-1]]
olag = np.r_[0.0, ri["o"][:-1]]
ystlag = np.r_[0.0, ri["ystar"][:-1]]
want = np.c_[100 * (ri["y"] - ylag), 100 * (ri["o"] - olag + ri["pistar"]), 100 * (ri["ystar"] - ystlag)]
dev_ss = float(np.abs(obs[:, [0, 4, 5]] - want).max())
check("T21d state space (loading, observation rows) = impulse responses after a world-output shock", dev_ss < 1e-12,
      f"max gap {dev_ss:.1e} in GDP growth, Dubai crude change and world output growth over 6 quarters; doil on impact "
      f"{obs[0, 4]:.3f} = 100 x chi_o x 0.01 = {100 * chi * 0.01:.3f}")

n_pass = sum(ok for _, ok, _ in results)
print(f"\n{n_pass}/{len(results)} passed")
sys.exit(0 if n_pass == len(results) else 1)
