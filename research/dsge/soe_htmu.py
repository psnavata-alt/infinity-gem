"""DSGE research, milestone 19 (20 Oct 2026, about 01:40): soe_htm.py plus a domestic cost-push (markup) shock.

Why: milestone 18b found that, even with STL-adjusted GDP, the posterior of soe_htm on 2002-2026 has a second region of higher
density where the productivity shock's s.d. is about 7.7% a quarter with very sticky domestic prices (theta 0.93): with output
demand-determined in the short run, huge productivity swings are the model's only way to move domestic marginal cost, and so
domestic inflation, without moving GDP. The model has no domestic cost-push shock, so the productivity shock stands in for
one. Philippine CPI inflation is dominated by supply shocks (food and fuel). The standard remedy is a price markup (cost-push)
shock in the domestic Phillips curve (Smets and Wouters 2007; Adolfson, Laseen, Linde and Villani 2007 for the open economy):
    piH = gamma_b piH_lag + gamma_f E piH' + lambda mc + u,   u' = rho_u u + e_u.
Everything else is soe_htm.py; with the shock never drawn the solution equals soe_htm's on every common variable (check T19a).
Smets, F., and R. Wouters (2007). "Shocks and Frictions in US Business Cycles: A Bayesian DSGE Approach." American Economic
Review 97(3): 586-606. Adolfson, M., S. Laseen, J. Linde and M. Villani (2007). "Bayesian Estimation of an Open Economy DSGE
Model with Incomplete Pass-Through." Journal of International Economics 72(2): 481-511.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

import klein
import soe_htm

STATES = soe_htm.STATES + ["u"]
JUMPS = list(soe_htm.JUMPS)


@dataclass
class Params(soe_htm.Params):
    rho_u: float = 0.5        # persistence of the domestic cost-push shock


def system(p: Params):
    if p.gH or p.gF:
        raise ValueError("soe_htmu builds on soe_htm (rule-of-thumb price setters): set gH = gF = 0")
    if not 0.0 <= p.lam_h < 1.0 or not 0.0 <= p.kappa < 1.0:
        raise ValueError("lam_h and kappa must be in [0, 1)")
    names = STATES + JUMPS
    ix = {n: k for k, n in enumerate(names)}
    sh = p.sigma / (1 - p.hab)
    bH, fH, lH = p.gg(p.theta, p.omega_H)
    bF, fF, lF = p.gg(p.theta_F, p.omega_F)
    k_ = p.kappa

    def f(xp, x):
        g = lambda n: x[ix[n]]
        e = lambda n: xp[ix[n]]
        mu = lambda c, cl: sh * (c - p.hab * cl)
        gap = g("x") if p.rule == "gap_gm" else g("y")
        d = p.derived
        Eco = (1 - k_) * e("co") + k_ * g("co_lag")
        Epi = (1 - k_) * e("pi") + k_ * g("pi_lag")
        n = g("y") - g("a")
        wr = mu(g("c"), g("c_lag")) + p.phi * n
        return [
            e("v") - p.rho_v * g("v"), e("a") - p.rho_a * g("a"), e("ystar") - p.rho_y * g("ystar"),
            e("pistar") - p.rho_ps * g("pistar"), e("zeta") - p.rho_z * g("zeta"),
            e("s_lag") - g("s"), e("q_lag") - g("q"), e("i_lag") - g("i"), e("c_lag") - g("c"),
            e("ystar_lag") - g("ystar"), e("piH_lag") - g("piH"), e("piF_lag") - g("piF"),
            e("co_lag") - g("co"), e("pi_lag") - g("pi"),
            e("u") - p.rho_u * g("u"),                                                                   # cost-push shock
            mu(g("co"), g("co_lag")) - (mu(Eco, g("co")) - (g("i") - Epi)),
            mu(g("co"), g("co_lag")) - (mu(g("ystar"), g("ystar_lag")) + g("q") - g("zeta")),
            g("q") - (g("psi") + (1 - p.alpha) * g("s")),
            g("y") - ((1 - p.alpha) * (g("c") + p.alpha * p.eta * g("s")) + p.alpha * (p.gamma * (g("s") + g("psi")) + g("ystar"))),
            g("mc") - (wr + p.alpha * g("s") - g("a")),
            g("piH") - (bH * g("piH_lag") + fH * e("piH") + lH * g("mc") + g("u")),                   # + cost push
            g("piF") - (bF * g("piF_lag") + fF * e("piF") + lF * g("psi")),
            g("pi") - ((1 - p.alpha) * g("piH") + p.alpha * g("piF")),
            g("s") - (g("s_lag") + g("piF") - g("piH")),
            g("de") - (g("q") - g("q_lag") + g("pi") - g("pistar")),
            g("istar") - (e("pistar") + p.sigma * (e("ystar") - g("ystar"))),
            g("x") - (g("y") - d["Gamma_a"] * g("a") - d["Gamma_star"] * g("ystar")),
            g("i") - (p.rho_i * g("i_lag") + (1 - p.rho_i) * (p.phi_pi * g("pi") + p.phi_x * gap + p.phi_e * g("de")) + g("v")),
            g("cr") - (g("y") - p.alpha * g("s")),
            g("c") - ((1 - p.lam_h) * g("co") + p.lam_h * g("cr")),
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
