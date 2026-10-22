"""The forward-looking CGE (Stage 2), step 2 (17 Oct 2026): a two-sector perfect-foresight model with a static price block.

Builds on pf_ramsey_prototype.py (step 1). Two sectors, goods g (also the capital good; numeraire) and services s, so the
model has a relative price p (services in goods), the static CGE ingredient each year: market clearing for both goods and
one wage for mobile labour. Each sector has its own capital with quadratic adjustment costs (sector q), and the household
plans ahead over a CES consumption bundle (Euler equation in units of the numeraire).
  Production   y_g = A_g k_g^ag l^(1-ag),  y_s = A_s k_s^as (1-l)^(1-as)          (labour total 1, mobile)
  Wage         (1-ag) y_g / l = p (1-as) y_s / (1-l)
  Bundle       C = CES(c_g, c_s; weight w, elasticity e); price index P = [w + (1-w) p^(1-e)]^(1/(1-e))
               c_g = w P^e C,  c_s = (1-w) (p/P)^(-e) C
  Goods g      c_g + i_g + i_s + adjustment costs = y_g;   services  c_s = y_s
  Investment   q_j = 1 + phi (i_j/k_j - delta);  q_j,t = m_t+1 [r_j,t+1 + q_j,t+1 (1-delta) + phi/2 ((i/k)^2 - delta^2)_t+1]
               r_g = ag y_g / k_g,  r_s = p as y_s / k_s,  m_t+1 = beta (C_t+1 / C_t)^-sigma (P_t / P_t+1)
  Capital      k_j,t+1 = (1-delta) k_j,t + i_j,t;  k_j,0 given;  k_j,T = steady state of the final parameters
9T+2 equations in as many unknowns, stacked and solved by Newton (SciPy; finite-difference Jacobian stored sparse).
Tests: (a) no shock from the steady state stays there; (b) a permanent +10% in A_g converges to the new steady state
computed separately by the static steady-state system; (c) the relative price of services rises when goods productivity
rises (Balassa-Samuelson direction); (d) announced shock: behaviour moves before it takes effect.
NOT part of Infinity GEM; research code. Run:  py research/intertemporal/pf_two_sector.py
"""
import numpy as np
import scipy.sparse as sp
from scipy.optimize import fsolve
from scipy.sparse.linalg import spsolve

AG, AS, BETA, DELTA, SIGMA, W, E, PHI = 0.40, 0.30, 0.96, 0.05, 2.0, 0.5, 0.8, 8.0


def prices(C, p):
    P = (W + (1 - W) * p ** (1 - E)) ** (1 / (1 - E))
    return P, W * P ** E * C, (1 - W) * (p / P) ** (-E) * C


def steady(Ag, As):
    """Static steady state (q = 1, i = delta k, r = 1/beta - 1 + delta in every sector)."""
    R = 1 / BETA - 1 + DELTA

    def f(z):
        kg, ks, l, p, C = np.exp(z[0]), np.exp(z[1]), 1 / (1 + np.exp(-z[2])), np.exp(z[3]), np.exp(z[4])
        yg, ys = Ag * kg ** AG * l ** (1 - AG), As * ks ** AS * (1 - l) ** (1 - AS)
        P, cg, cs = prices(C, p)
        return [AG * yg / kg - R, p * AS * ys / ks - R, (1 - AG) * yg / l - p * (1 - AS) * ys / (1 - l),
                cg + DELTA * (kg + ks) - yg, cs - ys]
    z = fsolve(f, [np.log(3), np.log(2), 0.0, 0.0, 0.0], xtol=1e-13)
    return dict(kg=np.exp(z[0]), ks=np.exp(z[1]), l=1 / (1 + np.exp(-z[2])), p=np.exp(z[3]), C=np.exp(z[4]))


def unpack(z, T):
    b = [z[i * T:(i + 1) * T] for i in range(7)]
    kg, ks = z[7 * T:8 * T + 1], z[8 * T + 1:9 * T + 2]
    return (*b, kg, ks)                              # C, p, l, ig, is, qg, qs, kg, ks


