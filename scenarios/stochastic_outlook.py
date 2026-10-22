"""The stochastic dynamic CGE (Stage 1): how uncertain is the 2027-2030 outlook from external shocks alone? (0.3.4, 14 Oct 2026)

Draws joint monthly paths of the world oil price (actual past oil paths since 0.3.7: backtest), geopolitical risk, remittances and FDI from a Bayesian VAR
(infinity_gem/stochastic.py), turns each into yearly CGE shocks, and runs the recursive-dynamic CGE (published 0.2
settings: long-run closure every year) for each. Results are deviations from the deterministic baseline.
NOT FOR CITATION until reviewed (data: a compiled monthly panel, not distributed).
Run:  py scenarios/stochastic_outlook.py [draws, default 500] [--setting=0.3]
      --setting=0.3 (16 Oct 2026): the '0.3 recommended' dynamic model (hybrid short-run years, public
      capital low) instead of the published 0.2 settings; outputs carry the suffix _03settings so nothing is overwritten.
"""
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scenarios"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np                                    # noqa: E402
import pandas as pd                                   # noqa: E402

from _common import Report, SAM_GDP_2023, PSA_GDP     # noqa: E402
from infinity_gem.dynamic import DynamicCGE               # noqa: E402
from infinity_gem import stochastic as SC                 # noqa: E402

N = next((int(a) for a in sys.argv[1:] if a.isdigit()), 500)
S03 = "--setting=0.3" in sys.argv
TAG = "_03settings" if S03 else ""
SEED = 20261014
d = SC.load_task1_monthly()
fx = float(d["fx"].dropna().iloc[-12:].mean())
# 0.3.7 (15 Oct 2026): oil follows actual past oil paths
# (World Bank Dubai since 1986, centred on no change). Backtest at 1-4 years (outputs/stochastic_backtest_horizons_*.md):
# the VAR's oil equation was biased low; a pure random walk was best at 1 year but far too wide by 4 years (and gave
# unsolvable 5-9x oil prices); past paths: 90% bands hold 0.71 / 0.86 / 1.00 / 1.00 at 1-4 years, smallest bias.
if S03:
    from infinity_gem.settings import dynamic_kwargs
    dyn = DynamicCGE(**dynamic_kwargs("0.3 recommended", public_capital="low"))
else:
    dyn = DynamicCGE()
st = SC.StochasticCGE(dyn, d, php_per_usd=fx, oil="history")
res = st.run(n=N, seed=SEED)
cum = "cumulative GDP gap ₱ bn (SAM year prices)"
to25 = PSA_GDP[2025] / SAM_GDP_2023                   # SAM-year pesos -> 2025 pesos, by share of GDP (as elsewhere)
res.draws["cumulative GDP gap ₱ bn (2025 pesos)"] = res.draws[cum] * to25
summ = SC.summarise(res.draws.drop(columns=[cum]))
shock_summ = res.shocks.groupby(level="year").describe(percentiles=[0.05, 0.5, 0.95]).T
cum25 = "cumulative GDP gap ₱ bn (2025 pesos)"
probs = {f"cumulative loss larger than ₱{t} bn (2025 pesos), 2027-2030": SC.probability(res.draws, cum25, -t) for t in (100, 250, 500)}
probs["GDP below baseline in 2030"] = SC.probability(res.draws, f"GDP gap % {st.years[-1]}", 0.0)

rep = Report("Stochastic outlook 2027-2030: uncertainty from external shocks (Stage 1)", "stochastic_outlook")
rep.p(f"**NOT FOR CITATION until reviewed.** {N} joint paths of the world oil price, geopolitical risk, remittances and "
      f"FDI, drawn from a Minnesota BVAR on monthly data {st.ext.index[0]:%b %Y}-{st.ext.index[-1]:%b %Y} (3 lags; "
      f"{res.mc_error['explosive draws discarded']} explosive draws discarded), simulated from {st.start:%b %Y}. Each path's "
      "yearly deviation from the BVAR's mean forecast is a CGE shock (oil price; remittances; FDI into investment "
      f"one-for-one; ₱{fx:.2f} per US$), run through the recursive-dynamic CGE with "
      + ("the '0.3 recommended' settings (hybrid short-run years; public capital low; infinity_gem/settings.py). " if S03
         else "the published (0.2) settings. ")
      + "Every number is a deviation from the deterministic baseline: the baseline's own growth path is not forecast here. "
      "Domestic shocks (policy, disasters) are not drawn.")
rep.h("GDP and consumption: mean and percentiles across draws (% of baseline, and ₱ bn)")
rep.table(summ, floatfmt=",.3f")
rep.h("Probabilities")
rep.table(pd.DataFrame({"share of draws": probs}), floatfmt=".3f")
rep.p(f"Monte Carlo standard error of the mean cumulative gap: ₱{res.mc_error['Monte Carlo standard error of the mean'] * to25:,.1f} bn "
      f"(2025 pesos), on a mean of ₱{res.mc_error['cumulative GDP gap, mean'] * to25:,.1f} bn.")
rep.h("The external shocks drawn (yearly deviation from the mean forecast)")
rep.table(shock_summ, floatfmt=",.2f")
rep.p("Checks: `checks/run_all_checks.py` X1 (zero variance = baseline; fixed path = deterministic scenario; seed; "
      "posterior covariance; one-year-ahead spread of oil and remittances against 2016-2025 history).")

try:                                                  # fan chart
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    yrs = st.years
    g = res.draws[[f"GDP gap % {y}" for y in yrs]].to_numpy()
    fig, ax = plt.subplots(figsize=(7, 4))
    for lo, hi, a in ((5, 95, 0.18), (10, 90, 0.28), (25, 75, 0.42)):
        ax.fill_between(yrs, np.percentile(g, lo, axis=0), np.percentile(g, hi, axis=0), alpha=a, color="#2f6db5",
                        linewidth=0, label=f"{lo}-{hi}th percentile")
    ax.plot(yrs, np.median(g, axis=0), color="#1b3f6b", linewidth=2, label="median")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(yrs)
    ax.set_ylabel("Real GDP vs baseline (%)")
    ax.set_title("External-shock uncertainty, 2027-2030 (not for citation)")
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    fig.tight_layout()
    png = ROOT / "outputs" / f"stochastic_outlook_fan{TAG}.png"
    fig.savefig(png, dpi=150)
    rep.p(f"Fan chart: `{Path(png).name}` (this folder).")
except Exception as e:                                # the chart is optional
    rep.p(f"(Fan chart not drawn: {e!r})")

res.draws.to_csv(ROOT / "outputs" / f"stochastic_outlook_draws{TAG}.csv")
if S03:
    rep.slug = "stochastic_outlook" + TAG             # report file name only; the 'Generated by' line names the script
rep.save()
print(summ.round(3).to_string()); print(probs); print(res.mc_error)
