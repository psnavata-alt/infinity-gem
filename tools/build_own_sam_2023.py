"""Infinity GEM's own 2023 SAM, version 0.3: Philippine data as controls, IFPRI's structure only as the prior (18 Oct 2026).

18 Oct 2026: a SAM built from Philippine sources, with IFPRI's structure only as the prior. Design and the
block-by-block source table: a design note (not included). Same 112 accounts as the rice-split SAM, so
Infinity GEM runs it unchanged; households grouped as the poverty microsimulation groups FIES families (urban/rural x national
per-capita income quintile, infinity_gem/household.py).

Prior: the PSA-consistent SAM (IFPRI's rice-split SAM with taxes on products counted once). Controls (exact):
  PSA 2023 national accounts (OpenSTAT 0012B5BEXQ1, four quarters): household consumption, government consumption, fixed
     investment, stock change (gross capital formation minus fixed), exports, imports;
  value added at basic prices by PSA's 16 industries: PSA GVA 2023 (0052B5BPRA1) minus the net taxes PSA's 2018 I-O (Table
     A.1) puts inside each industry, scaled to the SAM's taxes on products (public administration not cut);
  labour income by PSA industry: the 2018 I-O's compensation / total primary inputs x PSA GVA 2023 (IFPRI's own method,
     data paper p. 5, with PSA's industry values);
  FIES 2023 (public-use file, RFACT weights), families grouped as in the microsimulation: each group's share of household
     consumption (TOTEX), of wages and salaries (WAGES) and of cash transfers from abroad (CASH_ABROAD).
Version 0.2 (18 Oct 2026, about 1:40 AM) adds:
  taxes (DBM BESF 2025, Table C.3, 2023 actuals; data/raw/fiscal/): customs duties and fees are the tax on imports (mtax);
     VAT (domestic and on imports), excises (domestic and on imports), percentage taxes on services, the documentary stamp tax
     and franchise taxes are taxes on the product, domestic or imported (stax), as in the SNA; income taxes are direct taxes
     (corporate to enterprises, individual and property transfer to households, 'others' half and half). IFPRI's SAM put VAT
     on imports into the import tax (its ₱1,268 bn exceeds all BOC collections, ₱883 bn).
  labour by skill (Infinity GEM's three education groups, infinity_gem.dynamic.LABOUR_EDUCATION) from PSA's FIES-LFS 2023 member file
     (licensed by PSA to each user; only these aggregates are used): wage-and-salary earnings (basic daily pay x days worked last week,
     member weights) by PSA industry and skill, and by household group and skill; the household matrix is balanced (RAS) to
     FIES wages by group and to the industry side's skill totals.
Version 0.3 (18 Oct 2026, about 3:15 AM; design note §8) adds:
  household consumption by purpose = PSA's 2023 HFCE by purpose (OpenSTAT 0142B5BHFA1, 12 COICOP divisions, current prices),
     through a commodity-to-division bridge (COICOP_BRIDGE: shares from PSA's 2018 CPI weights where a commodity spans
     divisions; tested on 2018, where PSA publishes both the I-O household column and HFCE by purpose). Within each division
     the commodities keep the prior's proportions as far as the other controls allow. Why: the I-O's household column has
     PSA's own unusual product detail (₱1.6 tn of 'bakery products', ₱0.5 tn of public administration in 2018), and v0.2's
     housing division was about ₱0.75 tn below PSA's.
Version 0.4 (18 Oct 2026, about 12:45 PM; design note §10; OPT-IN candidate, v0.3 stays the 'own' variant) adds:
  labour income of professional and business services and of finance spread in proportion to the basic pay their employees
     report in the FIES-LFS 2023 (tools/services_labour_allocation_check.py), within the two industries' combined PSA-based
     total; capital takes up the difference, so each industry's value added is unchanged. Why: the 2018 labour share applied
     to 2023 GVA puts finance's labour income at 5.4 times LFS basic pay (economy 1.9) and business services' at 1.4; finance's
     GVA grew mostly through output per worker after 2018, business services' through employment (PIDS DP 2025-46, Table 1).
     Public administration is left at PSA's value (budget-based compensation; uniformed personnel's allowances are not basic
     pay).
Version 0.5 (18 Oct 2026, about 3 PM; design note §11; builds on v0.4) adds:
  domestic refining (apetr) grown from PSA's 2018 I-O by PSA's own GVA of 'coke and refined petroleum products' (2023/2018 =
     136,167/207,370 = 0.657; OpenSTAT 0462B5BMFA1, saved 18 Oct) instead of all manufacturing's growth, with its value added
     held at that level (a control), so imports supply the rest of refined fuel. Why: Shell's Tabangao refinery stopped
     refining in 2020; growing 2018's refining with manufacturing put domestic output at 45% of fuel's purchaser value (v0.4),
     and the 2026 fuel-product price shock then passed through too little (fuel +34% vs +43% on IFPRI's SAM;
     outputs/own_sam_cpi_decomposition_20261018_1244.md).
Kept from the prior (to replace later, design note §4): government transfers, the rest-of-world income flows (BOP-based),
the activity mix within each PSA industry, intermediate inputs, land and trade margins. Everything not controlled moves as
little as possible (deterministic cross-entropy; tools/build_sam_psa_consistent.cross_entropy).
Outputs: data/processed/InfinityGEM_SAM_PHL_2023_own_v<version>.csv and outputs/own_sam_2023_v<version>_<date>.md (earlier versions'
files kept). build(version) rebuilds any version: '0.2' leaves out the controls by purpose.
Run:  py tools/build_own_sam_2023.py [version]     NOT the default SAM: settings sam_variant="own" (with rice=True). Check S6.
"""
from __future__ import annotations

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
import build_sam_psa_consistent as P                                # noqa: E402

