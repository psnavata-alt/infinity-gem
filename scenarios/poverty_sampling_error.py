"""Sampling error of the poverty counts (16 Oct 2026).

NOT FOR CITATION until reviewed. Run:  py scenarios/poverty_sampling_error.py   (a few minutes; 1,000 bootstrap replicates)

The poverty counts come from PSA's FIES 2023 public-use file (163,268 families), a sample, so every count has a margin of
error. This script measures it for the baseline count and for the combined run's "new poor" (central run of
scenarios/combined_revised.py: public capital low, central wage curve, family inflation reconciled to the SAM).

Design: the FIES is a stratified multi-stage sample. In the public-use file a primary sampling unit is identified by
province (W_PROV) and RPSU (RPSU numbers repeat across provinces); strata are taken as province x urban/rural (171
strata), which follows the sample's domains (PSA's exact strata are not in the public file; this is an approximation,
stated in the report). Bootstrap: Rao and Wu (1988) rescaling bootstrap with n_h - 1 PSUs drawn with replacement in each
stratum h and weights rescaled by n_h / (n_h - 1) times the number of draws (Rao, Wu and Yue 1992); the one stratum with a
single PSU keeps its weights. Each replicate recomputes the poor persons before and after the shock with the SAME
household-level incomes and prices (the model's results are held fixed): the bands are sampling error only, not model
uncertainty.
"""
import sys

import numpy as np
import pandas as pd

from _common import Report, ROOT
from combined_revised import Runs, SHOCKS

sys.path.insert(0, str(ROOT))
from infinity_gem import paths  # noqa: E402

REPS, SEED = 1000, 20261016


def psu_tables(R, ref, sim, years=(2026, 2027)):
    """Household-level poor flags before and after (recommended method), returned with the design variables."""
    ml, f = R.ml, R.ml.hd.f
    d = pd.read_csv(paths.FIES_PUF, usecols=["W_PROV", "RPSU", "URB", "SEQ_NO"])
    assert len(d) == len(f) and (d["W_PROV"].values == f["W_PROV"].values).all() and (d["SEQ_NO"].values == f["SEQ_NO"].values).all()
    out = pd.DataFrame({"psu": d["W_PROV"].astype(str) + "_" + d["RPSU"].astype(str),
                        "stratum": d["W_PROV"].astype(str) + "_" + d["URB"].astype(str),
                        "w": f["MEM_RFACT"].values, "poor0": (f["PCI"] < f["PLINE"]).values})
    point = {}
    for y in years:
        link = ml.link_variables(R.d.ms, ref.solutions[y], sim.solutions[y])
        pi = ml.family_inflation(link)
        g = link["_g"]
        eh = f["grp"].map(g["real_factor"] * (1 + g["inflation_pct"] / 100)).fillna(1.0)
        pci = f["PCI"] * eh / (1 + pi / 100)
        out[f"poor{y}"] = (pci < f["PLINE"]).values
        point[y] = float(ml.poverty(link, pi).loc["Poor persons", "Change"])
    return out, point


def bootstrap(t, years, reps=REPS, seed=SEED):
    rng = np.random.default_rng(seed)
    cols = {"poor0": "poor0", **{f"poor{y}": f"poor{y}" for y in years}}
    agg = t.assign(**{k: t["w"] * t[c] for k, c in cols.items()}).groupby(["stratum", "psu"])[list(cols)].sum()
    strata = agg.index.get_level_values(0)
    groups = {s: np.where(strata == s)[0] for s in pd.unique(strata)}
    vals = agg.to_numpy()
    draws = np.zeros((reps, vals.shape[1]))
    for r in range(reps):
        mult = np.ones(len(agg))
        for s, ix in groups.items():
            n = len(ix)
            if n < 2:
                continue
            pick = rng.integers(0, n, n - 1)
            cnt = np.bincount(pick, minlength=n)
            mult[ix] = cnt * n / (n - 1)
        draws[r] = mult @ vals
    return pd.DataFrame(draws, columns=list(cols)), agg


def main():
    cal = pd.read_csv(__import__("_common").calibration_file(), index_col=0)
    R = Runs("low", wage_curve=float(cal.loc["central (e)", "beta"]))
    piece, _ = R.pieces()
    ref, sim = R.run(set(), piece=piece), R.run(set(SHOCKS), piece=piece)
    years = (2026, 2027)
    t, point = psu_tables(R, ref, sim, years)
    full = {c: float((t["w"] * t[c]).sum()) for c in ["poor0"] + [f"poor{y}" for y in years]}
    dr, agg = bootstrap(t, years)
    rows = {}
    rows["poor persons, FIES 2023 baseline"] = (full["poor0"], dr["poor0"])
    for y in years:
        rows[f"new poor {y} (four shocks)"] = (full[f"poor{y}"] - full["poor0"], dr[f"poor{y}"] - dr["poor0"])
    tab = pd.DataFrame({k: {"estimate (M)": v / 1e6, "standard error (M)": d.std() / 1e6,
                            "90% low (M)": np.percentile(d, 5) / 1e6, "90% high (M)": np.percentile(d, 95) / 1e6,
                            "coefficient of variation (%)": d.std() / abs(v) * 100} for k, (v, d) in rows.items()}).T
    rep = Report("Sampling error of the poverty counts (FIES 2023; Infinity GEM 0.3.7)", "poverty_sampling_error")
    rep.p(f"**NOT FOR CITATION until reviewed**. Rao-Wu rescaling bootstrap, {REPS} replicates, seed {SEED}; "
          f"{agg.index.get_level_values(1).nunique():,} primary sampling units (province x RPSU) in "
          f"{agg.index.get_level_values(0).nunique()} strata (province x urban/rural; an approximation of PSA's design). "
          "Model results held fixed: the bands are SAMPLING error only. Central combined run (public capital low, central wage curve).")
    rep.table(tab, floatfmt=".3f")
    rep.p(f"Check: the new-poor point estimates equal the combined run's ({', '.join(f'{y}: {point[y] / 1e6:.3f} M' for y in years)}). "
          "Compare the baseline's coefficient of variation with PSA's published one for the 2023 poor population (PSA, 2023 Full Year "
          "Official Poverty Statistics, Table of CVs): the approximate strata should give a similar size.")
    rep.save()
    print(tab.round(3).to_string())
    print({y: point[y] / 1e6 for y in years}, {y: (full[f"poor{y}"] - full["poor0"]) / 1e6 for y in years})


if __name__ == "__main__":
    main()
