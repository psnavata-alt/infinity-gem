"""Pipeline (d): the stochastic outlook with and without the opt-in typhoon draw (23 Oct 2026). RESEARCH, NOT FOR CITATION.

Runs infinity_gem.stochastic.StochasticCGE twice on the same seed and the same dynamic model: once as published (no disaster
draw) and once with DisasterDraw.from_data() (PAGASA/NDRRMC damage data; centred on a normal year; entered as decided in
). The external draws are identical in both runs (the typhoon draw has its own random stream; checked
below), so the paired difference per draw is the typhoon draw's own contribution. Also: single bad seasons (the model's
1-in-10, 1-in-20 and 1-in-100 seasons) in 2027 with no external shock, to show the size of one typhoon year in the model.
Writes only its own files: outputs/stochastic_outlook_disasters_comparison_<stamp>.md and _draws.csv, _shocks.csv.

Run:  py validation/stochastic_disasters/compare_outlook_with_without.py [draws, default 200] [--setting=0.2]
      default settings: '0.3 recommended' with public capital low (as outputs/stochastic_outlook_03settings_20261016.md),
      where infrastructure damage enters as public capital destroyed; --setting=0.2: the published settings, where it
      enters as a one-year productivity loss of the same first-year size (no public capital in those settings).
"""
import datetime as dt
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scenarios"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np                                    # noqa: E402
import pandas as pd                                   # noqa: E402

from _common import SAM_GDP_2023, PSA_GDP             # noqa: E402
from infinity_gem.dynamic import DynamicCGE               # noqa: E402
from infinity_gem import stochastic as SC                 # noqa: E402

N = next((int(a) for a in sys.argv[1:] if a.isdigit()), 200)
S02 = "--setting=0.2" in sys.argv
SEED = 20261014                                       # the published outlook's seed
CUM = "cumulative GDP gap ₱ bn (SAM year prices)"
TO25 = PSA_GDP[2025] / SAM_GDP_2023