VERSION = "0.5"   # the version in use (paths.SAM_2023_OWN; check S6); 18 Oct 2026, 0.3.10: Infinity GEM's default 2023 SAM for rice=True runs
# Version 0.3: SAM commodity -> PSA's COICOP divisions of household consumption (the names of OpenSTAT 0142B5BHFA1).
# Shares sum to one. Where a commodity spans divisions, PSA's 2018 CPI weights (all households) give the split: beverages and
# tobacco 01.2 vs 02; chemicals 06.1 medicines, 13.1 personal care, 05.6 household cleaning goods; refined petroleum
# 04.5.2-04.5.3 LPG and kerosene vs 07.2.2 vehicle fuel; machinery 07.1+07.2.1 vehicles and parts, 05.3 appliances, 08.1 ICT
# equipment; information and communication 08.3 vs 09.6-09.7; other manufactures 09.2 vs 13.2; other services 09.4-09.8,
# 13.1 services, 05.6 domestic services. Public administration bought by households (PSA's own SUT records it) goes to
# miscellaneous services (COICOP 12.7). Trade is not bought by households in the SAM (margins sit in commodity prices).
COICOP = ["Food and non-alcoholic beverages", "Alcoholic beverages, tobacco", "Clothing and footwear",
          "Housing, water, electricity, gas and other fuels",
          "Furnishings, household equipment and routine household maintenance", "Health", "Transport", "Communication",
          "Recreation and culture", "Education", "Restaurants and hotels", "Miscellaneous goods and services"]
_FD, _AT, _CL, _HO, _FU, _HE, _TR, _CO, _RE, _ED, _RH, _MI = COICOP
COICOP_BRIDGE = {
    **{c: {_FD: 1.0} for c in ("crice", "cmaiz", "cocer", "cpuls", "coils", "croot", "cvege", "csugr", "cfrui", "ccoff",
                               "cocrp", "ccatt", "cpoul", "coliv", "cfish", "cfood", "cmric")},
    "ctoba": {_AT: 1.0}, "cbeve": {_FD: 0.58, _AT: 0.42}, "ccott": {_CL: 1.0}, "ctext": {_CL: 0.97, _FU: 0.03},
    "cfore": {_HO: 1.0}, "cwood": {_FU: 1.0}, "cchem": {_HE: 0.27, _MI: 0.58, _FU: 0.15}, "cpetr": {_HO: 0.36, _TR: 0.64},
    "cnmet": {_HO: 1.0}, "cmetl": {_HO: 1.0}, "cmine": {_HO: 1.0}, "cmach": {_TR: 0.52, _FU: 0.17, _CO: 0.31},
    "coman": {_RE: 0.23, _MI: 0.77}, "celec": {_HO: 1.0}, "cwatr": {_HO: 1.0}, "creal": {_HO: 1.0}, "ccons": {_HO: 1.0},
    "ctrad": {_MI: 1.0}, "ctran": {_TR: 1.0}, "chotl": {_RH: 1.0}, "ccomm": {_CO: 0.83, _RE: 0.17}, "cfsrv": {_MI: 1.0},
    "cbsrv": {_MI: 1.0}, "cpadm": {_MI: 1.0}, "ceduc": {_ED: 1.0}, "cheal": {_HE: 1.0},
    "cosrv": {_RE: 0.30, _MI: 0.40, _FU: 0.30},
}


def hfce_by_purpose_2023() -> pd.Series:
    """PSA's 2023 household final consumption by purpose (₱ bn, current prices; OpenSTAT 0142B5BHFA1, saved 18 Oct 2026)."""
    p = pd.read_csv(paths.DATA_RAW / "macro" / "PSA_OpenSTAT_0142B5BHFA1_HFCE_by_purpose_annual_2000-2025.csv", comment="#")
    p = p[(p["valuation"] == "At Current Prices") & (p["year"] == 2023)].set_index("purpose")["value_php_million"] / 1e3
    return p.reindex(COICOP)


def by_purpose(t: pd.DataFrame, s: SAM) -> pd.Series:
    """Household consumption of a SAM by COICOP division through COICOP_BRIDGE (market purchases + home consumption, ₱ bn)."""
    H = s.accounts("hhd")
    out = pd.Series(0.0, index=COICOP)
    for c, sh in COICOP_BRIDGE.items():
        v = sum(float(t.loc[k, H].sum()) for k in (c, "a" + c[1:]) if k in t.index)
        for d, w in sh.items():
            out[d] += v * w
    return out
# fuel excise 2023 (BIR + BOC, ₱ bn): as tools/build_sam_petroleum_split.FUEL_EXCISE_2023 (CPBRD FF2025-42, attributed, to
# verify); BIR's own fuel excise is ₱7 m (BESF), so this is collected by BOC on imported fuel
from build_sam_petroleum_split import FUEL_EXCISE_2023                  # noqa: E402
AGRI_FISH = ("cmaiz", "crice", "cocer", "cpuls", "coils", "croot", "cvege", "csugr", "ctoba", "ccott", "cfrui", "ccoff", "cocrp",
             "ccatt", "cpoul", "coliv", "cfore", "cfish")
