"""DSGE research (Stage 3) (21 Oct 2026, about 1:00 AM): a sequential Monte Carlo (SMC) sampler
for the DSGE posteriors, as an independent check on the random-walk Metropolis chains of estimate_rot.py, and an estimate of
the marginal data density as a by-product.

Method (Herbst and Schorfheide 2014; 2016, chapter 5). N particles are drawn from the prior. The likelihood is raised to a
tempering exponent phi that rises from 0 to 1 in stages; at each stage:
  1. correction: the particles are reweighted by the incremental likelihood ratio exp((phi_n - phi_{n-1}) x log likelihood);
  2. selection: systematic resampling (the weights become equal);
  3. mutation: each particle takes M steps of a random-walk Metropolis move on the tempered posterior, in random blocks of
     parameters, with a proposal covariance equal to the particle cloud's covariance (block by block) scaled by c; c is adapted
     after every stage towards an acceptance rate of 25% (Herbst and Schorfheide 2014, equation for c_n).
The tempering schedule is ADAPTIVE: the next phi is found by bisection so that the effective sample size (ESS) of the corrected
weights is a share alpha of the particles (Del Moral, Doucet and Jasra 2012; Cai, Del Negro, Herbst, Matlin, Sarfati and
Schorfheide 2021), and the last stage sets phi = 1. The log marginal data density is the sum over stages of the log mean
incremental weight (the standard SMC estimate).
The target is estimate_rot.py's posterior for the model named on the command line (model=, prior=, sample=, gdp=, theta_fix=,
world= as there): the parameter prior, plus, tempered together with the likelihood, the system prior on transmission strength
(weight w). Stage 0 therefore draws from the parameter prior alone, which is sampleable; a particle the model cannot solve
(indeterminate or explosive) has zero likelihood and disappears at the first correction.
Why: a second sampler that starts from the prior, not from a mode or an earlier chain, cannot inherit a chain's region; agreement
with the Metropolis chains (posterior means within a fraction of a standard deviation, similar bands) is evidence that both
found the posterior, and a disagreement shows which parameters the chains had not explored. SMC also handles multimodal
posteriors, which milestone 18b found in soe_htm (two regions of productivity-shock size), by carrying particles in each mode.
Herbst, E., and F. Schorfheide (2014). "Sequential Monte Carlo Sampling for DSGE Models." Journal of Applied Econometrics 29(7):
1073-1098. Herbst, E., and F. Schorfheide (2016). Bayesian Estimation of DSGE Models. Princeton University Press. Del Moral, P.,
A. Doucet, and A. Jasra (2012). "An Adaptive Sequential Monte Carlo Method for Approximate Bayesian Computation." Statistics and
Computing 22: 1009-1020. Cai, M., M. Del Negro, E. Herbst, E. Matlin, R. Sarfati, and F. Schorfheide (2021). "Online Estimation of
DSGE Models." Econometrics Journal 24(1): C33-C58.
Run (repository root or research/dsge; the model arguments as for estimate_rot.py):
  py research/dsge/smc.py model=oilw prior=ratio sample=long gdp=stl theta_fix=0.85 [n=1000] [alpha=0.5] [m=1] [blocks=2]
                          [workers=8] [seed=1] [w=1] [max_stages=300] [compare=<glob of draws files>] [start=prior|chains]
start=chains (21 Oct 2026, morning): a BRIDGING run. The particles start from a Gaussian cloud around the pooled
Metropolis chains of the same specification (mean, 2 x the chains' s.d. per parameter, clipped to the prior's range); the target then
moves from the cloud q to the posterior by GENERALISED tempering, q^(1 - phi) x (prior x likelihood)^phi (Cai et al. 2021; the
tempered quantity is log prior + log likelihood - log q, and the mutation step targets the same mixture). A first version that
reweighted the cloud to the prior in one step at stage 0 collapsed the ESS to 2 (9:00 AM run, kept as `_0853_*_chains.md`). It checks
the chains' mode from inside its basin when a system prior's ridge stops a prior-started SMC from reaching it; it is not an
independent check, and its marginal data density is local to the cloud's region. Outputs carry "_chains".
Writes outputs/dsge_smc_<stamp>_<model><tags>_n<N>.md (settings, the stage table, the posterior against the pooled Metropolis chains
of the same specification), _particles.npy (N x k, equal weights after the final resampling) and _logw.npy.
Tests: test_smc.py (an exact Gaussian case: posterior mean, spread and the marginal data density; a short run on the DSGE target).
"""
from __future__ import annotations

