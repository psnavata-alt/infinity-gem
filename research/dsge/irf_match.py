"""DSGE research, milestone 7 (19 Oct 2026, about 3 AM): match soe_med's monetary-policy responses to the BSP's PAMPh.

Minimum distance (Christiano, Eichenbaum and Evans 2005 style) with the Philippine posterior (estimate_med.py) as a prior: choose
the structural parameters so that, after a policy shock scaled to PAMPh's +0.80 pp policy rate in its first quarter, the model's
y/y GDP growth, y/y CPI inflation, nominal exchange rate and policy rate track pamph_targets.py (charts read by eye: soft
targets). Objective = sum of squared gaps / tolerance^2 (tolerances 0.02 for growth and inflation, 0.05 for the rate and the
peso) - 2 x log prior. Writes outputs/dsge_irf_match_<stamp>.md.
Run:  py irf_match.py
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import optimize

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import estimate_med as EM   # noqa: E402
import klein                # noqa: E402
import pamph_targets as T   # noqa: E402
import soe_med as M         # noqa: E402

FREE = ["sigma", "theta", "theta_F", "hab", "gH", "gF", "phi_pi", "phi_x", "phi_e", "rho_i", "rho_v"]
TOL = {"growth": 0.02, "infl": 0.02, "rate": 0.05, "fx": 0.05}


def model_irf(par: dict, T_=21):
    """Responses (quarter 1 = shock) to a policy shock scaled to +0.80 pp (annualized) policy rate on impact."""
    p = M.Params(rule="output", **par)
    r = M.irf(p, "v", 0.001, T=T_)
    s = 0.80 / (400 * r["i"][0])
    y = 100 * s * np.concatenate([[0.0], r["y"]])                  # level deviation, quarter 0 = 0
    pi = 100 * s * np.concatenate([[0.0], r["pi"]])                # quarterly CPI inflation, %
    de = 100 * s * np.concatenate([[0.0], r["de"]])
    out = {}
    for q in T.QUARTERS:
        out.setdefault("growth", {})[q] = y[q] - (y[q - 4] if q >= 4 else 0.0)
        out.setdefault("infl", {})[q] = pi[max(q - 3, 0):q + 1].sum()
        out.setdefault("rate", {})[q] = 400 * s * r["i"][q - 1]
        out.setdefault("fx", {})[q] = de[1:q + 1].sum()
    return out


TARGET = {"growth": T.GDP_GROWTH_YOY, "infl": T.CPI_INFLATION_YOY, "rate": T.POLICY_RATE_PA, "fx": T.NOMINAL_EXCHANGE_RATE_100LOG}


def distance(par):
    m = model_irf(par)
    return sum(((m[k][q] - TARGET[k][q]) / TOL[k]) ** 2 for k in TARGET for q in T.QUARTERS)


def objective(x, base):
    th = base.copy()
    for k, v in zip(FREE, x):
        th[EM.NAMES.index(k)] = v
    lp = EM.prior(th)
    if not np.isfinite(lp):
        return 1e12
    par = {k: v for k, v in zip(EM.NAMES, th) if not k.startswith("sd_")}
    try:
        return distance(par) - 2 * lp
    except (klein.BlanchardKahnError, ValueError, np.linalg.LinAlgError):
        return 1e12


def main():
    d = np.load(sorted((HERE.parents[1] / "outputs").glob("dsge_ph_med_draws_*.npy"))[-1])
    base = d.mean(0)
    x0 = np.array([base[EM.NAMES.index(k)] for k in FREE])
    best = None
    for start in (x0, x0 * np.array([1.5, 1.1, 1.0, 1.1, 1.0, 1.0, 1.2, 1.0, 1.0, 0.8, 1.0])):
        res = optimize.minimize(objective, start, args=(base,), method="Nelder-Mead",
                                options=dict(maxiter=20000, xatol=1e-6, fatol=1e-6, adaptive=True))
        best = res if best is None or res.fun < best.fun else best
    th = base.copy()
    for k, v in zip(FREE, best.x):
        th[EM.NAMES.index(k)] = v
    par = {k: v for k, v in zip(EM.NAMES, th) if not k.startswith("sd_")}
    par0 = {k: v for k, v in zip(EM.NAMES, base) if not k.startswith("sd_")}
    m, m0 = model_irf(par), model_irf(par0)
    rows = []
    for k, lab in (("rate", "policy rate (pp p.a.)"), ("growth", "GDP growth (pp y/y)"), ("infl", "CPI inflation (pp y/y)"), ("fx", "nominal exchange rate (100 log)")):
        for src, name in ((TARGET[k], "PAMPh"), (m, "matched"), (m0, "posterior mean")):
            vals = src if name == "PAMPh" else src[k]
            rows.append({"variable": lab, "source": name, **{f"q{q}": vals[q] for q in T.QUARTERS}})
    tab = pd.DataFrame(rows).set_index(["variable", "source"])
    ptab = pd.DataFrame({"posterior mean": [par0[k] for k in FREE], "matched": [par[k] for k in FREE]}, index=FREE)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    out = HERE.parents[1] / "outputs" / f"dsge_irf_match_{stamp}.md"
    L = [f"# DSGE research, milestone 7: monetary transmission matched to the BSP's PAMPh ({dt.datetime.now():%d %B %Y, %H:%M})", "",
         "**NOT FOR CITATION** (research code). Targets: PAMPh (BSP WPS 2020-12, Annex 1.A), read off the charts (`pamph_targets.py`); "
         f"policy shock scaled to +0.80 pp on impact. Distance at the optimum {distance(par):.1f} (posterior mean {distance(par0):.1f}); "
         f"objective {best.fun:.1f}.", "", "## Parameters", "", ptab.to_markdown(floatfmt=".3f"), "",
         "## Responses (quarter after the shock)", "", tab.to_markdown(floatfmt=".2f")]
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:14])); print("saved", out)


if __name__ == "__main__":
    main()
