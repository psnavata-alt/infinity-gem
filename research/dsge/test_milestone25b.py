"""DSGE research, milestone 25b tests (23 Oct 2026, night): soe_htmkf plus sticky nominal wages (soe_htmkw.py).

T25g nesting: with theta_w = 0 (flexible wages), every one of soe_htmkf's seven shocks gives the same responses in soe_htmkw, on
     every common variable, to 1e-12.
T25h the wage block: along the responses to every shock (theta_w 0.75), theta_w (1 + eps_w phi)(piW - beta piW') =
     (1 - theta_w)(1 - beta theta_w)(mrs - wr) and wr = wr(-1) + piW - pi, to 1e-12 (perfect-foresight paths after the impact
     quarter); and sticky wages smooth real marginal cost: its unconditional s.d. at the milestone 24 posterior mean falls from
     theta_w 0 to 0.75 to 0.9.
T25i determinacy at the milestone 24 posterior mean with sticky wages (theta_w 0.6, 0.75, 0.9) and the Calvo at 0.73, 0.85, 0.956.
T25j estimation set-up: model=htmkw is model=htmkf plus theta_w (beta(0.75, 0.10)); eps_w calibrated at 4.5; me_inv last.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy import linalg

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import soe_htmkf as HF   # noqa: E402
import soe_htmkw as HW   # noqa: E402

results = []


def check(name, ok, detail):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


SHOCKS7 = ("v", "a", "ystar", "pistar", "zeta", "u", "ei")
m24 = dict(rule="output", sigma=1.699, theta=0.956, theta_F=0.529, hab=0.747, omega_H=0.222, omega_F=0.106, lam_h=0.580, kappa=0.685,
           phi_i=5.911, psi_u=0.380, phi_pi=1.261, phi_x=0.357, phi_e=0.104, rho_i=0.941, rho_a=0.738, rho_y=0.739, rho_ps=0.313,
           rho_v=0.503, rho_z=0.781, rho_u=0.381, rho_ei=0.513, alpha_k=0.5, i_y=0.24, delta=0.025, a_f=0.091)

gap = 0.0
for s in SHOCKS7:
    r1, r2 = HF.irf(HF.Params(**m24), s, 0.01), HW.irf(HW.Params(**m24, theta_w=0.0), s, 0.01)
    for n in HF.STATES + HF.JUMPS:
        gap = max(gap, float(np.max(np.abs(r1[n] - r2[n]))))
check("T25g nesting: with theta_w = 0, soe_htmkf's seven shocks give identical responses", gap < 1e-12,
      f"largest gap {gap:.1e} over 7 shocks and {len(HF.STATES + HF.JUMPS)} common variables")

p = HW.Params(**m24, theta_w=0.75)
b, tw = p.beta, p.theta_w
worst = 0.0
for s in SHOCKS7:
    r = HW.irf(p, s, 0.01, T=30)
    mrs = p.sigma / (1 - p.hab) * (r["c"] - p.hab * r["c_lag"]) + p.phi * r["n"]
    e1 = tw * (1 + p.eps_w * p.phi) * (r["piW"][1:-1] - b * r["piW"][2:]) - (1 - tw) * (1 - b * tw) * (mrs[1:-1] - r["wr"][1:-1])
    e2 = r["wr"] - (r["wr_lag"] + r["piW"] - r["pi"])
    worst = max(worst, float(np.abs(e1).max()), float(np.abs(e2).max()))


def sd_mc(theta_w):
    q = HW.Params(**m24, theta_w=theta_w)
    sol, _ = HW.solve(q)
    sds = np.array([0.079, 0.677, 0.099, 2.432, 0.372, 0.348, 1.262]) / 100.0
    Rm = np.zeros((len(HW.STATES), 7))
    for j, s in enumerate(SHOCKS7):
        Rm[HW.STATES.index(s), j] = 1.0
    S = linalg.solve_discrete_lyapunov(sol.P, Rm @ np.diag(sds ** 2) @ Rm.T)
    f = sol.F[HW.JUMPS.index("mc")]
    return 100 * float(np.sqrt(f @ S @ f))


sds_ = [sd_mc(t) for t in (0.0, 0.75, 0.9)]
check("T25h the wage curve and real-wage identity hold along the responses; sticky wages smooth real marginal cost",
      worst < 1e-12 and sds_[0] > sds_[1] > sds_[2],
      f"largest residual {worst:.1e} over 7 shocks; s.d. of real marginal cost {sds_[0]:.2f} / {sds_[1]:.2f} / {sds_[2]:.2f}% "
      "at theta_w 0 / 0.75 / 0.9")

ok, notes = True, []
for tw_ in (0.6, 0.75, 0.9):
    for th in (0.73, 0.85, 0.956):
        try:
            HW.solve(HW.Params(**{**m24, "theta": th}, theta_w=tw_))
            notes.append(f"{tw_}/{th}: solves")
        except Exception as exc:                                # noqa: BLE001
            ok = False
            notes.append(f"{tw_}/{th}: {type(exc).__name__}")
check("T25i determinacy with sticky wages (theta_w / Calvo)", ok, "; ".join(notes))

code = ("import sys; sys.argv=['x','model=htmkf','prior=ratio2','sample=long','gdp=stl','obs=inv']; import estimate_rot as A; "
        "a=(list(A.NAMES), list(A.SHOCKS), dict(A.FIXED)); "
        "sys.argv=['x','model=htmkw','prior=ratio2','sample=long','gdp=stl','obs=inv']; import importlib; B=importlib.reload(A); "
        "e=[x for x in B.EST if x[0]=='theta_w'][0]; "
        "print(sorted(set(B.NAMES)-set(a[0])), B.SHOCKS==a[1], B.FIXED=={**a[2], 'eps_w': 4.5}, e[1:4], B.R.__name__, B.NAMES[-1])")
out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=str(HERE)).stdout.strip()
check("T25j model=htmkw: model=htmkf's parameters plus theta_w beta(0.75, 0.10); eps_w 4.5 calibrated; me_inv last",
      out == "['theta_w'] True True ('beta', 0.75, 0.1) soe_htmkw me_inv", f"set-up: {out or 'nothing printed'}")

n_pass = sum(ok for _, ok, _ in results)
print(f"\ntest_milestone25b: {n_pass}/{len(results)} passed")
sys.exit(0 if n_pass == len(results) else 1)
