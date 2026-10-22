"""DSGE research, milestone 19c (20 Oct 2026, about 9:05 AM): why soe_htmu's 100 bp effect is 3-4 times PAMPh's.

Milestone 19's candidate DSGE (soe_htmu, 2002-2026, STL GDP) gives a 2026 output gap of about -1.0% after a 100 bp policy
shock; the BSP's PAMPh (its y/y GDP-growth chart turned into levels) gives about -0.23%. Two things differ:
(a) the RATE PATH after the shock. In soe_htmu the policy shock is persistent (rho_v about 0.5) and the rule smooth (rho_i
    0.95), so the rate keeps rising for two quarters, as the project's local projections of the BSP's rate do (milestone 12); in
    PAMPh it is back to zero within three quarters;
(b) TRANSMISSION: what a given rate path does to output and prices.
To separate them, each model is fed the same policy-rate paths by a sequence of policy surprises (Leeper and Zha 2003, as in
conditional_rate_path.py):
  own     the model's own response to a policy shock of +100 bp on impact (what the CGE link used on 20 Oct, 03:10);
  pamph   PAMPh's rate path, scaled to +100 bp on impact (1/0.8 of its chart);
  hold4   +100 bp held for four quarters, then the baseline ("one year of tighter policy").
Models: PAMPh (charts), the QPM calibrated to it (qpm.py), soe_htm (milestone 13, 2002-2019, converged seeds 4-6) and soe_htmu
(milestone 19, converged seeds 2-4), both over posterior draws (median, 5% and 95%); extra soe_htmu chains with extra=<glob>
(several allowed), e.g. the prior-sensitivity runs of 20 Oct (prior=ratio_cpi; w=0).
Run:  py rate_path_review.py [n_per_chain=150] [extra=dsge_ph_htmu_draws_*_w0_long_stl.npy]
Writes outputs/dsge_rate_path_review_<stamp>.md.
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
import klein                                   # noqa: E402
import pamph_targets as T                      # noqa: E402
import qpm                                     # noqa: E402
import soe_htm                                 # noqa: E402
import soe_htmu                                # noqa: E402
from transmission_benchmarks import HTM_NAMES  # noqa: E402

OUT = HERE.parents[1] / "outputs"
H = 24                                                         # quarters of every path
HTMU_NAMES = HTM_NAMES[:HTM_NAMES.index("rho_z") + 1] + ["rho_u"] + HTM_NAMES[HTM_NAMES.index("rho_z") + 1:] + ["sd_u"]


def pamph_rate_path():
    """PAMPh's policy-rate response (pp a year) for quarters 1..H, linear between charted quarters, 0 after q20; per 0.80 pp."""
    q = np.array(T.QUARTERS, float)
    v = np.array([T.POLICY_RATE_PA[k] for k in T.QUARTERS], float)
    g = np.arange(1, H + 1, dtype=float)
    return np.where(g <= q.max(), np.interp(g, q, v), 0.0)


PATHS = {"own": None, "pamph": pamph_rate_path() / 0.80, "hold4": np.r_[np.ones(4), np.zeros(H - 4)]}


def metrics(i_pa, y_pct, pi_pa, q_pct):
    """Summary of quarterly paths (index 0 = 2026Q1): rate in pp a year, output and real exchange rate in %, inflation in pp a
    year (annualized quarterly). The real-rate gap uses next quarter's realized inflation, as posterior_strength.annual does."""
    ylev = np.r_[np.zeros(4), y_pct]                           # four zero quarters before the shock
    growth = ylev[4:] - ylev[:-4]
    pil = np.r_[np.zeros(3), pi_pa]
    infl_yoy = np.array([pil[t:t + 4].sum() / 4 for t in range(len(pi_pa))])
    rr = i_pa[:-1] - pi_pa[1:]
    return {"rate q1-q4 (pp)": ", ".join(f"{x:.2f}" for x in i_pa[:4]),
            "policy rate 2026 (pp, mean)": i_pa[:4].mean(), "policy rate 2027 (pp, mean)": i_pa[4:8].mean(),
            "output gap 2026 (%)": y_pct[:4].mean(), "output gap 2027 (%)": y_pct[4:8].mean(),
            "GDP growth trough (pp y/y)": growth[:20].min(), "CPI inflation trough (pp y/y)": infl_yoy[:20].min(),
            "real-rate gap 2026 (pp)": rr[:4].mean(), "real exchange rate 2026 (%)": q_pct[:4].mean(),
            "output 2026 per pp of 2026 rate": y_pct[:4].mean() / i_pa[:4].mean()}


