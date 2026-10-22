"""A PSA-consistent variant of the IFPRI 2023 SAM: taxes on products counted once (step 1; 18 Oct 2026).

18 Oct 2026: the question was why the 2023 SAM's household consumption is ₱20.4 tn against PSA's ₱18.6 tn. The IFPRI 2023 SAM (the rice-split SAM that "0.3 recommended" and the 2026 scenarios use) has GDP ₱1,847 bn and household consumption ₱1,799 bn above PSA's. Its value added (₱24,245 bn) is PSA's GDP,
which already contains net taxes on products, and the SAM adds its own product taxes (₱1,916 bn, IMF GFS) on top
(a design note (not included)).

WHERE THE DOUBLE COUNT SITS (tested here, evidence table 1 of the report). IFPRI's data paper (p. 5) sets labour value added
= the I-O labour share x each sector's GDP, with capital the residual. With PSA's 2018 I-O (Table A.1), the SAM's labour
income equals compensation / total primary inputs INCLUDING net taxes x PSA's 2023 industry GDP (₱8,496.7 bn vs ₱8,497.3 bn);
the share without taxes would give ₱9,136.5 bn. So labour income is at the right level and the taxes sit in CAPITAL income.

THE VARIANT (opt-in; IFPRI's file is not changed):
  kept at IFPRI's values (they match PSA, the IMF's GFS or the BOP): labour income by activity and by household group;
  taxes on products (import and sales taxes); government consumption, fixed investment, stock changes, exports and imports by
  commodity; direct taxes; every transfer to and from government and the rest of the world; foreign saving.
  set: household consumption (market and home) = PSA's 2023 HFCE (OpenSTAT 0012B5BEXQ1, four quarters, ₱18,604.5 bn).
  cut: capital and land income of each activity by the net-tax content PSA's own 2018 I-O puts inside that industry's GDP
       (Table B.1, 80 industries: taxes less subsidies / total primary inputs, mapped to the SAM's activities below), scaled
       so the cuts add up to the fall in household consumption (the other expenditure items and the product taxes are kept,
       so value added falls by exactly that much). The I-O's own tax content, applied to the SAM, is within a few per cent
       of the gap: an independent check of the diagnosis (report, table 2).
  held: each activity's total intermediate inputs. IFPRI built output as GDP x PSA's I-O output/GDP ratio, both including
       the taxes, so the intermediate inputs are at PSA's level and the taxes sit in output: output falls with value added.
       (Public administration is not cut: its output is bought by government consumption, kept at PSA's level.)
  everything else (the input mix, the make matrix, trade margins, sales taxes by commodity, the commodity and household mix
  of consumption, enterprise payouts, household and enterprise saving) moves as little as possible:
  deterministic cross-entropy from the IFPRI SAM (Robinson, Cattaneo and El-Said 2001, Economic Systems Research 13(1);
  a reference copy (not distributed)), as tools/update_sam.py does.
Resulting GDP: PSA's HFCE plus the SAM's other expenditure items, ₱48 bn (0.2%) above PSA's GDP; the difference is the
SAM's own small gaps against PSA in government consumption, stock changes, exports and imports (report, table 3).

Data: data/raw/sam (via paths.SAM_2023_RICE), data/raw/io/16-Industry_Table_2018.csv and 80-Industry20Table202018.csv (PSA
2018 I-O, released Dec 2021), data/raw/macro/PSA_OpenSTAT_GVA_by_industry_annual_2000-2025.csv and
PSA_OpenSTAT_GDP_by_expenditure_quarterly_2000-2026.csv.
Outputs: data/processed/InfinityGEM_SAM_PHL_2023_PSA_consistent_from_IFPRI_petroleum_rice_split.csv and
outputs/sam_psa_consistent_2023_<date>.md.
Run:  py tools/build_sam_psa_consistent.py      NOT the default SAM: settings sam_variant="psa" (with rice=True). Check S5.
"""
from __future__ import annotations