# VAT base weights: exempt = agricultural and marine food products in their original state (incl. milled rice), education,
# health, financial services (percentage taxes instead) and government services (NIRC Sec. 109); half for real estate
# (residential rent exempt below a threshold) and transport (land passenger carriers pay a percentage tax instead)
VAT_WEIGHT = {**{c: 0.0 for c in AGRI_FISH + ("cmric", "ceduc", "cheal", "cfsrv", "cpadm")}, "creal": 0.5, "ctran": 0.5}
PUBLIC_ADMIN = "Public administration and defense; compulsory social activities"


def fies_groups() -> pd.DataFrame:
    """FIES 2023 totals by SAM household group (RFACT-weighted, ₱), grouped as infinity_gem/household.py does."""
    f = pd.read_csv(paths.FIES_PUF, usecols=["TOINC", "TOTEX", "WAGES", "CASH_ABROAD", "RFACT", "URB", "NPCINC"])
    f["grp"] = np.where(f["URB"] == 1, "hhd-u", "hhd-r") + np.ceil(f["NPCINC"] / 2).astype(int).astype(str)
    w = f["RFACT"]
    return pd.DataFrame({k: (f[k] * w).groupby(f["grp"]).sum() for k in ("TOTEX", "WAGES", "CASH_ABROAD", "TOINC")})


def industry_targets(psa: dict, product_taxes: float) -> pd.DataFrame:
    """Value added at basic prices and labour income by PSA industry (₱ bn)."""
    _, io = P._io_rows(paths.DATA_RAW / "io" / "16-Industry_Table_2018.csv", 16)
    io.index = list(PSA_INDUSTRIES)
    d = pd.DataFrame({"PSA GVA 2023": pd.Series(psa["gva"])})
    d["net-tax share (I-O 2018)"] = io["T-S"] / io["TPI"]
    d["labour share (I-O 2018, of primary inputs)"] = io["COE"] / io["TPI"]
    content = d["net-tax share (I-O 2018)"] * d["PSA GVA 2023"]
    content[PUBLIC_ADMIN] = 0.0
    d["taxes on products inside GVA"] = content * product_taxes / content.sum()
    d["value added at basic prices"] = d["PSA GVA 2023"] - d["taxes on products inside GVA"]
    d["labour income"] = d["labour share (I-O 2018, of primary inputs)"] * d["PSA GVA 2023"]
    d["capital and land income"] = d["value added at basic prices"] - d["labour income"]
    return d


LFS_SPLIT = ("Professional and business services", "Financial and insurance activities")


def lfs_split(ind: pd.DataFrame) -> pd.DataFrame:
    """Version 0.4: labour income of LFS_SPLIT in proportion to FIES-LFS 2023 employees' basic pay, within their combined
    total; capital and land income = value added at basic prices less labour (value added unchanged)."""
    import mixed_income_diagnostic as MI                         # FIES-LFS member file (licensed; aggregates only)
    m = MI.lfs_workers()
    we = m[m["cls"].isin(MI.WAGE_CLASSES) & (m["earn"] > 0)]
    pay = (we["earn"] * we["w"]).groupby(we["industry"]).sum().reindex(list(LFS_SPLIT))
    d = ind.copy()
    total = float(d.loc[list(LFS_SPLIT), "labour income"].sum())
    d.loc[list(LFS_SPLIT), "labour income"] = (total * pay / pay.sum()).values
    d["capital and land income"] = d["value added at basic prices"] - d["labour income"]
    if (d.loc[list(LFS_SPLIT), "capital and land income"] <= 0).any():
        raise ValueError("v0.4 labour split leaves no capital income in " + ", ".join(LFS_SPLIT))
    return d


def io_2018() -> dict:
    """PSA 2018 input-output table (240 sectors, Table C.1, producers' prices; tools/build_sam_petroleum_split.load_psa)
    aggregated to the rice-split SAM's activities and commodities (₱ bn). Sector 57 (rice/corn milling) -> amric; 107-108
    (refined petroleum) -> apetr; the rest by IFPRI's concordance (psa_activity)."""
    from build_sam_petroleum_split import load_psa, psa_activity
    Tm, fd, va = load_psa()
    act = [("amric" if k == 57 else "apetr" if k in (107, 108) else psa_activity(k)) for k in range(1, 241)]
    com = ["c" + a[1:] for a in act]
    g = lambda v, keys: pd.Series(v / 1000, index=keys).groupby(level=0).sum()
    ic = pd.DataFrame(Tm / 1000, index=com, columns=act).groupby(level=0).sum().T.groupby(level=0).sum().T
    out = {"ic": ic, **{k: g(va[k], act) for k in ("COE", "GOS", "T-S")},
           **{k: g(np.abs(v) if k == "imp" else v, com) for k, v in fd.items()}}
    return out


def psa_2018_growth() -> tuple:
    """Nominal growth 2023/2018: PSA GVA by industry, and the expenditure aggregates (four quarters summed)."""
    gv = pd.read_csv(paths.DATA_RAW / "macro" / "PSA_OpenSTAT_GVA_by_industry_annual_2000-2025.csv", comment="#")
    gv = gv[gv["valuation"] == "At Current Prices"].pivot_table(index="industry", columns="year", values="value_million_php")
    ind = {k: float(gv.loc[k, 2023] / gv.loc[k, 2018]) for k in PSA_INDUSTRIES}
    e = pd.read_csv(paths.DATA_RAW / "macro" / "PSA_OpenSTAT_GDP_by_expenditure_quarterly_2000-2026.csv", comment="#")
    e = e[e["valuation"] == "At Current Prices"]
    tot = lambda name, y: float(e[(e["expenditure"] == name) & (e["year"] == y)]["value_million_php"].sum())
    names = {"hfce": "Household final consumption expenditure", "gfce": "Government final consumption expenditure",
             "gcf": "Gross fixed capital formation", "exp": "Exports of goods and services", "imp": "Imports of goods and services"}
    return ind, {k: tot(v, 2023) / tot(v, 2018) for k, v in names.items()}


