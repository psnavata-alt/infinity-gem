"""DSGE research, milestone 25 tests (22-23 Oct 2026, night): soe_htmki plus a flexible-price share of the CPI (soe_htmkf.py).

T25a nesting, impulse responses: with a_f = 0, every one of soe_htmki's seven shocks gives the same responses in soe_htmkf, on
     every common variable, to 1e-12.
T25b nesting, state space: with a_f = 0, estimate_rot.state_space for model=htmkf and model=htmki (obs=inv) gives the same
     responses of the five observables to each shock (12 quarters, to 1e-12) and the same Kalman log likelihood on the Philippine
     data at the milestone 24 posterior mean (to 1e-8).
T25c the flexible share's price moves one for one with marginal cost (a_f = 0.091): along the responses to every shock,
     r_f = p_f - p_H = mc and pi_f = piH + mc - mc(-1); and the identities pi = (1 - a_f) pi_c + a_f pi_f,
     X = (1 - a_f) alpha s + a_f r_f, X = (psi + (1 - alpha) s) + alpha s - q (the wedge consistent with the real exchange rate).
T25d cost shocks reach the CPI faster than the core, at the milestone 24 posterior (Calvo 0.956) and at the micro-data Calvo 0.73:
     a shock that RAISES marginal cost (productivity -1%) raises impact CPI inflation more than core inflation; the cost-push
     (markup) shock u does the reverse. Why the second half: u raises the sticky core's prices over marginal cost and LOWERS real
     marginal cost (the markup rises; the BSP tightens), and the flexible share is priced at marginal cost, so after u the CPI
     rises less than the core. The statement first expected ("a positive cost-push shock raises CPI inflation more than core inflation")
     holds for a cost shock, not for the markup shock u; this test checks the mechanism in both directions instead of only one.
     With a_f = 0 the CPI and the core coincide.
T25e determinacy at the 22 Oct 2026 posterior regions, a_f = 0.091: soe_htmk's two morning regions (Calvo 0.94 and 0.97; phi_i 7.8
     and 4.9, as T24e) and the milestone 24 posterior mean with the Calvo at 0.956, 0.85 and 0.73.
T25f estimation set-up: model=htmkf has model=htmki's parameters and shocks (no new estimated parameter), a_f = 0.091 calibrated
     beside the capital calibration, five observables with obs=inv, me_inv last; theta_fix= drops the Calvo parameter.
"""
import importlib
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import soe_htmkf as HF   # noqa: E402
import soe_htmki as HI   # noqa: E402

results = []


def check(name, ok, detail):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


SHOCKS7 = ("v", "a", "ystar", "pistar", "zeta", "u", "ei")
base = dict(rule="output", sigma=1.5, theta=0.95, theta_F=0.6, hab=0.76, omega_H=0.22, omega_F=0.10, lam_h=0.61, kappa=0.71,
            phi_pi=1.34, phi_x=0.32, phi_e=0.13, rho_i=0.95, rho_a=0.71, rho_y=0.74, rho_ps=0.29, rho_v=0.5, rho_z=0.88, rho_u=0.42,
            alpha_k=0.5, i_y=0.24, delta=0.025, phi_i=4.0, psi_u=0.5, rho_ei=0.5)
# the milestone 24 posterior mean (outputs/dsge_smc_20261022_1704_htmki_w1_ratio2_long_stl_inv_n3000_seed11_chains.md), calibration added
m24 = dict(rule="output", sigma=1.699, theta=0.956, theta_F=0.529, hab=0.747, omega_H=0.222, omega_F=0.106, lam_h=0.580, kappa=0.685,
           phi_i=5.911, psi_u=0.380, phi_pi=1.261, phi_x=0.357, phi_e=0.104, rho_i=0.941, rho_a=0.738, rho_y=0.739, rho_ps=0.313,
           rho_v=0.503, rho_z=0.781, rho_u=0.381, rho_ei=0.513, alpha_k=0.5, i_y=0.24, delta=0.025)
m24_sd = np.array([0.079, 0.677, 0.099, 2.432, 0.372, 0.348, 1.262])          # sd_v, sd_a, sd_ystar, sd_pistar, sd_zeta, sd_u, sd_ei
m24_me_inv = 3.799

