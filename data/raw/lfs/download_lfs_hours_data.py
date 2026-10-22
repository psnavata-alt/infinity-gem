"""Download PSA LFS tables on hours, underemployment and class of worker (0.3.9, 18 Oct 2026).

Why: the evidence behind the wage curve's Okun target. The employment-to-population elasticity
(preshock/okun.py) is 0.71 only because of the 2020-2021 quarters. The model's labour input is persons x hours, so the
hours-inclusive relation (employed x mean hours) is the closer data counterpart; visible underemployment and the
class-of-worker split show the informal margin.

Each CSV starts with '#' lines giving the source, the URL and the download time (read with
pandas.read_csv(..., comment="#")); the body is PSA's raw layout, every item selected. PSA OpenSTAT answers scripts only
with a browser User-Agent header. Run:  py data/raw/lfs/download_lfs_hours_data.py
"""
import datetime as dt
import json
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PX = "https://openstat.psa.gov.ph/PXWeb/api/v1/en/DB/1B/LFS"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
TABLES = {
    "0191B3FHRS1": "PSA_OpenSTAT_0191B3FHRS1_LFS_mean_hours_worked_2005-2026.csv",
    "0201B3FHRS2": "PSA_OpenSTAT_0201B3FHRS2_LFS_employed_by_hours_worked_2005-2026.csv",
    "0011B3FKEI1": "PSA_OpenSTAT_0011B3FKEI1_LFS_key_employment_levels_2005-2026.csv",
    "0171B3FVIS1": "PSA_OpenSTAT_0171B3FVIS1_LFS_visibly_underemployed_2005-2026.csv",
    "0131B3FEMP5": "PSA_OpenSTAT_0131B3FEMP5_LFS_employed_by_class_of_worker_2005-2026.csv",
}


def get(url, data=None):
    req = urllib.request.Request(url, data=data, headers={**UA, "Content-Type": "application/json"} if data else UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def main():
    for table, name in TABLES.items():
        url = f"{PX}/{table}.px"
        meta = json.loads(get(url))
        sel = [{"code": v["code"], "selection": {"filter": "all", "values": ["*"]}} for v in meta["variables"]]
        text = get(url, json.dumps({"query": sel, "response": {"format": "csv"}}).encode()).decode("utf-8-sig", errors="replace")
        stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(HERE / name, "w", encoding="utf-8", newline="") as f:
            f.write(f"# Source: PSA OpenSTAT table {table}, {meta.get('title', '')}. {url}\n")
            f.write(f"# Downloaded {stamp} through PSA's PXWeb API (POST, every item, CSV). Raw PSA layout, unchanged.\n")
            f.write(text)
        print(f"{name}: {len(text.splitlines())} lines")


if __name__ == "__main__":
    main()
