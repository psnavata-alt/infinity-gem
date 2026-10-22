"""DSGE research, milestone 25b (23 Oct 2026, night):
soe_htmkf plus sticky nominal wages (Calvo wage setting), so that real marginal cost is no longer the households' marginal rate
of substitution every quarter. A new file, so that soe_htmkf and soe_htmki stay reproducible. Research code; no Infinity GEM result
uses it. Built at about 1:00 AM, estimated only if soe_htmkf leaves the Calvo parameter at its bound (a condition set in advance).

Why (research/dsge/README.md, milestone 25): with flexible wages the real wage equals the marginal rate of substitution each
quarter, mrs = sigma / (1 - hab) (c - hab c(-1)) + phi n, about 6.7 times consumption's movement at the estimated habits, so
real marginal cost has a standard deviation of about 7% a quarter; only a nearly flat Phillips curve (Calvo at its bound) keeps
CPI inflation near its observed volatility, and below about 0.90 the transmission ratio crosses its singularity (a tightening
raises inflation). With the domestic Calvo fixed at the micro-data 0.73 the stickiness moves to import prices instead (milestone
25, run A1: the import Calvo at its bound). Christiano, Eichenbaum and Evans (2005) found sticky wages, not sticky prices, to be
the key nominal rigidity (with them, price contracts of about two quarters fit US data); Smets and Wouters (2007) estimate both.
Philippine minimum wages are set in pesos by the regional wage boards about once a year, and LFS pay barely moved in 2026.
Why Calvo wages and not a partial-adjustment real wage (Blanchard and Gali 2007), the first alternative considered (both nest
at zero rigidity): on a scratch profile at the milestone 24 posterior mean (`outputs/dsge_price_block_fix_22Oct2026_results.md`)
sticky nominal wages removed the singularity and the inverted transmission at every Calvo value, while the partial-adjustment
real wage (0.5-0.95) left both in place: the inertia that matters is in the nominal wage.
The wage block (Erceg, Henderson and Levin 2000; Smets and Wouters 2007 without wage indexation or a wage-markup shock), in log
deviations, with wr the real (CPI) wage and piW wage inflation:
    theta_w (1 + eps_w phi) (piW - beta E piW') = (1 - theta_w)(1 - beta theta_w) (mrs - wr)
    wr = wr(-1) + piW - pi
i.e. the textbook piW = beta E piW' + lambda_w (mrs - wr), lambda_w = (1 - theta_w)(1 - beta theta_w) / (theta_w (1 + eps_w phi)),
multiplied through so that theta_w = 0 gives wr = mrs exactly: soe_htmkf (test_milestone25b.py, T25g). Hours are
demand-determined (households supply the hours firms demand at the set wage); wr, not mrs, enters marginal cost and the rental
rate; hand-to-mouth income is unchanged (cr = y - X). eps_w, the elasticity of substitution between labour types, is calibrated
at 4.5 (Gali 2015, chapter 6: a wage markup of about 29%); only lambda_w is identified, so eps_w just scales theta_w's reading.
Estimation: estimate_rot.py model=htmkw (soe_htmkf's parameters plus theta_w, prior beta(0.75, 0.10): a mean wage duration of
one year, the wage boards' rhythm; Smets and Wouters' US prior is beta(0.5, 0.1)).
Blanchard, O., and J. Gali (2007). "Real Wage Rigidities and the New Keynesian Model." Journal of Money, Credit and Banking
39(1): 35-65. Erceg, C. J., D. W. Henderson and A. T. Levin (2000). "Optimal Monetary Policy with Staggered Wage and Price
Contracts." Journal of Monetary Economics 46(2): 281-313. Christiano, L. J., M. Eichenbaum and C. L. Evans (2005). Journal of
Political Economy 113(1): 1-45. Smets, F., and R. Wouters (2007). American Economic Review 97(3): 586-606. Gali, J. (2015).
Monetary Policy, Inflation, and the Business Cycle, 2nd ed. Princeton University Press.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

import klein
import soe_htmkf

STATES = soe_htmkf.STATES + ["wr_lag"]
JUMPS = soe_htmkf.JUMPS + ["wr", "piW"]


@dataclass
class Params(soe_htmkf.Params):
    theta_w: float = 0.0      # Calvo wage parameter (0 = flexible wages: soe_htmkf)
    eps_w: float = 4.5        # elasticity of substitution between labour types (Gali 2015, ch. 6)


def system(p: Params):
    if p.gH or p.gF:
        raise ValueError("soe_htmkw builds on soe_htm: set gH = gF = 0")
    if not 0.0 <= p.lam_h < 1.0 or not 0.0 <= p.kappa < 1.0:
        raise ValueError("lam_h and kappa must be in [0, 1)")
    if not 0.0 <= p.alpha_k < 1.0 or not 0.0 <= p.i_y < 1.0 or not 0.0 < p.delta < 1.0 or p.phi_i <= 0.0 or not 0.0 < p.psi_u <= 1.0:
        raise ValueError("alpha_k and i_y in [0, 1), delta in (0, 1), phi_i > 0, psi_u in (0, 1]")
    if not 0.0 <= p.rho_ei < 1.0:
        raise ValueError("rho_ei must be in [0, 1)")
    if not 0.0 <= p.a_f < 1.0:
        raise ValueError("a_f must be in [0, 1)")
    if not 0.0 <= p.theta_w < 1.0 or p.eps_w <= 0.0:
        raise ValueError("theta_w must be in [0, 1) and eps_w > 0")
    names = STATES + JUMPS
    ix = {n: k for k, n in enumerate(names)}
    sh = p.sigma / (1 - p.hab)
    bH, fH, lH = p.gg(p.theta, p.omega_H)
    bF, fF, lF = p.gg(p.theta_F, p.omega_F)
    k_, ak, iy, dl, phi_i, b, af = p.kappa, p.alpha_k, p.i_y, p.delta, p.phi_i, p.beta, p.a_f
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
        mrs = mu(g("c"), g("c_lag")) + p.phi * g("n")
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
            e("r_f_lag") - g("r_f"),
            e("wr_lag") - g("wr"),                                                                      # milestone 25b
            mu(g("co"), g("co_lag")) - (mu(Eco, g("co")) - (g("i") - Epi)),
            mu(g("co"), g("co_lag")) - (mu(g("ystar"), g("ystar_lag")) + g("q") - g("zeta")),
            g("q") - (g("psi") + (1 - p.alpha) * g("s") + af * (p.alpha * g("s") - g("r_f"))),
            g("y") - ((1 - p.alpha) * (z + p.alpha * p.eta * g("s")) + p.alpha * (p.gamma * (g("s") + g("psi")) + g("ystar"))),
            g("mc") - ((1 - ak) * (g("wr") + g("X")) + ak * g("rk") - g("a")),                           # milestone 25b: wr
            g("piH") - (bH * g("piH_lag") + fH * e("piH") + lH * g("mc") + g("u")),
            g("piF") - (bF * g("piF_lag") + fF * e("piF") + lF * g("psi")),
            g("pi") - ((1 - af) * g("pi_c") + af * g("pi_f")),
            g("s") - (g("s_lag") + g("piF") - g("piH")),
            g("de") - (g("q") - g("q_lag") + g("pi") - g("pistar")),
            g("istar") - (e("pistar") + p.sigma * (e("ystar") - g("ystar"))),
            g("x") - (g("y") - d["Gamma_a"] * g("a") - d["Gamma_star"] * g("ystar")),
            g("i") - (p.rho_i * g("i_lag") + (1 - p.rho_i) * (p.phi_pi * g("pi") + p.phi_x * gap + p.phi_e * g("de")) + g("v")),
            g("cr") - (g("y") - g("X")),
            g("c") - ((1 - p.lam_h) * g("co") + p.lam_h * g("cr")),
            g("y") - (g("a") + ak * (g("k") + g("z")) + (1 - ak) * g("n")),
            g("inv") - ((g("inv_lag") + b * e("inv") + g("qk") / phi_i) / (1 + b) + g("ei")),
            g("qk") - (-(g("i") - e("pi")) + wq * e("qk") + wr_ * e("rk")),
            g("rk") - (g("wr") + g("X") + g("n") - g("k") - g("z")),                                    # milestone 25b: wr
            g("z") - z1 * g("rk"),
            g("X") - ((1 - af) * p.alpha * g("s") + af * g("r_f")),
            g("pi_c") - ((1 - p.alpha) * g("piH") + p.alpha * g("piF")),
            g("r_f") - g("mc"),
            g("pi_f") - (g("piH") + g("r_f") - g("r_f_lag")),
            lhs_w * (g("piW") - b * e("piW")) - rhs_w * (mrs - g("wr")),                                # milestone 25b: wage curve
            g("wr") - (g("wr_lag") + g("piW") - g("pi")),                                                # milestone 25b
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
