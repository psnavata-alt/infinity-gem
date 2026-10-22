"""DSGE research (Stage 3): the posterior distribution of monetary transmission in the candidate DSGE (19 Oct 2026, about 1:45 PM).

For draws from the long chains of milestone 13 (soe_htm, system prior on transmission strength;
outputs/dsge_ph_htm_draws_*_w1_ratio_seed[456].npy by default), solve the model and record:
- transmission strength: CPI y/y and GDP-growth troughs per pp of the first year's cumulative policy-rate path (as in
  estimate_rot.strength), after a policy shock scaled to +0.80 pp on impact;
- the annual inputs of the DSGE-CGE link for a 100 bp tightening (qpm_cge_link.dsge_annual's quantities): output gap, real
  interest-rate gap, real exchange rate and inflation in 2026 and 2027.
Reports the 5th, 50th and 95th percentiles and the posterior mean (the posterior mean of a nonlinear function differs from the
function at the mean of the parameters, which is what the estimation report shows).
Run:  py posterior_strength.py [n_per_chain=300] [pattern=...]   (writes outputs/dsge_posterior_strength_<stamp>.md)
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
if not any(a.startswith("model=") for a in sys.argv):   # 20 Oct 2026: model=htmu (milestone 19) allowed; default htm as before
    sys.argv = sys.argv + ["model=htm"]
import estimate_rot as ER          # noqa: E402  (model=htm: soe_htm, pamph_responses, strength)
import klein                       # noqa: E402
from transmission_benchmarks import HTM_NAMES   # noqa: E402

OUT = HERE.parents[1] / "outputs"


def annual(sol, bp=100.0, years=2):
    ixk = {n: j for j, n in enumerate(ER.R.STATES)}
    ixd = {n: j for j, n in enumerate(ER.R.JUMPS)}
    e = np.zeros(len(ER.R.STATES)); e[ixk["v"]] = 0.001
    k, d = sol.irf(np.eye(len(ER.R.STATES)), e, T=4 * years + 2)
    i_, y_, q_, pi_ = d[:, ixd["i"]], d[:, ixd["y"]], d[:, ixd["q"]], d[:, ixd["pi"]]
    s = (bp / 100.0) / (400 * i_[0])
    out = {}
    for n in range(years):
        sl = slice(4 * n, 4 * n + 4)
        out[f"output gap {2026 + n} (%)"] = s * 100 * y_[sl].mean()
        out[f"real-rate gap {2026 + n} (pp)"] = s * 400 * (i_[sl] - pi_[1:][sl]).mean()
        out[f"real exchange rate {2026 + n} (%)"] = s * 100 * q_[sl].mean()
        out[f"inflation {2026 + n} (pp a year)"] = s * 400 * pi_[sl].mean()
    return out


def main():
    n_per = int(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("n_per_chain=")), 300))
    pattern = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("pattern=")), "dsge_ph_htm_draws_*_w1_ratio_seed[456].npy")
    files = sorted(OUT.glob(pattern))
    rng = np.random.default_rng(0)
    rows = []
    for f in files:
        D = np.load(f)
        for j in rng.choice(len(D), size=min(n_per, len(D)), replace=False):
            kw = {k: v for k, v in zip(ER.NAMES, D[j]) if not k.startswith(("sd_", "me_"))}   # = HTM_NAMES for model=htm;
            # "me_" (22 Oct 2026): obs=inv's measurement error is a likelihood parameter, not a model one
            try:
                # 21 Oct 2026, about 11:05 PM: the calibrated parameters (ER.FIXED) were missing here. For soe_htmk they are the
                # capital share 0.5, investment share 0.24 and depreciation, whose Params defaults are 0, 0 and 0.025: the 9:07 AM
                # run (outputs/dsge_posterior_strength_20261021_0907.md) therefore solved soe_htmk WITHOUT capital at parameters
                # estimated WITH capital, and its "transmission unpinned" finding is void. Models with FIXED = {} (htm, htmu)
                # were unaffected.
                sol, _ = ER.R.solve(ER.R.Params(rule="output", **{**kw, **ER.FIXED}))
                st = ER.strength(ER.pamph_responses(sol))
                rows.append({"CPI strength (trough per pp)": st["infl"], "GDP strength (trough per pp)": st["growth"],
                             **annual(sol)})
            except (klein.BlanchardKahnError, ValueError, np.linalg.LinAlgError, ZeroDivisionError):
                continue
    T = pd.DataFrame(rows)
    q = T.quantile([0.05, 0.5, 0.95]).T
    q.columns = ["5%", "median", "95%"]
    q["mean"] = T.mean()
    inband = float(((T["CPI strength (trough per pp)"] <= -0.22) & (T["CPI strength (trough per pp)"] >= -0.50)).mean())
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    L = [f"# The posterior distribution of monetary transmission in the candidate DSGE ({dt.datetime.now():%d %B %Y, %H:%M})", "",
         f"**NOT FOR CITATION** (research code, `research/dsge/posterior_strength.py`). {len(T)} draws solved from "
         f"{', '.join(f.name for f in files)}. Evidence band for the CPI strength (milestone 12): −0.22 to −0.50; share of "
         f"draws inside it: **{inband:.0%}**. Link inputs are for a 100 bp tightening in 2026Q1.", "",
         q.to_markdown(floatfmt=".3f")]
    path = OUT / f"dsge_posterior_strength_{stamp}.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L)); print("saved", path)


if __name__ == "__main__":
    main()
