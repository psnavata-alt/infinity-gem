"""DSGE research, milestones 27-28 (12 Nov 2026): the BSP's response to the 2026-sized oil SUPPLY shock in the sticky-wage capital
DSGEs with oil, for any of model=htmkwo (milestone 26), htmkwoi (27: wage indexation) or htmkwod (28: plus dollar pricing of
exports). oil_policy_htmkwo.py generalised; that file stays as it is so milestone 26 reproduces. NOT FOR CITATION; research only.

Same construction as oil_policy_htmkwo.py (a real oil-price rise of oil % in its supply component, world output unchanged):
1. the estimated rule (headline CPI inflation, as the BSP targets); 2. a core-inflation rule; 3. the policy rate held at baseline
for four quarters by policy surprises (Leeper and Zha 2003), then the rule. The output cost of the BSP's response is 1 minus 3.
Two checks added for milestones 27-28:
- the POLE check: the share of draws in which the oil supply shock LOWERS year-1 headline inflation. Milestone 27 found a pole in
  the solution (milestone27_scratch/indexation_scan.py: near iota_w 0.92 at milestone 26's posterior); beyond it an oil price rise
  lowers inflation, which no evidence supports. Draws beyond it are counted and reported, and the summary is shown with and
  without them.
- the EXPORTS part of year-1 output: alpha gamma (s + psi) under producer-currency pricing, alpha gamma (-tX) under dollar pricing
  (milestone27_scratch/output_decomposition.py).
Run (research/dsge):  py -I -X utf8 oil_policy_dsge.py model=htmkwod [oil=36] [tag=oillp] [file=<particles .npy in outputs/>]
      [draws=500]   (default file: the newest outputs/dsge_smc_*_<model>_w1_ratio2_long_stl_inv[_<tag>]_n*_particles.npy; writes
      outputs/dsge_oil_policy_<stamp>_<model>_long_stl_inv[_<tag>].md)
"""
from __future__ import annotations

import datetime as dt
import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
OUT = HERE.parents[1] / "outputs"
T = 12
YEARS = (2026, 2027)
MODELS = ("htmkwo", "htmkwoi", "htmkwod")


def _arg(name, default, cast=str):
    return next((cast(a.split("=", 1)[1]) for a in sys.argv[1:] if a.startswith(f"{name}=")), default)


MODEL = _arg("model", "htmkwod")
if MODEL not in MODELS:
    raise SystemExit(f"model must be one of {MODELS}")
# tag= (milestone 30, 12 Nov 2026): the estimation's extra tag after "_inv", e.g. tag=oillp for runs with estimate_rot's oil system
# prior (oilprior=lp). Without it only untagged runs are read (the glob needs "_inv_n" right after the specification).
TAG = _arg("tag", "")
TAGS = f"_{TAG}" if TAG else ""
_saved = sys.argv
sys.argv = ["oil_policy_dsge", f"model={MODEL}", "prior=ratio2", "sample=long", "gdp=stl", "obs=inv"]
import estimate_rot as ER   # noqa: E402  (names and fixed calibration of the model, obs=inv)
sys.argv = _saved
Oil = importlib.import_module(f"soe_{MODEL}")


def particles(file=None):
    if file is None:
        files = sorted(OUT.glob(f"dsge_smc_*_{MODEL}_w1_ratio2_long_stl_inv{TAGS}_n*_particles.npy"))
        if not files:
            raise SystemExit(f"no soe_{MODEL} SMC particles in outputs/")
        f = files[-1]
    else:
        f = OUT / file
    X = np.load(f)
    if X.shape[1] != len(ER.NAMES):
        raise SystemExit(f"{f.name}: {X.shape[1]} columns, model={MODEL} obs=inv has {len(ER.NAMES)}")
    return X, f.name


def params(theta, **extra):
    kw = {k: v for k, v in zip(ER.NAMES, theta) if not k.startswith("sd_") and k != "me_inv"}
    return Oil.Params(rule="output", **{**kw, **ER.FIXED, **extra})


