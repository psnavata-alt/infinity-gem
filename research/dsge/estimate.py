"""DSGE research, milestone 4 (19 Oct 2026, about 2 AM): Bayesian estimation of the small open economy (soe_lcp.py).

- likelihood: the Kalman filter on the model's state space (k_{t+1} = P k_t + R eps; observables z_t = H [k_t; k_{t-1}] + me),
  started at the unconditional distribution (discrete Lyapunov equation);
- priors: the usual families (beta for probabilities, gamma for positive parameters, inverse gamma for shock sizes), centred on
  standard values for an inflation-targeting emerging economy;
- posterior mode by numerical optimisation, then random-walk Metropolis-Hastings with the inverse Hessian (or a diagonal scale)
  as the proposal covariance (An and Schorfheide 2007; Herbst and Schorfheide 2015).
Observables (quarterly, demeaned, %): output growth (100 dy), CPI inflation (100 pi), the policy rate (100 i), depreciation
(100 de). Shocks: v, a, ystar, pistar, so the model has as many shocks as observables (no stochastic singularity).
"""
from __future__ import annotations

import numpy as np
from scipy import linalg, optimize, stats

import klein
import soe_lcp as L

EST = [  # name, prior family, prior mean, prior sd, lower, upper
    ("sigma", "gamma", 2.0, 0.5, 0.2, 10.0),
    ("theta", "beta", 0.70, 0.10, 0.05, 0.97),
    ("theta_F", "beta", 0.60, 0.15, 0.05, 0.97),
    ("phi_pi", "gamma", 1.5, 0.25, 1.01, 5.0),
    ("phi_x", "gamma", 0.25, 0.10, 0.0, 2.0),
    ("rho_i", "beta", 0.70, 0.10, 0.0, 0.98),
    ("rho_a", "beta", 0.70, 0.15, 0.0, 0.99),
    ("rho_y", "beta", 0.70, 0.15, 0.0, 0.99),
    ("rho_ps", "beta", 0.50, 0.20, 0.0, 0.99),
    ("rho_v", "beta", 0.30, 0.15, 0.0, 0.95),
    ("sd_v", "invgamma", 0.25, 1.0, 1e-3, 10.0),
    ("sd_a", "invgamma", 0.50, 1.0, 1e-3, 10.0),
    ("sd_ystar", "invgamma", 0.50, 1.0, 1e-3, 10.0),
    ("sd_pistar", "invgamma", 0.50, 1.0, 1e-3, 10.0),
]
NAMES = [e[0] for e in EST]
OBS = ["dy", "pi", "i", "de"]


def _prior_logpdf(theta):
    lp = 0.0
    for v, (_, fam, m, s, lo, hi) in zip(theta, EST):
        if not lo < v < hi:
            return -np.inf
        if fam == "gamma":
            k = (m / s) ** 2; lp += stats.gamma.logpdf(v, k, scale=m / k)
        elif fam == "beta":
            a = m * (m * (1 - m) / s ** 2 - 1); b = (1 - m) * (m * (1 - m) / s ** 2 - 1); lp += stats.beta.logpdf(v, a, b)
        elif fam == "invgamma":                      # Dynare-style inv_gamma with mean m and 'sd' s (here a loose prior)
            a_ = 2 + (m / s) ** 2; lp += stats.invgamma.logpdf(v, a_, scale=m * (a_ - 1))
        elif fam == "normal":                        # 21 Oct 2026 (milestone 23, phi_i): mean m, s.d. s, truncated to (lo, hi)
            lp += stats.norm.logpdf(v, m, s)
    return lp


