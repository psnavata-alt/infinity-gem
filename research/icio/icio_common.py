"""OECD Inter-Country Input-Output tables, 2025 edition (small CSV version): loader and helpers for research/icio.

Research, 23 Oct 2026. NOT FOR CITATION.

The data are NOT kept in this folder or anywhere in this repository: the OECD states no terms of use beyond the citation line (check
https://oe.cd/icio before any public use or redistribution). Extract one year's CSV (for example 2022_SML.csv from
2016-2022_SML.zip; or 2022.csv from the extended zips) into a NEW folder under
%TEMP%, and pass its path on the command line or in the environment variable ICIO_CSV_<year> (for example ICIO_CSV_2022).
Run with python -I (the data are third-party files):
    python -I research/icio/oil_cost_push_2022.py "%TEMP%\\icio...\\2022_SML.csv"
Only small derived tables (shares, price changes by industry) are written, to outputs/.

Layout of the small version (ReadMe, a reference copy (not distributed)): 81 areas
(80 economies and the Rest of the World, ROW) x 50 industries (ISIC Rev. 4) = 4,050 rows 'AREA_IND'; then the rows TLS
(taxes less subsidies on products, by using column), VA (value added at basic prices) and OUT (output). Columns: the 4,050
area-industries, then six final-demand columns per area (HFCE, NPISH, GGFC, GFCF, INVNT, DPABR) and OUT. Current US
dollars, million. Cite as: OECD (2025), OECD Inter-Country Input-Output Tables, https://oe.cd/icio.
The extended version (85 areas: China and Mexico split into CN1/CN2 and MX1/MX2, CHN and MEX rows zero) also loads; for
the Philippines the two versions are identical (a reference copy (not distributed) section 4).
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs"
FD_ITEMS = ("HFCE", "NPISH", "GGFC", "GFCF", "INVNT", "DPABR")

ASEAN_OTHER = ("BRN", "KHM", "IDN", "LAO", "MYS", "MMR", "SGP", "THA", "VNM")          # ASEAN without the Philippines
EU27 = ("AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN", "FRA", "DEU", "GRC", "HUN", "IRL", "ITA", "LVA",
        "LTU", "LUX", "MLT", "NLD", "POL", "PRT", "ROU", "SVK", "SVN", "ESP", "SWE")
CHINA = ("CHN", "CN1", "CN2")             # CN1/CN2 only in the extended version
MEXICO = ("MEX", "MX1", "MX2")

INDUSTRY_NAMES = {
    "A01": "Agriculture and hunting", "A02": "Forestry and logging", "A03": "Fishing and aquaculture",
    "B05": "Coal mining", "B06": "Crude petroleum and natural gas", "B07": "Metal ores", "B08": "Other mining and quarrying",
    "B09": "Mining support services", "C10T12": "Food, beverages and tobacco", "C13T15": "Textiles, apparel, leather",
    "C16": "Wood products", "C17_18": "Paper and printing", "C19": "Coke and refined petroleum", "C20": "Chemicals",
    "C21": "Pharmaceuticals", "C22": "Rubber and plastics", "C23": "Other non-metallic minerals",
    "C24A": "Basic iron and steel", "C24B": "Basic precious and non-ferrous metals", "C25": "Fabricated metal products",
    "C26": "Computer, electronic and optical", "C27": "Electrical equipment", "C28": "Machinery n.e.c.",
    "C29": "Motor vehicles", "C301": "Ships and boats", "C302T309": "Other transport equipment",
    "C31T33": "Furniture and other manufacturing", "D": "Electricity, gas, steam", "E": "Water, sewerage, waste",
    "F": "Construction", "G": "Wholesale and retail trade", "H49": "Land transport", "H50": "Water transport",
    "H51": "Air transport", "H52": "Warehousing and transport support", "H53": "Postal and courier",
    "I": "Accommodation and food services", "J58T60": "Publishing and broadcasting", "J61": "Telecommunications",
    "J62_63": "IT and information services", "K": "Finance and insurance", "L": "Real estate",
    "M": "Professional, scientific, technical", "N": "Administrative and support services",
    "O": "Public administration and defence", "P": "Education", "Q": "Health and social work",
    "R": "Arts and recreation", "S": "Other services", "T": "Households as employers"}


def utf8_stdout():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def csv_path(year: int, argv=None) -> Path:
    """The ICIO CSV for `year`: the first command-line argument that ends in .csv, else ICIO_CSV_<year>."""
    argv = sys.argv[1:] if argv is None else argv
    p = next((a for a in argv if a.lower().endswith(".csv")), None) or os.environ.get(f"ICIO_CSV_{year}")
    if not p:
        raise SystemExit(f"Give the path of the ICIO {year} CSV (extracted under %TEMP%) as an argument, or set ICIO_CSV_{year}.")
    p = Path(p)
    if ROOT in p.resolve().parents:
        raise SystemExit("The ICIO CSV must not sit inside this repository (terms of use not stated): extract it under %TEMP%.")
    return p


@dataclass
class ICIO:
    year: int
    areas: list            # area codes in table order
    inds: list             # 50 industry codes
    labels: list           # 'AREA_IND' row and column labels of the intermediate block
    Z: np.ndarray          # intermediate use, rows = supplying area-industry, columns = using area-industry
    Y: np.ndarray          # final demand, rows = supplying area-industry, columns = fd_labels
    fd_labels: list        # 'AREA_ITEM'
    TLS: np.ndarray        # taxes less subsidies on products, by using area-industry
    TLS_fd: np.ndarray     # same, by final-demand column
    VA: np.ndarray         # value added at basic prices, by area-industry
    X: np.ndarray          # output, by area-industry (OUT row)
    X_col: np.ndarray      # output from the OUT column (rows): must equal X
    n_na: int              # cells read as 'NA' (set to zero)

    def block(self, area: str) -> np.ndarray:
        """Row (or column) positions of one area's 50 industries."""
        i = self.areas.index(area)
        n = len(self.inds)
        return np.arange(i * n, (i + 1) * n)

    def fd_cols(self, area: str, items=FD_ITEMS) -> np.ndarray:
        return np.array([self.fd_labels.index(f"{area}_{it}") for it in items if f"{area}_{it}" in self.fd_labels])

    def area_of_row(self) -> np.ndarray:
        return np.array([lab.split("_", 1)[0] for lab in self.labels])

    def ind_of_row(self) -> np.ndarray:
        return np.array([lab.split("_", 1)[1] for lab in self.labels])


