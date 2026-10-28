"""DSGE research, milestone 26 tests (24 Oct 2026): the sticky-wage capital DSGE with oil (soe_htmkwo.py).

T26a nesting: with a_o = s_o = s_f = chi_o = 0, every one of soe_htmkw's seven shocks gives the same responses in soe_htmkwo, on
     every common variable, to 1e-12 (at milestone 25's W1 posterior mean, sticky wages on).
T26b the oil block's identities along an oil-supply response (calibration a_o 0.037, s_o 0.030, s_f 0.19, a_f 0.091): the CPI
     aggregation, pi_o = o - o_lag + pistar + de, the oil demand oin = mc + y - (q + o + X), the production function and the
     services' price r_f, to 1e-12; an oil-supply shock raises headline inflation on impact by at least oil's direct CPI weight
     times the peso oil-price change (a_o x pi_o), and raises the flexible services' relative price.
T26c the oil-demand loading: a world-output innovation moves the real oil price by chi_o on impact (loading()), and an oil
     SUPPLY innovation leaves world output unchanged.
T26d determinacy at the W1 posterior mean with the oil block, at the Calvo 0.63, 0.73, 0.79, 0.91 and the wage Calvo 0.90-0.96.
T26e estimation set-up: model=htmkwo obs=inv is model=htmkw obs=inv plus rho_o, chi_o and sd_o (soe_oilw's priors); the oil
     calibration (a_o, s_o, eps_o, s_f) added to soe_htmkw's; seven observables (Dubai crude and G3 growth before investment); a
     finite log likelihood at the W1 mean with the oil parameters at soe_oilf's posterior means.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import soe_htmkw as HW    # noqa: E402
import soe_htmkwo as HO   # noqa: E402

results = []


def check(name, ok, detail):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


SHOCKS7 = ("v", "a", "ystar", "pistar", "zeta", "u", "ei")
# milestone 25, run W1 (outputs/dsge_smc_20261023_0503_htmkw_w1_ratio2_long_stl_inv_n3000_seed15_chains.md): posterior means
w1 = dict(rule="output", sigma=1.655, theta=0.786, theta_F=0.647, theta_w=0.933, hab=0.743, omega_H=0.291, omega_F=0.219,
          lam_h=0.525, kappa=0.661, phi_i=5.245, psi_u=0.573, phi_pi=1.224, phi_x=0.348, phi_e=0.113, rho_i=0.942, rho_a=0.805,
          rho_y=0.761, rho_ps=0.330, rho_v=0.498, rho_z=0.822, rho_u=0.498, rho_ei=0.375, alpha_k=0.5, i_y=0.24, delta=0.025,
          a_f=0.091, eps_w=4.5)
oil = dict(a_o=0.037, s_o=0.030, s_f=0.19, eps_o=0.2, rho_o=0.911, chi_o=6.94)       # soe_oilf's posterior (21 Oct, 3:19 AM)

gap = 0.0
for s in SHOCKS7:
    r1, r2 = HW.irf(HW.Params(**w1), s, 0.01), HO.irf(HO.Params(**w1), s, 0.01)
    for n in HW.STATES + HW.JUMPS:
        gap = max(gap, float(np.max(np.abs(r1[n] - r2[n]))))
check("T26a nesting: with the oil block off, soe_htmkw's seven shocks give identical responses", gap < 1e-12,
      f"largest gap {gap:.1e} over 7 shocks and {len(HW.STATES + HW.JUMPS)} common variables")

p = HO.Params(**w1, **oil)
r = HO.irf(p, "o", 0.10, T=30)
fuel = r["q"] + r["o"] + r["X"]
va = (1 - p.alpha_k) * (r["wr"] + r["X"]) + p.alpha_k * r["rk"]
res = [r["pi"] - ((1 - p.a_o - p.a_f) * r["pi_c"] + p.a_o * r["pi_o"] + p.a_f * r["pi_f"]),
       r["pi_o"] - (r["o"] - r["o_lag"] + r["pistar"] + r["de"]),
       r["oin"] - (r["mc"] + r["y"] - fuel),
       r["y"] - (r["a"] + (1 - p.s_o) * (p.alpha_k * (r["k"] + r["z"]) + (1 - p.alpha_k) * r["n"]) + p.s_o * r["oin"]),
       r["r_f"] - ((1 - p.s_f) * (va - r["a"]) + p.s_f * fuel)]
worst = max(float(np.abs(x).max()) for x in res)
direct = p.a_o * r["pi_o"][0]
check("T26b the oil block's identities; an oil supply shock raises headline inflation and the services' relative price",
      worst < 1e-12 and r["pi"][0] >= direct > 0 and r["r_f"][0] > 0,
      f"largest residual {worst:.1e}; 10% oil supply shock: impact headline {400 * r['pi'][0]:+.2f} pp a year (oil's direct "
      f"part {400 * direct:+.2f}), services' relative price {100 * r['r_f'][0]:+.2f}%, year-1 output "
      f"{100 * r['y'][:4].mean():+.2f}%")

rw = HO.irf(p, "ystar", 0.01, T=5)
ro = HO.irf(p, "o", 0.10, T=5)
check("T26c the oil-demand loading: a world-output innovation moves o by chi_o; an oil supply innovation leaves world output",
      abs(rw["o"][0] - p.chi_o * 0.01) < 1e-14 and float(np.abs(ro["ystar"]).max()) == 0.0,
      f"o on impact {rw['o'][0]:.4f} against chi_o x 0.01 = {p.chi_o * 0.01:.4f}; world output after the oil shock "
      f"{float(np.abs(ro['ystar']).max()):.1e}")

ok, notes = True, []
for tw_ in (0.90, 0.933, 0.96):
    for th in (0.63, 0.73, 0.79, 0.91):
        try:
            HO.solve(HO.Params(**{**w1, "theta": th, "theta_w": tw_}, **oil))
            notes.append(f"{tw_}/{th}: solves")
        except Exception as exc:                                # noqa: BLE001
            ok = False
            notes.append(f"{tw_}/{th}: {type(exc).__name__}")
check("T26d determinacy with the oil block (wage Calvo / price Calvo)", ok, "; ".join(notes))

code = ("import sys; import numpy as np; sys.argv=['x','model=htmkw','prior=ratio2','sample=long','gdp=stl','obs=inv']; "
        "import estimate_rot as A; a=(list(A.NAMES), list(A.SHOCKS), dict(A.FIXED)); "
        "sys.argv=['x','model=htmkwo','prior=ratio2','sample=long','gdp=stl','obs=inv']; import importlib; B=importlib.reload(A); "
        "pr={e[0]: e[1:4] for e in B.EST}; Z=B.observables(); "
        "base={'sigma':1.655,'theta':0.786,'theta_F':0.647,'theta_w':0.933,'hab':0.743,'omega_H':0.291,'omega_F':0.219,'lam_h':0.525,"
        "'kappa':0.661,'phi_i':5.245,'psi_u':0.573,'phi_pi':1.224,'phi_x':0.348,'phi_e':0.113,'rho_i':0.942,'rho_a':0.805,'rho_y':0.761,"
        "'rho_ps':0.330,'rho_v':0.498,'rho_z':0.822,'rho_u':0.498,'rho_ei':0.375,'sd_v':0.078,'sd_a':1.55,'sd_ystar':0.108,"
        "'sd_pistar':2.444,'sd_zeta':0.49,'sd_u':0.293,'sd_ei':1.545,'me_inv':3.70,'rho_o':0.911,'chi_o':6.94,'sd_o':13.8}; "
        "th=np.array([base[n] for n in B.NAMES]); pc=B.pieces(th, Z); "
        "print(sorted(set(B.NAMES)-set(a[0])), B.SHOCKS==a[1]+['o'], "
        "B.FIXED=={**a[2], 'a_o':0.037, 's_o':0.030, 'eps_o':0.2, 's_f':0.19}, pr['chi_o'], pr['sd_o'], Z.shape[1], "
        "B.NAMES[-1], B.R.__name__, bool(pc is not None and np.isfinite(pc[1])))")
out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=str(HERE)).stdout.strip()
check("T26e model=htmkwo obs=inv: model=htmkw's parameters plus rho_o, chi_o, sd_o; oil calibration; seven observables",
      out == "['chi_o', 'rho_o', 'sd_o'] True True ('gamma', 5.0, 4.0) ('invgamma', 12.0, 6.0) 7 me_inv soe_htmkwo True",
      f"set-up: {out or 'nothing printed'}")

n_pass = sum(ok for _, ok, _ in results)
print(f"\ntest_milestone26: {n_pass}/{len(results)} passed")
sys.exit(0 if n_pass == len(results) else 1)
