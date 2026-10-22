"""Stochastic recursive-dynamic CGE (Stage 1; 0.3.4, 14 Oct 2026).

The recursive-dynamic CGE (dynamic.py) answers "what if this path of external shocks happens?". Stage 1 adds "how
uncertain is the outlook?": it draws many joint paths of the external variables from a Bayesian VAR, turns each
path into CGE shocks year by year, runs the dynamic model for each, and reports ranges and probabilities.

Steps (14 Oct 2026):
1. External data, monthly (external_data), in LEVELS: 100 x log of the world oil price, the geopolitical risk index,
   100 x log of remittances as a deviation from their linear trend (about +3% a year), and FDI inflows (US$ million).
   Remittances and FDI are seasonally adjusted (calendar-month effects removed), because the VAR has only a constant.
   Levels, not growth rates: in growth rates every month's noise becomes a permanent change in the level, and
   uncertainty piles up without limit (tried first, 14 Oct: +-98% for the 2030 oil price). Remittances detrended:
   as a random walk their monthly noise made the yearly spread +-9.4%, against +-1.7% in 2016-2025; detrended and
   mean-reverting it is +-1.7% (and oil +-30%, against +-30.5% historically). Calibration check: X1.
2. A Minnesota-prior BVAR (svar.bvar_minnesota; Banbura, Giannone and Reichlin 2010) with prior mean 1 on the own
   first lag of the oil price (random walk) and 0 on the others (detrended remittances, GPR, FDI), and exact
   draws from its posterior (BVAR.draw): each draw has its own coefficients and covariance (parameter uncertainty)
   and its own future shocks (shock uncertainty). Explosive draws (an eigenvalue of 1 or more) are discarded and
   counted, as is usual.
3. For each draw, the monthly path is simulated from the last observed month and compared with the posterior-mean
   forecast (the path with mean coefficients and no future shocks). The DIFFERENCE, averaged or summed by calendar
   year, is the CGE shock for that year: oil price and remittances in % of the mean path's level, FDI in US$ million.
   So every result is a deviation from the deterministic baseline, and a draw with no uncertainty reproduces it.
4. macrolink.cge_shocks turns the yearly changes into a CGE spec (FDI enters investment one-for-one), and
   DynamicCGE.scenario runs it.

What it does NOT do: forecast the level of growth (the baseline path stays the documented one); add uncertainty in
domestic policy or disasters (draw those separately if needed); capture expectations (Stage 2).
Checks: run_all_checks.py X1 (zero variance gives the baseline exactly; a fixed path gives exactly the deterministic
scenario; reproducible with a seed; the draws' shocks have the posterior covariance; Monte Carlo error reported).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import macrolink as ML
from . import svar

VARIABLES = ["loil", "gpr", "lrem_dt", "fdi_sa"]     # order in the VAR (external block first, as in the reference VAR)
PRIOR_MEAN = [1.0, 0.0, 0.0, 0.0]                      # Minnesota prior on the own first lag: random walk for oil only


def _seasonal(x: pd.Series) -> pd.Series:
    """Calendar-month effect: average by month of the deviation from a centred 12-month mean (sums to about zero)."""
    dev = x - x.rolling(12, center=True).mean()
    eff = dev.groupby(dev.index.month).mean()
    return pd.Series(x.index.month, index=x.index).map(eff - eff.mean())


def external_data(monthly: pd.DataFrame) -> pd.DataFrame:
    """The VAR's variables from monthly levels with columns oil (US$/bbl), gpr (index), remit (US$ mn), fdi (US$ mn):
    loil = 100 x log oil; lrem_dt = 100 x log remittances, seasonally adjusted, minus its linear trend;
    fdi_sa = FDI, seasonally adjusted."""
    d = monthly.copy()
    d.index = pd.DatetimeIndex(d.index)
    out = pd.DataFrame(index=d.index)
    out["loil"] = 100 * np.log(d["oil"])
    out["gpr"] = d["gpr"]
    lrem = 100 * np.log(d["remit"])
    lrem = (lrem - _seasonal(lrem)).dropna()
    tt = np.arange(len(lrem))
    out["lrem_dt"] = lrem - np.polyval(np.polyfit(tt, lrem.to_numpy(), 1), tt)
    out["fdi_sa"] = d["fdi"] - _seasonal(d["fdi"])
    return out[VARIABLES].dropna()


def load_task1_monthly(path=None) -> pd.DataFrame:
    """Monthly levels (oil, gpr, remit, fdi, fx) from a compiled monthly panel (sheet "Data monthly"; not distributed:
    paths.MACRO_MONTHLY, data/raw/macro/README.md). Read from a temporary copy, so the original is never locked."""
    import shutil, tempfile
    from pathlib import Path
    from . import paths
    src = Path(path) if path else paths.MACRO_MONTHLY
    tmp = Path(tempfile.gettempdir()) / "infinity_gem_stochastic_task1.xlsx"
    shutil.copy2(src, tmp)
    d = pd.read_excel(tmp, sheet_name="Data monthly").set_index("month")[["oil", "gpr", "remit", "fdi", "fx"]]
    d.index = pd.DatetimeIndex(d.index)
    return d


def shock_pool(bvar) -> np.ndarray:
    """0.3.7 (15 Oct 2026): the VAR's own
    in-sample surprises, demeaned and whitened to unit covariance (inverse Cholesky of their sample covariance), one row
    per month. Resampling whole rows keeps the historical fat tails (e.g. the 2008, 2014-16, 2020 and 2022 oil moves)
    and the co-movement between variables; each draw's Cholesky factor then gives them that draw's covariance. An iid
    residual bootstrap (Efron and Tibshirani 1993, An Introduction to the Bootstrap; for VARs see Kilian and Lütkepohl
    2017, Structural Vector Autoregressive Analysis: chapter to verify before citing)."""
    U = bvar.model().U
    U = U - U.mean(axis=0)
    W = np.linalg.cholesky(np.cov(U, rowvar=False))
    return np.linalg.solve(W, U.T).T


def oil_random_walk(B, k: int):
    """0.3.7: the oil equation (variable 0) as a no-change random walk: own first lag 1, every other lag and the
    constant 0, so the oil forecast does not revert to the sample mean (the no-change forecast is hard to beat for oil:
    Alquist, Kilian and Vigfusson 2013, Handbook of Economic Forecasting vol. 2A, to verify before citing). The other
    equations keep their estimated coefficients, so oil still moves remittances, FDI and GPR."""
    B = B.copy()
    B[:, 0] = 0.0
    B[0, 0] = 1.0
    return B


def oil_history_pool(since: str = "1986-01", until=None) -> np.ndarray:
    """0.3.7: monthly changes of 100 x log Dubai crude (World Bank Pink Sheet, data/raw/macro), from `since` (1986:
    market pricing; before it prices were administered) to `until`, demeaned so the central path is 'no change'. Whole
    blocks of consecutive months are drawn (oil='history' in StochasticCGE): each future path is an actual past oil path
    of the same length, so it carries the real fat tails and the real partial reversals over several years. Backtest
    (Dec 2017-Dec 2023 origins; validation/stochastic_backtest/backtest_horizons.py, outputs/stochastic_backtest_horizons_*):
    inside the 90% band 0.71 / 0.86 / 1.00 / 1.00 at 1-4 years ahead, with the smallest bias of the three options; a pure
    random walk is better at 1 year (0.86) but its band is about 550% wide by 4 years, with tail draws of 5-9 times today's
    price; the VAR's own oil equation is biased low (0.57-0.86)."""
    from . import paths
    w = pd.read_csv(paths.DATA_RAW / "macro" / "WorldBank_PinkSheet_crude_oil_monthly_1960-2026.csv", comment="#")
    s = pd.Series(100 * np.log(w["crude_dubai_usd_bbl"].to_numpy(float)), index=pd.PeriodIndex(w["month"], freq="M"))
    d = s.diff().loc[since:until].dropna().to_numpy()
    return d - d.mean()


