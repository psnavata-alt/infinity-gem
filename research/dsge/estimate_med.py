"""DSGE research, milestone 6b (19 Oct 2026, about 2:25 AM): Bayesian estimation of soe_med.py (habits, indexation, risk
premium, Lubik-Schorfheide rule) on the Philippine data of ph_data.py. Same machinery as estimate.py (Kalman likelihood, priors,
mode, random-walk Metropolis); five shocks (policy, productivity, world output, world inflation, risk premium) for four
observables (output growth, CPI inflation, policy rate, depreciation).
Run:  py estimate_med.py [n_draws]      (writes outputs/dsge_ph_med_estimation_<stamp>.md and the draws .npy)
"""
from __future__ import annotations

import datetime as dt
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import linalg

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import estimate as E0   # noqa: E402  (kalman_loglik, rwmh pattern)
import klein            # noqa: E402
import ph_data          # noqa: E402
import soe_med as M     # noqa: E402

EST = [  # name, family, mean, sd, lower, upper
    ("sigma", "gamma", 2.0, 0.5, 0.2, 10.0), ("theta", "beta", 0.70, 0.10, 0.05, 0.97), ("theta_F", "beta", 0.60, 0.15, 0.05, 0.97),
    ("hab", "beta", 0.70, 0.10, 0.0, 0.97), ("gH", "beta", 0.50, 0.15, 0.0, 0.97), ("gF", "beta", 0.50, 0.15, 0.0, 0.97),
    ("phi_pi", "gamma", 1.5, 0.25, 1.01, 5.0), ("phi_x", "gamma", 0.25, 0.10, 0.0, 2.0), ("phi_e", "gamma", 0.15, 0.10, 0.0, 2.0),
    ("rho_i", "beta", 0.70, 0.10, 0.0, 0.98), ("rho_a", "beta", 0.70, 0.15, 0.0, 0.99), ("rho_y", "beta", 0.70, 0.15, 0.0, 0.99),
    ("rho_ps", "beta", 0.50, 0.20, 0.0, 0.99), ("rho_v", "beta", 0.30, 0.15, 0.0, 0.95), ("rho_z", "beta", 0.70, 0.15, 0.0, 0.99),
    ("sd_v", "invgamma", 0.25, 1.0, 1e-3, 10.0), ("sd_a", "invgamma", 0.50, 1.0, 1e-3, 10.0),
    ("sd_ystar", "invgamma", 0.50, 1.0, 1e-3, 10.0), ("sd_pistar", "invgamma", 0.50, 1.0, 1e-3, 10.0),
    ("sd_zeta", "invgamma", 0.50, 1.0, 1e-3, 10.0),
]
NAMES = [e[0] for e in EST]
SHOCKS = ["v", "a", "ystar", "pistar", "zeta"]


def prior(theta):
    saved = E0.EST
    try:
        E0.EST = EST
        return E0._prior_logpdf(theta)
    finally:
        E0.EST = saved


def state_space(theta):
    kw = dict(zip(NAMES, theta))
    sds = np.array([kw.pop(f"sd_{s}") for s in SHOCKS])
    sol, _ = M.solve(M.Params(rule="output", **kw))
    nk = len(M.STATES)
    ixk, ixd = {n: j for j, n in enumerate(M.STATES)}, {n: j for j, n in enumerate(M.JUMPS)}
    Pbig = np.block([[sol.P, np.zeros((nk, nk))], [np.eye(nk), np.zeros((nk, nk))]])
    R = np.zeros((nk, len(SHOCKS)))
    for j, s in enumerate(SHOCKS):
        R[ixk[s], j] = 1.0
    Rbig = np.vstack([R, np.zeros((nk, len(SHOCKS)))])
    Q = np.diag((sds / 100.0) ** 2)
    F = sol.F
    H = np.zeros((4, 2 * nk))
    H[0, :nk], H[0, nk:] = F[ixd["y"]], -F[ixd["y"]]
    H[1, :nk], H[2, :nk], H[3, :nk] = F[ixd["pi"]], F[ixd["i"]], F[ixd["de"]]
    return Pbig, Rbig, Q, 100.0 * H


def log_post(theta, Z):
    lp = prior(theta)
    if not np.isfinite(lp):
        return -np.inf
    try:
        return lp + E0.kalman_loglik(*state_space(theta), Z)
    except (klein.BlanchardKahnError, linalg.LinAlgError, ValueError):
        return -np.inf


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30000
    t0 = time.time()
    Z = ph_data.observables()[E0.OBS].to_numpy()
    from scipy import optimize
    x0 = np.array([e[2] for e in EST])
    for _ in range(2):
        res = optimize.minimize(lambda t: -log_post(t, Z), x0, method="Nelder-Mead",
                                options=dict(maxiter=12000, xatol=1e-5, fatol=1e-6, adaptive=True))
        x0 = res.x
    m, lp = res.x, -res.fun
    rng = np.random.default_rng(7)
    scale = np.diag((0.12 * np.minimum([e[3] for e in EST], np.maximum(np.abs(m), 0.05))) ** 2)
    for it in range(4):
        Lc = np.linalg.cholesky(scale)
        x, lx, draws, acc = m.copy(), log_post(m, Z), np.empty((n, len(m))), 0
        for t in range(n):
            y = x + Lc @ rng.standard_normal(len(x))
            ly = log_post(y, Z)
            if np.log(rng.uniform()) < ly - lx:
                x, lx, acc = y, ly, acc + 1
            draws[t] = x
        acc /= n
        if 0.2 < acc < 0.4 or it == 3:
            break
        scale = (2.38 ** 2 / len(m)) * np.cov(draws[n // 4:].T) * (0.6 if acc < 0.2 else 1.4) + 1e-10 * np.eye(len(m))
    d = draws[n // 4:]
    tab = pd.DataFrame({"prior": [f"{e[1]} ({e[2]}, {e[3]})" for e in EST], "mode": m, "mean": d.mean(0),
                        "5%": np.percentile(d, 5, 0), "95%": np.percentile(d, 95, 0)}, index=NAMES)
    kw = dict(zip(NAMES, d.mean(0)))
    sds = {s: kw.pop(f"sd_{s}") for s in SHOCKS}
    p = M.Params(rule="output", **kw)
    r = M.irf(p, "v", sds["v"] / 100, T=12)
    irf = pd.DataFrame({"policy rate (pp, ann.)": 400 * r["i"], "output (%)": 100 * r["y"], "CPI inflation (pp, ann.)": 400 * r["pi"],
                        "depreciation (%)": 100 * r["de"]}, index=[f"q{k}" for k in range(12)]).T
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    outd = HERE.parents[1] / "outputs"
    np.save(outd / f"dsge_ph_med_draws_{stamp}.npy", d)
    L = [f"# DSGE research (Stage 3): the small open economy with habits, indexation and a risk premium, estimated on Philippine data "
         f"({dt.datetime.now():%d %B %Y, %H:%M})", "",
         "**NOT FOR CITATION** (research code, Infinity GEM 0.3.11 `research/dsge/`). Model `soe_med.py`; data `ph_data.py` (2002Q1-2019Q4). "
         f"Random-walk Metropolis {n:,} draws, 25% burn-in, acceptance {acc:.2f}; log posterior at the mode {lp:.1f}; {time.time() - t0:.0f} s.", "",
         "## Posterior", "", tab.to_markdown(floatfmt=".3f"), "",
         f"## One-standard-deviation policy shock ({sds['v']:.2f}% a quarter), posterior mean", "", irf.to_markdown(floatfmt=".2f")]
    (outd / f"dsge_ph_med_estimation_{stamp}.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
