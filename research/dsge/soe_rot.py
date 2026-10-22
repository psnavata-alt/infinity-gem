"""DSGE research, milestone 10 (19 Oct 2026, about 8:30 AM): rule-of-thumb price setters (Gali and Gertler 1999) in the
small open economy of soe_med.py, in place of indexation.

Why: matching the BSP's PAMPh responses (milestone 7) pushed soe_med's indexation to its bounds (0.97, 0.94): PAMPh's Phillips
curve is backward-looking, which full indexation mimics only at the extreme. Gali and Gertler's alternative: of the firms that
reset their price in a quarter, a share omega sets it by a rule of thumb (last quarter's average reset price, updated by last
quarter's inflation); the rest are forward-looking Calvo setters. For each Phillips curve (domestic goods theta, omega_H;
imports theta_F, omega_F; cost = real marginal cost mc, or the law-of-one-price gap psi):
    phi * pi = omega * pi_lag + beta * theta * E pi' + (1 - omega) (1 - theta) (1 - beta * theta) * cost,
    phi = theta + omega (1 - theta (1 - beta)),
i.e. pi = gamma_b pi_lag + gamma_f E pi' + lambda cost with gamma_b = omega / phi, gamma_f = beta theta / phi and
lambda = (1 - omega)(1 - theta)(1 - beta theta) / phi (Gali and Gertler 1999, eqs. 25-27). With omega = 0 this is soe_med's curve
without indexation (check T26). Everything else (habits, risk premium, Lubik-Schorfheide rule) is soe_med's, unchanged.
Gali, J., and M. Gertler (1999). "Inflation Dynamics: A Structural Econometric Analysis." Journal of Monetary Economics 44(2):
195-222.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

import klein
import soe_med

STATES, JUMPS = soe_med.STATES, soe_med.JUMPS


@dataclass
class Params(soe_med.Params):
    omega_H: float = 0.0
    omega_F: float = 0.0

    def gg(self, theta, omega):
        """Gali-Gertler reduced-form coefficients (gamma_b, gamma_f, lambda) of one Phillips curve."""
        phi = theta + omega * (1 - theta * (1 - self.beta))
        return omega / phi, self.beta * theta / phi, (1 - omega) * (1 - theta) * (1 - self.beta * theta) / phi


def system(p: Params):
    if p.gH or p.gF:
        raise ValueError("soe_rot replaces indexation with rule-of-thumb price setters: set gH = gF = 0")
    names = STATES + JUMPS
    ix = {n: k for k, n in enumerate(names)}
    sh = p.sigma / (1 - p.hab)
    bH, fH, lH = p.gg(p.theta, p.omega_H)
    bF, fF, lF = p.gg(p.theta_F, p.omega_F)

    def f(xp, x):
        g = lambda n: x[ix[n]]
        e = lambda n: xp[ix[n]]
        mu = lambda c, cl: sh * (c - p.hab * cl)
        gap = g("x") if p.rule == "gap_gm" else g("y")
        d = p.derived
        return [
            e("v") - p.rho_v * g("v"), e("a") - p.rho_a * g("a"), e("ystar") - p.rho_y * g("ystar"),
            e("pistar") - p.rho_ps * g("pistar"), e("zeta") - p.rho_z * g("zeta"),
            e("s_lag") - g("s"), e("q_lag") - g("q"), e("i_lag") - g("i"), e("c_lag") - g("c"),
            e("ystar_lag") - g("ystar"), e("piH_lag") - g("piH"), e("piF_lag") - g("piF"),
            mu(g("c"), g("c_lag")) - (mu(e("c"), g("c")) - (g("i") - e("pi"))),                       # Euler
            mu(g("c"), g("c_lag")) - (mu(g("ystar"), g("ystar_lag")) + g("q") - g("zeta")),            # risk sharing + wedge
            g("q") - (g("psi") + (1 - p.alpha) * g("s")),
            g("y") - ((1 - p.alpha) * (g("c") + p.alpha * p.eta * g("s")) + p.alpha * (p.gamma * (g("s") + g("psi")) + g("ystar"))),
            g("mc") - (mu(g("c"), g("c_lag")) + p.phi * g("y") + p.alpha * g("s") - (1 + p.phi) * g("a")),
            g("piH") - (bH * g("piH_lag") + fH * e("piH") + lH * g("mc")),                             # Gali-Gertler, home
            g("piF") - (bF * g("piF_lag") + fF * e("piF") + lF * g("psi")),                            # Gali-Gertler, imports
            g("pi") - ((1 - p.alpha) * g("piH") + p.alpha * g("piF")),
            g("s") - (g("s_lag") + g("piF") - g("piH")),
            g("de") - (g("q") - g("q_lag") + g("pi") - g("pistar")),
            g("istar") - (e("pistar") + p.sigma * (e("ystar") - g("ystar"))),
            g("x") - (g("y") - d["Gamma_a"] * g("a") - d["Gamma_star"] * g("ystar")),
            g("i") - (p.rho_i * g("i_lag") + (1 - p.rho_i) * (p.phi_pi * g("pi") + p.phi_x * gap + p.phi_e * g("de")) + g("v")),
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