def _simulate(B, Sig, Y_last, H, rng=None, pool=None, oil_path=None):
    """H months ahead from the last p observations Y_last (p x k). B: (k p + 1) x k (lags then constant).
    rng=None: no future shocks (a forecast). pool: None = normal shocks; an array from shock_pool = resampled
    historical surprises (bootstrap). oil_path (H values of 100 x log oil): oil follows this path instead of its
    VAR equation; the other variables still respond to it through their own equations."""
    p, k = Y_last.shape
    hist = [row for row in Y_last]
    L = np.linalg.cholesky(Sig) if rng is not None else None
    out = np.zeros((H, k))
    for h in range(H):
        x = np.concatenate([hist[-j] for j in range(1, p + 1)] + [np.ones(1)])
        y = x @ B
        if rng is not None:
            z = rng.standard_normal(k) if pool is None else pool[rng.integers(len(pool))]
            y = y + L @ z
        if oil_path is not None:
            y = y.copy()
            y[0] = oil_path[h]
        out[h] = y
        hist.append(y)
    return out


def yearly_changes(path: np.ndarray, mean_path: np.ndarray, start: pd.Timestamp, years: list) -> dict:
    """Calendar-year changes of a simulated monthly path relative to the mean path. start = first simulated month.
    Returns {year: dict(oil_pct, remit_pct, fdi_usd_m)}; years must be fully inside the simulated months."""
    months = pd.date_range(start, periods=len(path), freq="MS")
    i = {v: VARIABLES.index(v) for v in VARIABLES}
    lvl = lambda x: np.exp(x / 100)                                # level from 100 x log
    oil, oil0 = lvl(path[:, i["loil"]]), lvl(mean_path[:, i["loil"]])
    rem, rem0 = lvl(path[:, i["lrem_dt"]]), lvl(mean_path[:, i["lrem_dt"]])
    fdi_d = path[:, i["fdi_sa"]] - mean_path[:, i["fdi_sa"]]
    out = {}
    for y in years:
        sel = np.asarray(months.year == y)
        if sel.sum() != 12:
            raise ValueError(f"year {y} is not fully inside the simulated months ({months[0]:%b %Y} to {months[-1]:%b %Y})")
        out[y] = dict(oil_pct=100 * (oil[sel].mean() / oil0[sel].mean() - 1),
                      remit_pct=100 * (rem[sel].mean() / rem0[sel].mean() - 1),
                      fdi_usd_m=float(fdi_d[sel].sum()))
    return out