def refining_growth() -> float:
    """Version 0.5: PSA's GVA of 'coke and refined petroleum products', 2023 / 2018, current prices (OpenSTAT 0462B5BMFA1)."""
    d = pd.read_csv(paths.DATA_RAW / "macro" / "PSA_OpenSTAT_0462B5BMFA1_GVA_manufacturing_by_industry_annual.csv", comment="#")
    r = d[d.iloc[:, 0].str.contains("coke and refined petroleum", case=False)].iloc[0]
    return float(r["At Current Prices 2023"]) / float(r["At Current Prices 2018"])


def io_prior(s78: SAM, version: str = VERSION) -> pd.DataFrame:
    """Prior SAM: production and demand from PSA's 2018 I-O moved to 2023 (activity columns by their PSA industry's GVA
    growth, final demand by its aggregate's growth); taxes on products, the trade-margin pattern, home consumption, the
    other-cereals import account and all institutional flows from the PSA-consistent SAM. Not balanced: cross-entropy balances it."""
    t78 = s78.table
    X = t78.copy() * 0.0
    A, C, H = s78.accounts("a"), s78.accounts("c"), s78.accounts("hhd")
    io = io_2018()
    gi, ge = psa_2018_growth()
    ind_of = {a: k for k, acts in PSA_INDUSTRIES.items() for a in acts}
    io_c = [c for c in C if c in io["ic"].index]                       # commodities the I-O has (all but cocer)
    io_a = [a for a in A if a in io["ic"].columns]
    g_ref = refining_growth() if version >= "0.5" else None
    for a in io_a:                                                    # activity columns: inputs and value added
        g = g_ref if (a == "apetr" and g_ref is not None) else gi[ind_of[a]]   # v0.5: refining by its own GVA growth
        X.loc[io_c, a] = io["ic"].reindex(index=io_c).loc[:, a].fillna(0).values * g
        lab = t78.loc[list(P.LABOUR), a]
        nl = t78.loc[list(P.NONLAB), a]
        X.loc[list(P.LABOUR), a] = io["COE"][a] * g * (lab / lab.sum()).values if lab.sum() else 0.0
        X.loc[list(P.NONLAB), a] = io["GOS"][a] * g * (nl / nl.sum()).values if nl.sum() else 0.0
    out_basic = X.loc[:, io_a].sum()                                  # inputs + labour + capital (net taxes left out)
    X.loc[A, H] = t78.loc[A, H]                                       # home consumption (own produce), IFPRI
    for a in io_a:                                                    # make: output less own produce
        X.loc[a, "c" + a[1:]] = out_basic[a] - float(t78.loc[a, H].sum())
    # trade: the I-O's final-demand purchases of trade services are the margins on goods in the SAM layout
    trade_fd = (io["hfce"].get("ctrad", 0.0) * ge["hfce"] + io["gfce"].get("ctrad", 0.0) * ge["gfce"]
                + io["gcf"].get("ctrad", 0.0) * ge["gcf"])
    X.loc["ctrad", "trc"] = trade_fd
    X.loc["ctran", "trc"] = t78.loc["ctran", "trc"]
    X.loc["trc", C] = t78.loc["trc", C] * float(X.loc[C, "trc"].sum()) / float(t78.loc["trc", C].sum())
    # final demand by commodity (the I-O, moved to 2023); households split across groups by IFPRI's pattern, or by FIES
    fg = fies_groups()
    fshare = fg["TOTEX"] / fg["TOTEX"].sum()
    for c in io_c:
        hf = io["hfce"].get(c, 0.0) * ge["hfce"] if c != "ctrad" else 0.0
        a = "a" + c[1:]
        if a in A:
            hf -= float(t78.loc[a, H].sum())                          # own produce is consumption already
        row = t78.loc[c, H]
        X.loc[c, H] = max(hf, 0.0) * ((row / row.sum()).values if row.sum() > 0 else fshare.reindex(H).values)
        X.loc[c, "gov"] = io["gfce"].get(c, 0.0) * ge["gfce"] if c != "ctrad" else 0.0
        X.loc[c, "s-i"] = io["gcf"].get(c, 0.0) * ge["gcf"] if c != "ctrad" else 0.0
        X.loc[c, "dstk"] = io["inv"].get(c, 0.0)
        X.loc[c, "row"] = io["exp"].get(c, 0.0) * ge["exp"]
        X.loc["row", c] = io["imp"].get(c, 0.0) * ge["imp"]
    X.loc[C, "dstk"] *= float(t78.loc["dstk", "s-i"]) / float(X.loc[C, "dstk"].sum())
    # accounts PSA's 240 sectors do not have (pulses sit inside 'other crops'; other cereals are imports only): IFPRI's rows
    # and columns. Without this the pulses activity had output but no inputs or value added, and the CGE on the SAM was
    # near-singular (a first build, 18 Oct 2026, about 1:20 AM: the short-run model wandered to a spurious solution).
    others = [c for c in C if c not in io_c] + [a for a in A if a not in io_a]
    X.loc[others, :] = t78.loc[others, :]
    X.loc[:, others] = t78.loc[:, others]
    X.loc[["mtax", "stax"], C] = t78.loc[["mtax", "stax"], C]         # taxes on products by commodity (GFS via IFPRI)
    inst = [c for c in t78.index if c not in A + C + ["trc"]]         # factors and institutions: the PSA-consistent SAM (IFPRI)
    X.loc[inst, inst] = t78.loc[inst, inst]
    return X


