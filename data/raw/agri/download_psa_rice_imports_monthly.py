"""Download PSA's MONTHLY rice imports (HS 1006), quantity and CIF value, 2019-2026, for the Armington sensitivity (17 Oct 2026, night).

Tables: PSA OpenSTAT 2L/IMT/QPI ("Monthly Quantity of Philippine Import by commodity and country of origin, <year>") and
2L/IMT/CIF ("Monthly CIF Value of Philippine Import ..."), one table per year. Source of basic data: Bureau of Customs
import entries, compiled by PSA; commodity codes = PSCC (HS-based); quantity in kilograms (as in the annual table), CIF
value in US dollars.

Quirk (as in download_psa_rice_imports.py): commodity codes cannot be selected in a query, so each country is
requested with every commodity and only HS 1006 lines are kept. Countries: the seven origins that supplied 99.9% of 2023
rice imports by volume (PSA annual table 0032L4DMFD2, on file): Viet Nam 892, Thailand 780, Myanmar 116, Pakistan 624,
India 376, China 164, Cambodia 428 (PSA country codes).

Writes PSA_OpenSTAT_rice_imports_HS1006_monthly_2019-2026.csv (this folder): one row per year, month, country and HS 1006
commodity line: quantity_kg, cif_usd ('..' as published = missing). Run:  py data/raw/agri/download_psa_rice_imports_monthly.py
"""
import csv, io, json, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

OUT = Path(__file__).resolve().parent / "PSA_OpenSTAT_rice_imports_HS1006_monthly_2019-2026.csv"
BASE = "https://openstat.psa.gov.ph/PXWeb/api/v1/en/DB/2L/IMT"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
COUNTRIES = ["892", "780", "116", "624", "376", "164", "428"]
YEARS = range(2019, 2027)
CACHE = Path(__file__).resolve().parent / "_cache_psa_rice_monthly"   # HS 1006 lines of each response (re-runs skip the download)
CACHE.mkdir(exist_ok=True)


def get(url, data=None):
    req = urllib.request.Request(url, data=data, headers={**UA, "Content-Type": "application/json"} if data else UA)
    with urllib.request.urlopen(req, timeout=600) as r:
        return r.read()


def tables():
    """{(kind, year): url} from the folder listings (table ids differ by year)."""
    out = {}
    for kind in ("QPI", "CIF"):
        for t in json.loads(get(f"{BASE}/{kind}")):
            title = t["text"]
            for y in YEARS:
                if title.rstrip().endswith(str(y)) or title.rstrip().endswith(f", {y}"):
                    out[(kind, y)] = f"{BASE}/{kind}/{t['id']}"
    # the QPI table labelled ", 2000" with id 0072L4DMQC9 is the 2020 table (its neighbours are 2021 and 2019)
    if ("QPI", 2020) not in out:
        out[("QPI", 2020)] = f"{BASE}/QPI/0072L4DMQC9.px"
    return out


def one(job):
    kind, year, url, code = job
    meta = json.loads(get(url))
    period = next(v for v in meta["variables"] if v["code"] == "Period")
    yr = next(v for v in meta["variables"] if v["code"] == "Year")
    if yr["valueTexts"][0] != str(year):
        raise RuntimeError(f"{url}: table year {yr['valueTexts'][0]} is not {year}")
    q = {"query": [{"code": "Commodity Code", "selection": {"filter": "all", "values": ["*"]}},
                   {"code": "Country", "selection": {"filter": "item", "values": [code]}}],
         "response": {"format": "csv"}}
    err = None
    for attempt in range(4):
        try:
            cache = CACHE / f"{kind}_{year}_{code}.csv"
            if cache.exists():
                text = cache.read_text(encoding="utf-8")
            else:
                text = get(url, json.dumps(q).encode()).decode("utf-8-sig")
                lines = text.splitlines()
                keep_text = "\n".join(lines[:1] + [l for l in lines[1:] if l.lstrip('"').startswith("1006")])
                cache.write_text(keep_text, encoding="utf-8")
                text = keep_text
            rows = list(csv.reader(io.StringIO(text)))
            head = rows[0]
            keep = [r for r in rows[1:] if r[0].startswith("1006")]
            return kind, year, code, head, keep, period["valueTexts"]
        except Exception as e:  # noqa: BLE001
            err = e
            time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"{kind} {year} {code}: {err}")


def main():
    tb = tables()
    missing = [(k, y) for k in ("QPI", "CIF") for y in YEARS if (k, y) not in tb]
    if missing:
        print("tables not found:", missing)
    jobs = [(k, y, tb[(k, y)], c) for (k, y) in sorted(tb) for c in COUNTRIES]
    data = {}
    with ThreadPoolExecutor(4) as ex:
        for kind, year, code, head, keep, months in ex.map(one, jobs):
            # columns: commodity code, country, then one per month ("2024 January", ...)
            mnames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
                      "November", "December"]
            for r in keep:
                for col, val in zip(head[2:], r[2:]):
                    parts = col.split(" ", 1)
                    if len(parts) != 2 or not parts[0].isdigit():
                        continue
                    yy, mm = parts
                    ab = [n[:3].lower() for n in mnames]
                    if mm.strip()[:3].lower() not in ab:       # totals or other non-month columns
                        continue
                    if int(yy) != year:
                        raise RuntimeError(f"{kind} {year}: column {col}")
                    key = (year, ab.index(mm.strip()[:3].lower()) + 1, code, r[0])
                    data.setdefault(key, {})[kind] = val
            print(f"{kind} {year} {code}: {len(keep)} HS 1006 lines; columns {head[1:3]}...", flush=True)
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        for h in ["Source: Philippine Statistics Authority (PSA) OpenSTAT; source of basic data Bureau of Customs. Tables 2L/IMT/QPI "
                  "(Monthly Quantity of Philippine Import by commodity and country of origin) and 2L/IMT/CIF (Monthly CIF Value), "
                  "2019-2026, one table per year.",
                  f"URLs: {sorted(set(tb.values()))}",
                  "Units: quantity in kilograms; CIF value in US dollars. HS 1006 (rice) lines only; countries " + ", ".join(COUNTRIES)
                  + " (PSA codes; 99.9% of 2023 rice imports by volume).",
                  f"Downloaded {datetime.now():%Y-%m-%d %H:%M} by download_psa_rice_imports_monthly.py. '..' = no data."]:
            f.write("# " + h + "\n")
        w = csv.writer(f)
        w.writerow(["year", "month", "country_code", "commodity_code", "quantity_kg", "cif_usd"])
        for (y, mth, c, com), v in sorted(data.items()):
            w.writerow([y, mth, c, com, v.get("QPI", ""), v.get("CIF", "")])
    print(f"wrote {OUT.name}: {len(data)} rows")


if __name__ == "__main__":
    main()
