"""DSGE research (Stage 3) (21 Oct 2026, about 1:30 AM): the candidate DSGE's posterior across
specifications, in one table, for the estimation report (guide 11b).

For each specification of soe_htmu on file (the system prior on transmission strength 'ratio' against 'ratio_cpi' and the data-only
w = 0; the long sample 2002-2026 against the short 2002-2019; STL-adjusted GDP against raw; the Calvo bound 0.97 against 0.99; the
sequential Monte Carlo cloud against the Metropolis chains; the sample cut at 2023Q4 for the forecast check) the script pools the
saved draws (first run and its seeds), and reports the posterior mean and 90% band of the parameters that matter for the CGE link
and the money block (theta, kappa, lam_h, hab, the rule), the transmission strength at the posterior mean (trough of CPI y/y and
GDP y/y growth per pp of the first year's cumulative policy-rate path), the log likelihood at the mean, and the implied annual rule
coefficients as infinity_gem.monetary.rule reads them. Nothing is re-estimated here.
Run: py robustness_candidate.py      (writes outputs/dsge_robustness_candidate_<stamp>.md)
"""
from __future__ import annotations

import datetime as dt
import importlib
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
OUT = HERE.parents[1] / "outputs"

# label: (estimate_rot arguments, glob of draws files, regex the stem must match (None = any), what it tests)
SPECS = {
    "ratio, 2002-2026, STL (the candidate)": (["prior=ratio", "sample=long", "gdp=stl"], "dsge_ph_htmu_draws_*_w1_ratio_long_stl*.npy",
                                              r"_w1_ratio_long_stl(_seed\d+)?$", "reference"),
    "SMC cloud, same specification": (["prior=ratio", "sample=long", "gdp=stl"], "dsge_smc_*_htmu_w1_ratio_long_stl_n1000_particles.npy",
                                      None, "a second sampler from the prior (smc.py)"),
    "ratio on CPI only (ratio_cpi)": (["prior=ratio_cpi", "sample=long", "gdp=stl"], "dsge_ph_htmu_draws_*_w1_ratiocpi_long_stl*.npy",
                                      r"_w1_ratiocpi_long_stl(_seed\d+)?$", "the output-strength prior's role"),
    "ratio2: ratio plus a prior on the rate path's scale": (["prior=ratio2", "sample=long", "gdp=stl"],
                                                                     "dsge_ph_htmu_draws_*_w1_ratio2_long_stl*.npy",
                                                                     r"_w1_ratio2_long_stl(_seed\d+)?$", "the repaired system prior"),
    "data only (w = 0)": (["prior=ratio", "sample=long", "gdp=stl"], "dsge_ph_htmu_draws_*_w0_long_stl*.npy",
                          r"_w0_long_stl(_seed\d+)?$", "no system prior"),
    "ratio, 2002-2026, raw GDP": (["prior=ratio", "sample=long"], "dsge_ph_htmu_draws_*_w1_ratio_long.npy", r"_w1_ratio_long$",
                                  "the seasonal adjustment's role"),
    "ratio, 2002-2019, STL (short sample)": (["prior=ratio", "sample=short", "gdp=stl"], "dsge_ph_htmu_draws_*_w1_ratio_stl*.npy",
                                             r"_w1_ratio_stl(_seed\d+)?$", "before COVID and the 2026 shocks"),
    "ratio, 2002-2026, STL, Calvo bound 0.99": (["prior=ratio", "sample=long", "gdp=stl", "theta_hi=0.99"],
                                                "dsge_ph_htmu_draws_*_w1_ratio_long_stl_thhi0.99*.npy", None, "the bound on theta"),
    "ratio, 2002-2023Q4, STL (forecast check)": (["prior=ratio", "sample=long", "gdp=stl", "end=2023Q4"],
                                                 "dsge_ph_htmu_draws_*_w1_ratio_long_stl_to2023Q4*.npy", None, "estimated before 2024-2026"),
}
KEY = ["theta", "theta_F", "omega_H", "hab", "lam_h", "kappa", "phi_pi", "phi_x", "phi_e", "rho_i", "sd_a", "sd_u"]


def load_spec(args, pattern, must):
    sys.argv = ["x", "model=htmu"] + args
    import estimate_rot as ER
    ER = importlib.reload(ER)
    files = [f for f in sorted(OUT.glob(pattern)) if must is None or re.search(must, f.stem)]
    if not files:
        return ER, None, []
    D = np.vstack([np.load(f) for f in files])
    return ER, D, files


def main():
    rows, strength, notes = {}, {}, []
    Zcache = {}
    for label, (args, pattern, must, what) in SPECS.items():
        ER, D, files = load_spec(args, pattern, must)
        if D is None or D.shape[1] != len(ER.NAMES):
            notes.append(f"- {label}: no draws on file (pattern `{pattern}`){'' if D is None else f'; {D.shape[1]} columns against {len(ER.NAMES)} names'}.")
            continue
        key = (ER.SAMPLE, ER.GDP_SA, ER.END, ER.MODEL)
        if key not in Zcache:
            Zcache[key] = ER.observables()
        Z = Zcache[key]
        m = D.mean(0)
        row = {}
        for k in KEY:
            if k in ER.NAMES:
                j = ER.NAMES.index(k)
                row[k] = f"{m[j]:.3f} ({np.percentile(D[:, j], 5):.2f}–{np.percentile(D[:, j], 95):.2f})"
        p = ER.pieces(m, Z)
        if p is None:
            row["at the mean"] = "no solution"
        else:
            row["log likelihood at the mean"] = f"{p[1]:.1f}"
            row["transmission: CPI / growth per pp"] = f"{p[4]['infl']:.2f} / {p[4]['growth']:.2f}"
        row["draws (files)"] = f"{D.shape[0]:,} ({len(files)})"
        row["tests"] = what
        rows[label] = row
    tab = pd.DataFrame(rows).T
    stamp = dt.datetime.now()
    path = OUT / f"dsge_robustness_candidate_{stamp:%Y%m%d_%H%M}.md"
    L = [f"# The candidate DSGE (soe_htmu) across specifications ({stamp:%d %B %Y, %H:%M})", "",
         "**NOT FOR CITATION** (research code, `research/dsge/robustness_candidate.py`). Posterior mean (5%–95% band) from the pooled saved "
         "draws of each specification; the transmission strength (trough of CPI y/y inflation and of GDP y/y growth per pp of the first "
         "year's cumulative policy-rate path) and the log likelihood at the posterior mean. The system prior 'ratio' is N(−0.35, 0.10) on CPI "
         "strength and N(−0.20, 0.15) on growth strength; 'ratio_cpi' drops the growth part; w = 0 drops both.", "",
         tab.to_markdown(), ""]
    if notes:
        L += ["Specifications without draws on file:", *notes, ""]
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(tab.to_string())
    print("\n".join(notes))
    print("saved", path)


if __name__ == "__main__":
    main()
