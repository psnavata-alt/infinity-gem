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
domestic policy (draw it separately if needed); capture expectations (Stage 2). Disasters: an OPT-IN separate draw of
typhoon damage (23 Oct 2026; research, NOT FOR CITATION): StochasticCGE(..., disasters=
DisasterDraw.from_data()); the default (disasters=None) leaves every result unchanged.
Checks: run_all_checks.py X1 (zero variance gives the baseline exactly; a fixed path gives exactly the deterministic
scenario; reproducible with a seed; the draws' shocks have the posterior covariance; Monte Carlo error reported).
The disaster draw: validation/stochastic_disasters/test_disaster_draw.py (standalone).
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


# ---------------------------------------------------------------------------------------------- disasters
DISASTER_FILE = "PAGASA_ARTC_typhoon_damage_events_and_seasons_2017-2023.csv"     # data/raw/disasters (sources inside)


def gdp_nominal_annual() -> pd.Series:
    """PSA nominal GDP by calendar year, ₱ bn (OpenSTAT 0012B5BEXQ1 in data/raw/macro; complete years only)."""
    from . import paths
    d = pd.read_csv(paths.DATA_RAW / "macro" / "PSA_OpenSTAT_GDP_by_expenditure_quarterly_2000-2026.csv", comment="#")
    g = d[(d["valuation"] == "At Current Prices") & (d["expenditure"] == "Gross Domestic Product")]
    nq = g.groupby("year")["quarter"].nunique()
    return (g.groupby("year")["value_million_php"].sum() / 1000)[nq == 4]


@dataclass
class DisasterDraw:
    """Typhoon damage as a separate random draw in the stochastic outlook (23 Oct 2026; research, NOT
    FOR CITATION; OPT-IN: StochasticCGE(..., disasters=None), the default, leaves every result unchanged).

    Each year's damage to agriculture and infrastructure, in % of GDP, is a compound Poisson sum, the usual frequency-
    severity model of catastrophe losses (Klugman, Panjer and Willmot, Loss Models: to verify before citing):
        D = background + S_1 + ... + S_N,   N ~ Poisson(lam),   ln S_j ~ Normal(mu, sigma^2).
    from_data() calibrates it on data/raw/disasters/PAGASA_ARTC_typhoon_damage_events_and_seasons_2017-2023.csv (NDRRMC
    figures published in PAGASA's annual tropical-cyclone reports; pages in the file):
      lam         destructive tropical cyclones per season (names PAGASA decommissioned: at least 300 deaths or PHP 1 bn
                  of damage): frequency='sample' (default) = the severity sample's own count, 11 in the 4 seasons
                  2017-2020 (2.75); frequency='2001-2019' = 44 names in 19 seasons (2.32), the long run, when the nominal
                  PHP 1 bn threshold was relatively higher. With 'sample' the model matches PAGASA's own rankings of
                  2019-2022 (exceedance 0.75 / 0.18 / 0.11 / 0.44 against 0.71 / 0.23 / 0.11 / 0.43 from the ranks;
                  validation/stochastic_disasters/test_disaster_draw.py);
      mu, sigma   mean and standard deviation of the log damage of the 11 destructive cyclones of 2017-2020, each in % of
                  that year's nominal GDP (PSA);
      background  the rest of each 2017-2020 season's damage (cyclones below the threshold, monsoon surges), mean % of GDP;
      agri_share  agriculture's share of the destructive cyclones' damage where the split is published (pooled).
    centre: 'mean' (default) subtracts the expected season, because the baseline already assumes a normal year (preshock/typhoons_normal_year.py): the draws average zero and a quiet season is a gain; 'median' subtracts
      the median season (its other normal year); 'none' keeps gross damage (a disaster-free baseline).
    scale: multiplies the centred draws (a sensitivity: NDRRMC's agriculture and infrastructure damage leaves out housing and
      other private assets; the World Bank puts average typhoon losses at PHP 133.2 bn a year from a catastrophe model,
      Background Paper PH-11, 2023, p. 8, a reference copy (not distributed)).
    How the damage enters the CGE: StochasticCGE.disaster_shocks (decided 17 Oct 2026)."""
    lam: float
    mu: float
    sigma: float
    background: float
    agri_share: float
    centre: str = "mean"
    scale: float = 1.0
    source: str = ""
    _c: float = field(default=None, init=False, repr=False, compare=False)

    def __post_init__(self):
        if self.centre not in ("mean", "median", "none"):
            raise ValueError("centre must be 'mean', 'median' or 'none'")
        if not (self.lam >= 0 and self.sigma >= 0 and self.scale >= 0 and 0 <= self.agri_share <= 1):
            raise ValueError("lam, sigma and scale must be non-negative and agri_share between 0 and 1")

    @classmethod
    def from_data(cls, centre: str = "mean", scale: float = 1.0, frequency: str = "sample", path=None) -> "DisasterDraw":
        from pathlib import Path
        from . import paths
        if frequency not in ("sample", "2001-2019"):
            raise ValueError("frequency must be 'sample' (2017-2020 events per season) or '2001-2019' (decommissioned names)")
        f = Path(path) if path else paths.DATA_RAW / "disasters" / DISASTER_FILE
        if not f.exists():                         # public version: the table is not in this repository
            raise FileNotFoundError(f"{f.name} is not in this repository: it is compiled from PAGASA's Annual Reports on "
                                    "Philippine Tropical Cyclones, whose terms ask for written permission to reproduce them; "
                                    "data/raw/disasters/README.md says how to compile it")
        d = pd.read_csv(f, comment="#")
        gdp = gdp_nominal_annual()
        ev = d[d["record"] == "event"].assign(season=lambda x: x["season"].astype(int))
        x = np.log((ev["total_php_bn"] / ev["season"].map(gdp) * 100).to_numpy(float))
        se = d[d["record"] == "season"].assign(season=lambda x: x["season"].astype(int)).set_index("season")["total_php_bn"]
        bg = [(float(se[y]) - float(ev.loc[ev["season"] == y, "total_php_bn"].sum())) / gdp[y] * 100
              for y in sorted(ev["season"].unique())]
        fr = d[d["record"] == "frequency"].iloc[0]
        lam = len(ev) / ev["season"].nunique() if frequency == "sample" else float(fr["count"]) / float(fr["seasons"])
        sp = ev.dropna(subset=["agriculture_php_bn", "infrastructure_php_bn"])
        return cls(lam=float(lam), mu=float(x.mean()), sigma=float(x.std(ddof=1)),
                   background=float(np.mean(bg)), agri_share=float(sp["agriculture_php_bn"].sum() / sp["total_php_bn"].sum()),
                   centre=centre, scale=scale, source=f.name)

    def expected(self) -> float:
        """Expected season damage, % of GDP (gross: before centring and scaling)."""
        return self.background + self.lam * float(np.exp(self.mu + self.sigma ** 2 / 2))

    def gross(self, rng, n: int) -> np.ndarray:
        """n seasons of gross damage, % of GDP."""
        N = rng.poisson(self.lam, size=n)
        tot = np.zeros(n)
        np.add.at(tot, np.repeat(np.arange(n), N), np.exp(rng.normal(self.mu, self.sigma, size=int(N.sum()))))
        return self.background + tot

    def centre_value(self) -> float:
        if self._c is None:
            self._c = (self.expected() if self.centre == "mean" else 0.0 if self.centre == "none"
                       else float(np.median(self.gross(np.random.default_rng(20261023), 400_000))))   # median: fixed seed
        return self._c

    def draw(self, rng, years) -> dict:
        """{year: damage in % of GDP, centred and scaled} for one path."""
        g = self.gross(rng, len(years))
        return {y: self.scale * (float(g[i]) - self.centre_value()) for i, y in enumerate(years)}


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
    php_per_usd and gdp_bn convert FDI to the SAM's units by share of GDP (macrolink.cge_shocks).
    disasters (23 Oct 2026; OPT-IN): None (default) = no disaster draw, results exactly as before; a
    DisasterDraw = each path also draws typhoon damage, from its own random stream (the external draws are unchanged)."""

    def __init__(self, dyn, data: pd.DataFrame, years=(2027, 2028, 2029, 2030), p: int = 3, lam: float = 0.2,
                 php_per_usd: float = 58.0, gdp_bn: float = 28009.93, investment_passthrough: float = 1.0,
                 shocks: str = "normal", oil: str = "var", disasters=None):
        if disasters is not None and not isinstance(disasters, DisasterDraw):
            raise TypeError("disasters must be None (off, the default) or a DisasterDraw, e.g. DisasterDraw.from_data()")
        self.dis = disasters
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
        if self.dis is not None:                         # (d): what the damage hits, from the model's own SAM
            from .dynamic import PSA_INDUSTRIES
            from .settings import PUBLIC_CAPITAL
            m = dyn.m
            self._agri = [a for a in PSA_INDUSTRIES["Agriculture, forestry, and fishing"] if a in m.A]
            if not self._agri:
                raise ValueError("disasters: the model's SAM has no agricultural activities")
            self._agri_out_gdp = float(sum(m.QA0[m.A.index(a)] for a in self._agri)) / ML.sam_gdp(m)
            self._pubcap = dyn.a.get("public_capital") is not None and getattr(dyn, "pc", None) is not None
            self._pc_low = PUBLIC_CAPITAL["low"]         # phi, kg_gdp for the one-year stand-in when public capital is off

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

    def disaster_shocks(self, damage: dict) -> tuple:
        """CGE shocks from {year: damage, % of GDP (centred)}, entered as decided (17 Oct
        2026): lost productivity at the average product of capital (Hallegatte and Vogt-Schilb 2016, WB WPS 7885), not lost
        capital with capital-labour substitution; results are read as output, incomes and poverty, not job counts.
          agriculture (agri_share of the damage): lost output capacity of the agricultural activities in the damage year,
            tfp_scale = 1 - x, x = damage / their output (an industry that loses x% of its productive capacity loses x% of
            its output; NDRRMC's agricultural damage is mostly the value of crops, livestock and fish destroyed);
          infrastructure (the rest): public capital destroyed. With the public-capital option on (the '0.3 recommended'
            dynamic settings with public_capital 'low' or 'high'), through the engine's own channel, public_capital
            'kg_loss' (as scenarios/combined_2025_2030.py enters 2026's typhoon damage): productivity in every activity from
            the next year, decaying with public-capital depreciation. With it off (the published 0.2 settings), a one-year
            productivity loss in every activity of the same first-year size, (1 - d / kg_gdp) ** phi, with the 'low'
            public-capital parameters (settings.PUBLIC_CAPITAL: Bom and Ligthart 2014; IMF ICSD).
        Returns ({year: CGE spec}, {year: public capital destroyed, ₱ bn in the SAM's units})."""
        specs, kg = {}, {}
        m = self.dyn.m
        for y, s in damage.items():
            if s == 0:
                continue
            d = s / 100
            x = self.dis.agri_share * d / self._agri_out_gdp
            if x >= 1:
                raise ValueError(f"disasters: {y} damage would destroy all agricultural output ({x:.0%})")
            tfp = {a: 1.0 - x for a in self._agri}
            infra = (1 - self.dis.agri_share) * d
            if self._pubcap:
                kg[y] = infra * float(self.dyn.base.table.loc[y, "real_gdp"])
            else:
                f = (1 - infra / self._pc_low["kg_gdp"]) ** self._pc_low["phi"]
                tfp = {a: tfp.get(a, 1.0) * f for a in m.A}
            specs[y] = {"tfp_scale": tfp}
        return specs, kg

    def _scenario(self, spec: dict, kg: dict):
        """dyn.scenario(spec) with public capital destroyed in `kg` added to the model's own kg_loss for this run only."""
        if not kg:
            return self.dyn.scenario(spec)
        pc = self.dyn.pc
        had, old = "kg_loss" in pc, pc.get("kg_loss")
        new = dict(old or {})
        for y, v in kg.items():
            new[y] = new.get(y, 0.0) + v
        pc["kg_loss"] = new
        try:
            return self.dyn.scenario(spec)
        finally:                                         # restore the model exactly as it was
            if had:
                pc["kg_loss"] = old
            else:
                pc.pop("kg_loss", None)

    def run_path(self, changes: dict, disaster: dict | None = None) -> dict:
        """Run the dynamic model for one set of yearly changes; return GDP and consumption gaps.
        disaster (opt-in): {year: typhoon damage, % of GDP, centred}; None = none (as before)."""
        spec, kg = self.spec(changes), {}
        if disaster:
            dspec, kg = self.disaster_shocks(disaster)
            for y, s in dspec.items():
                cur = spec.setdefault(y, {})
                for k, v in s.items():                   # factors by activity multiply any external one
                    cur[k] = ({a: cur[k].get(a, 1.0) * v.get(a, 1.0) for a in dict.fromkeys(list(cur[k]) + list(v))}
                              if k in cur else v)
        sim = self._scenario(spec, kg)
        cmp_ = self.dyn.compare(self.dyn.base, sim)
        row = {f"GDP gap % {y}": cmp_.loc[y, "gdp_gap_pct"] for y in self.years}
        row.update({f"consumption gap % {y}": cmp_.loc[y, "consumption_gap_pct"] for y in self.years})
        row["cumulative GDP gap ₱ bn (SAM year prices)"] = cmp_.loc["cumulative", "gdp_gap_bn"]
        return row

    def run(self, n: int = 200, seed: int = 20261014, zero_variance: bool = False) -> StochasticResult:
        """n draws. zero_variance=True: mean coefficients and no future shocks in every draw (check X1: = baseline)."""
        rng = np.random.default_rng(seed + 1)            # future shocks: a stream separate from BVAR.draw's
        oil_rng = np.random.default_rng(seed + 2)        # 0.3.7: historical oil blocks (oil='history')
        dis_rng = np.random.default_rng(seed + 3)        # (d): typhoon damage, its own stream (opt-in)
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
            dis = None if (self.dis is None or zero_variance) else self.dis.draw(dis_rng, self.years)
            shocks += [dict(draw=d, year=y, **c, **({} if dis is None else {"typhoon_damage_pct_gdp": dis[y]}))
                       for y, c in ch.items()]
            rows.append(dict(draw=d, **self.run_path(ch, dis)))
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
