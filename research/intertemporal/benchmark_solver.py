"""The forward-looking CGE (Stage 2), step 4(a) (17 Oct 2026, night): the stacked solver (pf_solver.py) against independent benchmarks.

Neither benchmark shares code with the solver:
  (1) Brock and Mirman (1972), J. Economic Theory 4(3): log utility, y = A k^alpha, full depreciation. The exact optimal
      policy is known in closed form: k[t+1] = alpha beta A k[t]^alpha (c = (1 - alpha beta) y). The solver's path
      from k0 = 0.5 k* must match it to machine precision (except the last few years, where the finite horizon's terminal
      condition k[T] = k* binds; the exact path is not exactly at k* there).
  (2) The linearised Ramsey model (delta < 1, CRRA), solved by the Blanchard and Kahn (1980) eigenvalue method: the
      stable eigenvalue of the linearised system gives the deviation path k[t] - k* = lambda^t (k0 - k*). For a small
      initial gap the solver's path must agree to second order: the error falls about 4-fold when the gap halves.
Run:  py research/intertemporal/benchmark_solver.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pf_solver  # noqa: E402


class Ramsey:
    """One sector, one unknown per year: k[t] (end of year). Euler: c[t]^-s = beta c[t+1]^-s (A alpha k[t]^(alpha-1) + 1 - d),
    c[t] = A k[t-1]^alpha + (1 - d) k[t-1] - k[t]. The residual uses y = (k[t-1], k[t], k[t+1])."""
    n_y, n_x, names = 1, 1, ["k"]

    def __init__(self, alpha=0.36, beta=0.96, delta=1.0, sigma=1.0, A=1.0):
        self.a, self.b, self.d, self.s, self.A = alpha, beta, delta, sigma, A

    def c(self, k_lag, k):
        return self.A * k_lag ** self.a + (1 - self.d) * k_lag - k

    def resid(self, ylag, y, ylead, x, xlead):
        kl, k, kn = ylag[0], y[0], ylead[0]
        c0, c1 = self.c(kl, k), self.c(k, kn)
        R = self.A * self.a * k ** (self.a - 1) + 1 - self.d
        return np.atleast_2d(c0 ** (-self.s) - self.b * c1 ** (-self.s) * R)

    def kss(self):
        return (self.a * self.A / (1 / self.b - 1 + self.d)) ** (1 / (1 - self.a))


def solve_path(m, k0, T):
    ks = m.kss()
    X = np.ones((1, T + 1))
    guess = np.linspace(k0, ks, T)[None, :]
    Y, info = pf_solver.solve(m, np.array([k0]), np.array([ks]), X, guess, tol=1e-13)
    return Y[0], info


def brock_mirman():
    m = Ramsey(delta=1.0, sigma=1.0)
    ks, T = m.kss(), 100
    k0 = 0.5 * ks
    path, info = solve_path(m, k0, T)
    exact = np.empty(T)
    k = k0
    for t in range(T):
        k = m.a * m.b * m.A * k ** m.a
        exact[t] = k
    err = np.abs(path[:T - 10] / exact[:T - 10] - 1).max()
    return err, info["iterations"]


def blanchard_kahn(gap, T=200):
    m = Ramsey(delta=0.08, sigma=2.0)
    ks = m.kss()
    # linearise the second-order difference equation F(k[t-1], k[t], k[t+1]) = 0 around k*: a dk[t-1] + b dk[t] + c dk[t+1] = 0
    h = 1e-6 * ks
    f = lambda a, b, c: m.resid(np.array([[a]]), np.array([[b]]), np.array([[c]]), None, None)[0, 0]
    A_ = (f(ks + h, ks, ks) - f(ks - h, ks, ks)) / (2 * h)
    B_ = (f(ks, ks + h, ks) - f(ks, ks - h, ks)) / (2 * h)
    C_ = (f(ks, ks, ks + h) - f(ks, ks, ks - h)) / (2 * h)
    roots = np.roots([C_, B_, A_])                       # c lam^2 + b lam + a = 0
    stable = roots[np.abs(roots) < 1]
    assert len(stable) == 1, f"Blanchard-Kahn condition fails: roots {roots}"   # saddle path: one stable root
    lam = float(np.real(stable[0]))
    k0 = ks * (1 - gap)
    lin = ks + (k0 - ks) * lam ** np.arange(1, T + 1)
    path, info = solve_path(m, k0, T)
    err = np.abs(path[:T // 2] - lin[:T // 2]).max() / ks
    return err, lam, np.abs(roots)


def main():
    res = {}
    e, it = brock_mirman()
    res["brock_mirman"] = e < 1e-10
    print(f"(1) Brock-Mirman closed form: largest relative gap over years 1-90 {e:.1e} ({it} Newton steps) -> "
          f"{'PASS' if res['brock_mirman'] else 'FAIL'}")
    e1, lam, roots = blanchard_kahn(0.02)
    e2, *_ = blanchard_kahn(0.01)
    ratio = e1 / e2
    res["blanchard_kahn"] = e2 < 1e-4 and 3.0 < ratio < 5.0
    print(f"(2) Blanchard-Kahn linear solution (stable root {lam:.6f}; |roots| {roots.round(4)}): gap of solver to linear "
          f"path {e1:.2e} (initial gap 2%) and {e2:.2e} (1%); ratio {ratio:.2f} (second order: about 4) -> "
          f"{'PASS' if res['blanchard_kahn'] else 'FAIL'}")
    print(f"\n{sum(res.values())} of {len(res)} benchmarks pass")
    return res


if __name__ == "__main__":
    main()
