"""DSGE research, milestone 11b (19 Oct 2026): transmission compared at the SAME policy-rate path.

Why: milestone 10 compared the estimated DSGE with the BSP's PAMPh 'per +0.80 pp policy shock on impact'. But the DSGE
estimated on data alone turns a policy shock into a persistent rate rise (interest smoothing 0.94: 0.80, 0.82, 0.62, 0.42 ...
pp), while PAMPh's rate is back to zero within three quarters (0.80, 0.35, 0.05, -0.12): about seven times less tightening
over two years. So 'transmission 10-15 times PAMPh's' mixes two things: what the central bank does after a shock (the rule)
and what a given rate path does to the economy (transmission).
Here each model is given PAMPh's own rate path, quarter by quarter, through a sequence of policy surprises (an unanticipated
path, Leeper and Zha 2003 'modest policy interventions'), and its GDP growth, CPI inflation and peso are compared with PAMPh's.
Models: soe_rot (milestone 10) at its data-only (w = 0) and system-prior (w = 1) posterior means; soe_med (milestone 6) at its
posterior mean. Writes outputs/dsge_conditional_rate_path_<stamp>.md.
Leeper, E. M., and T. Zha (2003). "Modest Policy Interventions." Journal of Monetary Economics 50(8): 1673-1700.
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import estimate_med as EM    # noqa: E402
import estimate_rot as ER    # noqa: E402
import pamph_targets as T    # noqa: E402
import soe_med               # noqa: E402
import soe_rot               # noqa: E402

OUT = HERE.parents[1] / "outputs"
H_ = 24                                                        # quarters of the imposed path


def pamph_rate_path():
    """PAMPh's policy-rate response (pp, annualized) for quarters 1..H_, linear between the charted quarters, 0 after q20."""
    q = np.array(T.QUARTERS, float)
    v = np.array([T.POLICY_RATE_PA[k] for k in T.QUARTERS], float)
    grid = np.arange(1, H_ + 1, dtype=float)
    return np.where(grid <= q.max(), np.interp(grid, q, v), 0.0)


def responses_on_path(irf_fn, rate_pa):
    """Policy surprises e_t that make the model's rate equal rate_pa; return PAMPh-style responses at T.QUARTERS."""
    r = irf_fn(H_ + 4)                                         # responses to a unit policy innovation at t = 0
    M = lambda x: np.array([[x[t - s] if t >= s else 0.0 for s in range(H_)] for t in range(H_)])
    e = np.linalg.solve(M(r["i"]), rate_pa / 400.0)
    y, pi, de, i = (M(r[k]) @ e for k in ("y", "pi", "de", "i"))
    pad = lambda x: 100 * np.concatenate([[0.0], x])
    y, pi, de = pad(y), pad(pi), pad(de)
    out = {"rate": {}, "growth": {}, "infl": {}, "fx": {}}
    for q in T.QUARTERS:
        out["rate"][q] = 400 * i[q - 1]
        out["growth"][q] = y[q] - (y[q - 4] if q >= 4 else 0.0)
        out["infl"][q] = pi[max(q - 3, 0):q + 1].sum()
        out["fx"][q] = de[1:q + 1].sum()
    return out, e


def latest(pattern):
    files = sorted(OUT.glob(pattern))
    if not files:
        raise FileNotFoundError(pattern)
    return files[-1]


def model_set():
    sets = {}
    for w in ("0", "1"):
        f = latest(f"dsge_ph_rot_draws_*_w{w}.npy")
        kw, _ = ER.split(np.load(f).mean(0))
        p = soe_rot.Params(rule="output", **kw)
        sets[f"soe_rot, w = {w} ({'data only' if w == '0' else 'PAMPh system prior'})"] = (
            lambda T_, p=p: soe_rot.irf(p, "v", 1.0, T=T_), f.name, p)
    f = latest("dsge_ph_med_draws_*.npy")
    kw = {k: v for k, v in zip(EM.NAMES, np.load(f).mean(0)) if not k.startswith("sd_")}
    p = soe_med.Params(rule="output", **kw)
    sets["soe_med (milestone 6, data only)"] = (lambda T_, p=p: soe_med.irf(p, "v", 1.0, T=T_), f.name, p)
    return sets


def main():
    rate = pamph_rate_path()
    tgt = {"rate": T.POLICY_RATE_PA, "growth": T.GDP_GROWTH_YOY, "infl": T.CPI_INFLATION_YOY, "fx": T.NOMINAL_EXCHANGE_RATE_100LOG}
    tol = {"growth": 0.02, "infl": 0.02, "rate": 0.05, "fx": 0.05}
    rows, summ = [], []
    for k, lab in (("rate", "policy rate (pp p.a.)"), ("growth", "GDP growth (pp y/y)"), ("infl", "CPI inflation (pp y/y)"),
                   ("fx", "nominal exchange rate (100 log)")):
        rows.append({"variable": lab, "source": "PAMPh", **{f"q{q}": tgt[k][q] for q in T.QUARTERS}})
    for name, (fn, src, p) in model_set().items():
        resp, e = responses_on_path(fn, rate)
        unc = fn(H_ + 4)
        s = 0.80 / (400 * unc["i"][0])
        cum_unc = 400 * s * unc["i"][:8].sum()
        dist = sum(((resp[k][q] - tgt[k][q]) / tol[k]) ** 2 for k in ("growth", "infl", "fx") for q in T.QUARTERS)
        ratio = lambda k, q: resp[k][q] / tgt[k][q] if abs(tgt[k][q]) > 1e-9 else np.nan
        summ.append({"model": name, "draws": src,
                     "8-quarter sum of its own policy-shock rate path (PAMPh 0.48)": cum_unc,
                     "distance to PAMPh on PAMPh's rate path (growth, inflation, peso)": dist,
                     "GDP growth trough, model / PAMPh": min(resp["growth"].values()) / min(tgt["growth"].values()),
                     "CPI inflation q5, model / PAMPh": ratio("infl", 5),
                     "peso q1, model / PAMPh": ratio("fx", 1)})
        for k, lab in (("rate", "policy rate (pp p.a.)"), ("growth", "GDP growth (pp y/y)"), ("infl", "CPI inflation (pp y/y)"),
                       ("fx", "nominal exchange rate (100 log)")):
            rows.append({"variable": lab, "source": name, **{f"q{q}": resp[k][q] for q in T.QUARTERS}})
    tab = pd.DataFrame(rows).set_index(["variable", "source"]).sort_index(level=0, sort_remaining=False)
    S = pd.DataFrame(summ).set_index("model")
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    L = [f"# DSGE research, milestone 11b: transmission at PAMPh's own policy-rate path ({dt.datetime.now():%d %B %Y, %H:%M})", "",
         "**NOT FOR CITATION** (research code, `research/dsge/conditional_rate_path.py`). Each model is fed PAMPh's policy-rate "
         "path (BSP WPS 2020-12, Annex 1.A, read off the charts; linear between charted quarters) by a sequence of policy "
         "surprises; its responses are then compared with PAMPh's. Ratios near 1 = same transmission for the same policy.", "",
         "## Summary", "", S.T.to_markdown(floatfmt=".2f"), "", "## Responses on PAMPh's rate path", "", tab.to_markdown(floatfmt=".2f")]
    path = OUT / f"dsge_conditional_rate_path_{stamp}.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L)); print("saved", path)


if __name__ == "__main__":
    main()
