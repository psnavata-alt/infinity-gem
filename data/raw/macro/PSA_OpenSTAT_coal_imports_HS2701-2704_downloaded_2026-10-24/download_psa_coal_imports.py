"""Download PSA's imports of coal (HS 2701; and 2702-2704: lignite, peat, coke) by country from PSA OpenSTAT (24 Oct 2026).
A Philippine coal price in place of Newcastle. Tables under DB/2L/IMT/: AVI (annual value, quantity
and gross kilo; e.g. AVI/0032L4DMFD2.px = 2023), CIF (monthly CIF value, US$) and GKI (monthly gross kilo). The tables'
commodity codes are not in the API metadata, so each country is requested with every commodity and the HS 2701-2704 lines
are kept (as data/raw/agri/download_psa_rice_imports.py does). Some replies are not UTF-8: read as cp1252 then.
Run:  py -I download_psa_coal_imports.py <table, e.g. CIF/0012L4DMVD5.px> <output csv>
Source: PSA, from Bureau of Customs import entries; quantity in kg; values CIF in US$; latest month preliminary (P)."""
import csv, io, json, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
TABLE, OUT = sys.argv[1], sys.argv[2]
URL = "https://openstat.psa.gov.ph/PXWeb/api/v1/en/DB/2L/IMT/" + TABLE
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
KEEP = ("2701", "2702", "2703", "2704")
def get(data=None):
    req = urllib.request.Request(URL, data=data, headers={**UA, "Content-Type": "application/json"} if data else UA)
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()
def one(code):
    q = {"query": [{"code": "Commodity Code", "selection": {"filter": "all", "values": ["*"]}},
                   {"code": "Country", "selection": {"filter": "item", "values": [code]}}], "response": {"format": "csv"}}
    err = None
    for a in range(4):
        try:
            raw = get(json.dumps(q).encode())
            try: txt = raw.decode("utf-8-sig")
            except UnicodeDecodeError: txt = raw.decode("cp1252", errors="replace")
            rows = list(csv.reader(io.StringIO(txt)))
            return rows[0], [[code] + r for r in rows[1:] if r[0].startswith(KEEP)], len(rows) - 1
        except Exception as e:
            err = e; time.sleep(5 * (a + 1))
    raise RuntimeError(f"country {code}: {err}")
meta = json.loads(get())
c = next(v for v in meta["variables"] if v["code"] == "Country")
names = dict(zip(c["values"], c["valueTexts"]))
with ThreadPoolExecutor(4) as ex:
    res = list(ex.map(one, c["values"]))
head = res[0][0]
counts = {n for _, _, n in res}
with open(OUT, "w", newline="", encoding="utf-8") as f:
    f.write(f"# PSA OpenSTAT {TABLE}: {meta.get('title')}; {URL}; downloaded {datetime.now():%Y-%m-%d %H:%M} (PXWeb API, every commodity per country; HS 2701-2704 kept). Rows per country: {sorted(counts)}\n")
    w = csv.writer(f); w.writerow(["country_code", "country"] + head)
    for _, rows, _ in res:
        for r in rows:
            w.writerow([r[0], names[r[0]]] + r[1:])
print("done", OUT, "row counts per country:", sorted(counts))