def residuals(z, Ag, As, k0, T):
    C, p, l, ig, is_, qg, qs, kg, ks = unpack(z, T)
    ss = steady(Ag[-1], As[-1])
    yg, ys = Ag * kg[:-1] ** AG * l ** (1 - AG), As * ks[:-1] ** AS * (1 - l) ** (1 - AS)
    P, cg, cs = prices(C, p)
    adj = PHI / 2 * ((ig / kg[:-1] - DELTA) ** 2 * kg[:-1] + (is_ / ks[:-1] - DELTA) ** 2 * ks[:-1])
    r = [[kg[0] - k0[0], ks[0] - k0[1]],
         (1 - AG) * yg / l - p * (1 - AS) * ys / (1 - l),
         cg + ig + is_ + adj - yg, cs - ys,
         qg - (1 + PHI * (ig / kg[:-1] - DELTA)), qs - (1 + PHI * (is_ / ks[:-1] - DELTA)),
         kg[1:] - ((1 - DELTA) * kg[:-1] + ig), ks[1:] - ((1 - DELTA) * ks[:-1] + is_)]
    m = BETA * (C[1:] / C[:-1]) ** (-SIGMA) * (P[:-1] / P[1:])
    xg, xs = ig[1:] / kg[1:-1], is_[1:] / ks[1:-1]
    rg, rs = AG * yg[1:] / kg[1:-1], p[1:] * AS * ys[1:] / ks[1:-1]
    r += [qg[:-1] - m * (rg + qg[1:] * (1 - DELTA) + PHI / 2 * (xg ** 2 - DELTA ** 2)),
          qs[:-1] - m * (rs + qs[1:] * (1 - DELTA) + PHI / 2 * (xs ** 2 - DELTA ** 2)),
          [kg[-1] - ss["kg"], ks[-1] - ss["ks"]]]
    return np.concatenate([np.atleast_1d(x) for x in r])


def solve(Ag, As, k0, tol=1e-10):
    T = len(Ag)
    s0, s1 = steady(Ag[0], As[0]), steady(Ag[-1], As[-1])
    lin = lambda a, b, n: np.linspace(a, b, n)
    z = np.concatenate([lin(s0["C"], s1["C"], T), lin(s0["p"], s1["p"], T), lin(s0["l"], s1["l"], T),
                        DELTA * lin(k0[0], s1["kg"], T), DELTA * lin(k0[1], s1["ks"], T), np.ones(T), np.ones(T),
                        lin(k0[0], s1["kg"], T + 1), lin(k0[1], s1["ks"], T + 1)])
    for it in range(60):
        f0 = residuals(z, Ag, As, k0, T)
        err = np.abs(f0).max()
        if err < tol:
            return unpack(z, T), it, err
        J = np.empty((len(f0), len(z)))
        for j in range(len(z)):
            h = 1e-7 * max(1.0, abs(z[j])); zp = z.copy(); zp[j] += h
            J[:, j] = (residuals(zp, Ag, As, k0, T) - f0) / h
        J[np.abs(J) < 1e-14] = 0.0
        step = spsolve(sp.csc_matrix(J), -f0)
        t_ = 1.0
        while t_ > 1e-4 and np.abs(residuals(z + t_ * step, Ag, As, k0, T)).max() >= err:
            t_ /= 2
        z = z + t_ * step
    raise RuntimeError(f"no convergence ({err:.2e})")


def main():
    T = 80
    s0 = steady(1.0, 1.0)
    k0 = (s0["kg"], s0["ks"])
    (C, p, l, ig, is_, qg, qs, kg, ks), it, err = solve(np.ones(T), np.ones(T), k0)
    print(f"(a) no shock: max |kg - kg*| {np.abs(kg - s0['kg']).max():.1e}, max |p - p*| {np.abs(p - s0['p']).max():.1e} ({it} steps)")
    s1 = steady(1.1, 1.0)
    (C, p, l, ig, is_, qg, qs, kg, ks), it, err = solve(np.full(T, 1.1), np.ones(T), k0)
    print(f"(b) goods productivity +10%: after 50 years kg {kg[50]:.4f} (new steady state {s1['kg']:.4f}), ks {ks[50]:.4f} "
          f"({s1['ks']:.4f}), p {p[50]:.4f} ({s1['p']:.4f}); {it} Newton steps")
    print(f"(c) relative price of services: {s0['p']:.4f} -> {s1['p']:.4f} in the steady state "
          f"({'rises' if s1['p'] > s0['p'] else 'falls'}, as goods get cheaper to make)")
    Ag = np.ones(T); Ag[5:] = 1.1
    (C2, p2, l2, ig2, is2, *_), it, err = solve(Ag, np.ones(T), k0)
    print(f"(d) announced +10% goods productivity from year 5: services investment in years 0-4 vs steady state (%): "
          f"{', '.join(f'{(x / (DELTA * k0[1]) - 1) * 100:+.2f}' for x in is2[:5])}; consumption bundle year 0 "
          f"{(C2[0] / s0['C'] - 1) * 100:+.2f}%")


if __name__ == "__main__":
    main()