import csv
import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from infinity_gem import paths                                          # noqa: E402
from infinity_gem.sam import SAM                                        # noqa: E402
from infinity_gem.dynamic import PSA_INDUSTRIES                          # noqa: E402
from build_sam_petroleum_split import write_ifpri_csv               # noqa: E402

LABOUR = ("flab-n", "flab-p", "flab-s")
NONLAB = ("flnd", "fcap")
# Public administration is not cut: its output is bought by government consumption, which is kept at PSA's level, so a cut
# in its value added could only be offset by more intermediate purchases (a first build did that: +9%), which corrects
# nothing. Its share of the cut goes to the other activities through the scale k.
NO_CUT = ("apadm",)
# SAM activities -> PSA 2018 I-O industries (Table B.1, 80 industries). '20 Support activities to agriculture' (net taxes
# 0.3% of its primary inputs) has no SAM activity of its own and is left out. Vegetables and pulses are in '14 Other
# agricultural crops, n.e.c.', as PSA's list has no line for them.
ACT_IO80 = {"amaiz": ["02"], "arice": ["01"], "apuls": ["14"], "aoils": ["03"], "aroot": ["09"], "avege": ["14"],
            "asugr": ["04"], "atoba": ["13"], "acott": ["12"], "afrui": ["05", "06", "07"], "acoff": ["08", "11"],
            "aocrp": ["10", "14"], "acatt": ["15"], "apoul": ["16"], "aoliv": ["15", "17"], "afore": ["18"], "afish": ["19"],
            "amine": ["21", "22", "23", "24", "25", "26"],
            "afood": ["27"], "amric": ["27"], "abeve": ["28", "29"], "atext": ["30", "31", "32"], "awood": ["33", "34", "35"],
            "achem": ["37", "38", "39"], "apetr": ["36"], "anmet": ["40"], "ametl": ["41", "42"],
            "amach": ["43", "44", "45", "46"], "aoman": ["47", "48"],
            "aelec": ["49", "50"], "awatr": ["51", "52"], "acons": ["53"], "atrad": ["54", "55", "56"],
            "atran": ["57", "58", "59", "60", "61"], "ahotl": ["62", "63"], "acomm": ["64", "65"],
            "afsrv": ["66", "67", "68", "69"], "areal": ["70", "71"], "absrv": ["72"], "apadm": ["73"], "aeduc": ["74", "75"],
            "aheal": ["76", "77", "78"], "aosrv": ["79", "80"]}


def out_path() -> Path:
    return paths.SAM_2023_RICE_PSA


def _io_rows(path: Path, n: int) -> tuple[list, pd.DataFrame]:
    """PSA I-O transaction table (CSV export): industry codes and the primary-input rows COE, GOS, T-S, TPI (₱ bn)."""
    rows = list(csv.reader(open(path, encoding="utf-8-sig")))
    head = next(r for r in rows if len(r) > 3 and r[0] == "" and r[2].strip() == "01")
    codes = [c.strip() for c in head[2:2 + n]]
    get = {r[0]: r for r in rows if r and r[0] in ("COE", "GOS", "T-S", "TPI")}
    return codes, pd.DataFrame({k: [float(x) / 1000 for x in get[k][2:2 + n]] for k in ("COE", "GOS", "T-S", "TPI")}, index=codes)


