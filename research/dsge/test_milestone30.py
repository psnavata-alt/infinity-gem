"""DSGE research, milestone 30 tests (12 Nov 2026): the opt-in oil system prior in estimate_rot.py (oilprior=lp).

T30a the targets written into estimate_rot.OIL_LP equal the local projections recomputed now (milestone28_scratch/oil_lp_targets.py,
     Kanzig's shock vintage 2025M12, 2002Q1-2025Q4 without COVID) to 1e-5 (they are written to six decimals).
T30b estimate_rot.oil_responses is compare_oil_lp.responses (the objects the score of milestone 29 uses), to 1e-12, for soe_htmkwod
     (dcp) at milestone 26's posterior mean with iota_w 0.3 and theta_X 0.75.
T30c opt-in: with oilprior=lp, pieces() has the same log prior and log likelihood, and its system-prior distance is the one without
     PLUS oil_distance (> 0); outputs carry "_inv_oillp"; without it STAG and the distance are as before.
T30d oilprior=lp refuses a model without the oil block (model=htmkw) and a run without a ratio prior (prior=pamph).
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "milestone28_scratch"))

results = []


def check(name, ok, detail):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


import oil_lp_targets  # noqa: E402

now = oil_lp_targets.targets()
src = (HERE / "estimate_rot.py").read_text(encoding="utf-8")
ns = {}
start = src.index("OIL_LP = {")
exec(src[start:src.index("}\n", start) + 1], ns)                # noqa: S102  (the literal dict only)
gap = max(max(abs(now[k][0] - ns["OIL_LP"][k][0]), abs(now[k][1] - ns["OIL_LP"][k][1])) for k in now)
check("T30a OIL_LP equals the local projections recomputed now", set(now) == set(ns["OIL_LP"]) and gap < 1e-5,
      f"10 entries; largest gap {gap:.1e}; GDP y2 {now[('real GDP', 2)][0]:+.3f} ({now[('real GDP', 2)][1]:.3f}), "
      f"policy rate y2 {now[('policy rate', 2)][0]:+.3f} ({now[('policy rate', 2)][1]:.3f})")

code = r"""
import sys, importlib
sys.path.insert(0, '.')
import numpy as np
base = ['x', 'model=htmkwod', 'prior=ratio2', 'sample=long', 'gdp=stl', 'obs=inv']
sys.argv = ['x', 'model=htmkwo', 'prior=ratio2', 'sample=long', 'gdp=stl', 'obs=inv']
import estimate_rot as A
n0 = list(A.NAMES)
X = np.load(sorted((A.HERE.parents[1] / 'outputs').glob('dsge_smc_*_htmkwo_w1_ratio2_long_stl_inv_n*_particles.npy'))[-1])
sys.argv = base
B = importlib.reload(A)
th = np.insert(X.mean(0), n0.index('iota_w') if 'iota_w' in n0 else n0.index('theta_w') + 1, 0.3)
th = np.insert(th, B.NAMES.index('theta_X'), 0.75)
Z = B.observables()
p0 = B.pieces(th, Z)
stag0 = B.STAG
kw, sds = B.split(th)
par = B.R.Params(rule='output', **{**kw, **B.FIXED})
sol, _ = B.R.solve(par)
r1 = B.oil_responses(sol, par)
import compare_oil_lp as C
r2 = C.responses(B.R, par)
g = max(abs(r1[(o, y + 1)] - r2[o][y]) for o in C.OBJ for y in (0, 1))
sys.argv = base + ['oilprior=lp']
B2 = importlib.reload(A)
p1 = B2.pieces(th, Z)
od = B2.oil_distance(sol, par)
print('T30b', f'{g:.1e}', f"{r1[('real GDP', 1)]:+.4f}", f"{r1[('real GDP', 2)]:+.4f}", f"{r1[('policy rate', 2)]:+.4f}")
print('T30c', p0[0] == p1[0], p0[1] == p1[1], abs(p1[3] - (p0[3] + od)) < 1e-9, od > 0, stag0, B2.STAG, f'{od:.3f}',
      f'{p0[3]:.3f}', f'{p1[3]:.3f}')
"""
out = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, cwd=str(HERE))
lines = {ln.split()[0]: ln.split()[1:] for ln in out.stdout.strip().splitlines() if ln.split()}
err = out.stderr.strip()[-400:]
b = lines.get("T30b")
check("T30b estimate_rot.oil_responses = compare_oil_lp.responses (soe_htmkwod, dcp)", b is not None and float(b[0]) < 1e-12,
      f"largest gap {b[0]}; 10% oil supply: GDP y1 {b[1]}%, y2 {b[2]}%, policy rate y2 {b[3]} pp" if b else err or "nothing printed")
c = lines.get("T30c")
check("T30c oilprior=lp: same prior and likelihood; distance = ratio2's + the oil distance; tag _oillp",
      c is not None and c[:4] == ["True"] * 4 and c[4] == "_long_stl_inv" and c[5] == "_long_stl_inv_oillp",
      f"oil distance {c[6]} (ratio2's {c[7]} -> {c[8]}); STAG {c[4]} -> {c[5]}" if c else err or "nothing printed")

refusals = []
for args in (["model=htmkw", "prior=ratio2", "sample=long", "gdp=stl", "obs=inv", "oilprior=lp"],
             ["model=htmkwod", "prior=pamph", "sample=long", "gdp=stl", "obs=inv", "oilprior=lp"]):
    o = subprocess.run([sys.executable, "-I", "-c", f"import sys; sys.path.insert(0, '.'); sys.argv = {['x'] + args!r}; "
                        "import estimate_rot"], capture_output=True, text=True, cwd=str(HERE))
    refusals.append(o.returncode != 0 and "oilprior=lp needs" in o.stderr)
check("T30d oilprior=lp refuses model=htmkw and prior=pamph", all(refusals), f"refused: {refusals}")

n_pass = sum(ok for _, ok, _ in results)
print(f"\ntest_milestone30: {n_pass}/{len(results)} passed")
sys.exit(0 if n_pass == len(results) else 1)