def besf_2023() -> dict:
    """2023 actual tax collections, ₱ bn (DBM BESF 2025 Table C.3; data/raw/fiscal/DBM_BESF_C3_tax_revenue_by_source_2023-2024_actual.csv)."""
    d = pd.read_csv(paths.DATA_RAW / "fiscal" / "DBM_BESF_C3_tax_revenue_by_source_2023-2024_actual.csv", comment="#")
    v = lambda line: float(d.loc[d["line"] == line, "actual_2023_million_php"].iloc[0]) / 1000
    x = "Selective Excises on Goods: "
    return {"duties": v("Import Duties and Taxes"), "fees": v("Other Fees"), "vat_imports": v("VAT on Imports"),
            "excise_boc": v("Excise Tax"), "vat_bir": v("Gen. Sales, Turnover or VAT (Net of VAT Refunds)"),
            "alcohol": v(x + "Alcohol Products"), "tobacco": v(x + "Tobacco Products"), "fuel_bir": v(x + "Fuel and Oils"),
            "mining": v(x + "Mining"), "autos": v(x + "Automobiles"), "misc_excise": v(x + "Miscellaneous"),
            "sweetened": v(x + "Sweetened Beverages and Junk Food"), "cosmetic": v(x + "Cosmetics Procedures"),
            "pct_other": v("Selective Taxes on Services: Other Percentage Taxes"),
            "pct_banks": v("Selective Taxes on Services: Banks/Financial Institutions"),
            "pct_insurance": v("Selective Taxes on Services: Insurance Premiums"),
            "pct_amusement": v("Selective Taxes on Services: Amusements"), "franchise": v("Franchise Taxes"),
            "dst": v("Documentary Stamp Tax"), "cit": v("Company, Corporate and Enterprises"), "pit": v("Individual"),
            "inc_other": v("Others"), "property": v("Property Transfer Tax")}


def tax_block(X: pd.DataFrame, t78: pd.DataFrame, A: list, C: list, H: list) -> pd.DataFrame:
    """Taxes on products by commodity and direct taxes, 2023 (BESF), written into the prior X; returns the allocation table."""
    b = besf_2023()
    stax = pd.Series(0.0, index=C)
    base = (X.loc[C, H].sum(axis=1) + X.loc[C, "gov"] + X.loc[C, "s-i"]).clip(lower=0) * pd.Series(
        {c: VAT_WEIGHT.get(c, 1.0) for c in C})
    vat = b["vat_bir"] + b["vat_imports"]
    stax += vat * base / base.sum()
    fuel_boc = FUEL_EXCISE_2023 - b["fuel_bir"]
    other_boc = b["excise_boc"] - fuel_boc                              # imported alcohol, tobacco, drinks, vehicles
    bev, car = b["alcohol"] + b["tobacco"] + b["sweetened"], b["autos"]
    stax["cpetr"] += FUEL_EXCISE_2023
    stax["cbeve"] += bev + other_boc * bev / (bev + car)
    stax["cmach"] += car + other_boc * car / (bev + car)
    stax["cmine"] += b["mining"]
    stax["coman"] += b["misc_excise"]
    stax["cosrv"] += b["cosmetic"] + b["pct_amusement"]
    stax["cfsrv"] += b["pct_banks"] + b["pct_insurance"] + b["dst"]
    stax["ccomm"] += b["franchise"]
    small = X.loc[["ctran", "chotl", "cosrv"], H].sum(axis=1)       # 3% tax on non-VAT sellers: transport, food stalls, services
    stax[small.index] += b["pct_other"] * small / small.sum()
    mtax = pd.Series(0.0, index=C)
    rice = ["cmric", "crice"]                                          # BOC rice tariff collections (rice-split SAM, 0.3.7)
    mtax[rice] = t78.loc["mtax", rice].values
    rest = [c for c in C if c not in rice]
    duties = b["duties"] + b["fees"]
    mtax[rest] = (duties - mtax[rice].sum()) * t78.loc["mtax", rest] / t78.loc["mtax", rest].sum()
    X.loc["stax", C], X.loc["mtax", C] = stax.values, mtax.values
    X.loc["gov", "stax"], X.loc["gov", "mtax"] = stax.sum(), mtax.sum()
    d_ent = b["cit"] + b["inc_other"] / 2
    d_hh = b["pit"] + b["inc_other"] / 2 + b["property"]
    X.loc["dtax", "ent"] = d_ent
    X.loc["dtax", H] = d_hh * t78.loc["dtax", H] / t78.loc["dtax", H].sum()
    X.loc["gov", "dtax"] = d_ent + d_hh
    return pd.DataFrame({"IFPRI tax on imports": t78.loc["mtax", C], "own SAM tax on imports": mtax,
                         "IFPRI taxes on products": t78.loc["stax", C], "own SAM taxes on products": stax})


