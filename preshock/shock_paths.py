"""Shock paths by calendar year, 2025-2030, from data and published forecasts only (0.3.7, 15 Oct 2026 night).

15 Oct 2026: no hand-picked values. Replaces the
windows of preshock/oil_shock_size.py and agri_price_shock_size.py (Mar-Sep average applied to a whole year; oil 'back to
January-February' in 2027) for the combined run. Audit: an audit note of 15 Oct 2026 (not included).

Rule for every world price (the CGE year is a calendar year):
    shock(t) = average price in year t (actual months + forecast months) / the no-conflict price for year t  - 1
No-conflict price: the government's own pre-conflict assumption where one exists, otherwise the pre-conflict level.
Forecast: an official or specialist forecast where one exists, otherwise the no-change forecast (the standard benchmark
for commodity prices: Alquist, Kilian and Vigfusson 2013, Handbook of Economic Forecasting 2A, ch. 8).

Oil (crude = Dubai; fuel products = diesel and gasoline import costs, weighted by the IEA product mix in oil_shock_size.MIX):
  actual      monthly Dubai (World Bank Pink Sheet) and US wholesale diesel and gasoline (EIA STEO history) as the
              product-cost proxies, Jan 2026 to the latest month (public version; the development copy used a weekly
              tracker that may not be redistributed);
  forecast    Oct 2026-Dec 2027: EIA Short-Term Energy Outlook of 1 Oct 2026 (data/raw/oil/forecasts/EIA_STEO_Oct2026_
              base.xlsx: Brent spot BREPUUS; US wholesale diesel DSWHUUS and gasoline MGWHUUS), as % changes from the
              latest actual month; 2028-2030: DBCC 193rd meeting, 8 Jul 2026 (Dubai US$60-80; midpoint 70), the only official
              medium-term path; fuel products move with crude from 2028 (EIA's path has product margins near their pre-
              conflict level by late 2027);
  no conflict DBCC 192nd meeting, 9 Dec 2025 (data/raw/oil/forecasts/DBCC_192nd_...pdf): Dubai US$60-70 for 2026-2030,
              midpoint 65 central, 60 and 70 as the range. The same statement sets the pre-conflict growth path, so the oil
              and growth assumptions are those the government held before the conflict. Fuel products: their
              January-February 2026 cost x (65 / January-February Dubai), i.e. at pre-conflict margins.
  Cross-check (not used): EIA's own pre-conflict forecast (STEO of 5 Feb 2026) had Brent at US$57.8 in 2026 and 53.0 in
              2027, below the DBCC's range, which would make the shock larger.
  Public data (0.3.13, 12 Nov 2026; OPT-IN, the default is unchanged): oil_paths(..., source=...) and
              oil_monthly(source) also take "public-mbie" (MBIE's weekly Dubai and importer costs, the public series the
              tracker's columns turned out to be) or "public-worldbank" (the World Bank Pink Sheet's monthly Dubai Fateh with
              MBIE's importer costs). Files and SOURCE notes: data/raw/oil/public/_SOURCE_NOTE.md; check OL1. Which public
              Dubai becomes the default is the decision (comparison of the two Dubai series and their effect on the central 2026 case: a working note (not included), 12 Nov 2026; scenarios/public_oil_compare_2026.py).
World rice (Viet Nam 5%) and urea: World Bank Pink Sheet monthly (agri_price_shock_size.prices()); no official forecast
  exists, so the no-change forecast from the latest month for every later month and year; no conflict = the January-
  February 2026 level (the pre-conflict no-change forecast).
Public works (the measurable corruption/freeze shock: construction that was not done): PSA OpenSTAT 0542B5BCNQ1, general
  government construction (gross fixed capital formation, current prices), against the same period of 2024 (before the
  scandal). 2025: the full year (DBM's verified -P238.3 bn for H2 2025 vs H2 2024, is the cross-check).
  2026: H1 actual; H2 by the no-change forecast of the year-on-year rate (H2 2026 = H2 2025 x H1 2026 / H1 2025, central)
  or H2 2026 = H2 2025 (lower bound: no further fall). 2027 on: back to the programme (DBCC 193rd: growth recovers to
  5-6% from 2027) - an ASSUMPTION, shown in the report.
NOT FOR CITATION until reviewed. Run:  py preshock/shock_paths.py
"""
import datetime as dt
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "preshock"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from infinity_gem import paths                                             # noqa: E402
import oil_shock_size as O                                             # noqa: E402
import agri_price_shock_size as A                                      # noqa: E402

