"""DSGE research, milestone 29 (12 Nov 2026): the DSGE candidates against the data's oil-supply responses (oil_supply_lp.py),
on the SAME objects: cumulative responses of real GDP, real exports, the CPI level, the peso (PHP per USD) and the policy rate,
year-1 (h 0-3) and year-2 (h 4-7) averages, per 10% impact rise in the dollar oil price. Research only; NOT FOR CITATION.

DSGE side: an oil SUPPLY innovation (world output unchanged) of 10% on impact, at the posterior mean of each model's newest SMC
particles (or a named file), and over 300 particles (median, 5-95%). Objects: real GDP = y; real exports = gamma x (relative
price) + ystar (gamma (s + psi) under producer-currency pricing, gamma (-tX) under dollar pricing); CPI level = the cumulative sum
of pi; peso = the cumulative sum of de; policy rate = 400 i (pp a year). The dollar oil price = o + p*, so with world inflation
unchanged a 10% oil supply innovation is a 10% impact rise, as the data's normalisation.
Data side: the newest outputs/dsge_oil_supply_lp_*.md is not parsed; the year averages are recomputed here with oil_supply_lp.lp
for both samples, with the plain 90% bands of the year averages (Newey-West, scaled by the impact oil response).
A score: for each object and year, (DSGE - data) / data s.e.; the sum of squares over the 10 entries (lower is closer). It is a
descriptive check, not a test: the data's errors are correlated across objects and years.
Run (research/dsge):  py -I -X utf8 compare_oil_lp.py [models=htmkwo,htmkwoi,htmkwod,htmkwod:oillp] [draws=300]
      (model:tag reads the run with that extra tag, e.g. htmkwod:oillp = estimate_rot's oil system prior, milestone 30; a model
      without a tag reads only untagged runs)
      (a model with no SMC particles yet is shown at milestone 26's posterior mean with its new parameters at the profile values
      iota_w 0, theta_X 0.75, marked "profile"); writes outputs/dsge_compare_oil_lp_<stamp>.md
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
import oil_supply_lp as LP  # noqa: E402

OBJ = ["real GDP", "real exports", "CPI", "PHP per USD", "policy rate"]


def _arg(name, default, cast=str):
    return next((cast(a.split("=", 1)[1]) for a in sys.argv[1:] if a.startswith(f"{name}=")), default)


def spec(model):
    saved = sys.argv
    sys.argv = ["x", f"model={model}", "prior=ratio2", "sample=long", "gdp=stl", "obs=inv"]
    import estimate_rot as ER
    ER = importlib.reload(ER)
    sys.argv = saved
    return list(ER.NAMES), dict(ER.FIXED), importlib.import_module(f"soe_{model}")


def responses(M, p, T=8):
    sol, _ = M.solve(p)
    ixk = {n: j for j, n in enumerate(M.STATES)}
    ixd = {n: j for j, n in enumerate(M.JUMPS)}
    e = np.zeros(len(M.STATES)); e[ixk["o"]] = 0.10
    k, d = sol.irf(np.eye(len(M.STATES)), e, T=T)
    g = lambda n: d[:, ixd[n]] if n in ixd else k[:, ixk[n]]
    rel = -g("tX") if "tX" in ixd else g("s") + g("psi")
    r = {"real GDP": 100 * g("y"), "real exports": 100 * (p.gamma * rel + g("ystar")), "CPI": 100 * np.cumsum(g("pi")),
         "PHP per USD": 100 * np.cumsum(g("de")), "policy rate": 400 * g("i")}
    return {o: (float(v[:4].mean()), float(v[4:8].mean())) for o, v in r.items()}


def model_rows(entry, ndraw, rng):
    model, _, tag = entry.partition(":")                        # milestone 30: "htmkwod:oillp" = the run with the oil prior
    names, fixed, M = spec(model)
    files = sorted(OUT.glob(f"dsge_smc_*_{model}_w1_ratio2_long_stl_inv{'_' + tag if tag else ''}_n*_particles.npy"))
    if tag and not files:
        raise SystemExit(f"no soe_{model} SMC particles tagged {tag} in outputs/")
    if files:
        X = np.load(files[-1]); src = files[-1].name; label = f"soe_{model}{' + ' + tag if tag else ''} (SMC)"
    else:                                                       # profile: milestone 26's particles plus the new parameters
        names0, _, _ = spec("htmkwo")
        P = np.load(sorted(OUT.glob("dsge_smc_*_htmkwo_w1_ratio2_long_stl_inv_n*_particles.npy"))[-1])
        prof = {"iota_w": 0.0, "theta_X": 0.75}
        X = np.column_stack([P[:, names0.index(n)] if n in names0 else np.full(len(P), prof[n]) for n in names])
        src = "milestone 26 particles + iota_w 0, theta_X 0.75"; label = f"soe_{model} (profile)"

    def par(th):
        kw = {k: v for k, v in zip(names, th) if not k.startswith("sd_") and k != "me_inv"}
        return M.Params(rule="output", **{**kw, **fixed})

    mean = responses(M, par(X.mean(0)))
    draws = []
    for j in rng.choice(len(X), size=min(ndraw, len(X)), replace=False):
        try:
            draws.append(responses(M, par(X[j])))
        except Exception:                                       # noqa: BLE001
            pass
    return label, src, mean, draws


def main():
    models = _arg("models", "htmkwo,htmkwoi,htmkwod").split(",")
    ndraw = _arg("draws", 300, int)
    rng = np.random.default_rng(29)
    df = LP.data()
    data = {}
    for lab, (sheet, a, b, drop) in {"data 2002-2019": ("Monthly (pre-Covid)", "2002Q1", "2019Q4", None),
                                     "data 2002-2025 ex COVID": ("Monthly", "2002Q1", "2025Q4", LP.ph_data.COVID)}.items():
        shk = LP.shock_q(sheet)
        res = {v: LP.lp(df, shk, v, a, b, drop) for v in OBJ + ["Dubai crude (USD)"]}
        sc = 10.0 / res["Dubai crude (USD)"][0, 0]
        data[lab] = {o: tuple((sc * res[o][4 * y:4 * y + 4, 0].mean(), sc * res[o][4 * y:4 * y + 4, 1].mean()) for y in (0, 1))
                     for o in OBJ}
    rows, scores, srcs = [], {}, []
    for lab, d in data.items():
        rows.append({"source": lab, **{f"{o}, y{y + 1}": f"{d[o][y][0]:+.2f} ({d[o][y][1]:.2f})" for o in OBJ for y in (0, 1)}})
    for m in models:
        label, src, mean, draws = model_rows(m, ndraw, rng)
        srcs.append(f"- {label}: `{src}`; {len(draws)} draws")
        med = {o: tuple(np.median([dr[o][y] for dr in draws]) for y in (0, 1)) for o in OBJ}
        rows.append({"source": f"{label}, posterior mean", **{f"{o}, y{y + 1}": f"{mean[o][y]:+.2f}" for o in OBJ for y in (0, 1)}})
        rows.append({"source": f"{label}, draws median [5%, 95%]", **{
            f"{o}, y{y + 1}": f"{med[o][y]:+.2f} [{np.percentile([dr[o][y] for dr in draws], 5):+.2f}, "
                              f"{np.percentile([dr[o][y] for dr in draws], 95):+.2f}]" for o in OBJ for y in (0, 1)}})
        for dl, d in data.items():
            scores[(label, dl)] = sum(((mean[o][y] - d[o][y][0]) / d[o][y][1]) ** 2 for o in OBJ for y in (0, 1))
    T = pd.DataFrame(rows).set_index("source").T
    S = pd.Series(scores).unstack()
    stamp = dt.datetime.now()
    L = [f"# DSGE candidates against the data's oil-supply responses ({stamp:%d %B %Y, %H:%M})", "",
         "**NOT FOR CITATION** (research code, `research/dsge/compare_oil_lp.py`, milestone 29). Year-1 (h 0-3) and year-2 (h 4-7) "
         "averages of cumulative responses, per 10% impact rise in the dollar oil price; % (policy rate: pp a year). Data: "
         "local projections on Känzig's (2021) oil supply news shock (oil_supply_lp.py), point estimate (s.e.).", "", *srcs, "",
         T.to_markdown(), "", "## Score: sum over the 10 entries of ((DSGE posterior mean - data) / data s.e.)^2 (lower = closer)", "",
         S.to_markdown(floatfmt=".1f")]
    path = OUT / f"dsge_compare_oil_lp_{stamp:%Y%m%d_%H%M}.md"
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L)); print("saved", path)


if __name__ == "__main__":
    main()
