"""World coal and LNG price paths for the opt-in coal and LNG part of the oil shock on Infinity GEM SAM v0.7 (24 Oct 2026).

RESEARCH, NOT FOR CITATION. Rule (preshock/shock_paths.py, the 2026 scenarios' rule for every world price): shock(t) = average price
in calendar year t (actual months + forecast months) / the pre-conflict level - 1, for 2026-2030.

Series used: the World Bank Pink Sheet's monthly coal (Australian, US$ a tonne) and LNG (Japan, US$ per MMBtu) prices
(CMO-Historical-Data-Monthly.xlsx, sheet 'Monthly Prices'). ON DISK since 24 Oct 2026, 02:15: PINK_COAL_LNG below
(a 'month' column YYYY-MM and the sheet's columns 'Coal, Australian' = Newcastle 6,000 kcal/kg f.o.b., 'Coal, South African'
= Richards Bay 6,000 kcal/kg f.o.b. and 'Liquefied natural gas, Japan' = import price c.i.f.), written from the workbook
'Updated on October 02, 2026' (data through September 2026), which is kept in data/raw/macro/
WorldBank_PinkSheet_CMO_Historical_Data_Monthly_downloaded_2026-10-24/. Whenever that CSV exists this script uses it; the
South African coal series is reported as a sensitivity only (outputs/coal_lng_price_paths_<stamp>_sensitivity_coal_south_africa.csv),
never written to the path file. Without the CSV (first run, 24 Oct 2026, 00:56; kept as the fallback) the script used:

PROXY (fallback only): the World Bank ENERGY price index (nominal US$, 2010 = 100), which covers coal, crude oil and natural gas,
crude oil with by far the largest weight (the index weights are not on disk either). The proxy moves mostly with crude oil: it
says that energy prices as a whole rose about as much as oil in 2026 (Jan-Feb to Mar-Sep: +38.4%, Dubai +31.0%), not how much
coal and LNG each rose. Coal and LNG both take the proxy's path. Results with it are a case in which coal and LNG rose with
oil, not a measurement of their prices.

Pre-conflict level: the January-February 2026 average (no official pre-conflict assumption exists for coal or LNG).
Forecast months: for the proxy, October 2026 to December 2027 move with EIA's Brent forecast (Short-Term Energy Outlook of
1 Oct 2026; preshock/shock_paths.eia_monthly), as the 2026 scenarios move Dubai (the proxy is mostly crude oil); 2028-2030 take the crude change of the 2026 scenarios (DBCC 193rd meeting, US$70, against the 192nd meeting's US$65). For the World Bank's own coal and LNG
series: the no-change forecast for every later month and year (no official forecast on disk), as the 2026 scenarios do for rice and
urea.
Outputs: data/processed/coal_lng_price_paths_2026-2030.csv (year, coal %, lng %, basis; '#' lines with the sources), read by
infinity_gem.oil.coal_lng_paths; outputs/coal_lng_price_paths_<stamp>_monthly.csv (the monthly path).
Run (Git Bash): PYTHONIOENCODING=utf-8 py research/coal_lng_prices/coal_lng_paths.py
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "preshock"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from infinity_gem import paths                                          # noqa: E402

INDICES = paths.DATA_RAW / "macro" / "WorldBank_PinkSheet_price_indices_monthly_1960-latest.csv"
PINK_COAL_LNG = paths.DATA_RAW / "macro" / "WorldBank_PinkSheet_coal_lng_monthly.csv"     # on disk since 24 Oct 2026, 02:15
COLS = {"Coal, Australian": "coal", "Liquefied natural gas, Japan": "lng"}
OUT = paths.DATA_PROCESSED / "coal_lng_price_paths_2026-2030.csv"
LAST_FORECAST = pd.Period("2027-12", "M")                            # EIA's STEO of 1 Oct 2026 runs to December 2027


def monthly() -> tuple:
    """Monthly coal and LNG prices (or the proxy for both) and a description of the source."""
    if PINK_COAL_LNG.exists():
        d = pd.read_csv(PINK_COAL_LNG, comment="#")
        s = d.set_index(pd.PeriodIndex(d["month"].astype(str), freq="M"))[list(COLS)].apply(pd.to_numeric, errors="coerce")
        return s.rename(columns=COLS).dropna(), "series", (
            f"World Bank Pink Sheet monthly prices ({PINK_COAL_LNG.name}: coal = 'Coal, Australian', Newcastle 6,000 kcal/kg f.o.b., "
            "US$/mt; LNG = 'Liquefied natural gas, Japan', import price c.i.f., US$/mmbtu)")
    d = pd.read_csv(INDICES, comment="#")
    e = pd.Series(pd.to_numeric(d["Energy"], errors="coerce").values, index=pd.PeriodIndex(d["month"].astype(str), freq="M")).dropna()
    return pd.DataFrame({"coal": e, "lng": e}), "proxy", (
        f"PROXY: World Bank energy price index (nominal US$, 2010 = 100; coal, crude oil and natural gas, mostly crude oil), "
        f"{INDICES.name}; the Pink Sheet's coal and LNG series are not on disk")


def build() -> tuple:
    import shock_paths as SP
    m, kind, src = monthly()
    last = m.index.max()
    months = pd.period_range("2026-01", "2030-12", freq="M")
    path = m.reindex(months)
    fut = months[months > last]
    if kind == "proxy":
        eia = SP.eia_monthly()
        for mo in fut:
            if mo <= LAST_FORECAST:
                path.loc[mo] = m.loc[last] * float(eia.loc[mo, "brent"] / eia.loc[last, "brent"])
    else:
        for mo in fut:
            path.loc[mo] = m.loc[last]                              # no-change forecast
    jf = m.loc[pd.Period("2026-01", "M"):pd.Period("2026-02", "M")].mean()
    crude_later = SP.DBCC_193_LATER / SP.DBCC_192["central"] - 1    # the 2026 scenarios' crude change, 2028-2030
    rows = {}
    for y in range(2026, 2031):
        if kind == "proxy" and y > LAST_FORECAST.year:
            rows[y] = {"coal": crude_later * 100, "lng": crude_later * 100,
                       "basis": "proxy: the 2026 scenarios' crude change (DBCC 193rd US$70 / 192nd US$65)"}
            path.loc[path.index.year == y] = (jf * (1 + crude_later)).values
        else:
            a = path[path.index.year == y].mean()
            n_act = int(((path.index.year == y) & (path.index <= last)).sum())
            rows[y] = {"coal": (a["coal"] / jf["coal"] - 1) * 100, "lng": (a["lng"] / jf["lng"] - 1) * 100,
                       "basis": (f"{'proxy: energy index' if kind == 'proxy' else 'World Bank coal and LNG'}, {n_act} actual months"
                                 + (", the rest with EIA's Brent forecast" if kind == "proxy" and n_act < 12 else
                                    ", the rest no change" if n_act < 12 else ""))}
    out = pd.DataFrame(rows).T
    out.index.name = "year"
    return out, path, kind, src, last, jf


def main():
    out, path, kind, src, last, jf = build()
    stamp = dt.datetime.now()
    head = ["# World coal and LNG price changes by calendar year, % against the January-February 2026 level (the pre-conflict level),",
            "# for the opt-in coal and LNG part of the oil shock on Infinity GEM SAM v0.7 (infinity_gem.oil.coal_lng_paths, coal_lng_shock).",
            f"# Source: {src}. Latest month on disk: {last}.",
            "# Rule: preshock/shock_paths.py (calendar-year average of actual and forecast months against the pre-conflict level).",
            ("# Forecast: EIA STEO 1 Oct 2026 Brent path to Dec 2027 (as the 2026 scenarios move Dubai); 2028-2030 the 2026 scenarios' crude change "
             "(DBCC 193rd US$70 / 192nd US$65)." if kind == "proxy" else "# Forecast: no change from the latest month (as the 2026 scenarios "
             "does for rice and urea)."),
            ("# CAUTION: a proxy that is mostly crude oil; coal and LNG take the same path. Not a measurement of coal or LNG prices."
             if kind == "proxy" else "# World Bank Pink Sheet (CC BY 4.0)."),
            f"# Written {stamp:%Y-%m-%d %H:%M} by research/coal_lng_prices/coal_lng_paths.py. RESEARCH, NOT FOR CITATION."]
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join(head) + "\n")
        out.to_csv(fh, float_format="%.6f")
    mon = path.copy()
    mon["January-February 2026 level"] = [jf["coal"]] * len(mon)
    mon["actual"] = mon.index <= last
    mon.index = mon.index.astype(str)
    f = paths.output_dir() / f"coal_lng_price_paths_{stamp:%Y%m%d_%H%M}_monthly.csv"
    mon.to_csv(f)
    pd.set_option("display.width", 200)
    print(out.to_string())
    print(f"source: {src}; latest month {last}; Jan-Feb 2026 level {jf['coal']:.2f}")
    print("saved", OUT, "and", f)
    if kind == "series":                                             # sensitivity only: South African coal, same rule
        d = pd.read_csv(PINK_COAL_LNG, comment="#")
        if "Coal, South African" in d.columns:
            sa = pd.Series(pd.to_numeric(d["Coal, South African"], errors="coerce").values,
                           index=pd.PeriodIndex(d["month"].astype(str), freq="M")).dropna()
            jf_sa, last_sa = sa.loc[pd.Period("2026-01", "M"):pd.Period("2026-02", "M")].mean(), sa.index.max()
            yr = {y: (pd.Series([sa.loc[mo] if mo <= last_sa else sa.loc[last_sa]
                                 for mo in pd.period_range(f"{y}-01", f"{y}-12", freq="M")]).mean() / jf_sa - 1) * 100
                  for y in range(2026, 2031)}
            s_out = pd.DataFrame({"coal, South African (%)": yr, "coal, Australian (%; the path file)": out["coal"].astype(float)})
            s_out.index.name = "year"
            fs = paths.output_dir() / f"coal_lng_price_paths_{stamp:%Y%m%d_%H%M}_sensitivity_coal_south_africa.csv"
            s_out.to_csv(fs)
            print("sensitivity (not used by the model): South African coal (Richards Bay), same rule; latest", last_sa)
            print(s_out.round(3).to_string())
            print("saved", fs)


if __name__ == "__main__":
    main()
