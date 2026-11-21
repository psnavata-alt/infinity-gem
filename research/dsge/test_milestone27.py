"""DSGE research, milestone 27 tests (12 Nov 2026): soe_htmkwoi.py (soe_htmkwo plus wage indexation iota_w and an opt-in CES
elasticity sig_o between oil and value added).

T27a nesting: with iota_w = 0 and sig_o = 1, every one of soe_htmkwo's eight shocks gives the same responses in soe_htmkwoi, on
     every variable, to 1e-12 (milestone 25's W1 posterior mean with soe_oilf's oil parameters, as test_milestone26.py).
T27b flexible wages: with theta_w = 0 the real wage equals the marginal rate of substitution every quarter whatever iota_w (0.6);
     at Calvo 0.9 (at W1's 0.786 flexible wages have no stable solution in soe_htmkwo either: milestone 25).
T27c the indexed wage curve holds along an oil-supply response (iota_w 0.5): theta_w (1 + eps_w phi)[(piW - iota_w pi_lag)
     - beta (piW' - iota_w pi)] = (1 - theta_w)(1 - beta theta_w)(mrs - wr), to 1e-12 (the response's next quarter is the
     expectation, no later shocks).
T27d CES oil demand: oin = (y - a) - sig_o (q + o + X - mc - a) along an oil-supply response at sig_o 0.1, to 1e-12, and a lower
     sig_o makes oil use fall less in the shock's first quarter.
T27e determinacy at the W1 mean with the oil block, iota_w 0, 0.3, 0.6, 0.85.
T27f estimation set-up: model=htmkwoi obs=inv is model=htmkwo obs=inv plus iota_w right after theta_w (prior beta(0.5, 0.15)),
     same calibration, seven observables; at the same parameters with iota_w = 0 the log likelihood equals model=htmkwo's
     (to 1e-8; computed directly, since iota_w = 0 is just outside the prior's range 0.01-0.99 and pieces() returns None).
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import soe_htmkwo as HO    # noqa: E402
import soe_htmkwoi as HI   # noqa: E402

results = []


def check(name, ok, detail):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


SHOCKS8 = ("v", "a", "ystar", "pistar", "zeta", "u", "ei", "o")
# as test_milestone26.py: milestone 25's W1 posterior means and soe_oilf's oil posterior
w1 = dict(rule="output", sigma=1.655, theta=0.786, theta_F=0.647, theta_w=0.933, hab=0.743, omega_H=0.291, omega_F=0.219,
          lam_h=0.525, kappa=0.661, phi_i=5.245, psi_u=0.573, phi_pi=1.224, phi_x=0.348, phi_e=0.113, rho_i=0.942, rho_a=0.805,
          rho_y=0.761, rho_ps=0.330, rho_v=0.498, rho_z=0.822, rho_u=0.498, rho_ei=0.375, alpha_k=0.5, i_y=0.24, delta=0.025,
          a_f=0.091, eps_w=4.5)
oil = dict(a_o=0.037, s_o=0.030, s_f=0.19, eps_o=0.2, rho_o=0.911, chi_o=6.94)

gap = 0.0
for s in SHOCKS8:
    r1, r2 = HO.irf(HO.Params(**w1, **oil), s, 0.01), HI.irf(HI.Params(**w1, **oil), s, 0.01)
    for n in HO.STATES + HO.JUMPS:
        gap = max(gap, float(np.max(np.abs(r1[n] - r2[n]))))
check("T27a nesting: iota_w 0 and sig_o 1 give soe_htmkwo's responses to all eight shocks", gap < 1e-12,
      f"largest gap {gap:.1e} over 8 shocks and {len(HO.STATES + HO.JUMPS)} variables")


def mrs(p, r):
    return p.sigma / (1 - p.hab) * (r["c"] - p.hab * r["c_lag"]) + p.phi * r["n"]


# Calvo 0.9: with flexible wages at W1's Calvo 0.786 neither soe_htmkwo nor soe_htmkwoi has a stable solution (milestone 25)
pf = HI.Params(**{**w1, "theta": 0.9, "theta_w": 0.0, "iota_w": 0.6}, **oil)
worst = 0.0
for s in ("o", "v", "a"):
    r = HI.irf(pf, s, 0.01, T=20)
    worst = max(worst, float(np.abs(r["wr"] - mrs(pf, r)).max()))
check("T27b flexible wages: wr = mrs every quarter with theta_w 0, whatever iota_w", worst < 1e-12, f"largest gap {worst:.1e}")

pi_ = HI.Params(**w1, **oil, iota_w=0.5)
r = HI.irf(pi_, "o", 0.10, T=30)
b, tw, iw = pi_.beta, pi_.theta_w, pi_.iota_w
lhs = tw * (1 + pi_.eps_w * pi_.phi) * ((r["piW"][:-1] - iw * r["pi_lag"][:-1]) - b * (r["piW"][1:] - iw * r["pi"][:-1]))
rhs = (1 - tw) * (1 - b * tw) * (mrs(pi_, r)[:-1] - r["wr"][:-1])
res = float(np.abs(lhs - rhs).max())
check("T27c the indexed wage curve holds along an oil-supply response (iota_w 0.5)", res < 1e-12,
      f"largest residual {res:.1e}; year-1 output {100 * r['y'][:4].mean():+.3f}% for a 10% oil supply shock")

ps = HI.Params(**w1, **oil, sig_o=0.1)
r = HI.irf(ps, "o", 0.10, T=30)
fuel = r["q"] + r["o"] + r["X"]
res = float(np.abs(r["oin"] - ((r["y"] - r["a"]) - ps.sig_o * (fuel - r["mc"] - r["a"]))).max())
r_cd = HI.irf(HI.Params(**w1, **oil), "o", 0.10, T=5)
check("T27d CES oil demand identity (sig_o 0.1); lower sig_o, smaller first-quarter fall in oil use",
      res < 1e-12 and r["oin"][0] > r_cd["oin"][0],
      f"largest residual {res:.1e}; oil use on impact {100 * r['oin'][0]:+.2f}% (sig_o 0.1) against {100 * r_cd['oin'][0]:+.2f}% "
      "(Cobb-Douglas)")

ok, notes = True, []
for iw_ in (0.0, 0.3, 0.6, 0.85):
    try:
        HI.solve(HI.Params(**w1, **oil, iota_w=iw_))
        notes.append(f"{iw_}: solves")
    except Exception as exc:                                    # noqa: BLE001
        ok = False
        notes.append(f"{iw_}: {type(exc).__name__}")
check("T27e determinacy with wage indexation (iota_w)", ok, "; ".join(notes))

code = ("import sys; sys.path.insert(0, '.'); import numpy as np; "
        "sys.argv=['x','model=htmkwo','prior=ratio2','sample=long','gdp=stl','obs=inv']; import estimate_rot as A; "
        "a=(list(A.NAMES), list(A.SHOCKS), dict(A.FIXED)); "
        "X=np.load(sorted((A.HERE.parents[1]/'outputs').glob('dsge_smc_*_htmkwo_w1_ratio2_long_stl_inv_*_particles.npy'))[-1]); "
        "m=X.mean(0); Z=A.observables(); la=A.pieces(m, Z)[1]; "
        "sys.argv=['x','model=htmkwoi','prior=ratio2','sample=long','gdp=stl','obs=inv']; import importlib; B=importlib.reload(A); "
        "pr={e[0]: e[1:6] for e in B.EST}; th=np.insert(m, a[0].index('theta_w') + 1, 0.0); "
        "kw, sds = B.split(th); sol, _ = B.R.solve(B.R.Params(rule='output', **{**kw, **B.FIXED})); "
        "lb=B.E0.kalman_loglik(*B.state_space(sol, sds, kw.get('chi_o', 0.0)), B.observables(), **B.me_kw(th)); "
        "print(sorted(set(B.NAMES)-set(a[0])), B.NAMES.index('iota_w') == B.NAMES.index('theta_w') + 1, B.SHOCKS==a[1], "
        "B.FIXED==a[2], pr['iota_w'], B.observables().shape[1], B.R.__name__, bool(abs(la - lb) < 1e-8), f'{la:.6f}')")
out = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, cwd=str(HERE)).stdout.strip()
want = "['iota_w'] True True True ('beta', 0.5, 0.15, 0.01, 0.99) 7 soe_htmkwoi True"
NR = ""
if not sorted((HERE.parents[1] / "outputs").glob("dsge_smc_*_htmkwo_w1_ratio2_long_stl_inv_*_particles.npy")):
    # public version: the particle cloud of a long SMC estimation run is not in this repository
    NR = " (1 not run: T27f)"
    print("[NOT RUN] T27f: needs the particle cloud of a long SMC estimation run in outputs/ (not in this repository)")
else:
    check("T27f model=htmkwoi obs=inv: model=htmkwo's set-up plus iota_w; same likelihood at iota_w 0",
          out.startswith(want), f"set-up: {out or 'nothing printed'}")

n_pass = sum(ok for _, ok, _ in results)
print(f"\ntest_milestone27: {n_pass}/{len(results)} passed{NR}")
sys.exit(0 if n_pass == len(results) else 1)