def psa_2023() -> dict:
    """PSA 2023 GDP by expenditure, current prices, ₱ bn (four quarters summed), and GVA by industry."""
    e = pd.read_csv(paths.DATA_RAW / "macro" / "PSA_OpenSTAT_GDP_by_expenditure_quarterly_2000-2026.csv", comment="#")
    e = e[(e["valuation"] == "At Current Prices") & (e["year"] == 2023)]
    out = {}
    for k, name in {"hfce": "Household final consumption expenditure", "gfce": "Government final consumption expenditure",
                    "gcf": "Gross capital formation", "gfcf": "Gross fixed capital formation",
                    "exports": "Exports of goods and services", "imports": "Imports of goods and services",
                    "discrepancy": "Statistical discrepancy", "gdp": "Gross Domestic Product"}.items():
        x = e[e["expenditure"] == name]
        if len(x) != 4:
            raise ValueError(f"PSA 2023 {name}: {len(x)} quarters on file, need 4")
        out[k] = float(x["value_million_php"].sum()) / 1000
    g = pd.read_csv(paths.DATA_RAW / "macro" / "PSA_OpenSTAT_GVA_by_industry_annual_2000-2025.csv", comment="#")
    g = g[g["valuation"] == "At Current Prices"].pivot_table(index="industry", columns="year", values="value_million_php")
    out["gva"] = (g.loc[list(PSA_INDUSTRIES), 2023] / 1000).to_dict()
    return out


def labour_share_test(t0: pd.DataFrame, gva: dict) -> pd.DataFrame:
    """Evidence table 1: the SAM's labour income by PSA industry against PSA's 2018 I-O labour share x PSA 2023 GVA, with the
    share taken over total primary inputs including net taxes ('incl.') or over compensation + operating surplus ('excl.')."""
    _, io = _io_rows(paths.DATA_RAW / "io" / "16-Industry_Table_2018.csv", 16)
    io.index = list(PSA_INDUSTRIES)
    rows = {}
    for k, acts in PSA_INDUSTRIES.items():
        a = [x for x in acts if x in t0.columns]
        lab = float(t0.loc[list(LABOUR), a].values.sum())
        rows[k] = {"PSA GVA 2023": gva[k], "SAM labour income": lab,
                   "I-O share incl. taxes x GVA": io.loc[k, "COE"] / io.loc[k, "TPI"] * gva[k],
                   "I-O share excl. taxes x GVA": io.loc[k, "COE"] / (io.loc[k, "COE"] + io.loc[k, "GOS"]) * gva[k]}
    d = pd.DataFrame(rows).T
    d.loc["Total"] = d.sum()
    return d


def tax_content(t0: pd.DataFrame, acts: list) -> pd.DataFrame:
    """Evidence table 2: net taxes on production and imports as a share of total primary inputs, PSA 2018 I-O (80 industries),
    mapped to the SAM's activities, and that share x the SAM's value added."""
    _, io = _io_rows(paths.DATA_RAW / "io" / "80-Industry20Table202018.csv", 80)
    d = pd.DataFrame(index=acts)
    d["I-O industries"] = [", ".join(ACT_IO80[a]) for a in acts]
    d["net-tax share of primary inputs"] = [io.loc[ACT_IO80[a], "T-S"].sum() / io.loc[ACT_IO80[a], "TPI"].sum() for a in acts]
    d["SAM value added"] = [float(t0.loc[list(LABOUR + NONLAB), a].sum()) for a in acts]
    d["SAM capital and land income"] = [float(t0.loc[list(NONLAB), a].sum()) for a in acts]
    d["tax content"] = d["net-tax share of primary inputs"] * d["SAM value added"]
    return d


