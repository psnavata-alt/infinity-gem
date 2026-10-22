"""DSGE research, milestone 2 tests (19 Oct 2026): the Gali-Monacelli small open economy.

T6  Isomorphism (Gali-Monacelli 2005): under a domestic-inflation rule, output gap and domestic inflation after a monetary shock
    equal the closed-economy closed form with sigma -> sigma_alpha and kappa -> lambda (sigma_alpha + phi).
T7  Uncovered interest parity holds in the solution: E[nominal depreciation next quarter] = i (world rate 0).
T8  Terms of trade = sigma_alpha * (y - ystar), and CPI inflation = domestic inflation + alpha * change in the terms of trade.
T9  A closed economy (alpha = 0) is Gali's closed model (T1 form with kappa = lambda (sigma + phi)).
T10 Productivity shock under strict domestic inflation targeting (phi_pi very large): output gap and domestic inflation about 0
    (the "divine coincidence" of the GM model) while output follows its natural level.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import soe_nk as M  # noqa: E402

results = []


def check(name, ok, detail):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def closed_form(sig, kap, p):
    Lam = 1 / ((1 - p.beta * p.rho_v) * (sig * (1 - p.rho_v) + p.phi_x) + kap * (p.phi_pi - p.rho_v))
    return -(1 - p.beta * p.rho_v) * Lam, -kap * Lam


p = M.Params()
r = M.irf(p, "v", 1.0, T=30)
x0, pi0 = closed_form(p.derived["sigma_a"], p.derived["kappa_a"], p)
e6 = max(abs(r["x"][0] - x0), abs(r["piH"][0] - pi0))
check("T6 GM isomorphism (monetary shock)", e6 < 1e-12,
      f"sigma_a {p.derived['sigma_a']:.4f}; x {r['x'][0]:.6f} (closed form {x0:.6f}), piH {r['piH'][0]:.6f}; error {e6:.1e}")

e7 = np.abs(r["de"][1:] - r["i"][:-1]).max()           # deterministic IRF: E[de_{t+1}] = de_{t+1}
check("T7 uncovered interest parity", e7 < 1e-10, f"max |de(t+1) - i(t)| {e7:.1e}")

e8a = np.abs(r["s"] - p.derived["sigma_a"] * (r["y"] - r["ystar"])).max()
e8b = np.abs(r["pi"] - (r["piH"] + p.alpha * (r["s"] - np.concatenate([[0.0], r["s"][:-1]])))).max()
check("T8 terms of trade and CPI identities", max(e8a, e8b) < 1e-10, f"{e8a:.1e}, {e8b:.1e}")

pc = M.Params(alpha=0.0)
rc = M.irf(pc, "v", 1.0)
x0c, pi0c = closed_form(pc.sigma, pc.derived["lam"] * (pc.sigma + pc.phi), pc)
e9 = max(abs(rc["y"][0] - x0c), abs(rc["piH"][0] - pi0c))
check("T9 alpha = 0 is the closed economy", e9 < 1e-12, f"error {e9:.1e}")

ps = M.Params(phi_pi=1e6)
ra = M.irf(ps, "a", 1.0)
gap = max(np.abs(ra["x"]).max(), np.abs(ra["piH"]).max())
yn = ps.derived["Gamma_a"] * ra["a"]
check("T10 strict domestic inflation targeting closes the gap after a productivity shock", gap < 1e-5 and np.abs(ra["y"] - yn).max() < 1e-5,
      f"max |x|, |piH| {gap:.1e}; output = natural output (Gamma_a {ps.derived['Gamma_a']:.4f})")

n_pass = sum(ok for _, ok, _ in results)
print(f"\n{n_pass}/{len(results)} passed")
sys.exit(0 if n_pass == len(results) else 1)
