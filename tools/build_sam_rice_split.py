"""Split milled rice and corn out of processed food in the 2023 SAM (0.3.7, 15 Oct 2026).

Why: in the IFPRI 2023 SAM, milled rice (and its imports) sits inside 'food processing' (afood / cfood), so in the CGE an
El Nino palay loss cannot be met by more rice imports at the rice price: imported rice is mixed with bread, meat and
canned fish. PSA's 2018 input-output table (240 sectors) has sector 57, 'Rice/corn milling' (household purchases
₱612 bn, imports ₱43 bn in 2018); the rest of food processing is sectors 46-56 and 58-68.

Method: the same rules as tools/build_sam_petroleum_split.py (read its docstring), applied to the petroleum-split
SAM: every cell of the food row and column is split by PSA 2018 shares (buyers' purchases of sector 57 vs the other food
sectors; the miller's cost structure from PSA's sector-57 column; imports, duties, sales taxes and margins in proportion);
every other account keeps exactly its row and column totals and cells. No excise tax applies.
Imports (15 Oct 2026, about 4:30 PM; default imports="psa2023"): the 2018 shares put milled-rice imports at ₱50.3 bn, before
rice tariffication (2019) raised them. They are now PSA's 2023 customs value (data/raw/agri/PSA_OpenSTAT_0032L4DMFD2_...csv:
HS 1006.20-1006.40 milled, husked and broken rice + the corn-milling products 1102.20, 1103.13, 1104.23; seed rice 1006.10
stays in palay, where the SAM already has ₱4.1 bn of imports) at the 2023 mean of BSP's monthly peso-dollar rates (a compiled monthly panel, sheet FX): ₱87.0 bn, moved from other food's imports (the total is unchanged). The SAM's import-tax row on food is
about 100% of its import value (it holds more than tariffs), so a proportional split would give rice ₱88 bn of duty;
instead rice's duty = the Bureau of Customs' certified 2023 rice tariff collections, ₱29.93 bn (a reference copy (not distributed)
Philippine Star, 29 May 2025), the rest stays with other food. imports="io2018" rebuilds the earlier version.
Maize imports (15 Oct 2026, about 5:20 PM; with imports="psa2023"): the IFPRI SAM records NO maize imports, although its
own definitions keep maize (FAO 56) in 'cmaiz' (data paper, Table A2); with none, a maize shortfall cannot be met from abroad,
its price explodes, and because the miller buys palay and maize in fixed proportions, rice milling and palay output collapse
with it (found in the El Nino sizing: maize land at half cut rice output 39%). PSA's 2023 maize grain imports (HS 1005.90,
₱16.0 bn CIF) are placed in 'cmaiz', taken from 'cocer' (other cereals: its only buyer is food processing, which includes
feed milling, the main user of imported yellow corn), with the import duty at 'cocer''s average rate; food processing's
purchases move from 'cocer' to 'cmaiz' by the same amount. ASSUMPTION (IFPRI's booking of maize imports is not documented:
its 'cocer' imports, ₱47.5 bn, match neither PSA's wheat, ₱111.1 bn, nor all non-rice cereals); every other cell unchanged.
New accounts: amric / cmric (milled rice and corn); afood / cfood keep the code but now exclude milling.
Output: data/processed/IFPRI_SAM_PHL_2023_SAM_petroleum_rice_split.csv and outputs/sam_rice_split_<date>.md.
Run:  py tools/build_sam_rice_split.py            (py tools/build_sam_rice_split.py io2018 for the 2018-share version)
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from infinity_gem import paths                                             # noqa: E402
from infinity_gem.sam import SAM                                           # noqa: E402
from build_sam_petroleum_split import load_psa, psa_activity, share, write_ifpri_csv   # noqa: E402

MILL = [57]                                                            # PSA 2018: Rice/corn milling
FOOD = [k for k in range(46, 69) if k not in MILL]                     # the rest of afood (PSA 46-68)
OUT = paths.DATA_PROCESSED / "IFPRI_SAM_PHL_2023_SAM_petroleum_rice_split.csv"
OLD_A, OLD_C, NEW_A, NEW_C = "afood", "cfood", "amric", "cmric"
PSA_IMPORTS = paths.DATA_RAW / "agri" / "PSA_OpenSTAT_0032L4DMFD2_cereals_and_milled_corn_imports_by_country_2023.csv"
MAIZE = ("100590",)      # maize grain other than seed (1005.10, seed, left out)
MILLED = ("100620", "100630", "100640", "110220", "110313", "110423")  # husked, milled, broken rice; maize flour, groats/meal, worked grains
RICE_DUTY_2023 = 29.93   # ₱ bn: Bureau of Customs' certified 2023 rice tariff collections (Philippine Star, 29 May 2025;
                         # a reference copy (not distributed)); 34.5% of rice's CIF value (34.4% of milled rice and corn), i.e. the 35% tariff of 2023


def peso_per_usd_2023() -> float:
    """2023 mean of BSP's monthly average peso-dollar rates, from the quarterly macro panel (sheet FX)."""
    import openpyxl
    ws = openpyxl.load_workbook(paths.MACRO_QUARTERLY, read_only=True, data_only=True)["FX"]
    yr, vals = None, []
    for r in list(ws.iter_rows(values_only=True))[2:]:
        yr = r[0] if r[0] is not None else yr
        if yr == 2023 and isinstance(r[2], (int, float)):
            vals.append(float(r[2]))
    assert len(vals) == 12, vals
    return sum(vals) / 12


