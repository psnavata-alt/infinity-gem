"""DSGE research, milestone 26 (24 Oct 2026): the BSP's response to the 2026-sized oil SUPPLY shock in the sticky-wage capital
DSGE with oil (soe_htmkwo.py), as research/dsge/oil_policy.py does for the oil models (oil_policy.py accepts only soe_oil, oilu,
oilw and oilf, and reads Metropolis chains by name; this file reads an SMC particle cloud). NOT FOR CITATION; research only.

A real oil-price rise of oil % (log; its supply component, world output unchanged), under three policies:
1. the estimated rule (headline CPI inflation, as the BSP targets);
2. a core-inflation rule (same coefficients on the sticky core);
3. the policy rate held at its baseline for four quarters by policy surprises (Leeper and Zha 2003), then the rule.
The output cost of the BSP's response is 1 minus 3 (year-1 and year-2 averages), as in oil_policy.py; the annual differences of
1 and 3 (output, real exchange rate, policy rate, inflation, real-rate gap) are what scenarios/qpm_cge_link.py's dsge_oil_annual
feeds the CGE link (annual_response() below, used by scenarios/bsp_oil_response_netting_htmkwo.py).
Two readings: at the posterior MEAN (oil_policy.py's convention, comparable with 20-23 Oct) and over posterior DRAWS (median and
5-95% of each quantity across particles; a quantity of the mean is not the mean of the quantity in a nonlinear model).
Run (research/dsge):  py -I -X utf8 oil_policy_htmkwo.py [oil=36] [file=<particles .npy in outputs/>] [draws=500]
      (default file: the newest outputs/dsge_smc_*_htmkwo_w1_ratio2_long_stl_inv_*_particles.npy; writes
      outputs/dsge_oil_policy_<stamp>_htmkwo_long_stl_inv.md)
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
OUT = HERE.parents[1] / "outputs"
T = 12
YEARS = (2026, 2027)

_saved = sys.argv
sys.argv = ["oil_policy_htmkwo", "model=htmkwo", "prior=ratio2", "sample=long", "gdp=stl", "obs=inv"]
import estimate_rot as ER   # noqa: E402  (names, fixed calibration of model=htmkwo obs=inv)
sys.argv = _saved
import soe_htmkwo as Oil    # noqa: E402


def _arg(name, default, cast=str):
    return next((cast(a.split("=", 1)[1]) for a in sys.argv[1:] if a.startswith(f"{name}=")), default)


def particles(file=None):
    if file is None:
        files = sorted(OUT.glob("dsge_smc_*_htmkwo_w1_ratio2_long_stl_inv_*_particles.npy"))
        if not files:
            raise SystemExit("no soe_htmkwo SMC particles in outputs/")
        f = files[-1]
    else:
        f = OUT / file
    X = np.load(f)
    if X.shape[1] != len(ER.NAMES):
        raise SystemExit(f"{f.name}: {X.shape[1]} columns, model=htmkwo obs=inv has {len(ER.NAMES)}")
    return X, f.name


def params(theta, **extra):
    kw = {k: v for k, v in zip(ER.NAMES, theta) if not k.startswith("sd_") and k != "me_inv"}
    return Oil.Params(rule="output", **{**kw, **ER.FIXED, **extra})


def paths(p, size, hold=0):
    """Responses to an oil-supply shock of `size` (log); hold = quarters the policy rate is held at baseline by surprises
    (the same construction as oil_policy.paths)."""
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
    return {"policy rate (pp a year)": 400 * g("i"), "headline inflation (pp a year)": 400 * g("pi"),
            "core inflation (pp a year)": 400 * g("pi_c"), "output (%)": 100 * g("y"), "consumption (%)": 100 * g("c"),
            "investment (%)": 100 * g("inv"), "real wage (%)": 100 * g("wr"),
            "real exchange rate (%)": 100 * g("q"), "real-rate gap (pp a year)": 400 * (g("i") - pi_next)}


def summary(p, oil):
    """Year-1 and year-2 averages under the rule and with the rate held; the BSP's cost; the CGE link's inputs by year."""
    a, b = paths(p, oil), paths(p, oil, hold=4)
    yr = lambda x, n: float(np.nanmean(x[4 * n:4 * n + 4]))
    out = {"rule y1 output": yr(a["output (%)"], 0), "rule y2 output": yr(a["output (%)"], 1),
           "held y1 output": yr(b["output (%)"], 0), "held y2 output": yr(b["output (%)"], 1),
           "rule y1 headline": yr(a["headline inflation (pp a year)"], 0), "held y1 headline": yr(b["headline inflation (pp a year)"], 0),
           "rule y1 consumption": yr(a["consumption (%)"], 0), "rule y1 investment": yr(a["investment (%)"], 0),
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
    """For the CGE link (as scenarios/qpm_cge_link.dsge_oil_annual): the estimated rule MINUS the rate held, by year, at the
    posterior mean of the SMC particles."""
    X, name = particles(file)
    _, link, _, _ = summary(params(X.mean(0)), oil_pct / 100)
    return link, f"soe_htmkwo SMC particles, posterior mean ({name})"


def main():
    oil = _arg("oil", 36.0, float) / 100
    ndraw = _arg("draws", 500, int)
    X, name = particles(_arg("file", None))
    mean = X.mean(0)
    pm = params(mean)
    s_mean, link, a, b = summary(pm, oil)
    core = paths(params(mean, rule_infl="core"), oil)
    rng = np.random.default_rng(26)
    idx = rng.choice(len(X), size=min(ndraw, len(X)), replace=False)
    rows = []
    for j in idx:
        try:
            s, _, _, _ = summary(params(X[j]), oil)
        except Exception:                                       # noqa: BLE001  (a draw that does not solve is skipped)
            continue
        rows.append({"theta": X[j][ER.NAMES.index("theta")], **s})
    D = pd.DataFrame(rows)
    keys = ["rule y1 output", "held y1 output", "rule y2 output", "cost y1", "cost y2", "rule y1 headline", "held y1 headline",
            "rule y1 consumption", "rule y1 investment", "rule y1 policy rate"]
    dist = pd.DataFrame({"posterior mean": [s_mean[k] for k in keys], "draws: median": [D[k].median() for k in keys],
                         "5%": [D[k].quantile(0.05) for k in keys], "95%": [D[k].quantile(0.95) for k in keys],
                         "share of draws below 0": [(D[k] < 0).mean() for k in keys]}, index=keys)
    runs = {"estimated rule (headline)": a, "core-inflation rule": core, "rate held for 4 quarters": b}
    ann, qrows = {}, []
    for nm, r in runs.items():
        for var, x in r.items():
            ann[(nm, var)] = {"year 1": float(np.nanmean(x[:4])), "year 2": float(np.nanmean(x[4:8]))}
            qrows.append({"policy": nm, "variable": var, **{f"q{t + 1}": x[t] for t in range(8)}})
    A = pd.DataFrame(ann).T
    A.index.names = ["policy", "variable"]
    Q = pd.DataFrame(qrows).set_index(["variable", "policy"]).sort_index(level=0, sort_remaining=False)
    Lk = pd.DataFrame(link)
    stamp = dt.datetime.now()
    pmd = dict(zip(ER.NAMES, mean))
    L = [f"# The BSP's response to a {100 * oil:g}% oil supply shock in the sticky-wage capital DSGE with oil "
         f"({stamp:%d %B %Y, %H:%M})", "",
         f"**NOT FOR CITATION** (research code, `research/dsge/oil_policy_htmkwo.py`, milestone 26). Model `soe_htmkwo.py` "
         f"(soe_htmkw's sticky wages and capital, plus soe_oilf's oil block); posterior from `{name}` ({len(X):,} particles); "
         f"the Calvo parameter ESTIMATED (posterior mean {pmd['theta']:.3f}; wage Calvo {pmd['theta_w']:.3f}). Real oil price's "
         f"supply component up {100 * oil:g}% (log), world output unchanged; persistence rho_o {pmd['rho_o']:.3f}.", "",
         f"- **Year-1 output under the estimated rule: {s_mean['rule y1 output']:+.3f}% at the posterior mean; draws: median "
         f"{D['rule y1 output'].median():+.3f}% (5-95%: {D['rule y1 output'].quantile(0.05):+.3f} to "
         f"{D['rule y1 output'].quantile(0.95):+.3f}), {100 * (D['rule y1 output'] < 0).mean():.0f}% of {len(D)} draws below "
         "zero.**",
         f"- With the rate held for a year: {s_mean['held y1 output']:+.3f}% (draws: median {D['held y1 output'].median():+.3f}%).",
         f"- **Output cost of the BSP's response** (rule minus held): year 1 {s_mean['cost y1']:+.3f}%, year 2 "
         f"{s_mean['cost y2']:+.3f}% at the mean; draws: year 1 median {D['cost y1'].median():+.3f}% (5-95%: "
         f"{D['cost y1'].quantile(0.05):+.3f} to {D['cost y1'].quantile(0.95):+.3f}), year 2 {D['cost y2'].median():+.3f}%.",
         f"- Headline inflation, year 1: {s_mean['rule y1 headline']:+.2f} pp a year under the rule, "
         f"{s_mean['held y1 headline']:+.2f} with the rate held (at the mean).", "",
         "## Year-1 and year-2 quantities: posterior mean and over draws", "", dist.to_markdown(floatfmt=".3f"), "",
         "## The CGE link's inputs (estimated rule minus the rate held, by year; posterior mean)", "", Lk.to_markdown(floatfmt=".3f"), "",
         "## Annual averages (posterior mean)", "", A.to_markdown(floatfmt=".3f"), "",
         "## Quarterly paths (posterior mean)", "", Q.to_markdown(floatfmt=".3f")]
    path = OUT / f"dsge_oil_policy_{stamp:%Y%m%d_%H%M}_htmkwo_long_stl_inv.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:12])); print(dist.to_string(float_format=lambda v: f"{v:.3f}")); print("saved", path)


if __name__ == "__main__":
    main()