# T25a
gap = 0.0
for s in SHOCKS7:
    r1, r2 = HI.irf(HI.Params(**base), s, 0.01), HF.irf(HF.Params(**base, a_f=0.0), s, 0.01)
    for n in HI.STATES + HI.JUMPS:
        gap = max(gap, float(np.max(np.abs(r1[n] - r2[n]))))
check("T25a nesting: with a_f = 0, soe_htmki's seven shocks give identical responses", gap < 1e-12,
      f"largest gap {gap:.1e} over 7 shocks and {len(HI.STATES + HI.JUMPS)} common variables")


# T25b
def observable_paths(ER, sol, sds, T=12):
    Pbig, Rbig, Q, H = ER.state_space(sol, sds)
    paths = []
    for j in range(len(ER.SHOCKS)):
        x, path = Rbig[:, j] * 0.01, []
        for _ in range(T):
            path.append(H @ x)
            x = Pbig @ x
        paths.append(path)
    return np.array(paths), (Pbig, Rbig, Q, H)


args = ["prior=ratio2", "sample=long", "gdp=stl", "obs=inv"]
argv0 = list(sys.argv)
sys.argv = [argv0[0], "model=htmki"] + args
import estimate_rot as ER   # noqa: E402
Z = ER.observables()
me = np.full(Z.shape[1], 1e-4)
me[-1] = m24_me_inv ** 2
sol_i, _ = HI.solve(HI.Params(**m24))
obs_i, ss_i = observable_paths(ER, sol_i, m24_sd)
ll_i = ER.E0.kalman_loglik(*ss_i, Z, me=me)
shocks_i = list(ER.SHOCKS)
sys.argv = [argv0[0], "model=htmkf"] + args
ER = importlib.reload(ER)
sol_f, _ = HF.solve(HF.Params(**m24, a_f=0.0))
obs_f, ss_f = observable_paths(ER, sol_f, m24_sd)
ll_f = ER.E0.kalman_loglik(*ss_f, Z, me=me)
sol_f9, _ = HF.solve(HF.Params(**m24, a_f=0.091))
ll_f9 = ER.E0.kalman_loglik(*ER.state_space(sol_f9, m24_sd), Z, me=me)
sys.argv = argv0
dobs = float(np.max(np.abs(obs_i - obs_f)))
check("T25b nesting: with a_f = 0, the state space (five observables' responses, Kalman likelihood) equals soe_htmki's",
      dobs < 1e-12 and abs(ll_i - ll_f) < 1e-8 and shocks_i == list(ER.SHOCKS) and ss_f[3].shape == (5, 2 * len(HF.STATES)),
      f"observables' responses: largest gap {dobs:.1e}; log likelihood {ll_i:.6f} (soe_htmki) against {ll_f:.6f} "
      f"(gap {abs(ll_i - ll_f):.1e}); with a_f = 0.091 at the same parameters: {ll_f9:.2f}")

# T25c
p = HF.Params(**m24, a_f=0.091)
worst, worst_mc = 0.0, 0.0
for s in SHOCKS7:
    r = HF.irf(p, s, 0.01, T=30)
    mclag = np.r_[0.0, r["mc"][:-1]]
    e_mc = np.abs(r["r_f"] - r["mc"]).max()
    e_pf = np.abs(r["pi_f"] - (r["piH"] + r["mc"] - mclag)).max()
    e1 = r["pi"] - ((1 - p.a_f) * r["pi_c"] + p.a_f * r["pi_f"])
    e2 = r["X"] - ((1 - p.a_f) * p.alpha * r["s"] + p.a_f * r["r_f"])
    e3 = r["X"] - ((r["psi"] + (1 - p.alpha) * r["s"]) + p.alpha * r["s"] - r["q"])
    worst_mc = max(worst_mc, float(e_mc), float(e_pf))
    worst = max(worst, *(float(np.abs(e).max()) for e in (e1, e2, e3)))
ra = HF.irf(p, "a", -0.01, T=4)
check("T25c the flexible share is priced at marginal cost: r_f = mc and pi_f = piH + mc - mc(-1); CPI, X and q identities",
      worst_mc < 1e-12 and worst < 1e-12,
      f"largest gap to marginal cost {worst_mc:.1e}, identities {worst:.1e} over 7 shocks; after productivity -1%, mc "
      f"{100 * ra['mc'][0]:+.3f}% and p_f - p_H {100 * ra['r_f'][0]:+.3f}% on impact")

