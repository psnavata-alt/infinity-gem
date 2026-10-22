"""Download PSA national-accounts tables for Infinity GEM's own SAM v0.5: refined petroleum supply (18 Oct 2026).

Why: Infinity GEM's own SAM v0.4 takes refined petroleum's supply mix from PSA's 2018 I-O (45% domestic refining, 39% imports of its
purchaser value in 2023). Shell's Tabangao refinery stopped refining in 2020, so 2023 imports should be larger. These tables
give 2023 values: manufacturing GVA by industry (coke and refined petroleum products) and imports of goods by type.
Each CSV starts with '#' lines (source, URL, time); body = PSA's raw layout, every item. Browser User-Agent required.
Run:  py data/raw/macro/download_psa_petroleum_supply_tables.py
"""
import datetime as dt
import json
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PX = "https://openstat.psa.gov.ph/PXWeb/api/v1/en/DB/2B/NA/AN"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
TABLES = {"10MFG/0462B5BMFA1.px": "PSA_OpenSTAT_0462B5BMFA1_GVA_manufacturing_by_industry_annual.csv",
          "6IOG/0302B5BIGA1.px": "PSA_OpenSTAT_0302B5BIGA1_imports_of_goods_annual.csv"}


def get(url, data=None):
    req = urllib.request.Request(url, data=data, headers={**UA, "Content-Type": "application/json"} if data else UA)
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def main():
    for rel, name in TABLES.items():
        url = f"{PX}/{rel}"
        meta = json.loads(get(url))
        sel = [{"code": v["code"], "selection": {"filter": "all", "values": ["*"]}} for v in meta["variables"]]
        text = get(url, json.dumps({"query": sel, "response": {"format": "csv"}}).encode()).decode("utf-8-sig", errors="replace")
        with open(HERE / name, "w", encoding="utf-8", newline="") as f:
            f.write(f"# Source: PSA OpenSTAT table {rel.split('/')[-1][:-3]}, {meta.get('title', '')}. {url}\n")
            f.write(f"# Downloaded {dt.datetime.now():%Y-%m-%d %H:%M} through PSA's PXWeb API (POST, every item, CSV). Raw PSA layout, unchanged.\n")
            f.write(text)
        print(name, len(text.splitlines()), "lines")


if __name__ == "__main__":
    main()
