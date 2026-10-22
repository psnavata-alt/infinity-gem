"""The forward-looking CGE (Stage 2), milestone 1: a one-sector perfect-foresight (forward-looking) growth model solved for all years at once.

Why a prototype first (17 Oct 2026; design: a design note (not included)): Stage 2 stacks ~150 equations x
~10 sectors x 30-50 years into one system. Before building that on the condensed SAM, this file tests the two pieces every
Stage 2 equation will rest on, with SciPy only (no Pyomo/Ipopt install needed):
  (1) the intertemporal blocks: a Ramsey household (consumption Euler equation, CRRA utility) and firms that invest with
      quadratic adjustment costs (Tobin's q, Hayashi 1982), with a terminal condition at the steady state;
  (2) the solver: Newton's method on the stacked system with a sparse Jacobian (scipy.sparse; spsolve).
Model (per period t = 0..T-1; k_0 given; Cobb-Douglas output y = A k^alpha, labour fixed at 1):
  Euler:       c_t^-s = beta * c_{t+1}^-s * [ (alpha A_{t+1} k_{t+1}^(alpha-1) + q_{t+1}(1-delta) + phi/2 (i_{t+1}/k_{t+1})^2 - phi... ) / q_t ]
               (written below through the firm's q; see residuals())
  Investment:  q_t = 1 + phi (i_t / k_t - delta)                       (adjustment cost phi/2 (i/k - delta)^2 k)
  q equation:  q_t = beta_t * [ MPK_{t+1} + q_{t+1}(1-delta) + phi/2 ((i/k)^2 - delta^2)_{t+1} ]   with the household's
               stochastic discount factor beta (c_{t+1}/c_t)^-s
  Capital:     k_{t+1} = (1-delta) k_t + i_t
  Resources:   c_t + i_t + phi/2 (i_t/k_t - delta)^2 k_t = A_t k_t^alpha
  Terminal:    k_T = k* (the steady state of the final A)
Tests (run this file): (a) starting at the steady state with no shock, the path stays there (max deviation ~1e-12);
(b) a permanent 10% rise in A converges to the analytic new steady state k* = (alpha A / (1/beta - 1 + delta))^(1/(1-alpha));
(c) with phi -> 0 the model collapses to the textbook Ramsey model (q = 1 every period);
(d) an ANNOUNCED rise in A (known at t = 0, effective at t = 5) changes behaviour before t = 5: the anticipation effect a
    recursive-dynamic model cannot show (the reason for Stage 2). In this standard model households, expecting to be richer,
    consume more at once and investment FALLS before the change (17 Oct run: -9% to -12% in years 0-4), the textbook
    news-shock result (Barro and King 1984, QJE 99(4); Beaudry and Portier 2004, JME 51): a check that the solver gets a
    known, non-obvious answer right.
NOT part of Infinity GEM; research code. Run:  py research/intertemporal/pf_ramsey_prototype.py
"""
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import spsolve

ALPHA, BETA, DELTA, SIGMA = 0.35, 0.96, 0.05, 2.0


def kstar(A):
    return (ALPHA * A / (1 / BETA - 1 + DELTA)) ** (1 / (1 - ALPHA))


def unpack(z, T):
    c, i, q, k = z[:T], z[T:2 * T], z[2 * T:3 * T], z[3 * T:4 * T + 1]          # k has T+1 entries (k_0..k_T)
    return c, i, q, k


