"""PSA's 2023 imports of mineral fuels (HS chapter 27, customs records) against the SAMs' fuel imports (24 Oct 2026, afternoon).

RESEARCH, NOT FOR CITATION. Reads PSA OpenSTAT AVI/0032L4DMFD2.px (annual imports by commodity and country, 2023; PSA from Bureau
of Customs entries; CIF US$), HS chapter 27 lines, downloaded 24 Oct 2026, 13:17 through the PXWeb API (browser User-Agent) into
data/raw/macro/PSA_OpenSTAT_fuels_trade_energy_downloaded_2026-10-24/PSA_OpenSTAT_0032L4DMFD2_imports_HS27_by_country_annual_2023_downloaded_20261024.csv,
in pesos at the BIS 2023 average (data/raw/macro/BIS_WS_XRU_PHP_per_USD_monthly_
average.csv). Groups: coal = HS 2701-2703; crude = 2709; natural gas = 2711.11 (LNG) + 2711.21 (gaseous); refined and other
petroleum = 2710 + 2711.12-2711.19 + 2711.29 (LPG and other petroleum gases) + 2704 (coke) + 2706-2708 + 2712-2715. SAM accounts:
ccoal (coal), cmine (crude, gas and non-fuel ores: the SAM's 'rest of mining'), cpetr (refined petroleum).
Output: outputs/fuel_imports_2023_customs_<stamp>.csv. Run: py -I -X utf8 research/coal_lng_prices/fuel_imports_2023_customs.py
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from infinity_gem import paths                                          # noqa: E402
from infinity_gem.oil import import_shares                              # noqa: E402
from infinity_gem.sam import SAM                                        # noqa: E402

HS27 = (paths.ROOT / "data" / "raw" / "macro" / "PSA_OpenSTAT_fuels_trade_energy_downloaded_2026-10-24"
        / "PSA_OpenSTAT_0032L4DMFD2_imports_HS27_by_country_annual_2023_downloaded_20261024.csv")


def group(code: str) -> str:
    if code[:4] in ("2701", "2702", "2703"):
        return "coal (HS 2701-2703)"
    if code[:4] == "2709":
        return "crude oil (HS 2709)"
    if code[:6] in ("271111", "271121"):
        return "natural gas and LNG (HS 2711.11, 2711.21)"
    return "refined and other petroleum (HS 2710, LPG 2711.12-19 and .29, coke 2704, 2706-2708, 2712-2715)"


def main():
    bis = pd.read_csv(paths.DATA_RAW / "macro" / "BIS_WS_XRU_PHP_per_USD_monthly_average.csv", comment="#")
    fx = float(bis.loc[bis["month"].astype(str).str.startswith("2023"), "value"].mean())
    d = pd.read_csv(HS27, comment="#", dtype={"Commodity Code": str})
    d["CIF"] = pd.to_numeric(d["2023 CIF"], errors="coerce")
    d["kg"] = pd.to_numeric(d["2023 Gross Kilo"], errors="coerce")
    d["group"] = d["Commodity Code"].map(group)
    g = d.groupby("group")[["CIF", "kg"]].sum()
    g["PSA 2023 (₱ bn, CIF)"] = g["CIF"] * fx / 1e9
    g["Mt"] = g["kg"] / 1e9
    out = g[["PSA 2023 (₱ bn, CIF)", "Mt"]].copy()
    k = import_shares()["crude_in_mining_ex_coal"]
    for v in ("0.5", "0.7", "0.7b", "0.8"):
        p = paths.sam_own(v)
        if not p.exists():
            continue
        t = SAM.load(p).table
        col = f"SAM v{v} (₱ bn)"
        if "ccoal" in t.columns:
            out.loc["coal (HS 2701-2703)", col] = float(t.loc["row", "ccoal"])
            cm = float(t.loc["row", "cmine"])
            kk = k if v != "0.8" else (k * float(SAM.load(paths.sam_own("0.7b")).table.loc["row", "cmine"])
                                       + cm - float(SAM.load(paths.sam_own("0.7b")).table.loc["row", "cmine"])) / cm
            out.loc["crude oil (HS 2709)", col] = cm * kk
            out.loc["SAM: rest of cmine imports (gas, ores)", col] = cm * (1 - kk)
        else:
            out.loc["SAM v0.5: cmine imports (coal, crude, gas, ores)", col] = float(t.loc["row", "cmine"])
        out.loc["refined and other petroleum (HS 2710, LPG 2711.12-19 and .29, coke 2704, 2706-2708, 2712-2715)", col] = float(t.loc["row", "cpetr"])
        out.loc["TOTAL fuel and mining imports in the SAM (cpetr + cmine + ccoal)", col] = float(
            t.loc["row", [c for c in ("cpetr", "cmine", "ccoal") if c in t.columns]].sum())
    out.loc["TOTAL HS chapter 27", "PSA 2023 (₱ bn, CIF)"] = float(g["PSA 2023 (₱ bn, CIF)"].sum())
    out.loc["BIS pesos per US$, 2023", "PSA 2023 (₱ bn, CIF)"] = fx
    f = paths.output_dir() / f"fuel_imports_2023_customs_{dt.datetime.now():%Y%m%d_%H%M}.csv"
    out.to_csv(f)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 70)
    print(out.round(2).to_string())
    print("saved", f)


if __name__ == "__main__":
    main()
