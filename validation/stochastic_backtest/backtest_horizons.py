"""Backtest of the stochastic CGE's OIL paths at 1-4 years ahead (0.3.7, 15 Oct 2026).

Why: the outlook (scenarios/stochastic_outlook.py) runs to 2030, about four years past the data, but backtest.py tests
12-month bands only. 15 Oct 2026.
Three ways to draw the oil path, each from data up to the origin only:
  'VAR oil'      the Bayesian VAR's own oil equation (the model's default);
  'random walk'  oil's equation as a no-change random walk (stochastic.oil_random_walk);
  'history'      actual past 48-month paths of the World Bank Dubai price since 1986, centred on no change
                 (stochastic.oil_history_pool, blocks ending before the origin).
For origins December 2017-2023: share of origins whose realized calendar-year-ahead average oil price (the quarterly macro panel) fell
inside the draws' 50% and 90% bands, the median width of the 90% band, and the mean error of the median.
Run:  py validation/stochastic_backtest/backtest_horizons.py
"""
import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from backtest import transform                                                     # noqa: E402
from infinity_gem import svar                                                          # noqa: E402
from infinity_gem.stochastic import PRIOR_MEAN, _simulate, load_task1_monthly, oil_history_pool, oil_random_walk  # noqa: E402

N, P, H = 400, 3, 48


def main():
    raw = load_task1_monthly()
    raw.index = pd.DatetimeIndex(raw.index)
    rows = []
    for yr in range(2017, 2024):
        o = pd.Timestamp(f"{yr}-12-01")
        x = transform(raw, o)
        est = x.loc[:o].dropna()
        bv = svar.bvar_minnesota(est, P, lam=0.2, delta=PRIOR_MEAN)
        Yl = est.to_numpy(float)[-P:]
        pool = oil_history_pool(until=f"{yr}-12")
        for method in ("VAR oil", "random walk", "history"):
            rng = np.random.default_rng(1000 + yr)
            if method == "history":
                starts = rng.integers(0, len(pool) - H + 1, 4 * N)
                sims = np.array([Yl[-1, 0] + np.cumsum(pool[s:s + H]) for s in starts])
            else:
                sims, s = [], yr
                while len(sims) < N:
                    for B, Sig in bv.draw(N, seed=s):
                        if len(sims) == N:
                            break
                        if bv.model(B, Sig).stable():
                            Bu = oil_random_walk(B, Yl.shape[1]) if method == "random walk" else B
                            sims.append(_simulate(Bu, Sig, Yl, H, rng)[:, 0])
                    s += 1000
                sims = np.array(sims)
            for yh in (1, 2, 3, 4):
                real = x["loil"].loc[o + pd.offsets.MonthBegin(12 * (yh - 1) + 1): o + pd.offsets.MonthBegin(12 * yh)].dropna()
                if len(real) < 10:
                    continue
                v = sims[:, 12 * (yh - 1):12 * yh].mean(axis=1)
                q = np.quantile(v, [0.05, 0.25, 0.5, 0.75, 0.95])
                r = float(real.mean())
                rows.append({"origin": f"Dec {yr}", "oil paths": method, "years ahead": yh, "in 50% band": q[1] <= r <= q[3],
                             "in 90% band": q[0] <= r <= q[4], "90% band width (%)": (np.exp((q[4] - q[0]) / 100) - 1) * 100,
                             "realized minus median (log points)": r - q[2]})
    t = pd.DataFrame(rows)
    summ = t.groupby(["oil paths", "years ahead"]).agg(origins=("in 50% band", "size"), in_50=("in 50% band", "mean"),
                                                       in_90=("in 90% band", "mean"), width_90=("90% band width (%)", "median"),
                                                       bias=("realized minus median (log points)", "mean"))
    print(summ.round(2).to_string())
    md = lambda df, idx=True: df.to_markdown(index=idx, floatfmt=".2f") if hasattr(df, "to_markdown") else df.to_string(index=idx)
    L = [f"# Oil paths in the stochastic CGE: backtest at 1-4 years ahead ({dt.date.today():%d %B %Y})", "",
         "**NOT FOR CITATION** (Infinity GEM 0.3.7). Script: `validation/stochastic_backtest/backtest_horizons.py`. "
         "Realized = the compiled panel's oil price (Dubai crude), calendar-year averages after each December origin. "
         "History = World Bank Pink Sheet Dubai, 1986 to the origin.", "",
         "## Summary", "", md(summ.round(2)), "",
         "Well calibrated: about 0.50 and 0.90. With 5-7 origins a share is only a rough guide (one origin moves it by 0.14-0.20). "
         "Bias > 0: oil came in above the median. Reading: the VAR's oil equation is biased low and too narrow; a random walk is right at "
         "one year but its band keeps widening (by four years about 550% wide, and its tail draws are 5-9 times today's price, beyond "
         "anything since 1986 and beyond what the CGE can solve); actual past paths are about unbiased, right at one and two years, and "
         "bounded by experience. The outlook uses 'history' (`StochasticCGE(oil='history')`).", "",
         "## Every origin", "", md(t, False), ""]
    rep = ROOT / "outputs" / f"stochastic_backtest_horizons_{dt.date.today():%Y%m%d}.md"
    rep.write_text(chr(10).join(L), encoding="utf-8")
    print("saved", rep)


if __name__ == "__main__":
    main()