def residuals(z, A, k0, phi, T):
    c, i, q, k = unpack(z, T)
    r = []
    r.append(k[0] - k0)                                                        # initial capital
    r.extend(k[1:] - ((1 - DELTA) * k[:-1] + i))                               # accumulation
    adj = phi / 2 * (i / k[:-1] - DELTA) ** 2 * k[:-1]
    r.extend(c + i + adj - A * k[:-1] ** ALPHA)                                # resources
    r.extend(q - (1 + phi * (i / k[:-1] - DELTA)))                             # investment (Tobin's q)
    sdf = BETA * (c[1:] / c[:-1]) ** (-SIGMA)                                  # stochastic discount factor
    mpk = ALPHA * A[1:] * k[1:-1] ** (ALPHA - 1)
    x = i[1:] / k[1:-1]
    ret = mpk + q[1:] * (1 - DELTA) + phi / 2 * (x ** 2 - DELTA ** 2)        # return on one unit of installed capital
    r.extend(q[:-1] - sdf * ret)                                               # q equation (Euler for capital), t < T-1
    r.append(k[-1] - kstar(A[-1]))                                             # terminal condition
    return np.array(r)


def jacobian(z, A, k0, phi, T, h=1e-7):
    """Finite-difference Jacobian, stored sparse (each unknown enters only the equations of neighbouring periods, so
    about 99% of entries are zero). Fine for this prototype (4T+1 = 481 unknowns); Stage 2 will build the Jacobian
    analytically, block by block (design note, section 3)."""
    f0 = residuals(z, A, k0, phi, T)
    J = np.empty((len(f0), len(z)))
    for j in range(len(z)):
        dz = h * max(1.0, abs(z[j]))
        zp = z.copy(); zp[j] += dz
        J[:, j] = (residuals(zp, A, k0, phi, T) - f0) / dz
    J[np.abs(J) < 1e-14] = 0.0
    return sp.csc_matrix(J), f0


def solve(A, k0, phi=10.0, T=None, tol=1e-11):
    T = len(A) if T is None else T
    ks = kstar(A[-1])
    k = np.linspace(k0, ks, T + 1)
    i = DELTA * k[:-1]
    c = A * k[:-1] ** ALPHA - i
    z = np.concatenate([c, i, np.ones(T), k])
    for it in range(50):
        J, f = jacobian(z, A, k0, phi, T)
        err = np.abs(f).max()
        if err < tol:
            return unpack(z, T), it, err
        step = spsolve(J, -f)
        t_ = 1.0
        while t_ > 1e-6:
            if np.abs(residuals(z + t_ * step, A, k0, phi, T)).max() < err or t_ < 1e-3:
                break
            t_ /= 2
        z = z + t_ * step
    raise RuntimeError(f"no convergence: {err:.2e}")


def main():
    T = 120
    A0 = np.ones(T)
    k0 = kstar(1.0)
    (c, i, q, k), it, err = solve(A0, k0)
    print(f"(a) no shock from the steady state: max |k - k*| {np.abs(k - k0).max():.1e}, max |q - 1| {np.abs(q - 1).max():.1e} ({it} Newton steps)")
    A1 = np.full(T, 1.1)
    (c, i, q, k), it, err = solve(A1, k0)
    print(f"(b) permanent +10% productivity: k after 60 years {k[60]:.5f}, analytic new k* {kstar(1.1):.5f}, "
          f"gap at the end {abs(k[-2] - kstar(1.1)):.1e}; q jumps to {q[0]:.4f} on impact ({it} steps)")
    (c0, i0, q0, k0_), it, err = solve(A1, k0, phi=1e-6)
    print(f"(c) adjustment cost -> 0: max |q - 1| {np.abs(q0 - 1).max():.1e} (textbook Ramsey); first-year investment "
          f"{i0[0]:.4f} vs {i[0]:.4f} with adjustment costs")
    A2 = np.ones(T); A2[5:] = 1.1
    (c2, i2, q2, k2), it, err = solve(A2, k0)
    pre = (i2[:5] / (DELTA * k0) - 1) * 100
    print(f"(d) announced +10% productivity from year 5: investment in years 0-4 vs steady state (%): "
          f"{', '.join(f'{x:+.2f}' for x in pre)} -> behaviour changes before the change (here investment falls as households "
          f"consume more: the textbook news-shock result)")


if __name__ == "__main__":
    main()