FORECASTS = paths.DATA_RAW / "oil" / "forecasts"
EIA_OCT26 = FORECASTS / "EIA_STEO_Oct2026_base.xlsx"
EIA_FEB26 = FORECASTS / "EIA_STEO_Feb2026_base.xlsx"
DBCC_192 = {"low": 60.0, "central": 65.0, "high": 70.0}     # Dubai US$/bbl, 2026-2030 (9 Dec 2025)
DBCC_193_LATER = 70.0                                       # Dubai US$/bbl, 2028-2030, midpoint of 60-80 (8 Jul 2026)
YEARS = (2025, 2026, 2027, 2028, 2029, 2030)
GOV_CONS = paths.DATA_RAW / "macro" / "PSA_OpenSTAT_0542B5BCNQ1_construction_GFCF_by_sector_quarterly_2000-2026.csv"


def eia_monthly(path=EIA_OCT26) -> pd.DataFrame:
    """EIA STEO table 2, monthly: Brent (US$/bbl), US wholesale diesel and gasoline (US$/gal)."""
    t = pd.read_excel(path, sheet_name="2tab", header=None)
    yrs, mos = t.iloc[2, 2:].ffill(), t.iloc[3, 2:]
    idx = pd.PeriodIndex([f"{int(y)}-{m}" for y, m in zip(yrs, mos)], freq="M")
    out = {}
    for code, name in (("BREPUUS", "brent"), ("DSWHUUS_$", "diesel"), ("MGWHUUS_$", "gasoline")):
        r = t.index[t.iloc[:, 0] == code][0]
        out[name] = pd.Series(pd.to_numeric(t.iloc[r, 2:].values, errors="coerce"), index=idx)
    return pd.DataFrame(out)


def oil_actual_monthly() -> pd.DataFrame:
    """Monthly Dubai crude (World Bank Pink Sheet, CC BY 4.0) and US wholesale diesel and gasoline (EIA STEO history,
    public domain) as the fuel-product cost proxies, 2025 on. Public version (Infinity GEM): the development copy read
    weekly prices from a compiled tracker that may not be redistributed; only ratios of these prices enter the shocks."""
    wb = pd.read_csv(paths.DATA_RAW / "macro" / "WorldBank_PinkSheet_crude_oil_monthly_1960-2026.csv", comment="#")
    dubai = pd.Series(wb["crude_dubai_usd_bbl"].astype(float).values, index=pd.PeriodIndex(wb["month"], freq="M"))
    eia = eia_monthly()
    d = pd.DataFrame({"dubai": dubai}).join(eia[["diesel", "gasoline"]], how="left")
    d = d.loc["2025-01":]
    return d[d["dubai"].notna() & d["diesel"].notna() & d["gasoline"].notna()]