def conditional_paths(unit, target):
    """unit: responses to one unit policy innovation at t = 0 (dict of arrays "i", "y", "pi", "q" in the units of metrics);
    target: the rate path (pp a year) for t = 0..H-1, or None for the model's own response scaled to +1 pp on impact.
    Returns the quarterly paths of the four variables (also used by scenarios/qpm_cge_link.py path=hold4)."""
    if target is None:
        e = np.zeros(H); e[0] = 1.0 / unit["i"][0]
    else:
        M = np.array([[unit["i"][t - s] if t >= s else 0.0 for s in range(H)] for t in range(H)])
        e = np.linalg.solve(M, target)
    conv = lambda x: np.array([sum(x[t - s] * e[s] for s in range(t + 1)) for t in range(H)])
    return {k: conv(unit[k]) for k in ("i", "y", "pi", "q")}


def conditional(unit, target):
    return metrics(*conditional_paths(unit, target).values())


def dsge_unit(M, kw):
    r = M.irf(M.Params(rule="output", **kw), "v", 0.001, T=H + 1)
    return {"i": 400 * r["i"], "y": 100 * r["y"], "pi": 400 * r["pi"], "q": 100 * r["q"]}


def qpm_unit():
    p, *_ = qpm.match_pamph()
    r = qpm.irf(p, "e_i", 1.0, T=H + 1)
    return {"i": r["i"], "y": r["ygap"], "pi": r["pi"], "q": r["z"]}


def pamph_row():
    """PAMPh's own responses (charts), per +100 bp on impact. Output levels from y/y growth: y(q) = g(q) + y(q - 4)."""
    s = 1 / 0.80
    g = {q: T.GDP_GROWTH_YOY[q] for q in range(1, 9)}
    y = {}
    for q in range(1, 9):
        y[q] = g[q] + (y[q - 4] if q > 4 else 0.0)
    rate = pamph_rate_path() * s
    return {"rate q1-q4 (pp)": ", ".join(f"{x:.2f}" for x in rate[:4]),
            "policy rate 2026 (pp, mean)": rate[:4].mean(), "policy rate 2027 (pp, mean)": rate[4:8].mean(),
            "output gap 2026 (%)": s * np.mean([y[q] for q in (1, 2, 3, 4)]),
            "output gap 2027 (%)": s * np.mean([y[q] for q in (5, 6, 7, 8)]),
            "GDP growth trough (pp y/y)": s * min(T.GDP_GROWTH_YOY.values()),
            "CPI inflation trough (pp y/y)": s * min(T.CPI_INFLATION_YOY.values()),
            "real-rate gap 2026 (pp)": np.nan, "real exchange rate 2026 (%)": np.nan,
            "output 2026 per pp of 2026 rate": s * np.mean([y[q] for q in (1, 2, 3, 4)]) / rate[:4].mean()}


def posterior(M, names, files, n_per, rng):
    """Metrics for each path over posterior draws: {path: DataFrame of draws x metrics}."""
    rows = {k: [] for k in PATHS}
    for f in files:
        D = np.load(f)
        for j in rng.choice(len(D), size=min(n_per, len(D)), replace=False):
            kw = {k: v for k, v in zip(names, D[j]) if not k.startswith("sd_")}
            try:
                unit = dsge_unit(M, kw)
                res = {k: conditional(unit, tgt) for k, tgt in PATHS.items()}
            except (klein.BlanchardKahnError, ValueError, np.linalg.LinAlgError, ZeroDivisionError):
                continue
            for k in PATHS:
                rows[k].append(res[k])
    return {k: pd.DataFrame(v) for k, v in rows.items()}


