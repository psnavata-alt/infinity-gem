"""Cement's coal in 2023 at IEA volumes, priced two ways, and PSA's 2023 coal imports against the SAMs (24 Oct 2026, afternoon).

RESEARCH, NOT FOR CITATION. Reads only files on disk; no model file changes.
  * How the v0.7b note's ₱23.6 bn was priced: tools/build_own_sam_2023.metals_coal_2023 (the v0.7b target function), cement's
    line 'cement's coal 2023 at IEA volumes (not used)' = GTAP 10A 2014's coal use by nmm (cement etc.; IEA energy balances, in
    data/processed/electricity_fuel_mix_inputs_2014-2023.csv) x PSA's real GVA of other non-metallic minerals 2023 / 2014
    (OpenSTAT 0462B5BMFA1) x the POWER PLANTS' implied 2023 price per kgoe (electricity's coal in the SAM, ₱195.09 bn, over DOE's
    2023 coal generation x GTAP 2014's Mtoe per GWh). Not Newcastle.
  * The same volume at the Philippine import price: PSA OpenSTAT annual imports 2023, HS 2701, all countries (CIF US$ / kg;
    data/raw/macro/PSA_OpenSTAT_coal_imports_HS2701-2704_downloaded_2026-10-24/PSA_OpenSTAT_0032L4DMFD2_coal_imports_by_country_
    annual_2023.csv), in pesos at the BIS 2023 average (data/raw/macro/BIS_WS_XRU_PHP_per_USD_monthly_average.csv, series
    M.PH.PHP.A, mean of the 12 months of 2023). A tonne is turned into tonnes of oil equivalent with a calorific value that is NOT
    on disk (PSA's records have no grades): 4,500 to 6,000 kcal/kg shown, 5,000 kcal/kg (the convention of the fuel-mix code) central.
  * PSA's 2023 coal imports in pesos against the SAMs' coal imports (row x ccoal).
Outputs: outputs/cement_coal_2023_<stamp>.csv. Run: py -I -X utf8 research/coal_lng_prices/cement_coal_2023.py
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from infinity_gem import paths                                          # noqa: E402
from infinity_gem.sam import SAM                                        # noqa: E402
import build_own_sam_2023 as bs                                    # noqa: E402

PSA_2023 = (paths.DATA_RAW / "macro" / "PSA_OpenSTAT_coal_imports_HS2701-2704_downloaded_2026-10-24" /
            "PSA_OpenSTAT_0032L4DMFD2_coal_imports_by_country_annual_2023.csv")
BIS = "BIS_WS_XRU_PHP_per_USD_monthly_average.csv"
KCAL = (4500, 5000, 5500, 6000)


def main():
    t7 = SAM.load(paths.sam_own("0.7b")).table
    coal_el = float(t7.loc["ccoal", "aelec"])
    mc = bs.metals_coal_2023(coal_el)
    price_power = float(mc["implied coal price 2023 (₱ per kgoe)"])            # ₱ per kgoe = ₱ bn per Mtoe
    nmm_value = float(mc["cement's coal 2023 at IEA volumes (₱ bn; not used)"])
    nmm_mtoe = nmm_value / price_power
    fx = bs._annual(BIS, "value", 2023)
    d = pd.read_csv(PSA_2023, comment="#", dtype={"Commodity Code": str})
    d = d[d["Commodity Code"].str.startswith("2701")]
    for c in ("2023 Gross Kilo", "2023 CIF"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    usd_t = float(d["2023 CIF"].sum() / d["2023 Gross Kilo"].sum() * 1000)
    ido = d[d["country"].astype(str).str.startswith("Indonesia")]
    usd_t_ido = float(ido["2023 CIF"].sum() / ido["2023 Gross Kilo"].sum() * 1000)
    imp_php = float(d["2023 CIF"].sum()) * fx / 1e9
    rows = {"cement's coal 2023 at IEA volumes (Mtoe; GTAP 2014 nmm x PSA real GVA 2023/2014)": nmm_mtoe,
            "power plants' implied 2023 coal price (₱ per kgoe; the v0.7b note's price)": price_power,
            "the same in US$ per toe (BIS 2023 pesos per US$)": price_power * 1000 / fx,
            "the same in US$ per tonne of 5,000 kcal/kg coal": price_power * 1000 / fx * 0.5,
            "cement's coal 2023 at IEA volumes, power plants' price (₱ bn; the note's ₱23.6 bn)": nmm_value,
            "BIS pesos per US$, 2023 average": fx,
            "PSA imports 2023, HS 2701, all countries: Mt": float(d["2023 Gross Kilo"].sum()) / 1e9,
            "PSA imports 2023, HS 2701: US$ per tonne CIF": usd_t, "PSA imports 2023, HS 2701 from Indonesia: US$ per tonne CIF": usd_t_ido,
            "calorific value at which the import price equals the power plants' price (kcal/kg)": 1e4 * usd_t / (price_power * 1000 / fx)}
    for k in KCAL:
        p_kgoe = usd_t * fx / 1000 * (1e4 / k)                     # ₱ per kgoe: (₱ per kg coal) x (kg coal per kgoe)
        rows[f"cement's coal at the import price, {k:,} kcal/kg (₱ bn)"] = nmm_mtoe * p_kgoe
    rows["cement's coal in SAM v0.7b (₱ bn)"] = float(t7.loc["ccoal", "anmet"])
    p8 = paths.sam_own("0.8")
    if p8.exists():
        rows["cement's coal in SAM v0.8 (₱ bn)"] = float(SAM.load(p8).table.loc["ccoal", "anmet"])
    rows["PSA imports 2023, HS 2701, CIF in pesos (₱ bn)"] = imp_php
    for v in ("0.7", "0.7b", "0.8"):
        if paths.sam_own(v).exists():
            rows[f"coal imports in SAM v{v} (row x ccoal, ₱ bn)"] = float(SAM.load(paths.sam_own(v)).table.loc["row", "ccoal"])
    out = pd.Series(rows).to_frame("value")
    f = paths.output_dir() / f"cement_coal_2023_{dt.datetime.now():%Y%m%d_%H%M}.csv"
    out.to_csv(f)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_colwidth", 120)
    print(out.to_string())
    print("saved", f)


if __name__ == "__main__":
    main()