# 0.3.13 (12 Nov 2026; opt-in): the same three columns from public data only. SOURCE notes:
# data/raw/oil/public/_SOURCE_NOTE.md (MBIE) and the header lines of the World Bank file (DATA_INVENTORY.md rows). Check OL1.
OIL_SOURCES = ("tracker", "public-mbie", "public-worldbank")
# 12 Nov 2026, about 10:10 PM: the default is MBIE's public series. Checked first
# in a browser against MBIE's own weekly-table.csv (mbie.govt.nz, last modified 10 Nov 2026): 382 of 384 values for 2025w01-2026w44
# identical, every Dubai price included; the 2 differences are MBIE's later revision of the provisional 2026w44 importer costs
# (diesel 219.30 vs 220.14, petrol 178.34 vs 181.37 NZD c/L). MBIE does not define its Dubai price beyond Figure.NZ's "a medium
# sour crude oil extracted from Dubai" (data from Envisory, formerly Hale & Twomey): a caveat, not asked. The World Bank's Dubai
# is the stated sensitivity; "tracker" was the default before 12 Nov 2026 (in this repository it reads public World Bank and EIA series instead).
DEFAULT_OIL_SOURCE = __import__("os").environ.get("INFINITY_GEM_OIL_SOURCE", "") or "public-mbie"   # INFINITY_GEM_OIL_SOURCE=tracker: runs before 12 Nov
if DEFAULT_OIL_SOURCE not in OIL_SOURCES:
    raise ValueError(f"INFINITY_GEM_OIL_SOURCE must be one of {OIL_SOURCES}, not {DEFAULT_OIL_SOURCE!r}")
MBIE_WEEKLY = paths.DATA_RAW / "oil" / "public" / "MBIE_Weekly_Fuel_Price_Monitoring_4_November_2026_via_FigureNZ.csv"
WB_CRUDE_MONTHLY = (paths.DATA_RAW / "macro" / "inflation_forecast_downloads_2026-11-05"
                    / "WorldBank_PinkSheet_crude_oil_monthly_1960-2026.csv")


def mbie_weekly(path=MBIE_WEEKLY) -> pd.DataFrame:
    """MBIE Weekly Fuel Price Monitoring (New Zealand), one row per week: MBIE's weekly Dubai (USD/bbl), the importer costs of
    diesel and regular petrol (NZD c/L), the exchange rate (USD per NZD) and MBIE's status flag, indexed by the week's starting
    Tuesday (MBIE dates a week by its Friday; the tracker's "Week starting (Tue)" = that Friday - 3 days), with the importer
    costs in US cents per litre (per week NZ c/L x USD/NZD, as oil_actual_monthly() converts the tracker's MBIE columns)."""
    t = pd.read_csv(path)
    t["Date"] = pd.to_datetime(t["Date"])

    def ser(fuel, var, unit):
        s = t[(t["Variable"] == var) & (t["Unit"] == unit) & ((t["Fuel"] == fuel) if fuel else t["Fuel"].isna())]
        if s["Date"].duplicated().any():
            raise ValueError(f"MBIE weekly table: more than one value a week for {fuel} {var} ({unit})")
        return s.set_index("Date")

    fx = ser(None, "Exchange rate", "USD/NZD")
    w = pd.DataFrame({"week": fx["Week"], "status": fx["Status"], "usd_per_nzd": fx["Value"]})
    w["dubai"] = ser(None, "Dubai crude price", "USD/bbl")["Value"]
    w["diesel_nzc_l"] = ser("Diesel", "Importer cost", "NZD c/L")["Value"]
    w["petrol_nzc_l"] = ser("Regular Petrol", "Importer cost", "NZD c/L")["Value"]
    start = w.index - pd.Timedelta(days=3)
    if not (start.dayofweek == 1).all():
        raise ValueError("MBIE weekly table: a week's date is not a Friday")
    w.index = pd.DatetimeIndex(start, name="week_starting_tue")
    w["diesel"] = w["diesel_nzc_l"] * w["usd_per_nzd"]
    w["gasoline"] = w["petrol_nzc_l"] * w["usd_per_nzd"]
    return w.sort_index()


def worldbank_dubai_monthly(path=WB_CRUDE_MONTHLY) -> pd.Series:
    """World Bank Pink Sheet, monthly 'Crude oil, Dubai' (Dubai Fateh 32 API; US$/bbl), as a monthly PeriodIndex series."""
    wb = pd.read_csv(path, comment="#")
    s = pd.Series(pd.to_numeric(wb["crude_dubai_usd_bbl"], errors="coerce").values,
                  index=pd.PeriodIndex(wb["month"], freq="M"), name="dubai")
    return s.dropna()


