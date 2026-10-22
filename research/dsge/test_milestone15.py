"""DSGE research, milestone 15 tests (19 Oct 2026): oil as an imported good and input (soe_oil.py).

T41 reduction: with a_o = s_o = 0, soe_oil = soe_htm for all five earlier shocks.
T42 identities along an oil shock: pi = (1 - a_o) pi_c + a_o pi_o; pi_o = o - o_lag + pistar + de;
    q = (1 - a_o)(psi + (1 - alpha) s) - a_o o; the production side (n, w, mc) consistent.
T43 first and second round: an oil-price rise raises headline inflation on impact (first round, through pi_o) and core
    inflation through marginal cost (second round); with s_o = 0 and no exchange-rate move, core inflation's response is smaller.
T44 headline vs core targeting (Blanchard-Gali trade-off): after an oil-price rise, the policy rate rises less under a core
    rule than under a headline rule, and output falls less (default eps_o 0.2: the shock is stagflationary; with unit
    substitution between core and oil, output rose on impact, which is why eps_o was added).
T45 determinacy over a_o in {0.03, 0.06, 0.10} and s_o in {0.02, 0.05}.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import soe_htm as Hm   # noqa: E402
import soe_oil as Oil  # noqa: E402

results = []


def check(name, ok, detail):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


base = dict(rho_i=0.8, rule="output", phi_x=0.2, hab=0.7, phi_e=0.1, omega_H=0.3, omega_F=0.5, phi_pi=1.6, lam_h=0.4, kappa=0.3)
e41 = 0.0
for s in ("v", "a", "ystar", "pistar", "zeta"):
    r1, r2 = Hm.irf(Hm.Params(**base), s, 0.01), Oil.irf(Oil.Params(**base), s, 0.01)
    e41 = max(e41, max(np.abs(r1[k] - r2[k]).max() for k in ("y", "c", "co", "cr", "pi", "piH", "piF", "i", "q", "de", "mc")))
check("T41 a_o = s_o = 0 is soe_htm", e41 < 1e-12, f"max gap {e41:.1e} over 5 shocks")

p = Oil.Params(**base, a_o=0.06, s_o=0.04)
r = Oil.irf(p, "o", 0.10, T=40)                       # a 10% rise in the real oil price
o_lag = np.concatenate([[0.0], r["o"][:-1]])
e42 = max(float(np.abs(r["pi"] - ((1 - p.a_o) * r["pi_c"] + p.a_o * r["pi_o"])).max()),
          float(np.abs(r["pi_o"] - (r["o"] - o_lag + r["pistar"] + r["de"])).max()),
          float(np.abs(r["q"] - ((1 - p.a_o) * (r["psi"] + (1 - p.alpha) * r["s"]) - p.a_o * r["o"])).max()),
          float(np.abs(r["n"] - (r["mc"] + r["y"] - r["wr"] - r["X"])).max()))
check("T42 oil identities hold along the response", e42 < 1e-12, f"max residual {e42:.1e}")

peak = lambda z: int(np.argmax(np.abs(z)))
check("T43 first round on impact, second round through costs",
      r["pi"][0] > 0 and r["pi_o"][0] > 0 and r["mc"][0] > 0 and max(r["pi_c"][:8]) > 0,
      f"impact: headline {400 * r['pi'][0]:.2f} pp, oil {400 * r['pi_o'][0]:.1f} pp, core {400 * r['pi_c'][0]:.3f} pp annualized; "
      f"core peak q{peak(r['pi_c'])} {400 * max(r['pi_c'][:8]):.3f} pp; marginal cost {100 * r['mc'][0]:.2f}%")

rh = Oil.irf(Oil.Params(**base, a_o=0.06, s_o=0.04, rule_infl="headline"), "o", 0.10, T=24)
rc = Oil.irf(Oil.Params(**base, a_o=0.06, s_o=0.04, rule_infl="core"), "o", 0.10, T=24)
check("T44 a core rule tightens less and costs less output after an oil shock",
      rc["i"][:4].sum() < rh["i"][:4].sum() and rc["y"][:4].sum() > rh["y"][:4].sum(),
      f"first-year rate {100 * rh['i'][:4].mean() * 4:.3f} (headline) vs {100 * rc['i'][:4].mean() * 4:.3f} (core) pp annualized; "
      f"first-year output {100 * rh['y'][:4].mean():.3f}% vs {100 * rc['y'][:4].mean():.3f}%")

bad = []
for ao in (0.03, 0.06, 0.10):
    for so in (0.02, 0.05):
        try:
            Oil.solve(Oil.Params(**base, a_o=ao, s_o=so))
        except Exception as ex:  # noqa: BLE001
            bad.append(f"({ao}, {so}): {type(ex).__name__}")
check("T45 determinate over a_o 0.03-0.10, s_o 0.02-0.05", not bad, "all determinate" if not bad else "; ".join(bad))

n_pass = sum(ok for _, ok, _ in results)
print(f"\n{n_pass}/{len(results)} passed")
sys.exit(0 if n_pass == len(results) else 1)
