"""DSGE research, milestone 23b (21 Oct 2026, about 11:20 PM): the investment semi-elasticity theta implied by soe_htmk,
the candidate DSGE with capital, for the DSGE-CGE link.

Why: the CGE's interest-rate closure and the monetary block move investment by theta % per pp of the real-rate gap. PSA data
alone do not identify theta (investment_lp.py: wide bands), so the link has used 1.9-3.3 (central 2: the QPM held for a year
1.9; soe_htmu matched through the output gap 2.7-3.3; milestone 14's 0.55 as a low case). soe_htmk estimates the investment
block itself (phi_i about 7.1 on three chains), so it implies its own theta.

Definition (as investment_lp.py, so the numbers compare): after a policy shock scaled to +1 pp on impact, theta = minus the
average investment response (%) over a year divided by the average real-rate gap (pp) that year; real rate = policy rate minus
the next quarter's annualized inflation (as posterior_strength.annual). Year 1 is the link's case; the two-year ratio is shown
too. Draws from every converged chain of the specification, solved WITH the calibrated parameters (ER.FIXED: capital share
0.5, investment share 0.24, depreciation 0.025), the omission that voided outputs/dsge_posterior_strength_20261021_0907.md.
Run:  py htmk_theta.py [model=htmki] [n_per_chain=300] [obs=inv] [theta_fix=0.95]   (writes outputs/dsge_<model>_theta_<stamp>[_inv][_thfix..].md;
obs=inv: the chains estimated with PSA investment data, milestone 23c; theta_fix=: the chains with the Calvo parameter
calibrated at that value, 22 Oct 2026)
model=htmkf (milestone 25, 22-23 Oct 2026, night): soe_htmkf, soe_htmki plus the flexible-price share of the CPI.
pattern=<glob in outputs/> (milestone 25): score the files matching the glob instead of the specification's Metropolis chains,
e.g. an SMC run's particles (`pattern=dsge_smc_<stamp>_..._particles.npy`; equal weights after the final resampling); the output
then carries "_smc" (or "_files" for another glob). The columns must be the specification's parameters (ER.NAMES).
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
_ARGS = sys.argv[1:]
INV = "obs=inv" in _ARGS            # the chains estimated WITH investment data (milestone 23c); default: without
THFIX = next((a for a in _ARGS if a.startswith("theta_fix=")), None)   # 22 Oct 2026: chains with the Calvo parameter fixed
MODEL = next((a.split("=", 1)[1] for a in _ARGS if a.startswith("model=")), "htmk")   # 22 Oct 2026: or htmki (milestone 24), htmkf (25)
FILES_GLOB = next((a.split("=", 1)[1] for a in _ARGS if a.startswith("pattern=")), None)   # milestone 25: e.g. SMC particles
sys.argv = ([sys.argv[0], f"model={MODEL}", "prior=ratio2", "sample=long", "gdp=stl"] + (["obs=inv"] if INV else [])
            + ([THFIX] if THFIX else []))
import estimate_rot as ER   # noqa: E402
import klein                # noqa: E402
import re                   # noqa: E402

OUT = HERE.parents[1] / "outputs"
# the chains of exactly one specification: "_w1_ratio2_long_stl" (+ "_inv") and an optional "_seedN"; never a mix
TFTAG = f"_thfix{float(THFIX.split('=', 1)[1]):g}" if THFIX else ""
SPEC = "_w1_ratio2_long_stl" + ("_inv" if INV else "") + TFTAG
PATTERN = f"dsge_ph_{MODEL}_draws_*" + SPEC + "*.npy"


def chain_files():
    if FILES_GLOB:                                            # milestone 25: the files named on the command line (e.g. SMC particles)
        return sorted(OUT.glob(FILES_GLOB))
    return [f for f in sorted(OUT.glob(PATTERN)) if re.search(re.escape(SPEC) + r"(_seed\d+)?$", f.stem)]


def responses(theta_vec, T=13):
    kw, _ = ER.split(theta_vec)
    sol, _ = ER.R.solve(ER.R.Params(rule="output", **{**kw, **ER.FIXED}))
    ixk = {n: j for j, n in enumerate(ER.R.STATES)}
    ixd = {n: j for j, n in enumerate(ER.R.JUMPS)}
    e = np.zeros(len(ER.R.STATES)); e[ixk["v"]] = 0.001
    k, d = sol.irf(np.eye(len(ER.R.STATES)), e, T=T + 1)
    i_, pi_, inv_, y_ = d[:, ixd["i"]], d[:, ixd["pi"]], d[:, ixd["inv"]], d[:, ixd["y"]]
    c_ = d[:, ixd["c"]] if "c" in ixd else None
    s = 1.0 / (400 * i_[0])                                   # +1 pp a year on impact
    rr = 400 * s * (i_[:T] - pi_[1:T + 1])                    # real-rate gap, pp a year
    inv = 100 * s * inv_[:T]                                  # investment, % from baseline
    y = 100 * s * y_[:T]
    out = {}
    for lab, sl in (("year 1", slice(0, 4)), ("year 2", slice(4, 8)), ("two years", slice(0, 8))):
        out[f"theta, {lab}"] = -inv[sl].mean() / rr[sl].mean()
    out["investment, year 1 (%)"] = inv[:4].mean()
    out["investment, year 2 (%)"] = inv[4:8].mean()
    out["real-rate gap, year 1 (pp)"] = rr[:4].mean()
    out["real-rate gap, year 2 (pp)"] = rr[4:8].mean()
    out["output, year 1 (%)"] = y[:4].mean()
    out["investment / output response, year 1"] = inv[:4].mean() / y[:4].mean() if abs(y[:4].mean()) > 1e-9 else np.nan
    if c_ is not None:
        out["consumption, year 1 (%)"] = (100 * s * c_[:T])[:4].mean()
    return out


def main():
    n_per = int(next((a.split("=", 1)[1] for a in _ARGS if a.startswith("n_per_chain=")), 300))
    files = chain_files()
    rng = np.random.default_rng(0)
    rows, fails = [], 0
    for f in files:
        D = np.load(f)
        for j in rng.choice(len(D), size=min(n_per, len(D)), replace=False):
            try:
                rows.append(responses(D[j]))
            except (klein.BlanchardKahnError, ValueError, np.linalg.LinAlgError, ZeroDivisionError):
                fails += 1
    T = pd.DataFrame(rows)
    q = T.quantile([0.05, 0.5, 0.95]).T
    q.columns = ["5%", "median", "95%"]
    q["mean"] = T.mean()
    med = np.median(np.vstack([np.load(f) for f in files]), 0)
    at_med = responses(med)
    q["at the parameters' median"] = pd.Series(at_med)
    th1 = T["theta, year 1"]
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    L = [f"# The investment semi-elasticity theta implied by soe_{MODEL} ({dt.datetime.now():%d %B %Y, %H:%M})", "",
         f"**NOT FOR CITATION** (research code, `research/dsge/htmk_theta.py`). {len(T)} posterior draws solved ({fails} failed) "
         f"from {', '.join(f.name for f in files)}, with the calibrated capital share 0.5, investment share 0.24 and depreciation "
         f"0.025. A policy shock scaled to +1 pp on impact; theta = minus the year's average investment response (%) over the "
         f"year's average real-rate gap (pp), the definition of `investment_lp.py`.", "",
         q.to_markdown(floatfmt=".3f"), "",
         f"Share of draws with year-1 theta inside the link's range 1.9-3.3: **{((th1 >= 1.9) & (th1 <= 3.3)).mean():.0%}**; "
         f"below 1.9: {(th1 < 1.9).mean():.0%}; above 3.3: {(th1 > 3.3).mean():.0%}.", "",
         "For comparison (the link's values so far, `investment_lp.py` docstring and `research/dsge/README.md`): milestone 14's "
         "0.55; the QPM, rate held for a year, 1.9; soe_htmu matched through the output gap, 2.7-3.3; central 2.",
         ]
    src = ("_smc" if "dsge_smc_" in FILES_GLOB else "_files") if FILES_GLOB else ""     # milestone 25: pattern= runs
    path = OUT / f"dsge_{MODEL}_theta_{stamp}{'_inv' if INV else ''}{TFTAG}{src}.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L)); print("saved", path)


if __name__ == "__main__":
    main()
