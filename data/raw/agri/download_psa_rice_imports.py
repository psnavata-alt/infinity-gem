"""Download PSA's 2023 imports of cereals and milled corn (every country) for the rice and maize accounts of the SAM (54b).

The rice-split SAM's milling sector is PSA 2018 I-O sector 57, rice and corn milling, so the file keeps all of HS chapter
10 (cereals: wheat 1001, rye 1002, barley 1003, oats 1004, maize 1005, rice 1006, sorghum 1007, others 1008) and the
products of corn milling: HS 1102.20 (maize flour), 1103.13 (maize groats and meal) and 1104.23 (other worked maize grains).
(15 Oct 2026, about 5:30 PM: widened from rice only, to place maize imports, which the IFPRI SAM books outside 'cmaiz'.)

Table: PSA OpenSTAT 2L/IMT/AVI/0032L4DMFD2.px, "Annual Value of Philippine Imports by Commodity and Country of Origin,
2023" (source: PSA and the Bureau of Customs import entries; commodity codes = PSCC 2019; quantity in kilograms, value
CIF in US dollars).

Two quirks of this table, found 15 Oct 2026:
- its 10,505 commodity codes are not listed in the API's metadata, and a query that names commodity codes (or uses a
  "1006*" wildcard) returns an empty table or unrelated codes. Only "all commodities" works, so each country is
  requested with every commodity and the lines above are kept;
- countries use PSA's own codes (Viet Nam = 892), not ISO codes.

Run again to refresh:  py data/raw/agri/download_psa_rice_imports.py
Writes PSA_OpenSTAT_0032L4DMFD2_cereals_and_milled_corn_imports_by_country_2023.csv (this folder), every such line of
every country as published ('..' = no data); read with pandas.read_csv(path, comment="#").
"""
import csv, io, json, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

OUT = Path(__file__).resolve().parent / "PSA_OpenSTAT_0032L4DMFD2_cereals_and_milled_corn_imports_by_country_2023.csv"
KEEP = ("10", "110220", "110313", "110423")     # HS chapter 10 (cereals); maize flour; maize groats and meal; worked maize
URL = "https://openstat.psa.gov.ph/PXWeb/api/v1/en/DB/2L/IMT/AVI/0032L4DMFD2.px"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
N_COMMODITIES = 10505


def get(data=None):
    req = urllib.request.Request(URL, data=data, headers={**UA, "Content-Type": "application/json"} if data else UA)
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


def one_country(code):
    q = {"query": [{"code": "Commodity Code", "selection": {"filter": "all", "values": ["*"]}},
                   {"code": "Country", "selection": {"filter": "item", "values": [code]}}],
         "response": {"format": "csv"}}
    for attempt in range(4):
        try:
            rows = list(csv.reader(io.StringIO(get(json.dumps(q).encode()).decode("utf-8-sig"))))
            if len(rows) - 1 != N_COMMODITIES:
                raise ValueError(f"{len(rows) - 1} rows, expected {N_COMMODITIES}")
            return [[code] + r for r in rows[1:] if r[0].startswith(KEEP)]
        except Exception as e:  # noqa: BLE001  (network hiccups: retry, then fail loudly)
            err = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"country {code}: {err}")


def main():
    meta = json.loads(get())
    country = next(v for v in meta["variables"] if v["code"] == "Country")
    with ThreadPoolExecutor(4) as ex:
        rows = [r for part in ex.map(one_country, country["values"]) for r in part]
    header = [
        "Source: Philippine Statistics Authority (PSA) and source of basic data - Bureau of Customs (BOC). "
        "PSA OpenSTAT table 0032L4DMFD2, Annual Value of Philippine Imports by Commodity and Country of Origin, 2023 "
        "(table last updated 27 Aug 2024).",
        f"URL (PXWeb API, POST): {URL}",
        "Units (table metadata): Volume in Kilograms, Value in US Dollars. CIF = FOB + insurance + freight. "
        "Commodity Code = Philippine Standard Commodity Classification (PSCC) version 2019.",
        f"Selection: every commodity, one country at a time ({len(country['values'])} countries, PSA country codes); "
        "lines of HS chapter 10 (cereals; code starting 10) and 110220 (maize flour), 110313 (maize groats and meal), "
        "110423 (other worked maize grains) kept. '..' = no data.",
        "HS 1006 subheadings: 1006.10 rice in the husk (paddy; PSCC 1006101000 = for sowing); 1006.20 husked (brown); "
        "1006.30 semi-milled or wholly milled; 1006.40 broken.",
        f"Downloaded {datetime.now():%Y-%m-%d %H:%M} by download_psa_rice_imports.py{' (' + sys.argv[1] + ')' if len(sys.argv) > 1 else ''}.",
    ]
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        for h in header:
            f.write("# " + h + "\n")
        w = csv.writer(f)
        w.writerow(["country_code", "commodity_code", "country", "quantity_kg_2023", "gross_kilo_2023", "cif_usd_2023"])
        w.writerows(sorted(rows))
    val = lambda x: float(x) if x not in ("..", "") else 0.0  # noqa: E731
    print(f"{OUT.name}: {len(rows)} lines")
    for label, pre in (("wheat (1001)", ("1001",)), ("maize (1005)", ("1005",)), ("rice (HS 1006)", ("1006",)),
                       ("other cereals (1002-1004, 1007-1008)", ("1002", "1003", "1004", "1007", "1008")), ("milled corn", KEEP[1:])):
        part = [r for r in rows if r[1].startswith(pre)]
        kg, usd = sum(val(r[3]) for r in part), sum(val(r[5]) for r in part)
        print(f"  {label}: {kg / 1e9:.4f} Mt, US$ {usd / 1e6:,.1f} M CIF")


if __name__ == "__main__":
    main()
