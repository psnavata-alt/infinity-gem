"""Backtest of the stochastic CGE's shock distributions (benchmarking (a); 15 Oct 2026).

Question: do the Bayesian VAR's forecast bands contain what actually happened as often as they claim? A fan chart is
only as good as this coverage.
Method (pseudo-out-of-sample): for each origin = December of 2017 ... 2024, rebuild the VAR's variables from data up to the
origin only (seasonal factors and the remittance trend estimated on that sample), estimate the Minnesota BVAR (as
infinity_gem.stochastic), draw 500 stable coefficient sets with future shocks, simulate 12 months, and compare the realized
12-month averages with the draws' 50% and 90% bands. Expected: inside the 50% band about half the time, the 90% band about
nine times in ten. Data: a compiled monthly panel (not distributed).
Run:  py validation/stochastic_backtest/backtest.py
"""
import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from infinity_gem import svar                                               # noqa: E402
from infinity_gem.stochastic import PRIOR_MEAN, VARIABLES, _simulate, load_task1_monthly, shock_pool, oil_random_walk  # noqa: E402

N, H, P = 500, 12, 3


def transform(raw: pd.DataFrame, origin: pd.Timestamp) -> pd.DataFrame:
    """VAR variables for the whole sample, with seasonal factors and the remittance trend from data up to the origin only."""
    est = raw.loc[:origin]
    out = pd.DataFrame(index=raw.index)
    out["loil"] = 100 * np.log(raw["oil"])
    out["gpr"] = raw["gpr"]
    def season(x_est):
        dev = x_est - x_est.rolling(12, center=True).mean()
        eff = dev.groupby(dev.index.month).mean()
        return eff - eff.mean()
    lrem = 100 * np.log(raw["remit"])
    e_r = season(lrem.loc[:origin])
    lrem_sa = lrem - pd.Series(raw.index.month, index=raw.index).map(e_r)
    t_all = np.arange(len(raw))
    m_est = lrem_sa.notna().to_numpy() & (raw.index <= origin)
    coef = np.polyfit(t_all[m_est], lrem_sa.to_numpy()[m_est], 1)
    out["lrem_dt"] = lrem_sa - np.polyval(coef, t_all)
    e_f = season(raw["fdi"].loc[:origin])
    out["fdi_sa"] = raw["fdi"] - pd.Series(raw.index.month, index=raw.index).map(e_f)
    return out[VARIABLES]


def main():
    raw = load_task1_monthly()
    raw.index = pd.DatetimeIndex(raw.index)
    out = {}
    for method in ("normal", "bootstrap", "oil random walk", "oil random walk + bootstrap"):   # 0.3.7
        out[method] = backtest(raw, method)
    report(out)


def backtest(raw, method):
    rows = []
    for yr in range(2017, 2025):
        origin = pd.Timestamp(f"{yr}-12-01")
        x = transform(raw, origin)
        est = x.loc[:origin].dropna()
        real = x.loc[origin + pd.offsets.MonthBegin(1): origin + pd.offsets.MonthBegin(H)]
        bv = svar.bvar_minnesota(est, P, lam=0.2, delta=PRIOR_MEAN)
        Y_last = est.to_numpy(float)[-P:]
        rng = np.random.default_rng(1000 + yr)
        pool = shock_pool(bv) if "bootstrap" in method else None
        rw = method.startswith("oil random walk")
        sims, s = [], yr
        while len(sims) < N:
            for B, Sig in bv.draw(N, seed=s):
                if len(sims) == N:
                    break
                if bv.model(B, Sig).stable():
                    sims.append(_simulate(oil_random_walk(B, len(VARIABLES)) if rw else B, Sig, Y_last, H, rng, pool).mean(axis=0))
            s += 1000
        sims = np.array(sims)
        for j, v in enumerate(VARIABLES):
            r = real[v].dropna()
            if len(r) < 10:
                continue
            obs = float(r.mean())
            q = np.quantile(sims[:, j], [0.05, 0.25, 0.75, 0.95])
            rows.append({"origin": f"Dec {yr}", "variable": v, "realized 12-month mean": obs, "p05": q[0], "p25": q[1], "p75": q[2], "p95": q[3],
                         "in 50% band": q[1] <= obs <= q[2], "in 90% band": q[0] <= obs <= q[3]})
    t = pd.DataFrame(rows)
    cov = t.groupby("variable")[["in 50% band", "in 90% band"]].mean()
    cov.loc["all"] = t[["in 50% band", "in 90% band"]].mean()
    return t, cov


def report(out):
    stamp = dt.date.today().strftime("%Y%m%d")
    md = lambda df, idx=False: df.to_markdown(index=idx, floatfmt=".2f") if hasattr(df, "to_markdown") else df.to_string(index=idx)
    both = pd.concat({m: c for m, (t, c) in out.items()}, axis=1)
    print(both.round(2).to_string())
    L = [f"# Backtest of the stochastic CGE's shock bands (Minnesota BVAR), origins Dec 2017-Dec 2024 ({dt.date.today():%d %B %Y})", "",
         "**NOT FOR CITATION** (Infinity GEM 0.3.7). Script: `validation/stochastic_backtest/backtest.py`. Variables as in "
         "`infinity_gem/stochastic.py`: loil = 100 x log world oil price; gpr = geopolitical risk index; lrem_dt = 100 x log remittances, seasonally "
         "adjusted and detrended; fdi_sa = FDI (US$ m), seasonally adjusted. Seasonal factors and trends from data up to each origin only. "
         "Four variants (15 Oct 2026: 'go with your recommendations on the oil-price swings'): 'normal' (the model's default); 'bootstrap' "
         "(resampled historical surprises: `stochastic.shock_pool`); 'oil random walk' (oil's equation as a no-change random walk: "
         "`stochastic.oil_random_walk`); and both together.", "",
         "## Coverage (share of origins where the realized 12-month average fell inside the band)", "", md(both, True), "",
         "Well calibrated: about 0.50 and 0.90. Lower means the fan is too narrow (overconfident); higher, too wide. With 8 origins a share "
         "is only a rough guide (one miss moves it by 0.125); 2020 (COVID) is a known outlier year.", ""]
    for m, (t, c) in out.items():
        L += [f"## Every origin: {m} shocks", "", md(t), ""]
    rep = ROOT / "outputs" / f"stochastic_backtest_{stamp}.md"
    rep.write_text(chr(10).join(L), encoding="utf-8")
    print("saved", rep)


if __name__ == "__main__":
    main()