def cross_entropy(t0: np.ndarray, fixed: np.ndarray, controls: list, tol: float = 1e-7, it_max: int = 200):
    """Deterministic cross-entropy balancing (Robinson, Cattaneo and El-Said 2001) with fixed cells.
    t0: prior SAM (n x n). fixed: boolean n x n, cells kept at t0. controls: [(name, n x n mask, target)]; the mask is boolean or, since 18 Oct 2026 (own SAM v0.3), cell weights.
    Minimises sum |x| ln(|x|/|x0|) - |x| + |x0| over the free non-zero cells, subject to every account balancing and the
    controls; zero cells stay zero and signs are kept. Solution x = x0 exp(A'lambda) (signs kept); Newton on the dual,
    with backtracking, as tools/update_sam.py. tol is in ₱ bn (1e-7 = ₱100, about 1e-12 of the SAM's totals: rounding level)."""
    n = len(t0)
    free = (t0 != 0) & ~fixed
    nz = np.argwhere(free)
    y0 = np.abs(t0[nz[:, 0], nz[:, 1]])
    sg = np.sign(t0[nz[:, 0], nz[:, 1]])
    tf = np.where(fixed, t0, 0.0)
    rows, b, names = [], [], []
    for k in range(n):                                            # receipts - payments = 0, fixed cells on the right
        rows.append(np.where(nz[:, 0] == k, 1.0, 0.0) - np.where(nz[:, 1] == k, 1.0, 0.0))
        b.append(-(tf[k, :].sum() - tf[:, k].sum()))
        names.append(f"balance {k}")
    for name, mask, target in controls:
        if ((mask != 0) & fixed & (t0 != 0)).any():                # mask: boolean, or weights (own SAM v0.3)
            raise ValueError(f"control '{name}' covers fixed cells")
        rows.append(mask[nz[:, 0], nz[:, 1]].astype(float)); b.append(target); names.append(name)
    Am, bv = np.array(rows), np.array(b)
    lam = np.zeros(len(bv))
    for it in range(it_max):
        y = y0 * np.exp(np.clip(sg * (Am.T @ lam), -30, 30))
        x = sg * y
        r = Am @ x - bv
        err = float(np.abs(r).max())
        if err < tol:
            break
        J = (Am * y) @ Am.T
        step = np.linalg.lstsq(J, -r, rcond=None)[0]
        s = 1.0
        while s > 1e-6:
            y_n = y0 * np.exp(np.clip(sg * (Am.T @ (lam + s * step)), -30, 30))
            if np.linalg.norm(Am @ (sg * y_n) - bv) < np.linalg.norm(r):
                break
            s /= 2
        lam = lam + s * step
    else:
        raise RuntimeError(f"cross-entropy did not converge (largest constraint gap {err:.3g})")
    X = tf.copy()
    X[nz[:, 0], nz[:, 1]] = x
    ratio = y / y0
    diag = {"iterations": it, "largest constraint gap": err, "free cells": int(len(y0)), "fixed cells": int((fixed & (t0 != 0)).sum()),
            "median free-cell change (%)": float((np.median(ratio) - 1) * 100),
            "free cells moved more than 5%": int((np.abs(ratio - 1) > 0.05).sum()),
            "free cells moved more than 20%": int((np.abs(ratio - 1) > 0.20).sum()),
            "largest move (%)": float(np.abs(ratio - 1).max() * 100)}
    ctl = pd.DataFrame({"target": bv[n:], "achieved": (Am @ x)[n:]}, index=names[n:])
    return X, diag, ctl


def expenditure(t: pd.DataFrame, s: SAM) -> dict:
    C, H, A = s.accounts("c"), s.accounts("hhd"), s.accounts("a")
    d = {"household consumption": float(t.loc[C, H].values.sum() + t.loc[A, H].values.sum()),
         "government consumption": float(t.loc[C, "gov"].sum()), "fixed investment": float(t.loc[C, "s-i"].sum()),
         "stock change": float(t.loc[C, "dstk"].sum()), "exports": float(t.loc[C, "row"].sum()),
         "imports": float(t.loc["row", C].sum())}
    d["GDP (expenditure)"] = d["household consumption"] + d["government consumption"] + d["fixed investment"] + \
        d["stock change"] + d["exports"] - d["imports"]
    d["value added"] = float(t.loc[list(LABOUR + NONLAB), A].values.sum())
    d["taxes on products"] = float(t.loc[["mtax", "stax"], C].values.sum())
    d["GDP (income)"] = d["value added"] + d["taxes on products"] + float(t.loc[[c for c in ("atax",) if c in t.index], A].values.sum())
    return d


