"""DSGE research, milestone 25 (22-23 Oct 2026, night): soe_htmki plus soe_oilf's
flexible-price share of the consumption basket, so that the domestic Calvo parameter governs only the sticky core of the CPI.
A new file, so that soe_htmki (milestone 24) and its SMC stay reproducible. Research code; no Infinity GEM result uses it.

Why: estimated with PSA's investment data, soe_htmki puts the domestic Calvo parameter at 0.956 (prices fixed about 23 quarters
on average), against the BSP's micro price data (WPS 2020-02: a price change about every ten months, a quarterly Calvo of about
0.73), and its CPI transmission is weak (-0.22 per pp of first-year tightening, the weak edge of the evidence band). In soe_htmki
every consumer price except imports is set in the one Calvo block, so the one Calvo parameter must fit the whole CPI. In the
Philippine CPI, passenger transport services and electricity (PSA 2018 weights 4.54% and 4.55%: a_f = 0.091, as in milestone 22)
reprice with their costs (fares and power rates follow fuel, generation and wage costs). Here that share is priced at marginal
cost each quarter (a flexible-price sector beside a sticky-price sector, Aoki 2001) and the Calvo parameter governs only the core.

DESIGN CHOICE (the minimal port of soe_oilf's mechanism, milestone 22):
- soe_oilf prices the flexible share at r_f = p_f - p_H = (1 - s_f)(wr + X - a) + s_f (q + o + X): a labour-only unit cost plus
  a fuel cost at the oil price. soe_htmki has no oil price (it is soe_oilf's a_o = 0 with o = 0), and its firms produce with
  labour and capital services, y = a + alpha_k (k + z) + (1 - alpha_k) n. Without the oil terms soe_oilf's expression is
  wr + X - a, the real marginal cost of a labour-only technology; the coherent counterpart here is the economy's own real marginal
  cost in domestic-price units, mc = (1 - alpha_k)(wr + X) + alpha_k rk - a: the flexible firms share the domestic technology and
  keep a constant markup, so their relative price moves one for one with marginal cost:
      r_f = mc,      pi_f = piH + r_f - r_f(-1)          (with alpha_k = 0 this is soe_oilf's r_f with s_f = 0, a_o = 0).
  A fuel share s_f is left out: it needs an oil price, which soe_htmki does not have (an imported input at world prices would give
  the flexible firms an input the sticky firms do not use).
- The CPI, the CPI-based real exchange rate and the CPI-to-domestic-price wedge X = p - p_H carry the flexible component, exactly
  as soe_oilf's equations with a_o = 0:
      pi = (1 - a_f) pi_c + a_f pi_f,    pi_c = (1 - alpha) piH + alpha piF                 (pi_c: the sticky core)
      q  = psi + (1 - alpha) s + a_f (alpha s - r_f),    X = (1 - a_f) alpha s + a_f r_f     (X = alpha s when a_f = 0)
  and X replaces alpha s wherever soe_htmki converts between the CPI and domestic prices: real marginal cost and the rental rate
  (the real wage in domestic-price units is wr + X) and the hand-to-mouth households' real income, cr = y - X.
- The demand side is unchanged: the services are home-produced, so their demand stays inside domestic output and only their PRICE
  leaves the Calvo block (soe_oilf's words). soe_oilf's core-consumption substitution term eps_o a_f/(1 - a_f)(r_f - X) is not
  ported: it was built for imported oil, whose spending crowds out spending on domestic goods; for home-produced services a shift
  of spending between them and the core does not move the demand for domestic output to first order in the Gali-Monacelli
  weights, and porting it would add an elasticity with no Philippine estimate.
- The cost-push (markup) shock u stays in the sticky core's Phillips curve only: the flexible share has no Calvo block, and the
  same markup shock there would have to be scaled by 1 / lambda, which is huge where the curve is flat.
With a_f = 0 the model is soe_htmki exactly, on every common variable and in the state space (test_milestone25.py, T25a-T25b).
Estimation: estimate_rot.py model=htmkf (soe_htmki's parameters and shocks; a_f calibrated at 0.091).
Aoki, K. (2001). "Optimal Monetary Policy Responses to Relative-Price Changes." Journal of Monetary Economics 48(1): 55-80.
Blanchard, O. J., and J. Gali (2007). "The Macroeconomic Effects of Oil Price Shocks: Why Are the 2000s So Different from the
1970s?" NBER Working Paper 13368.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

import klein
import soe_htmki

STATES = soe_htmki.STATES + ["r_f_lag"]
JUMPS = soe_htmki.JUMPS + ["X", "pi_c", "r_f", "pi_f"]


@dataclass
class Params(soe_htmki.Params):
    a_f: float = 0.0          # CPI weight of the flexible-price, energy-intensive services (0 = soe_htmki)


def system(p: Params):
    if p.gH or p.gF:
        raise ValueError("soe_htmkf builds on soe_htm: set gH = gF = 0")
    if not 0.0 <= p.lam_h < 1.0 or not 0.0 <= p.kappa < 1.0:
        raise ValueError("lam_h and kappa must be in [0, 1)")
    if not 0.0 <= p.alpha_k < 1.0 or not 0.0 <= p.i_y < 1.0 or not 0.0 < p.delta < 1.0 or p.phi_i <= 0.0 or not 0.0 < p.psi_u <= 1.0:
        raise ValueError("alpha_k and i_y in [0, 1), delta in (0, 1), phi_i > 0, psi_u in (0, 1]")
    if not 0.0 <= p.rho_ei < 1.0:
        raise ValueError("rho_ei must be in [0, 1)")
    if not 0.0 <= p.a_f < 1.0:
        raise ValueError("a_f must be in [0, 1)")
    names = STATES + JUMPS
    ix = {n: k for k, n in enumerate(names)}
    sh = p.sigma / (1 - p.hab)
    bH, fH, lH = p.gg(p.theta, p.omega_H)
    bF, fF, lF = p.gg(p.theta_F, p.omega_F)
    k_, ak, iy, dl, phi_i, b, af = p.kappa, p.alpha_k, p.i_y, p.delta, p.phi_i, p.beta, p.a_f
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
            e("k") - ((1 - dl) * g("k") + dl * g("inv") + dl * (1 + b) * phi_i * g("ei")),
            e("inv_lag") - g("inv"),
            e("ei") - p.rho_ei * g("ei"),
            e("r_f_lag") - g("r_f"),                                                                    # milestone 25
            mu(g("co"), g("co_lag")) - (mu(Eco, g("co")) - (g("i") - Epi)),
            mu(g("co"), g("co_lag")) - (mu(g("ystar"), g("ystar_lag")) + g("q") - g("zeta")),
            g("q") - (g("psi") + (1 - p.alpha) * g("s") + af * (p.alpha * g("s") - g("r_f"))),          # milestone 25
            g("y") - ((1 - p.alpha) * (z + p.alpha * p.eta * g("s")) + p.alpha * (p.gamma * (g("s") + g("psi")) + g("ystar"))),
            g("mc") - ((1 - ak) * (wr + g("X")) + ak * g("rk") - g("a")),                                # milestone 25: X for alpha s
            g("piH") - (bH * g("piH_lag") + fH * e("piH") + lH * g("mc") + g("u")),
            g("piF") - (bF * g("piF_lag") + fF * e("piF") + lF * g("psi")),
            g("pi") - ((1 - af) * g("pi_c") + af * g("pi_f")),                                           # milestone 25
            g("s") - (g("s_lag") + g("piF") - g("piH")),
            g("de") - (g("q") - g("q_lag") + g("pi") - g("pistar")),
            g("istar") - (e("pistar") + p.sigma * (e("ystar") - g("ystar"))),
            g("x") - (g("y") - d["Gamma_a"] * g("a") - d["Gamma_star"] * g("ystar")),
            g("i") - (p.rho_i * g("i_lag") + (1 - p.rho_i) * (p.phi_pi * g("pi") + p.phi_x * gap + p.phi_e * g("de")) + g("v")),
            g("cr") - (g("y") - g("X")),                                                                 # milestone 25
            g("c") - ((1 - p.lam_h) * g("co") + p.lam_h * g("cr")),
            g("y") - (g("a") + ak * (g("k") + g("z")) + (1 - ak) * g("n")),
            g("inv") - ((g("inv_lag") + b * e("inv") + g("qk") / phi_i) / (1 + b) + g("ei")),
            g("qk") - (-(g("i") - e("pi")) + wq * e("qk") + wr_ * e("rk")),
            g("rk") - (wr + g("X") + g("n") - g("k") - g("z")),                                         # milestone 25: X for alpha s
            g("z") - z1 * g("rk"),
            g("X") - ((1 - af) * p.alpha * g("s") + af * g("r_f")),                                      # milestone 25: p - p_H
            g("pi_c") - ((1 - p.alpha) * g("piH") + p.alpha * g("piF")),                                 # milestone 25: the core
            g("r_f") - g("mc"),                                                                          # milestone 25: p_f - p_H
            g("pi_f") - (g("piH") + g("r_f") - g("r_f_lag")),                                            # milestone 25
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
