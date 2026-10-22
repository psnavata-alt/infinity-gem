"""DSGE research, milestone 11 (19 Oct 2026, about 9:20 AM): hand-to-mouth households and partly adaptive expectations in
the small open economy of soe_rot.py.

Why: milestone 10 showed that the size of monetary transmission is decided in the demand block. On Philippine data alone the
forward-looking model moves output and inflation 10-15 times as much as the BSP's PAMPh after a policy shock; imposing PAMPh's
responses cost about 92 log points of likelihood and pushed sigma and phi_pi to their bounds. Two standard departures from
fully forward-looking households, both plausible for the Philippines (many households without credit; expectations that PAMPh
itself treats as backward-looking):
- hand-to-mouth households (Gali, Lopez-Salido and Valles 2007; Bilbiie 2008), a share lam_h of consumption: they consume their
  share of current real income, c_r = y - alpha s (domestic output in CPI units: p_H - p = -alpha s). Optimizers' consumption
  c_o obeys the Euler equation and international risk sharing; aggregate consumption c = (1 - lam_h) c_o + lam_h c_r enters
  the goods market and the real wage (mu(c, c_lag) + phi n). Why income, not GLV's labour income w + n: with habits the wage
  moves with consumption by sigma / (1 - h) (about 6.7 at sigma 2, h 0.7), so c_r = w + n feeds back on itself by lam_h x 6.7
  > 1 already at lam_h = 0.2 and the model has no stable solution (19 Oct, about 9:24 AM; GLV use log utility and no habits,
  Smets-Wouters-type models sticky wages). Philippine hand-to-mouth households are largely informal and self-employed, living
  on labour and mixed income, which moves with output; the feedback through the goods market, (1 - alpha) lam_h < 1, is stable;
- partly adaptive expectations in the optimizers' Euler equation: E* x' = (1 - kappa) E x' + kappa x_lag, for consumption and CPI
  inflation (a share kappa of the expectation is last quarter's value; Gaspar, Smets and Vestin 2006 discuss such departures).
With lam_h = kappa = 0 the model is soe_rot.py exactly (check T31). Real marginal cost is unchanged in form:
mc = w + alpha s - a = mu(c, c_lag) + phi y + alpha s - (1 + phi) a.
Gali, J., J. D. Lopez-Salido and J. Valles (2007). "Understanding the Effects of Government Spending on Consumption." Journal of
the European Economic Association 5(1): 227-270. Bilbiie, F. O. (2008). "Limited Asset Markets Participation, Monetary Policy
and (Inverted) Aggregate Demand Logic." Journal of Economic Theory 140(1): 162-196.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

import klein
import soe_rot

STATES = soe_rot.STATES + ["co_lag", "pi_lag"]
JUMPS = soe_rot.JUMPS + ["co", "cr"]


@dataclass
class Params(soe_rot.Params):
    lam_h: float = 0.0
    kappa: float = 0.0


def system(p: Params):
    if p.gH or p.gF:
        raise ValueError("soe_htm builds on soe_rot (rule-of-thumb price setters): set gH = gF = 0")
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
        Eco = (1 - k_) * e("co") + k_ * g("co_lag")                  # optimizers' (partly adaptive) expectations
        Epi = (1 - k_) * e("pi") + k_ * g("pi_lag")
        n = g("y") - g("a")
        wr = mu(g("c"), g("c_lag")) + p.phi * n                       # real (CPI) wage: average MRS
        return [
            e("v") - p.rho_v * g("v"), e("a") - p.rho_a * g("a"), e("ystar") - p.rho_y * g("ystar"),
            e("pistar") - p.rho_ps * g("pistar"), e("zeta") - p.rho_z * g("zeta"),
            e("s_lag") - g("s"), e("q_lag") - g("q"), e("i_lag") - g("i"), e("c_lag") - g("c"),
            e("ystar_lag") - g("ystar"), e("piH_lag") - g("piH"), e("piF_lag") - g("piF"),
            e("co_lag") - g("co"), e("pi_lag") - g("pi"),
            mu(g("co"), g("co_lag")) - (mu(Eco, g("co")) - (g("i") - Epi)),                          # optimizers' Euler
            mu(g("co"), g("co_lag")) - (mu(g("ystar"), g("ystar_lag")) + g("q") - g("zeta")),          # risk sharing + wedge
            g("q") - (g("psi") + (1 - p.alpha) * g("s")),
            g("y") - ((1 - p.alpha) * (g("c") + p.alpha * p.eta * g("s")) + p.alpha * (p.gamma * (g("s") + g("psi")) + g("ystar"))),
            g("mc") - (wr + p.alpha * g("s") - g("a")),
            g("piH") - (bH * g("piH_lag") + fH * e("piH") + lH * g("mc")),
            g("piF") - (bF * g("piF_lag") + fF * e("piF") + lF * g("psi")),
            g("pi") - ((1 - p.alpha) * g("piH") + p.alpha * g("piF")),
            g("s") - (g("s_lag") + g("piF") - g("piH")),
            g("de") - (g("q") - g("q_lag") + g("pi") - g("pistar")),
            g("istar") - (e("pistar") + p.sigma * (e("ystar") - g("ystar"))),
            g("x") - (g("y") - d["Gamma_a"] * g("a") - d["Gamma_star"] * g("ystar")),
            g("i") - (p.rho_i * g("i_lag") + (1 - p.rho_i) * (p.phi_pi * g("pi") + p.phi_x * gap + p.phi_e * g("de")) + g("v")),
            g("cr") - (g("y") - p.alpha * g("s")),                                                       # hand-to-mouth: real income
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