def lfs_skills(fg_index) -> tuple:
    """Wage-and-salary earnings by skill from PSA's FIES-LFS 2023 member file (licensed; paths.FIES_LFS_MEMBERS): shares by PSA
    industry (16 x 3) and earnings by household group (10 x 3, families grouped as the microsimulation groups them)."""
    from infinity_gem.household import psic_to_psa16, PSA16
    cols = ["W_REGN", "W_PROV", "SEQ_NO", "LC07_GRADE", "LC16_PKB", "LC19_PDAYS", "LC23_PCLASS", "LC25_PBASIC", "NEWEMPSTAT", "PWGTPRV"]
    m = pd.read_csv(paths.FIES_LFS_MEMBERS, usecols=cols, dtype=str, encoding="utf-8-sig")
    g = pd.to_numeric(m["LC07_GRADE"], errors="coerce")
    m["skill"] = np.select([g < 10018, g < 24015, g >= 24015], ["flab-n", "flab-p", "flab-s"], default="")
    cls = pd.to_numeric(m["LC23_PCLASS"], errors="coerce")
    pay = pd.to_numeric(m["LC25_PBASIC"], errors="coerce")
    days = pd.to_numeric(m["LC19_PDAYS"], errors="coerce")
    days = days.where(days > 0)
    days = days.fillna(days.median())
    m["ind"] = m["LC16_PKB"].map(psic_to_psa16)
    m["earn"] = pay * days * pd.to_numeric(m["PWGTPRV"], errors="coerce")
    sel = (m["NEWEMPSTAT"].str.strip() == "1") & cls.isin([0, 1, 2, 5]) & (m["ind"] >= 0) & (pay > 0) & (m["skill"] != "")
    w = m[sel].copy()
    by_ind = w.pivot_table(index="ind", columns="skill", values="earn", aggfunc="sum").reindex(columns=list(P.LABOUR)).fillna(0)
    by_ind.index = [PSA16[int(i)] for i in by_ind.index]
    f = pd.read_csv(paths.FIES_PUF, usecols=["W_REGN", "W_PROV", "SEQ_NO", "URB", "NPCINC"])
    f["grp"] = np.where(f["URB"] == 1, "hhd-u", "hhd-r") + np.ceil(f["NPCINC"] / 2).astype(int).astype(str)
    for c in ("W_REGN", "W_PROV", "SEQ_NO"):
        w[c] = w[c].astype(int)
    w = w.merge(f[["W_REGN", "W_PROV", "SEQ_NO", "grp"]], on=["W_REGN", "W_PROV", "SEQ_NO"], how="left")
    by_grp = w.pivot_table(index="grp", columns="skill", values="earn", aggfunc="sum").reindex(index=fg_index, columns=list(P.LABOUR)).fillna(0)
    return by_ind.div(by_ind.sum(axis=1), axis=0), by_grp, int(sel.sum())


def ras(seed: pd.DataFrame, rows: pd.Series, cols: pd.Series, it: int = 500) -> pd.DataFrame:
    """Biproportional scaling of seed to row and column totals (they must have the same sum)."""
    x = seed.astype(float).copy()
    for _ in range(it):
        x = x.mul(rows / x.sum(axis=1), axis=0)
        x = x.mul(cols / x.sum(axis=0), axis=1)
        if float((x.sum(axis=1) - rows).abs().max()) < 1e-10:
            break
    return x