def psa_maize_imports_2023() -> float:
    """PSA's 2023 maize grain imports (HS 1005.90, CIF), ₱ bn."""
    import pandas as pd
    d = pd.read_csv(PSA_IMPORTS, comment="#", dtype={"commodity_code": str}, na_values=[".."])
    return float(d.loc[d["commodity_code"].str[:6].isin(MAIZE), "cif_usd_2023"].sum()) * peso_per_usd_2023() / 1e9


def psa_milled_imports_2023() -> dict:
    """PSA's 2023 imports of milled rice and corn (CIF), in US$ and ₱ bn."""
    import pandas as pd
    d = pd.read_csv(PSA_IMPORTS, comment="#", dtype={"commodity_code": str}, na_values=[".."])
    usd = float(d.loc[d["commodity_code"].str[:6].isin(MILLED), "cif_usd_2023"].sum())
    fx = peso_per_usd_2023()
    return {"usd": usd, "fx": fx, "php_bn": usd * fx / 1e9}


def main(imports: str = "psa2023"):
    if imports not in ("psa2023", "io2018"):
        raise ValueError("imports must be 'psa2023' or 'io2018'")
    import openpyxl
    ws = openpyxl.load_workbook(paths.DATA_RAW / "io" / "240-Industry20Table202018.xlsx", read_only=True, data_only=True)["240 TT"]
    rows = list(ws.iter_rows(values_only=True))
    assert "milling" in str(rows[9 + 57][1]).lower(), rows[9 + 57][:3]            # layout check: sector 57 = rice/corn milling
    T, fd, va = load_psa()
    s = SAM.load(paths.SAM_2023_PETR)
    t = s.table.copy()
    A, H = s.accounts("a"), s.accounts("hhd")
    P, C = [k - 1 for k in MILL], [k - 1 for k in FOOD]
    act_of = {k: psa_activity(k) for k in range(1, 241)}
    for k in range(107, 109):
        act_of[k] = "apetr"                                            # the base SAM already has refined petroleum split
    cols_of = {a: [k - 1 for k in range(1, 241) if act_of[k] == a] for a in set(act_of.values())}

    codes = list(t.index)
    new = codes[:codes.index(OLD_A) + 1] + [NEW_A] + codes[codes.index(OLD_A) + 1:codes.index(OLD_C) + 1] \
        + [NEW_C] + codes[codes.index(OLD_C) + 1:]
    t = t.reindex(index=new, columns=new, fill_value=0.0)
    labels = dict(s.labels)
    labels[NEW_A] = "Activities - Milled rice and corn (split from food processing, Infinity GEM 0.3.7)"
    labels[NEW_C] = "Commodities - Milled rice and corn (split from food processing, Infinity GEM 0.3.7)"
    labels[OLD_A] = "Activities - Food processing except rice and corn milling (Infinity GEM 0.3.7)"
    labels[OLD_C] = "Commodities - Food processing except rice and corn milling (Infinity GEM 0.3.7)"
    orig = s.table
    rep = []

    # 1. uses of the commodity (row cfood)
    for a in A:
        x = orig.loc[OLD_C, a]
        if not x or a == OLD_A:
            continue
        j = cols_of.get(a)
        sh = share(T[np.ix_(P, j)].sum(), T[np.ix_(C, j)].sum()) if j else share(T[P, :].sum(), T[C, :].sum())
        t.loc[NEW_C, a], t.loc[OLD_C, a] = x * sh, x * (1 - sh)
        rep.append((f"cfood -> {a}", x, round(sh, 4)))
    fdmap = {**{h: "hfce" for h in H}, "gov": "gfce", "s-i": "gcf", "dstk": "inv", "row": "exp"}
    for c_, key in fdmap.items():
        x = orig.loc[OLD_C, c_]
        if not x:
            continue
        sh = share(fd[key][P].sum(), fd[key][C].sum())
        t.loc[NEW_C, c_], t.loc[OLD_C, c_] = x * sh, x * (1 - sh)
        if c_ == H[0] or c_ in ("gov", "s-i", "dstk", "row"):
            rep.append((f"cfood -> {c_ if c_ not in H else 'households (all groups)'}",
                        x if c_ not in H else float(orig.loc[OLD_C, H].sum()), round(sh, 4)))

    # 2-3. miller technology, supply and output, solved together
    row_of = {}
    for k in range(1, 241):
        row_of.setdefault("c" + act_of[k][1:], []).append(k - 1)
    row_of[NEW_C], row_of[OLD_C] = P, C
    comm_in = [r for r in orig.index if r.startswith("c") and orig.loc[r, OLD_A] >= 1.0 and r != OLD_C and r in row_of] + [NEW_C, OLD_C]
    out_b = T[:, P].sum() + va["COE"][P].sum() + va["GOS"][P].sum()
    coef = {r: T[np.ix_(row_of[r], P)].sum() / out_b for r in comm_in}
    lab = va["COE"][P].sum() / out_b
    cap = va["GOS"][P].sum() / out_b
    scale = 1 / (sum(coef.values()) + lab + cap)
    coef = {r: v * scale for r, v in coef.items()}
    lab, cap = lab * scale, cap * scale
    labs = [f for f in orig.index if f.startswith("flab") and orig.loc[f, OLD_A]]
    labmix = {f: orig.loc[f, OLD_A] / sum(orig.loc[g, OLD_A] for g in labs) for f in labs}
    pc = T[np.ix_(P, C)].sum() / (T[np.ix_(P, C)].sum() + T[np.ix_(C, C)].sum())
    M = float(orig.loc["row", OLD_C]); mt = float(orig.loc["mtax", OLD_C])
    st = float(orig.loc["stax", OLD_C]); tr = float(orig.loc["trc", OLD_C])
    shm = share(fd["imp"][P].sum(), fd["imp"][C].sum())
    if imports == "psa2023":
        psa = psa_milled_imports_2023()
        M_new, mt_new = psa["php_bn"], RICE_DUTY_2023
        rep.append((f"imports at PSA 2023 (US$ {psa['usd'] / 1e6:,.1f} M x ₱{psa['fx']:.3f}); 2018 share was {shm:.4f}", M, round(M_new / M, 4)))
        rep.append(("import duty = BOC rice tariff collections 2023 (₱ bn); share of food duty", mt, round(mt_new / mt, 4)))
    else:
        M_new, mt_new = M * shm, mt * shm
    total_make = float(orig.loc[OLD_A, OLD_C])
    make_p = 0.15 * total_make
    for _ in range(500):
        for r in [r for r in orig.index if r.startswith("c") and orig.loc[r, OLD_A] and r not in comm_in]:
            t.loc[r, OLD_A] = orig.loc[r, OLD_A]
        for r in comm_in:
            if r not in (NEW_C, OLD_C):
                t.loc[r, NEW_A] = coef[r] * make_p
                t.loc[r, OLD_A] = orig.loc[r, OLD_A] - t.loc[r, NEW_A]
        t.loc[NEW_C, NEW_A] = coef[NEW_C] * make_p
        t.loc[OLD_C, NEW_A] = coef[OLD_C] * make_p
        rem = orig.loc[OLD_C, OLD_A] - t.loc[NEW_C, NEW_A] - t.loc[OLD_C, NEW_A]
        t.loc[NEW_C, OLD_A], t.loc[OLD_C, OLD_A] = rem * pc, rem * (1 - pc)
        for f in labs:
            t.loc[f, NEW_A] = lab * make_p * labmix[f]
            t.loc[f, OLD_A] = orig.loc[f, OLD_A] - t.loc[f, NEW_A]
        t.loc["fcap", NEW_A] = cap * make_p
        t.loc["fcap", OLD_A] = orig.loc["fcap", OLD_A] - t.loc["fcap", NEW_A]
        U = {k: float(t.loc[k].sum()) for k in (NEW_C, OLD_C)}
        absorb = {k: U[k] - float(t.loc[k, "row"]) for k in U}
        sha = absorb[NEW_C] / (absorb[NEW_C] + absorb[OLD_C])
        t.loc["row", NEW_C], t.loc["row", OLD_C] = M_new, M - M_new
        t.loc["mtax", NEW_C], t.loc["mtax", OLD_C] = mt_new, mt - mt_new
        t.loc["stax", NEW_C], t.loc["stax", OLD_C] = st * sha, st * (1 - sha)
        t.loc["trc", NEW_C], t.loc["trc", OLD_C] = tr * sha, tr * (1 - sha)
        new_p = U[NEW_C] - float(t.loc[["row", "mtax", "stax", "trc"], NEW_C].sum())
        if abs(new_p - make_p) < 1e-11:
            make_p = new_p
            break
        make_p = new_p
    else:
        raise RuntimeError("Milling output did not converge")
    make = {NEW_C: make_p, OLD_C: total_make - make_p}
    t.loc[NEW_A, NEW_C], t.loc[OLD_A, OLD_C] = make[NEW_C], make[OLD_C]
    neg = {r: round(float(t.loc[r, OLD_A]), 3) for r in t.index if t.loc[r, OLD_A] < -1e-9}
    if neg or min(make.values()) <= 0:
        raise ValueError(f"Negative cells in the food column after the split: {neg}; output {make}")
    rep.append(("imports (2018 PSA share, used only with imports='io2018')", M, round(shm, 4)))
    rep.append(("domestic use (for margins and taxes)", absorb[NEW_C] + absorb[OLD_C], round(sha, 4)))
    rep.append(("miller cost structure (PSA 57, basic prices; renormalised by)", scale, {r: round(v, 4) for r, v in coef.items() if v > 0.002}))
    rep.append(("miller labour / capital shares", lab, round(cap, 4)))

    moved = 0.0
    if imports == "psa2023":                       # maize imports into 'cmaiz', from 'cocer' (see the module notes)
        mz = psa_maize_imports_2023()
        rate = float(orig.loc["mtax", "cocer"] / orig.loc["row", "cocer"])
        moved = mz * (1 + rate)
        t.loc["row", "cmaiz"] += mz
        t.loc["mtax", "cmaiz"] += mz * rate
        t.loc["row", "cocer"] -= mz
        t.loc["mtax", "cocer"] -= mz * rate
        t.loc["cmaiz", OLD_A] += moved
        t.loc["cocer", OLD_A] -= moved
        rep.append((f"maize imports placed in cmaiz (PSA 2023, from cocer; duty at cocer's rate {rate:.4f})", mz, round(mz / float(orig.loc['row', 'cocer']), 4)))
        if min(float(t.loc["row", "cocer"]), float(t.loc["cocer", OLD_A])) < 0:
            raise ValueError("maize imports exceed other cereals' imports or food processing's purchases of them")
    S = SAM(t, labels, f"{paths.SAM_2023_PETR.name} with milled rice and corn split (Infinity GEM 0.3.7; imports {imports})")
    chk = S.check(tol=1e-6, verbose=False)
    keep = [c for c in orig.index if c not in (OLD_A, OLD_C) + (("cmaiz", "cocer") if moved else ())]
    d_rows = float(np.abs(t.loc[keep].sum(axis=1) - orig.loc[keep].sum(axis=1)).max())
    d_cells = float(np.abs(t.loc[keep, keep] - orig.loc[keep, keep]).to_numpy().max())
    if moved:                                      # maize and other cereals change by exactly the moved amount
        d_mz = abs(float(t.loc["cmaiz"].sum() - orig.loc["cmaiz"].sum()) - moved) + abs(float(t.loc["cocer"].sum() - orig.loc["cocer"].sum()) + moved)
        d_rows = max(d_rows, d_mz)
    if not chk["balanced"] or d_rows > 1e-9 or d_cells > 1e-9:
        raise ValueError(f"Split SAM fails checks: balanced={chk['balanced']}, other totals {d_rows:.2e}, cells {d_cells:.2e}")
    write_ifpri_csv(S, OUT if imports == "psa2023" else OUT.with_name(OUT.stem + "_io2018_imports.csv"))
    summary = {"output, milled rice and corn (₱ bn)": make[NEW_C], "output, other processed food (₱ bn)": make[OLD_C],
               "imports, milled rice and corn (₱ bn)": float(t.loc["row", NEW_C]), "imports, other food (₱ bn)": float(t.loc["row", OLD_C]),
               "import duty, milled rice and corn (₱ bn)": float(t.loc["mtax", NEW_C]), "import duty, other food (₱ bn)": float(t.loc["mtax", OLD_C]),
               "imports, maize (₱ bn)": float(t.loc["row", "cmaiz"]), "imports, other cereals (₱ bn)": float(t.loc["row", "cocer"]),
               "household purchases, milled rice and corn (₱ bn)": float(t.loc[NEW_C, H].sum()),
               "miller purchases of palay (₱ bn)": float(t.loc["crice", NEW_A]), "miller purchases of corn (₱ bn)": float(t.loc["cmaiz", NEW_A]),
               "max account imbalance": chk["max_row_col_gap"], "largest change in any other account's total": d_rows}
    return S, summary, rep


