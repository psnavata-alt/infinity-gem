"""Inputs for Infinity GEM SAM v0.9 (a customs-anchored coal and fuel account): PSA's 2023 customs records of mineral-fuel imports and
exports, one row per number with its source (24 Oct 2026, afternoon).

RESEARCH, NOT FOR CITATION. Reads only PSA OpenSTAT downloads on disk (PSA from Bureau of Customs entries; imports CIF, exports
FOB, US$; gross kg) and data/raw/macro price files; writes data/processed/fuel_trade_customs_2023_v0.9_inputs.csv, which
tools/build_own_sam_2023.py version '0.9' reads (CUSTOMS_V09).
  imports 2023, HS chapter 27: data/raw/macro/PSA_OpenSTAT_fuels_trade_energy_downloaded_2026-10-24/PSA_OpenSTAT_0032L4DMFD2_
     imports_HS27_by_country_annual_2023_downloaded_20261024.csv (the groups of research/coal_lng_prices/fuel_imports_2023_customs.py);
  exports 2023, HS 27 (AVE/0032L4DXFD2), imports 2022, HS 27 (AVI/0042L4DMFD1), imports 2023, HS 25-26 (AVI/0032L4DMFD2):
     downloaded 24 Oct 2026, 14:08-14:30 by research/coal_lng_prices/download_psa_trade_hs.py into DOWNLOADS (under
     data/raw/macro/; outputs/ is searched too, where a fresh download lands);
  PSA OpenSTAT 0012F2BPES1 (Table 14.1a, total primary energy supply by source, ktoe, from DOE): coal imported and indigenous
     2022, in data/raw/macro/PSA_OpenSTAT_fuels_trade_energy_downloaded_2026-10-24/;
  BIS pesos per US$ (2023 mean of the months) and the World Bank's 2023 Japan LNG price (US$ per MMBtu, mean of the months):
     data/raw/macro/BIS_WS_XRU_PHP_per_USD_monthly_average.csv, WorldBank_PinkSheet_coal_lng_monthly.csv.
Run: py -I -X utf8 research/coal_lng_prices/customs_inputs_v09.py
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

OUT = paths.DATA_PROCESSED / "fuel_trade_customs_2023_v0.9_inputs.csv"
RAW = paths.DATA_RAW / "macro" / "PSA_OpenSTAT_fuels_trade_energy_downloaded_2026-10-24"
DOWNLOADS = ("PSA_OpenSTAT_downloads_for_SAM_v0.9_20261024",)
IMP23 = RAW / "PSA_OpenSTAT_0032L4DMFD2_imports_HS27_by_country_annual_2023_downloaded_20261024.csv"
TPES = RAW / "PSA_OpenSTAT_0012F2BPES1_primary_energy_supply_by_source_2014-2022_downloaded_20261024.csv"
EXP23 = "PSA_OpenSTAT_0032L4DXFD2_exports_HS27_by_country_annual_2023.csv"
IMP22 = "PSA_OpenSTAT_0042L4DMFD1_imports_HS27_by_country_annual_2022.csv"
ORE23 = "PSA_OpenSTAT_0032L4DMFD2_imports_HS25-26_by_country_annual_2023.csv"
MMBTU_PER_TOE = 41.868 / 1.055056                                   # unit definitions: 1 toe = 41.868 GJ; 1 MMBtu = 1.055056 GJ
# HS 25 lines that are manufactures in the SAM (cement and lime: non-metallic mineral products), not mining
HS25_MANUFACTURES = ("2522", "2523")


def find(name: str) -> Path:
    for d in [paths.DATA_RAW / "macro" / x for x in DOWNLOADS] + [paths.ROOT / "outputs" / x for x in DOWNLOADS] + \
             [p / x for p in paths.output_dirs() for x in DOWNLOADS]:
        if (d / name).exists():
            return d / name
    raise FileNotFoundError(f"{name}: run research/coal_lng_prices/download_psa_trade_hs.py first (see this file's docstring)")


def read(p: Path, year: int, flow: str) -> pd.DataFrame:
    d = pd.read_csv(p, comment="#", dtype={"Commodity Code": str})
    d["value"] = pd.to_numeric(d[f"{year} {flow}"], errors="coerce")
    d["kg"] = pd.to_numeric(d[f"{year} Gross Kilo"], errors="coerce")
    return d


def mean_year(fname: str, col: str, y: int) -> float:
    x = pd.read_csv(paths.DATA_RAW / "macro" / fname, comment="#")
    return float(x.loc[x["month"].astype(str).str.startswith(str(y)), col].mean())


def main():
    fx = mean_year("BIS_WS_XRU_PHP_per_USD_monthly_average.csv", "value", 2023)
    lng_jp = mean_year("WorldBank_PinkSheet_coal_lng_monthly.csv", "Liquefied natural gas, Japan", 2023)
    rows = []

    def add(key, value, unit, source):
        rows.append({"key": key, "value": float(value), "unit": unit, "source": source})
    src_i = f"PSA OpenSTAT AVI/0032L4DMFD2 (imports 2023, CIF), {IMP23.name}"
    i = read(IMP23, 2023, "CIF")
    c = i["Commodity Code"]
    groups = {"coal (HS 2701-2703)": c.str[:4].isin(["2701", "2702", "2703"]), "crude oil (HS 2709)": c.str[:4] == "2709",
              "natural gas and LNG (HS 2711.11, 2711.21)": c.str[:6].isin(["271111", "271121"])}
    groups["refined and other petroleum (HS 2710, 2711.12-.19 and .29, 2704, 2706-2708, 2712-2715)"] = ~(
        groups["coal (HS 2701-2703)"] | groups["crude oil (HS 2709)"] | groups["natural gas and LNG (HS 2711.11, 2711.21)"])
    for k, m in groups.items():
        add(f"customs imports 2023, CIF: {k}", i.loc[m, "value"].sum() * fx / 1e9, "₱ bn", src_i + f"; x BIS 2023 pesos per US$")
        add(f"customs imports 2023, gross weight: {k}", i.loc[m, "kg"].sum() / 1e9, "Mt", src_i)
    m = c.str[:4] == "2701"
    add("customs imports 2023, CIF unit value: coal (HS 2701)", i.loc[m, "value"].sum() / i.loc[m, "kg"].sum() * 1000, "US$ per tonne", src_i)
    m = groups["natural gas and LNG (HS 2711.11, 2711.21)"]
    add("customs imports 2023, CIF unit value: natural gas and LNG", i.loc[m, "value"].sum() / i.loc[m, "kg"].sum() * 1000, "US$ per tonne", src_i)
    e = read(find(EXP23), 2023, "FOB")
    src_e = f"PSA OpenSTAT AVE/0032L4DXFD2 (exports 2023, FOB), {EXP23}"
    ce = e["Commodity Code"]
    for k, m in (("coal (HS 2701-2703)", ce.str[:4].isin(["2701", "2702", "2703"])), ("crude oil (HS 2709)", ce.str[:4] == "2709"),
                 ("natural gas and LNG (HS 2711.11, 2711.21)", ce.str[:6].isin(["271111", "271121"]))):
        add(f"customs exports 2023, FOB: {k}", e.loc[m, "value"].sum() * fx / 1e9, "₱ bn", src_e + "; x BIS 2023 pesos per US$")
        add(f"customs exports 2023, gross weight: {k}", e.loc[m, "kg"].sum() / 1e9, "Mt", src_e)
    i22 = read(find(IMP22), 2022, "CIF")
    m = i22["Commodity Code"].str[:4] == "2701"
    add("customs imports 2022, gross weight: coal (HS 2701)", i22.loc[m, "kg"].sum() / 1e9, "Mt", f"PSA OpenSTAT AVI/0042L4DMFD1 (imports 2022), {IMP22}")
    tp = pd.read_csv(TPES, comment="#").set_index("Energy Source")
    tp.index = tp.index.str.lstrip(".").str.strip()
    for k in ("Coal Imported Energy", "Coal Indegenous Energy"):
        add(f"PSA TPES 2022 (DOE): {k}", tp.loc[k, "2022"], "ktoe", f"PSA OpenSTAT 0012F2BPES1 (Table 14.1a), {TPES.name}")
    try:
        o = read(find(ORE23), 2023, "CIF")
        co = o["Commodity Code"]
        m25 = co.str[:2].eq("25") & ~co.str[:4].isin(HS25_MANUFACTURES)
        m26 = co.str[:2].eq("26")
        src_o = f"PSA OpenSTAT AVI/0032L4DMFD2 (imports 2023, CIF), {ORE23}"
        add("customs imports 2023, CIF: salt, sulphur, earths and stone (HS 25 less 2522 lime and 2523 cement)",
            o.loc[m25, "value"].sum() * fx / 1e9, "₱ bn", src_o + "; x BIS 2023 pesos per US$")
        add("customs imports 2023, CIF: ores, slag and ash (HS 26)", o.loc[m26, "value"].sum() * fx / 1e9, "₱ bn", src_o + "; x BIS 2023 pesos per US$")
    except FileNotFoundError as err:
        print("not on disk (the rest-of-mining check is left out):", err)
    add("BIS pesos per US$, 2023 mean", fx, "₱ per US$", "data/raw/macro/BIS_WS_XRU_PHP_per_USD_monthly_average.csv (M.PH.PHP.A), mean of the 12 months")
    add("World Bank Pink Sheet, LNG Japan, 2023 mean", lng_jp, "US$ per MMBtu", "data/raw/macro/WorldBank_PinkSheet_coal_lng_monthly.csv, mean of the 12 months")
    add("MMBtu per toe", MMBTU_PER_TOE, "MMBtu", "unit definitions: 1 toe = 41.868 GJ (IEA); 1 MMBtu = 1.055056 GJ")
    out = pd.DataFrame(rows)
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        f.write("# Inputs for tools/build_own_sam_2023.py version '0.9' (customs-anchored coal and fuel account). RESEARCH, NOT FOR CITATION.\n")
        f.write(f"# Written by research/coal_lng_prices/customs_inputs_v09.py on {dt.datetime.now():%Y-%m-%d %H:%M} from files on disk only; each row names its source.\n")
        out.to_csv(f, index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 110)
    print(out[["key", "value", "unit"]].to_string(index=False))
    print("saved", OUT)


if __name__ == "__main__":
    main()