def oil_public_monthly(dubai="mbie") -> pd.DataFrame:
    """Monthly Dubai (US$/bbl) and diesel and gasoline importer costs (US cents per litre), 2025 on, from public data only:
    the columns and units of oil_actual_monthly(). dubai="mbie": MBIE's weekly Dubai, monthly mean of its weeks (the series the
    tracker's Dubai column equals); dubai="worldbank": the World Bank Pink Sheet's monthly Dubai. Diesel and gasoline: MBIE's
    importer costs either way. Each column is the mean of the weeks of the month (by starting Tuesday) that have it; a month
    with no World Bank value has a missing Dubai (oil_paths() drops it)."""
    if dubai not in ("mbie", "worldbank"):
        raise ValueError(f"oil_public_monthly: dubai must be 'mbie' or 'worldbank', not {dubai!r}")
    w = mbie_weekly()
    w["month"] = w.index.to_period("M")
    g = w.groupby("month")
    d = pd.DataFrame({"dubai": g["dubai"].mean(), "diesel": g["diesel"].mean(), "gasoline": g["gasoline"].mean()})
    if dubai == "worldbank":
        d["dubai"] = worldbank_dubai_monthly().reindex(d.index)
    d.index.name = "month"
    return d.loc["2025-01":]


def oil_monthly(source=None) -> pd.DataFrame:
    """The monthly oil prices oil_paths() uses: source "tracker" (DEFAULT_OIL_SOURCE; oil_actual_monthly()), "public-mbie" or
    "public-worldbank" (oil_public_monthly). None = DEFAULT_OIL_SOURCE."""
    source = DEFAULT_OIL_SOURCE if source is None else source
    if source not in OIL_SOURCES:
        raise ValueError(f"oil source must be one of {OIL_SOURCES}, not {source!r}")
    if source == "tracker":
        return oil_actual_monthly()
    return oil_public_monthly("mbie" if source == "public-mbie" else "worldbank")


def oil_paths(no_conflict="central", forecast="EIA", source=None) -> pd.DataFrame:
    """% shocks by year: crude (Dubai) and fuel products (weighted). forecast: 'EIA' (central) or
    'no change' (prices stay at the latest actual month through 2027: the stochastic model's centre).
    source (12 Nov 2026; opt-in): None or "tracker" = as before; "public-mbie" or "public-worldbank" (oil_monthly)."""
    act = oil_monthly(source).dropna()
    last = act.index.max()
    eia = eia_monthly()
    months = pd.period_range("2026-01", "2027-12", freq="M")
    path = act.reindex(months)
    for m in months[months > last]:
        if forecast == "EIA":
            path.loc[m, "dubai"] = act.loc[last, "dubai"] * eia.loc[m, "brent"] / eia.loc[last, "brent"]
            path.loc[m, "diesel"] = act.loc[last, "diesel"] * eia.loc[m, "diesel"] / eia.loc[last, "diesel"]
            path.loc[m, "gasoline"] = act.loc[last, "gasoline"] * eia.loc[m, "gasoline"] / eia.loc[last, "gasoline"]
        else:
            path.loc[m] = act.loc[last]
    jf = act.loc["2026-01":"2026-02"].mean()
    cf = DBCC_192[no_conflict]
    rows = {}
    for y in (2026, 2027):
        a = path[path.index.year == y].mean()
        crude = a["dubai"] / cf - 1
        dsl = a["diesel"] / (jf["diesel"] * cf / jf["dubai"]) - 1
        gas = a["gasoline"] / (jf["gasoline"] * cf / jf["dubai"]) - 1
        prod = O.MIX["diesel"] * dsl + O.MIX["gasoline"] * gas + O.MIX["LPG and other products"] * crude
        rows[y] = {"crude (Dubai)": crude * 100, "diesel": dsl * 100, "gasoline": gas * 100, "fuel products, weighted": prod * 100,
                   "Dubai, US$/bbl": a["dubai"], "actual months": int((path.index.year == y).sum() - (path.index[path.index.year == y] > last).sum())}
    for y in (2028, 2029, 2030):
        c = DBCC_193_LATER / cf - 1
        rows[y] = {"crude (Dubai)": c * 100, "diesel": c * 100, "gasoline": c * 100, "fuel products, weighted": c * 100,
                   "Dubai, US$/bbl": DBCC_193_LATER, "actual months": 0}
    out = pd.DataFrame(rows).T
    out.attrs.update(latest=str(last), no_conflict=cf, forecast=forecast)
    return out


