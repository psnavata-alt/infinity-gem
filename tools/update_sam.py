"""Update the 2023 SAM to a later year by cross-entropy balancing to PSA national-accounts totals.

17 Oct 2026. Route (a): keep IFPRI's 2023 structure (the petroleum-
and rice-split SAM that "0.3 recommended" uses) and move it to year Y's nominal totals from PSA, as IFPRI's own SAM updates do.

Method (Robinson, Cattaneo and El-Said 2001, Economic Systems Research 13(1), deterministic cross-entropy;
a reference copy (not distributed)):
  1. A prior x0 = each 2023 cell scaled by the PSA nominal growth (Y over 2023) of the aggregate it belongs to: an activity's
     column and its make row by its PSA industry's GVA; household, government, investment, export and import cells by
     household consumption, government consumption, fixed capital formation, exports and imports; every other cell by
     nominal GDP. Zero cells stay zero; signs are kept.
  2. The updated SAM x minimises the cross-entropy distance sum |x| ln(|x| / |x0|) - |x| + |x0| from the prior, subject to
     (a) every account balancing (row total = column total) and (b) the control totals: value added of each of PSA's 16
     industries, and economy-wide household consumption, government consumption, fixed capital formation, exports and
     imports, each equal to its 2023 SAM value times PSA's nominal growth Y/2023. Controlling growth rates, not PSA's levels,
     keeps the SAM's own 2023 definitions (IFPRI's SAM differs from PSA's 2023 accounts in places).
  The solution has the form x = x0 exp(A'lambda) (signs kept); the multipliers lambda are found by Newton's method on the
  dual (one per constraint), which converges in a few iterations.
Data: PSA OpenSTAT 0052B5BPRA1 (GVA by industry, annual, current prices) and 0012B5BEXQ1 (GDP by expenditure, quarterly,
current prices; four quarters summed), both in data/raw/macro/.
Outputs: data/processed/InfinityGEM_SAM_PHL_<Y>_updated_from_IFPRI_2023_petroleum_rice_split.csv and outputs/sam_update_<Y>_<date>.md.
Run:  py tools/update_sam.py 2024   (and 2025). NOT the default SAM: opt-in (settings, sam_year=...). Check S4.
      py tools/update_sam.py 2024 2025 --base psa   (0.3.9: from the PSA-consistent 2023 SAM; settings
      sam_year=... with sam_variant='psa'; check S5)
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from infinity_gem import paths                                          # noqa: E402
from infinity_gem.sam import SAM                                        # noqa: E402
from infinity_gem.dynamic import PSA_INDUSTRIES                          # noqa: E402
from build_sam_petroleum_split import write_ifpri_csv               # noqa: E402

BASE = 2023
EXP = {"hfce": "Household final consumption expenditure", "gfce": "Government final consumption expenditure",
       "gfcf": "Gross fixed capital formation", "exports": "Exports of goods and services",
       "imports": "Imports of goods and services", "gdp": "Gross Domestic Product"}
FACTORS = ("flab-n", "flab-p", "flab-s", "flnd", "fcap")


def out_path(year: int, base: str = "ifpri") -> Path:
    return paths.sam_updated(year, base)


def base_sam(base: str = "ifpri"):
    """The 2023 SAM being updated: IFPRI's rice-split SAM (as before) or the PSA-consistent one."""
    return SAM.load(paths.SAM_2023_RICE_PSA if base == "psa" else paths.SAM_2023_RICE)


def psa_growth(year: int) -> tuple[dict, dict]:
    """Nominal growth factors year/2023: by PSA industry (GVA) and for the expenditure aggregates."""
    g = pd.read_csv(paths.DATA_RAW / "macro" / "PSA_OpenSTAT_GVA_by_industry_annual_2000-2025.csv", comment="#")
    g = g[g["valuation"] == "At Current Prices"].pivot_table(index="industry", columns="year", values="value_million_php")
    ind = {k: float(g.loc[k, year] / g.loc[k, BASE]) for k in PSA_INDUSTRIES}
    e = pd.read_csv(paths.DATA_RAW / "macro" / "PSA_OpenSTAT_GDP_by_expenditure_quarterly_2000-2026.csv", comment="#")
    e = e[e["valuation"] == "At Current Prices"]
    tot = lambda name, y: float(e[(e["expenditure"] == name) & (e["year"] == y)]["value_million_php"].sum())
    for name in EXP.values():
        n = e[(e["expenditure"] == name) & (e["year"] == year)].shape[0]
        if n != 4:
            raise ValueError(f"PSA {name} {year}: {n} quarters on file, need 4")
    agg = {k: tot(v, year) / tot(v, BASE) for k, v in EXP.items()}
    return ind, agg


