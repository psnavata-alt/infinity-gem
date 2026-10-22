"""DSGE research, milestone 2 (19 Oct 2026, about 1:40 AM): the small open economy New Keynesian model of Gali and Monacelli
(2005), log-linear, solved by QZ (klein.py). It is the core of the money and financial block: the peso (terms of trade,
real and nominal exchange rates, uncovered interest parity) and a BSP interest-rate rule.

Variables (log deviations from the steady state; world variables exogenous; quarterly):
  predetermined: v (monetary-policy shock), a (domestic productivity), ystar (world output), s_lag (last quarter's terms of trade)
  forward-looking: y output, c consumption, s terms of trade, piH domestic inflation, pi CPI inflation, i policy rate, mc real
  marginal cost, x output gap
Equations (Gali 2015, ch. 8; Gali and Monacelli 2005):
  Euler           c = E c' - (1/sigma)(i - E pi')
  risk sharing    c = cstar + (1 - alpha)/sigma * s,   cstar = ystar (world goods market)
  goods market    y = c + (alpha * omega / sigma) * s
  marginal cost   mc = (sigma_a + phi) y + (sigma - sigma_a) ystar - (1 + phi) a
  Phillips curve  piH = beta E piH' + lambda mc,  lambda = (1 - theta)(1 - beta theta)/theta
  CPI inflation   pi = piH + alpha (s - s_lag)
  natural output  yn = Gamma_a a + Gamma_star ystar;  x = y - yn
  policy rule     i = phi_pi * (piH or pi) + phi_x x + v      (rule="dit" domestic inflation, "cpi" CPI inflation)
with omega = sigma*gamma + (1 - alpha)(sigma*eta - 1), sigma_a = sigma / ((1 - alpha) + alpha*omega).
Gali, J., and T. Monacelli (2005). "Monetary Policy and Exchange Rate Volatility in a Small Open Economy." Review of Economic
Studies 72(3): 707-734. Gali, J. (2015). Monetary Policy, Inflation, and the Business Cycle, 2nd ed., ch. 8.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

import klein

STATES = ["v", "a", "ystar", "s_lag"]
JUMPS = ["y", "c", "s", "piH", "pi", "i", "mc", "x"]


@dataclass
class Params:
    beta: float = 0.99
    sigma: float = 2.0         # inverse intertemporal elasticity
    eta: float = 1.5           # home-foreign substitution
    gamma: float = 1.0         # substitution among foreign goods
    alpha: float = 0.4         # openness (import share)
    phi: float = 3.0           # inverse Frisch elasticity
    theta: float = 0.75        # Calvo: share of prices not reset each quarter
    phi_pi: float = 1.5
    phi_x: float = 0.125
    rho_v: float = 0.5
    rho_a: float = 0.66
    rho_y: float = 0.86
    rule: str = "dit"
    derived: dict = field(default_factory=dict, repr=False)

    def __post_init__(self):
        om = self.sigma * self.gamma + (1 - self.alpha) * (self.sigma * self.eta - 1)
        sa = self.sigma / ((1 - self.alpha) + self.alpha * om)
        lam = (1 - self.theta) * (1 - self.beta * self.theta) / self.theta
        self.derived = dict(omega=om, sigma_a=sa, lam=lam, kappa_a=lam * (sa + self.phi),
                            Gamma_a=(1 + self.phi) / (sa + self.phi), Gamma_star=-(self.sigma - sa) / (sa + self.phi))


def system(p: Params):
    d = p.derived
    names = STATES + JUMPS
    ix = {n: k for k, n in enumerate(names)}

    def f(xp, x):
        g = lambda n: x[ix[n]]
        e = lambda n: xp[ix[n]]
        infl = g("piH") if p.rule == "dit" else g("pi")
        return [
            e("v") - p.rho_v * g("v"),
            e("a") - p.rho_a * g("a"),
            e("ystar") - p.rho_y * g("ystar"),
            e("s_lag") - g("s"),
            g("c") - (e("c") - (g("i") - e("pi")) / p.sigma),
            g("c") - (g("ystar") + (1 - p.alpha) / p.sigma * g("s")),
            g("y") - (g("c") + p.alpha * d["omega"] / p.sigma * g("s")),
            g("mc") - ((d["sigma_a"] + p.phi) * g("y") + (p.sigma - d["sigma_a"]) * g("ystar") - (1 + p.phi) * g("a")),
            g("piH") - (p.beta * e("piH") + d["lam"] * g("mc")),
            g("pi") - (g("piH") + p.alpha * (g("s") - g("s_lag"))),
            g("x") - (g("y") - d["Gamma_a"] * g("a") - d["Gamma_star"] * g("ystar")),
            g("i") - (p.phi_pi * infl + p.phi_x * g("x") + g("v")),
        ]
    A, B = klein.linearize(f, np.zeros(len(names)))        # linear model: the expansion is exact
    return A, B, names


def solve(p: Params):
    A, B, names = system(p)
    return klein.solve(A, B, n_k=len(STATES)), names


def irf(p: Params, shock: str, size: float = 1.0, T: int = 20) -> dict:
    sol, names = solve(p)
    R = np.eye(len(STATES))
    k, dpath = sol.irf(R, np.array([size if s == shock else 0.0 for s in STATES]), T=T)
    out = {n: k[:, j] for j, n in enumerate(STATES)}
    out.update({n: dpath[:, j] for j, n in enumerate(JUMPS)})
    out["de"] = out["s"] - np.concatenate([[0.0], out["s"][:-1]]) + out["piH"]      # nominal depreciation, pistar = 0
    return out
