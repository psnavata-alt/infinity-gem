"""Download the PSA OpenSTAT tables that Infinity GEM's own 2023 SAM version 0.6 uses (23 Oct 2026).

Why: v0.5 still takes several blocks from IFPRI's 2023 SAM structure (government transfers, rest-of-world flows, the activity mix
within industries, land, household direct taxes, ...). PSA publishes the institutional-sector accounts that replace most of them
(folder 2B/CA: income and outlay accounts of general government, households, non-financial and financial corporations; external
transactions; taxes), GVA by sub-industry for agriculture and utilities, exports and imports by product group, and the farm
costs-and-returns surveys (land rent). Each CSV starts with '#' lines (source table id, title, URL, download time); the body is
PSA's raw layout, every item, unchanged ('.' or '..' = not available). Browser User-Agent required (PSA refuses the default one).
Existing files are never overwritten (a dated copy is written instead).
Run:  py data/raw/macro/download_psa_sam_v06_tables.py
"""
import datetime as dt
import json
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE.parent
PX = "https://openstat.psa.gov.ph/PXWeb/api/v1/en/DB"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
TABLES = {   # OpenSTAT path -> file under data/raw
    "2B/CA/0042B5BCA04.px": "macro/PSA_OpenSTAT_0042B5BCA04_external_transactions_annual.csv",
    "2B/CA/0072B5BIO03.px": "macro/PSA_OpenSTAT_0072B5BIO03_general_government_income_outlay_annual.csv",
    "2B/CA/0082B5BIO04.px": "macro/PSA_OpenSTAT_0082B5BIO04_households_income_outlay_annual.csv",
    "2B/CA/0052B5BIO01.px": "macro/PSA_OpenSTAT_0052B5BIO01_nonfinancial_corporations_income_outlay_annual.csv",
    "2B/CA/0062B5BIO02.px": "macro/PSA_OpenSTAT_0062B5BIO02_financial_corporations_income_outlay_annual.csv",
    "2B/CA/0122B5BDT01.px": "macro/PSA_OpenSTAT_0122B5BDT01_taxes_on_production_imports_income_annual.csv",
    "2B/CA/0022B5BCA02.px": "macro/PSA_OpenSTAT_0022B5BCA02_national_disposable_income_annual.csv",
    "2B/CA/0032B5BCA03.px": "macro/PSA_OpenSTAT_0032B5BCA03_gross_accumulation_annual.csv",
    "2B/CA/0092B5BSA01.px": "macro/PSA_OpenSTAT_0092B5BSA01_factor_shares_by_institutional_sector_annual.csv",
    "2B/NA/AN/1SUM/0092B5BNPA1.px": "macro/PSA_OpenSTAT_0092B5BNPA1_net_primary_income_from_ROW_annual.csv",
    "2B/NA/AN/8AFF/0382B5BAFA1.px": "macro/PSA_OpenSTAT_0382B5BAFA1_GVA_agriculture_by_subsector_annual.csv",
    "2B/NA/AN/11ESWW/0502B5BEWA1.px": "macro/PSA_OpenSTAT_0502B5BEWA1_GVA_electricity_water_by_industry_annual.csv",
    "2B/NA/AN/4EOG/0222B5BEGA1.px": "macro/PSA_OpenSTAT_0222B5BEGA1_exports_of_goods_annual.csv",
    "2B/NA/AN/5EOS/0262B5BESA1.px": "macro/PSA_OpenSTAT_0262B5BESA1_exports_of_services_annual.csv",
    "2B/NA/AN/7IOS/0342B5BISA1.px": "macro/PSA_OpenSTAT_0342B5BISA1_imports_of_services_annual.csv",
    "2B/AA/CR/0012B5EAPC0.px": "agri/PSA_OpenSTAT_0012B5EAPC0_palay_costs_and_returns_2022-2025.csv",
    "2B/AA/CR/0022B5EAPC1.px": "agri/PSA_OpenSTAT_0022B5EAPC1_palay_corn_costs_and_returns_2002-2021.csv",
    "2B/AA/CR/0032B5ECOP1.px": "agri/PSA_OpenSTAT_0032B5ECOP1_rootcrops_costs_and_returns.csv",
    "2B/AA/CR/0042B5ECOP2.px": "agri/PSA_OpenSTAT_0042B5ECOP2_legumes_costs_and_returns.csv",
    "2B/AA/CR/0052B5ECOP3.px": "agri/PSA_OpenSTAT_0052B5ECOP3_vegetables_costs_and_returns.csv",
    "2B/AA/CR/0062B5ECOP4.px": "agri/PSA_OpenSTAT_0062B5ECOP4_fruits_costs_and_returns.csv",
    "2B/AA/CR/0072B5ECOP5.px": "agri/PSA_OpenSTAT_0072B5ECOP5_commercial_crops_costs_and_returns.csv",
    "2B/AA/CR/0082B5ECOP6.px": "agri/PSA_OpenSTAT_0082B5ECOP6_nuts_costs_and_returns.csv",
    "2B/AA/CR/0092B5ECOP7.px": "agri/PSA_OpenSTAT_0092B5ECOP7_milkfish_tilapia_costs_and_returns.csv",
}


def get(url, data=None):
    req = urllib.request.Request(url, data=data, headers={**UA, "Content-Type": "application/json"} if data else UA)
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def main(only=None):
    for rel, name in TABLES.items():
        if only and not any(o in rel for o in only):
            continue
        out = RAW / name
        if out.exists():                       # never overwrite a saved download: keep it, write a dated copy beside it
            out = out.with_name(out.stem + f"_{dt.date.today():%Y%m%d}" + out.suffix)
            if out.exists():
                print("kept", name); continue
        url = f"{PX}/{rel}"
        for attempt in range(3):
            try:
                meta = json.loads(get(url))
                sel = [{"code": v["code"], "selection": {"filter": "all", "values": ["*"]}} for v in meta["variables"]]
                text = get(url, json.dumps({"query": sel, "response": {"format": "csv"}}).encode()).decode("utf-8-sig", errors="replace")
                break
            except Exception as e:             # PSA's server is slow at times: retry
                print(rel, "attempt", attempt + 1, "failed:", e)
                time.sleep(5)
        else:
            print("FAILED", rel); continue
        with open(out, "w", encoding="utf-8", newline="") as f:
            f.write(f"# Source: PSA OpenSTAT table {rel.split('/')[-1][:-3]}, {meta.get('title', '')}. {url}\n")
            f.write(f"# Downloaded {dt.datetime.now():%Y-%m-%d %H:%M} through PSA's PXWeb API (POST, every "
                    "item, CSV) for Infinity GEM's own SAM v0.6. Raw PSA layout, unchanged; '.' or '..' = not available.\n")
            f.write(text)
        print(out.relative_to(RAW), len(text.splitlines()), "lines")


if __name__ == "__main__":
    import sys
    main(sys.argv[1:] or None)