def main():
    t0 = time.time()
    d = SC.load_task1_monthly()
    fx = float(d["fx"].dropna().iloc[-12:].mean())
    if S02:
        dyn, setting = DynamicCGE(), "published (0.2) settings"
    else:
        from infinity_gem.settings import dynamic_kwargs
        dyn, setting = DynamicCGE(**dynamic_kwargs("0.3 recommended", public_capital="low")), "'0.3 recommended', public capital low"
    dyn.baseline()
    dd = SC.DisasterDraw.from_data()
    st0 = SC.StochasticCGE(dyn, d, php_per_usd=fx, oil="history")
    st1 = SC.StochasticCGE(dyn, d, php_per_usd=fx, oil="history", disasters=dd)
    r0 = st0.run(n=N, seed=SEED)
    print(f"without: {time.time() - t0:.0f} s", flush=True)
    r1 = st1.run(n=N, seed=SEED)
    print(f"with: {time.time() - t0:.0f} s", flush=True)
    ext = ["oil_pct", "remit_pct", "fdi_usd_m"]
    same_ext = float((r1.shocks[ext] - r0.shocks[ext]).abs().to_numpy().max())

    def add25(df):
        df = df.copy()
        df["cumulative GDP gap ₱ bn (2025 pesos)"] = df[CUM] * TO25
        return df.drop(columns=[CUM])

    d0, d1 = add25(r0.draws), add25(r1.draws)
    diff = d1 - d0
    cum25 = "cumulative GDP gap ₱ bn (2025 pesos)"
    tab = pd.DataFrame({"without: mean": d0.mean(), "with: mean": d1.mean(),
                        "without: p05": d0.quantile(0.05), "with: p05": d1.quantile(0.05),
                        "without: p50": d0.quantile(0.5), "with: p50": d1.quantile(0.5),
                        "without: p95": d0.quantile(0.95), "with: p95": d1.quantile(0.95),
                        "without: sd": d0.std(), "with: sd": d1.std()})
    dtab = SC.summarise(diff).assign(sd=diff.std())
    probs = {}
    for lab, dr in (("without", d0), ("with", d1)):
        p = {f"cumulative loss larger than ₱{t} bn (2025 pesos), 2027-2030": SC.probability(dr, cum25, -t) for t in (100, 250, 500)}
        p["GDP below baseline in 2030"] = SC.probability(dr, "GDP gap % 2030", 0.0)
        probs[lab] = p
    probs = pd.DataFrame(probs)
    ty = r1.shocks["typhoon_damage_pct_gdp"].unstack("year")
    tys = pd.DataFrame({"mean": ty.mean(), "sd": ty.std(), "p05": ty.quantile(0.05), "p50": ty.quantile(0.5),
                        "p95": ty.quantile(0.95), "max": ty.max()})
    # single seasons in 2027 (no external shock): the model's 1-in-10, 1-in-20 and 1-in-100 seasons, gross minus the mean
    g = dd.gross(np.random.default_rng(7), 400_000)
    single = []
    for lab, q in (("1-in-10 season (p90)", 0.90), ("1-in-20 season (p95)", 0.95), ("1-in-100 season (p99)", 0.99)):
        s = float(np.quantile(g, q)) - dd.centre_value()
        zero = {y: dict(oil_pct=0.0, remit_pct=0.0, fdi_usd_m=0.0) for y in st1.years}
        row = st1.run_path(zero, {2027: s})
        single.append({"season": lab, "gross damage (% of GDP)": float(np.quantile(g, q)), "shock: above the mean (% of GDP)": s,
                       **{k: v for k, v in row.items() if k.startswith(("GDP gap", "consumption gap"))},
                       "cumulative GDP gap ₱ bn (2025 pesos)": row[CUM] * TO25})
    single = pd.DataFrame(single).set_index("season")
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    base = ROOT / "outputs" / f"stochastic_outlook_disasters_comparison{'_02settings' if S02 else ''}_{stamp}"
    pd.concat({"without": d0, "with": d1, "with minus without": diff}, axis=1).to_csv(f"{base}_draws.csv")
    r1.shocks.to_csv(f"{base}_shocks.csv")
    mc = lambda s: float(s.std(ddof=1) / np.sqrt(len(s)))
    L = [f"# Stochastic outlook with and without the typhoon draw, {dt.datetime.now():%d %b %Y %H:%M}", "",
         "**RESEARCH, NOT FOR CITATION.** Script: `validation/stochastic_disasters/compare_outlook_with_without.py`. "
         f"{N} draws, seed {SEED}, {setting}, oil from actual past paths (as `scenarios/stochastic_outlook.py`). The typhoon draw "
         "is opt-in (`StochasticCGE(..., disasters=DisasterDraw.from_data())`); without it the outlook is unchanged.", "",
         f"Typhoon draw: {dd.lam:.2f} destructive cyclones a season (Poisson), damage per cyclone lognormal (mu {dd.mu:.3f}, "
         f"sigma {dd.sigma:.3f}, log of % of GDP), background {dd.background:.4f}% of GDP, agriculture {dd.agri_share:.1%} of "
         f"damage; expected season {dd.expected():.3f}% of GDP, subtracted (the baseline assumes a normal year). Data: "
         f"`data/raw/disasters/{dd.source}`. Entry: agriculture as lost output that year; infrastructure as public "
         + ("capital destroyed (one-year productivity stand-in: no public capital in the 0.2 settings)." if S02 else
            "capital destroyed (the engine's kg_loss: productivity from the next year)."), "",
         f"Check: the external shocks are identical in the two runs (largest difference {same_ext:.1e}).", "",
         "## GDP and consumption gaps (% of baseline) and cumulative GDP gap (₱ bn, 2025 pesos)", "",
         tab.to_markdown(floatfmt=",.3f"), "",
         "## The typhoon draw's own contribution (with minus without, draw by draw)", "", dtab.to_markdown(floatfmt=",.3f"), "",
         f"Monte Carlo standard error of the mean contribution to the cumulative gap: ₱{mc(diff[cum25]):,.1f} bn; of the mean "
         f"cumulative gap itself: without ₱{mc(d0[cum25]):,.1f} bn, with ₱{mc(d1[cum25]):,.1f} bn.", "",
         "## Probabilities (share of draws)", "", probs.to_markdown(floatfmt=".3f"), "",
         "## The typhoon damage drawn (% of GDP, centred on the expected season)", "", tys.to_markdown(floatfmt=".3f"), "",
         "## One bad season in 2027, no external shock", "", single.to_markdown(floatfmt=",.3f"), "",
         "Reading: results are output and household consumption, not jobs. Poverty is not computed in the outlook.",
         f"Files: `{Path(base).name}_draws.csv`, `{Path(base).name}_shocks.csv`. Run time {time.time() - t0:.0f} s.", ""]
    Path(f"{base}.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
