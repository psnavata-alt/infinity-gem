"""DSGE research, milestone 17a (19 Oct 2026, about 3:05 PM): the BSP's response to an oil shock in the estimated DSGE.

Model: soe_oil.py at the posterior mean of milestone 16 (outputs/dsge_ph_oil_draws_*_w1_ratio.npy; calibrated a_o 0.037,
s_o 0.030, eps_o 0.2). A 10% rise in the real oil price (AR(1), the estimated persistence), under three policies:
1. the estimated rule (headline CPI inflation, as the BSP targets);
2. a core-inflation rule (same coefficients on core inflation): the Blanchard-Gali alternative;
3. the policy rate held at its baseline for four quarters by policy surprises (Leeper and Zha 2003), then the rule: what the
   oil shock does without the BSP's first-year response.
The difference 1 - 3 is the part of the output loss caused by the BSP's tightening. Reports quarterly paths and the annual
averages (year 1 and year 2) that feed the CGE link (output gap, real-rate gap, real exchange rate, inflation).
Run:  py oil_policy.py [oil=10] [spec=_long_stl]       (writes outputs/dsge_oil_policy_<stamp><spec>.md)
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
# 20 Oct 2026: model=oilu (milestone 19b: the oil model with the cost-push shock) or model=oilw (milestone 21: oil supply
# separated from world oil demand; the shock here is then a pure oil SUPPLY shock, world output unchanged); default model=oil
_M = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("model=")), "oil")   # 21 Oct 2026: model=oilf (milestone 22) too
if _M not in ("oil", "oilu", "oilw", "oilf"):
    raise SystemExit("model must be oil, oilu, oilw or oilf")
_OILU = _M == "oilu"
sys.argv = [a for a in sys.argv if not a.startswith("model=")] + [f"model={_M}"]
import estimate_rot as ER   # noqa: E402  (model=oil: names, fixed calibration)
if _M == "oilw":
    import soe_oilw as Oil  # noqa: E402
elif _M == "oilf":
    import soe_oilf as Oil  # noqa: E402
elif _OILU:
    import soe_oilu as Oil  # noqa: E402
else:
    import soe_oil as Oil   # noqa: E402

OUT = HERE.parents[1] / "outputs"
T = 12


def posterior_mean_params(spec=""):
    """Posterior mean pooled over every chain of milestone 16 (19 Oct, 3:47 PM: three chains, largest R-hat 1.054). spec (milestone
    18b): "" = those chains (2002-2019, unadjusted GDP); "_long_stl" = 2002-2026 with STL-adjusted GDP; "_stl", "_long" likewise.
    src=smc (21 Oct 2026): the newest SMC particle cloud of the same specification (research/dsge/smc.py) instead of the chains."""
    if any(a == "src=smc" for a in sys.argv[1:]):
        files = sorted(OUT.glob(f"dsge_smc_*_{ER.MODEL}_w1_ratio{spec}_n*_particles.npy"))[-1:]
        if not files:
            raise SystemExit(f"no SMC particles for dsge_smc_*_{ER.MODEL}_w1_ratio{spec}_n*_particles.npy")
    else:
        files = [f for f in sorted(OUT.glob(f"dsge_ph_{ER.MODEL}_draws_*_w1_ratio{spec}*.npy"))
                 if all((f"_{t}" in f.stem) == (f"_{t}" in spec) for t in ("long", "stl", "thfix", "thhi", "igrea"))]   # 20 Oct: theta and world-demand tags too
    D = np.vstack([np.load(f) for f in files])
    kw = {k: v for k, v in zip(ER.NAMES, D.mean(0)) if not k.startswith("sd_")}
    return {**kw, **ER.FIXED}, f"{len(files)} chains pooled ({', '.join(f.name for f in files)})"


def paths(p, size, hold=0):
    """Responses to an oil shock of `size` (log); hold = quarters the policy rate is held at baseline by surprises."""
    sol, _ = Oil.solve(p)
    ixk = {n: j for j, n in enumerate(Oil.STATES)}
    ixd = {n: j for j, n in enumerate(Oil.JUMPS)}
    e_o = np.zeros(len(Oil.STATES)); e_o[ixk["o"]] = size
    e_v = np.zeros(len(Oil.STATES)); e_v[ixk["v"]] = 1.0
    _, d_o = sol.irf(np.eye(len(Oil.STATES)), e_o, T=T)
    _, d_v = sol.irf(np.eye(len(Oil.STATES)), e_v, T=T)
    d = d_o.copy()
    if hold:                                               # surprises e_t (t < hold) that keep i_t = 0 for t < hold
        M = np.array([[d_v[t - s, ixd["i"]] if t >= s else 0.0 for s in range(hold)] for t in range(hold)])
        eps = np.linalg.solve(M, -d_o[:hold, ixd["i"]])
        for s, e in enumerate(eps):
            d[s:] += e * d_v[:T - s]
    g = lambda n: d[:, ixd[n]]
    pi_next = np.append(g("pi")[1:], np.nan)
    return {"policy rate (pp a year)": 400 * g("i"), "headline inflation (pp a year)": 400 * g("pi"),
            "core inflation (pp a year)": 400 * g("pi_c"), "output (%)": 100 * g("y"), "consumption (%)": 100 * g("c"),
            "real exchange rate (%)": 100 * g("q"), "real-rate gap (pp a year)": 400 * (g("i") - pi_next)}


def main():
    oil = next((float(a.split("=", 1)[1]) for a in sys.argv[1:] if a.startswith("oil=")), 10.0) / 100
    spec = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("spec=")), "")   # e.g. spec=_long_stl (milestone 18b)
    kw, src = posterior_mean_params(spec)
    runs = {"estimated rule (headline)": paths(Oil.Params(rule="output", **kw), oil),
            "core-inflation rule": paths(Oil.Params(rule="output", **{**kw, "rule_infl": "core"}), oil),
            "rate held for 4 quarters": paths(Oil.Params(rule="output", **kw), oil, hold=4)}
    rows, ann = [], {}
    for name, r in runs.items():
        for var, x in r.items():
            rows.append({"policy": name, "variable": var, **{f"q{t + 1}": x[t] for t in range(8)}})
            ann[(name, var)] = {"year 1": float(np.nanmean(x[:4])), "year 2": float(np.nanmean(x[4:8]))}
    Q = pd.DataFrame(rows).set_index(["variable", "policy"]).sort_index(level=0, sort_remaining=False)
    A = pd.DataFrame(ann).T
    A.index.names = ["policy", "variable"]
    cost = {y: ann[("estimated rule (headline)", "output (%)")][y] - ann[("rate held for 4 quarters", "output (%)")][y]
            for y in ("year 1", "year 2")}
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    L = [f"# The BSP's response to a {100 * oil:g}% oil-price rise in the estimated DSGE ({dt.datetime.now():%d %B %Y, %H:%M})", "",
         f"**NOT FOR CITATION** (research code, `research/dsge/oil_policy.py`). Model soe_{_M}.py at the posterior mean of `{src}` "
         f"({'milestone 21: an oil SUPPLY shock, world output unchanged' if _M == 'oilw' else 'milestone 16'}). Real oil price up "
         f"{100 * oil:g}% (persistence {kw['rho_o']:.2f}).", "",
         f"- **Output cost of the BSP's response** (estimated rule minus the rate held for a year): year 1 {cost['year 1']:+.3f}%, "
         f"year 2 {cost['year 2']:+.3f}% of output.", "",
         "## Annual averages (inputs for the CGE link)", "", A.to_markdown(floatfmt=".3f"), "",
         "## Quarterly paths", "", Q.to_markdown(floatfmt=".3f")]
    path = OUT / f"dsge_oil_policy_{stamp}{'' if _M == 'oil' else '_' + _M}{spec}{'_smc' if any(a == 'src=smc' for a in sys.argv[1:]) else ''}.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:8])); print(A.to_string(float_format=lambda v: f"{v:.3f}")); print("saved", path)


if __name__ == "__main__":
    main()