def build(version: str = VERSION):
    s78 = SAM.load(paths.SAM_2023_RICE_PSA)                         #: IFPRI's institutional detail, double count removed
    t0 = io_prior(s78, version)
    A0, C0, H0 = s78.accounts("a"), s78.accounts("c"), s78.accounts("hhd")
    taxes = tax_block(t0, s78.table, A0, C0, H0)
    codes = list(t0.index)
    ix = {c: i for i, c in enumerate(codes)}
    n = len(codes)
    A, C, H = s78.accounts("a"), s78.accounts("c"), s78.accounts("hhd")
    psa = P.psa_2023()
    T = float(t0.loc[["mtax", "stax"], C].values.sum())
    ind = industry_targets(psa, T)
    if version >= "0.4":                                            # business services and finance labour from LFS pay (v0.4)
        ind = lfs_split(ind)
    fg = fies_groups()
    I = lambda names: [ix[c] for c in names if c in ix]
    # labour by skill (FIES-LFS): industry shares into the prior; household x skill balanced to FIES wages and skill totals
    sh_ind, by_grp, n_workers = lfs_skills(H)
    ind_of = {a: k for k, acts in PSA_INDUSTRIES.items() for a in acts}
    for a in A:
        if a in ind_of and float(t0.loc[list(P.LABOUR), a].sum()) > 0:
            t0.loc[list(P.LABOUR), a] = float(t0.loc[list(P.LABOUR), a].sum()) * sh_ind.loc[ind_of[a]].values
    lab_row = (t0.loc[list(P.LABOUR), "row"] - t0.loc["row", list(P.LABOUR)]).values      # from abroad less paid abroad
    skill_tot = pd.Series([float((ind["labour income"] * sh_ind[x]).sum()) for x in P.LABOUR], index=list(P.LABOUR)) + lab_row
    hh_lab = ras(by_grp, fg["WAGES"] / fg["WAGES"].sum() * float(skill_tot.sum()), skill_tot)
    t0.loc[H, list(P.LABOUR)] = hh_lab.loc[H].values

    fixed = np.zeros((n, n), dtype=bool)
    def fix(r, c):
        fixed[np.ix_(I(r), I(c))] = True
    fix(["mtax", "stax"], C)                                            # taxes by commodity (BESF 2023)
    fix(["dtax"], ["ent"] + H)
    fix(["gov"], ["ent", "dtax", "ftax", "mtax", "stax", "row"] + H)
    fix(["ent", "row"] + H, ["gov"])
    fix(["row"], list(P.LABOUR + P.NONLAB) + ["ent", "gov"] + H)
    fix(list(P.LABOUR + P.NONLAB) + ["ent"], ["row"])
    fix(["ftax"], ["fcap"])

    def mask(r, c):
        m = np.zeros((n, n), dtype=bool)
        m[np.ix_(I(r), I(c))] = True
        return m
    hfce = psa["hfce"]
    controls = [(f"household consumption: {h} (FIES share)", mask(C + A, [h]), hfce * fg.loc[h, "TOTEX"] / fg["TOTEX"].sum())
                for h in H]
    controls += [("government consumption = PSA", mask(C, ["gov"]), psa["gfce"]),
                 ("fixed investment = PSA", mask(C, ["s-i"]), psa["gfcf"]),
                 ("stock change = PSA (commodities)", mask(C, ["dstk"]), psa["gcf"] - psa["gfcf"]),
                 ("stock change = PSA (financing)", mask(["dstk"], ["s-i"]), psa["gcf"] - psa["gfcf"]),
                 ("exports = PSA", mask(C, ["row"]), psa["exports"]),
                 ("imports = PSA", mask(["row"], C), psa["imports"])]
    for k, acts in PSA_INDUSTRIES.items():
        a = [x for x in acts if x in ix]
        for x in P.LABOUR:
            if sh_ind.loc[k, x] > 0:
                controls.append((f"labour income {x}: {k} (FIES-LFS skill share)", mask([x], a), float(ind.loc[k, "labour income"] * sh_ind.loc[k, x])))
        controls.append((f"capital and land income: {k}", mask(list(P.NONLAB), a), float(ind.loc[k, "capital and land income"])))
    if version >= "0.5" and "apetr" in ix:                         # v0.5: refining's value added at PSA's 2023 refining level
        va_ref = float(t0.loc[list(P.LABOUR + P.NONLAB), "apetr"].sum())
        controls.append(("value added: refining (I-O 2018 x PSA refining GVA 2023/2018)", mask(list(P.LABOUR + P.NONLAB), ["apetr"]), va_ref))
    abroad = float(t0.loc[H, "row"].sum())
    for h in H:
        for x in P.LABOUR:
            controls.append((f"wages {x}: {h} (FIES wages x FIES-LFS skills)", mask([h], [x]), float(hh_lab.loc[h, x])))
        controls.append((f"transfers from abroad: {h} (FIES share)", mask([h], ["row"]),
                         abroad * fg.loc[h, "CASH_ABROAD"] / fg["CASH_ABROAD"].sum()))
    if version >= "0.3":                                            # household consumption by purpose = PSA 2023 (v0.3)
        hh_items = [k for k in C + A if float(t0.loc[k, H].abs().sum()) > 0]
        missing = [k for k in hh_items if ("c" + k[1:]) not in COICOP_BRIDGE]
        if missing:
            raise ValueError(f"household purchases with no COICOP division: {missing}")
        hp = hfce_by_purpose_2023()
        if abs(float(hp.sum()) - hfce) > 0.5:                       # PSA's divisions add up to its HFCE (₱ bn, rounding)
            raise ValueError(f"HFCE by purpose sums to {hp.sum():.1f}, national accounts {hfce:.1f}")
        hp = hp * hfce / float(hp.sum())                            # remove rounding, so the controls are consistent
        for d in COICOP:
            m = np.zeros((n, n))
            for c, sh in COICOP_BRIDGE.items():
                for k in (c, "a" + c[1:]):
                    if d in sh and k in ix:
                        m[ix[k], I(H)] = sh[d]
            controls.append((f"household consumption by purpose: {d} (PSA 2023)", m, float(hp[d])))
    X, diag, ctl = P.cross_entropy(t0.values.astype(float), fixed, controls)
    S = SAM(pd.DataFrame(X, index=codes, columns=codes), dict(s78.labels),
            f"Infinity GEM SAM 2023 version {version}: PSA 2018 I-O moved to 2023, PSA national accounts and FIES 2023 as controls, "
            "IFPRI's institutional detail as prior (tools/build_own_sam_2023.py)")
    diag["max row-column gap"] = S.check(verbose=False)["max_row_col_gap"]
    diag["FIES-LFS wage earners used"] = n_workers
    extra = {"taxes": taxes, "skills by industry": sh_ind, "wages by group and skill": hh_lab}
    return S, s78, diag, ctl, ind, fg, psa, extra