def food_paths() -> pd.DataFrame:
    """% shocks by year (2026-2030) for world rice (Viet Nam 5%) and urea: actual months + no-change forecast, against
    the January-February 2026 level."""
    p = A.prices()[["rice, Viet Nam 5% (central)", "urea (central)"]].dropna()
    last = p.index.max()
    jf = p.loc["2026-01":"2026-02"].mean()
    rows = {}
    for y in range(2026, 2031):
        months = pd.period_range(f"{y}-01", f"{y}-12", freq="M")
        v = pd.DataFrame([p.loc[m] if m <= last else p.loc[last] for m in months], index=months)
        rows[y] = ((v.mean() / jf - 1) * 100).rename({"rice, Viet Nam 5% (central)": "world rice", "urea (central)": "urea"})
    out = pd.DataFrame(rows).T
    out.attrs["latest"] = str(last)
    return out


def public_works() -> dict:
    """General government construction shortfall vs the same period of 2024, ₱ bn current prices: {'2025', '2026 central',
    '2026 low'} plus the quarterly data used."""
    g = pd.read_csv(GOV_CONS, comment="#").set_index("Institutional Sector")
    row = g.loc["..General government"]
    q = {c.replace("At Current Prices ", ""): float(pd.to_numeric(row[c], errors="coerce")) / 1000 for c in g.columns
         if c.startswith("At Current Prices 202")}                    # PSA publishes ₱ million; here ₱ bn
    h = lambda y, a, b: q[f"{y} Q{a}"] + q[f"{y} Q{b}"]
    h1_24, h2_24, h1_25, h2_25, h1_26 = h(2024, 1, 2), h(2024, 3, 4), h(2025, 1, 2), h(2025, 3, 4), h(2026, 1, 2)
    h2_26c = h2_25 * h1_26 / h1_25
    return {"2025": (h1_25 + h2_25) - (h1_24 + h2_24),
            "2026 central": (h1_26 + h2_26c) - (h1_24 + h2_24),
            "2026 low": (h1_26 + h2_25) - (h1_24 + h2_24),
            "H1 2026 vs H1 2025 (%)": (h1_26 / h1_25 - 1) * 100,
            "quarters": q}


# DPWH budget execution, all funds, ₱ bn (DBM SAAODB "By Agency"). "Commitments" = obligations incurred; "available" = current-year plus continuing appropriations.
DPWH = {"2024 available": 1407.0, "2024 commitments": 1236.5,              # FY2024 SAAODB (preliminary, upd. 29 Apr 2025)
        "2025 available": 1380.8, "2025 commitments": 1077.2,              # FY2025 SAAODB (final, 7 Jul 2026)
        "2025 Jun current-year rate": 783.8 / 1214.6, "2025 Dec current-year rate": 938.0 / 1220.0,   # FY2025 Q2 and Q4
        "2026 current-year available": 557.6, "2026 Jun current-year commitments": 84.9,             # FY2026 Q2 (12 Aug 2026)
        "2027 NEP": 643.9}                                                 # CPBRD Agency Budget Notes via PDI, 1 Sept 2026 (B28)
GG_CONSTRUCTION = {2024: 1624.7, 2025: 1361.0}   # PSA 0542B5BCNQ1, general government, current prices, ₱ bn (sum of quarters)


