"""DSGE research, milestone 5 tests (19 Oct 2026): the DSGE side of the DSGE-CGE link (link_cge.py).

T18 the realised policy-rate path equals the scenario exactly (the rule's own response included);
T19 a zero scenario gives zero CGE shocks (peso scale 1, no output target);
T20 linearity: a 200 bp scenario gives twice the 100 bp paths;
T21 signs: a tightening lowers output and CPI inflation and appreciates the peso (exr_scale < 1).
Known limit (recorded, not tested): the estimated small model's transmission is too strong (100 bp for a year: output -2.4%,
CPI inflation -16 pp annualized, against about -0.3 to -0.5% and a few tenths in Philippine evidence): habits and inflation
indexation come before the link drives the CGE.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import link_cge as LC  # noqa: E402

results = []


def check(name, ok, detail):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


p100, p200, p0 = LC.scenario_paths("policy", 100, 4), LC.scenario_paths("policy", 200, 4), LC.scenario_paths("policy", 0, 4)
e18 = np.abs(40000 * p100["i"][:4] - 100).max()
check("T18 policy-rate path = scenario", e18 < 1e-9, f"max gap {e18:.1e} bp")
z = LC.annual_shocks(p0)[2026]
check("T19 zero scenario = no CGE shock", abs(z["exr_scale"] - 1) < 1e-15 and abs(z["dsge_output_pct"]) < 1e-15, str(z))
e20 = max(np.abs(p200[k] - 2 * p100[k]).max() for k in ("y", "pi", "q", "i"))
check("T20 linearity", e20 < 1e-12, f"{e20:.1e}")
a = LC.annual_shocks(p100)[2026]
check("T21 signs of a tightening", a["dsge_output_pct"] < 0 and a["dsge_cpi_inflation_pp"] < 0 and a["exr_scale"] < 1,
      f"output {a['dsge_output_pct']:.2f}%, CPI inflation {a['dsge_cpi_inflation_pp']:.1f} pp, peso scale {a['exr_scale']:.4f} (2026)")
n_pass = sum(ok for _, ok, _ in results)
print(f"\n{n_pass}/{len(results)} passed")
sys.exit(0 if n_pass == len(results) else 1)