# T25d
ok, notes = True, []
for th in (0.956, 0.73):
    q = HF.Params(**{**m24, "theta": th}, a_f=0.091)
    q0 = HF.Params(**{**m24, "theta": th}, a_f=0.0)
    ra, ru = HF.irf(q, "a", -0.01, T=4), HF.irf(q, "u", 0.01, T=4)
    ra0, ru0 = HF.irf(q0, "a", -0.01, T=4), HF.irf(q0, "u", 0.01, T=4)
    ok &= bool(ra["mc"][0] > 0 and ra["pi"][0] > ra["pi_c"][0] and ru["mc"][0] < 0 and ru["pi"][0] < ru["pi_c"][0])
    ok &= bool(abs(ra0["pi"][0] - ra0["pi_c"][0]) < 1e-14 and abs(ru0["pi"][0] - ru0["pi_c"][0]) < 1e-14)
    notes.append(f"Calvo {th}: productivity -1% (mc {100 * ra['mc'][0]:+.2f}%): CPI {400 * ra['pi'][0]:+.2f} against core "
                 f"{400 * ra['pi_c'][0]:+.2f} pp a year; cost-push u +1% (mc {100 * ru['mc'][0]:+.2f}%): CPI {400 * ru['pi'][0]:+.2f} "
                 f"against core {400 * ru['pi_c'][0]:+.2f}")
check("T25d a marginal-cost shock reaches the CPI before the core; the markup shock u the reverse; a_f = 0: the same", ok,
      "; ".join(notes))

# T25e
ok, notes = True, []
points = [("soe_htmk region A", {**base, "theta": 0.94, "phi_i": 7.8}), ("soe_htmk region B", {**base, "theta": 0.97, "phi_i": 4.9}),
          ("milestone 24 mean", m24), ("m24 mean, Calvo 0.85", {**m24, "theta": 0.85}), ("m24 mean, Calvo 0.73", {**m24, "theta": 0.73})]
for lab, kw in points:
    try:
        sol, _ = HF.solve(HF.Params(**{**kw, "rho_ei": kw.get("rho_ei", 0.6)}, a_f=0.091))
        notes.append(f"{lab} (Calvo {kw['theta']}, phi_i {kw['phi_i']}): solves, largest |root| of P {np.abs(np.linalg.eigvals(sol.P)).max():.3f}")
    except Exception as exc:                                    # noqa: BLE001
        ok = False
        notes.append(f"{lab}: {type(exc).__name__}")
check("T25e determinacy with a_f = 0.091 at the 22 Oct 2026 posterior regions", ok, "; ".join(notes))

# T25f
code = ("import sys; sys.argv=['x','model=htmki','prior=ratio2','sample=long','gdp=stl','obs=inv']; import estimate_rot as A; "
        "a=(list(A.NAMES), list(A.SHOCKS), dict(A.FIXED)); "
        "sys.argv=['x','model=htmkf','prior=ratio2','sample=long','gdp=stl','obs=inv']; import importlib; B=importlib.reload(A); "
        "b=(list(B.NAMES), list(B.SHOCKS), dict(B.FIXED), B.R.__name__, B.observables().shape[1]); "
        "sys.argv=['x','model=htmkf','prior=ratio2','sample=long','gdp=stl','obs=inv','theta_fix=0.73']; C=importlib.reload(A); "
        "print(b[0]==a[0], b[1]==a[1], b[2]=={**a[2], 'a_f': 0.091}, b[3], b[4], b[0][-1], 'theta' in C.NAMES, C.FIXED.get('theta'))")
out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=str(HERE)).stdout.strip()
check("T25f model=htmkf: model=htmki's parameters and shocks, a_f = 0.091 calibrated, five observables, me_inv last",
      out == "True True True soe_htmkf 5 me_inv False 0.73", f"set-up: {out or 'nothing printed'}")

n_pass = sum(ok for _, ok, _ in results)
print(f"\ntest_milestone25: {n_pass}/{len(results)} passed")
sys.exit(0 if n_pass == len(results) else 1)