def paths(p, size, hold=0):
    """Responses to an oil-supply shock of `size` (log); hold = quarters the policy rate is held at baseline by surprises."""
    sol, _ = Oil.solve(p)
    ixk = {n: j for j, n in enumerate(Oil.STATES)}
    ixd = {n: j for j, n in enumerate(Oil.JUMPS)}
    e_o = np.zeros(len(Oil.STATES)); e_o[ixk["o"]] = size
    e_v = np.zeros(len(Oil.STATES)); e_v[ixk["v"]] = 1.0
    _, d_o = sol.irf(np.eye(len(Oil.STATES)), e_o, T=T)
    _, d_v = sol.irf(np.eye(len(Oil.STATES)), e_v, T=T)
    d = d_o.copy()
    if hold:
        M = np.array([[d_v[t - s, ixd["i"]] if t >= s else 0.0 for s in range(hold)] for t in range(hold)])
        eps = np.linalg.solve(M, -d_o[:hold, ixd["i"]])
        for s, e in enumerate(eps):
            d[s:] += e * d_v[:T - s]
    g = lambda n: d[:, ixd[n]]
    pi_next = np.append(g("pi")[1:], np.nan)
    exports = (p.alpha * p.gamma * (-g("tX")) if "tX" in ixd else p.alpha * p.gamma * (g("s") + g("psi")))
    return {"policy rate (pp a year)": 400 * g("i"), "headline inflation (pp a year)": 400 * g("pi"),
            "core inflation (pp a year)": 400 * g("pi_c"), "output (%)": 100 * g("y"), "consumption (%)": 100 * g("c"),
            "investment (%)": 100 * g("inv"), "real wage (%)": 100 * g("wr"),
            "real exchange rate (%)": 100 * g("q"), "real-rate gap (pp a year)": 400 * (g("i") - pi_next),
            "exports' part of output (pt)": 100 * exports}


def summary(p, oil):
    a, b = paths(p, oil), paths(p, oil, hold=4)
    yr = lambda x, n: float(np.nanmean(x[4 * n:4 * n + 4]))
    out = {"rule y1 output": yr(a["output (%)"], 0), "rule y2 output": yr(a["output (%)"], 1),
           "held y1 output": yr(b["output (%)"], 0), "held y2 output": yr(b["output (%)"], 1),
           "rule y1 headline": yr(a["headline inflation (pp a year)"], 0), "held y1 headline": yr(b["headline inflation (pp a year)"], 0),
           "rule y1 consumption": yr(a["consumption (%)"], 0), "rule y1 investment": yr(a["investment (%)"], 0),
           "rule y1 exports' part": yr(a["exports' part of output (pt)"], 0),
           "rule y1 policy rate": yr(a["policy rate (pp a year)"], 0)}
    out["cost y1"] = out["rule y1 output"] - out["held y1 output"]
    out["cost y2"] = out["rule y2 output"] - out["held y2 output"]
    link = {}
    for n, y in enumerate(YEARS):
        diff = lambda k: yr(a[k] - b[k], n)
        link[y] = {"output_gap_pct": diff("output (%)"), "real_fx_gap_pct": diff("real exchange rate (%)"),
                   "policy_rate_pp": diff("policy rate (pp a year)"), "inflation_pp": diff("headline inflation (pp a year)"),
                   "real_rate_gap_pp": diff("real-rate gap (pp a year)")}
    return out, link, a, b


def annual_response(oil_pct, file=None):
    """For the CGE link (as oil_policy_htmkwo.annual_response): the estimated rule MINUS the rate held, by year, at the posterior
    mean of the SMC particles."""
    X, name = particles(file)
    _, link, _, _ = summary(params(X.mean(0)), oil_pct / 100)
    return link, f"soe_{MODEL} SMC particles, posterior mean ({name})"


