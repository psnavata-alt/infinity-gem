"""Download PSA's annual imports or exports by commodity (HS) and country, keeping chosen HS prefixes (SAM v0.9 research;
24 Oct 2026, afternoon). Same method as data/raw/macro/PSA_OpenSTAT_coal_imports_HS2701-2704_downloaded_2026-10-24/
download_psa_coal_imports.py: the tables' commodity codes are not in the API metadata, so each country is requested with every
commodity and the wanted lines are kept. Some replies are not UTF-8: read as cp1252 then (only names are affected).
Tables under https://openstat.psa.gov.ph/PXWeb/api/v1/en/DB/2L/IMT/: AVI = annual imports (CIF US$, gross kg), AVE = annual
exports (FOB US$, gross kg); e.g. AVI/0042L4DMFD1.px = imports 2022, AVE/0032L4DXFD2.px = exports 2023.
Run:  py -I -X utf8 research/coal_lng_prices/download_psa_trade_hs.py <table, e.g. AVE/0032L4DXFD2.px> <prefixes, e.g. 2701,2702> <output csv>
Source: PSA, from Bureau of Customs entries. RESEARCH, NOT FOR CITATION."""
import csv
import io
import json
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

TABLE, KEEP, OUT = sys.argv[1], tuple(sys.argv[2].split(",")), sys.argv[3]
URL = "https://openstat.psa.gov.ph/PXWeb/api/v1/en/DB/2L/IMT/" + TABLE
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}


def get(data=None):
    req = urllib.request.Request(URL, data=data, headers={**UA, "Content-Type": "application/json"} if data else UA)
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


meta = json.loads(get())
cvar = next(v for v in meta["variables"] if v["text"].lower().startswith("country") or v["code"] == "Country")
kvar = next(v for v in meta["variables"] if v["code"].lower().startswith("commodity"))
names = dict(zip(cvar["values"], cvar["valueTexts"]))


def one(code):
    q = {"query": [{"code": kvar["code"], "selection": {"filter": "all", "values": ["*"]}},
                   {"code": cvar["code"], "selection": {"filter": "item", "values": [code]}}], "response": {"format": "csv"}}
    err = None
    for a in range(4):
        try:
            raw = get(json.dumps(q).encode())
            try:
                txt = raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                txt = raw.decode("cp1252", errors="replace")
            rows = list(csv.reader(io.StringIO(txt)))
            return rows[0], [[code] + r for r in rows[1:] if r and r[0].startswith(KEEP)], len(rows) - 1
        except Exception as e:                                     # noqa: BLE001
            err = e
            time.sleep(5 * (a + 1))
    raise RuntimeError(f"country {code}: {err}")


with ThreadPoolExecutor(4) as ex:
    res = list(ex.map(one, cvar["values"]))
head = res[0][0]
counts = {n for _, _, n in res}
with open(OUT, "w", newline="", encoding="utf-8") as f:
    f.write(f"# PSA OpenSTAT {TABLE}: {meta.get('title')}; {URL}; downloaded {datetime.now():%Y-%m-%d %H:%M} (PXWeb API, POST, "
            f"browser User-Agent, every commodity per country; HS {','.join(KEEP)} kept). Rows per country: {sorted(counts)}\n")
    w = csv.writer(f)
    w.writerow(["country_code", "country"] + head)
    for _, rows, _ in res:
        for r in rows:
            w.writerow([r[0], names[r[0]]] + r[1:])
print("done", OUT, "countries", len(res), "row counts per country:", sorted(counts))