def build(year: int, base: str = "ifpri"):
    s0 = base_sam(base)
    t0 = s0.table
    codes = list(t0.index)
    n = len(codes)
    ix = {c: i for i, c in enumerate(codes)}
    A, C, H = s0.accounts("a"), s0.accounts("c"), s0.accounts("hhd")
    ind_g, agg_g = psa_growth(year)
    ind_of = {a: k for k, acts in PSA_INDUSTRIES.items() for a in acts if a in A}

    # ---- 1. prior: each cell scaled by the growth of the aggregate it belongs to
    F = np.full((n, n), agg_g["gdp"])
    for a in A:                                                   # activity column (costs, value added) and make row
        F[:, ix[a]] = ind_g[ind_of[a]]
        F[ix[a], :] = np.where(np.isin(np.arange(n), [ix[c] for c in C]), ind_g[ind_of[a]], F[ix[a], :])
    for c in C:
        r = ix[c]
        for h in H:
            F[r, ix[h]] = agg_g["hfce"]
        F[r, ix["gov"]] = agg_g["gfce"]
        F[r, ix["s-i"]] = agg_g["gfcf"]
        F[r, ix["row"]] = agg_g["exports"]
        F[ix["row"], r] = agg_g["imports"]
        F[ix["mtax"], r] = agg_g["imports"]
    for a in A:                                                   # home consumption (activity -> household) with HFCE
        for h in H:
            F[ix[a], ix[h]] = agg_g["hfce"]
    X0 = t0.values * F
    nz = np.argwhere(t0.values != 0)
    y0 = np.abs(X0[nz[:, 0], nz[:, 1]])
    sg = np.sign(X0[nz[:, 0], nz[:, 1]])

    # ---- 2. constraints A x = b (x = signed cell values of the nonzero cells)
    rows, b, names = [], [], []
    for k, c in enumerate(codes):                                 # balance: receipts - payments = 0
        r = np.where(nz[:, 0] == k, 1.0, 0.0) - np.where(nz[:, 1] == k, 1.0, 0.0)
        rows.append(r); b.append(0.0); names.append(f"balance {c}")
    fac = [ix[f] for f in FACTORS]
    for k, acts in PSA_INDUSTRIES.items():                         # value added by PSA industry
        cols = [ix[a] for a in acts if a in ix]
        m = np.isin(nz[:, 0], fac) & np.isin(nz[:, 1], cols)
        base = float(t0.values[np.ix_(fac, cols)].sum())
        rows.append(m.astype(float)); b.append(base * ind_g[k]); names.append(f"value added: {k}")
    def ctrl(name, mask_rows, mask_cols, g):
        m = np.isin(nz[:, 0], mask_rows) & np.isin(nz[:, 1], mask_cols)
        base = float(t0.values[np.ix_(mask_rows, mask_cols)].sum())
        rows.append(m.astype(float)); b.append(base * g); names.append(name)
    ci = [ix[c] for c in C]
    ctrl("household consumption (market and home)", ci + [ix[a] for a in A], [ix[h] for h in H], agg_g["hfce"])
    ctrl("government consumption", ci, [ix["gov"]], agg_g["gfce"])
    ctrl("fixed capital formation", ci, [ix["s-i"]], agg_g["gfcf"])
    ctrl("exports", ci, [ix["row"]], agg_g["exports"])
    ctrl("imports", [ix["row"]], ci, agg_g["imports"])
    Am, bv = np.array(rows), np.array(b)

    # ---- 3. cross-entropy: x = sg * y0 * exp(sg * A'lam); Newton on the dual
    lam = np.zeros(len(bv))
    for it in range(100):
        y = y0 * np.exp(np.clip(sg * (Am.T @ lam), -30, 30))
        x = sg * y
        r = Am @ x - bv
        err = float(np.abs(r).max())
        if err < 1e-8:
            break
        J = (Am * y) @ Am.T                                       # A diag(y) A'  (sg^2 = 1)
        step = np.linalg.lstsq(J, -r, rcond=None)[0]
        t_ = 1.0
        while t_ > 1e-4:                                          # backtracking on the residual norm
            y_n = y0 * np.exp(np.clip(sg * (Am.T @ (lam + t_ * step)), -30, 30))
            if np.linalg.norm(Am @ (sg * y_n) - bv) < np.linalg.norm(r):
                break
            t_ /= 2
        lam = lam + t_ * step
    else:
        raise RuntimeError(f"cross-entropy did not converge (largest constraint gap {err:.3g})")
    X = np.zeros((n, n))
    X[nz[:, 0], nz[:, 1]] = x
    S = SAM(pd.DataFrame(X, index=codes, columns=codes), dict(s0.labels),
            f"Infinity GEM SAM {year}: IFPRI 2023 petroleum- and rice-split SAM updated to PSA {year} nominal totals by cross-entropy (tools/update_sam.py)")
    ratio = y / y0
    diag = {"iterations": it, "largest constraint gap": err, "max row-column gap": S.check(verbose=False)["max_row_col_gap"],
            "cells": int(len(y0)), "median cell change vs prior (%)": float((np.median(ratio) - 1) * 100),
            "cells moved more than 5% from the prior": int((np.abs(ratio - 1) > 0.05).sum()),
            "largest move from the prior (%)": float((np.abs(ratio - 1).max()) * 100)}
    ctl = pd.DataFrame({"target": bv[n:], "achieved": (Am @ x)[n:]}, index=names[n:])
    return S, diag, ctl, ind_g, agg_g