def main():
    oil = _arg("oil", 36.0, float) / 100
    ndraw = _arg("draws", 500, int)
    X, name = particles(_arg("file", None))
    mean = X.mean(0)
    pm = params(mean)
    s_mean, link, a, b = summary(pm, oil)
    rng = np.random.default_rng(27)
    idx = rng.choice(len(X), size=min(ndraw, len(X)), replace=False)
    rows, failed = [], 0
    for j in idx:
        try:
            s, _, _, _ = summary(params(X[j]), oil)
        except Exception:                                       # noqa: BLE001  (a draw that does not solve is skipped)
            failed += 1
            continue
        rows.append({n: X[j][ER.NAMES.index(n)] for n in ("theta", "theta_w") + tuple(
            n for n in ("iota_w", "theta_X") if n in ER.NAMES)} | s)
    D = pd.DataFrame(rows)
    beyond = D["rule y1 headline"] < 0
    keys = ["rule y1 output", "held y1 output", "rule y2 output", "cost y1", "cost y2", "rule y1 headline", "held y1 headline",
            "rule y1 consumption", "rule y1 investment", "rule y1 exports' part", "rule y1 policy rate"]

    def table(Dx):
        return pd.DataFrame({"draws: median": [Dx[k].median() for k in keys], "5%": [Dx[k].quantile(0.05) for k in keys],
                             "95%": [Dx[k].quantile(0.95) for k in keys],
                             "share below 0": [(Dx[k] < 0).mean() for k in keys]}, index=keys)

    dist = table(D)
    dist.insert(0, "posterior mean", [s_mean[k] for k in keys])
    dist_ok = table(D[~beyond]) if (~beyond).any() else None
    pmd = dict(zip(ER.NAMES, mean))
    extra = "".join(f", {n} {pmd[n]:.3f}" for n in ("iota_w", "theta_X") if n in pmd)
    Lk = pd.DataFrame(link)
    stamp = dt.datetime.now()
    L = [f"# The BSP's response to a {100 * oil:g}% oil supply shock in soe_{MODEL} ({stamp:%d %B %Y, %H:%M})", "",
         f"**NOT FOR CITATION** (research code, `research/dsge/oil_policy_dsge.py`, milestones 27-28). Posterior from `{name}` "
         f"({len(X):,} particles); posterior means: Calvo {pmd['theta']:.3f}, wage Calvo {pmd['theta_w']:.3f}{extra}; rho_o "
         f"{pmd['rho_o']:.3f}. Real oil price's supply component up {100 * oil:g}% (log), world output unchanged.", "",
         f"- **Year-1 output under the estimated rule: {s_mean['rule y1 output']:+.3f}% at the posterior mean; draws: median "
         f"{D['rule y1 output'].median():+.3f}% (5-95%: {D['rule y1 output'].quantile(0.05):+.3f} to "
         f"{D['rule y1 output'].quantile(0.95):+.3f}), {100 * (D['rule y1 output'] < 0).mean():.0f}% of {len(D)} draws below "
         f"zero** ({failed} draws did not solve).",
         f"- With the rate held for a year: {s_mean['held y1 output']:+.3f}%.",
         f"- **Output cost of the BSP's response** (rule minus held): year 1 {s_mean['cost y1']:+.3f}%, year 2 "
         f"{s_mean['cost y2']:+.3f}% at the mean; draws: year 1 median {D['cost y1'].median():+.3f}% (5-95%: "
         f"{D['cost y1'].quantile(0.05):+.3f} to {D['cost y1'].quantile(0.95):+.3f}).",
         f"- Headline inflation, year 1: {s_mean['rule y1 headline']:+.2f} pp a year under the rule (at the mean). Exports' part "
         f"of year-1 output {s_mean['rule y1 exports\' part']:+.3f} pt.",
         f"- **Pole check:** {int(beyond.sum())} of {len(D)} draws ({100 * beyond.mean():.1f}%) have the oil supply shock LOWERING "
         "year-1 headline inflation (beyond the solution's pole; not credible)." , "",
         "## Year-1 and year-2 quantities: posterior mean and over draws", "", dist.to_markdown(floatfmt=".3f"), ""]
    if dist_ok is not None and beyond.any():
        L += ["## The same over the draws on the credible side of the pole only", "", dist_ok.to_markdown(floatfmt=".3f"), ""]
    L += ["## The CGE link's inputs (estimated rule minus the rate held, by year; posterior mean)", "",
          Lk.to_markdown(floatfmt=".3f"), "", "## Quarterly paths under the estimated rule (posterior mean)", "",
          pd.DataFrame({k: v[:8] for k, v in a.items()}, index=[f"q{t + 1}" for t in range(8)]).T.to_markdown(floatfmt=".3f")]
    path = OUT / f"dsge_oil_policy_{stamp:%Y%m%d_%H%M}_{MODEL}_long_stl_inv{TAGS}.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:10])); print(dist.to_string(float_format=lambda v: f"{v:.3f}")); print("saved", path)


if __name__ == "__main__":
    main()
