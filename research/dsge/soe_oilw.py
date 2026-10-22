"""DSGE research, milestone 21 (20 Oct 2026, about 9:20 AM): oil supply and oil demand in the oil DSGE.

Why: soe_oilu (milestone 19b; oil model plus the cost-push shock) estimated an oil shock that RAISES Philippine output (+0.7%
in year 1), because in 2002-2026 oil-price rises mostly came with world booms that also lifted Philippine growth: a single oil
shock mixes oil supply with world demand (Kilian 2009). Here the world real oil price has a world-demand part,
    o = o_s + chi_o ystar,   o_s' = rho_o o_s + e_o,
so  o' = rho_o o + chi_o (ystar' - rho_o ystar) + e_o  (soe_oilu.system carries the chi_o term), and a world-output innovation
moves o by chi_o on impact (the shock loading: irf() below and estimate_rot.state_space). World output gets an observable
(ph_data.observables_oilw: G3 real GDP growth), which identifies chi_o. A supply disruption such as 2026's is then e_o alone:
it moves o_s and leaves world output unchanged. With chi_o = 0 the model is soe_oilu exactly (test T21a).
Kilian, L. (2009). "Not All Oil Price Shocks Are Alike: Disentangling Demand and Supply Shocks in the Crude Oil Market."
American Economic Review 99(3): 1053-1069.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

import soe_oilu

STATES = list(soe_oilu.STATES)
JUMPS = list(soe_oilu.JUMPS)


@dataclass
class Params(soe_oilu.Params):
    chi_o: float = 0.0        # world real oil price per unit of world output (log on log): the oil-demand loading


system = soe_oilu.system


def solve(p: Params):
    return soe_oilu.solve(p)


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
