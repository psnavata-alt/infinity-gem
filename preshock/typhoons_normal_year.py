"""Typhoons: is 2025 or 2026 damage above a normal year? (16 Oct 2026).

NOT FOR CITATION until reviewed. Run:  py preshock/typhoons_normal_year.py

Rule: the government's pre-shock forecast already assumes a normal typhoon year, so only damage ABOVE a normal year is a
shock. Normal year = the median (and mean) of annual tropical-cyclone damage over the latest seasons with a consistent
published total, in 2026 pesos (PSA CPI, annual average, 2018=100).

Annual damage (agriculture + infrastructure; NDRRMC totals as published in PAGASA's Annual Report on Philippine Tropical
Cyclones, ARTC; PDFs in data/raw/disasters/pagasa_annual_tc_reports/ except 2023, which is 72 MB: URL below):
  2017  ₱6.639 bn   ARTC 2017 p.28            2018  ₱48.679 bn  ARTC 2018 p.40, Table 3.5
  2019  ₱11.270 bn  ARTC 2019 p.44            2020  ₱44.222 bn  ARTC 2020 p.44
  2021  ₱61.323 bn  ARTC 2021 rev1 p.53 (p.6 calls it 'adjusted for inflation'; p.53 gives it as the season total: taken as published)
  2022  ₱30.077 bn  ARTC 2022 p.44 (from 2022 the total includes 'other assets')
  2023  ₱18.089 bn  ARTC 2023 p.45 (https://pubfiles.pagasa.dost.gov.ph/pagasaweb/files/tamss/weather/tcsummary/PAGASA_ARTC_2023.pdf)
  2024  not found (no ARTC 2024 published yet; search 16 Oct 2026)
2025 (all natural hazards, not typhoons only; PSA Compendium of Philippine Environment Statistics 2016-2025, Component 4
  highlights, read 16 Oct 2026): medium-scale events ₱39.34 bn (Table 4.21; includes the Bogo City, Cebu
  earthquake), large-scale TC Tino ₱3.30 bn (Table 4.22), small-scale ₱0.91 bn (Table 4.19): about ₱43.5 bn, an UPPER
  bound for typhoons.
2026 to date: ₱18.68 bn, tropical cyclones Luis, Maymay, Neneng, Pilandok and the enhanced southwest monsoon, as of 16 Sept
  2026 (NDRRMC via The Manila Times, 12 Oct 2026); the newspaper's 'at least ₱21.69 bn' adds an earthquake and local reports.
"""
import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DAMAGE = {2017: 6.639, 2018: 48.679, 2019: 11.270, 2020: 44.222, 2021: 61.323, 2022: 30.077, 2023: 18.089}
Y2025_UPPER = 39.34 + 3.30 + 0.91          # all natural hazards (PSA CPES 2016-2025), an upper bound for typhoons
Y2026_TO_SEP = 18.68                        # NDRRMC as of 16 Sept 2026 (TCs + enhanced monsoon)


def cpi_annual():
    f = ROOT / "data" / "raw" / "macro" / "PSA_OpenSTAT_0012M4ACP22_CPI_2018base_by_commodity_group_2018-latest.csv"
    d = pd.read_csv(f, comment="#")
    row = d[d["Commodity Description"].astype(str).str.strip() == "0 - ALL ITEMS"].iloc[0]
    out = {}
    for y in range(2017, 2027):
        cols = [c for c in d.columns if c.startswith(f"{y} ") and not c.endswith("Ave")]
        v = pd.to_numeric(row[cols], errors="coerce").dropna()
        if len(v):
            out[y] = float(v.mean())
    if 2017 not in out:                      # backcast table for 2017
        b = pd.read_csv(ROOT / "data" / "raw" / "macro" / "PSA_OpenSTAT_0012M4ACP28_CPI_2018base_by_commodity_group_1994-2017_backcast.csv", comment="#")
        rb = b[b["Commodity Description"].astype(str).str.strip() == "0 - ALL ITEMS"].iloc[0]
        cols = [c for c in b.columns if c.startswith("2017 ") and not c.endswith("Ave")]
        out[2017] = float(pd.to_numeric(rb[cols], errors="coerce").mean())
    return pd.Series(out)


def main():
    cpi = cpi_annual()
    to26 = cpi[2026] / cpi                   # 2026 = Jan-Sep average
    s = pd.DataFrame({"damage (₱ bn, as published)": pd.Series(DAMAGE)})
    s["CPI (2018=100, annual average)"] = cpi.reindex(s.index)
    s["damage (₱ bn, 2026 prices)"] = s.iloc[:, 0] * to26.reindex(s.index)
    real = s["damage (₱ bn, 2026 prices)"]
    normal_med, normal_mean = float(real.median()), float(real.mean())
    y25 = Y2025_UPPER * float(to26[2025])
    # a normal year's damage to mid-September: share of a season's damage before 16 Sept is not published; bound it
    L = [f"# Typhoons: is 2025 or 2026 above a normal year? ({dt.date.today():%d %b %Y})", "",
         "**NOT FOR CITATION until reviewed** (Infinity GEM 0.3.7). Script: `preshock/typhoons_normal_year.py` "
         "(sources and pages in its notes).", "",
         "## Annual tropical-cyclone damage (NDRRMC, via PAGASA's annual reports)", "",
         s.to_markdown(floatfmt=".2f"), "",
         f"**A normal year (2017-2023, 2026 prices):** median ₱{normal_med:.1f} bn; mean ₱{normal_mean:.1f} bn "
         f"(range ₱{real.min():.1f}-{real.max():.1f} bn). Seven seasons only; 2024 not yet published.", "",
         "## 2025 and 2026 against a normal year", "",
         f"- **2025:** all natural hazards, about ₱{Y2025_UPPER:.1f} bn (₱{y25:.1f} bn in 2026 prices), which includes the Bogo City "
         f"earthquake: an upper bound for typhoons. Against the normal year: {y25 - normal_med:+.1f} bn (median) or "
         f"{y25 - normal_mean:+.1f} bn (mean). **Not clearly above normal.**",
         f"- **2026 to 16 September:** ₱{Y2026_TO_SEP:.2f} bn (typhoons and the enhanced monsoon), {Y2026_TO_SEP / normal_med * 100:.0f}% of a "
         "normal full year. The October-December peak is still to come. **Not above normal so far.**", "",
         "## Conclusion", "",
         "- The data so far support the combined run's choice to leave typhoons out: neither 2025 nor 2026 to date is shown to be "
         "above a normal year, which the pre-shock forecast already assumes.",
         "- **Revisit** when NDRRMC's full-year 2026 total is out (January 2027), and when PAGASA publishes ARTC 2024-2025. If 2026 "
         "ends above the normal year, the excess enters as damage to public capital (`kg_loss`, already in the engine) and to crops "
         "in the year it happens.",
         "- Caution: damage reporting changed over time (from 2022 the totals include 'other assets'), and a seven-season median is a "
         "thin base. A longer consistent series (NDRRMC final reports since 2000) would firm up the normal year.", ""]
    out = ROOT / "outputs" / f"typhoons_normal_year_{dt.date.today():%Y%m%d}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    s.to_csv(ROOT / "outputs" / f"typhoons_normal_year_{dt.date.today():%Y%m%d}.csv")
    print("\n".join(L))


if __name__ == "__main__":
    main()