def build(exclude: tuple = NO_CUT, ic_totals: bool = True):
    """exclude: activities whose value added is not cut. ic_totals: also hold each activity's intermediate inputs at IFPRI's."""
    s0 = SAM.load(paths.SAM_2023_RICE)
    t0 = s0.table
    codes = list(t0.index)
    ix = {c: i for i, c in enumerate(codes)}
    n = len(codes)
    A, C, H = s0.accounts("a"), s0.accounts("c"), s0.accounts("hhd")
    psa = psa_2023()
    e0 = expenditure(t0, s0)

    # ---- targets: household consumption = PSA; value added falls by the same amount, as capital and land income
    cut_total = e0["household consumption"] - psa["hfce"]
    tc = tax_content(t0, A)
    tc.loc[list(exclude), "tax content"] = 0.0
    k = cut_total / tc["tax content"].sum()
    tc["cut"] = k * tc["tax content"]
    tc["capital and land income after"] = tc["SAM capital and land income"] - tc["cut"]
    if (tc["capital and land income after"] <= 0.5 * tc["SAM capital and land income"]).any():
        raise ValueError("a cut takes more than half of an activity's capital income: check the mapping")

    # ---- fixed cells: everything IFPRI took from PSA, the GFS or the BOP and that matches them
    I = lambda names: [ix[c] for c in names if c in ix]
    fixed = np.zeros((n, n), dtype=bool)
    def fix(r, c):
        fixed[np.ix_(I(r), I(c))] = True
    fix(LABOUR, A)                                    # labour income by activity (evidence table 1)
    fix(H, LABOUR)                                    # ... and by household group (LFS/FIES)
    fix(["mtax"], C); fix(["row"], C); fix(C, ["row"])  # import taxes, imports, exports by commodity
    fix(C, ["gov", "s-i", "dstk"]); fix(["dstk"], ["s-i"])
    fix(["dtax"], ["ent"] + H); fix(["gov"], ["ent", "dtax", "ftax", "mtax", "stax", "row"] + H)
    fix(["ent", "row"] + H, ["gov"]); fix(["s-i"], ["gov", "row"])
    fix(["row"], list(LABOUR + NONLAB) + ["ent", "gov"] + H); fix(list(LABOUR + NONLAB) + ["ent"] + H, ["row"])
    fix(["ftax"], ["fcap"])

    # ---- controls
    mask = lambda r, c: (lambda m: (m.__setitem__(np.ix_(I(r), I(c)), True), m)[1])(np.zeros((n, n), dtype=bool))
    controls = [("household consumption (market and home) = PSA 2023 HFCE", mask(C + A, H), psa["hfce"])]
    for a in A:
        controls.append((f"capital and land income: {a}", mask(list(NONLAB), [a]), float(tc.loc[a, "capital and land income after"])))
    if ic_totals:
        for a in A:
            controls.append((f"intermediate inputs: {a}", mask(C, [a]), float(t0.loc[C, a].sum())))
    X, diag, ctl = cross_entropy(t0.values.astype(float), fixed, controls)
    S = SAM(pd.DataFrame(X, index=codes, columns=codes), dict(s0.labels),
            "Infinity GEM SAM 2023, PSA-consistent: IFPRI's petroleum- and rice-split 2023 SAM with taxes on products counted once "
            "(tools/build_sam_psa_consistent.py)")
    diag["max row-column gap"] = S.check(verbose=False)["max_row_col_gap"]
    diag["scale on the I-O tax content (k)"] = k
    lab = labour_share_test(t0, psa["gva"])
    return S, s0, diag, ctl, tc, lab, psa


