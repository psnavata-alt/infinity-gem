"""DSGE research, milestone 4b (19 Oct 2026): estimate the small open economy on Philippine data, 2002Q1-2019Q4.

Posterior mode (Nelder-Mead from the prior means), then random-walk Metropolis (proposal: diagonal, scaled to an acceptance rate
near 25-35%), posterior means and 90% bands, and impulse responses at the posterior mean: a 25 bp policy-rate shock and a
productivity shock. Writes dsge_ph_estimation_<stamp>.md next to this script (moved to outputs/).
Run:  py run_ph_estimation.py [n_draws]
"""
import datetime as dt
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import estimate as E   # noqa: E402
import ph_data         # noqa: E402
import soe_lcp as L    # noqa: E402


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30000
    t0 = time.time()
    Zdf = ph_data.observables()
    Z = Zdf[E.OBS].to_numpy()
    m, lp, res = E.mode(Z, maxiter=8000)
    m, lp, res = E.mode(Z, theta0=m, maxiter=8000)                 # restart once from the first mode
    prior_sd = np.array([e[3] for e in E.EST])
    scale = np.diag((0.15 * np.minimum(prior_sd, np.maximum(np.abs(m), 0.05))) ** 2)
    draws, acc = E.rwmh(Z, m, scale, n=n)
    for _ in range(3):                                              # re-tune the step from the draws' covariance
        if 0.2 < acc < 0.4:
            break
        cov = np.cov(draws.T) + 1e-10 * np.eye(len(m))
        draws, acc = E.rwmh(Z, draws[-1], (2.38 ** 2 / len(m)) * cov * (0.6 if acc < 0.2 else 1.4), n=n)
    mean, lo, hi = draws.mean(0), np.percentile(draws, 5, 0), np.percentile(draws, 95, 0)
    tab = pd.DataFrame({"prior": [f"{e[1]} ({e[2]}, {e[3]})" for e in E.EST], "mode": m, "mean": mean, "5%": lo, "95%": hi},
                       index=E.NAMES)
    kw = dict(zip(E.NAMES, mean))
    sd = {k: kw.pop(k) for k in ("sd_v", "sd_a", "sd_ystar", "sd_pistar")}
    p = L.Params(**kw)
    rv = L.irf(p, "v", 0.25 / 100 / (1 - p.rho_i) if p.rho_i < 1 else 0.0025, T=12)   # about 25 bp on impact
    scale_v = 0.25 / (100 * rv["i"][0]) if rv["i"][0] else 1.0
    rows = {}
    for k in ("i", "y", "pi", "piH", "piF", "de", "q"):
        rows[k] = 100 * rv[k][:9] * scale_v
    irf_v = pd.DataFrame(rows, index=[f"q{t}" for t in range(9)]).T
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    out = HERE.parents[1] / "outputs" / f"dsge_ph_estimation_{stamp}.md"                 # Infinity GEM outputs/
    Lines = [f"# DSGE research (Stage 3): the small open economy estimated on Philippine data ({dt.datetime.now():%d %B %Y, %H:%M})", "",
             "**NOT FOR CITATION** (research code, Infinity GEM 0.3.11 `research/dsge/`). Model: Gali-Monacelli (2005) with Monacelli "
             "(2005) import-price stickiness and a CPI rule with smoothing (`soe_lcp.py`). Data: 2002Q1-2019Q4, 72 quarters "
             "(`ph_data.py`: PSA real GDP and CPI, BIS policy rate and PHP/USD; demeaned, seasonal means removed). "
             f"Random-walk Metropolis: {n:,} draws per chain run, 25% burn-in, acceptance {acc:.2f}; log posterior at the mode "
             f"{lp:.1f}; {time.time() - t0:.0f} s.", "",
             "## Posterior", "", tab.to_markdown(floatfmt=".3f"), "",
             "## A 25 bp rise in the policy rate (posterior mean; % deviations, quarters after the shock)", "",
             irf_v.to_markdown(floatfmt=".3f"), "",
             f"Shock sizes (% a quarter, posterior mean): policy {sd['sd_v']:.2f}, productivity {sd['sd_a']:.2f}, world output "
             f"{sd['sd_ystar']:.2f}, world inflation {sd['sd_pistar']:.2f}."]
    out.write_text("\n".join(Lines) + "\n", encoding="utf-8")
    print("\n".join(Lines))
    np.save(HERE.parents[1] / "outputs" / f"dsge_ph_draws_{stamp}.npy", draws)
    print("saved", out)


if __name__ == "__main__":
    main()
