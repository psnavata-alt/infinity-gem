"""DSGE research, milestone 8 (19 Oct 2026, about 3:05 AM): a semi-structural quarterly projection model (QPM) of the BSP's
PAMPh type, as the monetary block of the DSGE-CGE link.

Berg, Karam and Laxton (2006), IMF WP/06/80 and /81; PAMPh (BSP WPS 2020-12) follows this structure. Gaps and rates are
deviations; inflation and rates in % a year (annualized); z = real exchange rate gap (+ = peso depreciation).
  output gap      ygap = b1 ygap_lag + b2 E ygap' - b3 rmci + b4 ystar + e_y,   rmci = b5 rrgap + (1 - b5) (-z)
  Phillips curve  pi = a1 pi_lag + (1 - a1) E pi' + a2 (a3 ygap + (1 - a3) z) + e_pi
  policy rule     i = g1 i_lag + (1 - g1) (E pi' + g2 pi + g3 ygap) + e_i
  real UIP        z = E z' - (rrgap - rrstar) / 4 + e_z,   rrgap = i - E pi'
States: shocks (AR(1)) and lags; solved by QZ (klein.py). Calibrated to PAMPh's monetary-policy responses (match_pamph()).
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np

import klein

STATES = ["e_y", "e_pi", "e_i", "e_z", "ystar", "ygap_lag", "pi_lag", "i_lag"]
JUMPS = ["ygap", "pi", "i", "z", "rrgap"]


@dataclass
class Params:
    b1: float = 0.7
    b2: float = 0.1
    b3: float = 0.2
    b4: float = 0.2
    b5: float = 0.7
    a1: float = 0.6
    a2: float = 0.1
    a3: float = 0.7
    g1: float = 0.7
    g2: float = 1.5
    g3: float = 0.5
    rho_y: float = 0.5
    rho_pi: float = 0.0
    rho_i: float = 0.0
    rho_z: float = 0.5
    rho_ys: float = 0.8


def system(p: Params):
    names = STATES + JUMPS
    ix = {n: k for k, n in enumerate(names)}

    def f(xp, x):
        g = lambda n: x[ix[n]]
        e = lambda n: xp[ix[n]]
        rmci = p.b5 * g("rrgap") + (1 - p.b5) * (-g("z"))
        return [
            e("e_y") - p.rho_y * g("e_y"), e("e_pi") - p.rho_pi * g("e_pi"), e("e_i") - p.rho_i * g("e_i"),
            e("e_z") - p.rho_z * g("e_z"), e("ystar") - p.rho_ys * g("ystar"),
            e("ygap_lag") - g("ygap"), e("pi_lag") - g("pi"), e("i_lag") - g("i"),
            g("ygap") - (p.b1 * g("ygap_lag") + p.b2 * e("ygap") - p.b3 * rmci + p.b4 * g("ystar") + g("e_y")),
            g("pi") - (p.a1 * g("pi_lag") + (1 - p.a1) * e("pi") + p.a2 * (p.a3 * g("ygap") + (1 - p.a3) * g("z")) + g("e_pi")),
            g("i") - (p.g1 * g("i_lag") + (1 - p.g1) * (e("pi") + p.g2 * g("pi") + p.g3 * g("ygap")) + g("e_i")),
            g("z") - (e("z") - g("rrgap") / 4 + g("e_z")),
            g("rrgap") - (g("i") - e("pi")),
        ]
    A, B = klein.linearize(f, np.zeros(len(names)))
    return A, B, names


def irf(p: Params, shock: str, size: float = 1.0, T: int = 24) -> dict:
    A, B, names = system(p)
    sol = klein.solve(A, B, n_k=len(STATES))
    k, d = sol.irf(np.eye(len(STATES)), np.array([size if s == shock else 0.0 for s in STATES]), T=T)
    out = {n: k[:, j] for j, n in enumerate(STATES)}
    out.update({n: d[:, j] for j, n in enumerate(JUMPS)})
    return out


def pamph_like(p: Params, quarters):
    """Monetary-policy responses in PAMPh's units: rate shock scaled to +0.80 pp in quarter 1; y/y CPI inflation (average of four
    quarterly annualized rates); y/y GDP growth = change in the output gap over four quarters (potential unaffected); nominal
    exchange rate (100 log) = real gap + cumulative relative inflation (foreign inflation zero)."""
    r = irf(p, "e_i", 1.0, T=max(quarters) + 2)
    s = 0.80 / r["i"][0]
    pad = lambda x: s * np.concatenate([[0.0], x])
    y, pi, i, z = pad(r["ygap"]), pad(r["pi"]), pad(r["i"]), pad(r["z"])
    out = {"rate": {}, "growth": {}, "infl": {}, "fx": {}}
    for q in quarters:
        out["rate"][q] = i[q]
        out["growth"][q] = y[q] - (y[q - 4] if q >= 4 else 0.0)
        out["infl"][q] = pi[max(q - 3, 1):q + 1].sum() / 4
        out["fx"][q] = z[q] + pi[1:q + 1].sum() / 4
    return out


BOUNDS = dict(b1=(0.3, 0.9), b2=(0.0, 0.3), b3=(0.05, 0.6), b5=(0.4, 0.9), a1=(0.3, 0.9), a2=(0.02, 0.4), a3=(0.4, 0.95),
              g1=(0.3, 0.9), g2=(1.05, 3.0), g3=(0.1, 1.0), rho_i=(0.0, 0.6))


def match_pamph():
    from scipy import optimize
    import pamph_targets as T
    tgt = {"rate": T.POLICY_RATE_PA, "growth": T.GDP_GROWTH_YOY, "infl": T.CPI_INFLATION_YOY, "fx": T.NOMINAL_EXCHANGE_RATE_100LOG}
    tol = {"rate": 0.05, "growth": 0.02, "infl": 0.02, "fx": 0.05}
    keys = list(BOUNDS)

    def dist(x):
        p = Params(**dict(zip(keys, x)))
        try:
            m = pamph_like(p, T.QUARTERS)
        except (klein.BlanchardKahnError, ValueError, np.linalg.LinAlgError):
            return 1e9
        return sum(((m[k][q] - tgt[k][q]) / tol[k]) ** 2 for k in tgt for q in T.QUARTERS)
    x0 = np.array([getattr(Params(), k) for k in keys])
    res = optimize.minimize(dist, x0, method="L-BFGS-B", bounds=[BOUNDS[k] for k in keys])
    p = Params(**dict(zip(keys, res.x)))
    return p, res.fun, dist(x0), pamph_like(p, T.QUARTERS), tgt