def choices(S, s0, diag) -> pd.DataFrame:
    """The balancing choices compared (report section 5): cut every activity with free intermediate inputs; exclude public
    administration; and that plus intermediate totals held (this tool's SAM)."""
    A, C, H = s0.accounts("a"), s0.accounts("c"), s0.accounts("hhd")
    a = s0.table
    def row(b, d):
        icp = (b.loc[C, A].sum() / a.loc[C, A].sum() - 1) * 100
        hh = households(b, s0)
        return {"scale k": d["scale on the I-O tax content (k)"], "free cells moved more than 20%": d["free cells moved more than 20%"],
                "largest move (%)": d["largest move (%)"], "median free-cell change (%)": d["median free-cell change (%)"],
                "largest change in an activity's intermediate inputs (%)": float(icp.abs().max()),
                "trade: intermediate inputs (%)": float(icp["atrad"]), "public administration: intermediate inputs (%)": float(icp["apadm"]),
                "household saving (₱ bn)": float(b.loc["s-i", H].sum()), "enterprise saving (₱ bn)": float(b.loc["s-i", "ent"]),
                "saving rate, rural bottom fifth (%)": float(hh.loc["hhd-r1", "saving rate (%)"]),
                "saving rate, urban top fifth (%)": float(hh.loc["hhd-u5", "saving rate (%)"])}
    out = {}
    for name, kw in {"cut every activity; inputs free": dict(exclude=(), ic_totals=False),
                     "public administration not cut; inputs free": dict(exclude=NO_CUT, ic_totals=False)}.items():
        S_, _, d, *_ = build(**kw)
        out[name] = row(S_.table, d)
    out["public administration not cut; intermediate totals held (THIS SAM)"] = row(S.table, diag)
    return pd.DataFrame(out)


def households(t: pd.DataFrame, s: SAM) -> pd.DataFrame:
    H, C, A = s.accounts("hhd"), s.accounts("c"), s.accounts("a")
    inc = t.loc[H].sum(axis=1)
    cap = t.loc[H, ["fcap", "flnd", "ent"]].sum(axis=1)
    cons = t.loc[C, H].sum() + t.loc[A, H].sum()
    return pd.DataFrame({"income": inc, "capital share of income (%)": cap / inc * 100, "consumption": cons,
                         "consumption share (%)": cons / cons.sum() * 100, "saving rate (%)": t.loc["s-i", H] / inc * 100})


