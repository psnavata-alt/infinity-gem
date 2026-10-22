"""Milestone 23c (21 Oct 2026, night): tests of estimate_rot.py obs=inv (investment growth as a fifth observable of soe_htmk).

T23c-a  the data: dinv exists, is demeaned, missing exactly where GDP growth is (the COVID quarters), s.d. about 4-5% a quarter.
T23c-b  the likelihood with obs=inv at a huge measurement error (s.d. 1,000%) equals the four-observable likelihood plus the
        log density of an uninformative fifth observable (the model's own investment variance is negligible against it):
        checks the H row's place and the measurement-error vector without trusting either. Calls the Kalman filter directly
        (the prior bounds me_inv at 30).
T23c-c  the investment row of H: after a policy shock, H's last row applied to the state path equals 100 x (inv - inv(-1))
        from the IRF.
Run: py test_milestone23c.py
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PRE = r'''
import sys, re, numpy as np
sys.path.insert(0, r"{here}")
sys.argv = ["x", "model=htmk", "prior=ratio2", "sample=long", "gdp=stl"] + {extra}
import estimate_rot as ER, estimate as E0
from pathlib import Path
out = Path(r"{here}").parents[1] / "outputs"
prev = [f for f in sorted(out.glob("dsge_ph_htmk_draws_*_w1_ratio2_long_stl*.npy")) if re.search(r"_w1_ratio2_long_stl(_seed\d+)?$", f.stem)]
med = (np.median(np.vstack([np.load(f) for f in prev]), 0) if prev       # the posterior median if the chains are on file,
       else np.array([e[2] for e in ER.EST if e[0] != "me_inv"]))        # else the prior means (the test needs no outputs)
theta = np.append(med, 3.0) if ER.OBS_INV else med
kw, sds = ER.split(theta)
sol = ER.R.solve(ER.R.Params(rule="output", **{{**kw, **ER.FIXED}}))[0]
Pm, Rm, Q, H = ER.state_space(sol, sds)
nk = len(ER.R.STATES)
'''


def run(extra, body):
    code = PRE.format(here=str(HERE), extra=extra) + "\nprint('RESULT', repr(" + body + "))\n"
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=str(HERE))
    line = [l for l in r.stdout.splitlines() if l.startswith("RESULT")]
    if not line:
        raise SystemExit("subprocess failed:\n" + r.stdout[-2000:] + r.stderr[-3000:])
    return eval(line[0][len("RESULT "):])


ok = True
sys.path.insert(0, str(HERE))
import ph_data as D  # noqa: E402

# T23c-a
df = D.observables_inv(end=D.LONG_END, covid="missing", gdp_sa="stl")
na_same = bool((df["dinv"].isna() == df["dy"].isna()).all())
sd, mean = float(df["dinv"].std()), float(df["dinv"].mean())
t_a = na_same and 3.0 < sd < 6.5 and abs(mean) < 1e-9
print(f"T23c-a data: missing where GDP is {na_same}, s.d. {sd:.2f}, mean {mean:.1e}: {'PASS' if t_a else 'FAIL'}")
ok &= t_a

# T23c-b
BIG = 1000.0
ll4 = run("[]", "float(E0.kalman_loglik(Pm, Rm, Q, H, ER.observables()))")
ll5 = run('["obs=inv"]', f"float(E0.kalman_loglik(Pm, Rm, Q, H, ER.observables(), me=np.r_[np.full(4, 1e-4), {BIG}**2]))")
z = df["dinv"].dropna().to_numpy()
gauss = float(np.sum(-0.5 * (np.log(2 * np.pi * BIG ** 2) + z ** 2 / BIG ** 2)))
gap = (ll5 - ll4) - gauss
t_b = abs(gap) < 0.05
print(f"T23c-b likelihood: ll4 {ll4:.3f}, ll5 {ll5:.3f}, difference {ll5 - ll4:.3f}, Gaussian of dinv at s.d. {BIG:g}: "
      f"{gauss:.3f}, gap {gap:.4f}: {'PASS' if t_b else 'FAIL'}")
ok &= t_b

# T23c-c
body = ("[float(v) for v in (lambda kd: np.array([H[-1, :nk] @ kd[0][t] + H[-1, nk:] @ kd[0][t - 1] for t in range(1, 6)])"
        " - 100 * np.diff(kd[1][:, ER.R.JUMPS.index('inv')]))(sol.irf(np.eye(nk), 0.001 * np.eye(nk)[ER.R.STATES.index('v')], T=6))]")
diffs = run('["obs=inv"]', body)
t_c = max(abs(d) for d in diffs) < 1e-10
print(f"T23c-c H row = 100 x IRF (inv - inv(-1)): largest gap {max(abs(d) for d in diffs):.1e}: {'PASS' if t_c else 'FAIL'}")
ok &= t_c
print("test_milestone23c:", "3/3 passed" if ok else "FAILED")
sys.exit(0 if ok else 1)
