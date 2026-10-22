"""DSGE research, milestone 24 (22 Oct 2026, afternoon): soe_htmk plus an investment-specific
(marginal efficiency of investment, MEI) shock. A new file, so that soe_htmk and its chains stay reproducible.

Why: estimated with PSA's investment data, soe_htmk's posterior favours a region where the Calvo parameter sits at its upper
bound (prices fixed about seven or eight years) and productivity shocks have a standard deviation of 4-5% a quarter
(`research/dsge/README.md`, 22 Oct 2026). Both point to a missing shock: with no disturbance of its own, investment's large
swings must be explained by productivity and by a nearly flat Phillips curve. Smets and Wouters (2007) found the investment-
specific shock to be a main driver of investment; Justiniano, Primiceri and Tambalotti (2010) found it the main driver of the
US business cycle.

The two changed equations, in log deviations (Smets and Wouters 2007, equations 3 and 9, with no trend growth):
    inv = [inv(-1) + beta E inv' + (1 / phi_i) qk] / (1 + beta) + ei              investment Euler with the MEI shock
    k'  = (1 - delta) k + delta inv + delta (1 + beta) phi_i ei                    capital accumulation: the same shock
                                                                                  makes each unit of investment yield more
    ei' = rho_ei ei + innovation                                                   AR(1), estimated (rho_ei, sd_ei)
Everything else is soe_htmk exactly; with ei = 0 every other shock's responses equal soe_htmk's (test T24a).
Justiniano, A., G. E. Primiceri and A. Tambalotti (2010). "Investment Shocks and Business Cycles." Journal of Monetary
Economics 57(2): 132-145. Smets, F., and R. Wouters (2007). "Shocks and Frictions in US Business Cycles: A Bayesian DSGE
Approach." American Economic Review 97(3): 586-606.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

import klein
import soe_htmk

STATES = soe_htmk.STATES + ["ei"]
JUMPS = list(soe_htmk.JUMPS)


@dataclass
class Params(soe_htmk.Params):
    rho_ei: float = 0.5       # persistence of the investment-specific shock


def system(p: Params):
    if p.gH or p.gF:
        raise ValueError("soe_htmki builds on soe_htm: set gH = gF = 0")
    if not 0.0 <= p.lam_h < 1.0 or not 0.0 <= p.kappa < 1.0:
        raise ValueError("lam_h and kappa must be in [0, 1)")
    if not 0.0 <= p.alpha_k < 1.0 or not 0.0 <= p.i_y < 1.0 or not 0.0 < p.delta < 1.0 or p.phi_i <= 0.0 or not 0.0 < p.psi_u <= 1.0:
        raise ValueError("alpha_k and i_y in [0, 1), delta in (0, 1), phi_i > 0, psi_u in (0, 1]")
    if not 0.0 <= p.rho_ei < 1.0:
        raise ValueError("rho_ei must be in [0, 1)")
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
        z = (1 - iy) * g("c") + iy * g("inv")
        return [
            e("v") - p.rho_v * g("v"), e("a") - p.rho_a * g("a"), e("ystar") - p.rho_y * g("ystar"),
            e("pistar") - p.rho_ps * g("pistar"), e("zeta") - p.rho_z * g("zeta"),
            e("s_lag") - g("s"), e("q_lag") - g("q"), e("i_lag") - g("i"), e("c_lag") - g("c"),
            e("ystar_lag") - g("ystar"), e("piH_lag") - g("piH"), e("piF_lag") - g("piF"),
            e("co_lag") - g("co"), e("pi_lag") - g("pi"),
            e("u") - p.rho_u * g("u"),
            e("k") - ((1 - dl) * g("k") + dl * g("inv") + dl * (1 + b) * phi_i * g("ei")),           # milestone 24
            e("inv_lag") - g("inv"),
            e("ei") - p.rho_ei * g("ei"),                                                               # milestone 24
            mu(g("co"), g("co_lag")) - (mu(Eco, g("co")) - (g("i") - Epi)),
            mu(g("co"), g("co_lag")) - (mu(g("ystar"), g("ystar_lag")) + g("q") - g("zeta")),
            g("q") - (g("psi") + (1 - p.alpha) * g("s")),
            g("y") - ((1 - p.alpha) * (z + p.alpha * p.eta * g("s")) + p.alpha * (p.gamma * (g("s") + g("psi")) + g("ystar"))),
            g("mc") - ((1 - ak) * (wr + p.alpha * g("s")) + ak * g("rk") - g("a")),
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
            g("y") - (g("a") + ak * (g("k") + g("z")) + (1 - ak) * g("n")),
            g("inv") - ((g("inv_lag") + b * e("inv") + g("qk") / phi_i) / (1 + b) + g("ei")),         # milestone 24
            g("qk") - (-(g("i") - e("pi")) + wq * e("qk") + wr_ * e("rk")),
            g("rk") - (wr + p.alpha * g("s") + g("n") - g("k") - g("z")),
            g("z") - z1 * g("rk"),
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
