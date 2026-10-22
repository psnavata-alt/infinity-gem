"""DSGE research (Stage 3) (20 Oct 2026, about 9:45 PM): the estimated policy rule against the BSP's actual 2026 decisions
(next step: "check the estimated rule against the BSP's actual 2026 rate decisions before any monetary
number is cited").

Method. At the posterior mean of the chosen chains (pooled as oil_policy.posterior_mean_params), the Kalman smoother (Rauch-Tung-
Striebel, as research/dsge/investment_response.py) reads the estimation data 2002Q1-2026Q2 (COVID quarters missing) through the
model. For each quarter it gives the smoothed inflation, output gap and depreciation, the policy rate the RULE prescribes from them
(i_rule = rho_i i_lag + (1 - rho_i)(phi_pi pi + phi_x y + phi_e de), no shock) and the monetary-policy shock v (the part of the actual
rate the rule does not explain; an AR(1) state), with its innovation e_v = v - rho_v v_lag in pp a year and in units of the
estimated s.d. (sd_v). A 2026 decision the rule explains leaves a small innovation; a rate higher than the rule prescribes leaves a
positive one. Reported for 2024Q1-2026Q2; the BSP's August 2026 move is after the last quarter with GDP data (2026Q2) and is
compared in levels from the BIS series. Also shown: the model's own policy-rate response to the 2026-sized oil shock (oil_policy.py).
Run (repository root):
  py research/dsge/rule_check_2026.py model=oilw theta_fix=0.73 spec=_long_stl_thfix0.73 sample=long gdp=stl prior=ratio [oil=36]
Output: outputs/dsge_rule_check_2026_<stamp><spec>.md
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import linalg

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import oil_policy as OP          # noqa: E402  (sets model= from argv; imports estimate_rot as ER with theta_fix=, sample=, gdp=, prior=)
import estimate_rot as ER        # noqa: E402
import ph_data as D              # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = HERE.parents[1] / "outputs"
RAW = HERE.parents[1] / "data" / "raw" / "macro"


def arg(name, default, cast=float):
    return next((cast(a.split("=", 1)[1]) for a in sys.argv[1:] if a.startswith(f"{name}=")), default)


def pooled(spec):
    """Posterior mean over the chains of the specification (the same files as oil_policy.posterior_mean_params)."""
    files = [f for f in sorted(OUT.glob(f"dsge_ph_{ER.MODEL}_draws_*_w1_ratio{spec}*.npy"))
             if all((f"_{t}" in f.stem) == (f"_{t}" in spec) for t in ("long", "stl", "thfix", "thhi", "igrea"))]
    theta = np.vstack([np.load(f) for f in files]).mean(0)
    kw, sds = ER.split(theta)
    return {**kw, **ER.FIXED}, sds, files


def smooth(Pm, Rm, Q, Hm, Z, me=1e-4):
    """RTS smoother with missing observations (as investment_response.smoothed_policy_shocks). Returns the smoothed state vectors."""
    n = Pm.shape[0]
    RQR = Rm @ Q @ Rm.T
    S = linalg.solve_discrete_lyapunov(Pm, RQR)
    x = np.zeros(n)
    Me = np.eye(Hm.shape[0]) * me
    xp, Sp, xf, Sf = [], [], [], []
    for z in Z:
        xp.append(x); Sp.append(S)
        ok = np.isfinite(z)
        if ok.any():
            Hk, Mk = Hm[ok], Me[np.ix_(ok, ok)]
            F = Hk @ S @ Hk.T + Mk
            G = S @ Hk.T @ np.linalg.inv(F)
            x, S = x + G @ (z[ok] - Hk @ x), S - G @ Hk @ S
        xf.append(x); Sf.append(S)
        x, S = Pm @ x, Pm @ S @ Pm.T + RQR
    xs = [None] * len(Z)
    xs[-1] = xf[-1]
    for t in range(len(Z) - 2, -1, -1):
        J = Sf[t] @ Pm.T @ np.linalg.pinv(Sp[t + 1])
        xs[t] = xf[t] + J @ (xs[t + 1] - xp[t + 1])
    return xs


def main():
    spec = arg("spec", "", str)
    oil = arg("oil", 36.0)
    kw, sds, files = pooled(spec)
    p = OP.Oil.Params(rule="output", **kw)
    sol, _ = OP.Oil.solve(p)
    Pm, Rm, Q, Hm = ER.state_space(sol, sds, kw.get("chi_o", 0.0))
    dkw = dict(end=D.LONG_END, covid="missing") if ER.SAMPLE == "long" else {}
    if ER.GDP_SA == "stl":
        dkw["gdp_sa"] = "stl"
    df = D.observables_oilw(world=ER.WORLD, **dkw)
    Z = df[ER.E0.OBS + ["doil", "dystar"]].to_numpy()
    mean_i = 4 * df.attrs["means"]["i"]                                       # the sample mean of the policy rate, % a year
    xs = smooth(Pm, Rm, Q, Hm, Z)
    nk = len(OP.Oil.STATES)
    ixk = {n: j for j, n in enumerate(OP.Oil.STATES)}
    ixd = {n: j for j, n in enumerate(OP.Oil.JUMPS)}
    F = sol.F
    rows = []
    sd_v = 4 * sds[ER.SHOCKS.index("v")]                                       # pp a year (sds are % a quarter)
    for t, q in enumerate(df.index):
        s = xs[t][:nk]
        jump = lambda n: float(F[ixd[n]] @ s)
        i, pi, y, de = 400 * jump("i"), 400 * jump("pi"), 100 * jump("y"), 400 * jump("de")
        pic = 400 * jump("pi_c")
        i_lag, v = 400 * float(s[ixk["i_lag"]]), 400 * float(s[ixk["v"]])
        v_lag = 400 * float(xs[t][nk + ixk["v"]])
        pi_rule = pi if getattr(p, "rule_infl", "headline") == "headline" else pic
        i_rule = kw["rho_i"] * i_lag + (1 - kw["rho_i"]) * (kw["phi_pi"] * pi_rule + 4 * kw["phi_x"] * y + kw["phi_e"] * de)
        e_v = v - kw["rho_v"] * v_lag
        rows.append({"quarter": str(q), "actual policy rate (% a year)": mean_i + 4 * Z[t, 2] if np.isfinite(Z[t, 2]) else np.nan,
                     "smoothed rate (% a year)": mean_i + i, "rule's rate, no shock (% a year)": mean_i + i_rule,
                     "headline inflation gap (pp a year)": pi, "core inflation gap (pp a year)": pic, "output gap (%)": y,
                     "peso depreciation gap (pp a year)": de, "policy shock v (pp)": v, "innovation e_v (pp)": e_v,
                     "e_v / s.d.": e_v / sd_v, "check: rate - rule - v (pp)": i - i_rule - v})
    T = pd.DataFrame(rows).set_index("quarter")
    recent = T.loc["2024Q1":]
    z26 = T.loc["2026Q1":, "e_v / s.d."]
    zsample = T["e_v / s.d."].dropna()
    # the BIS level path, quarterly averages, 2025Q1-2026Q3 (the rate is end of month; the quarter's mean of the three months)
    bis = pd.read_csv(RAW / "BIS_WS_CBPOL_policy_rate_Philippines_monthly.csv", comment="#")
    bis["q"] = pd.PeriodIndex(bis["month"], freq="M").asfreq("Q")
    lv = bis.groupby("q")["value"].mean().loc["2025Q1":]
    lv.index = lv.index.astype(str)
    # the model's own response to the 2026-sized oil shock (the estimated rule, quarterly path, pp a year)
    a = OP.paths(p, oil / 100)
    own = pd.Series(np.asarray(a["policy rate (pp a year)"][:6], float), index=[f"q{k + 1}" for k in range(6)])
    stamp = dt.datetime.now()
    out = OUT / f"dsge_rule_check_2026_{stamp:%Y%m%d_%H%M}{spec}.md"
    L = [f"# The estimated policy rule against the BSP's actual 2026 decisions ({stamp:%d %B %Y, %H:%M})", "",
         f"**NOT FOR CITATION** (research code, `research/dsge/rule_check_2026.py`). Model `soe_{OP._M}.py` at the posterior mean of "
         f"{len(files)} chain(s) pooled ({', '.join(f.name for f in files)}); rule: i = {kw['rho_i']:.3f} i_lag + (1 - {kw['rho_i']:.3f}) "
         f"({kw['phi_pi']:.3f} headline inflation + {4 * kw['phi_x']:.3f} output gap (pp a year per % of output) + {kw['phi_e']:.3f} "
         f"peso depreciation) + v, v an AR(1) with rho_v {kw['rho_v']:.3f} and innovation s.d. {sd_v:.2f} pp a year. Data: the estimation "
         f"sample 2002Q1-{df.index[-1]} (COVID quarters missing, STL-adjusted GDP), read through the model by the Kalman smoother; the "
         f"gaps are deviations from the sample means (policy rate mean {mean_i:.2f}% a year).", "",
         "## Reading", "",
         f"- Policy-shock innovations in 2026 (e_v / s.d.): {', '.join(f'{q} {z:+.2f}' for q, z in z26.items())}; sample mean of |e_v / s.d.| "
         f"{zsample.abs().mean():.2f}, 95th percentile {zsample.abs().quantile(0.95):.2f}.",
         f"- The BSP's policy rate, quarterly averages (BIS): {', '.join(f'{q} {v:.2f}%' for q, v in lv.items())}.",
         f"- The model's own response to a {oil:g}% oil-price rise (the estimated rule, pp a year above baseline): "
         f"{', '.join(f'{q} {v:+.2f}' for q, v in own.items())}.", "",
         "## 2024Q1 to the last quarter of data", "", recent.to_markdown(floatfmt=".2f"), "",
         "## Whole sample: the ten largest innovations", "",
         T.reindex(T["e_v / s.d."].abs().sort_values(ascending=False).index[:10])[["actual policy rate (% a year)", "rule's rate, no shock (% a year)",
                                                                                   "innovation e_v (pp)", "e_v / s.d."]].to_markdown(floatfmt=".2f"), ""]
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L)); print("saved", out)


if __name__ == "__main__":
    main()