import datetime as dt
import re
import sys
import time
from pathlib import Path

import numpy as np
from scipy import stats
from scipy.special import logsumexp

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
OUT = HERE.parents[1] / "outputs"


def _arg(name, default, cast=str):
    return next((cast(a.split("=", 1)[1]) for a in sys.argv[1:] if a.startswith(f"{name}=")), default)


# ----------------------------------------------------------------------------------------------------- the DSGE target
_ER, _Z, _W = None, None, 1.0


def _init(w: float):
    """Worker set-up: estimate_rot (which reads the model arguments from sys.argv, which multiprocessing passes on), the data."""
    global _ER, _Z, _W
    import estimate_rot as ER
    _ER, _W = ER, float(w)
    _Z = ER.observables()


def _eval(theta):
    """(log parameter prior, log likelihood + the system-prior penalty) of one parameter vector; (-inf, -inf) outside the prior or
    where the model has no unique stable solution."""
    p = _ER.pieces(np.asarray(theta, float), _Z)
    if p is None:
        return (-np.inf, -np.inf)
    pen = -0.5 * _W * (p[3] if _ER.PRIOR in getattr(_ER, "RATIO_PRIORS", ("ratio", "ratio_cpi")) else p[2])
    return (float(p[0]), float(p[1] + pen))


def prior_distributions(est):
    """scipy distributions of estimate.py's prior families, in its parameterisation (mean, s.d.; Dynare-style inverse gamma)."""
    out = []
    for _, fam, m, s, lo, hi in est:
        if fam == "gamma":
            k = (m / s) ** 2
            d = stats.gamma(k, scale=m / k)
        elif fam == "beta":
            a = m * (m * (1 - m) / s ** 2 - 1)
            b = (1 - m) * (m * (1 - m) / s ** 2 - 1)
            d = stats.beta(a, b)
        elif fam == "invgamma":
            a_ = 2 + (m / s) ** 2
            d = stats.invgamma(a_, scale=m * (a_ - 1))
        elif fam == "normal":
            d = stats.norm(m, s)
        else:
            raise ValueError(f"prior family {fam!r} unknown")
        out.append((d, lo, hi))
    return out


