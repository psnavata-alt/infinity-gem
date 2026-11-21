"""DSGE research, milestone 28 (12 Nov 2026, morning; under of about 5:50 AM, "do as much as you can"):
soe_htmkwoi plus DOMINANT-CURRENCY (dollar) PRICING OF EXPORTS, opt-in. A new file, so that soe_htmkwoi (milestone 27) stays
reproducible. Research code; NOT FOR CITATION; no Infinity GEM result uses it.

Why (milestone27_scratch/output_decomposition.py): on milestone 26's posterior the 36% oil supply shock raises year-1 output
(+0.39%) entirely through EXPORTS (+0.99 point): the peso depreciates, home prices are sticky in pesos, and with producer-currency
pricing (soe_nk, Gali and Monacelli 2005) foreign buyers see a lower dollar price in the same quarter, so exports jump. Most
trade, and most emerging-market exports, is invoiced in US dollars, and dollar prices are sticky (Gopinath, Boz, Casas, Diez,
Gourinchas and Plagborg-Moller 2020; Gopinath and Rigobon 2008: a median price duration of about a year at the US border). With
dollar pricing a depreciation does not cut the dollar price of exports in the short run; it raises exporters' peso margins
instead, and export volumes respond only as dollar prices are re-set.

The export block (dcp=True), in log deviations; tX = p_X* - p* is the dollar price of home exports relative to world prices, piX
its dollar inflation, theta_X the Calvo parameter of dollar export prices:
    piX = beta E piX' + lambda_X mcX,   lambda_X = (1 - theta_X)(1 - beta theta_X) / theta_X
    mcX = mc - (s + psi) - tX           (real marginal cost over the peso value of the dollar price; s + psi = e + p* - p_H)
    tX  = tX(-1) + piX - pistar
    exports = alpha [gamma (-tX) + ystar]   in place of producer-currency pricing's alpha [gamma (s + psi) + ystar]
With dcp=False tX = -(s + psi) (the dollar price is the peso price over the exchange rate) and the model is soe_htmkwoi exactly
(test_milestone28.py, T28a). Simplification (first order, documented): exporters' extra peso margin under dollar pricing goes to
the optimizing households' profits; hand-to-mouth income cr = y - X is left as in soe_htmkwoi.
Gopinath, G., E. Boz, C. Casas, F. J. Diez, P.-O. Gourinchas and M. Plagborg-Moller (2020). "Dominant Currency Paradigm."
American Economic Review 110(3): 677-719. Gopinath, G., and R. Rigobon (2008). "Sticky Borders." Quarterly Journal of Economics
123(2): 531-575. Gali, J., and T. Monacelli (2005). Review of Economic Studies 72(3): 707-734.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

import klein
import soe_htmkwo
import soe_htmkwoi

STATES = list(soe_htmkwoi.STATES) + ["tX_lag"]
JUMPS = list(soe_htmkwoi.JUMPS) + ["tX", "piX"]


@dataclass
class Params(soe_htmkwoi.Params):
    dcp: bool = False         # dollar (dominant-currency) pricing of exports (False = producer-currency pricing = soe_htmkwoi)
    theta_X: float = 0.75     # Calvo parameter of dollar export prices (dcp=True only)


def system(p: Params):
    if not 0.0 <= p.iota_w <= 1.0:
        raise ValueError("iota_w must be in [0, 1]")
    if not 0.0 <= p.sig_o <= 1.0:
        raise ValueError("sig_o must be in [0, 1]")
    if p.dcp and not 0.0 < p.theta_X < 1.0:
        raise ValueError("theta_X must be in (0, 1) with dcp=True")
    if p.gH or p.gF:
        raise ValueError("soe_htmkwod builds on soe_htm: set gH = gF = 0")
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
    lamX = (1 - p.theta_X) * (1 - b * p.theta_X) / p.theta_X if p.dcp else 0.0

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
            e("tX_lag") - g("tX"),                                                                      # milestone 28
            mu(g("co"), g("co_lag")) - (mu(Eco, g("co")) - (g("i") - Epi)),
            mu(g("co"), g("co_lag")) - (mu(g("ystar"), g("ystar_lag")) + g("q") - g("zeta")),
            g("q") - ((1 - ao) * (g("psi") + (1 - p.alpha) * g("s")) - ao * g("o") + af * (p.alpha * g("s") - g("r_f"))),
            # milestone 28: exports priced in dollars (dcp) or in pesos (tX = -(s + psi))
            g("y") - ((1 - p.alpha) * (z + p.alpha * p.eta * g("s")) + p.alpha * (p.gamma * (-g("tX")) + g("ystar"))),
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
            # milestone 28: the dollar export price (Calvo in dollars) or the peso price over the exchange rate
            (g("piX") - (b * e("piX") + lamX * (g("mc") - (g("s") + g("psi")) - g("tX")))) if p.dcp
            else (g("tX") + g("s") + g("psi")),
            g("tX") - (g("tX_lag") + g("piX") - g("pistar")),
        ]
    A, B = klein.linearize(f, np.zeros(len(names)))
    return A, B, names


def solve(p: Params):
    A, B, names = system(p)
    return klein.solve(A, B, n_k=len(STATES)), names


def loading(p: Params) -> np.ndarray:
    """Shock loadings (states x shocks): identity, plus chi_o of the world-output shock on o (soe_htmkwo.loading)."""
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