def load(path: Path, year: int) -> ICIO:
    """Read one year's ICIO CSV (small or extended version)."""
    d = pd.read_csv(path, index_col=0, na_values=["NA"], keep_default_na=False, low_memory=False)
    n_na = int(d.isna().sum().sum())
    d = d.fillna(0.0).astype(float)
    rows = d.index.tolist()
    labels = [r for r in rows if r not in ("TLS", "VA", "OUT")]
    cols = d.columns.tolist()
    if cols[:len(labels)] != labels:
        raise ValueError("unexpected layout: the first columns are not the area-industries in row order")
    fd_labels = [c for c in cols[len(labels):] if c != "OUT"]
    areas = list(dict.fromkeys(lab.split("_", 1)[0] for lab in labels))
    inds = list(dict.fromkeys(lab.split("_", 1)[1] for lab in labels))
    if len(labels) != len(areas) * len(inds):
        raise ValueError("unexpected layout: rows are not areas x industries")
    nI = len(labels)
    Z = d.iloc[:nI, :nI].to_numpy()
    Y = d.loc[labels, fd_labels].to_numpy()
    return ICIO(year=year, areas=areas, inds=inds, labels=labels, Z=Z, Y=Y, fd_labels=fd_labels,
                TLS=d.loc["TLS", labels].to_numpy(), TLS_fd=d.loc["TLS", fd_labels].to_numpy(),
                VA=d.loc["VA", labels].to_numpy(), X=d.loc["OUT", labels].to_numpy(),
                X_col=d.loc[labels, "OUT"].to_numpy(), n_na=n_na)


def balance_report(t: ICIO, area: str = "PHL") -> dict:
    """Accounting checks for one area: inputs + TLS + VA = output (by column); output = sales (by row)."""
    b = t.block(area)
    col = t.Z[:, b].sum(axis=0) + t.TLS[b] + t.VA[b] - t.X[b]
    row = t.Z[b, :].sum(axis=1) + t.Y[b, :].sum(axis=1) - t.X_col[b]
    return {"max |inputs + TLS + VA - output| (US$ mn)": float(np.abs(col).max()),
            "max |sales - output| (US$ mn)": float(np.abs(row).max()),
            "max |OUT row - OUT column| (US$ mn)": float(np.abs(t.X[b] - t.X_col[b]).max()),
            "NA cells set to zero (whole table)": t.n_na}


def partner_group(area: str) -> str:
    """Partner groups for (b)."""
    if area == "PHL":
        return "Philippines (own final demand)"
    if area == "USA":
        return "United States"
    if area in CHINA:
        return "China"
    if area == "JPN":
        return "Japan"
    if area == "KOR":
        return "Korea"
    if area in ASEAN_OTHER:
        return "ASEAN (other nine)"
    if area in EU27:
        return "European Union (27)"
    return "Rest of the world"


GROUP_ORDER = ["United States", "China", "Japan", "Korea", "ASEAN (other nine)", "European Union (27)", "Rest of the world",
               "Philippines (own final demand)"]