class DSGETarget:
    """estimate_rot.py's posterior as an SMC target: draw_prior (the truncated parameter prior, by inverse CDF) and evaluate
    (log prior, log likelihood + system-prior penalty), in parallel over `workers` processes."""

    def __init__(self, workers: int = 1, w: float = 1.0):
        import estimate_rot as ER
        self.ER, self.w, self.workers = ER, float(w), int(workers)
        self.names, self.est = list(ER.NAMES), list(ER.EST)
        self.k = len(self.names)
        self.dists = prior_distributions(self.est)
        self.pool = None

    def __enter__(self):
        if self.workers > 1:
            import multiprocessing as mp
            self.pool = mp.Pool(self.workers, initializer=_init, initargs=(self.w,))
        else:
            _init(self.w)
        return self

    def __exit__(self, *exc):
        if self.pool is not None:
            self.pool.close()
            self.pool.join()

    def draw_prior(self, n: int, rng) -> np.ndarray:
        X = np.empty((n, self.k))
        for j, (d, lo, hi) in enumerate(self.dists):
            u = rng.uniform(d.cdf(lo), d.cdf(hi), n)
            X[:, j] = np.clip(d.ppf(u), np.nextafter(lo, hi), np.nextafter(hi, lo))
        return X

    def evaluate(self, X):
        X = [np.asarray(x, float) for x in X]
        if self.pool is None:
            E = [_eval(x) for x in X]
        else:
            E = self.pool.map(_eval, X, chunksize=max(1, len(X) // (self.workers * 4)))
        E = np.asarray(E, float)
        return E[:, 0], E[:, 1]


# ----------------------------------------------------------------------------------------------------- the sampler
def _ess(logw: np.ndarray) -> float:
    lw = logw - logsumexp(logw)
    return float(np.exp(-logsumexp(2 * lw)))


def systematic_resample(logw: np.ndarray, rng) -> np.ndarray:
    W = np.exp(logw - logsumexp(logw))
    n = len(W)
    u = (rng.uniform() + np.arange(n)) / n
    cs = np.cumsum(W)
    cs[-1] = 1.0
    return np.minimum(np.searchsorted(cs, u), n - 1)


def run_smc(target, n: int = 1000, alpha: float = 0.5, m: int = 1, blocks: int = 2, seed: int = 1, max_stages: int = 300,
            c0: float = 0.5, log=print, X0=None, logq_fn=None):
    """Returns (particles, log weights, log prior, log likelihood, log marginal data density, the stage table). The log weights are
    equal after the final resampling; `log likelihood` includes the tempered system-prior penalty."""
    rng = np.random.default_rng(seed)
    t0 = time.time()
    X = np.asarray(target.draw_prior(n, rng), float) if X0 is None else np.asarray(X0, float)   # start=chains: a given cloud
    k = X.shape[1]
    lp, ll = target.evaluate(X)
    lp, ll = np.asarray(lp, float), np.asarray(ll, float)
    bridge = logq_fn is not None          # start=chains: generalised tempering from the cloud q to the posterior (Cai et al. 2021):
    lq = np.asarray(logq_fn(X), float) if bridge else np.zeros(n)   # target at stage phi = q^(1-phi) (prior x likelihood)^phi, so the
    tq = (lambda: lp + ll - lq) if bridge else (lambda: ll)           # tempered quantity is log prior + log likelihood - log q; logZ is then
    logW, logZ = np.full(n, -np.log(n)), 0.0                          # the marginal data density local to the cloud's region
    phi, c, stages, n_ev = 0.0, float(c0), [], n
    log(f"stage 0: {n} {'prior' if X0 is None else 'cloud'} draws, {int(np.isfinite(ll).sum())} with a solution, {time.time() - t0:.0f} s")
    for s in range(1, max_stages + 1):
        finite = np.isfinite(ll) & np.isfinite(lp)
        n_target = alpha * max(int(finite.sum()), 1)
        logw_at = lambda p: logW + (p - phi) * np.where(finite, tq(), -np.inf)
        if _ess(logw_at(1.0)) >= n_target:
            phin = 1.0
        else:
            lo, hi = phi, 1.0
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                if _ess(logw_at(mid)) >= n_target:
                    lo = mid
                else:
                    hi = mid
            phin = lo if lo > phi else hi                   # hi: the smallest step found when no phi reaches the target ESS
        lw = logw_at(phin)
        inc = logsumexp(lw)                                  # log of the incremental evidence (the weights were normalised)
        logZ += float(inc)
        logW = lw - inc
        ess = _ess(logW)
        phi = phin
        idx = systematic_resample(logW, rng)
        X, lp, ll, lq = X[idx], lp[idx], ll[idx], lq[idx]
        logW = np.full(n, -np.log(n))
        Sigma = np.atleast_2d(np.cov(X.T)) + 1e-10 * np.eye(k)
        acc_tot, prop_tot = 0, 0
        for _ in range(m):
            for b in np.array_split(rng.permutation(k), max(1, min(blocks, k))):
                b = np.asarray(b)
                try:
                    Lb = np.linalg.cholesky(Sigma[np.ix_(b, b)])
                except np.linalg.LinAlgError:
                    Lb = np.diag(np.sqrt(np.diag(Sigma)[b]) + 1e-8)
                Y = X.copy()
                Y[:, b] = X[:, b] + c * (rng.standard_normal((n, len(b))) @ Lb.T)
                lpy, lly = target.evaluate(Y)
                lpy, lly = np.asarray(lpy, float), np.asarray(lly, float)
                n_ev += n
                if bridge:
                    lqy = np.asarray(logq_fn(Y), float)
                    new, cur = (1 - phi) * lqy + phi * (lpy + lly), (1 - phi) * lq + phi * (lp + ll)
                else:
                    new, cur = lpy + phi * lly, lp + phi * ll
                with np.errstate(invalid="ignore"):
                    a = np.isfinite(new) & (np.log(rng.uniform(size=n)) < (new - cur))
                X[a], lp[a], ll[a] = Y[a], lpy[a], lly[a]
                if bridge:
                    lq[a] = lqy[a]
                acc_tot += int(a.sum())
                prop_tot += n
        acc = acc_tot / max(prop_tot, 1)
        c = c * (0.95 + 0.10 * np.exp(16 * (acc - 0.25)) / (1 + np.exp(16 * (acc - 0.25))))
        uniq = len(np.unique(X, axis=0))
        stages.append({"stage": s, "phi": phi, "ESS after correction": ess, "acceptance": acc, "c after": c,
                       "unique particles": uniq, "evaluations": n_ev, "seconds": time.time() - t0})
        log(f"stage {s}: phi {phi:.6f}, ESS {ess:.0f}, acceptance {acc:.2f}, c {c:.3f}, unique {uniq}, {time.time() - t0:.0f} s")
        if phi >= 1.0:
            break
    return X, logW, lp, ll, logZ, stages


# ----------------------------------------------------------------------------------------------------- the run on a DSGE
def matching_chains(ER, w: float, compare: str | None):
    """The saved Metropolis chains of the same specification (first run and its seeds), as estimate_rot.py start=pooled takes them."""
    ptag = f"_w{w:g}" + ER.PTAG + ER.STAG
    pattern = compare or f"dsge_ph_{ER.MODEL}_draws_*{ptag}*.npy"
    files = sorted(OUT.glob(pattern))
    if not compare:
        files = [f for f in files if re.search(re.escape(ptag) + r"(_seed\d+)?$", f.stem)]
    return files


def main():
    import pandas as pd
    n, alpha, m = int(_arg("n", 1000)), float(_arg("alpha", 0.5)), int(_arg("m", 1))
    blocks, workers, seed = int(_arg("blocks", 2)), int(_arg("workers", 8)), int(_arg("seed", 1))
    w, max_stages, compare = float(_arg("w", 1.0)), int(_arg("max_stages", 300)), _arg("compare", None)
    start = _arg("start", "prior")
    if start not in ("prior", "chains"):
        raise SystemExit("start must be prior or chains")
    t0 = time.time()
    with DSGETarget(workers=workers, w=w) as T:
        ER = T.ER
        print(f"model {ER.MODEL}, prior {ER.PRIOR}, sample {ER.SAMPLE}, gdp {ER.GDP_SA}, fixed {ER.FIXED}, {T.k} parameters; "
              f"N {n}, alpha {alpha}, m {m}, blocks {blocks}, workers {workers}, seed {seed}", flush=True)
        X0 = logq_fn = None
        if start == "chains":                 # 21 Oct 2026: a bridging run from a cloud around the pooled Metropolis chains
            from scipy.stats import norm
            files0 = matching_chains(ER, w, compare)
            if not files0:
                raise SystemExit("start=chains needs saved Metropolis chains of this specification")
            D0 = np.vstack([np.load(f) for f in files0])
            mu0, sd0 = D0.mean(0), 2.0 * D0.std(0)
            lo = np.array([np.nextafter(d[1], d[2]) for d in T.dists])
            hi = np.array([np.nextafter(d[2], d[1]) for d in T.dists])
            X0 = np.clip(mu0 + sd0 * np.random.default_rng(seed).standard_normal((n, T.k)), lo, hi)
            logq_fn = lambda Z_: norm.logpdf(np.asarray(Z_, float), mu0, sd0).sum(1)
            print(f"start=chains: cloud around {len(files0)} chain(s), {D0.shape[0]:,} draws: {', '.join(f.name for f in files0)}", flush=True)
        X, logW, lp, ll, logZ, stages = run_smc(T, n=n, alpha=alpha, m=m, blocks=blocks, seed=seed, max_stages=max_stages,
                                                log=lambda s: print(s, flush=True), X0=X0, logq_fn=logq_fn)
    Z = ER.observables()
    mean, sd = X.mean(0), X.std(0)
    lo5, hi95 = np.percentile(X, 5, 0), np.percentile(X, 95, 0)
    files = matching_chains(ER, w, compare)
    D = np.vstack([np.load(f) for f in files]) if files else None
    tab = pd.DataFrame({"prior": [f"{e[1]} ({e[2]}, {e[3]})" for e in ER.EST], "SMC mean": mean, "SMC 5%": lo5, "SMC 95%": hi95,
                        "SMC s.d.": sd}, index=ER.NAMES)
    if D is not None and D.shape[1] == T.k:
        tab["MH mean"], tab["MH 5%"], tab["MH 95%"] = D.mean(0), np.percentile(D, 5, 0), np.percentile(D, 95, 0)
        tab["(SMC - MH) / SMC s.d."] = (mean - D.mean(0)) / np.where(sd > 0, sd, np.nan)
    pm = ER.pieces(mean, Z)
    pmh = ER.pieces(D.mean(0), Z) if D is not None and D.shape[1] == T.k else None
    stamp = dt.datetime.now()
    tag = f"_{ER.MODEL}_w{w:g}" + ER.PTAG + ER.STAG + f"_n{n}" + (f"_seed{seed}" if seed != 1 else "") + ("_chains" if start == "chains" else "")
    base = OUT / f"dsge_smc_{stamp:%Y%m%d_%H%M}{tag}"
    np.save(base.with_name(base.name + "_particles.npy"), X)
    np.save(base.with_name(base.name + "_logw.npy"), logW)
    st = pd.DataFrame(stages).set_index("stage")
    worst = tab["(SMC - MH) / SMC s.d."].abs().max() if "MH mean" in tab else float("nan")
    L = [f"# Sequential Monte Carlo estimate of the DSGE posterior: soe_{ER.MODEL} ({stamp:%d %B %Y, %H:%M})", "",
         f"**NOT FOR CITATION** (research code, `research/dsge/smc.py`). Model `soe_{ER.MODEL}.py`, prior {ER.PRIOR}, sample {ER.SAMPLE}, "
         f"GDP {ER.GDP_SA}, calibrated {ER.FIXED or 'none'}; system-prior weight w = {w:g}. SMC: {n:,} particles, adaptive tempering "
         f"to an ESS share of {alpha:g}, {m} mutation step(s) of a blocked random-walk Metropolis ({blocks} random blocks) per stage, "
         f"{len(stages)} stages, {stages[-1]['evaluations']:,} posterior evaluations in {time.time() - t0:.0f} s on {workers} "
         f"worker(s); seed {seed}. " + ("Particles start from the prior (no mode search, no earlier chain)." if start == "prior" else
         "**Bridging run (start=chains):** particles start from a Gaussian cloud around the pooled Metropolis chains (mean, 2 x s.d. per "
         "parameter); the target moves from that cloud to the posterior by generalised tempering (Cai et al. 2021). Not an independent "
         "check of the chains; the marginal data density below is local to the cloud's region."), "",
         f"- **Log marginal data density (SMC estimate): {logZ:.2f}** (the parameter prior's truncation constant is not included; "
         "comparable across runs of the same model, prior and data).",
         f"- At the SMC posterior mean: log prior {pm[0]:.1f}, log likelihood {pm[1]:.1f}; transmission strength (trough per pp of "
         f"first-year tightening) CPI {pm[4]['infl']:.2f}, GDP growth {pm[4]['growth']:.2f}." if pm else
         "- The SMC posterior mean itself has no solution (a sign of a multimodal posterior); see the particles.",
         (f"- At the pooled Metropolis mean ({len(files)} chain(s), {D.shape[0]:,} draws: {', '.join(f.name for f in files)}): log "
          f"likelihood {pmh[1]:.1f}; transmission CPI {pmh[4]['infl']:.2f}, GDP growth {pmh[4]['growth']:.2f}. **Largest gap between "
          f"the two posterior means: {worst:.2f} SMC standard deviations** ({tab['(SMC - MH) / SMC s.d.'].abs().idxmax()})."
          if pmh else "- No Metropolis chains of this specification on file for comparison."),
         f"- Final stage: acceptance {stages[-1]['acceptance']:.2f}, c {stages[-1]['c after']:.3f}, unique particles "
         f"{stages[-1]['unique particles']} of {n}.", "",
         "## Posterior: SMC against the pooled Metropolis chains", "", tab.to_markdown(floatfmt=".3f"), "",
         "## Stages", "", st.to_markdown(floatfmt=".4f"), ""]
    md = base.with_name(base.name + ".md")       # not with_suffix: it would eat a decimal in the tag ("thfix0.85" -> "thfix0")
    md.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:10]))
    print("saved", md)


if __name__ == "__main__":
    main()
