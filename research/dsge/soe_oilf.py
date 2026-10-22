"""DSGE research, milestone 22 (21 Oct 2026, about 1:20 AM): oil pass-through OUTSIDE
the Calvo block, through a flexible-price, energy-intensive part of the consumption basket.

Why: in soe_oilw (milestone 21) the only flexible oil price in the CPI is oil itself (weight a_o = 0.037: LPG, kerosene, vehicle
fuels). Everything else oil touches (transport fares, electricity bills) sits inside the domestic Calvo sector, whose price moves
with the domestic Phillips curve; with theta estimated at about 0.95 (prices fixed for years, a flat curve) fuel costs barely
reach those prices, the oil shock lowers home goods' relative price, demand switches to them and output RISES (milestone 21).
The data say the opposite: in 2026 "energy beyond crude" (transport fares, electricity) explains more of the inflation gap than
crude itself (preshock/inflation_var.py: about 2.5 points against 0.5 by November). Here a share a_f of the basket (passenger
transport services and electricity, PSA 2018 CPI weights 4.54 + 4.55 = 9.1%) is priced each quarter at marginal cost:
    p_f = (1 - s_f) (unit labour cost in domestic-price units) + s_f (oil price in domestic-price units),
so  r_f  = p_f - p_H = (1 - s_f) (wr + X - a) + s_f (q + o + X),       pi_f = piH + r_f - r_f(-1),
with s_f the fuel cost share of those services from Infinity GEM's own 2023 SAM (v0.5): refined petroleum 16.1% of the transport
activity's cost; refined petroleum 17.1% plus coal and gas 5.0% of electricity's (the DSGE's one oil price stands for all fossil
fuels), CPI-weighted s_f = 0.19 (oil only: 0.17). The CPI, the real exchange rate, the CPI-to-domestic-price wedge X and the
core-consumption substitution term carry the new component:
    pi = (1 - a_o - a_f) pi_c + a_o pi_o + a_f pi_f,
    q  = (1 - a_o) (psi + (1 - alpha) s) - a_o o + a_f (alpha s - r_f),
    X  = [(1 - a_o - a_f) alpha s + a_o (q + o) + a_f r_f] / (1 - a_o)      (= alpha s + a_o/(1 - a_o) (q + o) when a_f = 0),
    c_core = c + eps_o [a_o/(1 - a_o) (q + o) + a_f/(1 - a_f) (r_f - X)].
Demand for the flexible services stays inside domestic output (they are home-produced); only their PRICE leaves the Calvo block.
Everything else is soe_oilw (oil supply and world oil demand, chi_o; the cost-push shock u). With a_f = 0 the model is soe_oilw
exactly on every common variable (test T22a). The question it answers (estimate_rot.py model=oilf): is an oil supply shock
contractionary with theta ESTIMATED, once fuel reaches the CPI through flexible energy-intensive prices, as it is in the data?
Related: Blanchard, O. J., and J. Gali (2007). "The Macroeconomic Effects of Oil Price Shocks: Why Are the 2000s So Different
from the 1970s?" NBER Working Paper 13368 (oil in consumption and production with flexible oil prices); Aoki, K. (2001). "Optimal
Monetary Policy Responses to Relative-Price Changes." Journal of Monetary Economics 48(1): 55-80 (a flexible-price sector beside
a sticky-price sector).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

import klein
import soe_oilu
import soe_oilw

STATES = soe_oilu.STATES + ["r_f_lag"]
JUMPS = soe_oilu.JUMPS + ["r_f", "pi_f"]


@dataclass
class Params(soe_oilw.Params):
    a_f: float = 0.0          # CPI weight of the flexible-price, energy-intensive services (0 = soe_oilw)
    s_f: float = 0.0          # fuel cost share in those services


def system(p: Params):
    if p.gH or p.gF:
        raise ValueError("soe_oilf builds on soe_htm: set gH = gF = 0")
    if (p.a_o or p.s_o or p.a_f) and p.rule == "gap_gm":
        raise ValueError("with oil, use rule='output' (the Gali-Monacelli flexible-price gap does not include oil)")
    if not 0.0 <= p.a_f < 1.0 - p.a_o or not 0.0 <= p.s_f <= 1.0:
        raise ValueError("a_f must be in [0, 1 - a_o) and s_f in [0, 1]")
    names = STATES + JUMPS
    ix = {n: k for k, n in enumerate(names)}
    sh = p.sigma / (1 - p.hab)
    bH, fH, lH = p.gg(p.theta, p.omega_H)
    bF, fF, lF = p.gg(p.theta_F, p.omega_F)
    k_, ao, so, af, sf = p.kappa, p.a_o, p.s_o, p.a_f, p.s_f
    r_ao = ao / (1 - ao)
    r_af = af / (1 - af)
    chi = getattr(p, "chi_o", 0.0)

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
            e("o") - p.rho_o * g("o") - chi * (e("ystar") - p.rho_o * g("ystar")), e("o_lag") - g("o"),
            e("u") - p.rho_u * g("u"),
            e("r_f_lag") - g("r_f"),                                                                     # milestone 22
            mu(g("co"), g("co_lag")) - (mu(Eco, g("co")) - (g("i") - Epi)),
            mu(g("co"), g("co_lag")) - (mu(g("ystar"), g("ystar_lag")) + g("q") - g("zeta")),
            g("q") - ((1 - ao) * (g("psi") + (1 - p.alpha) * g("s")) - ao * g("o") + af * (p.alpha * g("s") - g("r_f"))),
            g("y") - ((1 - p.alpha) * (g("c_core") + p.alpha * p.eta * g("s"))
                      + p.alpha * (p.gamma * (g("s") + g("psi")) + g("ystar"))),
            g("mc") - ((1 - so) * g("wr") + g("X") + so * (g("q") + g("o")) - g("a")),
            g("piH") - (bH * g("piH_lag") + fH * e("piH") + lH * g("mc") + g("u")),
            g("piF") - (bF * g("piF_lag") + fF * e("piF") + lF * g("psi")),
            g("pi") - ((1 - ao - af) * g("pi_c") + ao * g("pi_o") + af * g("pi_f")),                     # milestone 22
            g("s") - (g("s_lag") + g("piF") - g("piH")),
            g("de") - (g("q") - g("q_lag") + g("pi") - g("pistar")),
            g("istar") - (e("pistar") + p.sigma * (e("ystar") - g("ystar"))),
            g("x") - (g("y") - d["Gamma_a"] * g("a") - d["Gamma_star"] * g("ystar")),
            g("i") - (p.rho_i * g("i_lag") + (1 - p.rho_i) * (p.phi_pi * pi_rule + p.phi_x * gap + p.phi_e * g("de")) + g("v")),
            g("cr") - (g("y") - g("X")),
            g("c") - ((1 - p.lam_h) * g("co") + p.lam_h * g("cr")),
            g("n") - (g("mc") + g("y") - g("wr") - g("X")),
            g("wr") - (mu(g("c"), g("c_lag")) + p.phi * g("n")),
            g("X") - (((1 - ao - af) * p.alpha * g("s") + ao * (g("q") + g("o")) + af * g("r_f")) / (1 - ao)),   # milestone 22
            g("c_core") - (g("c") + p.eps_o * (r_ao * (g("q") + g("o")) + r_af * (g("r_f") - g("X")))),        # milestone 22
            g("pi_c") - ((1 - p.alpha) * g("piH") + p.alpha * g("piF")),
            g("pi_o") - (g("o") - g("o_lag") + g("pistar") + g("de")),
            g("r_f") - ((1 - sf) * (g("wr") + g("X") - g("a")) + sf * (g("q") + g("o") + g("X"))),              # milestone 22
            g("pi_f") - (g("piH") + g("r_f") - g("r_f_lag")),                                                  # milestone 22
        ]
    A, B = klein.linearize(f, np.zeros(len(names)))
    return A, B, names


def solve(p: Params):
    A, B, names = system(p)
    return klein.solve(A, B, n_k=len(STATES)), names


def loading(p: Params) -> np.ndarray:
    """Shock-loading matrix (states x shocks, shocks named as their states): identity, plus chi_o of the world-output shock on o."""
    G = np.eye(len(STATES))
    G[STATES.index("o"), STATES.index("ystar")] = p.chi_o
    return G


def irf(p: Params, shock: str, size: float = 1.0, T: int = 40) -> dict:
    sol, names = solve(p)
    e = loading(p) @ np.array([size if s == shock else 0.0 for s in STATES])
    k, dpath = sol.irf(np.eye(len(STATES)), e, T=T)
    out = {n: k[:, j] for j, n in enumerate(STATES)}
    out.update({n: dpath[:, j] for j, n in enumerate(JUMPS)})
    return out
