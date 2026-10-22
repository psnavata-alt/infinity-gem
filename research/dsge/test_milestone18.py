"""DSGE research, milestone 18 tests (19 Oct 2026, about 11:15 PM): the longer sample with the COVID quarters missing.

T18a Without missing data the Kalman filter is unchanged: the same log likelihood, to the last bit, as the milestone 4 filter
     (kept here as the reference), and equal to the exact Gaussian likelihood (T16's brute force).
T18b With missing entries (two whole quarters and one partly observed quarter) the filter equals the exact Gaussian log
     likelihood of the observed entries only (brute force: the stacked covariance with the missing rows and columns deleted).
T18c The data: the default sample (2002Q1-2019Q4) is unchanged; the long sample runs to ph_data.LONG_END with exactly the
     COVID quarters missing, demeaned over the observed quarters.
"""
import sys
from pathlib import Path

import numpy as np
from scipy import linalg, stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import estimate as E  # noqa: E402
import ph_data         # noqa: E402

results = []


def check(name, ok, detail):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def kalman_m4(Pm, Rm, Q, H, Z, me=1e-4):
    """The milestone 4 filter (no missing data), unchanged: the reference for T18a."""
    n = Pm.shape[0]
    RQR = Rm @ Q @ Rm.T
    Sig = linalg.solve_discrete_lyapunov(Pm, RQR)
    x = np.zeros(n)
    Me = np.eye(H.shape[0]) * me
    ll = 0.0
    for z in Z:
        Fm = H @ Sig @ H.T + Me
        e = z - H @ x
        cf = linalg.cho_factor(Fm)
        ll -= 0.5 * (len(z) * np.log(2 * np.pi) + 2 * np.log(np.diag(cf[0])).sum() + e @ linalg.cho_solve(cf, e))
        K = Pm @ Sig @ H.T @ linalg.cho_solve(cf, np.eye(len(z)))
        x = Pm @ x + K @ e
        Sig = Pm @ Sig @ Pm.T + RQR - K @ Fm @ K.T
    return ll


def exact(Pm, Rm, Q, H, Z, me=1e-4):
    """Exact Gaussian log likelihood of the observed (finite) entries of Z, by brute force."""
    Sig = linalg.solve_discrete_lyapunov(Pm, Rm @ Q @ Rm.T)
    T, m = Z.shape
    C = np.zeros((T * m, T * m))
    for s in range(T):
        for t in range(T):
            blk = H @ np.linalg.matrix_power(Pm, abs(s - t)) @ Sig @ H.T
            C[s * m:(s + 1) * m, t * m:(t + 1) * m] = blk if s >= t else blk.T
    C += np.eye(T * m) * me
    z = Z.ravel()
    ok = np.isfinite(z)
    return stats.multivariate_normal(np.zeros(ok.sum()), C[np.ix_(ok, ok)]).logpdf(z[ok])


truth = np.array([2.0, 0.70, 0.55, 1.6, 0.30, 0.75, 0.80, 0.85, 0.45, 0.30, 0.30, 0.60, 0.50, 0.40])
Pm, Rm, Q, H = E.state_space(truth)
Z = E.simulate(truth, 14, seed=5)
new, old, bf = E.kalman_loglik(Pm, Rm, Q, H, Z), kalman_m4(Pm, Rm, Q, H, Z), exact(Pm, Rm, Q, H, Z)
check("T18a no missing data: filter unchanged and exact", new == old and abs(new - bf) < 1e-6 * abs(bf),
      f"new {new:.10f}, milestone 4 {old:.10f} (identical: {new == old}), brute force {bf:.10f}")

Zm = Z.copy()
Zm[4] = np.nan
Zm[5] = np.nan
Zm[9, [0, 3]] = np.nan
km, bm = E.kalman_loglik(Pm, Rm, Q, H, Zm), exact(Pm, Rm, Q, H, Zm)
drop = E.kalman_loglik(Pm, Rm, Q, H, np.delete(Z, [4, 5], axis=0))   # simply deleting the quarters is NOT the same model
check("T18b missing entries: filter = exact likelihood of the observed entries", abs(km - bm) < 1e-6 * abs(bm),
      f"filter {km:.10f}, brute force {bm:.10f}; deleting the rows instead would give {drop:.4f}")

before = ph_data.observables()
short_ok = before.shape == (72, 4) and str(before.index[0]) == "2002Q1" and str(before.index[-1]) == "2019Q4"
lo = ph_data.observables(end=ph_data.LONG_END, covid="missing")
miss = lo.index[lo.isna().all(axis=1)]
covid_ok = [str(q) for q in miss] == [str(q) for q in __import__("pandas").period_range(*ph_data.COVID, freq="Q")]
partial = int((lo.isna().any(axis=1) & ~lo.isna().all(axis=1)).sum())
means = float(np.nanmax(np.abs(lo.mean().to_numpy())))
lo_oil = ph_data.observables_oil(end=ph_data.LONG_END, covid="missing")
oil_ok = bool(lo_oil["doil"].isna().equals(lo_oil["dy"].isna()))
check("T18c data: default sample unchanged; long sample with exactly the COVID quarters missing",
      short_ok and covid_ok and partial == 0 and means < 1e-12 and str(lo.index[-1]) == ph_data.LONG_END and oil_ok,
      f"default {before.shape} {before.index[0]}-{before.index[-1]}; long {lo.shape} {lo.index[0]}-{lo.index[-1]}, "
      f"missing {len(miss)} quarters {miss[0] if len(miss) else ''}-{miss[-1] if len(miss) else ''}, partly missing rows {partial}, "
      f"largest mean {means:.1e}; Dubai missing in the same quarters: {oil_ok}")

raw = before["dy"]
stl = ph_data.observables(gdp_sa="stl")
others_same = all(stl[v].equals(before[v]) for v in ("pi", "i", "de"))
check("T18d GDP seasonally adjusted by STL (milestone 18b): less leftover seasonality; other series unchanged",
      others_same and abs(stl["dy"].autocorr(4)) < abs(raw.autocorr(4)) and stl["dy"].std() < raw.std(),
      f"GDP growth lag-4 autocorrelation {raw.autocorr(4):.2f} -> {stl['dy'].autocorr(4):.2f}; s.d. {raw.std():.2f} -> "
      f"{stl['dy'].std():.2f}; inflation, rate and peso unchanged: {others_same}")

n_pass = sum(ok for _, ok, _ in results)
print(f"\n{n_pass}/{len(results)} passed")
sys.exit(0 if n_pass == len(results) else 1)
