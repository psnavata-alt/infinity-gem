"""DSGE research, milestone 6 (19 Oct 2026, about 2:20 AM): real rigidities for the small open economy, so that monetary
transmission is of a realistic size before the DSGE drives the CGE (milestone 5 found it far too strong without them).

Extends soe_lcp.py with:
- external consumption habits h (marginal utility lam = -sigma/(1 - h) (c - h c_lag)) in the Euler equation, in risk sharing and
  in the real wage (Smets and Wouters 2003; Justiniano and Preston 2010);
- inflation indexation gH, gF (hybrid Phillips curves: pi - g pi_lag = beta (E pi' - g pi) + lambda * cost);
- a risk-premium (risk-sharing wedge) shock zeta that moves the real exchange rate on its own: lam - lamstar = -q + zeta;
- the policy rule of Lubik and Schorfheide (2007): i = rho_i i_lag + (1 - rho_i)(phi_pi pi + phi_x * gap + phi_e de) + v, with
  gap = y (output deviation, rule="output") or the Gali-Monacelli flexible-price gap (rule="gap_gm", exact only when h = 0).
With h = gH = gF = 0, no zeta shock, rule="gap_gm" and phi_e = 0 the model is soe_lcp.py exactly (check T22).
Lubik, T., and F. Schorfheide (2007). "Do central banks respond to exchange rate movements? A structural investigation." Journal
of Monetary Economics 54(4): 1069-1087. Justiniano, A., and B. Preston (2010). Journal of International Economics 81(1): 61-74.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

import klein

STATES = ["v", "a", "ystar", "pistar", "zeta", "s_lag", "q_lag", "i_lag", "c_lag", "ystar_lag", "piH_lag", "piF_lag"]
JUMPS = ["y", "c", "s", "q", "psi", "piH", "piF", "pi", "i", "istar", "de", "mc", "x"]


@dataclass
class Params:
    beta: float = 0.99
    sigma: float = 2.0
    eta: float = 1.5
    gamma: float = 1.0
    alpha: float = 0.4
    phi: float = 3.0
    theta: float = 0.75
    theta_F: float = 0.75
    hab: float = 0.0
    gH: float = 0.0
    gF: float = 0.0
    phi_pi: float = 1.5
    phi_x: float = 0.125
    phi_e: float = 0.0
    rho_i: float = 0.0
    rho_v: float = 0.5
    rho_a: float = 0.66
    rho_y: float = 0.86
    rho_ps: float = 0.5
    rho_z: float = 0.8
    rule: str = "output"
    derived: dict = field(default_factory=dict, repr=False)

    def __post_init__(self):
        om = self.sigma * self.gamma + (1 - self.alpha) * (self.sigma * self.eta - 1)
        sa = self.sigma / ((1 - self.alpha) + self.alpha * om)
        lam = lambda th: (1 - th) * (1 - self.beta * th) / th
        self.derived = dict(omega=om, sigma_a=sa, lam=lam(self.theta), lamF=lam(self.theta_F),
                            Gamma_a=(1 + self.phi) / (sa + self.phi), Gamma_star=-(self.sigma - sa) / (sa + self.phi))


def system(p: Params):
    d = p.derived
    names = STATES + JUMPS
    ix = {n: k for k, n in enumerate(names)}
    sh = p.sigma / (1 - p.hab)                                   # slope of marginal utility in (c - h c_lag)

    def f(xp, x):
        g = lambda n: x[ix[n]]
        e = lambda n: xp[ix[n]]
        mu = lambda c, cl: sh * (c - p.hab * cl)                   # = -lambda (minus marginal utility)
        gap = g("x") if p.rule == "gap_gm" else g("y")
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
            (g("piH") - p.gH * g("piH_lag")) - (p.beta * (e("piH") - p.gH * g("piH")) + d["lam"] * g("mc")),
            (g("piF") - p.gF * g("piF_lag")) - (p.beta * (e("piF") - p.gF * g("piF")) + d["lamF"] * g("psi")),
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
