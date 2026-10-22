"""DSGE research, milestone 15 (19 Oct 2026, about 2:25 PM): oil as an imported good and input in the candidate DSGE.

Design: a design note (not included). Builds on soe_htm.py (milestone 11; estimated in milestone 13).
Why: the 2026 scenarios' largest shock is oil, and the BSP's response to it (first- and second-round effects) is what the CGE lacks.
After Medina and Soto (2005) and Blanchard and Gali (2007), in log deviations:
- world real oil price o (dollars deflated by world prices), AR(1) shock; peso oil price p_o = e + p* + o, full and immediate
  pass-through (the downstream oil industry is deregulated, RA 8479, 1998; pump prices change weekly):
      pi_o = (o - o_lag) + pistar + de;
- headline CPI = (1 - a_o) core + a_o oil, core = the Gali-Monacelli index of home and imported goods:
      pi = (1 - a_o) pi_c + a_o pi_o,  pi_c = (1 - alpha) piH + alpha piF;
  the real exchange rate is CPI-based: q = (1 - a_o)(psi + (1 - alpha) s) - a_o o;
  headline over home-goods prices: X = p - p_H = alpha s + a_o / (1 - a_o) (q + o);
- production Y = A N^(1 - s_o) O^s_o (oil an input with cost share s_o): real marginal cost in home-goods prices
      mc = (1 - s_o) w + X + s_o (q + o) - a,   labour demand n = mc + y - w - X,   real wage w = mu(c, c_lag) + phi n;
- demand for core goods c_core = c + eps_o a_o / (1 - a_o) (q + o), with eps_o the elasticity of substitution between core
  goods and oil in consumption (CES). Default 0.2: short-run oil demand is very inelastic (price elasticities about 0.1-0.3), so
  an oil-price rise raises oil spending and crowds out core spending. A first version used unit elasticity (Cobb-Douglas): it
  made households buy MORE core goods after an oil-price rise and output rose on impact (19 Oct, about 2:30 PM); home output
      y = (1 - alpha)(c_core + alpha eta s) + alpha (gamma (s + psi) + ystar)
  (the GM weights are kept: an approximation that ignores the steady-state exports needed to pay for oil);
- hand-to-mouth real income c_r = y - X (home output in headline-CPI units: an oil price rise lowers it);
- the BSP's rule on headline inflation (rule_infl="headline", the BSP's target) or core (rule_infl="core", for comparison).
With a_o = s_o = 0 the model is soe_htm.py exactly (check T41). Oil is a sixth shock; the flexible-price gap x is not defined
with oil (rule="output" only when a_o or s_o > 0).
Medina, J. P., and C. Soto (2005). "Oil Shocks and Monetary Policy in an Estimated DSGE Model for a Small Open Economy."
Central Bank of Chile Working Paper 353. Blanchard, O., and J. Gali (2007). "The Macroeconomic Effects of Oil Shocks: Why are
the 2000s So Different from the 1970s?" NBER Working Paper 13368.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

import klein
import soe_htm

STATES = soe_htm.STATES + ["o", "o_lag"]
JUMPS = soe_htm.JUMPS + ["n", "wr", "X", "c_core", "pi_c", "pi_o"]


@dataclass
class Params(soe_htm.Params):
    a_o: float = 0.0          # oil's weight in headline CPI
    s_o: float = 0.0          # oil's cost share in domestic production
    rho_o: float = 0.8        # persistence of the real oil price
    eps_o: float = 0.2        # elasticity of substitution between core goods and oil in consumption
    rule_infl: str = "headline"


def system(p: Params):
    if p.gH or p.gF:
        raise ValueError("soe_oil builds on soe_htm: set gH = gF = 0")
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
            e("o") - p.rho_o * g("o"), e("o_lag") - g("o"),
            mu(g("co"), g("co_lag")) - (mu(Eco, g("co")) - (g("i") - Epi)),                          # optimizers' Euler
            mu(g("co"), g("co_lag")) - (mu(g("ystar"), g("ystar_lag")) + g("q") - g("zeta")),          # risk sharing + wedge
            g("q") - ((1 - ao) * (g("psi") + (1 - p.alpha) * g("s")) - ao * g("o")),                  # CPI-based real exchange rate
            g("y") - ((1 - p.alpha) * (g("c_core") + p.alpha * p.eta * g("s"))
                      + p.alpha * (p.gamma * (g("s") + g("psi")) + g("ystar"))),
            g("mc") - ((1 - so) * g("wr") + g("X") + so * (g("q") + g("o")) - g("a")),               # labour and oil
            g("piH") - (bH * g("piH_lag") + fH * e("piH") + lH * g("mc")),
            g("piF") - (bF * g("piF_lag") + fF * e("piF") + lF * g("psi")),
            g("pi") - ((1 - ao) * g("pi_c") + ao * g("pi_o")),
            g("s") - (g("s_lag") + g("piF") - g("piH")),
            g("de") - (g("q") - g("q_lag") + g("pi") - g("pistar")),
            g("istar") - (e("pistar") + p.sigma * (e("ystar") - g("ystar"))),
            g("x") - (g("y") - d["Gamma_a"] * g("a") - d["Gamma_star"] * g("ystar")),
            g("i") - (p.rho_i * g("i_lag") + (1 - p.rho_i) * (p.phi_pi * pi_rule + p.phi_x * gap + p.phi_e * g("de")) + g("v")),
            g("cr") - (g("y") - g("X")),                                                                 # hand-to-mouth: real income
            g("c") - ((1 - p.lam_h) * g("co") + p.lam_h * g("cr")),
            g("n") - (g("mc") + g("y") - g("wr") - g("X")),                                              # labour demand
            g("wr") - (mu(g("c"), g("c_lag")) + p.phi * g("n")),                                         # real wage = MRS
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
