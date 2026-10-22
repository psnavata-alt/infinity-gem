"""DSGE research, milestone 23 (21 Oct 2026, about 1:35 AM): capital and investment
inside the candidate DSGE (soe_htmu.py), with Smets-Wouters-type investment adjustment costs. MODEL AND TESTS ONLY; estimation
later (estimate_rot.py model=htmk is wired: phi_i estimated, the shares calibrated).

Why: every model so far produces with labour alone, so monetary policy reaches output only through consumption, and the
DSGE-CGE link had to borrow an investment response (theta, not identified by Philippine data). With capital, a policy
tightening lowers investment through Tobin's q and the link's investment channel becomes the model's own.
The block (Christiano, Eichenbaum and Evans 2005; Smets and Wouters 2007, log-linear equations 3-6 without the utilisation
margin and the investment-specific shock), in log deviations, quarterly:
    k'   = (1 - delta) k + delta inv                                        capital at the end of the quarter
    inv  = [inv(-1) + beta E inv' + (1 / phi_i) qk] / (1 + beta)            investment Euler, phi_i = S''(1) the adjustment-cost curvature
    qk   = -(i - E* pi) + [(1 - delta) / (1 - delta + rk_ss)] E qk' + [rk_ss / (1 - delta + rk_ss)] E rk'     Tobin's q
    z    = [(1 - psi_u) / psi_u] rk                                         capital utilisation (Smets-Wouters eq. 7; psi_u = 1: fixed)
    rk   = (wr + alpha s) + n - (k + z)                                     rental rate from cost minimisation (Cobb-Douglas)
    y    = a + alpha_k (k + z) + (1 - alpha_k) n                            production (capital services = installed capital x utilisation)
    mc   = (1 - alpha_k)(wr + alpha s) + alpha_k rk - a                     real marginal cost
    y    = (1 - alpha)[(1 - i_y) c + i_y inv + alpha eta s] + alpha [gamma (s + psi) + ystar]     goods market with investment
with rk_ss = 1 / beta - 1 + delta, E* the optimisers' partly adaptive expectation of CPI inflation (as in their Euler equation),
and the rest of soe_htmu unchanged (hand-to-mouth households, the cost-push shock, the Lubik-Schorfheide rule). With alpha_k = 0
and i_y = 0 the model is soe_htmu exactly on every common variable (test T23a).
Why utilisation is in from the start (found 21 Oct 2026, about 2:05 AM): with fixed utilisation (psi_u = 1), the Philippine
calibration (capital share 0.5, investment 0.24 of absorption, delta 0.025, phi_i 4) has a complex pair of roots at modulus
1.0025: the accelerator (more demand -> more hours -> a higher rental rate -> a higher Tobin's q -> more investment -> more demand)
is explosive, because with a capital share of 0.5 hours must move twice as much as output. Variable utilisation damps the rental
rate's response by the factor 1 / (1 + (1 - psi_u) / psi_u), and at Smets and Wouters' prior mean psi_u = 0.5 the model is
determinate across the calibration grid (test T23e). The reduction to soe_htmu holds for any psi_u (alpha_k = i_y = 0).
Calibration for the Philippines (estimate_rot.py model=htmk): alpha_k 0.5 (Infinity GEM's own SAM v0.5 gives capital 0.60 of value added
and labour 0.38, but its capital income includes the mixed income of the self-employed; 0.5 is the usual middle ground),
i_y 0.24 (the SAM's investment over household consumption plus investment, 5,746 / 24,350), delta 0.025 a quarter (10% a year);
phi_i estimated with Smets and Wouters' prior (normal 4, s.d. 1.5, on [0.5, 15]).
Christiano, L. J., M. Eichenbaum and C. L. Evans (2005). "Nominal Rigidities and the Dynamic Effects of a Shock to Monetary
Policy." Journal of Political Economy 113(1): 1-45. Smets, F., and R. Wouters (2007). American Economic Review 97(3): 586-606.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

import klein
import soe_htmu

STATES = soe_htmu.STATES + ["k", "inv_lag"]
JUMPS = soe_htmu.JUMPS + ["n", "inv", "qk", "rk", "z"]


@dataclass
class Params(soe_htmu.Params):
    alpha_k: float = 0.0      # capital share in production (0 = labour only, soe_htmu)
    i_y: float = 0.0          # investment's share of domestic absorption (0 = soe_htmu)
    delta: float = 0.025      # depreciation a quarter
    phi_i: float = 4.0        # investment adjustment-cost curvature S''(1)
    psi_u: float = 0.5        # utilisation-cost elasticity (Smets-Wouters psi; 1 = fixed utilisation)


def system(p: Params):
    if p.gH or p.gF:
        raise ValueError("soe_htmk builds on soe_htm: set gH = gF = 0")
    if not 0.0 <= p.lam_h < 1.0 or not 0.0 <= p.kappa < 1.0:
        raise ValueError("lam_h and kappa must be in [0, 1)")
    if not 0.0 <= p.alpha_k < 1.0 or not 0.0 <= p.i_y < 1.0 or not 0.0 < p.delta < 1.0 or p.phi_i <= 0.0 or not 0.0 < p.psi_u <= 1.0:
        raise ValueError("alpha_k and i_y in [0, 1), delta in (0, 1), phi_i > 0, psi_u in (0, 1]")
    names = STATES + JUMPS
    ix = {n: k for k, n in enumerate(names)}
    sh = p.sigma / (1 - p.hab)
    bH, fH, lH = p.gg(p.theta, p.omega_H)
    bF, fF, lF = p.gg(p.theta_F, p.omega_F)
    k_, ak, iy, dl, phi_i, b = p.kappa, p.alpha_k, p.i_y, p.delta, p.phi_i, p.beta
    rk_ss = 1.0 / b - 1.0 + dl
    wq, wr_ = (1 - dl) / (1 - dl + rk_ss), rk_ss / (1 - dl + rk_ss)
    z1 = (1 - p.psi_u) / p.psi_u

    def f(xp, x):
        g = lambda n: x[ix[n]]
        e = lambda n: xp[ix[n]]
        mu = lambda c, cl: sh * (c - p.hab * cl)
        gap = g("x") if p.rule == "gap_gm" else g("y")
        d = p.derived
        Eco = (1 - k_) * e("co") + k_ * g("co_lag")
        Epi = (1 - k_) * e("pi") + k_ * g("pi_lag")
        wr = mu(g("c"), g("c_lag")) + p.phi * g("n")
        z = (1 - iy) * g("c") + iy * g("inv")                                                           # domestic absorption
        return [
            e("v") - p.rho_v * g("v"), e("a") - p.rho_a * g("a"), e("ystar") - p.rho_y * g("ystar"),
            e("pistar") - p.rho_ps * g("pistar"), e("zeta") - p.rho_z * g("zeta"),
            e("s_lag") - g("s"), e("q_lag") - g("q"), e("i_lag") - g("i"), e("c_lag") - g("c"),
            e("ystar_lag") - g("ystar"), e("piH_lag") - g("piH"), e("piF_lag") - g("piF"),
            e("co_lag") - g("co"), e("pi_lag") - g("pi"),
            e("u") - p.rho_u * g("u"),
            e("k") - ((1 - dl) * g("k") + dl * g("inv")),                                              # milestone 23
            e("inv_lag") - g("inv"),                                                                    # milestone 23
            mu(g("co"), g("co_lag")) - (mu(Eco, g("co")) - (g("i") - Epi)),
            mu(g("co"), g("co_lag")) - (mu(g("ystar"), g("ystar_lag")) + g("q") - g("zeta")),
            g("q") - (g("psi") + (1 - p.alpha) * g("s")),
            g("y") - ((1 - p.alpha) * (z + p.alpha * p.eta * g("s")) + p.alpha * (p.gamma * (g("s") + g("psi")) + g("ystar"))),
            g("mc") - ((1 - ak) * (wr + p.alpha * g("s")) + ak * g("rk") - g("a")),                     # milestone 23
            g("piH") - (bH * g("piH_lag") + fH * e("piH") + lH * g("mc") + g("u")),
            g("piF") - (bF * g("piF_lag") + fF * e("piF") + lF * g("psi")),
            g("pi") - ((1 - p.alpha) * g("piH") + p.alpha * g("piF")),
            g("s") - (g("s_lag") + g("piF") - g("piH")),
            g("de") - (g("q") - g("q_lag") + g("pi") - g("pistar")),
            g("istar") - (e("pistar") + p.sigma * (e("ystar") - g("ystar"))),
            g("x") - (g("y") - d["Gamma_a"] * g("a") - d["Gamma_star"] * g("ystar")),
            g("i") - (p.rho_i * g("i_lag") + (1 - p.rho_i) * (p.phi_pi * g("pi") + p.phi_x * gap + p.phi_e * g("de")) + g("v")),
            g("cr") - (g("y") - p.alpha * g("s")),
            g("c") - ((1 - p.lam_h) * g("co") + p.lam_h * g("cr")),
            g("y") - (g("a") + ak * (g("k") + g("z")) + (1 - ak) * g("n")),                              # milestone 23: production
            g("inv") - ((g("inv_lag") + b * e("inv") + g("qk") / phi_i) / (1 + b)),                      # milestone 23: investment
            g("qk") - (-(g("i") - e("pi")) + wq * e("qk") + wr_ * e("rk")),                             # milestone 23: Tobin's q
            g("rk") - (wr + p.alpha * g("s") + g("n") - g("k") - g("z")),                               # milestone 23: rental rate
            g("z") - z1 * g("rk"),                                                                      # milestone 23: utilisation
        ]
    A, B = klein.linearize(f, np.zeros(len(names)))
    return A, B, names


def solve(p: Params):
    A, B, names = system(p)
    return klein.solve(A, B, n_k=len(STATES)), names


def irf(p: Params, shock: str, size: float = 1.0, T: int = 40) -> dict:
    sol, names = solve(p)
    k, dpath = sol.irf(np.eye(len(STATES)), np.array([size if s == shock else 0.0 for s in STATES]), T=T)
    out = {n: k[:, j] for j, n in enumerate(STATES)}
    out.update({n: dpath[:, j] for j, n in enumerate(JUMPS)})
    return out
