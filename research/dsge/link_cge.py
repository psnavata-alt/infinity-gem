"""DSGE research, milestone 5 (19 Oct 2026, about 2:15 AM): the DSGE-CGE link (the money and financial block).

Top-down macro-micro link: the estimated small open economy (soe_lcp.py at the posterior mean of report_ph_estimation.py) gives
the aggregate paths of a monetary or external scenario: the policy rate, output, CPI inflation and the real exchange rate. Annual
averages of those paths become shocks to Infinity GEM's recursive CGE in its short-run years:
- the peso: 'exr_scale' = exp(annual real-exchange-rate deviation) (dynamic.py's peso lever, check EX1);
- the interest-rate (demand) channel, which the CGE does not have: a scale on real investment demand, solved so that the CGE's
  GDP response equals the DSGE's annual output response (calibrate_investment()).
The CGE then gives what the DSGE cannot: industries, households and the poverty count.
Usage:
    paths = scenario_paths("policy", size_bp=100, quarters=4)    # a 100 bp (annualized) tightening held for 4 quarters
    shocks = annual_shocks(paths, years=(2026, 2027))           # {year: {"exr_scale": ..., "dsge_output_pct": ...}}
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

import estimate as E
import soe_lcp as L

HERE = Path(__file__).resolve().parent


def posterior_params(draws_file: Path | None = None):
    """Params at the posterior mean of the latest saved Philippine draws (outputs/dsge_ph_draws_*.npy) and the shock sizes."""
    # public version: the draws saved with the repository (research/dsge/draws/) when outputs/ has none of its own
    f = draws_file or sorted(list((HERE.parents[1] / "outputs").glob("dsge_ph_draws_*.npy"))
                             or list((HERE / "draws").glob("dsge_ph_draws_*.npy")))[-1]
    m = np.load(f).mean(0)
    kw = dict(zip(E.NAMES, m))
    sd = {k: kw.pop(k) for k in ("sd_v", "sd_a", "sd_ystar", "sd_pistar")}
    return L.Params(**kw), sd, f.name


def scenario_paths(kind="policy", size_bp=100.0, quarters=4, T=12, params=None) -> dict:
    """Quarterly paths (model units: log deviations; rates per quarter) of a scenario starting in quarter 0.
    kind='policy': the policy rate held size_bp (annualized) above its rule for `quarters` quarters, by a sequence of policy
    shocks solved so that the realised rate path is exactly that (the rule's own response included);
    kind='peso': a depreciation of size_bp/100 % on impact through a world-inflation-style nominal shock is not real (a float
    insulates, test T14a), so the peso scenario is a policy easing; left for the next milestone (risk-premium shock)."""
    p = params or posterior_params()[0]
    sol, names = L.solve(p)
    nk = len(L.STATES)
    iv = L.STATES.index("v")
    ix = {n: j for j, n in enumerate(L.JUMPS)}
    target = np.zeros(T)
    target[:quarters] = size_bp / 400.0 / 100.0                 # annualized bp -> per-quarter rate, log units
    eps = np.zeros(T)
    k = np.zeros((T, nk))
    d = np.zeros((T, len(L.JUMPS)))
    state = np.zeros(nk)
    for t in range(T):
        base = sol.P @ state if t else np.zeros(nk)
        # the rate this quarter is linear in the shock: i = F_i (base + e_v * eps); solve for eps hitting the target
        e = np.zeros(nk); e[iv] = 1.0
        i0 = sol.F[ix["i"]] @ base
        di = sol.F[ix["i"]] @ e
        eps[t] = (target[t] - i0) / di if t < quarters else 0.0
        state = base + e * eps[t]
        k[t], d[t] = state, sol.F @ state
    out = {n: d[:, j] for n, j in ix.items()}
    out["v"] = k[:, iv]
    out["eps"] = eps
    return out


def annual_shocks(paths: dict, years=(2026, 2027)) -> dict:
    """Annual averages of the quarterly paths (quarter 0 = first quarter of the first year) as CGE inputs."""
    res = {}
    for n, y in enumerate(years):
        sl = slice(4 * n, 4 * n + 4)
        q = float(np.mean(paths["q"][sl]))
        res[y] = {"exr_scale": float(np.exp(q)), "dsge_output_pct": 100 * float(np.mean(paths["y"][sl])),
                  "dsge_cpi_inflation_pp": 400 * float(np.mean(paths["pi"][sl])), "policy_rate_pp": 400 * float(np.mean(paths["i"][sl]))}
    return res