def state_space(theta, base=None):
    """Return (Pbig, Rbig, Q, H) for the augmented state [k_t; k_{t-1}]; observables in % (x100)."""
    kw = dict(zip(NAMES, theta))
    sds = np.array([kw.pop("sd_v"), kw.pop("sd_a"), kw.pop("sd_ystar"), kw.pop("sd_pistar")])
    p = L.Params(**{**(base or {}), **kw})
    sol, names = L.solve(p)
    nk = len(L.STATES)
    ixk = {n: j for j, n in enumerate(L.STATES)}
    ixd = {n: j for j, n in enumerate(L.JUMPS)}
    F = sol.F
    Pbig = np.block([[sol.P, np.zeros((nk, nk))], [np.eye(nk), np.zeros((nk, nk))]])
    R = np.zeros((nk, 4))
    for j, s in enumerate(["v", "a", "ystar", "pistar"]):
        R[ixk[s], j] = 1.0
    Rbig = np.vstack([R, np.zeros((nk, 4))])
    Q = np.diag((sds / 100.0) ** 2)                  # shocks in % -> model units
    row = lambda n: F[ixd[n]]
    H = np.zeros((4, 2 * nk))
    H[0, :nk] = row("y"); H[0, nk:] = -row("y")      # output growth = y_t - y_{t-1}
    H[1, :nk] = row("pi")
    H[2, :nk] = row("i")
    H[3, :nk] = row("de")
    return Pbig, Rbig, Q, 100.0 * H


def kalman_loglik(Pm, Rm, Q, H, Z, me=1e-4):
    """Milestone 18 (19 Oct 2026, about 11:15 PM): missing observations (NaN) are skipped, the filter predicting through them and updating on
    the observed entries only (Durbin and Koopman 2012, section 4.10); e.g. the COVID quarters 2020-2021. Without NaN the
    arithmetic is the same as before."""
    n = Pm.shape[0]
    RQR = Rm @ Q @ Rm.T
    Sig = linalg.solve_discrete_lyapunov(Pm, RQR)
    x = np.zeros(n)
    Me = np.eye(H.shape[0]) * me
    ll = 0.0
    for z in Z:
        ok = np.isfinite(z)
        if ok.all():
            Hk, zk, Mk = H, z, Me
        elif not ok.any():                           # nothing observed: predict only
            x = Pm @ x
            Sig = Pm @ Sig @ Pm.T + RQR
            continue
        else:
            Hk, zk, Mk = H[ok], z[ok], Me[np.ix_(ok, ok)]
        Fm = Hk @ Sig @ Hk.T + Mk
        e = zk - Hk @ x
        cf = linalg.cho_factor(Fm)
        ll -= 0.5 * (len(zk) * np.log(2 * np.pi) + 2 * np.log(np.diag(cf[0])).sum() + e @ linalg.cho_solve(cf, e))
        K = Pm @ Sig @ Hk.T @ linalg.cho_solve(cf, np.eye(len(zk)))
        x = Pm @ x + K @ e
        Sig = Pm @ Sig @ Pm.T + RQR - K @ Fm @ K.T
    return ll


def log_post(theta, Z, base=None):
    lp = _prior_logpdf(theta)
    if not np.isfinite(lp):
        return -np.inf
    try:
        Pm, Rm, Q, H = state_space(theta, base)
        return lp + kalman_loglik(Pm, Rm, Q, H, Z)
    except (klein.BlanchardKahnError, linalg.LinAlgError, ValueError):
        return -np.inf


def mode(Z, theta0=None, base=None, maxiter=4000):
    x0 = np.array([e[2] for e in EST]) if theta0 is None else np.asarray(theta0, float)
    res = optimize.minimize(lambda t: -log_post(t, Z, base), x0, method="Nelder-Mead",
                            options=dict(maxiter=maxiter, xatol=1e-5, fatol=1e-6, adaptive=True))
    return res.x, -res.fun, res


def rwmh(Z, start, scale, n=20000, base=None, seed=7, burn=0.25):
    rng = np.random.default_rng(seed)
    x, lp = np.asarray(start, float), log_post(start, Z, base)
    draws, acc = np.empty((n, len(x))), 0
    Lc = np.linalg.cholesky(scale)
    for t in range(n):
        y = x + Lc @ rng.standard_normal(len(x))
        ly = log_post(y, Z, base)
        if np.log(rng.uniform()) < ly - lp:
            x, lp, acc = y, ly, acc + 1
        draws[t] = x
    return draws[int(burn * n):], acc / n


def simulate(theta, T, base=None, seed=1):
    Pm, Rm, Q, H = state_space(theta, base)
    rng = np.random.default_rng(seed)
    x = np.zeros(Pm.shape[0]); out = []
    Lq = np.linalg.cholesky(Q)
    for _ in range(T + 50):
        x = Pm @ x + Rm @ (Lq @ rng.standard_normal(4))
        out.append(H @ x)
    return np.array(out[50:])
