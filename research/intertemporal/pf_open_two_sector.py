"""The forward-looking CGE (Stage 2), step 3a (17 Oct 2026): the two-sector forward-looking model with a TRADE BLOCK (small open economy).

Extends pf_two_sector.py (step 2, a closed economy) with the trade equations of a standard CGE (as in Infinity GEM's static
model and the IFPRI standard model: Lofgren, Harris and Robinson 2002), and moves to the general stacked solver
(pf_solver.py, Dynare's method).

Goods g are traded, services s are not. World prices are given (small open economy); the numeraire is foreign currency
(exchange rate 1), so pm = pwm and pe = pwe, and the real exchange rate is the inverse of the consumer price index P.
  Production   X = A_g kg[t-1]^ag l^(1-ag) (goods);  ys = A_s ks[t-1]^as (1-l)^(1-as) (services); labour 1, mobile
  CET          X splits into domestic sales D and exports E (elasticity OMEGA):
               px = [thD pd^(1+OMEGA) + thE pe^(1+OMEGA)]^(1/(1+OMEGA)),  D = thD X (pd/px)^OMEGA,  E = thE X (pe/px)^OMEGA
  Armington    the goods composite Q combines D and imports M (elasticity SIGA):
               pq = [alD pd^(1-SIGA) + alM pm^(1-SIGA)]^(1/(1-SIGA)),  D = alD Q (pd/pq)^-SIGA,  M = alM Q (pm/pq)^-SIGA
  Household    CES bundle C of goods composite and services (weight W, elasticity E); price index P
  Markets      Q = cg + ig + is + adjustment costs (the composite is also the capital good);  cs = ys
  Wage         px (1-ag) X / l = ps (1-as) ys / (1-l)
  Investment   q_j = pq (1 + PHI (i_j/k_j[t-1] - DELTA));  Euler for capital as in step 2, valued at pq
  Foreign      b[t] = (1 + r(b[t-1])) b[t-1] + pe E - pm M   (current account; b = net foreign assets, foreign currency)
               1 = m[t+1] (1 + r(b[t])),  m[t+1] = BETA (C[t+1]/C[t])^-SIGMA P[t]/P[t+1]
               r(b) = RSTAR - PSI (exp(b - BBAR) - 1),  RSTAR = 1/BETA - 1
  The debt-elastic interest rate closes the model (Schmitt-Grohe and Uribe 2003, J. International Economics 61: 163-185,
  their "model 1"): with a world rate equal to the rate of time preference alone, a small open economy's foreign assets
  have a unit root and no unique steady state. PSI is small; test (g) shows the short-run results barely depend on it.
Unknowns per period (11): C, ps, l, pd, ig, is, qg, qs, kg, ks, b (k and b at the END of the period, Dynare's timing).
Exogenous (4): A_g, A_s, pwm, pwe.

Tests (run this file):
  (a) no shock from the steady state stays there;
  (b) permanent +10% goods productivity converges to the new steady state computed separately;
  (c) the household budget, NOT one of the model's equations, holds every period (Walras' law), and GDP by expenditure
      equals GDP by income;
  (d) an announced productivity rise changes behaviour before it happens;
  (e) a temporary 20% rise in the world price of imports for three years (an oil-price episode): the economy borrows
      abroad to smooth consumption (current-account deficit), then repays, and foreign assets return to their starting
      level (the textbook intertemporal current account: Obstfeld and Rogoff 1996, ch. 1-2);
  (f) a permanent 20% rise in the world import price converges to the separately computed new steady state;
  (g) the closing device: results for PSI 0.02 and 0.005 are close in the first years (Schmitt-Grohe and Uribe's finding).
NOT part of Infinity GEM; research code. Run:  py research/intertemporal/pf_open_two_sector.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.optimize import fsolve

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pf_solver  # noqa: E402

NAMES = ["C", "ps", "l", "pd", "ig", "is", "qg", "qs", "kg", "ks", "b"]
EXO = ["Ag", "As", "pwm", "pwe"]


class OpenTwoSector:
    n_y, n_x, names = len(NAMES), len(EXO), NAMES

    def __init__(self, ag=0.40, as_=0.30, beta=0.96, delta=0.05, sigma=2.0, w=0.5, e=0.8, phi=8.0,
                 siga=2.0, omega=2.0, alM=0.30, thE=0.30, psi=0.02, bbar=0.0):
        self.ag, self.as_, self.beta, self.delta, self.sigma, self.w, self.e, self.phi = ag, as_, beta, delta, sigma, w, e, phi
        self.siga, self.omega, self.alM, self.alD, self.thE, self.thD = siga, omega, alM, 1 - alM, thE, 1 - thE
        self.psi, self.bbar, self.rstar = psi, bbar, 1 / beta - 1

    # ---- the static (within-period) block: everything that follows from this period's prices and last period's stocks
    def static(self, C, ps, l, pd, kg_lag, ks_lag, Ag, As, pwm, pwe):
        X = Ag * kg_lag ** self.ag * l ** (1 - self.ag)
        ys = As * ks_lag ** self.as_ * (1 - l) ** (1 - self.as_)
        pe, pm = pwe, pwm
        px = (self.thD * pd ** (1 + self.omega) + self.thE * pe ** (1 + self.omega)) ** (1 / (1 + self.omega))
        D = self.thD * X * (pd / px) ** self.omega
        E = self.thE * X * (pe / px) ** self.omega
        pq = (self.alD * pd ** (1 - self.siga) + self.alM * pm ** (1 - self.siga)) ** (1 / (1 - self.siga))
        Q = D / (self.alD * (pd / pq) ** (-self.siga))
        M = self.alM * Q * (pm / pq) ** (-self.siga)
        P = (self.w * pq ** (1 - self.e) + (1 - self.w) * ps ** (1 - self.e)) ** (1 / (1 - self.e))
        cg = self.w * (pq / P) ** (-self.e) * C
        cs = (1 - self.w) * (ps / P) ** (-self.e) * C
        rk_g = px * self.ag * X / kg_lag
        rk_s = ps * self.as_ * ys / ks_lag
        wage = px * (1 - self.ag) * X / l
        return dict(X=X, ys=ys, pe=pe, pm=pm, px=px, D=D, E=E, pq=pq, Q=Q, M=M, P=P, cg=cg, cs=cs,
                    rk_g=rk_g, rk_s=rk_s, wage=wage)

    def r(self, b):
        return self.rstar - self.psi * (np.exp(b - self.bbar) - 1)

    def resid(self, ylag, y, ylead, x, xlead):
        C, ps, l, pd, ig, is_, qg, qs, kg, ks, b = y
        kgL, ksL, bL = ylag[8], ylag[9], ylag[10]
        s = self.static(C, ps, l, pd, kgL, ksL, *x)
        Cn, psn, ln, pdn, ign, isn, qgn, qsn = ylead[:8]
        sn = self.static(Cn, psn, ln, pdn, kg, ks, *xlead)   # next period uses this period's end-of-period capital
        d, phi = self.delta, self.phi
        xg, xs = ig / kgL, is_ / ksL
        adj = phi / 2 * ((xg - d) ** 2 * kgL + (xs - d) ** 2 * ksL)
        m = self.beta * (Cn / C) ** (-self.sigma) * s["P"] / sn["P"]
        xgn, xsn = ign / kg, isn / ks
        return np.array([
            s["px"] * (1 - self.ag) * s["X"] / l - ps * (1 - self.as_) * s["ys"] / (1 - l),      # wage equalised
            s["Q"] - (s["cg"] + ig + is_ + adj),                                              # goods composite market
            s["cs"] - s["ys"],                                                                # services market
            qg - s["pq"] * (1 + phi * (xg - d)),                                              # Tobin's q, goods sector
            qs - s["pq"] * (1 + phi * (xs - d)),                                              # Tobin's q, services
            kg - ((1 - d) * kgL + ig),                                                        # capital accumulation
            ks - ((1 - d) * ksL + is_),
            b - ((1 + self.r(bL)) * bL + s["pe"] * s["E"] - s["pm"] * s["M"]),                # current account
            1 - m * (1 + self.r(b)),                                                          # bond Euler equation
            qg - m * (sn["rk_g"] + qgn * (1 - d) + sn["pq"] * phi / 2 * (xgn ** 2 - d ** 2)),   # capital Euler, goods
            qs - m * (sn["rk_s"] + qsn * (1 - d) + sn["pq"] * phi / 2 * (xsn ** 2 - d ** 2)),   # capital Euler, services
        ])

    # ---- steady state, solved on its own (not by the stacked solver): the check for tests (b) and (f)
    def steady(self, Ag=1.0, As=1.0, pwm=1.0, pwe=1.0):
        R = 1 / self.beta - 1 + self.delta

        def f(z):
            kg, ks, pd, ps, C = (np.exp(v) for v in (z[0], z[1], z[3], z[4], z[5]))
            l = 1 / (1 + np.exp(-z[2]))
            s = self.static(C, ps, l, pd, kg, ks, Ag, As, pwm, pwe)
            return [s["rk_g"] - s["pq"] * R, s["rk_s"] - s["pq"] * R,
                    s["px"] * (1 - self.ag) * s["X"] / l - ps * (1 - self.as_) * s["ys"] / (1 - l),
                    s["Q"] - (s["cg"] + self.delta * (kg + ks)), s["cs"] - s["ys"],
                    self.rstar * self.bbar + s["pe"] * s["E"] - s["pm"] * s["M"]]
        z, info, ier, msg = fsolve(f, [np.log(3.0), np.log(2.0), 0.0, 0.0, 0.0, 0.0], xtol=1e-14, full_output=True)
        res = np.abs(f(z)).max()
        if res > 1e-10:                     # judged by the residual (fsolve reports xtol warnings at machine precision)
            raise RuntimeError(f"steady state not found: {msg} (residual {res:.1e})")
        kg, ks, pd, ps, C = (np.exp(v) for v in (z[0], z[1], z[3], z[4], z[5]))
        l = 1 / (1 + np.exp(-z[2]))
        pq = self.static(C, ps, l, pd, kg, ks, Ag, As, pwm, pwe)["pq"]
        return np.array([C, ps, l, pd, self.delta * kg, self.delta * ks, pq, pq, kg, ks, self.bbar])

    def run(self, X, ss_start=None, verbose=False):
        """Solve from the steady state of the first period's exogenous values (or ss_start) to that of the last."""
        T = X.shape[1] - 1
        y0 = self.steady(*X[:, 0]) if ss_start is None else ss_start
        yT = self.steady(*X[:, -1])
        guess = y0[:, None] + (yT - y0)[:, None] * np.linspace(0, 1, T)[None, :]
        Y, info = pf_solver.solve(self, y0, yT, X, guess, verbose=verbose)
        return Y, y0, yT, info

    def accounts(self, Y, y0, X):
        """Household budget and GDP identities per period (none of them is one of the model's equations)."""
        lag = np.column_stack([y0, Y[:, :-1]])
        C, ps, l, pd, ig, is_, qg, qs, kg, ks, b = Y
        s = self.static(C, ps, l, pd, lag[8], lag[9], *X[:, :-1])
        d = self.delta
        adj = self.phi / 2 * ((ig / lag[8] - d) ** 2 * lag[8] + (is_ / lag[9] - d) ** 2 * lag[9])
        income = s["wage"] * 1.0 + s["rk_g"] * lag[8] + s["rk_s"] * lag[9] + self.r(lag[10]) * lag[10]
        spending = s["P"] * C + s["pq"] * (ig + is_ + adj) + (b - lag[10])
        gdp_exp = s["P"] * C + s["pq"] * (ig + is_ + adj) + s["pe"] * s["E"] - s["pm"] * s["M"]
        gdp_inc = s["wage"] + s["rk_g"] * lag[8] + s["rk_s"] * lag[9]
        return dict(budget_gap=np.abs(income - spending).max(), gdp_gap=np.abs(gdp_exp - gdp_inc).max(), s=s)


