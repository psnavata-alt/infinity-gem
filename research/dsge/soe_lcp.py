"""DSGE research, milestone 3 (19 Oct 2026, about 1:50 AM): the small open economy with incomplete import-price pass-through
(Monacelli 2005), a foreign-price (imported inflation) shock and a BSP-style policy rule with interest smoothing.

Adds to soe_nk.py (Gali-Monacelli):
- importers buy at the world price in pesos (e + p*) and reset their peso prices with Calvo probability 1 - theta_F, so the law
  of one price fails in the short run: LOP gap psi = e + p* - pF, import inflation piF = beta E piF' + lambda_F psi;
- CPI inflation pi = (1 - alpha) piH + alpha piF; terms of trade s = pF - pH, so s = s_lag + piF - piH;
- real exchange rate q = psi + (1 - alpha) s; risk sharing c = ystar + q / sigma;
- goods market y = (1 - alpha)(c + alpha*eta*s) + alpha*(gamma*(s + psi) + ystar) (home and foreign demand for home goods);
- marginal cost mc = sigma*c + phi*y + alpha*s - (1 + phi)*a (real wage over the price of home goods, less productivity);
- foreign inflation pistar (exogenous AR(1)) with the foreign rate istar = E pistar' + sigma (E ystar' - ystar) (foreign Euler);
- policy rule i = rho_i i_lag + (1 - rho_i)(phi_pi * pi_target + phi_x * x) + v, pi_target = CPI ("cpi") or domestic ("dit").
With theta_F -> 0 the model is Gali-Monacelli again (check T11).
Monacelli, T. (2005). "Monetary Policy in a Low Pass-Through Environment." Journal of Money, Credit and Banking 37(6): 1047-1066.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

import klein

STATES = ["v", "a", "ystar", "pistar", "s_lag", "q_lag", "i_lag"]
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
    phi_pi: float = 1.5
    phi_x: float = 0.125
    rho_i: float = 0.0
    rho_v: float = 0.5
    rho_a: float = 0.66
    rho_y: float = 0.86
    rho_ps: float = 0.5
    rule: str = "cpi"
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

    def f(xp, x):
        g = lambda n: x[ix[n]]
        e = lambda n: xp[ix[n]]
        target = g("pi") if p.rule == "cpi" else g("piH")
        return [
            e("v") - p.rho_v * g("v"),
            e("a") - p.rho_a * g("a"),
            e("ystar") - p.rho_y * g("ystar"),
            e("pistar") - p.rho_ps * g("pistar"),
            e("s_lag") - g("s"),
            e("q_lag") - g("q"),
            e("i_lag") - g("i"),
            g("c") - (e("c") - (g("i") - e("pi")) / p.sigma),                                  # Euler
            g("c") - (g("ystar") + g("q") / p.sigma),                                           # risk sharing
            g("q") - (g("psi") + (1 - p.alpha) * g("s")),                                       # real exchange rate
            g("y") - ((1 - p.alpha) * (g("c") + p.alpha * p.eta * g("s"))
                      + p.alpha * (p.gamma * (g("s") + g("psi")) + g("ystar"))),               # goods market
            g("mc") - (p.sigma * g("c") + p.phi * g("y") + p.alpha * g("s") - (1 + p.phi) * g("a")),
            g("piH") - (p.beta * e("piH") + d["lam"] * g("mc")),                                # home Phillips curve
            g("piF") - (p.beta * e("piF") + d["lamF"] * g("psi")),                              # import Phillips curve
            g("pi") - ((1 - p.alpha) * g("piH") + p.alpha * g("piF")),                          # CPI
            g("s") - (g("s_lag") + g("piF") - g("piH")),                                        # terms of trade
            g("de") - (g("q") - g("q_lag") + g("pi") - g("pistar")),                            # nominal depreciation
            g("istar") - (e("pistar") + p.sigma * (e("ystar") - g("ystar"))),                   # foreign Euler
            g("x") - (g("y") - d["Gamma_a"] * g("a") - d["Gamma_star"] * g("ystar")),           # output gap (flexible-price GM)
            g("i") - (p.rho_i * g("i_lag") + (1 - p.rho_i) * (p.phi_pi * target + p.phi_x * g("x")) + g("v")),
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
