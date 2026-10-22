"""DSGE research, milestone 1 tests (19 Oct 2026): the QZ solver against exact benchmarks.

T1  Gali's three-equation New Keynesian model, monetary shock: QZ = closed form (Gali 2015, ch. 3, eq. 3.21-3.22 analogues).
T2  Gali's model, natural-rate (demand) shock: QZ = closed form.
T3  Brock-Mirman growth model (log utility, full depreciation), through the numerical linearizer: policy k' = alpha*k + a
    (log deviations) and c = alpha*k + a, the exact log-linear form of the closed-form policy k' = alpha*beta*A*k^alpha.
T4  Blanchard-Kahn: a passive central bank (phi_pi < 1) is indeterminate and is refused; an explosive system is refused.
T5  Impulse responses: the IRF of T1 decays at rho_v and the interest rate rises on impact (the textbook signs).
Gali, J. (2015). Monetary Policy, Inflation, and the Business Cycle, 2nd ed. Princeton University Press.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import klein  # noqa: E402

sigma, beta, kappa, phi_pi, phi_x = 1.0, 0.99, 0.1275, 1.5, 0.125     # Gali (2015) ch. 3 calibration (kappa from theta = 2/3)
results = []


def check(name, ok, detail):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def nk(rho, which, phi_pi_=phi_pi):
    """State [z; x, pi]: z = monetary shock v (which='v') or natural-rate shock r^n (which='r')."""
    s = 1 if which == "v" else -1                       # v enters the Taylor rule; r^n enters the IS curve with the other sign
    A = np.array([[1, 0, 0], [0, 1, 1 / sigma], [0, 0, beta]], float)
    B = np.array([[rho, 0, 0],
                  [s / sigma, 1 + phi_x / sigma, phi_pi_ / sigma],
                  [0, -kappa, 1]], float)
    return A, B


# T1 monetary shock
rho_v = 0.5
sol = klein.solve(*nk(rho_v, "v"), n_k=1)
Lam = 1 / ((1 - beta * rho_v) * (sigma * (1 - rho_v) + phi_x) + kappa * (phi_pi - rho_v))
exact = np.array([-(1 - beta * rho_v) * Lam, -kappa * Lam])
err = np.abs(sol.F[:, 0] - exact).max()
check("T1 NK monetary shock = closed form", err < 1e-12, f"x {sol.F[0, 0]:.6f} (exact {exact[0]:.6f}), pi {sol.F[1, 0]:.6f}; max error {err:.1e}")

# T2 natural-rate shock: x = (1 - beta rho) Lam_r r^n / sigma-scaled; closed form with the same Lambda at rho_r
rho_r = 0.8
sol_r = klein.solve(*nk(rho_r, "r"), n_k=1)
Lr = 1 / ((1 - beta * rho_r) * (sigma * (1 - rho_r) + phi_x) + kappa * (phi_pi - rho_r))
exact_r = np.array([(1 - beta * rho_r) * Lr, kappa * Lr])
err_r = np.abs(sol_r.F[:, 0] - exact_r).max()
check("T2 NK natural-rate shock = closed form", err_r < 1e-12, f"x {sol_r.F[0, 0]:.6f}, pi {sol_r.F[1, 0]:.6f}; max error {err_r:.1e}")

# T3 Brock-Mirman through the numerical linearizer; x = [k, a; c], all in logs except a (already log TFP)
alpha, b_, rho_a = 0.36, 0.96, 0.9
kss = (alpha * b_) ** (1 / (1 - alpha))
css = kss ** alpha - kss


def bm(xp, x):
    kp, ap, cp = xp
    k, a, c = x
    return [kp - (np.exp(a) * k ** alpha - c),                          # resource constraint (full depreciation)
            1 / c - b_ * alpha * np.exp(ap) * kp ** (alpha - 1) / cp,   # Euler equation
            ap - rho_a * a]                                              # TFP
A3, B3 = klein.linearize(bm, np.array([kss, 0.0, css]), log=np.array([True, False, True]))
s3 = klein.solve(A3, B3, n_k=2)
e3 = max(abs(s3.P[0, 0] - alpha), abs(s3.P[0, 1] - 1), abs(s3.F[0, 0] - alpha), abs(s3.F[0, 1] - 1))
check("T3 Brock-Mirman: linearizer + QZ = exact policy", e3 < 1e-6,
      f"k' = {s3.P[0, 0]:.8f} k + {s3.P[0, 1]:.8f} a (exact {alpha}, 1); c = {s3.F[0, 0]:.8f} k + {s3.F[0, 1]:.8f} a; max error {e3:.1e}")

# T4 Blanchard-Kahn refusals
try:
    klein.solve(*nk(rho_v, "v", phi_pi_=0.8), n_k=1)
    check("T4a passive central bank refused (indeterminate)", False, "no error raised")
except klein.BlanchardKahnError as e:
    check("T4a passive central bank refused (indeterminate)", True, str(e))
try:
    klein.solve(np.eye(2), np.diag([0.5, 0.9]), n_k=1)     # two stable roots, one predetermined: indeterminate
    check("T4b wrong root count refused", False, "no error raised")
except klein.BlanchardKahnError as e:
    check("T4b wrong root count refused", True, str(e))

# T5 IRF signs and decay
R = np.array([[1.0]])
k, d = sol.irf(R, np.array([0.25]), T=12)
i_rate = phi_pi * d[:, 1] + phi_x * d[:, 0] + k[:, 0]
decay = np.allclose(d[1:, 0] / d[:-1, 0], rho_v)
check("T5 IRF: output and inflation fall, the rate rises, decay at rho_v",
      d[0, 0] < 0 and d[0, 1] < 0 and i_rate[0] > 0 and decay,
      f"impact x {d[0, 0]:.4f}, pi {d[0, 1]:.4f}, i {i_rate[0]:.4f}; ratio {d[1, 0] / d[0, 0]:.4f}")

n_pass = sum(ok for _, ok, _ in results)
print(f"\n{n_pass}/{len(results)} passed")
sys.exit(0 if n_pass == len(results) else 1)