def main(version: str = VERSION):
    S, s0, diag, ctl, ind, fg, psa, extra = build(version)
    path = paths.sam_own(version)
    write_ifpri_csv(S, path)
    with open(path, encoding="utf-8-sig") as f:
        txt = f.read()
    txt = txt.replace("2023 Social Accounting Matrix for Philippines, petroleum split (Infinity GEM 0.3)",
                      f"Infinity GEM 2023 Social Accounting Matrix for the Philippines, version {version} (PSA and FIES controls; IFPRI "
                      "structure as prior; Infinity GEM 0.3.9)", 1)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(txt)
    S1 = SAM.load(path)
    ifpri = SAM.load(paths.SAM_2023_RICE)
    A, C, H = S1.accounts("a"), S1.accounts("c"), S1.accounts("hhd")
    e = {"IFPRI 2023 SAM": P.expenditure(ifpri.table, ifpri), "PSA-consistent": P.expenditure(s0.table, s0),
         f"Infinity GEM SAM v{version}": P.expenditure(S1.table, S1)}
    macro = pd.DataFrame(e)
    purpose = pd.DataFrame({"PSA 2023": hfce_by_purpose_2023(), "IFPRI 2023 SAM": by_purpose(ifpri.table, ifpri),
                            "PSA-consistent": by_purpose(s0.table, s0), f"own SAM v{version}": by_purpose(S1.table, S1)})
    purpose.loc["Total"] = purpose.sum()
    macro["PSA 2023"] = [psa["hfce"], psa["gfce"], psa["gfcf"], psa["gcf"] - psa["gfcf"], psa["exports"], psa["imports"],
                         psa["gdp"], np.nan, np.nan, psa["gdp"]]
    va = lambda t: pd.Series({k: float(t.loc[list(P.LABOUR + P.NONLAB), [a for a in acts if a in t.columns]].values.sum())
                              for k, acts in PSA_INDUSTRIES.items()})
    lab = lambda t: pd.Series({k: float(t.loc[list(P.LABOUR), [a for a in acts if a in t.columns]].values.sum())
                               for k, acts in PSA_INDUSTRIES.items()})
    vt = pd.DataFrame({"PSA GVA 2023 (market prices)": ind["PSA GVA 2023"], "IFPRI value added": va(ifpri.table),
                       f"own SAM v{version} value added (basic prices)": va(S1.table),
                       "IFPRI labour": lab(ifpri.table), f"own SAM v{version} labour": lab(S1.table)})
    vt.loc["Total"] = vt.sum()
    hh = pd.concat({"IFPRI": P.households(ifpri.table, ifpri), f"own SAM v{version}": P.households(S1.table, S1)}, axis=1)
    fies = pd.DataFrame({"FIES consumption share (%)": fg["TOTEX"] / fg["TOTEX"].sum() * 100,
                         "FIES wage share (%)": fg["WAGES"] / fg["WAGES"].sum() * 100,
                         "FIES share of transfers from abroad (%)": fg["CASH_ABROAD"] / fg["CASH_ABROAD"].sum() * 100,
                         "FIES saving rate (%)": (fg["TOINC"] - fg["TOTEX"]) / fg["TOINC"] * 100})
    inst = pd.DataFrame({k: {"enterprise saving": t.loc["s-i", "ent"], "household saving": t.loc["s-i", H].sum(),
                             "government saving": t.loc["s-i", "gov"], "foreign saving": t.loc["s-i", "row"],
                             "enterprise payouts to households": t.loc[H, "ent"].sum()}
                         for k, t in (("IFPRI", ifpri.table), ("PSA-consistent", s0.table), (f"own SAM v{version}", S1.table))})
    stamp = dt.datetime.now()
    L = [f"# Infinity GEM's own 2023 SAM, version {version} ({stamp:%d %B %Y, %H:%M})", "",
         f"**NOT YET THE MODEL'S SAM** (Infinity GEM 0.3.9; opt-in: settings `sam_variant=\"own\"` with "
         f"`rice=True`). Tool: `tools/build_own_sam_2023.py`; design and source table: "
         f"a design note (not included). File: `{path.relative_to(ROOT)}`.", "",
         "## 1. Macro totals against PSA (₱ bn, current prices)", "", macro.round(1).to_markdown(), "",
         "## 1b. Household consumption by purpose (₱ bn; COICOP divisions through COICOP_BRIDGE; v0.3 controls them)", "",
         purpose.round(1).to_markdown(), "",
         "## 2. Value added and labour income by PSA industry (₱ bn)", "",
         "the project's value added is PSA's GVA minus the taxes on products inside it (PSA's 2018 I-O shares, scaled to the SAM's "
         "taxes on products; public administration not cut). Labour = the I-O's compensation share x PSA GVA"
         + ("; from v0.4, business services and finance share their combined labour in proportion to FIES-LFS 2023 basic pay"
            if version >= "0.4" else "") + ".", "",
         vt.round(1).to_markdown(), "", "Targets:", "", ind.round(4).to_markdown(), "",
         "## 3. Household groups (grouped as the microsimulation groups FIES families)", "", fies.round(1).to_markdown(), "",
         hh.round(1).to_markdown(), "", "Saving and payouts (₱ bn):", "", inst.round(1).to_markdown(), "",
         "## 4. Taxes on products by commodity (₱ bn; BESF 2025 Table C.3, 2023 actuals)", "",
         "Customs duties and fees are the tax on imports; VAT and excises (domestic and on imports), percentage taxes, the "
         "documentary stamp tax and franchise taxes are taxes on the product. IFPRI's SAM counted VAT on imports as an import "
         "tax.", "", extra["taxes"].round(2).to_markdown(), "",
         "## 5. Labour by skill (FIES-LFS 2023 wage-and-salary earnings)", "", "Shares by PSA industry:", "",
         extra["skills by industry"].round(3).to_markdown(), "", "Wages by household group and skill (₱ bn):", "",
         extra["wages by group and skill"].round(1).to_markdown(), "",
         "## 6. Balancing (cross-entropy; prior = PSA's 2018 I-O moved to 2023 with IFPRI's institutional detail)", "",
         "| Item | Value |", "|---|---|"] + \
        [f"| {k} | {v:,.6g} |" for k, v in diag.items()] + ["", ctl.round(6).to_markdown(), "",
         "## 7. Still from IFPRI's structure in this version (design note §4)", "",
         "Government transfers; rest-of-world income flows; the activity mix within each PSA industry; land; the margin "
         "pattern; household direct taxes by group; customs duties by commodity other than rice."]
    rp = paths.output_dir() / f"own_sam_2023_v{version}_{stamp:%Y%m%d_%H%M}.md"
    rp.write_text("\n".join(L), encoding="utf-8")
    print(macro.round(1).to_string()); print(purpose.round(1).to_string()); print(vt.round(1).to_string()); print(hh.round(1).to_string()); print(inst.round(1).to_string())
    print(pd.Series(diag).to_string())
    print("saved", path, "and", rp)
    return S1


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else VERSION)
