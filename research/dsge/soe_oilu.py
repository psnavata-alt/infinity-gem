"""DSGE research, milestone 19b (20 Oct 2026, about 03:25): the oil model (soe_oil.py, milestone 15) plus the domestic
cost-push shock of soe_htmu.py (milestone 19), so that the BSP's response to oil shocks is computed on the same structure as
the new candidate DSGE.
    piH = gamma_b piH_lag + gamma_f E piH' + lambda mc + u,   u' = rho_u u + e_u.
Everything else is soe_oil.py; with u never drawn the solution equals soe_oil's on every common variable (check T19d).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

import klein
import soe_oil

STATES = soe_oil.STATES + ["u"]
JUMPS = list(soe_oil.JUMPS)


@dataclass
class Params(soe_oil.Params):
    rho_u: float = 0.5        # persistence of the domestic cost-push shock


def system(p: Params):
    if p.gH or p.gF:
        raise ValueError("soe_oilu builds on soe_htm: set gH = gF = 0")
    if (p.a_o or p.s_o) and p.rule == "gap_gm":
        raise ValueError("with oil, use rule='output' (the Gali-Monacelli flexible-price gap does not include oil)")
    names = STATES + JUMPS
    ix = {n: k for k, n in enumerate(names)}
    sh = p.sigma / (1 - p.hab)
    bH, fH, lH = p.gg(p.theta, p.omega_H)
    bF, fF, lF = p.gg(p.theta_F, p.omega_F)
    k_, ao, so = p.kappa, p.a_o, p.s_o
    r_ao = ao / (1 - ao)

    def f(xp, x):
        g = lambda n: x[ix[n]]
        e = lambda n: xp[ix[n]]
        mu = lambda c, cl: sh * (c - p.hab * cl)
        gap = g("x") if p.rule == "gap_gm" else g("y")
        d = p.derived
        Eco = (1 - k_) * e("co") + k_ * g("co_lag")
        Epi = (1 - k_) * e("pi") + k_ * g("pi_lag")
        pi_rule = g("pi") if p.rule_infl == "headline" else g("pi_c")
        return [
            e("v") - p.rho_v * g("v"), e("a") - p.rho_a * g("a"), e("ystar") - p.rho_y * g("ystar"),
            e("pistar") - p.rho_ps * g("pistar"), e("zeta") - p.rho_z * g("zeta"),
            e("s_lag") - g("s"), e("q_lag") - g("q"), e("i_lag") - g("i"), e("c_lag") - g("c"),
            e("ystar_lag") - g("ystar"), e("piH_lag") - g("piH"), e("piF_lag") - g("piF"),
            e("co_lag") - g("co"), e("pi_lag") - g("pi"),
            # milestone 21 (20 Oct 2026): soe_oilw.py's oil-demand loading chi_o (o = o_s + chi_o ystar); soe_oilu has no
            # chi_o, so the term is zero and soe_oilu is unchanged (test T21a)
            e("o") - p.rho_o * g("o") - getattr(p, "chi_o", 0.0) * (e("ystar") - p.rho_o * g("ystar")), e("o_lag") - g("o"),
            e("u") - p.rho_u * g("u"),                                                                   # cost-push shock
            mu(g("co"), g("co_lag")) - (mu(Eco, g("co")) - (g("i") - Epi)),
            mu(g("co"), g("co_lag")) - (mu(g("ystar"), g("ystar_lag")) + g("q") - g("zeta")),
            g("q") - ((1 - ao) * (g("psi") + (1 - p.alpha) * g("s")) - ao * g("o")),
            g("y") - ((1 - p.alpha) * (g("c_core") + p.alpha * p.eta * g("s"))
                      + p.alpha * (p.gamma * (g("s") + g("psi")) + g("ystar"))),
            g("mc") - ((1 - so) * g("wr") + g("X") + so * (g("q") + g("o")) - g("a")),
            g("piH") - (bH * g("piH_lag") + fH * e("piH") + lH * g("mc") + g("u")),                   # + cost push
            g("piF") - (bF * g("piF_lag") + fF * e("piF") + lF * g("psi")),
            g("pi") - ((1 - ao) * g("pi_c") + ao * g("pi_o")),
            g("s") - (g("s_lag") + g("piF") - g("piH")),
            g("de") - (g("q") - g("q_lag") + g("pi") - g("pistar")),
            g("istar") - (e("pistar") + p.sigma * (e("ystar") - g("ystar"))),
            g("x") - (g("y") - d["Gamma_a"] * g("a") - d["Gamma_star"] * g("ystar")),
            g("i") - (p.rho_i * g("i_lag") + (1 - p.rho_i) * (p.phi_pi * pi_rule + p.phi_x * gap + p.phi_e * g("de")) + g("v")),
            g("cr") - (g("y") - g("X")),
            g("c") - ((1 - p.lam_h) * g("co") + p.lam_h * g("cr")),
            g("n") - (g("mc") + g("y") - g("wr") - g("X")),
            g("wr") - (mu(g("c"), g("c_lag")) + p.phi * g("n")),
            g("X") - (p.alpha * g("s") + r_ao * (g("q") + g("o"))),
            g("c_core") - (g("c") + p.eps_o * r_ao * (g("q") + g("o"))),
            g("pi_c") - ((1 - p.alpha) * g("piH") + p.alpha * g("piF")),
            g("pi_o") - (g("o") - g("o_lag") + g("pistar") + g("de")),
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