def main():
    S, s0, diag, ctl, tc, lab, psa = build()
    alt = choices(S, s0, diag)
    path = out_path()
    write_ifpri_csv(S, path)
    with open(path, encoding="utf-8-sig") as f:
        txt = f.read()
    txt = txt.replace("2023 Social Accounting Matrix for Philippines, petroleum split (Infinity GEM 0.3)",
                      "2023 Social Accounting Matrix for Philippines, PSA-consistent variant of IFPRI petroleum and rice split "
                      "(taxes on products counted once; Infinity GEM 0.3.9)", 1)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(txt)
    S1 = SAM.load(path)                                            # what the model will read
    e0, e1 = expenditure(s0.table, s0), expenditure(S1.table, S1)
    macro = pd.DataFrame({"IFPRI 2023 SAM": e0, "PSA-consistent variant": e1})
    macro["PSA 2023"] = [psa["hfce"], psa["gfce"], psa["gfcf"], psa["gcf"] - psa["gfcf"], psa["exports"], psa["imports"],
                         psa["gdp"], np.nan, np.nan, psa["gdp"]]
    macro["variant minus PSA"] = macro["PSA-consistent variant"] - macro["PSA 2023"]
    fac = pd.DataFrame({"IFPRI": s0.table.loc[list(LABOUR + NONLAB), s0.accounts("a")].sum(axis=1),
                        "variant": S1.table.loc[list(LABOUR + NONLAB), S1.accounts("a")].sum(axis=1)})
    inst = pd.DataFrame({"IFPRI": [s0.v("s-i", "ent"), float(s0.table.loc["s-i", s0.accounts("hhd")].sum()),
                                   float(s0.table.loc[s0.accounts("hhd"), "ent"].sum())],
                         "variant": [S1.v("s-i", "ent"), float(S1.table.loc["s-i", S1.accounts("hhd")].sum()),
                                     float(S1.table.loc[S1.accounts("hhd"), "ent"].sum())]},
                        index=["enterprise saving", "household saving", "enterprise payouts to households"])
    hh = pd.concat({"IFPRI": households(s0.table, s0), "variant": households(S1.table, S1)}, axis=1)
    stamp = dt.datetime.now()
    L = [f"# PSA-consistent 2023 SAM: taxes on products counted once ({stamp:%d %B %Y, %H:%M})", "",
         "**NOT YET THE MODEL'S SAM** (Infinity GEM 0.3.9, step 1; opt-in: settings `sam_variant=\"psa\"` with "
         f"`rice=True`). Tool: `tools/build_sam_psa_consistent.py`. File: `{path.relative_to(ROOT)}`. IFPRI's SAM is unchanged. "
         "Diagnosis: a design note (not included).", "",
         "## 1. Where the double count sits: labour income is right, capital income is not", "",
         "IFPRI's data paper (p. 5): labour value added = the I-O labour share x each sector's GDP; capital is the residual. "
         "The SAM's labour income matches PSA's 2018 I-O compensation share **including** net taxes x PSA 2023 GVA, not the "
         "share without taxes; so the taxes inside PSA's industry GDP ended up in capital income (₱ bn):", "",
         lab.round(1).to_markdown(), "",
         "## 2. The cut: PSA's own I-O tax content of each industry's GDP", "",
         f"Household consumption falls to PSA's ₱{psa['hfce']:,.1f} bn, so value added falls by the same "
         f"₱{tc['cut'].sum():,.1f} bn (taxes on products and the other expenditure items are kept). It is taken from capital "
         "and land income, activity by activity, in proportion to the net-tax content PSA's 2018 I-O (Table B.1) puts inside "
         f"that industry's GDP. The I-O's tax content applied to the SAM adds up to ₱{tc['tax content'].sum():,.1f} bn, so the "
         f"scale k = {diag['scale on the I-O tax content (k)']:.4f}: the I-O, an independent source, puts almost exactly the "
         "gap inside PSA's industry GDP. (₱ bn)", "",
         tc.round(4).to_markdown(), "",
         "## 3. Macro totals against PSA (₱ bn, current prices)", "",
         macro.round(1).to_markdown(), "",
         "GDP is ₱{:,.1f} bn above PSA's: the SAM's own small gaps against PSA in government consumption, stock changes, "
         "exports and imports, which IFPRI took from other sources and this variant keeps (the forward-looking model's foreign-saving bridge handles the external "
         "accounts).".format(e1["GDP (expenditure)"] - psa["gdp"]), "",
         "## 4. Factor incomes, saving and the household groups", "",
         fac.round(1).to_markdown(), "", inst.round(1).to_markdown(), "", hh.round(1).to_markdown(), "",
         "## 5. Balancing (cross-entropy from the IFPRI SAM)", "",
         "Three choices were built; the third is this file. Holding each activity's intermediate inputs keeps the technology "
         "IFPRI took from PSA's I-O and moves the SAM least cell by cell; the household and institution blocks are the same "
         "in all three.", "", alt.round(3).to_markdown(), "", "| Item | Value |", "|---|---|"] + \
        [f"| {k} | {v:,.6g} |" for k, v in diag.items()] + ["", "Controls:", "", ctl.round(6).to_markdown(), "",
         "## 6. What it is and is not", "",
         "- A correction of one identified error, with everything else kept as IFPRI built it; the household groups' "
         "income sources and consumption still follow IFPRI's construction (Infinity GEM's own SAM, rebuilds them from "
         "FIES and the LFS).",
         "- Opt-in. The default and every published result still use IFPRI's SAM (check R0). Check S5 rebuilds this file "
         "and tests that the CGE reproduces it."]
    rp = paths.output_dir() / f"sam_psa_consistent_2023_{stamp:%Y%m%d_%H%M}.md"
    rp.write_text("\n".join(L), encoding="utf-8")
    print(macro.round(1).to_string())
    print(pd.Series(diag).to_string())
    print("saved", path, "and", rp)
    return S1


if __name__ == "__main__":
    main()
