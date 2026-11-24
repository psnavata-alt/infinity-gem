"""Foreign flows by institution (0.4.3, 21 Nov 2026; opt-in, check GF2).

Data: the BSP's balance of payments, BPM6 (the BSP's Excel tables, Statistics, External Accounts, Balance of Payments, file
dates 18 Oct 2026; sheet 'Annual', US$ million; not distributed with this repository: save them in data/raw/macro/bsp_bop/):
  Table1.xlsx    A.1.bop6 summary: current account (A), capital account (B), financial account (C; by instrument C.3-C.6), net
                 unclassified items (D), overall BOP position (E; E.3 change in reserve assets, E.4 change in reserve liabilities);
  Table1.6.xlsx  direct investment (A.1.F; NOT split by institutional sector in the BSP's table);
  Table1.7.xlsx  portfolio investment (A.1.G; .1 assets, .2 liabilities) by sector;
  Table1.8.xlsx  financial derivatives (A.1.H; .5 assets, .6 liabilities) by sector;
  Table1.9.xlsx  other investment (A.1.I; .8 assets, .9 liabilities) by sector;
  Table1.10.xlsx change in net reserves (A.1.J).
Sectors, as the BSP's tables name them: Central Bank; Deposit-Taking Corporations, except the Central Bank; General Government;
Other Sectors.
Rows are found by their codes and sector names, not by row numbers.

BSP's sign convention (Table1.xlsx technical notes 2-4, 7): financial account = net acquisition of financial assets less net
incurrence of liabilities (negative = net inflow); overall BOP = CA + KA - FA + net unclassified items = change in reserve assets less
change in reserve liabilities. Here every line is written as FINANCING of the current account deficit (+ = money from abroad):
  -CA = KA + government + central bank (excl. reserves) + banks + other sectors + direct investment + not split by sector
        + net unclassified items - overall BOP position (reserves: an accumulation uses financing).

The model link (scenario_bop): Infinity GEM has one foreign saving (the current account deficit) plus, with DynamicCGE(gfin=...), the
government's borrowing abroad. The baseline's foreign saving is shared out with a year's BOP shares; a scenario's change is the
government's (gfin's foreign part) and the rest, which the model does not split between private flows, the BSP's reserves and
errors (with the fixed peso of the short-run years the BSP's reserves are the implicit buffer). The lines add up to the model's
total by construction; check GF2 T7 tests that, and the BSP identity in the data.
a design note (not included).
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

BSP_BOP = Path(__file__).resolve().parent.parent / "data" / "raw" / "macro" / "bsp_bop"   # not distributed: save the BSP's tables here
SECTORS = {"central bank": "central_bank", "deposit-taking corporations, except the central bank": "banks",
           "general government": "government", "other sectors": "other_sectors"}
# instrument: (file, code of the instrument total, code of its assets, code of its liabilities)
INSTRUMENTS = {"portfolio": ("Table1.7.xlsx", "A.1.G", "A.1.G.1", "A.1.G.2"),
               "derivatives": ("Table1.8.xlsx", "A.1.H", "A.1.H.5", "A.1.H.6"),
               "other_investment": ("Table1.9.xlsx", "A.1.I", "A.1.I.8", "A.1.I.9")}
LINES = ("capital_account", "government", "central_bank", "banks", "other_sectors", "direct_investment", "not_split_by_sector",
         "net_unclassified", "reserves")
_CODE = re.compile(r"^(A\.1(?:\.[A-Za-z0-9]+)+)\s+(.*)$")


def _annual(path):
    """The 'Annual' sheet as {code: (name, {year: value})}, codes as printed (A.1.G.2.2.3 ...)."""
    df = pd.read_excel(path, sheet_name="Annual", header=None)
    hdr = cols = None
    for i in range(min(15, len(df))):
        c = {}
        for j, v in enumerate(df.iloc[i].tolist()):
            try:
                y = int(float(str(v).strip()))
            except ValueError:
                continue
            if 1990 < y < 2100:
                c[y] = j
        if len(c) >= 3:
            hdr, cols = i, c
            break
    if hdr is None:
        raise ValueError(f"{Path(path).name}: no row of years in the first 15 rows")
    first = min(cols.values())
    out = {}
    for i in range(hdr + 1, len(df)):
        lab = next((str(v).strip() for v in df.iloc[i, :first].tolist() if isinstance(v, str) and v.strip()), "")
        m = _CODE.match(lab)
        if not m:
            continue
        vals = {}
        for y, j in cols.items():
            v = df.iat[i, j]
            vals[y] = float(v) if isinstance(v, (int, float, np.number)) and pd.notna(v) else 0.0   # BSP prints "." for ~0
        out[m.group(1)] = (" ".join(m.group(2).split()), vals)
    return out


def bsp_bop_by_institution(year=2023, folder=None) -> dict:
    """The current account deficit of `year` and its financing by institution (US$ million, + = from abroad), from the BSP's BPM6
    tables. Returns {'year', 'current_account', 'lines' {LINES: value}, 'shares' {line: value / -CA}, 'checks' {...}, 'source'}.
    checks: 'identity_gap' = the sum of the lines + CA (BSP's own totals; rounding only), 'not_split' = the part of portfolio,
    derivatives and other investment that BSP's tables do not assign to a sector, 'reserves_gap' = Table1's overall position less
    Table1.10's change in net reserves, 'instrument_gaps' = each instrument's total less its assets less liabilities."""
    folder = Path(folder or BSP_BOP)
    s = _annual(folder / "Table1.xlsx")
    v = lambda code: s[code][1][int(year)]
    ca, ka, fa, nui, ovr = v("A.1.bop6.A"), v("A.1.bop6.B"), v("A.1.bop6.C"), v("A.1.bop6.D"), v("A.1.bop6.E")
    di = v("A.1.bop6.C.3")
    net = {k: 0.0 for k in SECTORS.values()}          # net incurrence of liabilities less net acquisition of assets, by sector
    not_split, inst_gaps = 0.0, {}
    for name, (fn, tot, a_code, l_code) in INSTRUMENTS.items():
        t = _annual(folder / fn)
        by = {k: 0.0 for k in SECTORS.values()}
        for code, (nm, vals) in t.items():
            sec = SECTORS.get(nm.lower())
            if sec is None:
                continue
            if code.startswith(a_code + "."):
                by[sec] -= vals[int(year)]
            elif code.startswith(l_code + "."):
                by[sec] += vals[int(year)]
        total_fa = t[tot][1][int(year)]                     # the instrument's net (assets less liabilities)
        inst_gaps[name] = total_fa - (t[a_code][1][int(year)] - t[l_code][1][int(year)])
        not_split += -total_fa - sum(by.values())           # financing not assigned to a sector
        for k in net:
            net[k] += by[k]
    lines = dict(capital_account=ka, government=net["government"], central_bank=net["central_bank"], banks=net["banks"],
                 other_sectors=net["other_sectors"], direct_investment=-di, not_split_by_sector=not_split, net_unclassified=nui,
                 reserves=-ovr)
    r = _annual(folder / "Table1.10.xlsx")
    checks = {"identity_gap": sum(lines.values()) + ca, "not_split": not_split,
              "reserves_gap": ovr - r["A.1.J"][1][int(year)],
              "fa_gap": fa - (di + v("A.1.bop6.C.4") + v("A.1.bop6.C.5") + v("A.1.bop6.C.6")),
              "instrument_gaps": inst_gaps}
    return {"year": int(year), "current_account": ca, "current_account_pct_gdp": v("A.1.bop6.A.2"), "lines": lines,
            "shares": {k: x / -ca for k, x in lines.items()},
            "checks": checks, "source": f"BSP BPM6 balance of payments, Tables 1, 1.6-1.10 (sheet Annual), {folder}"}


def scenario_bop(d, sim, year=2023, shares=None) -> pd.DataFrame:
    """The model's current account deficit (foreign saving, the government's borrowing abroad included) of a DynamicCGE path, by
    institution, in the model's foreign-currency units (₱ bn at the 2023 SAM's exchange rate, the year's scale) and % of GDP.
    Baseline lines: the baseline's foreign saving x the BOP shares of `year` (bsp_bop_by_institution; or `shares` given). Path:
    the same lines, plus the change in the government's borrowing abroad on the government's line (DynamicCGE gfin: its foreign
    part of the extra borrowing, at the path's peso; 0 without gfin) and the rest of the change in foreign saving on
    'private_and_reserves_change' (private flows, the BSP's reserves and errors: not split by the model). Columns '<line>' and
    '<line>_pct_gdp', 'total', 'total_pct_gdp', 'base_total'; the lines add up to 'total' (check GF2 T7)."""
    sh = shares or bsp_bop_by_institution(year)["shares"]
    rows = []
    for t in sim.table.index:
        b, s = d.base.solutions[t], sim.solutions[t]
        fb = float(b["FSAV"]) + (float(b["GFOR"]) if "GFOR" in b else 0.0)
        fs = float(s["FSAV"]) + (float(s["GFOR"]) if "GFOR" in s else 0.0)
        exr, ngdp = float(sim.table.loc[t, "exr"]), float(sim.table.loc[t, "nominal_gdp"])
        dgov = (float(sim.table.loc[t, "gov_borrowing_abroad"]) / exr if "gov_borrowing_abroad" in sim.table.columns else 0.0)
        row = {"year": t, "base_total": fb, "total": fs}
        for k in LINES:
            row[k] = sh[k] * fb
        row["government"] += dgov
        row["private_and_reserves_change"] = (fs - fb) - dgov
        for k in list(LINES) + ["private_and_reserves_change", "total"]:
            row[f"{k}_pct_gdp"] = row[k] * exr / ngdp * 100
        rows.append(row)
    out = pd.DataFrame(rows).set_index("year")
    out.attrs.update({"shares_year": int(year), "shares": dict(sh), "units": "model foreign-currency units (₱ bn at the 2023 SAM's "
                      "exchange rate, the year's scale)"})
    return out