def exo(T, Ag=1.0, As=1.0, pwm=1.0, pwe=1.0):
    X = np.ones((4, T + 1))
    X[0], X[1], X[2], X[3] = Ag, As, pwm, pwe
    return X


def main():
    T = 150
    m = OpenTwoSector()
    ss = m.steady()
    print(f"Steady state: C {ss[0]:.4f}, ps {ss[1]:.4f}, l {ss[2]:.4f}, pd {ss[3]:.4f}, kg {ss[8]:.4f}, ks {ss[9]:.4f}, b {ss[10]:.4f}")
    results = {}

    X = exo(T)
    Y, y0, yT, info = m.run(X)
    dev = np.abs(Y - ss[:, None]).max()
    results["a"] = dev < 1e-9
    print(f"(a) no shock: max deviation from the steady state {dev:.1e} ({info['iterations']} Newton steps) -> {'PASS' if results['a'] else 'FAIL'}")

    # gaps are relative to max(|value|, 1): foreign assets are 0 in the steady state, and output is about 3
    def gap(y, s):
        return float(np.abs((y - s) / np.maximum(np.abs(s), 1.0)).max())

    X = exo(T, Ag=1.1)
    Y, y0, yT, info = m.run(X, ss_start=ss)
    s1 = m.steady(Ag=1.1)
    g20, g50, g100 = (gap(Y[:, t], s1) for t in (19, 49, 99))
    results["b"] = g100 < 1e-2 and g100 < g50 < g20
    print(f"(b) goods productivity +10% (permanent): largest gap to the separately solved new steady state after 20 / 50 / "
          f"100 years {g20 * 100:.2f}% / {g50 * 100:.2f}% / {g100 * 100:.3f}% (kg {Y[8, 99]:.4f} vs {s1[8]:.4f}; ps "
          f"{Y[1, 99]:.4f} vs {s1[1]:.4f}; b {Y[10, 99]:+.4f}); {info['iterations']} Newton steps, Jacobian nonzeros "
          f"{info['nnz']:,} -> {'PASS' if results['b'] else 'FAIL'}")
    acc = m.accounts(Y, y0, X)
    results["c"] = acc["budget_gap"] < 1e-8 and acc["gdp_gap"] < 1e-8
    print(f"(c) household budget (not imposed) holds every period: max gap {acc['budget_gap']:.1e}; GDP by expenditure = "
          f"by income: max gap {acc['gdp_gap']:.1e} -> {'PASS' if results['c'] else 'FAIL'}")
    Yb = Y.copy()

    Ag = np.ones(T + 1); Ag[5:] = 1.1          # X column 0 is year 1, so index 5 is year 6; known from year 1
    X = exo(T, Ag=Ag)
    Y, y0, yT, info = m.run(X, ss_start=ss)
    early = (Y[0, :5] / ss[0] - 1) * 100
    inv_s = (Y[5, :5] / ss[5] - 1) * 100
    results["d"] = abs(early[0]) > 0.1
    print(f"(d) +10% goods productivity announced in year 1 for year 6: consumption in years 1-5 (%): "
          f"{', '.join(f'{v:+.2f}' for v in early)}; services investment (%): {', '.join(f'{v:+.2f}' for v in inv_s)}; "
          f"foreign assets year 5 {Y[10, 4]:+.4f} -> {'PASS' if results['d'] else 'FAIL'} (behaviour moves before the change)")

    # (e) oil-type episode: imports with few substitutes (Armington elasticity 0.5), so the import bill rises with the price
    mo = OpenTwoSector(siga=0.5)
    so = mo.steady()
    pwm = np.ones(T + 1); pwm[:3] = 1.2         # years 1-3, unexpected in year 1
    X = exo(T, pwm=pwm)
    Y, y0, yT, info = mo.run(X, ss_start=so)
    acc = mo.accounts(Y, y0, X)
    ca = np.diff(np.concatenate([[so[10]], Y[10]]))
    bill = acc["s"]["pm"] * acc["s"]["M"]
    bill0 = mo.static(*so[:4], so[8], so[9], 1, 1, 1, 1)["M"]
    results["e"] = bool((ca[:3] < 0).all() and (ca[3:10] > 0).all() and abs(Y[10, 99]) < 0.1 * abs(Y[10].min())
                        and acc["budget_gap"] < 1e-8)
    print(f"(e) world import price +20% in years 1-3 (import elasticity 0.5): import bill year 1 {(bill[0] / bill0 - 1) * 100:+.1f}%; "
          f"current account years 1-6 {', '.join(f'{v:+.4f}' for v in ca[:6])}; foreign assets lowest {Y[10].min():+.4f} "
          f"(year {Y[10].argmin() + 1}), year 100 {Y[10, 99]:+.5f}; consumption year 1 {(Y[0, 0] / so[0] - 1) * 100:+.2f}%, "
          f"year 4 {(Y[0, 3] / so[0] - 1) * 100:+.2f}% -> {'PASS' if results['e'] else 'FAIL'} (borrow during the episode, then repay)")
    temp = Y.copy()

    X = exo(T, pwm=1.2)
    Y, y0, yT, info = m.run(X, ss_start=ss)
    s2 = m.steady(pwm=1.2)
    g100 = gap(Y[:, 99], s2)
    results["f"] = g100 < 1e-2
    print(f"(f) world import price +20% (permanent): after 100 years the largest gap to the new steady state {g100 * 100:.3f}%; "
          f"long-run consumption {(s2[0] / ss[0] - 1) * 100:+.2f}%, domestic goods price {(s2[3] / ss[3] - 1) * 100:+.2f}% "
          f"-> {'PASS' if results['f'] else 'FAIL'}")

    m2 = OpenTwoSector(siga=0.5, psi=0.005)
    Y2, *_ = m2.run(exo(T, pwm=pwm), ss_start=m2.steady())
    dC = np.abs(Y2[0, :5] / temp[0, :5] - 1).max() * 100
    results["g"] = dC < 0.1
    print(f"(g) closing device: the oil-type episode with PSI 0.005 instead of 0.02: consumption in years 1-5 differs by at "
          f"most {dC:.3f}% -> {'PASS' if results['g'] else 'FAIL'}")

    # (h) truncation: the terminal condition at T must not drive the early years
    T2 = 250
    Yl, *_ = m.run(exo(T2, Ag=1.1), ss_start=ss)
    dh = gap(Yl[:, :50], Yb[:, :50])
    results["h"] = dh < 1e-4
    print(f"(h) horizon 250 instead of 150 years (permanent +10% goods productivity): years 1-50 differ by at most "
          f"{dh * 100:.4f}% -> {'PASS' if results['h'] else 'FAIL'}")

    print(f"\n{sum(results.values())} of {len(results)} tests pass")
    return results


if __name__ == "__main__":
    main()
