"""DSGE research (Stage 3) (19 Oct 2026, about 2:05 AM): report of the Philippine estimation from its saved posterior draws.

Posterior means and 90% bands, and impulse responses to ONE-STANDARD-DEVIATION shocks at the posterior mean (the first report
scaled the policy shock to a 25 bp rise on impact, which overstates it: under a strong Taylor rule the rate's own response
offsets most of the shock, so a 25 bp net rise needs a very large shock).
Run:  py report_ph_estimation.py <draws .npy>      (writes outputs/dsge_ph_estimation_report_<stamp>.md)
"""
import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import estimate as E   # noqa: E402
import soe_lcp as L    # noqa: E402


def main():
    f = Path(sys.argv[1])
    d = np.load(f)
    tab = pd.DataFrame({"prior": [f"{e[1]} ({e[2]}, {e[3]})" for e in E.EST], "mean": d.mean(0),
                        "5%": np.percentile(d, 5, 0), "95%": np.percentile(d, 95, 0)}, index=E.NAMES)
    kw = dict(zip(E.NAMES, d.mean(0)))
    sd = {k: kw.pop(k) for k in ("sd_v", "sd_a", "sd_ystar", "sd_pistar")}
    p = L.Params(**kw)
    blocks = []
    for shock, key, label in (("v", "sd_v", "policy-rate shock"), ("a", "sd_a", "productivity shock"),
                              ("ystar", "sd_ystar", "world output shock"), ("pistar", "sd_pistar", "world inflation shock")):
        r = L.irf(p, shock, sd[key] / 100, T=9)
        t = pd.DataFrame({"policy rate (pp, annualized)": 400 * r["i"], "output (%)": 100 * r["y"],
                          "CPI inflation (pp, annualized)": 400 * r["pi"], "depreciation (%)": 100 * r["de"],
                          "real exchange rate (%)": 100 * r["q"]}, index=[f"q{k}" for k in range(9)]).T
        blocks += [f"### One-standard-deviation {label} ({sd[key]:.2f}% a quarter)", "", t.to_markdown(floatfmt=".2f"), ""]
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    out = HERE.parents[1] / "outputs" / f"dsge_ph_estimation_report_{stamp}.md"
    Lines = [f"# DSGE research (Stage 3): the small open economy estimated on Philippine data, 2002Q1-2019Q4 ({dt.datetime.now():%d %B %Y, %H:%M})", "",
             "**NOT FOR CITATION** (research code, Infinity GEM 0.3.11 `research/dsge/`). Model `soe_lcp.py` (Gali-Monacelli 2005 with "
             "Monacelli 2005 import-price stickiness and a CPI rule with smoothing); data `ph_data.py` (PSA real GDP and CPI, BIS "
             f"policy rate and PHP/USD; 72 quarters). Posterior from {len(d):,} random-walk Metropolis draws (`{f.name}`).", "",
             "## Posterior", "", tab.to_markdown(floatfmt=".3f"), "",
             "Reading: domestic prices are reset on average every 1 / (1 - theta) quarters; import prices adjust faster (theta_F); the "
             "policy rule answers inflation more than one for one (phi_pi > 1) with strong smoothing (rho_i).", "",
             "## Impulse responses at the posterior mean (quarters after the shock)", ""] + blocks
    out.write_text("\n".join(Lines) + "\n", encoding="utf-8")
    print("\n".join(Lines[:12]))
    print("saved", out)


if __name__ == "__main__":
    main()
