"""The forward-looking CGE (Stage 2), step 3 (17 Oct 2026): a general stacked Newton solver for perfect-foresight models.

The method is the one Dynare's perfect-foresight solver uses (Juillard 1996, CEPREMAP Working Paper 9602; Laffargue 1990):
every period's equations are written once as f(y[t-1], y[t], y[t+1], x[t], x[t+1]) = 0; the T periods are stacked into
one system, y[0] is the initial state and y[T+1] the terminal steady state, and Newton's method solves all periods at
once. The Jacobian is block-tridiagonal (period t depends on t-1, t, t+1 only), so it is stored sparse and solved by a
sparse direct method (SciPy's SuperLU).

The Jacobian's blocks are computed by finite differences, but cheaply and exactly in structure: the residual function
takes the lagged, current and lead values as separate arrays over all periods, so perturbing variable i in the lag
array (in every period at once) gives column i of every A_t = dF_t/dy_t-1 in one evaluation; the same for the current
and lead arrays. A Jacobian costs 3n evaluations of the vectorised residual, whatever T is. Exact zeros (variables an
equation does not contain) are dropped, so the stored matrix has the model's true sparsity.

A model is any object with:
  n_y (int), names (list of n_y str), n_x (int)
  resid(ylag, y, ylead, x, xlead) -> array (n_y, T)   [each argument an array (n_y or n_x, T)]
NOT part of Infinity GEM; research code (opt-in).
"""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import splu


class NoConvergence(RuntimeError):
    pass


def _views(Y, y0, yT1):
    """Lag, current and lead arrays (n, T) from the stacked unknowns Y (n, T) and the fixed end points."""
    lag = np.column_stack([y0, Y[:, :-1]])
    lead = np.column_stack([Y[:, 1:], yT1])
    return lag, Y, lead


def stacked_residuals(model, Y, y0, yT1, X):
    """Residuals F (n, T). X is (n_x, T + 1): exogenous values for periods 1..T and T+1 (the lead of the last period)."""
    lag, cur, lead = _views(Y, y0, yT1)
    return model.resid(lag, cur, lead, X[:, :-1], X[:, 1:])


def jacobian(model, Y, y0, yT1, X, rel=1e-7):
    """Sparse block-tridiagonal Jacobian dF/dY ((n T) x (n T)), variables ordered period by period (y_1, y_2, ...)."""
    n, T = Y.shape
    lag, cur, lead = _views(Y, y0, yT1)
    xc, xl = X[:, :-1], X[:, 1:]
    F0 = model.resid(lag, cur, lead, xc, xl)
    rows, cols, vals = [], [], []
    t_idx = np.arange(T)
    for which, shift in (("lag", -1), ("cur", 0), ("lead", 1)):
        base = {"lag": lag, "cur": cur, "lead": lead}[which]
        for i in range(n):
            h = rel * np.maximum(1.0, np.abs(base[i]))
            pert = base.copy()
            pert[i] = pert[i] + h
            args = dict(lag=lag, cur=cur, lead=lead)
            args[which] = pert
            dF = (model.resid(args["lag"], args["cur"], args["lead"], xc, xl) - F0) / h   # (n, T): d F_t / d y_{t+shift, i}
            src_t = t_idx + shift                      # period of the perturbed variable
            ok = (src_t >= 0) & (src_t < T)            # y_0 and y_T+1 are fixed, not unknowns
            sub = dF[:, ok]
            e_idx, pos = np.nonzero(np.abs(sub) > 1e-13)
            rows.append(t_idx[ok][pos] * n + e_idx)
            cols.append(src_t[ok][pos] * n + i)
            vals.append(sub[e_idx, pos])
    J = sp.csc_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(n * T, n * T))
    return J, F0


def solve(model, y0, yT1, X, guess, tol=1e-10, max_iter=50, verbose=False):
    """Stacked Newton with a backtracking line search on the max-norm. Returns (Y (n, T), info dict)."""
    Y = np.array(guess, dtype=float)
    n, T = Y.shape
    assert X.shape == (model.n_x, T + 1), f"X must be (n_x, T+1) = ({model.n_x}, {T + 1}), got {X.shape}"
    history = []
    for it in range(max_iter + 1):
        J, F = jacobian(model, Y, y0, yT1, X)
        err = float(np.abs(F).max())
        history.append(err)
        if verbose:
            print(f"  Newton {it}: max |F| {err:.2e}, Jacobian nnz {J.nnz:,}")
        if not np.isfinite(err):
            raise NoConvergence(f"non-finite residuals at step {it}")
        if err < tol:
            return Y, dict(iterations=it, max_residual=err, history=history, nnz=J.nnz)
        step = splu(J).solve(-F.T.reshape(-1)).reshape(T, n).T
        lam = 1.0
        while lam > 1e-6:
            Ynew = Y + lam * step
            with np.errstate(all="ignore"):
                e_new = np.abs(stacked_residuals(model, Ynew, y0, yT1, X)).max()
            if np.isfinite(e_new) and e_new < err:
                break
            lam /= 2
        else:
            raise NoConvergence(f"line search failed at step {it} (max |F| {err:.2e})")
        Y = Ynew
    raise NoConvergence(f"no convergence after {max_iter} steps (max |F| {err:.2e})")