def public_works_2027() -> dict:
    """2027 general government construction against 2024 (₱ bn, current prices; the same unit as public_works()), from the
    2027 budget and DPWH's commitment rate (16 Oct 2026: the latest actual rate as central, earlier rates as recovery).

    Why commitments and not payouts: from 2024 to 2025, DPWH commitments fell 12.9% and PSA's general government construction
    16.2%, while DPWH payouts fell 34.5% (payouts lag the work; DBM's payout figures exclude prior-year bills). The rate CPBRD
    quotes (payouts / available) is DBM's own ratio (53.3% 2024, 35.6% 2025: checked against the SAAODB, 16 Oct 2026).
    Money available to DPWH in 2027 = the 2027 NEP + FY2026 money still uncommitted at end-2026 (valid to 31 Dec 2027,
    RA 12314 Sec. 77): 2026 H2 commits at 2025's H2 pace (Dec rate minus June rate of 2025), from the June 2026 rate.
    2027 construction / 2024 construction = 2027 commitments / 2024 commitments (backtest: this ratio gives 2025 construction
    ₱1,415 bn against PSA's ₱1,361 bn, 4% high)."""
    d = DPWH
    r24, r25 = d["2024 commitments"] / d["2024 available"], d["2025 commitments"] / d["2025 available"]
    jun26 = d["2026 Jun current-year commitments"] / d["2026 current-year available"]
    dec26 = min(1.0, jun26 + d["2025 Dec current-year rate"] - d["2025 Jun current-year rate"])
    carry = d["2026 current-year available"] * (1 - dec26)
    avail27 = d["2027 NEP"] + carry
    out = {"2026 year-end commitment rate (projected)": dec26 * 100, "FY2026 money carried into 2027": carry,
           "available to DPWH in 2027": avail27, "commitment rate 2024 (%)": r24 * 100, "commitment rate 2025 (%)": r25 * 100}
    for case, r in (("2027 NEP x 2025 rate (central)", r25), ("2027 NEP x 2024 rate (recovery)", r24)):
        ratio = r * avail27 / d["2024 commitments"]
        out[case] = GG_CONSTRUCTION[2024] * (ratio - 1)
    out["backtest 2025 (ratio method vs PSA, ₱ bn)"] = (GG_CONSTRUCTION[2024] * d["2025 commitments"] / d["2024 commitments"],
                                                       GG_CONSTRUCTION[2025])
    return out


def main():
    pd.set_option("display.width", 200)
    L = [f"# Shock paths from data and published forecasts ({dt.date.today():%d %B %Y})", "",
         "**NOT FOR CITATION** (Infinity GEM 0.3.7). Script: `preshock/shock_paths.py` (rule and sources in its notes). "
         "Each year's shock = that calendar year's average price (actual months, then forecast) against the no-conflict price.", ""]
    for nc in ("central", "low", "high"):
        t = oil_paths(nc)
        L += [f"## Oil, EIA forecast, no-conflict Dubai US${DBCC_192[nc]:.0f} (DBCC 192nd, {nc})", "",
              t.round(1).to_markdown(), ""]
        print(nc, "\n", t.round(1).to_string())
    t = oil_paths("central", "no change")
    L += ["## Oil, no-change forecast (prices stay at the latest month through 2027), no-conflict US$65", "", t.round(1).to_markdown(), ""]
    print("no change\n", t.round(1).to_string())
    f = food_paths()
    L += [f"## World rice and urea (no-change forecast from {f.attrs['latest']}; vs January-February 2026)", "", f.round(1).to_markdown(), ""]
    print(f.round(1).to_string())
    pw = public_works()
    L += ["## Public works: general government construction vs the same period of 2024 (₱ bn, current prices; PSA 0542B5BCNQ1)", "",
          f"- 2025: {pw['2025']:,.1f} (DBM cross-check: -238.3 for H2 2025 vs H2 2024)",
          f"- 2026 central (H2 at H1's year-on-year rate, {pw['H1 2026 vs H1 2025 (%)']:+.1f}%): {pw['2026 central']:,.1f}",
          f"- 2026 lower bound (H2 2026 = H2 2025): {pw['2026 low']:,.1f}", ""]
    print({k: v for k, v in pw.items() if k != "quarters"})
    out = paths.output_dir() / f"shock_paths_{dt.date.today():%Y%m%d}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print("saved", out)


if __name__ == "__main__":
    main()
