"""DSGE research, milestone 1 (19 Oct 2026, about 1:30 AM): linear rational-expectations
solver by the generalised Schur (QZ) method of Klein (2000), the method behind Dynare's first-order solution.

Model form:  A E_t[x_{t+1}] = B x_t,  x = [k; d], with k (n_k) predetermined states, including the exogenous processes, and d
the forward-looking (jump) variables. Shocks enter the exogenous states: k_{t+1} = P k_t + R eps_{t+1}.
Solution:    d_t = F k_t,  k_{t+1} = P k_t.  Blanchard and Kahn (1980): a unique stable solution needs exactly n_k stable
             generalised eigenvalues (|lambda| < 1) and an invertible Z11; otherwise the model is indeterminate (too many) or
             explosive (too few) and solve() says so.

Klein, P. (2000). "Using the generalized Schur form to solve a multivariate linear rational expectations model." Journal of
Economic Dynamics and Control 24(10): 1405-1423. Blanchard, O. J., and C. M. Kahn (1980). Econometrica 48(5): 1305-1311.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.linalg import ordqz


class BlanchardKahnError(ValueError):
    pass


@dataclass
class Solution:
    F: np.ndarray            # d_t = F k_t
    P: np.ndarray            # k_{t+1} = P k_t (+ R eps)
    eig: np.ndarray          # generalised eigenvalues, stable first
    n_stable: int

    def irf(self, R: np.ndarray, shock: np.ndarray, T: int = 40) -> tuple[np.ndarray, np.ndarray]:
        """Impulse responses to an innovation in period 0: k_0 = R shock; returns (k path, d path), T rows each."""
        k = np.zeros((T, self.P.shape[0]))
        k[0] = R @ shock
        for t in range(1, T):
            k[t] = self.P @ k[t - 1]
        return k, k @ self.F.T

    def simulate(self, R: np.ndarray, eps: np.ndarray, k0=None) -> tuple[np.ndarray, np.ndarray]:
        """Paths for a sequence of innovations eps (T x n_eps): k_{t+1} = P k_t + R eps_{t+1}."""
        T = eps.shape[0]
        k = np.zeros((T, self.P.shape[0]))
        k[0] = (np.zeros(self.P.shape[0]) if k0 is None else k0) + R @ eps[0]
        for t in range(1, T):
            k[t] = self.P @ k[t - 1] + R @ eps[t]
        return k, k @ self.F.T


def solve(A: np.ndarray, B: np.ndarray, n_k: int, tol: float = 1e-9) -> Solution:
    """Solve A E[x'] = B x by QZ (Klein 2000). Raises BlanchardKahnError when the stable solution is not unique."""
    A, B = np.asarray(A, float), np.asarray(B, float)
    n = A.shape[0]
    # pencil (B - lambda A): lambda = alpha / beta is the growth factor of x; 'iuc' puts |lambda| < 1 (stable) first
    S, T, alpha, beta, Q, Z = ordqz(B, A, sort="iuc", output="complex")
    with np.errstate(divide="ignore", invalid="ignore"):
        lam = np.where(np.abs(beta) > tol, alpha / np.where(np.abs(beta) > tol, beta, 1), np.inf)
    n_s = int(np.sum(np.abs(lam) < 1 - 1e-12))
    if n_s != n_k:
        kind = "indeterminate (too many stable roots)" if n_s > n_k else "no stable solution (too few stable roots)"
        raise BlanchardKahnError(f"Blanchard-Kahn: {n_s} stable roots for {n_k} predetermined variables: {kind}")
    Z11, Z21 = Z[:n_k, :n_k], Z[n_k:, :n_k]
    if np.linalg.cond(Z11) > 1 / tol:
        raise BlanchardKahnError("Blanchard-Kahn rank condition fails: Z11 is singular")
    Z11i = np.linalg.inv(Z11)
    S11, T11 = S[:n_k, :n_k], T[:n_k, :n_k]
    F = Z21 @ Z11i
    P = Z11 @ np.linalg.solve(T11, S11) @ Z11i
    if max(np.abs(F.imag).max(initial=0), np.abs(P.imag).max(initial=0)) > 1e-8:
        raise BlanchardKahnError("complex solution: the stable block mixes conjugate roots unevenly")
    return Solution(F=F.real, P=P.real, eig=lam, n_stable=n_s)


def linearize(f, xss: np.ndarray, n_eq: int | None = None, h: float = 1e-6, log: np.ndarray | None = None):
    """Numerical first-order expansion of f(x_next, x) = 0 around the steady state xss (central differences).
    Returns (A, B) for A E[x'] = B x. With log[i] True, variable i is in log deviations (x = xss * exp(xhat))."""
    xss = np.asarray(xss, float)
    n = xss.size
    log = np.zeros(n, bool) if log is None else np.asarray(log, bool)
    lvl = lambda xh: np.where(log, xss * np.exp(xh), xss + xh)
    g = lambda xp, x: np.asarray(f(lvl(xp), lvl(x)), float)
    m = n_eq or n
    J1, J2 = np.zeros((m, n)), np.zeros((m, n))
    z = np.zeros(n)
    for j in range(n):
        e = np.zeros(n); e[j] = h
        J1[:, j] = (g(z + e, z) - g(z - e, z)) / (2 * h)
        J2[:, j] = (g(z, z + e) - g(z, z - e)) / (2 * h)
    return J1, -J2
