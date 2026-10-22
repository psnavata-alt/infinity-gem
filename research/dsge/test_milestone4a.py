"""DSGE research, milestone 4a tests (19 Oct 2026): the estimation machinery.

T16 Kalman filter log likelihood = the exact Gaussian log likelihood of the stacked sample (brute force, T = 12).
T17 Parameter recovery: on 300 quarters simulated from known parameters, the posterior mode lies close to the truth for the
    well-identified parameters (policy rule, Calvo parameters, persistence), and the shock sizes are recovered.
"""
import sys
import time
from pathlib import Path

import numpy as np
from scipy import linalg, stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import estimate as E  # noqa: E402

results = []


def check(name, ok, detail):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


truth = np.array([2.0, 0.70, 0.55, 1.6, 0.30, 0.75, 0.80, 0.85, 0.45, 0.30, 0.30, 0.60, 0.50, 0.40])
Z = E.simulate(truth, 12, seed=3)
Pm, Rm, Q, H = E.state_space(truth)
ll_kf = E.kalman_loglik(Pm, Rm, Q, H, Z)
# brute force: Cov(z_s, z_t) = H P^{|s-t|} Sigma H' (+ me on the diagonal)
Sig = linalg.solve_discrete_lyapunov(Pm, Rm @ Q @ Rm.T)
T, m = Z.shape
C = np.zeros((T * m, T * m))
for s in range(T):
    for t in range(T):
        blk = H @ np.linalg.matrix_power(Pm, abs(s - t)) @ Sig @ H.T
        C[s * m:(s + 1) * m, t * m:(t + 1) * m] = blk if s >= t else blk.T
C += np.eye(T * m) * 1e-4
ll_bf = stats.multivariate_normal(np.zeros(T * m), C, allow_singular=False).logpdf(Z.ravel())
check("T16 Kalman likelihood = exact Gaussian likelihood", abs(ll_kf - ll_bf) < 1e-6 * abs(ll_bf), f"{ll_kf:.6f} vs {ll_bf:.6f}")

t0 = time.time()
Zs = E.simulate(truth, 300, seed=11)
est, lp, res = E.mode(Zs, maxiter=6000)
key = ["theta", "theta_F", "phi_pi", "rho_i", "rho_a", "rho_y", "sd_v", "sd_a"]
errs = {k: est[E.NAMES.index(k)] - truth[E.NAMES.index(k)] for k in key}
ok = all(abs(v) < 0.35 * max(abs(truth[E.NAMES.index(k)]), 0.1) for k, v in errs.items())
check("T17 parameter recovery (posterior mode, 300 simulated quarters)", ok,
      "; ".join(f"{k} {est[E.NAMES.index(k)]:.2f} (true {truth[E.NAMES.index(k)]:.2f})" for k in key) + f"; {time.time() - t0:.0f} s")

n_pass = sum(ok for _, ok, _ in results)
print(f"\n{n_pass}/{len(results)} passed")
sys.exit(0 if n_pass == len(results) else 1)
