"""DSGE research, milestone 26 (24 Oct 2026):
the sticky-wage capital DSGE (soe_htmkw, milestone 25b) plus the oil block of soe_oilf (milestones 15, 21, 22), so that the BSP's
response to the 2026 oil SUPPLY shock is computed on the model whose price block is fixed. A new file, so that soe_htmkw and the
oil models stay reproducible. Research code; NOT FOR CITATION; no Infinity GEM result uses it.

Why: in every oil model so far (soe_oilw, soe_oilf) the domestic Calvo parameter is estimated at about 0.94-0.95 (a flat Phillips
curve), fuel costs barely reach domestic prices, demand switches to home goods and an oil supply shock RAISES output in year 1
(+0.56% in soe_oilf); it is contractionary only with the Calvo parameter CALIBRATED at the BSP's micro-data value 0.73-0.85
(milestone 21b). Milestone 25 found why the Calvo parameter sits at its bound (with flexible wages real marginal cost is far too
volatile for the data's calm CPI) and fixed it with sticky nominal wages (soe_htmkw: domestic Calvo 0.79, 0.63-0.91). The
question here: on that model, with the Calvo parameter ESTIMATED, does an oil supply shock lower year-1 output?

The oil block (soe_oil / soe_oilw / soe_oilf, in log deviations; the capital block of soe_htmk and the wage block of soe_htmkw
unchanged):
- world real oil price o = o_s + chi_o ystar, o_s' = rho_o o_s + e_o (oil supply separate from world oil demand; Kilian 2009);
  peso oil price with full and immediate pass-through, pi_o = o - o_lag + pistar + de;
- headline CPI  pi = (1 - a_o - a_f) pi_c + a_o pi_o + a_f pi_f   (a_o 0.037: LPG, kerosene, vehicle fuels; a_f 0.091: passenger
  transport services and electricity, priced at cost each quarter, as soe_oilf and soe_htmkf);
- CPI-based real exchange rate q = (1 - a_o)(psi + (1 - alpha) s) - a_o o + a_f (alpha s - r_f);
- the CPI-to-domestic-price wedge X = [(1 - a_o - a_f) alpha s + a_o (q + o) + a_f r_f] / (1 - a_o);
- production with capital services, labour and oil (oil cost share s_o 0.030, Infinity GEM's own SAM v0.5):
      y = a + (1 - s_o) [alpha_k (k + z) + (1 - alpha_k) n] + s_o oin,    oin = mc + y - (q + o + X)       (oil demand)
      mc = (1 - s_o) [(1 - alpha_k)(wr + X) + alpha_k rk] + s_o (q + o + X) - a                        (real marginal cost)
  with the capital-labour ratio rk = wr + X + n - k - z as in soe_htmk (Cobb-Douglas cost minimisation);
- the flexible-price services use the same capital-labour value added plus their own fuel share s_f (0.19; soe_oilf):
      r_f = p_f - p_H = (1 - s_f) [(1 - alpha_k)(wr + X) + alpha_k rk - a] + s_f (q + o + X)
  (with s_o = s_f = 0 this is soe_htmkf's r_f = mc);
- core spending is crowded out by oil spending: c_core = c + eps_o a_o / (1 - a_o) (q + o) (eps_o 0.2), and core spending, not
  total consumption, enters the demand for home output: z = (1 - i_y) c_core + i_y inv;
- hand-to-mouth real income cr = y - X (an oil-price rise lowers it through X);
- the rule on headline inflation (rule_infl="headline", the BSP's target) or core (rule_infl="core", for oil_policy's comparison).
soe_oilf's core-substitution term for the flexible services is not ported (soe_htmkf's reason: home-produced services). With
a_o = s_o = s_f = chi_o = 0 and no oil shock the model is soe_htmkw exactly on every common variable (test_milestone26.py, T26a).
Estimation: estimate_rot.py model=htmkwo obs=inv (soe_htmkw's 30 parameters plus rho_o, chi_o, sd_o: 33; seven observables: GDP
growth, CPI inflation, the policy rate, the peso, Dubai crude in dollars, G3 GDP growth, PSA investment growth).
Kilian, L. (2009). "Not All Oil Price Shocks Are Alike." American Economic Review 99(3): 1053-1069. Blanchard, O. J., and J. Gali
(2007). "The Macroeconomic Effects of Oil Price Shocks: Why Are the 2000s So Different from the 1970s?" NBER Working Paper 13368.
Medina, J. P., and C. Soto (2005). "Oil Shocks and Monetary Policy in an Estimated DSGE Model for a Small Open Economy." Central
Bank of Chile Working Paper 353.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

import klein
import soe_htmkw

STATES = soe_htmkw.STATES + ["o", "o_lag"]
JUMPS = soe_htmkw.JUMPS + ["c_core", "pi_o", "oin"]


@dataclass
class Params(soe_htmkw.Params):
    a_o: float = 0.0          # oil's weight in headline CPI
    s_o: float = 0.0          # oil's cost share in domestic production
    s_f: float = 0.0          # fuel cost share of the flexible-price services
    rho_o: float = 0.8        # persistence of the real oil price's supply component
    chi_o: float = 0.0        # world real oil price per unit of world output (the oil-demand loading)
    eps_o: float = 0.2        # elasticity of substitution between core goods and oil in consumption
    rule_infl: str = "headline"


def system(p: Params):
    if p.gH or p.gF:
        raise ValueError("soe_htmkwo builds on soe_htm: set gH = gF = 0")
    if (p.a_o or p.s_o or p.a_f) and p.rule == "gap_gm":
        raise ValueError("with oil, use rule='output' (the Gali-Monacelli flexible-price gap does not include oil)")
    if not 0.0 <= p.lam_h < 1.0 or not 0.0 <= p.kappa < 1.0:
        raise ValueError("lam_h and kappa must be in [0, 1)")
    if not 0.0 <= p.alpha_k < 1.0 or not 0.0 <= p.i_y < 1.0 or not 0.0 < p.delta < 1.0 or p.phi_i <= 0.0 or not 0.0 < p.psi_u <= 1.0:
        raise ValueError("alpha_k and i_y in [0, 1), delta in (0, 1), phi_i > 0, psi_u in (0, 1]")
    if not 0.0 <= p.rho_ei < 1.0 or not 0.0 <= p.rho_o < 1.0:
        raise ValueError("rho_ei and rho_o must be in [0, 1)")
    if not 0.0 <= p.a_o < 1.0 or not 0.0 <= p.a_f < 1.0 - p.a_o or not 0.0 <= p.s_o < 1.0 or not 0.0 <= p.s_f <= 1.0:
        raise ValueError("a_o in [0, 1), a_f in [0, 1 - a_o), s_o in [0, 1), s_f in [0, 1]")
    if not 0.0 <= p.theta_w < 1.0 or p.eps_w <= 0.0:
        raise ValueError("theta_w must be in [0, 1) and eps_w > 0")
    names = STATES + JUMPS
    ix = {n: k for k, n in enumerate(names)}
    sh = p.sigma / (1 - p.hab)
    bH, fH, lH = p.gg(p.theta, p.omega_H)
    bF, fF, lF = p.gg(p.theta_F, p.omega_F)
    k_, ak, iy, dl, phi_i, b, af = p.kappa, p.alpha_k, p.i_y, p.delta, p.phi_i, p.beta, p.a_f
    ao, so, sf, chi = p.a_o, p.s_o, p.s_f, p.chi_o
    r_ao = ao / (1 - ao)
    rk_ss = 1.0 / b - 1.0 + dl
    wq, wr_ = (1 - dl) / (1 - dl + rk_ss), rk_ss / (1 - dl + rk_ss)
    z1 = (1 - p.psi_u) / p.psi_u
    tw = p.theta_w
    lhs_w, rhs_w = tw * (1 + p.eps_w * p.phi), (1 - tw) * (1 - b * tw)

    def f(xp, x):
        g = lambda n: x[ix[n]]
        e = lambda n: xp[ix[n]]
        mu = lambda c, cl: sh * (c - p.hab * cl)
        gap = g("x") if p.rule == "gap_gm" else g("y")
        d = p.derived
        Eco = (1 - k_) * e("co") + k_ * g("co_lag")
        Epi = (1 - k_) * e("pi") + k_ * g("pi_lag")
        pi_rule = g("pi") if p.rule_infl == "headline" else g("pi_c")
        mrs = mu(g("c"), g("c_lag")) + p.phi * g("n")
        z = (1 - iy) * g("c_core") + iy * g("inv")                                                     # oil: core spending
        fuel = g("q") + g("o") + g("X")                                    # the oil price in domestic-price units
        va = (1 - ak) * (g("wr") + g("X")) + ak * g("rk")                  # value added's unit cost (capital and labour)
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
            e("r_f_lag") - g("r_f"),
            e("wr_lag") - g("wr"),
            e("o") - p.rho_o * g("o") - chi * (e("ystar") - p.rho_o * g("ystar")), e("o_lag") - g("o"),          # oil (soe_oilw)
            mu(g("co"), g("co_lag")) - (mu(Eco, g("co")) - (g("i") - Epi)),
            mu(g("co"), g("co_lag")) - (mu(g("ystar"), g("ystar_lag")) + g("q") - g("zeta")),
            g("q") - ((1 - ao) * (g("psi") + (1 - p.alpha) * g("s")) - ao * g("o") + af * (p.alpha * g("s") - g("r_f"))),
            g("y") - ((1 - p.alpha) * (z + p.alpha * p.eta * g("s")) + p.alpha * (p.gamma * (g("s") + g("psi")) + g("ystar"))),
            g("mc") - ((1 - so) * va + so * fuel - g("a")),                                                 # oil in costs
            g("piH") - (bH * g("piH_lag") + fH * e("piH") + lH * g("mc") + g("u")),
            g("piF") - (bF * g("piF_lag") + fF * e("piF") + lF * g("psi")),
            g("pi") - ((1 - ao - af) * g("pi_c") + ao * g("pi_o") + af * g("pi_f")),                       # oil in the CPI
            g("s") - (g("s_lag") + g("piF") - g("piH")),
            g("de") - (g("q") - g("q_lag") + g("pi") - g("pistar")),
            g("istar") - (e("pistar") + p.sigma * (e("ystar") - g("ystar"))),
            g("x") - (g("y") - d["Gamma_a"] * g("a") - d["Gamma_star"] * g("ystar")),
            g("i") - (p.rho_i * g("i_lag") + (1 - p.rho_i) * (p.phi_pi * pi_rule + p.phi_x * gap + p.phi_e * g("de")) + g("v")),
            g("cr") - (g("y") - g("X")),
            g("c") - ((1 - p.lam_h) * g("co") + p.lam_h * g("cr")),
            g("y") - (g("a") + (1 - so) * (ak * (g("k") + g("z")) + (1 - ak) * g("n")) + so * g("oin")),       # oil an input
            g("inv") - ((g("inv_lag") + b * e("inv") + g("qk") / phi_i) / (1 + b) + g("ei")),
            g("qk") - (-(g("i") - e("pi")) + wq * e("qk") + wr_ * e("rk")),
            g("rk") - (g("wr") + g("X") + g("n") - g("k") - g("z")),
            g("z") - z1 * g("rk"),
            g("X") - (((1 - ao - af) * p.alpha * g("s") + ao * (g("q") + g("o")) + af * g("r_f")) / (1 - ao)),
            g("pi_c") - ((1 - p.alpha) * g("piH") + p.alpha * g("piF")),
            g("r_f") - ((1 - sf) * (va - g("a")) + sf * fuel),                                              # services' fuel
            g("pi_f") - (g("piH") + g("r_f") - g("r_f_lag")),
            lhs_w * (g("piW") - b * e("piW")) - rhs_w * (mrs - g("wr")),                                   # the wage curve
            g("wr") - (g("wr_lag") + g("piW") - g("pi")),
            g("c_core") - (g("c") + p.eps_o * r_ao * (g("q") + g("o"))),                                    # oil crowds out core
            g("pi_o") - (g("o") - g("o_lag") + g("pistar") + g("de")),
            g("oin") - (g("mc") + g("y") - fuel),                                                           # oil demand
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
