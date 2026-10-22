"""Download the public data for the inflation and peso VAR (decision 2 of 16 Oct 2026; preshock/inflation_var.py).

Run again to refresh:  py data/raw/macro/download_inflation_var_data.py
Each CSV starts with '#' lines giving the source, the URL and the download time (read with
pandas.read_csv(..., comment="#")). PSA OpenSTAT answers scripts only with a browser User-Agent header; the BIS
statistics API and the World Bank file are plain downloads.

  PSA CPI, all income households, 2018=100, by commodity group: Jan 2018 to latest, and PSA's backcast Jan 1994-Dec 2017
  PSA core CPI, 2018=100: Jan 2018 to latest, and the backcast Jan 1994-Dec 2017
  PSA seasonally adjusted CPI by major commodity group (2018=100): Jan 2018 to latest
  PSA CPI weights (headline and core), 2018-based
  BIS central bank policy rates (WS_CBPOL), monthly, end of period: Philippines (BSP) and United States (Fed)
  BIS exchange rates (WS_XRU), monthly average, pesos per US dollar
  World Bank Pink Sheet monthly price indices (food, energy, fertilizers ...), 2010=100
"""
import io
import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
PX = "https://openstat.psa.gov.ph/PXWeb/api/v1/en/DB"
BIS = "https://stats.bis.org/api/v1/data"
NOW = datetime.now().strftime("%Y-%m-%d %H:%M")
WHO = sys.argv[1] if len(sys.argv) > 1 else Path(__file__).name

PSA_TABLES = {
    "2M/PI/CPI/2018NEW/0012M4ACP22.px": "PSA_OpenSTAT_0012M4ACP22_CPI_2018base_by_commodity_group_2018-latest.csv",
    "2M/PI/CPI/2018NEW/0012M4ACP28.px": "PSA_OpenSTAT_0012M4ACP28_CPI_2018base_by_commodity_group_1994-2017_backcast.csv",
    "2M/PI/CPI/2018NEW/0012M4ACP30.px": "PSA_OpenSTAT_0012M4ACP30_core_CPI_2018base_by_group_2018-latest.csv",
    "2M/PI/CPI/2018NEW/0012M4ACP33.px": "PSA_OpenSTAT_0012M4ACP33_core_CPI_2018base_1994-2017_backcast.csv",
    "2M/PI/SACPI/0012M4ASAC1.px": "PSA_OpenSTAT_0012M4ASAC1_seasonally_adjusted_CPI_2018base_2018-latest.csv",
    "2M/PI/CPI/2018NEW/0012M4ACP25.px": "PSA_OpenSTAT_0012M4ACP25_CPI_weights_2018base.csv",
    "2M/PI/CPI/2018NEW/0012M4ACP32.px": "PSA_OpenSTAT_0012M4ACP32_core_CPI_weights_2018base.csv",
}
BIS_SERIES = {
    "WS_CBPOL/M.PH": ("BIS_WS_CBPOL_policy_rate_Philippines_monthly.csv", "central bank policy rate, Philippines (BSP), monthly, end of period, % a year"),
    "WS_CBPOL/M.US": ("BIS_WS_CBPOL_policy_rate_United_States_monthly.csv", "central bank policy rate, United States (Federal Reserve), monthly, end of period, % a year"),
    "WS_XRU/M.PH.PHP.A": ("BIS_WS_XRU_PHP_per_USD_monthly_average.csv", "Philippine pesos per US dollar, monthly average of observations"),
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
    """Whole table, except that the geography is cut to the Philippines as a whole (the regional tables are too large
    for one request: PSA answers 403)."""
    meta = json.loads(get(f"{PX}/{table}"))
    sel = []
    for v in meta["variables"]:
        if v["code"].lower().startswith("geolocation") and "PHILIPPINES" in v["valueTexts"]:
            sel.append({"code": v["code"], "selection": {"filter": "item", "values": [v["values"][v["valueTexts"].index("PHILIPPINES")]]}})
        else:
            sel.append({"code": v["code"], "selection": {"filter": "all", "values": ["*"]}})
    query = {"query": sel, "response": {"format": "csv"}}
    text = get(f"{PX}/{table}", json.dumps(query).encode()).decode("utf-8-sig", errors="replace")
    save(name, [f"Source: PSA OpenSTAT table {table.split('/')[-1].replace('.px', '')}, {meta['title']}. {PX}/{table}",
                f"Downloaded {NOW} by {WHO} through the PXWeb API (POST, CSV; geography = PHILIPPINES only, every other item listed). Raw PSA layout below, unchanged; '.' or '..' = not available."],
         text)


def bis(key, name, what):
    flow, series = key.split("/")
    url = f"{BIS}/{flow}/{series}/all?format=csv"
    d = pd.read_csv(io.BytesIO(get(url)))
    d = d[["TIME_PERIOD", "OBS_VALUE"]].rename(columns={"TIME_PERIOD": "month", "OBS_VALUE": "value"})
    save(name, [f"Source: Bank for International Settlements, statistics API, dataflow {flow}, series {series}: {what}. {url}",
                f"Downloaded {NOW} by {WHO}. Columns: month (YYYY-MM), value (as published by the BIS)."],
         d.to_csv(index=False))


def pinksheet_indices():
    page = get("https://www.worldbank.org/en/research/commodity-markets").decode("utf-8", errors="replace")
    url = re.search(r'https://thedocs\.worldbank\.org/[^"\']*CMO-Historical-Data-Monthly\.xlsx', page).group(0)
    x = pd.read_excel(io.BytesIO(get(url)), sheet_name="Monthly Indices", header=None)
    head = x.index[x.iloc[:, 0].astype(str).str.fullmatch(r"\d{4}M\d{2}")][0]
    names = [" ".join(str(x.iloc[r, c]) for r in range(max(0, head - 4), head) if pd.notna(x.iloc[r, c])).strip()
             for c in range(x.shape[1])]
    d = x.iloc[head:].copy()
    d.columns = ["month"] + names[1:]
    d = d.dropna(axis=1, how="all")
    d["month"] = d["month"].astype(str).str.replace("M", "-")
    save("WorldBank_PinkSheet_price_indices_monthly_1960-latest.csv",
         [f"Source: World Bank, Commodity Markets ('Pink Sheet'), CMO-Historical-Data-Monthly.xlsx, sheet 'Monthly Indices' (CC BY 4.0). {url}",
          f"Downloaded {NOW} by {WHO} from the link on https://www.worldbank.org/en/research/commodity-markets. Nominal US$ indices, 2010=100. Column names = the sheet's header rows joined."],
         d.to_csv(index=False))


if __name__ == "__main__":
    for t, n in PSA_TABLES.items():
        psa(t, n)
    for k, (n, w) in BIS_SERIES.items():
        bis(k, n, w)
    pinksheet_indices()
