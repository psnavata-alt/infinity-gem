"""What PSA's 2018 'refined petroleum' I-O row really holds, by SAM user (SAM v0.8 candidates; 24 Oct 2026).

RESEARCH, NOT FOR CITATION. Reads only files on disk (data/raw/io/): PSA's 2018 Supply and Use Tables (240 products x 240
industries) and the 240-industry I-O transaction table (Table C.1). No downloads.

PSA's I-O is the Use table under the fixed product-sales structure, T = D U (research/electricity_fuel_mix/fuel_mix_evidence.py,
verified to about 1e-9): D[r, p] = industry r's share of the domestic production of product p (Supply table), applied to
every flow of p, imports included. The I-O's refined-petroleum rows, 107-108 (SAM's cpetr), therefore carry D[107-108, p] of every product p the
refining industries produce as secondary products. This script splits each user's purchases from rows 107-108, the final-demand
columns and the imports column into those products, grouped:
    coal (039) | crude oil and natural gas (040) | refined and other petroleum (107-108) | other mining (041-045) |
    electricity (172-173) | everything else,
aggregated to the SAM's activities (tools/build_sam_petroleum_split.psa_activity; 57 -> amric; 107-108 -> apetr) and final
demand, ₱ bn, and checks that the products add back to the I-O cells. It also reports which industries produce products
039 and 040 (Supply table) and who buys product 040 (Use table), the basis for any crude/gas split.
Outputs: outputs/refined_row_content_2018_<stamp>_{users,supply_039_040,use_040}.csv; the inputs of Infinity GEM SAM v0.8,
data/processed/refined_row_content_2018_v0.8_inputs.csv (each SAM user's coal and crude-gas content; the imported parts).
Run: py -I -X utf8 research/coal_lng_prices/refined_row_content_2018.py
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "research" / "electricity_fuel_mix"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from infinity_gem import paths                                          # noqa: E402
import fuel_mix_evidence as FM                                      # noqa: E402  (psa_sut, psa_tt, market_shares)
from build_sam_petroleum_split import psa_activity                  # noqa: E402

REF_ROWS = (107, 108)
GROUPS = {"coal (039)": [39], "crude oil and natural gas (040)": [40], "refined and other petroleum (107-108)": [107, 108],
          "other mining (041-045)": list(range(41, 46)), "electricity (172-173)": [172, 173]}


def sam_activity(k: int) -> str:
    return "amric" if k == 57 else "apetr" if k in REF_ROWS else psa_activity(k)


def main():
    s, t = FM.psa_sut(), FM.psa_tt()
    U, D = s["use"], FM.market_shares(s["supply"])                 # U[p, j] (products x industries); D[r, p]
    R = [r - 1 for r in REF_ROWS]
    w = D[R, :].sum(axis=0)                                         # refining's share of each product's domestic production
    content = w[:, None] * U                                        # product p inside rows 107-108, bought by industry j
    gap = float(np.abs(content.sum(axis=0) - t["T"][R, :].sum(axis=0)).max())
    fd = {k: w * v for k, v in s["fd"].items()}
    imp = w * s["imports"]
    gap_m = abs(float(imp.sum()) - float(t["imports"][R].sum()))
    grp = {g: [p - 1 for p in ps] for g, ps in GROUPS.items()}
    other = [p for p in range(240) if not any(p in v for v in grp.values())]
    grp["everything else"] = other
    acts = [sam_activity(k) for k in range(1, 241)]
    rows = {}
    for g, ps in grp.items():
        rows[g] = pd.Series(content[ps, :].sum(axis=0) / 1e3, index=acts).groupby(level=0).sum()
    users = pd.DataFrame(rows)
    for k, v in fd.items():
        if np.abs(v).sum() > 0 and k not in ("Final Demand", "Total Use at Purchasers' Prices"):   # the two totals: below
            users.loc[f"final demand: {k}"] = [float(v[ps].sum()) / 1e3 for ps in grp.values()]
    users.loc["total use (intermediate and final)"] = [float(content[ps, :].sum() + sum(v[ps].sum() for k, v in fd.items()
                                                       if k not in ("Final Demand", "Total Use at Purchasers' Prices"))) / 1e3
                                                       for ps in grp.values()]
    users.loc["imports (I-O imports column)"] = [float(imp[ps].sum()) / 1e3 for ps in grp.values()]
    users["total (I-O rows 107-108)"] = users[list(grp)].sum(axis=1)
    users["coal share"] = users["coal (039)"] / users["total (I-O rows 107-108)"].where(users["total (I-O rows 107-108)"] != 0)
    users["crude-gas share"] = users["crude oil and natural gas (040)"] / users["total (I-O rows 107-108)"].where(
        users["total (I-O rows 107-108)"] != 0)
    users = users.sort_values("total (I-O rows 107-108)", ascending=False)
    # who produces 039 and 040 (Supply table), who buys 040 (Use table)
    ind = s["industries"]
    sup = pd.DataFrame({f"produces {p:03d} (₱ bn)": s["supply"][p - 1, :] / 1e3 for p in (39, 40)}, index=[f"{j + 1} {ind[j]}" for j in range(240)])
    sup = sup[(sup.abs() > 0.01).any(axis=1)]
    sup.loc["imports"] = [s["imports"][38] / 1e3, s["imports"][39] / 1e3]
    use40 = pd.Series(U[39, :] / 1e3, index=[f"{j + 1} {ind[j]}" for j in range(240)])
    use40 = use40[use40.abs() > 0.01].sort_values(ascending=False)
    for k, v in s["fd"].items():
        if abs(v[39]) > 0.01:
            use40[f"final demand: {k}"] = v[39] / 1e3
    stamp = dt.datetime.now()
    base = paths.output_dir() / f"refined_row_content_2018_{stamp:%Y%m%d_%H%M}"
    users.to_csv(f"{base}_users.csv")
    sup.to_csv(f"{base}_supply_039_040.csv")
    use40.to_frame("buys product 040, crude oil and natural gas (₱ bn, Use table)").to_csv(f"{base}_use_040.csv")
    # inputs of Infinity GEM SAM v0.8 (tools/build_own_sam_2023.py, refined_row_content): each SAM user's coal and crude-gas content of
    # its purchases from rows 107-108, and the imported part of each (imports column content / total-use content)
    keep = users.drop(index=[i for i in users.index if i.startswith("final demand: Changes")])
    inp = keep[["coal (039)", "crude oil and natural gas (040)", "total (I-O rows 107-108)", "coal share", "crude-gas share"]].copy()
    inp.index.name = "user"
    phi = {"coal": float(users.loc["imports (I-O imports column)", "coal (039)"] / users.loc["total use (intermediate and final)", "coal (039)"]),
           "crude and gas": float(users.loc["imports (I-O imports column)", "crude oil and natural gas (040)"]
                                  / users.loc["total use (intermediate and final)", "crude oil and natural gas (040)"])}
    head = ["# PSA 2018: products inside the I-O's refined-petroleum rows (107-108) by SAM user, ₱ bn, and the imported part of each",
            "# (inputs of Infinity GEM SAM v0.8, tools/build_own_sam_2023.py refined_row_content; RESEARCH, NOT FOR CITATION).",
            "# Source: PSA 2018 Supply and Use Tables and 240-industry I-O Table C.1 (data/raw/io/); the I-O is T = D U (D = industry",
            "# shares of each product's domestic production, Supply table); content of product p in rows 107-108 = D[107-108, p] x U[p, user].",
            f"# Refining's (107-108) share of domestic production: coal {w[38]:.6f}, crude oil and natural gas {w[39]:.6f}.",
            f"# imported part (imports-column content / total-use content): coal {phi['coal']:.6f}, crude and gas {phi['crude and gas']:.6f}.",
            f"# Products add back to the I-O cells to {gap:.1e} ₱ m. Written {stamp:%Y-%m-%d %H:%M} by research/coal_lng_prices/refined_row_content_2018.py."]
    fp = paths.DATA_PROCESSED / "refined_row_content_2018_v0.8_inputs.csv"
    with open(fp, "w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join(head) + "\n")
        inp.to_csv(fh, float_format="%.9f")
    print("saved", fp, phi)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 20)
    print("refining industries' (107-108) share of domestic production: coal %.3f, crude and gas %.3f, refined %.3f, other petroleum %.3f"
          % (w[38], w[39], w[106], w[107]))
    print(f"products add back to the I-O cells: max gap {gap:.2e} ₱ m (industries), imports {gap_m:.2e} ₱ m")
    print(users.round(3).to_string())
    print(sup.round(3).to_string())
    print(use40.round(3).to_string())
    print("saved", base)


if __name__ == "__main__":
    main()
