"""DSGE research, milestone 27 (12 Nov 2026; after the recommendation to add wage indexation): soe_htmkwo (sticky wages, capital, oil) plus WAGE
INDEXATION to past CPI inflation. A new file, so that soe_htmkwo (milestone 26) stays reproducible. Research code; NOT FOR
CITATION; no Infinity GEM result uses it.

Why (research/dsge/README.md, milestone 26): on soe_htmkwo, with the domestic Calvo parameter estimated (0.86), the 36% oil supply
shock still RAISES year-1 output (+0.39% under the estimated rule; 99.6% of draws positive). The one-at-a-time decomposition
(milestone26_scratch/oil_sign_decomposition.py) put the cause in the sticky NOMINAL wage: the oil-driven CPI rise cuts the real
wage by 2.3%, which lowers real marginal cost and lets domestic firms expand; with flexible wages year-1 output is -0.03%. A wage
contract with no indexation at all is not what Philippine wage setting looks like: the regional wage boards adjust minimum wages
about once a year, and the law tells them to weigh inflation since the last order (Labor Code Article 124 as amended by RA 6727:
"wage adjustment vis-a-vis the consumer price index" and "the cost of living and changes or increases therein" are among the
criteria). Smets and Wouters (2007) estimate the same feature for
the US (iota_w about 0.6) and Christiano, Eichenbaum and Evans (2005) fix it at 1.

The wage block (Smets and Wouters 2007, eq. 13 without the wage-markup shock), in log deviations, with wr the real (CPI) wage,
piW wage inflation and pi_lag last quarter's CPI inflation (already a state of the model):
    theta_w (1 + eps_w phi) [(piW - iota_w pi_lag) - beta (E piW' - iota_w pi)] = (1 - theta_w)(1 - beta theta_w) (mrs - wr)
    wr = wr(-1) + piW - pi
Wages that are not re-set in a quarter rise by iota_w times last quarter's CPI inflation. iota_w = 0 gives soe_htmkwo exactly
(test_milestone27.py, T27a); theta_w = 0 still gives wr = mrs (flexible wages) whatever iota_w.
Estimation: estimate_rot.py model=htmkwoi obs=inv (soe_htmkwo's 33 parameters with me_inv, plus iota_w with Smets and Wouters'
prior beta(0.5, 0.15): 34). sig_o is NOT estimated: it stays at 1 (milestone 26's Cobb-Douglas) unless set by hand, because the
profile at the milestone 26 posterior (milestone27_scratch/indexation_profile.py) shows that even Leontief oil (sig_o 0) moves the
year-1 output response by only 0.02 point: with sticky prices output is demand-determined and oil's cost share is 3%.

Opt-in CES between oil and value added (sig_o): at first order the unit cost is share-weighted for any CES, so only the oil
demand changes, oin = (y - a) - sig_o (q + o + X - c) with c = mc + a; sig_o = 1 is soe_htmkwo's Cobb-Douglas oin = mc + y - fuel.
Smets, F., and R. Wouters (2007). "Shocks and Frictions in US Business Cycles: A Bayesian DSGE Approach." American Economic
Review 97(3): 586-606. Christiano, L. J., M. Eichenbaum and C. L. Evans (2005). "Nominal Rigidities and the Dynamic Effects of a
Shock to Monetary Policy." Journal of Political Economy 113(1): 1-45.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

import klein
import soe_htmkwo

STATES = list(soe_htmkwo.STATES)
JUMPS = list(soe_htmkwo.JUMPS)


@dataclass
class Params(soe_htmkwo.Params):
    iota_w: float = 0.0       # wage indexation to last quarter's CPI inflation (0 = soe_htmkwo)
    sig_o: float = 1.0        # elasticity of substitution between oil and value added in production (1 = Cobb-Douglas = soe_htmkwo)


def system(p: Params):
    if not 0.0 <= p.iota_w <= 1.0:
        raise ValueError("iota_w must be in [0, 1]")
    if not 0.0 <= p.sig_o <= 1.0:
        raise ValueError("sig_o must be in [0, 1]")
    if p.gH or p.gF:
        raise ValueError("soe_htmkwoi builds on soe_htm: set gH = gF = 0")
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
    tw, iw = p.theta_w, p.iota_w
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
        z = (1 - iy) * g("c_core") + iy * g("inv")
        fuel = g("q") + g("o") + g("X")
        va = (1 - ak) * (g("wr") + g("X")) + ak * g("rk")
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
            e("o") - p.rho_o * g("o") - chi * (e("ystar") - p.rho_o * g("ystar")), e("o_lag") - g("o"),
            mu(g("co"), g("co_lag")) - (mu(Eco, g("co")) - (g("i") - Epi)),
            mu(g("co"), g("co_lag")) - (mu(g("ystar"), g("ystar_lag")) + g("q") - g("zeta")),
            g("q") - ((1 - ao) * (g("psi") + (1 - p.alpha) * g("s")) - ao * g("o") + af * (p.alpha * g("s") - g("r_f"))),
            g("y") - ((1 - p.alpha) * (z + p.alpha * p.eta * g("s")) + p.alpha * (p.gamma * (g("s") + g("psi")) + g("ystar"))),
            g("mc") - ((1 - so) * va + so * fuel - g("a")),
            g("piH") - (bH * g("piH_lag") + fH * e("piH") + lH * g("mc") + g("u")),
            g("piF") - (bF * g("piF_lag") + fF * e("piF") + lF * g("psi")),
            g("pi") - ((1 - ao - af) * g("pi_c") + ao * g("pi_o") + af * g("pi_f")),
            g("s") - (g("s_lag") + g("piF") - g("piH")),
            g("de") - (g("q") - g("q_lag") + g("pi") - g("pistar")),
            g("istar") - (e("pistar") + p.sigma * (e("ystar") - g("ystar"))),
            g("x") - (g("y") - d["Gamma_a"] * g("a") - d["Gamma_star"] * g("ystar")),
            g("i") - (p.rho_i * g("i_lag") + (1 - p.rho_i) * (p.phi_pi * pi_rule + p.phi_x * gap + p.phi_e * g("de")) + g("v")),
            g("cr") - (g("y") - g("X")),
            g("c") - ((1 - p.lam_h) * g("co") + p.lam_h * g("cr")),
            g("y") - (g("a") + (1 - so) * (ak * (g("k") + g("z")) + (1 - ak) * g("n")) + so * g("oin")),
            g("inv") - ((g("inv_lag") + b * e("inv") + g("qk") / phi_i) / (1 + b) + g("ei")),
            g("qk") - (-(g("i") - e("pi")) + wq * e("qk") + wr_ * e("rk")),
            g("rk") - (g("wr") + g("X") + g("n") - g("k") - g("z")),
            g("z") - z1 * g("rk"),
            g("X") - (((1 - ao - af) * p.alpha * g("s") + ao * (g("q") + g("o")) + af * g("r_f")) / (1 - ao)),
            g("pi_c") - ((1 - p.alpha) * g("piH") + p.alpha * g("piF")),
            g("r_f") - ((1 - sf) * (va - g("a")) + sf * fuel),
            g("pi_f") - (g("piH") + g("r_f") - g("r_f_lag")),
            # milestone 27: the wage curve with indexation to last quarter's CPI inflation (Smets and Wouters 2007, eq. 13)
            lhs_w * ((g("piW") - iw * g("pi_lag")) - b * (e("piW") - iw * g("pi"))) - rhs_w * (mrs - g("wr")),
            g("wr") - (g("wr_lag") + g("piW") - g("pi")),
            g("c_core") - (g("c") + p.eps_o * r_ao * (g("q") + g("o"))),
            g("pi_o") - (g("o") - g("o_lag") + g("pistar") + g("de")),
            # milestone 27: CES oil demand, oin = (y - a) - sig_o (fuel - c), c = mc + a the unit cost before productivity;
            # sig_o = 1 gives soe_htmkwo's Cobb-Douglas oin = mc + y - fuel exactly
            g("oin") - (g("y") - g("a") - p.sig_o * (fuel - g("mc") - g("a"))),
        ]
    A, B = klein.linearize(f, np.zeros(len(names)))
    return A, B, names


def solve(p: Params):
    A, B, names = system(p)
    return klein.solve(A, B, n_k=len(STATES)), names


loading = soe_htmkwo.loading


def irf(p: Params, shock: str, size: float = 1.0, T: int = 40) -> dict:
    sol, names = solve(p)
    e = loading(p) @ np.array([size if s == shock else 0.0 for s in STATES])
    k, dpath = sol.irf(np.eye(len(STATES)), e, T=T)
    out = {n: k[:, j] for j, n in enumerate(STATES)}
    out.update({n: dpath[:, j] for j, n in enumerate(JUMPS)})
    return out
