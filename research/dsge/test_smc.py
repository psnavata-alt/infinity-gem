"""Tests of the sequential Monte Carlo sampler (research/dsge/smc.py; 21 Oct 2026, about 1:05 AM).

T1  An exact case: a Gaussian prior N(0, 1) on three parameters and a Gaussian likelihood y = theta + e, e ~ N(0, 0.5^2), y fixed.
    The posterior is N(0.8 y, 0.2) parameter by parameter and the log marginal data density is sum_j log N(y_j; 0, 1.25). The
    SMC posterior mean, spread and evidence must match within Monte Carlo error.
T2  The sampler's mechanics: phi rises to exactly 1, every stage's ESS is near the target share, the weights are equal at the end,
    the particles all lie inside the prior's support.
T3  A short run on the DSGE target (soe_htmu, system prior on transmission strength, 2002-2026 with STL GDP): a few particles,
    two stages, one worker: it runs, the retained particles have a solution and finite log likelihoods, and the marginal data
    density is finite.
T4  The bridging start (start=chains, 21 Oct 2026 morning; generalised tempering from a cloud): the Gaussian case of T1 started
    from an off-centre, too-wide Gaussian cloud q with run_smc(X0=..., logq_fn=...); the posterior mean, spread and the marginal
    data density must again match the exact values (the cloud integrates to one, so the evidence estimate is the true one).
Run: py test_smc.py   (about 10-20 s; T3 imports estimate_rot with the model arguments set below)
"""
from __future__ import annotations

import sys

from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))             # isolated mode (-I) does not add it
sys.argv += ["model=htmu", "prior=ratio", "sample=long", "gdp=stl"]       # for T3 (read by estimate_rot at import)
import smc  # noqa: E402


class GaussianTarget:
    """Prior N(0, I_k); likelihood y = theta + e, e ~ N(0, s^2 I)."""

    def __init__(self, y, s=0.5):
        self.y, self.s, self.k = np.asarray(y, float), float(s), len(y)

    def draw_prior(self, n, rng):
        return rng.standard_normal((n, self.k))

    def evaluate(self, X):
        X = np.asarray(X, float)
        lp = -0.5 * (X ** 2).sum(1) - 0.5 * self.k * np.log(2 * np.pi)
        ll = -0.5 * ((self.y - X) ** 2).sum(1) / self.s ** 2 - 0.5 * self.k * np.log(2 * np.pi * self.s ** 2)
        return lp, ll


def t1_t2():
    y = np.array([0.8, -0.4, 1.2])
    T = GaussianTarget(y, s=0.5)
    n = 3000
    X, logW, lp, ll, logZ, stages = smc.run_smc(T, n=n, alpha=0.5, m=2, blocks=1, seed=3, log=lambda s: None)
    prec = 1.0 + 1.0 / T.s ** 2
    mean_true, var_true = y / T.s ** 2 / prec, 1.0 / prec
    logZ_true = float(np.sum(-0.5 * np.log(2 * np.pi * (1 + T.s ** 2)) - 0.5 * y ** 2 / (1 + T.s ** 2)))
    err_mean = np.abs(X.mean(0) - mean_true).max()
    err_sd = np.abs(X.std(0) / np.sqrt(var_true) - 1).max()
    err_z = abs(logZ - logZ_true)
    ok1 = err_mean < 4 * np.sqrt(var_true / n) * 3 and err_sd < 0.08 and err_z < 0.15
    print(f"T1 exact Gaussian: mean error {err_mean:.4f} (tolerance {4 * np.sqrt(var_true / n) * 3:.4f}), s.d. ratio error "
          f"{err_sd:.3f}, log evidence {logZ:.3f} against {logZ_true:.3f} (error {err_z:.3f}); {len(stages)} stages")
    phis = [s["phi"] for s in stages]
    ess_ok = all(0.4 * n <= s["ESS after correction"] <= 1.0 * n for s in stages[:-1])
    ok2 = (phis[-1] == 1.0 and all(b > a for a, b in zip(phis, phis[1:])) and ess_ok
           and np.allclose(logW, -np.log(n)) and np.isfinite(X).all())
    print(f"T2 mechanics: phi path {', '.join(f'{p:.4f}' for p in phis)}; ESS in range {ess_ok}; equal final weights "
          f"{np.allclose(logW, -np.log(n))}")
    return ok1, ok2


def t3():
    with smc.DSGETarget(workers=1, w=1.0) as T:
        X, logW, lp, ll, logZ, stages = smc.run_smc(T, n=12, alpha=0.5, m=1, blocks=1, seed=5, max_stages=2, log=lambda s: None)
        inside = all(all(lo < x < hi for x, (_, _, _, _, lo, hi) in zip(row, T.est)) for row in X)
    ok = (len(stages) == 2 and 0 < stages[-1]["phi"] <= 1.0 and np.isfinite(ll).all() and np.isfinite(lp).all()
          and np.isfinite(logZ) and inside and X.shape == (12, T.k))
    print(f"T3 DSGE target (soe_htmu, {T.k} parameters): stages {len(stages)}, phi {stages[-1]['phi']:.6f}, all retained particles "
          f"solved {np.isfinite(ll).all()}, inside the prior {inside}, log evidence so far {logZ:.1f}")
    return ok


def t4():
    from scipy.stats import norm
    y = np.array([0.8, -0.4, 1.2])
    T = GaussianTarget(y, s=0.5)
    n = 3000
    prec = 1.0 + 1.0 / T.s ** 2
    mean_true, var_true = y / T.s ** 2 / prec, 1.0 / prec
    logZ_true = float(np.sum(-0.5 * np.log(2 * np.pi * (1 + T.s ** 2)) - 0.5 * y ** 2 / (1 + T.s ** 2)))
    rng = np.random.default_rng(7)
    mu0, sd0 = mean_true + 0.3, 2.0 * np.sqrt(var_true) * np.ones(T.k)     # the cloud: off-centre, twice the posterior's spread
    X0 = mu0 + sd0 * rng.standard_normal((n, T.k))
    logq_fn = lambda Z_: norm.logpdf(np.asarray(Z_, float), mu0, sd0).sum(1)
    X, logW, lp, ll, logZ, stages = smc.run_smc(T, n=n, alpha=0.5, m=2, blocks=1, seed=3, log=lambda s: None, X0=X0, logq_fn=logq_fn)
    err_mean = np.abs(X.mean(0) - mean_true).max()
    err_sd = np.abs(X.std(0) / np.sqrt(var_true) - 1).max()
    err_z = abs(logZ - logZ_true)
    ok = err_mean < 4 * np.sqrt(var_true / n) * 3 and err_sd < 0.08 and err_z < 0.15 and stages[-1]["phi"] == 1.0
    print(f"T4 bridging start (generalised tempering from a cloud): mean error {err_mean:.4f}, s.d. ratio error {err_sd:.3f}, log evidence "
          f"{logZ:.3f} against {logZ_true:.3f} (error {err_z:.3f}); {len(stages)} stages")
    return ok


if __name__ == "__main__":
    ok1, ok2 = t1_t2()
    ok3 = t3()
    ok4 = t4()
    res = [ok1, ok2, ok3, ok4]
    print(f"test_smc: {sum(res)}/{len(res)} passed")
    sys.exit(0 if all(res) else 1)
