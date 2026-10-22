"""Download PSA's quarterly GDP by industry (0.3.11, 19 Oct 2026).

Why: to compare the CGE's short-run industry pattern with PSA's data. The LFS (0101B3FEMP2) gives employed persons by
industry; this table gives real gross value added by industry, so output and jobs can be compared industry by industry
(output per worker shows whether firms kept workers on while output fell).

Same method as data/raw/lfs/download_lfs_hours_data.py: every item, CSV, '#' lines with the source, URL and download time.
PSA OpenSTAT answers scripts only with a browser User-Agent header. Run:  py data/raw/macro/download_gva_quarterly.py
"""
import datetime as dt
import json
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PX = "https://openstat.psa.gov.ph/PXWeb/api/v1/en/DB/2B/NA/QT/1SUM"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
TABLES = {
    "0052B5BPRQ1": "PSA_OpenSTAT_0052B5BPRQ1_GDP_by_industry_quarterly.csv",
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
