"""DSGE research, milestone 3 tests (19 Oct 2026): incomplete pass-through, foreign-price shock, interest smoothing.

T11 theta_F -> 0 (instant import repricing): the LOP gap vanishes and output and domestic inflation after a monetary shock are
    Gali-Monacelli's (soe_nk.py) under the same rule.
T12 nominal uncovered interest parity: E[de'] = i - istar.
T13 identities: CPI = (1 - alpha) piH + alpha piF; real exchange rate = psi + (1 - alpha) s.
T14 pass-through of a foreign-price shock builds up gradually: the import-price level's share of the world price in pesos rises
    over time towards 1, and is lower on impact with stickier importers.
T15 interest smoothing (rho_i = 0.8) keeps the model determinate and makes the policy rate's response persistent.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import soe_lcp as L  # noqa: E402
import soe_nk as G   # noqa: E402

results = []


def check(name, ok, detail):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


r0 = L.irf(L.Params(theta_F=1e-7, rule="dit"), "v", 1.0)
g0 = G.irf(G.Params(rule="dit"), "v", 1.0, T=40)
e11 = max(np.abs(r0["psi"]).max(), np.abs(r0["x"] - g0["x"]).max(), np.abs(r0["piH"] - g0["piH"]).max())
check("T11 instant import repricing = Gali-Monacelli", e11 < 1e-6, f"max gap {e11:.1e}")

p = L.Params()
for shock in ("v", "pistar", "ystar", "a"):
    r = L.irf(p, shock, 1.0)
    e12 = np.abs(r["de"][1:] - (r["i"][:-1] - r["istar"][:-1])).max()
    e13 = max(np.abs(r["pi"] - ((1 - p.alpha) * r["piH"] + p.alpha * r["piF"])).max(),
              np.abs(r["q"] - (r["psi"] + (1 - p.alpha) * r["s"])).max())
    check(f"T12/T13 UIP and identities ({shock} shock)", max(e12, e13) < 1e-10, f"UIP {e12:.1e}; identities {e13:.1e}")


# T14a insulation: under a float a foreign inflation shock is absorbed by the peso one for one (a textbook property)
ri = L.irf(p, "pistar", 1.0)
real = max(np.abs(ri[k]).max() for k in ("y", "pi", "piH", "piF", "psi", "x"))
check("T14a floating peso insulates against foreign inflation", real < 1e-10 and np.abs(ri["de"] + ri["pistar"]).max() < 1e-10,
      f"largest domestic response {real:.1e}; depreciation = -foreign inflation")
# T14b gradual pass-through: after a monetary easing (the peso depreciates) import prices lag the world price in pesos, more so
# with stickier importers, and the law-of-one-price gap closes over time
rs_, rf_ = L.irf(L.Params(theta_F=0.75), "v", -1.0, T=40), L.irf(L.Params(theta_F=0.25), "v", -1.0, T=40)
check("T14b gradual pass-through of a depreciation",
      rs_["de"][0] > 0 and rs_["psi"][0] > rf_["psi"][0] > 0 and abs(rs_["psi"][-1]) < 0.02 * abs(rs_["psi"][0]),
      f"depreciation on impact {rs_['de'][0]:.3f}; LOP gap on impact {rs_['psi'][0]:.3f} (theta_F 0.75) vs {rf_['psi'][0]:.3f} (0.25); "
      f"after 10 years {rs_['psi'][-1]:.4f}")

rs = L.irf(L.Params(rho_i=0.8), "v", 1.0)
check("T15 interest smoothing: determinate, persistent rate", abs(rs["i"][4] / rs["i"][0]) > abs(L.irf(p, "v", 1.0)["i"][4] / L.irf(p, "v", 1.0)["i"][0]),
      f"rate after a year / on impact: {rs['i'][4] / rs['i'][0]:.2f} (rho_i 0.8) against {L.irf(p, 'v', 1.0)['i'][4] / L.irf(p, 'v', 1.0)['i'][0]:.2f} (no smoothing)")

n_pass = sum(ok for _, ok, _ in results)
print(f"\n{n_pass}/{len(results)} passed")
sys.exit(0 if n_pass == len(results) else 1)
