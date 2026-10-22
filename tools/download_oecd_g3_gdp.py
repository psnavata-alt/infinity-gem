"""Download quarterly real GDP of the United States, the euro area and Japan from the OECD's Quarterly National Accounts
(22 Oct 2026), for the DSGE's world-output observable (research/dsge/ph_data.py, world_growth).

Why: the development copy reads these series from FRED copies, and FRED's terms of use do not allow stored FRED content
to be passed to third parties. The OECD publishes the same national-accounts series (the US and Japan identical to FRED's
growth rates; the euro area as the current 20-member area, FRED's being the 19-member area: G3 average growth differs by
0.005 percentage point on average, 0.024 at most, 2000Q2-2026Q2). The OECD's data are open (OECD press release, 1 July
2024); the national publishers' own terms allow reuse too (U.S. Bureau of Economic Analysis: a US government work;
Eurostat: reuse authorised with acknowledgment; Cabinet Office of Japan: numerical data not subject to copyright).

Series: OECD Data Explorer, dataflow OECD.SDD.NAD:DSD_NAMAIN1@DF_QNA(1.1), gross domestic product (B1GQ), chain-linked
volume (price base L), national currency, millions, calendar and seasonally adjusted (Y), not annualised (N), table T0102.

Run: py -X utf8 tools/download_oecd_g3_gdp.py      (writes data/raw/world/OECD_QNA_G3_real_GDP_downloaded_<date>/)
The files have the layout of the FRED copies (observation_date, value), so world_growth() reads either.
"""
from __future__ import annotations

import datetime as dt
import io
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KEY = "Q.Y.USA+EA+JPN.S1.S1.B1GQ._Z._Z._Z.XDC.L.N.T0102"
URL = ("https://sdmx.oecd.org/public/rest/data/OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA,1.1/" + KEY +
       "?startPeriod=2000-Q1&dimensionAtObservation=AllDimensions&format=csvfilewithlabels")
FILES = {"USA": "OECD_QNA_USA_real_GDP_quarterly",
         "EA": "OECD_QNA_EA20_euro_area_real_GDP_quarterly",
         "JPN": "OECD_QNA_JPN_real_GDP_quarterly"}
FRED = ROOT / "data" / "raw" / "world" / "FRED_world_activity_downloaded_2026-10-20"
FRED_FILES = {"USA": "FRED_GDPC1_US_real_GDP_quarterly_2000Q1-2026Q2.csv",
              "EA": "FRED_CLVMNACSCAB1GQEA19_euro_area_real_GDP_quarterly_2000Q1-2026Q2.csv",
              "JPN": "FRED_JPNRGDPEXP_Japan_real_GDP_quarterly_2000Q1-2026Q2.csv"}


def fetch() -> pd.DataFrame:
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        raw = r.read()
    return pd.read_csv(io.BytesIO(raw)), raw


def series(d: pd.DataFrame, area: str) -> pd.Series:
    s = d[d.REF_AREA == area].set_index("TIME_PERIOD")["OBS_VALUE"].astype(float)
    s.index = pd.PeriodIndex([p.replace("-Q", "Q") for p in s.index], freq="Q")
    return s.sort_index()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    d, raw = fetch()
    today = dt.date.today()
    out = ROOT / "data" / "raw" / "world" / f"OECD_QNA_G3_real_GDP_downloaded_{today:%Y-%m-%d}"
    out.mkdir(parents=True, exist_ok=True)
    lines = []
    for area, stem in FILES.items():
        s = series(d, area)
        if s.empty:
            print(f"no data for {area}")
            return 1
        name = f"{stem}_{s.index.min()}-{s.index.max()}.csv"
        pd.DataFrame({"observation_date": s.index.start_time.strftime("%Y-%m-%d"),
                      f"{area}_B1GQ_L_N": np.round(s.values, 1)}).to_csv(out / name, index=False, lineterminator="\n")
        lines.append(f"| `{name}` | {area} | {s.index.min()}-{s.index.max()} | {len(s)} |")
        print(f"wrote {name}: {len(s)} quarters")
    # the comparison with the FRED copies, when they are present (development copy only)
    comp = []
    if FRED.is_dir():
        go, gf = [], []
        for area, f in FRED_FILES.items():
            fr = pd.read_csv(FRED / f)
            sf = pd.Series(fr.iloc[:, 1].astype(float).values,
                           index=pd.PeriodIndex(pd.to_datetime(fr["observation_date"]), freq="Q"))
            a, b = 100 * np.log(series(d, area)).diff(), 100 * np.log(sf).diff()
            j = pd.concat([a, b], axis=1, keys=["oecd", "fred"]).dropna()
            comp.append(f"| {area} | {len(j)} | {j.corr().iloc[0, 1]:.5f} | {(j.oecd - j.fred).abs().mean():.3f} | "
                        f"{(j.oecd - j.fred).abs().max():.3f} |")
            go.append(a)
            gf.append(b)
        g = pd.concat([pd.concat(go, axis=1).mean(axis=1), pd.concat(gf, axis=1).mean(axis=1)], axis=1,
                      keys=["oecd", "fred"]).dropna()
        comp.append(f"| G3 average | {len(g)} | {g.corr().iloc[0, 1]:.5f} | {(g.oecd - g.fred).abs().mean():.3f} | "
                    f"{(g.oecd - g.fred).abs().max():.3f} |")
    note = [
        "# Quarterly real GDP of the United States, the euro area and Japan (OECD Quarterly National Accounts)",
        "",
        f"Downloaded {today:%d %B %Y} by `tools/download_oecd_g3_gdp.py` from the OECD Data Explorer's SDMX API:",
        "",
        f"`{URL}`",
        "",
        "Dataflow OECD.SDD.NAD:DSD_NAMAIN1@DF_QNA(1.1); gross domestic product (B1GQ); chain-linked volume (price base L);",
        "national currency, millions; calendar and seasonally adjusted; not annualised; table T0102. The euro area is",
        "the OECD's 'EA' aggregate (the current 20 members).",
        "",
        "| File | Area | Quarters | Observations |",
        "|---|---|---|---|",
        *lines,
        "",
        "**Source and terms.** OECD (2026), Quarterly National Accounts, OECD Data Explorer (accessed on the date above).",
        "The OECD's data are open (OECD press release, 1 July 2024:",
        "https://www.oecd.org/en/about/news/press-releases/2024/07/oecd-data-publications-and-analysis-become-freely-accessible.html).",
        "The national sources: U.S. Bureau of Economic Analysis (a US government work, public domain); Eurostat",
        "(reuse authorised provided the source is acknowledged); Cabinet Office, Government of Japan (numerical data",
        "are not subject to copyright). Values are as published, rounded to 0.1 million; only the layout was changed",
        "(observation_date, value).",
        "",
        "**Use.** `research/dsge/ph_data.py` (`world_growth`): world output growth = the simple average of the three",
        "series' quarterly log growth.",
    ]
    if comp:
        note += ["", "**Against the FRED copies** (quarterly log growth x 100, percentage points):", "",
                 "| Series | Quarters | Correlation | Mean absolute difference | Largest difference |",
                 "|---|---|---|---|---|", *comp]
    (out / "SOURCE_NOTE.md").write_text("\n".join(note) + "\n", encoding="utf-8")
    print(f"wrote {out / 'SOURCE_NOTE.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
