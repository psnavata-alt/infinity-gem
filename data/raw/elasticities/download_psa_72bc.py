"""Download the PSA OpenSTAT tables behind the own value-added (capital-labour) and export (CET) elasticity estimates
(the opt-in sets ph_va72b, ph_va72b_low and ph_cet72c of infinity_gem/elasticities.py; 24 Oct 2026).

Source: Philippine Statistics Authority (PSA), OpenSTAT, PXWeb API https://openstat.psa.gov.ph/PXWeb/api/v1/en/DB/ (POST,
every item of every variable, CSV, browser User-Agent as in data/raw/agri/download_psa_rice_imports.py). Each file keeps
PSA's raw layout unchanged under a '#' header with the table id, title, URL and download time; read with
pandas.read_csv(path, comment="#"). '.', '..' or '...' = not available.

Tables (folder PSA_OpenSTAT_72bc_downloaded_2026-10-24/ next to this script):
  72(b) capital-labour substitution
    1B/LFS/0091B3FEMP1    employed persons by major industry (1994 PSIC), Apr 2005-Jul 2011 (joins 0101B3FEMP2, 2012-2026, on disk)
    2N/0012N5EAWR0        agricultural wage rates of farm workers, 1975-2019
    2G/CONS/ASPBI/0012G4CASF0, 0022G4CASF1, 0032G4CASF2   ASPBI construction establishments, 2015, 2016, 2017
    2E/ES/0012E4CASA0, 0022E4CASA1, 0032E4CASA2           ASPBI agriculture, forestry and fishing establishments, 2015-2017
    2B/NA/QT/8AFF/0382B5BAFQ1   GVA in agriculture, forestry and fishing by subsector, quarterly
  72(c) export (CET) elasticities
    2B/NA/QT/4EOG/0222B5BEGQ1   exports of goods by commodity group, quarterly, current and constant 2018 prices
    2B/NA/QT/5EOS/0262B5BESQ1   exports of services by type, quarterly
    2B/NA/QT/10MFG/0462B5BMFQ1  GVA in manufacturing by industry, quarterly
    2G/MNFG/MISSI/2018/0032G4CMPO2, 0022G4CMPA2   MISSI volume and value of production indices (2018=100), monthly 2018-2026
    2G/MNFG/MISSI/BAC/0012G4CMPO1, 0022G4CMPA1    MISSI backcasted volume and value of production indices, 2001-2017
    2M/PI/PPI/PPIM/0012M4CPPI2, 0022M4CPPI1       PPI for manufacturing (2018=100) and its backcast 2001-2017

Run again to refresh:  py -I data/raw/elasticities/download_psa_72bc.py
"""
import csv, io, json, sys, time, urllib.request
from datetime import datetime
from pathlib import Path

BASE = "https://openstat.psa.gov.ph/PXWeb/api/v1/en/DB/"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
OUT = Path(__file__).resolve().parent / "PSA_OpenSTAT_72bc_downloaded_2026-10-24"
TABLES = {
    "1B/LFS/0091B3FEMP1.px": "LFS_employed_by_major_industry_1994PSIC_2005-2011",
    "2N/0012N5EAWR0.px": "agricultural_wage_rates_farm_workers_1975-2019",
    "2G/CONS/ASPBI/0012G4CASF0.px": "ASPBI_construction_2015",
    "2G/CONS/ASPBI/0022G4CASF1.px": "ASPBI_construction_2016",
    "2G/CONS/ASPBI/0032G4CASF2.px": "ASPBI_construction_2017",
    "2E/ES/0012E4CASA0.px": "ASPBI_agriculture_forestry_fishing_2015",
    "2E/ES/0022E4CASA1.px": "ASPBI_agriculture_forestry_fishing_2016",
    "2E/ES/0032E4CASA2.px": "ASPBI_agriculture_forestry_fishing_2017",
    "2B/NA/QT/8AFF/0382B5BAFQ1.px": "GVA_agriculture_by_subsector_quarterly",
    "2B/NA/QT/4EOG/0222B5BEGQ1.px": "exports_of_goods_quarterly",
    "2B/NA/QT/5EOS/0262B5BESQ1.px": "exports_of_services_quarterly",
    "2B/NA/QT/10MFG/0462B5BMFQ1.px": "GVA_manufacturing_by_industry_quarterly",
    "2G/MNFG/MISSI/2018/0032G4CMPO2.px": "MISSI_VoPI_2018base_monthly",
    "2G/MNFG/MISSI/2018/0022G4CMPA2.px": "MISSI_VaPI_2018base_monthly",
    "2G/MNFG/MISSI/BAC/0012G4CMPO1.px": "MISSI_VoPI_backcast_2001-2017",
    "2G/MNFG/MISSI/BAC/0022G4CMPA1.px": "MISSI_VaPI_backcast_2001-2017",
    "2M/PI/PPI/PPIM/0012M4CPPI2.px": "PPI_manufacturing_2018base_monthly",
    "2M/PI/PPI/PPIM/0022M4CPPI1.px": "PPI_manufacturing_backcast_2001-2017",
}


def get(url, data=None):
    req = urllib.request.Request(url, data=data, headers={**UA, "Content-Type": "application/json"} if data else UA)
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


def one(table, name):
    url = BASE + table
    for attempt in range(4):
        try:
            meta = json.loads(get(url))
            q = {"query": [{"code": v["code"], "selection": {"filter": "all", "values": ["*"]}} for v in meta["variables"]],
                 "response": {"format": "csv"}}
            raw = get(url, json.dumps(q).encode())
            try:
                body = raw.decode("utf-8-sig")
            except UnicodeDecodeError:              # some PSA tables are served in Windows-1252 (e.g. 0032E4CASA2)
                body = raw.decode("cp1252")
            if len(list(csv.reader(io.StringIO(body)))) < 2:
                raise ValueError("empty table")
            tid = table.rsplit("/", 1)[-1].replace(".px", "")
            f = OUT / f"PSA_OpenSTAT_{tid}_{name}.csv"
            with open(f, "w", encoding="utf-8", newline="") as fh:
                fh.write(f"# Source: PSA OpenSTAT table {tid}, {meta.get('title', '')}. {url}\n")
                fh.write(f"# Downloaded {datetime.now():%Y-%m-%d %H:%M} "
                         "through PSA's PXWeb API (POST, every item, CSV, browser User-Agent). Raw PSA layout, unchanged.\n")
                fh.write(body if body.endswith("\n") else body + "\n")
            print("saved", f.name, len(body), "bytes")
            return f
        except Exception as e:  # noqa: BLE001  (network hiccups: retry, then fail loudly)
            err = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"{table}: {err}")


def main():
    OUT.mkdir(exist_ok=True)
    only = sys.argv[1:]
    for t, n in TABLES.items():
        if not only or any(o in t for o in only):
            one(t, n)
            time.sleep(1)


if __name__ == "__main__":
    main()
