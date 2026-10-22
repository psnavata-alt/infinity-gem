"""Download the public data for the agriculture pre-CGE models.

Run again to refresh. Each CSV starts with '#' lines giving the source, the URL and the download time
(read with pandas.read_csv(..., comment="#")). PSA OpenSTAT answers scripts only with a browser
User-Agent header; the World Bank and NOAA files are plain downloads.
"""
import io, json, sys, urllib.request
from datetime import datetime
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
PX = "https://openstat.psa.gov.ph/PXWeb/api/v1/en/DB"
NOW = datetime.now().strftime("%Y-%m-%d %H:%M")
WHO = sys.argv[1] if len(sys.argv) > 1 else Path(__file__).name

PSA_TABLES = {
    "2E/CS/0012E4EVCP0.px": "PSA_OpenSTAT_0012E4EVCP0_palay_corn_production_by_province_1987-2026.csv",
    "2E/CS/0022E4EAHC0.px": "PSA_OpenSTAT_0022E4EAHC0_palay_corn_area_harvested_by_province_1987-2026.csv",
    "2E/CS/0042E4EPFU0.px": "PSA_OpenSTAT_0042E4EPFU0_palay_fertilizer_use_by_region_2003-2025.csv",
    "2E/CS/0052E4ECFU0.px": "PSA_OpenSTAT_0052E4ECFU0_corn_fertilizer_use_by_region_2003-2025.csv",
    "2M/NFG/0032M4AFN01.px": "PSA_OpenSTAT_0032M4AFN01_cereals_farmgate_prices_by_province_2010-2026.csv",
    "2M/FG/0032M4AFP01.px": "PSA_OpenSTAT_0032M4AFP01_cereals_farmgate_prices_old_series.csv",
    "2M/DP/0062M4AFER1.px": "PSA_OpenSTAT_0062M4AFER1_fertilizer_dealers_prices_1990-2019.csv",
}


def get(url, data=None):
    req = urllib.request.Request(url, data=data, headers={**UA, "Content-Type": "application/json"} if data else UA)
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def save(name, header_lines, text):
    with open(OUT / name, "w", encoding="utf-8", newline="") as f:
        for h in header_lines:
            f.write("# " + h + "\n")
        f.write(text if text.endswith("\n") else text + "\n")
    print("saved", name)


def psa(table, name):
    meta = json.loads(get(f"{PX}/{table}"))
    query = {"query": [{"code": v["code"], "selection": {"filter": "all", "values": ["*"]}} for v in meta["variables"]],
             "response": {"format": "csv"}}
    raw = get(f"{PX}/{table}", json.dumps(query).encode())
    text = raw.decode("utf-8-sig", errors="replace")
    save(name, [f"Source: PSA OpenSTAT table {table.split('/')[-1].replace('.px', '')}, {meta['title']}. {PX}/{table}",
                f"Downloaded {NOW} by {WHO} through the PXWeb API (POST, every item listed, CSV). Raw PSA layout below, unchanged; '.' or '..' = not available."],
         text)


def pinksheet():
    page = get("https://www.worldbank.org/en/research/commodity-markets").decode("utf-8", errors="replace")
    import re
    url = re.search(r'https://thedocs\.worldbank\.org/[^"\']*CMO-Historical-Data-Monthly\.xlsx', page).group(0)
    x = pd.read_excel(io.BytesIO(get(url)), sheet_name="Monthly Prices", header=None)
    head = x.index[x.iloc[:, 0].astype(str).str.fullmatch(r"\d{4}M\d{2}")][0]
    names = x.iloc[head - 2].tolist(); units = x.iloc[head - 1].tolist()
    keep = [i for i, n in enumerate(names) if isinstance(n, str) and any(k in n.upper() for k in ("UREA", "DAP", "TSP", "PHOSPHATE ROCK", "POTASSIUM", "RICE", "MAIZE"))]
    d = x.iloc[head:, [0] + keep].copy()
    d.columns = ["month"] + [f"{names[i].strip()} ({str(units[i]).strip()})" for i in keep]
    d["month"] = d["month"].str.replace("M", "-")
    save("WorldBank_PinkSheet_fertilizer_rice_maize_monthly_1960-2026.csv",
         [f"Source: World Bank, Commodity Markets ('Pink Sheet'), CMO-Historical-Data-Monthly.xlsx, sheet 'Monthly Prices' (CC BY 4.0). {url}",
          f"Downloaded {NOW} by {WHO} from the link on https://www.worldbank.org/en/research/commodity-markets. Nominal US$, monthly averages. Columns copied unchanged (fertilizers, rice, maize)."],
         d.to_csv(index=False))


def oni():
    url = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
    t = pd.read_csv(io.StringIO(get(url).decode()), sep=r"\s+")
    save("NOAA_CPC_ONI_ElNino_index_1950-2026.csv",
         [f"Source: NOAA Climate Prediction Center, Oceanic Nino Index (ONI): 3-month running mean of ERSST.v5 SST anomalies in the Nino 3.4 region. {url}",
          f"Downloaded {NOW} by {WHO}. El Nino episode = ONI >= +0.5 for 5 overlapping seasons; SEAS = 3-month season (DJF ... NDJ); TOTAL = SST degC; ANOM = ONI."],
         t.to_csv(index=False))


if __name__ == "__main__":
    for t, n in PSA_TABLES.items():
        try:
            psa(t, n)
        except Exception as e:
            print("FAILED", t, e)
    for f in (pinksheet, oni):
        try:
            f()
        except Exception as e:
            print("FAILED", f.__name__, e)