if __name__ == "__main__":
    IMPORTS = sys.argv[1] if len(sys.argv) > 1 else "psa2023"
    S, summary, rep = main(IMPORTS)
    lines = [f"# SAM milled rice and corn split, {dt.date.today():%d %b %Y}; imports: {IMPORTS}", "",
             f"File: `{OUT.relative_to(ROOT)}`. Builder: `tools/build_sam_rice_split.py` (rules: `tools/build_sam_petroleum_split.py`).", "",
             "## Summary", "", "| Item | Value |", "|---|---|"]
    lines += [f"| {k} | {v:,.4f} |" if isinstance(v, float) else f"| {k} | {v} |" for k, v in summary.items()]
    lines += ["", "## Cell splits (milled rice and corn share)", "", "| Cell | ₱ bn | Share |", "|---|---|---|"]
    lines += [f"| {a} | {b:,.2f} | {c} |" for a, b, c in rep]
    rp = paths.OUTPUTS / f"sam_rice_split_{dt.date.today():%Y%m%d}{'' if IMPORTS == 'psa2023' else '_io2018'}.md"
    rp.write_text(chr(10).join(lines) + chr(10), encoding="utf-8")
    for k, v in summary.items():
        print(f"{k}: {v:,.4f}" if isinstance(v, float) else f"{k}: {v}")
    print("report:", rp)