def main(year: int, base: str = "ifpri"):
    S, diag, ctl, ind_g, agg_g = build(year, base)
    path = out_path(year, base)
    write_ifpri_csv(S, path)
    with open(path, encoding="utf-8-sig") as f:                     # header names the year (the writer says 2023)
        txt = f.read()
    txt = txt.replace("2023 Social Accounting Matrix for Philippines, petroleum split (Infinity GEM 0.3)",
                      f"{year} Social Accounting Matrix for Philippines, updated from "
                      + ("the PSA-consistent 2023 SAM (Infinity GEM 0.3.9)" if base == "psa"
                         else "IFPRI 2023 petroleum and rice split (Infinity GEM 0.3.8)"), 1)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(txt)
    s0 = base_sam(base)
    gdp = lambda t, C, H: float(t.loc[C, H].values.sum() + t.loc[C, "gov"].sum() + t.loc[C, "s-i"].sum() + t.loc[C, "dstk"].sum()
                                + t.loc[C, "row"].sum() - t.loc["row", C].sum())
    C, H = s0.accounts("c"), s0.accounts("hhd")
    A_ = s0.accounts("a")
    g0 = gdp(s0.table, C, H) + float(s0.table.loc[A_, H].values.sum())
    g1 = gdp(S.table, C, H) + float(S.table.loc[A_, H].values.sum())
    L = [f"# SAM {year}, updated from the IFPRI 2023 SAM (petroleum and rice split) ({dt.datetime.now():%d %B %Y, %H:%M})", "",
         "**NOT YET THE MODEL'S SAM** (Infinity GEM 0.3.8; opt-in). Tool: `tools/update_sam.py`; method: "
         "cross-entropy balancing to PSA nominal totals (Robinson, Cattaneo and El-Said 2001). File: "
         f"`{path.relative_to(ROOT)}`.", "",
         "## Fit", "", "| Item | Value |", "|---|---|"] + [f"| {k} | {v:,.6g} |" for k, v in diag.items()] + [
         "", f"Nominal GDP in the SAM (expenditure side): 2023 {g0:,.1f}; {year} {g1:,.1f} (ratio {g1 / g0:.4f}; PSA nominal GDP "
         f"ratio {agg_g['gdp']:.4f}).", "",
         "## Control totals (SAM units, ₱ bn; 2023 SAM value x PSA nominal growth)", "", ctl.round(3).to_markdown(), "",
         "## PSA nominal growth used", "", pd.Series({**{f"GVA: {k}": v for k, v in ind_g.items()},
                                                     **{f"expenditure: {k}": v for k, v in agg_g.items()}}, name=f"{year}/2023").round(4).to_markdown()]
    rp = paths.OUTPUTS / f"sam_update_{year}{'_psa_base' if base == 'psa' else ''}_{dt.datetime.now():%Y%m%d_%H%M}.md"
    rp.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:20]))
    print("saved", path, "and", rp)
    return S


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    base = "psa" if "--base" in sys.argv and sys.argv[sys.argv.index("--base") + 1] == "psa" else "ifpri"
    for y in ([a for a in args if a != "psa"] or ["2024", "2025"]):
        main(int(y), base)