@dataclass
class StochasticResult:
    draws: pd.DataFrame                  # one row per draw: GDP gap % by year, cumulative ₱ bn, consumption gap %
    shocks: pd.DataFrame                 # one row per (draw, year): oil %, remittances %, FDI US$ mn
    summary: pd.DataFrame = field(default=None)
    mc_error: dict = field(default=None)


class StochasticCGE:
    """dyn: a DynamicCGE (its baseline is computed if needed). data: monthly levels (see external_data).
    years: model years that receive shocks (each must be fully after the last data month).
    php_per_usd and gdp_bn convert FDI to the SAM's units by share of GDP (macrolink.cge_shocks)."""

    def __init__(self, dyn, data: pd.DataFrame, years=(2027, 2028, 2029, 2030), p: int = 3, lam: float = 0.2,
                 php_per_usd: float = 58.0, gdp_bn: float = 28009.93, investment_passthrough: float = 1.0,
                 shocks: str = "normal", oil: str = "var"):
        self.dyn, self.years = dyn, list(years)
        self.ext = external_data(data)
        self.bvar = svar.bvar_minnesota(self.ext, p, lam=lam, delta=PRIOR_MEAN)
        if shocks not in ("normal", "bootstrap"):
            raise ValueError("shocks must be 'normal' or 'bootstrap'")
        self.pool = shock_pool(self.bvar) if shocks == "bootstrap" else None      # 0.3.7: fat-tailed option
        if oil not in ("var", "random_walk", "history"):
            raise ValueError("oil must be 'var', 'random_walk' or 'history'")
        # 0.3.7: oil as a no-change random walk. Backtest Dec 2017-Dec 2024 (validation/stochastic_backtest): oil inside the
        # 50% / 90% bands 0.12 / 0.75 with the VAR's oil equation, 0.50 / 0.88 as a random walk (normal shocks)
        self.oil_rw = oil == "random_walk"
        # 0.3.7: 'history' = actual past oil paths (oil_history_pool), centred on no change: calibrated at 1-4 years
        self.oil_hist = oil_history_pool() if oil == "history" else None
        self.p, self.php, self.gdp, self.theta = p, php_per_usd, gdp_bn, investment_passthrough
        self.start = self.ext.index[-1] + pd.offsets.MonthBegin(1)
        self.H = int((pd.Timestamp(f"{max(self.years)}-12-01").to_period("M") - self.start.to_period("M")).n) + 1
        self.Y_last = self.ext.to_numpy(float)[-p:]
        self.mean_path = _simulate(self._B(self.bvar.B_mean), None, self.Y_last, self.H, oil_path=self._flat_oil())
        if not hasattr(dyn, "base"):
            dyn.baseline()

    def _flat_oil(self):
        return np.full(self.H, self.Y_last[-1, 0]) if self.oil_hist is not None else None

    def _oil_draw(self, rng):
        if self.oil_hist is None:
            return None
        s = rng.integers(0, len(self.oil_hist) - self.H + 1)
        return self.Y_last[-1, 0] + np.cumsum(self.oil_hist[s:s + self.H])

    def _B(self, B):
        return oil_random_walk(B, len(VARIABLES)) if self.oil_rw else B

    def spec(self, changes: dict) -> dict:
        """{year: CGE spec} from {year: dict(oil_pct, remit_pct, fdi_usd_m)}."""
        m = self.dyn.m
        return {y: ML.cge_shocks(m, oil_pct=c["oil_pct"], remit_pct=c["remit_pct"], fdi_usd_m=c["fdi_usd_m"],
                                 php_per_usd=self.php, gdp_bn=self.gdp, fdi_channel="investment",
                                 investment_passthrough=self.theta)
                for y, c in changes.items() if any(abs(v) > 0 for v in c.values())}

    def run_path(self, changes: dict) -> dict:
        """Run the dynamic model for one set of yearly changes; return GDP and consumption gaps."""
        sim = self.dyn.scenario(self.spec(changes))
        cmp_ = self.dyn.compare(self.dyn.base, sim)
        row = {f"GDP gap % {y}": cmp_.loc[y, "gdp_gap_pct"] for y in self.years}
        row.update({f"consumption gap % {y}": cmp_.loc[y, "consumption_gap_pct"] for y in self.years})
        row["cumulative GDP gap ₱ bn (SAM year prices)"] = cmp_.loc["cumulative", "gdp_gap_bn"]
        return row

    def run(self, n: int = 200, seed: int = 20261014, zero_variance: bool = False) -> StochasticResult:
        """n draws. zero_variance=True: mean coefficients and no future shocks in every draw (check X1: = baseline)."""
        rng = np.random.default_rng(seed + 1)            # future shocks: a stream separate from BVAR.draw's
        oil_rng = np.random.default_rng(seed + 2)        # 0.3.7: historical oil blocks (oil='history')
        if zero_variance:
            draws, self.dropped = [(self.bvar.B_mean, None)] * n, 0
        else:                                            # keep stable draws only; count the explosive ones
            draws, k, tried, s = [], len(VARIABLES), 0, seed
            while len(draws) < n:
                for B, Sig in self.bvar.draw(n, seed=s):
                    if len(draws) == n:                  # count only the draws actually examined
                        break
                    tried += 1
                    if self.bvar.model(B, Sig).stable():
                        draws.append((B, Sig))
                s += 1000
                if tried > 20 * n:
                    raise RuntimeError(f"only {len(draws)} stable draws in {tried}: the VAR is too close to explosive")
            self.dropped = tried - n
        rows, shocks = [], []
        for d, (B, Sig) in enumerate(draws):
            oil_path = self._flat_oil() if zero_variance else self._oil_draw(oil_rng)
            path = _simulate(self._B(B), Sig, self.Y_last, self.H, None if zero_variance else rng, self.pool, oil_path)
            ch = yearly_changes(path, self.mean_path, self.start, self.years)
            shocks += [dict(draw=d, year=y, **c) for y, c in ch.items()]
            rows.append(dict(draw=d, **self.run_path(ch)))
        res = StochasticResult(pd.DataFrame(rows).set_index("draw"), pd.DataFrame(shocks).set_index(["draw", "year"]))
        res.summary = summarise(res.draws)
        cum = res.draws["cumulative GDP gap ₱ bn (SAM year prices)"]
        res.mc_error = {"draws": len(cum), "explosive draws discarded": self.dropped,
                        "cumulative GDP gap, mean": float(cum.mean()),
                        "Monte Carlo standard error of the mean": float(cum.std(ddof=1) / np.sqrt(len(cum))) if len(cum) > 1 else np.nan}
        return res


def summarise(draws: pd.DataFrame, q=(0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95)) -> pd.DataFrame:
    """Mean and percentiles of every column (for fan charts)."""
    s = draws.quantile(list(q)).T
    s.columns = [f"p{int(round(x * 100)):02d}" for x in q]
    s.insert(0, "mean", draws.mean())
    return s


def probability(draws: pd.DataFrame, column: str, threshold: float, below: bool = True) -> float:
    """Share of draws with `column` below (or above) `threshold`, e.g. the chance that the cumulative GDP loss exceeds
    ₱100 bn: probability(draws, 'cumulative GDP gap ₱ bn (SAM year prices)', -100)."""
    x = draws[column]
    return float((x < threshold).mean() if below else (x > threshold).mean())
