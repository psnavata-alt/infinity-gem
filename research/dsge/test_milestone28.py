"""DSGE research, milestone 28 tests (12 Nov 2026): soe_htmkwod.py (soe_htmkwoi plus dollar pricing of exports, dcp).

T28a nesting: with dcp=False every one of the eight shocks gives soe_htmkwoi's responses on every common variable, to 1e-12, with
     iota_w 0 and 0.5 (W1's posterior means with soe_oilf's oil parameters, as test_milestone26.py).
T28b the dollar export block along an oil-supply response (dcp, theta_X 0.75): tX = tX(-1) + piX - pistar; piX = beta piX' +
     lambda_X (mc - (s + psi) - tX); the goods market with exports alpha [gamma (-tX) + ystar]; all to 1e-12.
T28c dollar prices are sticky: after a risk-premium shock that depreciates the peso, the dollar price of exports falls on impact
     by less than under producer-currency pricing, and exports rise less in the first quarter.
T28d determinacy with dollar pricing: theta_X 0.5, 0.75, 0.9 with iota_w 0 and 0.5.
T28e estimation set-up: model=htmkwod obs=inv is model=htmkwoi obs=inv plus theta_X (beta(0.75, 0.10)) right after iota_w and
     dcp=True in the calibration; seven observables; a finite log likelihood at milestone 26's posterior mean with iota_w 0.3 and
     theta_X 0.75.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import soe_htmkwod as HD   # noqa: E402
import soe_htmkwoi as HI   # noqa: E402

results = []


def check(name, ok, detail):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


SHOCKS8 = ("v", "a", "ystar", "pistar", "zeta", "u", "ei", "o")
w1 = dict(rule="output", sigma=1.655, theta=0.786, theta_F=0.647, theta_w=0.933, hab=0.743, omega_H=0.291, omega_F=0.219,
          lam_h=0.525, kappa=0.661, phi_i=5.245, psi_u=0.573, phi_pi=1.224, phi_x=0.348, phi_e=0.113, rho_i=0.942, rho_a=0.805,
          rho_y=0.761, rho_ps=0.330, rho_v=0.498, rho_z=0.822, rho_u=0.498, rho_ei=0.375, alpha_k=0.5, i_y=0.24, delta=0.025,
          a_f=0.091, eps_w=4.5)
oil = dict(a_o=0.037, s_o=0.030, s_f=0.19, eps_o=0.2, rho_o=0.911, chi_o=6.94)

gap = 0.0
for iw in (0.0, 0.5):
    for s in SHOCKS8:
        r1, r2 = HI.irf(HI.Params(**w1, **oil, iota_w=iw), s, 0.01), HD.irf(HD.Params(**w1, **oil, iota_w=iw), s, 0.01)
        for n in HI.STATES + HI.JUMPS:
            gap = max(gap, float(np.max(np.abs(r1[n] - r2[n]))))
check("T28a nesting: dcp=False gives soe_htmkwoi's responses (iota_w 0 and 0.5, eight shocks)", gap < 1e-12,
      f"largest gap {gap:.1e} over {len(HI.STATES + HI.JUMPS)} common variables")

p = HD.Params(**w1, **oil, dcp=True, theta_X=0.75)
r = HD.irf(p, "o", 0.10, T=30)
b = p.beta
lamX = (1 - p.theta_X) * (1 - b * p.theta_X) / p.theta_X
c_core = r["c_core"]
z = (1 - p.i_y) * c_core + p.i_y * r["inv"]
res = [r["tX"] - (r["tX_lag"] + r["piX"] - r["pistar"]),
       (r["piX"][:-1] - (b * r["piX"][1:] + lamX * (r["mc"] - (r["s"] + r["psi"]) - r["tX"])[:-1])),
       r["y"] - ((1 - p.alpha) * (z + p.alpha * p.eta * r["s"]) + p.alpha * (p.gamma * (-r["tX"]) + r["ystar"]))]
worst = max(float(np.abs(x).max()) for x in res)
check("T28b the dollar export block's equations hold along an oil-supply response", worst < 1e-12,
      f"largest residual {worst:.1e}; 10% oil supply shock: year-1 output {100 * r['y'][:4].mean():+.3f}% (dcp, theta_X 0.75)")

pp = HD.Params(**w1, **oil)
rz_p, rz_d = HD.irf(pp, "zeta", 0.01, T=8), HD.irf(p, "zeta", 0.01, T=8)
dep = rz_p["de"][0]
exp_p, exp_d = p.alpha * p.gamma * (-rz_p["tX"][0]), p.alpha * p.gamma * (-rz_d["tX"][0])
check("T28c dollar prices are sticky: after a depreciation the dollar export price and exports move less on impact",
      abs(rz_d["tX"][0]) < abs(rz_p["tX"][0]) and exp_d < exp_p,
      f"risk-premium shock: peso {100 * dep:+.2f}% on impact; dollar export price {100 * rz_d['tX'][0]:+.3f}% (dcp) against "
      f"{100 * rz_p['tX'][0]:+.3f}% (pcp); exports' part of output {100 * exp_d:+.3f} against {100 * exp_p:+.3f} pt")

ok, notes = True, []
for iw in (0.0, 0.5):
    for tx in (0.5, 0.75, 0.9):
        try:
            HD.solve(HD.Params(**w1, **oil, iota_w=iw, dcp=True, theta_X=tx))
            notes.append(f"{iw}/{tx}: solves")
        except Exception as exc:                                # noqa: BLE001
            ok = False
            notes.append(f"{iw}/{tx}: {type(exc).__name__}")
check("T28d determinacy with dollar pricing (iota_w / theta_X)", ok, "; ".join(notes))

code = ("import sys; sys.path.insert(0, '.'); import numpy as np; "
        "sys.argv=['x','model=htmkwoi','prior=ratio2','sample=long','gdp=stl','obs=inv']; import estimate_rot as A; "
        "a=(list(A.NAMES), list(A.SHOCKS), dict(A.FIXED)); "
        "X=np.load(sorted((A.HERE.parents[1]/'outputs').glob('dsge_smc_*_htmkwo_w1_ratio2_long_stl_inv_*_particles.npy'))[-1]); "
        "m=X.mean(0); "
        "sys.argv=['x','model=htmkwod','prior=ratio2','sample=long','gdp=stl','obs=inv']; import importlib; B=importlib.reload(A); "
        "pr={e[0]: e[1:6] for e in B.EST}; th=np.insert(m, a[0].index('iota_w'), 0.3);"
        "th=np.insert(th, B.NAMES.index('theta_X'), 0.75); pc=B.pieces(th, B.observables()); "
        "print(sorted(set(B.NAMES)-set(a[0])), B.NAMES.index('theta_X') == B.NAMES.index('iota_w') + 1, B.SHOCKS==a[1], "
        "B.FIXED=={**a[2], 'dcp': True}, pr['theta_X'], B.observables().shape[1], B.R.__name__, "
        "bool(pc is not None and np.isfinite(pc[1])), f'{pc[1]:.3f}' if pc else 'none')")
out = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, cwd=str(HERE))
txt = out.stdout.strip()
want = "['theta_X'] True True True ('beta', 0.75, 0.1, 0.05, 0.97) 7 soe_htmkwod True"
NR = ""
if not sorted((HERE.parents[1] / "outputs").glob("dsge_smc_*_htmkwo_w1_ratio2_long_stl_inv_*_particles.npy")):
    # public version: the particle cloud of a long SMC estimation run is not in this repository
    NR = " (1 not run: T28e)"
    print("[NOT RUN] T28e: needs the particle cloud of a long SMC estimation run in outputs/ (not in this repository)")
else:
    check("T28e model=htmkwod obs=inv: model=htmkwoi's set-up plus theta_X and dcp=True; a finite likelihood",
          txt.startswith(want), f"set-up: {txt or out.stderr.strip()[-300:] or 'nothing printed'}")

n_pass = sum(ok for _, ok, _ in results)
print(f"\ntest_milestone28: {n_pass}/{len(results)} passed{NR}")
sys.exit(0 if n_pass == len(results) else 1)