def summarize(label, dfs):
    out = []
    for k, d in dfs.items():
        num = d.drop(columns=["rate q1-q4 (pp)"])
        med = num.median()
        lo, hi = num.quantile(0.05), num.quantile(0.95)
        row = {"model": label, "path": k, "draws": len(d)}
        for c in num.columns:
            row[c] = f"{med[c]:.2f} ({lo[c]:.2f} to {hi[c]:.2f})"
        rq = np.median(np.vstack([np.array([float(x) for x in s.split(", ")]) for s in d["rate q1-q4 (pp)"]]), axis=0)
        row["rate q1-q4 (pp)"] = ", ".join(f"{x:.2f}" for x in rq)
        out.append(row)
    return out


def main():
    n_per = int(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("n_per_chain=")), 150))
    extras = [a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("extra=")]
    rng = np.random.default_rng(0)
    rows = [{"model": "PAMPh (BSP WPS 2020-12, charts)", "path": "own (= pamph)", "draws": "",
             **{k: (f"{v:.2f}" if isinstance(v, float) and np.isfinite(v) else ("n.a." if isinstance(v, float) else v))
                for k, v in pamph_row().items()}}]
    qu = qpm_unit()
    for k, tgt in PATHS.items():
        rows.append({"model": "QPM calibrated to PAMPh (qpm.py)", "path": k, "draws": "",
                     **{c: (f"{v:.2f}" if isinstance(v, float) else v) for c, v in conditional(qu, tgt).items()}})
    specs = [("soe_htm, milestone 13 (2002-2019)", soe_htm, HTM_NAMES, sorted(OUT.glob("dsge_ph_htm_draws_*_w1_ratio_seed[456].npy"))),
             ("soe_htmu, milestone 19 candidate (2002-2026, STL GDP)", soe_htmu, HTMU_NAMES,
              sorted(OUT.glob("dsge_ph_htmu_draws_*_w1_ratio_long_stl_seed*.npy")))]
    for pat in extras:
        fs = sorted(OUT.glob(pat))
        if fs:
            specs.append((f"soe_htmu, {fs[-1].stem.split('_draws_')[1][14:]} ({len(fs)} chain{'s' * (len(fs) > 1)})", soe_htmu, HTMU_NAMES, fs))
    used = []
    for label, M, names, files in specs:
        if not files:
            continue
        used += [f.name for f in files]
        rows += summarize(label, posterior(M, names, files, n_per, rng))
    tab = pd.DataFrame(rows).set_index(["model", "path"])
    cols = ["draws", "rate q1-q4 (pp)", "policy rate 2026 (pp, mean)", "policy rate 2027 (pp, mean)", "output gap 2026 (%)",
            "output gap 2027 (%)", "output 2026 per pp of 2026 rate", "GDP growth trough (pp y/y)", "CPI inflation trough (pp y/y)",
            "real-rate gap 2026 (pp)", "real exchange rate 2026 (%)"]
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    L = [f"# DSGE research, milestone 19c: rate paths against transmission ({dt.datetime.now():%d %B %Y, %H:%M})", "",
         "**NOT FOR CITATION** (research code, `research/dsge/rate_path_review.py`). Each model is fed three policy-rate paths "
         "by a sequence of policy surprises (Leeper and Zha 2003): `own` = its own response to a +100 bp policy shock on impact; "
         "`pamph` = PAMPh's path scaled to +100 bp on impact; `hold4` = +100 bp for four quarters, then the baseline. "
         "DSGE cells: posterior median (5% to 95%). PAMPh's output gap comes from its y/y GDP-growth chart (y(q) = g(q) + y(q-4)); "
         "its inflation path is not charted quarter on quarter, so its real-rate gap is not available.", "",
         f"Draws from: {', '.join(used)}.", "", tab[cols].to_markdown()]
    path = OUT / f"dsge_rate_path_review_{stamp}.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L)); print("saved", path)


if __name__ == "__main__":
    main()
