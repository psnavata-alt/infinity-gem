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
Kept from the prior in v0.5 (design note §4): government transfers, the rest-of-world income flows (BOP-based),
the activity mix within each PSA industry, intermediate inputs, land and trade margins. Everything not controlled moves as
little as possible (deterministic cross-entropy; tools/build_sam_psa_consistent.cross_entropy).
Version 0.6 (23 Oct 2026; RESEARCH, NOT THE DEFAULT: VERSION below stays "0.5", settings and paths
still mean v0.5, and build() with no argument still reproduces the v0.5 file, check S6) replaces most of those blocks:
  rest of the world, general government and direct taxes: PSA's 2023 integrated accounts (OpenSTAT 2B/CA: external
     transactions 0042B5BCA04, general government 0072B5BIO03, households 0082B5BIO04, corporations 0052B5BIO01 and
     0062B5BIO02), consistent with the PSA exports and imports the SAM already uses: OFW compensation and transfers from
     abroad to households (₱4.49 tn, by FIES receipts from abroad), property income from and to the rest of the world, social
     benefits and other transfers to households (by FIES pensions and domestic cash assistance), interest and subsidies to
     enterprises, social contributions and fees, taxes on income and wealth by paying sector; foreign saving becomes PSA's
     current external SURPLUS (₱909.5 bn);
  household income tax by group: the TRAIN 2023 schedule on FIES-LFS 2023 wage earners' pay (licensed; ten shares leave it);
  labour income: PSA's 2023 compensation of employees (₱8,626.6 bn, 0022B5BCA02), the I-O's industry pattern;
  the activity mix within agriculture, manufacturing and utilities: PSA's 2023 GVA by sub-industry (0382B5BAFA1, 0462B5BMFA1,
     0502B5BEWA1), less the I-O's tax content;
  land: land's share of crop capital and land income from PSA's costs-and-returns surveys (2B/AA/CR; palay 2023, others to
     2021), IFPRI's share kept for crops without a survey;
  household capital income: land and farm capital paid to each group by FIES 2023 crop and farm income; household saving by
     FIES saving shares (total kept at v0.5's, see household_capital_and_saving); enterprise payouts close each account;
  trade by product: the 2018 I-O's exports and imports by commodity grown by PSA's 2018-2023 growth of their product group
     (0222B5BEGA1, 0262B5BESA1, 0302B5BIGA1, 0342B5BISA1), with the main groups controlled.
  Still IFPRI's in v0.6: trade margins, customs duties other than rice, home consumption, the household-enterprise split of
  private saving, land shares without a survey, each group's purchases by commodity (report section 8).
Version 0.6e (23 Oct 2026; RESEARCH, opt-in, NOT the default; everything else as v0.6): electricity's
  fuel mix. PSA's 2018 Use table books the electricity industry's fuel as 73% refined petroleum, 20% natural gas and 7% coal,
  against DOE's 2018 generation of 52% coal, 21% gas and 3% oil, and sends 78% of the country's intermediate coal to basic
  iron and steel (2% in GTAP 10A's IEA-based 2014 energy volumes; power plants 80%); the 240-industry I-O used as the prior
  also moves half of electricity's gas into the refined-petroleum row (it is the Use table under the fixed product-sales
  structure). v0.6e sets electricity's oil products to a DOE- and IEA-consistent 2023 oil bill and the rest of its fuel bill
  to coal and gas (cmine), with imports carrying the switch (electricity_fuel_mix); research/electricity_fuel_mix/ has the
  evidence; checks/test_own_sam_v06e.py the checks and the oil-shock tests.
Version 0.5e (23 Oct 2026; RESEARCH, opt-in, NOT the default; VERSION below stays "0.5"): v0.5, the
  approved default, with the same electricity fuel-mix correction as 0.6e and nothing else of v0.6 (the owner is ready to
  adopt the correction while v0.6's other blocks still have open issues). In the prior, electricity's oil products (cpetr) =
  the same 2023 oil bill (electricity_oil_2023) and the rest of its fuel bill = coal and gas (cmine), imports carrying the
  switch (electricity_fuel_mix with base "0.5"); three balancing controls hold electricity's oil products at that bill, its
  fuel bill (cpetr + cmine) at v0.5's balanced value and the imports of cpetr + cmine at v0.5's (in 0.6e PSA's product-group
  control holds that import total; v0.5 has none), so v0.5e differs from v0.5 in the fuel MIX, not in the size of the fuel
  bill or of the fuel and ore imports. Checks and tests: checks/test_own_sam_v05e.py.
Version 0.7 (24 Oct 2026; RESEARCH, opt-in, NOT the default; VERSION below stays "0.5"): v0.5e with coal split out of
  the mining account into its own activity and commodity (acoal, ccoal), so that an oil shock no longer moves coal at crude's
  share and coal prices can be shocked on their own (infinity_gem/oil.py). Every cell of the mining activity's and commodity's
  rows and columns is split into coal and the rest (coal_split); every other cell is v0.5e's, and acoal + amine and ccoal +
  cmine give v0.5e back, so v0.5e's balance and PSA and FIES controls hold. The coal part: PSA's 2018 240-industry I-O (the
  coal-mining row and column, 39, against mining, 39-45), DOE's 2023 generation with v0.5e's electricity fuel bill (its coal =
  its v0.5e mining purchases less gas and other mining), v0.5's mining imports (the rest of mining keeps them); basic metals'
  coal (PSA's least reliable coal cell) closes the coal account. Checks and tests: checks/test_own_sam_v07.py.
Version 0.7b (24 Oct 2026; RESEARCH, opt-in, NOT the default; VERSION below stays "0.5"): v0.7 without its coal double
  count. v0.5e kept PSA's coal in basic metals and also gave electricity the power plants' coal through extra mining imports, so
  v0.7's basic metals bought ₱77 bn of coal (the coal account's balancing cell) in a ₱309 bn coal account. v0.7b reads PSA's
  coal in basic metals as the power plants' coal to the extent of the double count S: in v0.5e's prior basic metals' mining
  purchases and the mining imports fall by S, refined-oil imports rise by S (PSA's oil imports partly restored) and the S of oil
  goes to the other users of refined petroleum; two controls hold those cells at v0.5e's less S, and the value added of every
  activity stays v0.5e's; then v0.7's coal split, with S solved so that basic metals' coal equals its IEA-consistent 2023 amount
  (build_v07b). Writes the SAM file and CSV tables (main_v07b; no report file). Checks and tests: checks/test_own_sam_v07b.py.
Outputs: data/processed/InfinityGEM_SAM_PHL_2023_own_v<version>.csv and outputs/own_sam_2023_v<version>_<date>.md (earlier versions'
files kept). build(version) rebuilds any version: '0.2' leaves out the controls by purpose.
Run:  py tools/build_own_sam_2023.py [version]     NOT the default SAM: settings sam_variant="own" (with rice=True). Check S6.
      py tools/build_own_sam_2023.py 0.6       v0.6 (research; reached only through paths.sam_own("0.6")); checks/test_own_sam_v06.py
      py tools/build_own_sam_2023.py 0.6b      sensitivity: v0.6 with the rest-of-world income flows from BSP's BPM6 BOP
      py tools/build_own_sam_2023.py 0.6c      decomposition only: v0.6 without the trade-by-product block (v0.5's trade)
      py tools/build_own_sam_2023.py 0.6e      research: v0.6 with electricity's fuel mix at DOE's (coal and gas, not oil)
      py tools/build_own_sam_2023.py 0.5e      research: v0.5 with the same electricity fuel-mix correction only
      py tools/build_own_sam_2023.py 0.7       research: v0.5e with coal split from mining (acoal, ccoal); checks/test_own_sam_v07.py
      py tools/build_own_sam_2023.py 0.7b      research: v0.7 without the coal double count; checks/test_own_sam_v07b.py
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
    "ccoal": {_HO: 1.0},                                   # v0.7 only: coal, split from mining, in the same division as cmine
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
    tg = trade_growth() if version >= "0.6" and not version.endswith("c") else None   # v0.6: trade by PSA product group
    #   ('0.6c', a decomposition run only: v0.6 without the trade-by-product block, i.e. v0.5's growth of total trade)
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
        X.loc[c, "row"] = io["exp"].get(c, 0.0) * (trade_factor(tg["exports"], c) if tg else ge["exp"])
        X.loc["row", c] = io["imp"].get(c, 0.0) * (trade_factor(tg["imports"], c) if tg else ge["imp"])
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


# ------------------------------------------------------------------------------------------------------------------------------
# Version 0.6 (23 Oct 2026; research, NOT the default): the blocks v0.5 still took from IFPRI's
# structure, replaced where Philippine data allow. Every function below is used only when version >= "0.6", so build("0.5")
# still reproduces the default file (check S6). Data: PSA OpenSTAT tables saved 23 Oct 2026 by
# data/raw/macro/download_psa_sam_v06_tables.py (each CSV carries its source lines), FIES 2023 (public-use file) and, for the
# household income-tax shares only, the licensed FIES-LFS 2023 member file (aggregates only; never copied).
# ------------------------------------------------------------------------------------------------------------------------------
SECTOR_FILES = {   # PSA's 2023 integrated accounts by institutional sector (OpenSTAT folder 2B/CA), ₱ million, current prices
    "row": "macro/PSA_OpenSTAT_0042B5BCA04_external_transactions_annual.csv",
    "gg": "macro/PSA_OpenSTAT_0072B5BIO03_general_government_income_outlay_annual.csv",
    "hh": "macro/PSA_OpenSTAT_0082B5BIO04_households_income_outlay_annual.csv",
    "nfc": "macro/PSA_OpenSTAT_0052B5BIO01_nonfinancial_corporations_income_outlay_annual.csv",
    "fc": "macro/PSA_OpenSTAT_0062B5BIO02_financial_corporations_income_outlay_annual.csv",
    "ndi": "macro/PSA_OpenSTAT_0022B5BCA02_national_disposable_income_annual.csv"}


def _psa_wide(name: str, col: str = "2023") -> pd.Series:
    """One column of a PSA OpenSTAT table saved in PSA's raw wide layout ('#' source lines first), in ₱ bn, indexed by the
    item label without PSA's leading dots."""
    d = pd.read_csv(paths.DATA_RAW / name, comment="#")
    s = pd.Series(pd.to_numeric(d[col], errors="coerce").values / 1e3,
                  index=d.iloc[:, 0].astype(str).str.strip().str.lstrip(".").str.strip())
    return s[~s.index.duplicated()]


def psa_sector_accounts_2023() -> dict:
    """PSA's 2023 income and outlay accounts (general government, households, non-financial and financial corporations),
    external transactions and national disposable income, ₱ bn."""
    return {k: _psa_wide(f) for k, f in SECTOR_FILES.items()}


def fies_groups_v06() -> pd.DataFrame:
    """Version 0.6: FIES 2023 totals by SAM household group (RFACT-weighted, ₱ bn) for the distributions v0.6 adds."""
    cols = ["TOINC", "TOTEX", "WAGES", "CASH_ABROAD", "CASH_DOMESTIC", "PENSION", "NETSHARE", "NET_CFG", "NET_LPR", "NET_FISH",
            "NET_FOR"]
    f = pd.read_csv(paths.FIES_PUF, usecols=cols + ["RFACT", "URB", "NPCINC"])
    f["grp"] = np.where(f["URB"] == 1, "hhd-u", "hhd-r") + np.ceil(f["NPCINC"] / 2).astype(int).astype(str)
    g = pd.DataFrame({k: (f[k] * f["RFACT"]).groupby(f["grp"]).sum() / 1e9 for k in cols})
    g["government transfers"] = g["PENSION"] + g["CASH_DOMESTIC"]          # pensions and domestic cash assistance
    g["saving"] = g["TOINC"] - g["TOTEX"]                                  # FIES saving (income less expenditure)
    g["crop income"] = g["NET_CFG"] + g["NETSHARE"]                        # crop farming and share of crops
    g["farm income"] = g["NET_CFG"] + g["NET_LPR"] + g["NET_FISH"] + g["NET_FOR"]   # crops, livestock, fishing, forestry
    return g


TRAIN_2023 = ((0.0, 0.00, 0.0), (250_000.0, 0.15, 0.0), (400_000.0, 0.20, 22_500.0), (800_000.0, 0.25, 102_500.0),
              (2_000_000.0, 0.30, 402_500.0), (8_000_000.0, 0.35, 2_202_500.0))   # (bracket floor, rate on excess, tax at floor)


def train_tax(y: np.ndarray) -> np.ndarray:
    """Income tax on annual taxable compensation under the schedule in force from 1 January 2023 (RA 10963 'TRAIN', Sec. 5;
    NIRC Sec. 24(A)(2)(a)), ₱."""
    y = np.asarray(y, float)
    tax = np.zeros_like(y)
    for floor, rate, base in TRAIN_2023:
        tax = np.where(y > floor, base + rate * (y - floor), tax)
    return tax


def pit_shares(H) -> tuple:
    """Version 0.6: each household group's share of personal income tax, from the TRAIN 2023 schedule applied to the annual
    pay of every wage and salary earner in PSA's FIES-LFS 2023 member file (licensed; only these ten shares and two totals
    leave it): basic daily pay x days worked last week x 52, grossed up to PSA's 2023 compensation of employees (k = PSA's
    compensation from resident producers, OpenSTAT 0022B5BCA02, / the earners' total basic pay: 13th-month pay, bonuses and
    allowances, which LFS basic pay leaves out; 1.88 on the I-O-based total, design note §10.2), less 5% for the employee's
    SSS, PhilHealth and Pag-IBIG contributions. The same shares spread PSA's whole household 'taxes on income and wealth' (the
    tax on business income and final taxes on interest follow the wage tax: an approximation, stated in the report).
    Returns (shares, k, the computed tax in ₱ bn, earners in the sample)."""
    cols = ["W_REGN", "W_PROV", "SEQ_NO", "LC19_PDAYS", "LC23_PCLASS", "LC25_PBASIC", "NEWEMPSTAT", "PWGTPRV"]
    m = pd.read_csv(paths.FIES_LFS_MEMBERS, usecols=cols, dtype=str, encoding="utf-8-sig")
    cls = pd.to_numeric(m["LC23_PCLASS"], errors="coerce")
    pay = pd.to_numeric(m["LC25_PBASIC"], errors="coerce")
    days = pd.to_numeric(m["LC19_PDAYS"], errors="coerce")
    days = days.where(days > 0)
    days = days.fillna(days.median())
    sel = (m["NEWEMPSTAT"].str.strip() == "1") & cls.isin([0, 1, 2, 5]) & (pay > 0)
    w = m[sel].copy()
    annual = pay[sel] * days[sel] * 52
    wt = pd.to_numeric(w["PWGTPRV"], errors="coerce")
    k = float(psa_sector_accounts_2023()["ndi"]["From resident producers"]) / (float((annual * wt).sum()) / 1e9)
    w["tax"] = train_tax(annual * k * 0.95) * wt
    f = pd.read_csv(paths.FIES_PUF, usecols=["W_REGN", "W_PROV", "SEQ_NO", "URB", "NPCINC"])
    f["grp"] = np.where(f["URB"] == 1, "hhd-u", "hhd-r") + np.ceil(f["NPCINC"] / 2).astype(int).astype(str)
    for c in ("W_REGN", "W_PROV", "SEQ_NO"):
        w[c] = w[c].astype(int)
    w = w.merge(f[["W_REGN", "W_PROV", "SEQ_NO", "grp"]], on=["W_REGN", "W_PROV", "SEQ_NO"], how="left")
    by = w.groupby("grp")["tax"].sum().reindex(H).fillna(0.0)
    return by / by.sum(), k, float(w["tax"].sum()) / 1e9, int(sel.sum())


AGRI_GROUPS = {   # Version 0.6: PSA GVA 2023 in agriculture, forestry and fishing by sub-industry (OpenSTAT 0382B5BAFA1) -> SAM
    # activities. The crop group holds what PSA's 240-sector I-O (the prior) puts in fruits, root crops, vegetables, pulses and
    # other crops: banana, mango, pineapple, cassava, rubber, other crops n.e.c. and the support activities (I-O sector 38 ->
    # aocrp, tools/build_sam_petroleum_split.psa_activity); within it the 2018 I-O mix is kept.
    ("arice",): ["Palay"], ("amaiz",): ["Corn"], ("aoils",): ["Coconut including copra"],
    ("asugr",): ["Sugarcane including muscovado sugar-making in the farm"], ("acoff",): ["Coffee", "Cacao"], ("acott",): ["Abaca"],
    ("atoba",): ["Tobacco"],
    ("afrui", "aroot", "avege", "aocrp", "apuls"): ["Banana", "Mango", "Pineapple", "Cassava", "Rubber",
                                                    "Other agricultural crops, n.e.c.",
                                                    "Support activities to agriculture, forestry and fishing"],
    ("acatt", "aoliv"): ["Livestock", "Other animal production"], ("apoul",): ["Poultry and egg production"],
    ("afore",): ["Forestry and logging"], ("afish",): ["Fishing and aquaculture"]}
MFG_GROUPS = {    # Version 0.6: PSA GVA 2023 in manufacturing by industry (OpenSTAT 0462B5BMFA1), labels matched by their start;
    # the groups follow the I-O concordance (food 46-68 incl. milling; beverages and tobacco 69-77; textiles, apparel, leather
    # 78-94; wood, paper, printing 95-106; refining 107-108; chemicals, pharmaceuticals, rubber, plastics 109-118; ...)
    ("afood", "amric"): ["Manufacture of food products"],
    ("abeve",): ["Manufacture of beverages", "Manufacture of tobacco products"],
    ("atext",): ["Manufacture of textiles", "Manufacture of wearing apparel", "Manufacture of leather"],
    ("awood",): ["Manufacture of wood", "Manufacture of paper", "Printing and reproduction"],
    ("apetr",): ["Manufacture of coke and refined petroleum"],
    ("achem",): ["Manufacture of chemical", "Manufacture of basic pharmaceutical", "Manufacture of rubber and plastic"],
    ("anmet",): ["Manufacture of other non-metallic"],
    ("ametl",): ["Manufacture of basic metals", "Manufacture of fabricated metal"],
    ("amach",): ["Manufacture of computer", "Manufacture of electrical", "Manufacture of machinery",
                 "Manufacture of transport equipment"],
    ("aoman",): ["Manufacture of furniture", "Other manufacturing"]}
UTIL_GROUPS = {("aelec",): ["Electricity", "Steam"], ("awatr",): ["Water supply", "Waste management"]}   # OpenSTAT 0502B5BEWA1
SUBINDUSTRY = {"Agriculture, forestry, and fishing": ("macro/PSA_OpenSTAT_0382B5BAFA1_GVA_agriculture_by_subsector_annual.csv", AGRI_GROUPS),
               "Manufacturing": ("macro/PSA_OpenSTAT_0462B5BMFA1_GVA_manufacturing_by_industry_annual.csv", MFG_GROUPS),
               "Electricity, steam, water and waste management": (
                   "macro/PSA_OpenSTAT_0502B5BEWA1_GVA_electricity_water_by_industry_annual.csv", UTIL_GROUPS)}


def subindustry_va(ind: pd.DataFrame) -> dict:
    """Version 0.6: value added at basic prices by activity group within agriculture, manufacturing and utilities: PSA's 2023
    GVA by sub-industry less the taxes on products inside it (net-tax share of total primary inputs in PSA's 2018 I-O, 80
    industries, through build_sam_psa_consistent.ACT_IO80), scaled so the groups add up to their industry's value added at
    basic prices (industry_targets). Returns {industry: DataFrame by group}."""
    _, io80 = P._io_rows(paths.DATA_RAW / "io" / "80-Industry20Table202018.csv", 80)
    out = {}
    for k, (fname, groups) in SUBINDUSTRY.items():
        g = _psa_wide(fname, "At Current Prices 2023")
        rows = {}
        for acts, labels in groups.items():
            hit = [i for i in g.index if any(i == lab or i.startswith(lab) for lab in labels)]
            if len(hit) < len(labels):
                raise ValueError(f"{k}: PSA lines {labels} not all found ({hit})")
            sec = sorted({s for a in acts for s in P.ACT_IO80[a]})
            rows["+".join(acts)] = {"activities": acts, "PSA GVA 2023": float(g[hit].sum()), "PSA lines": "; ".join(hit),
                                    "net-tax share (I-O 2018, 80 industries)": float(io80.loc[sec, "T-S"].sum() / io80.loc[sec, "TPI"].sum())}
        d = pd.DataFrame(rows).T
        gva_total = float(d["PSA GVA 2023"].sum())
        if abs(gva_total - float(ind.loc[k, "PSA GVA 2023"])) > 0.01 * gva_total:
            raise ValueError(f"{k}: sub-industries add up to {gva_total:.1f}, PSA's industry GVA {ind.loc[k, 'PSA GVA 2023']:.1f}")
        content = d["PSA GVA 2023"].astype(float) * d["net-tax share (I-O 2018, 80 industries)"].astype(float)
        target_tax = float(ind.loc[k, "PSA GVA 2023"] - ind.loc[k, "value added at basic prices"])
        d["taxes on products inside GVA"] = content * target_tax / float(content.sum()) if content.sum() else 0.0
        d["value added at basic prices"] = (d["PSA GVA 2023"].astype(float) - d["taxes on products inside GVA"]) * \
            float(ind.loc[k, "value added at basic prices"]) / (gva_total - target_tax)
        out[k] = d
    return out


LAND_CR = {   # Version 0.6: SAM crop activity -> PSA costs-and-returns surveys (OpenSTAT folder 2B/AA/CR) and the years used
    "arice": ("agri/PSA_OpenSTAT_0012B5EAPC0_palay_costs_and_returns_2022-2025.csv", {"Type": "Palay", "Geolocation": "PHILIPPINES"}, ["Average 2023"]),
    "amaiz": ("agri/PSA_OpenSTAT_0022B5EAPC1_palay_corn_costs_and_returns_2002-2021.csv", {"Type": "All Corn", "Geolocation": "PHILIPPINES"},
              ["Average 2019", "Average 2020", "Average 2021"]),
    "aroot": ("agri/PSA_OpenSTAT_0032B5ECOP1_rootcrops_costs_and_returns.csv", {}, ["2019", "2020", "2021"]),
    "apuls": ("agri/PSA_OpenSTAT_0042B5ECOP2_legumes_costs_and_returns.csv", {}, ["2019", "2020", "2021"]),
    "avege": ("agri/PSA_OpenSTAT_0052B5ECOP3_vegetables_costs_and_returns.csv", {}, ["2019", "2020", "2021"]),
    "afrui": ("agri/PSA_OpenSTAT_0062B5ECOP4_fruits_costs_and_returns.csv", {}, ["2019", "2020", "2021"]),
    "acoff": ("agri/PSA_OpenSTAT_0072B5ECOP5_commercial_crops_costs_and_returns.csv", {}, ["2019", "2020", "2021"])}


def _cr_class(item: str) -> str:
    """Classify a costs-and-returns line: 'land', 'labour', 'capital' (depreciation, interest, owned animals) or 'other'."""
    i = item.lower()
    if any(k in i for k in ("landowner", "landlord", "lease rental", "rental value of owned land", "land tax")):
        return "land"
    if any(k in i for k in ("labor", "labour", "harvester", "thresher", "reaper", "sheller", "laborer", "overseer",
                            "caretaker", "permanent employee", "food expense")):
        return "labour"
    if any(k in i for k in ("depreciation", "interest", "financier", "rental value of owned animals")):
        return "capital"
    return "other"


def land_shares_cr() -> pd.DataFrame:
    """Version 0.6: land's share of capital and land income for the crop activities with PSA costs-and-returns surveys (per
    hectare, ₱): land = landowner's or landlord's share, lease rental, rental value of owned land and land tax; hired labour =
    hired labour (cash and kind), harvesters', threshers' and other workers' shares, overseers, food for workers; own labour =
    operator, family and exchange labour (counted once where PSA lists both the parts and the combined line); intermediate
    inputs = all costs less labour, land, depreciation and interest; value added = gross returns less intermediate inputs.
    Share = land / (value added - hired labour), summed over the commodities and years listed in LAND_CR (palay 2023; the
    other surveys end in 2021): the SAM's labour is employees' compensation, so own labour is part of the SAM's capital and
    land income."""
    rows = {}
    for a, (fname, keys, years) in LAND_CR.items():
        d = pd.read_csv(paths.DATA_RAW / fname, comment="#")
        for k, v in keys.items():
            d = d[d[k].astype(str).str.strip() == v]
        item = d["Item"].astype(str).str.strip()
        head = ~item.str.startswith(".")                       # PSA's totals and returns lines carry no leading dots
        name = item.str.lstrip(".").str.strip().str.replace(r"\s+", " ", regex=True)
        low = name.str.lower()
        cls = name.map(_cr_class)
        own = low.str.contains("operator") | low.isin(["family labor", "exchange labor"])   # the farm family's own labour
        unit = d["Commodity"].astype(str) if "Commodity" in d.columns else pd.Series("all", index=d.index)
        tot = dict.fromkeys(("land", "hired labour", "own labour", "capital", "costs", "gross"), 0.0)
        for _, part in d.groupby(unit):                        # each commodity and year on its own
            ix_ = part.index
            for y in years:
                v = pd.to_numeric(part[y], errors="coerce").fillna(0.0)
                hd, nm, lo, cl, ow = head[ix_], name[ix_].str.upper(), low[ix_], cls[ix_], own[ix_]
                gross = float(v[hd & (nm == "GROSS RETURNS")].sum())
                costs = float(v[hd & nm.isin(["TOTAL COSTS", "ALL COSTS"])].sum())
                if gross <= 0 or costs <= 0:                   # not surveyed that year
                    continue
                own_l = float(v[~hd & (cl == "labour") & ow].sum())
                sep = float(v[~hd & lo.isin(["operator labor", "family labor"])].sum())
                comb = float(v[~hd & lo.isin(["operator and family labor", "operator/family labor"])].sum())
                if sep > 0 and comb > 0:                       # both the parts and the combined line filled in: count once
                    own_l -= min(sep, comb)
                tot["own labour"] += own_l
                tot["hired labour"] += float(v[~hd & (cl == "labour") & ~ow].sum())
                tot["land"] += float(v[~hd & (cl == "land")].sum())
                tot["capital"] += float(v[~hd & (cl == "capital")].sum())
                tot["costs"] += costs
                tot["gross"] += gross
        inter = tot["costs"] - tot["land"] - tot["hired labour"] - tot["own labour"] - tot["capital"]
        va = tot["gross"] - inter
        # the SAM's labour in agriculture is PSA's compensation of employees; the farm family's own labour is part of its
        # capital and land income (mixed income), so the share is taken of value added less HIRED labour
        rows[a] = {"source": fname.split("/")[-1], "years": ", ".join(years), "gross returns": tot["gross"],
                   "intermediate inputs": inter, "hired labour": tot["hired labour"], "own labour": tot["own labour"],
                   "land": tot["land"], "value added": va,
                   "land share of capital and land income": tot["land"] / (va - tot["hired labour"])}
    return pd.DataFrame(rows).T


EXP_GROUPS = {   # Version 0.6: SAM commodities -> PSA national-accounts export lines (0222B5BEGA1 goods, 0262B5BESA1 services)
    ("cmach",): ["Electronic Products", "Ignition wiring sets", "Machinery and transport equipment",
                 "Manufacturing services on physical inputs owned by others"],
    ("cmetl",): ["Cathodes and sections of cathodes, of refined copper", "Metal components"],
    ("ctext",): ["Articles of apparel and clothing accessories"], ("cpetr",): ["Petroleum products"], ("cchem",): ["Chemicals"],
    ("cfrui",): ["Bananas (fresh)", "Mangoes"], ("cfish",): ["Shrimps, prawns, and other fishery products"],
    ("cfood", "cbeve"): ["Coconut oil", "Copra oil cake or meal", "Desiccated coconut", "Pineapple and pineapple products", "Sugar",
                         "Tuna", "Processed food and beverages"],
    ("ctran",): ["Transport"], ("chotl",): ["Travel"], ("ccomm",): ["Telecommunications, computer and information services"],
    ("cbsrv", "ctrad"): ["Other business services"], ("cfsrv",): ["Insurance and pension services"],
    ("cpadm",): ["Government goods and services n.i.e."]}
EXP_REST = {"goods": ["Other agricultural products", "Other exports of goods", "Woodcrafts and furniture"],
            "services": ["Miscellaneous services"]}
IMP_GROUPS = {   # Version 0.6: SAM commodities -> PSA national-accounts import lines (0302B5BIGA1 goods, 0342B5BISA1 services)
    ("cmach",): ["Electronic products", "Industrial machinery and equipment", "Power generating and specialized machinery",
                 "Transport equipment", "Telecommunication and electrical machinery", "Professional scientific apparatus"],
    ("cpetr", "cmine"): ["Mineral fuels, lubricants and related materials", "Metalliferous ores and metal scrap"],
    ("cmetl",): ["Base metals", "Metal products"],
    ("cchem",): ["Chemical and chemical products", "Medicinal and pharmaceutical products", "Plastics in primary and non-primary forms"],
    ("ctext",): ["Textile yarn, fabrics, made-up articles and related products", "Articles of apparel"],
    ("crice", "cmric", "cmaiz"): ["Cereals and cereal preparation"], ("cfrui", "cvege"): ["Fruits and vegetables"],
    ("ctran",): ["Transport"], ("cfsrv",): ["Insurance and pension services"], ("chotl",): ["Travel"],
    ("cpadm",): ["Government goods and services n.i.e."], ("ccomm",): ["Telecommunications, computer and information services"],
    ("cbsrv",): ["Business services", "Charges for the use of intellectual property"]}
IMP_REST = {"goods": ["Other imports of goods", "Dairy products", "Feeding stuff", "Paper and paper products"],
            "services": ["Miscellaneous services"]}
TRADE_FILES = {"exports": ("macro/PSA_OpenSTAT_0222B5BEGA1_exports_of_goods_annual.csv", "macro/PSA_OpenSTAT_0262B5BESA1_exports_of_services_annual.csv"),
               "imports": ("macro/PSA_OpenSTAT_0302B5BIGA1_imports_of_goods_annual.csv", "macro/PSA_OpenSTAT_0342B5BISA1_imports_of_services_annual.csv")}
TRADE_CONTROLLED = {"exports": [("cmach",), ("cbsrv", "ctrad"), ("ccomm",), ("chotl",), ("ctran",)],
                    "imports": [("cmach",), ("cpetr", "cmine"), ("cchem",), ("cmetl",), ("chotl",), ("ctran",), ("cbsrv",)]}
GOODS = set(AGRI_FISH) | {"cmine", "cfood", "cmric", "cbeve", "ctext", "cwood", "cchem", "cpetr", "cnmet", "cmetl", "cmach", "coman",
                          "cocer", "cpuls", "celec", "cwatr"}


def trade_growth() -> dict:
    """Version 0.6: growth 2018-2023 (current prices) of exports and imports by SAM commodity: each commodity grows with PSA's
    national-accounts lines of its product group (EXP_GROUPS, IMP_GROUPS), the rest with the remaining goods or services lines.
    Returns {'exports': {commodity: growth}, 'imports': {...}, 'groups': DataFrame}."""
    out, rows = {}, {}
    for flow, groups, rest in (("exports", EXP_GROUPS, EXP_REST), ("imports", IMP_GROUPS, IMP_REST)):
        g23 = pd.concat([_psa_wide(f, "At Current Prices 2023") for f in TRADE_FILES[flow]])
        g18 = pd.concat([_psa_wide(f, "At Current Prices 2018") for f in TRADE_FILES[flow]])
        gr = {}
        for cs, labels in groups.items():
            miss = [x for x in labels if x not in g23.index]
            if miss:
                raise ValueError(f"PSA {flow} lines not found: {miss}")
            ratio = float(g23[labels].sum() / g18[labels].sum())
            gr.update({c: ratio for c in cs})
            rows[(flow, "+".join(cs))] = {"PSA 2018": float(g18[labels].sum()), "PSA 2023": float(g23[labels].sum()), "growth": ratio,
                                          "PSA lines": "; ".join(labels)}
        for kind, labels in rest.items():
            ratio = float(g23[labels].sum() / g18[labels].sum())
            rows[(flow, f"other {kind}")] = {"PSA 2018": float(g18[labels].sum()), "PSA 2023": float(g23[labels].sum()),
                                            "growth": ratio, "PSA lines": "; ".join(labels)}
            gr[f"other {kind}"] = ratio
        out[flow] = gr
    out["groups"] = pd.DataFrame(rows).T
    return out


def trade_factor(gr: dict, c: str) -> float:
    """Growth factor of commodity c from trade_growth()'s dict for one flow."""
    return gr.get(c, gr["other goods"] if c in GOODS else gr["other services"])


BSP_BOP_DIR = "macro/BSP_BOP_IIP_downloaded_2026-10-18"
BSP_LINES = {   # sensitivity "0.6b": BSP's BPM6 balance of payments 2023 (Tables 1.3 and 1.4, annual, US$ million, saved 18 Oct 2026)
    "A.1.C.3.1": "compensation of employees, receipts", "A.1.C.3.2": "compensation of employees, payments",
    "A.1.C.4.1": "investment income, receipts", "A.1.C.4.2": "investment income, payments",
    "A.1.D.3.1": "general government transfers, receipts", "A.1.D.3.2": "general government transfers, payments",
    "A.1.D.4.3.1": "personal transfers, receipts", "A.1.D.4.3.2": "personal transfers, payments",
    "A.1.D.4.4.1": "other current transfers, receipts", "A.1.D.4.4.2": "other current transfers, payments"}


def bsp_bop_2023() -> pd.Series:
    """Sensitivity '0.6b': BSP's 2023 primary and secondary income lines (BPM6), ₱ bn at the 2023 average of BIS's monthly
    PHP per USD (as tools/sam_row_vs_bsp_bop.py)."""
    import openpyxl
    out = {}
    for fn in ("Table1.3.xlsx", "Table1.4.xlsx"):
        ws = openpyxl.load_workbook(paths.DATA_RAW / BSP_BOP_DIR / fn, read_only=True, data_only=True)["Annual"]
        rows = list(ws.iter_rows(values_only=True))
        hdr = next(r for r in rows if r and any(str(v).strip() == "2023" for v in r if v is not None))
        j = [i for i, v in enumerate(hdr) if v is not None and str(v).strip() == "2023"][0]
        for r in rows:
            lab = next((str(c).strip() for c in r if isinstance(c, str) and str(c).strip().startswith("A.1.")), "")
            code = lab.split()[0] if lab else ""
            if code in BSP_LINES and isinstance(r[j], (int, float)):
                out[BSP_LINES[code]] = float(r[j])
    if len(out) != len(BSP_LINES):
        raise ValueError(f"BSP lines not found: {set(BSP_LINES.values()) - set(out)}")
    fx = pd.read_csv(paths.DATA_RAW / "macro" / "BIS_WS_XRU_PHP_per_USD_monthly_average.csv", comment="#")
    rate = float(fx[fx["month"].str.startswith("2023")]["value"].mean())
    return pd.Series(out) * rate / 1e3


def rest_of_world_and_government(t0: pd.DataFrame, t78: pd.DataFrame, H: list, fg6: pd.DataFrame, pit: pd.Series,
                                 bop: bool = False) -> pd.DataFrame:
    """Version 0.6: the rest-of-world and government cells of the prior from PSA's 2023 integrated accounts (external
    transactions 0042B5BCA04; general government 0072B5BIO03; households 0082B5BIO04; non-financial and financial corporations
    0052B5BIO01, 0062B5BIO02), with FIES 2023 shares across household groups. These cells are then fixed (or, for receipts
    from abroad, controlled) in the balancing, as v0.5 fixed IFPRI's. Taxes on products stay BESF's (tax_block). Returns the
    source table (₱ bn)."""
    S = psa_sector_accounts_2023()
    row, gg, hh, nfc, fc = S["row"], S["gg"], S["hh"], S["nfc"], S["fc"]
    L = list(P.LABOUR)
    share = lambda col: fg6[col].reindex(H) / float(fg6[col].reindex(H).sum())
    doc = {}

    def put(r, c, v, src):
        before = float(t0.loc[r, c].values.sum()) if isinstance(r, list) or isinstance(c, list) else float(t0.loc[r, c])
        t0.loc[r, c] = v
        after = float(t0.loc[r, c].values.sum()) if isinstance(r, list) or isinstance(c, list) else float(t0.loc[r, c])
        name = f"{r if isinstance(r, str) else 'households'} <- {c if isinstance(c, str) else 'households'}"
        if isinstance(r, list) and r == L or isinstance(c, list) and c == L:
            name = name.replace("households", "labour")
        doc[name] = {"v0.5 prior (IFPRI via the PSA-consistent SAM)": before, "v0.6": after, "source": src}

    # rest of the world (PSA's external account, consistent with PSA's exports and imports, which the SAM already uses)
    if bop:     # sensitivity '0.6b': BSP's BPM6 amounts (most OFW income is a personal transfer there), same layout
        b = bsp_bop_2023()
        rw = {"coe_out": b["compensation of employees, payments"], "coe_in": b["compensation of employees, receipts"],
              "hh_in": b["personal transfers, receipts"], "prop_in": b["investment income, receipts"],
              "prop_out": b["investment income, payments"], "ent_in": b["other current transfers, receipts"],
              "gov_in": b["general government transfers, receipts"], "ent_out": b["other current transfers, payments"],
              "gov_out": b["general government transfers, payments"], "hh_out": b["personal transfers, payments"]}
        src = "BSP BPM6 BOP 2023 (Tables 1.3-1.4) at BIS's 2023 average rate"
    else:
        rw = {"coe_out": row["Compensation of employees to ROW"], "coe_in": row["Compensation of employees from ROW"],
              "hh_in": row["To households"], "prop_in": row["Property income from ROW"], "prop_out": row["Property income to ROW"],
              "ent_in": row["To other institutional sectors"], "gov_in": row["To general government"],
              "ent_out": row["From other institutional sectors"], "gov_out": row["From general government"],
              "hh_out": row["From households"]}
        src = "PSA 0042B5BCA04"
    rw = {k: float(v) for k, v in rw.items()}
    put("row", L, rw["coe_out"] * (t78.loc["row", L] / t78.loc["row", L].sum()).values,
        f"{src} compensation of employees to ROW (skill split as IFPRI's)")
    put(L, "row", 0.0, "none: compensation from ROW (OFWs) goes to households directly (next lines)")
    put(H, "row", (rw["coe_in"] + rw["hh_in"]) * share("CASH_ABROAD").values,
        f"{src} compensation of employees from ROW + current transfers to households; FIES CASH_ABROAD shares")
    put("fcap", "row", rw["prop_in"], f"{src} property income from ROW")
    put("row", "fcap", rw["prop_out"], f"{src} property income to ROW")
    put("ent", "row", rw["ent_in"], f"{src} current transfers from ROW to other sectors")
    put("gov", "row", rw["gov_in"], f"{src} current transfers from ROW to general government")
    put("row", "ent", rw["ent_out"], f"{src} current transfers to ROW from corporations")
    put("row", "gov", rw["gov_out"], f"{src} current transfers to ROW from general government")
    put("row", H, rw["hh_out"] * share("TOTEX").values, f"{src} current transfers to ROW from households; FIES TOTEX shares")
    # general government (PSA's income and outlay account), households' and corporations' payments to it
    gg_other_net = float(gg["Other current transfers (Use of Income)"]) - float(row["From general government"]) - (
        float(gg["Other current transfers (Income)"]) - float(row["To general government"]))
    put(H, "gov", (float(gg["Social benefits other than in kind"]) + gg_other_net) * share("government transfers").values,
        "PSA 0072B5BIO03 social benefits + other current transfers to domestic sectors, net; FIES PENSION + CASH_DOMESTIC shares")
    put("ent", "gov", float(gg["Property expense"]) + float(gg["Subsidies"]), "PSA 0072B5BIO03 property expense (interest) + subsidies")
    put("gov", "ent", float(gg["Property income"]) + float(nfc["Compulsory fees and fines"]) + float(fc["Compulsory fees and fines"])
        + float(gg["Gross operating surplus*"]),
        "PSA 0072B5BIO03 property income + corporations' fees and fines (0052B5BIO01, 0062B5BIO02) + government's own operating surplus")
    put("gov", H, float(hh["Social contributions"]) * share("WAGES").values + float(hh["Compulsory fees and fines"]) * share("TOTEX").values,
        "PSA 0082B5BIO04 social contributions (FIES WAGES shares) + compulsory fees and fines (FIES TOTEX shares)")
    put("dtax", "ent", float(nfc["Current taxes on income and wealth, etc."]) + float(fc["Current taxes on income and wealth, etc."])
        - float(t0.loc["ftax", "fcap"]),
        "PSA 0052B5BIO01 + 0062B5BIO02 current taxes on income and wealth, less the factor tax kept from IFPRI (GFS taxes on property)")
    put("dtax", H, float(hh["Taxes on income and wealth"]) * pit.reindex(H).values,
        "PSA 0082B5BIO04 taxes on income and wealth; shares: TRAIN 2023 schedule on FIES-LFS 2023 wage earners (pit_shares)")
    put("gov", "dtax", float(t0.loc["dtax"].sum()), "the direct-tax account's receipts")
    if bop:     # the current-account balance with PSA's trade and BSP's income flows (a deficit)
        cab = (float(row["Exports of goods and services"]) - float(row["Imports of goods and services"])
               + rw["coe_in"] + rw["prop_in"] + rw["hh_in"] + rw["ent_in"] + rw["gov_in"]
               - rw["coe_out"] - rw["prop_out"] - rw["ent_out"] - rw["gov_out"] - rw["hh_out"])
        put("s-i", "row", -cab, "BSP BPM6 income flows with PSA's exports and imports: prior only, balanced by the cross-entropy")
    else:
        put("s-i", "row", -float(row["Current external balance"]), "PSA 0042B5BCA04 current external balance (net lending abroad): "
            "prior only, balanced by the cross-entropy")
    return pd.DataFrame(doc).T


def household_capital_and_saving(t0: pd.DataFrame, A: list, H: list, fg6: pd.DataFrame, hh_lab: pd.DataFrame, hfce: float,
                                 sav_total: float, gfce: float) -> pd.DataFrame:
    """Version 0.6: households' saving by group (fixed in the balancing: FIES 2023 saving shares x v0.5's household saving
    total) and the priors of the cells the balancing then solves for: land and farm capital income paid to each group (FIES
    shares of crop and farm income, totals from the prior; ratio controls in build), enterprises' payouts (the balancing item
    of each household account), enterprise, government and foreign saving. Returns the household table (₱ bn)."""
    AG = [a for a in PSA_INDUSTRIES["Agriculture, forestry, and fishing"] if a in t0.columns]
    sh = lambda col: fg6[col].reindex(H) / float(fg6[col].reindex(H).sum())
    t0.loc["s-i", H] = (sav_total * sh("saving")).values
    cons = hfce * sh("TOTEX")
    pay = cons + t0.loc["gov", H] + t0.loc["dtax", H] + t0.loc["row", H] + t0.loc["s-i", H]
    rec = hh_lab.loc[H].sum(axis=1) + t0.loc[H, "gov"] + t0.loc[H, "row"]
    k_h = pay - rec                                                   # capital-type income each group needs
    land, agk = float(t0.loc["flnd", A].sum()), float(t0.loc["fcap", AG].sum())
    t0.loc[H, "flnd"] = (land * sh("crop income")).values
    t0.loc[H, "fcap"] = (agk * sh("farm income")).values
    ent_h = k_h - t0.loc[H, "flnd"] - t0.loc[H, "fcap"]
    if (ent_h <= 0).any():
        raise ValueError(f"v0.6: enterprise payouts would be negative for {list(ent_h[ent_h <= 0].index)}")
    t0.loc[H, "ent"] = ent_h.values
    fcap_in = float(t0.loc["fcap", A].sum() + t0.loc["fcap", "row"])
    t0.loc["ent", "fcap"] = fcap_in - float(t0.loc[H, "fcap"].sum() + t0.loc["row", "fcap"] + t0.loc["ftax", "fcap"])
    t0.loc["s-i", "ent"] = 0.0                                        # priors of the savings: receipts less other payments
    t0.loc["s-i", "ent"] = float(t0.loc["ent"].sum()) - float(t0.loc[:, "ent"].sum())
    inst_rows = [r for r in t0.index if r[0] not in "ca"]            # commodity and activity codes start with c and a
    t0.loc["s-i", "gov"] = 0.0
    t0.loc["s-i", "gov"] = float(t0.loc["gov"].sum()) - gfce - float(t0.loc[inst_rows, "gov"].sum())
    if float(t0.loc["s-i", "ent"]) <= 0 or float(t0.loc["ent", "fcap"]) <= 0:
        raise ValueError("v0.6: enterprise income or saving prior is not positive")
    return pd.DataFrame({"consumption (FIES TOTEX shares x PSA HFCE)": cons, "labour income": hh_lab.loc[H].sum(axis=1),
                         "from government": t0.loc[H, "gov"], "from abroad": t0.loc[H, "row"],
                         "capital-type income needed": k_h, "land (FIES crop income shares)": t0.loc[H, "flnd"],
                         "farm capital (FIES farm income shares)": t0.loc[H, "fcap"], "enterprise payouts (prior)": t0.loc[H, "ent"],
                         "direct taxes": t0.loc["dtax", H], "to government": t0.loc["gov", H],
                         "saving (FIES saving shares x v0.5 total)": t0.loc["s-i", H]})


# ------------------------------------------------------------------------------------------------------------------------------
# Version '0.6e' (23 Oct 2026; RESEARCH, NOT the default; everything else as v0.6): electricity's
# fuel mix. Evidence: research/electricity_fuel_mix/fuel_mix_evidence.py (outputs/electricity_fuel_mix_evidence_*.csv):
#   PSA's 2018 Use table books the electricity industry's fuel (₱147.6 bn, 19.8% of its output) as refined petroleum ₱107.4 bn,
#   natural gas ₱30.2 bn and coal ₱10.0 bn, while DOE's 2018 gross generation was 52% coal, 21% gas and 3% oil-based (3,173
#   GWh). ₱107 bn of oil products for 3,173 GWh is ₱34 per kWh, or ₱136 per kilogram of oil equivalent burnt, about five
#   times the 2018 crude price per kilogram. PSA's coal row sends ₱100.7 bn of its ₱128.3 bn of intermediate coal (78%) to
#   basic iron and steel, which used 2% of the country's coal in GTAP 10A's IEA-based 2014 energy volumes (power plants 80%).
#   PSA's 240-industry I-O, the prior here (io_2018), is the Use table under the fixed product-sales structure (T = D U, to
#   1e-9), so it also moves 48% of electricity's natural gas and 27% of its coal into the refined-petroleum row: PSA's Supply
#   table credits the refining industry with those shares of the domestic production of gas and coal.
# Correction: electricity's oil products (cpetr) = the DOE/IEA-consistent 2023 oil bill (electricity_oil_2023); the rest of
#   its fuel bill in the prior (cpetr + cmine: PSA's 2018 fuel cost share, kept) becomes coal and gas (cmine). The fuel that
#   changes account is imported: cmine imports rise and cpetr imports fall by the same amount, so PSA's controlled total of
#   fuel and ore imports is unchanged (the split of fuel imports between the two accounts is the 2018 I-O's, grown by one
#   common factor, not a PSA 2023 figure). No other industry's inputs change in the prior. Two balancing controls then hold
#   electricity's oil products at that bill and its whole fuel bill (cpetr + cmine) at v0.6's balanced value, so v0.6e
#   differs from v0.6 in the fuel MIX, not in the size of the fuel bill (left free, the balancing scaled the larger cmine cell
#   up to a fuel bill ₱49 bn above v0.6's; first build, 23 Oct 2026, 7:02 PM). PSA's coal booked in basic iron and steel stays.
# Version '0.5e' (23 Oct 2026, evening; RESEARCH, opt-in): the same correction on v0.5 alone (electricity_fuel_mix with
#   base "0.5"; build adds a third control, the imports of cpetr + cmine at v0.5's, since v0.5 has no trade-by-product controls).
# ------------------------------------------------------------------------------------------------------------------------------
ELEC_FUEL_INPUTS = "electricity_fuel_mix_inputs_2014-2023.csv"   # data/processed; research/electricity_fuel_mix/fuel_mix_evidence.py


def electricity_oil_2023() -> dict:
    """Version '0.6e': oil products bought by power plants in 2023, ₱ bn at purchasers' prices = DOE's 2023
    oil-based generation (grid, 1,304 GWh, plus off-grid estimated as DOE's 2020 oil-based generation, which includes
    off-grid, less 2021's, which does not: 858 GWh) x GTAP 10A 2014's oil products per MWh of oil-based generation (IEA
    volumes / DOE 2014 generation: 0.248 toe) x GTAP 2014's unit value at agents' prices (US$782 per toe) x Dubai crude
    2023 / 2014 (World Bank Pink Sheet) x pesos per US dollar 2023 (BIS). Inputs: data/processed/ELEC_FUEL_INPUTS (DOE
    2025 Power Statistics and the GTAP 10A package, one row per number with its source) and data/raw/macro."""
    d = pd.read_csv(paths.DATA_PROCESSED / ELEC_FUEL_INPUTS, comment="#").set_index("key")["value"]
    gen = lambda typ, y: float(d[f"DOE gross generation {typ} {y}"])
    oil_mtoe, oil_usd = (float(d[f"GTAP 10A 2014 Philippines ely oil products {k}"]) for k in ("Mtoe", "US$m"))

    def annual(fname: str, col: str, y: int) -> float:
        x = pd.read_csv(paths.DATA_RAW / "macro" / fname, comment="#")
        return float(x.loc[x["month"].astype(str).str.startswith(str(y)), col].mean())
    dubai = {y: annual("WorldBank_PinkSheet_crude_oil_monthly_1960-2026.csv", "crude_dubai_usd_bbl", y) for y in (2014, 2023)}
    fx = annual("BIS_WS_XRU_PHP_per_USD_monthly_average.csv", "value", 2023)
    offgrid = gen("Oil-Based", 2020) - gen("Oil-Based", 2021)
    gwh = gen("Oil-Based", 2023) + offgrid
    toe_mwh = oil_mtoe * 1e6 / (gen("Oil-Based", 2014) * 1e3)
    php_toe = oil_usd / oil_mtoe * dubai[2023] / dubai[2014] * fx
    return {"oil-based generation 2023, grid (GWh)": gen("Oil-Based", 2023), "off-grid oil-based estimate (GWh)": offgrid,
            "toe of oil products per MWh (GTAP 2014 / DOE 2014)": toe_mwh, "US$ per toe 2014 (GTAP, agents' prices)": oil_usd / oil_mtoe,
            "Dubai crude 2023 / 2014": dubai[2023] / dubai[2014], "pesos per US$ 2023": fx, "₱ per toe 2023": php_toe,
            "oil products bought by power plants 2023 (₱ bn)": gwh * 1e3 * toe_mwh * php_toe / 1e9,
            "coal share of gross generation 2023": gen("Coal", 2023) / gen("Total Gross Generation", 2023),
            "gas share of gross generation 2023": gen("Natural Gas", 2023) / gen("Total Gross Generation", 2023),
            "oil share of gross generation 2023 (with the off-grid estimate)": gwh / (gen("Total Gross Generation", 2023) + offgrid)}


def electricity_fuel_mix(t0: pd.DataFrame, base: str = "0.6") -> dict:
    """Version '0.6e': in the prior, electricity's oil products (cpetr) = electricity_oil_2023() and the rest of its
    fuel bill (cpetr + cmine) = coal and gas (cmine); the fuel that changes account is imported (cmine imports up, cpetr
    imports down by the same amount: PSA's controlled import total of the two accounts is unchanged). Returns the prior's
    before/after table (₱ bn), the targets of build's two balancing controls (electricity's oil products = the 2023 oil bill;
    its fuel bill = v0.6's balanced value, read from the v0.6 file) and the inputs.
    Version '0.5e': base="0.5" does the same on v0.5's prior, with v0.5's balanced fuel bill; the result also
    carries the base file's imports of cpetr + cmine, which build holds in 0.5e. base="0.6" (the default) is 0.6e as built."""
    o = electricity_oil_2023()
    v6 = paths.sam_own(base)
    if not v6.exists():
        raise FileNotFoundError(f"v{base}e holds electricity's fuel bill at v{base}'s: build v{base} first ({v6.name})")
    t6 = SAM.load(v6).table
    fuel6 = float(t6.loc["cpetr", "aelec"] + t6.loc["cmine", "aelec"])
    p0, m0, i0, j0 = (float(t0.loc[r, c]) for r, c in (("cpetr", "aelec"), ("cmine", "aelec"), ("row", "cpetr"), ("row", "cmine")))
    oil = o["oil products bought by power plants 2023 (₱ bn)"]
    if not 0.0 < oil < p0:
        raise ValueError(f"v{base}e: electricity's oil bill {oil:.1f} is not between 0 and the prior's {p0:.1f} (₱ bn)")
    move = p0 - oil
    t0.loc["cpetr", "aelec"], t0.loc["cmine", "aelec"] = oil, m0 + move
    t0.loc["row", "cpetr"], t0.loc["row", "cmine"] = i0 - move, j0 + move
    if float(t0.loc["row", "cpetr"]) <= 0.0:
        raise ValueError(f"v{base}e: imports of refined petroleum would turn negative")
    tab = pd.DataFrame({f"prior as in v{base}": [p0, m0, p0 + m0, i0, j0], f"prior, v{base}e": [oil, m0 + move, p0 + m0, i0 - move, j0 + move]},
                       index=["electricity buys oil products (cpetr)", "electricity buys coal, gas and other mining (cmine)",
                              "electricity's fuel bill (cpetr + cmine)", "imports of cpetr", "imports of cmine"])
    return {"table": tab, "oil share": oil / (p0 + m0), "moved (₱ bn, prior)": move, "inputs": o,
            "targets": {"cpetr": oil, "cmine": fuel6 - oil}, f"fuel bill v{base} (₱ bn)": fuel6,
            f"imports of cpetr + cmine v{base} (₱ bn)": float(t6.loc["row", ["cpetr", "cmine"]].sum())}


# ------------------------------------------------------------------------------------------------------------------------------
# Version '0.7' (24 Oct 2026; RESEARCH, opt-in, NOT the default; VERSION stays "0.5"): v0.5e with coal split out of the
# mining account into its own activity and commodity. In v0.5e coal is inside mining (amine, cmine) with crude oil, natural gas
# and ores, so infinity_gem.oil.cge_oil_shock raises the import price of that coal at crude's share, and coal prices cannot be
# shocked on their own. v0.7 splits every cell of the mining activity's and commodity's rows and columns into coal (acoal,
# ccoal) and the rest (amine, cmine); every other cell is v0.5e's, and acoal + amine and ccoal + cmine give v0.5e back (to
# rounding), so v0.5e's balance and all its PSA and FIES controls hold. The coal part of each cell (coal_split):
#   users of mining products: PSA's 2018 240-industry I-O (Table C.1, the table and concordance the prior was built from,
#     io_2018): the coal-mining industry's row (39) over the mining rows (39-45) in each SAM user's columns; final demand
#     (households, government, investment, stock change, exports) likewise from the I-O's final-demand columns;
#   electricity (aelec): v0.5e's mining purchases (its fuel bill less oil, electricity_fuel_mix) less natural gas
#     (electricity_gas_2023) and less other mining products (the I-O's rows 41-45 share of electricity's mining purchases, on
#     v0.5's): the coal that DOE's 2023 coal-fired generation burns;
#   coal mining (acoal): the I-O's coal-mining column (39) over the mining columns (39-45): gross output, inputs by commodity,
#     compensation (one share for the three skill levels); capital income closes the column; acoal makes only ccoal (a
#     diagonal make, as every SAM activity);
#   supply: imports = v0.5's mining imports x the I-O's coal share of mining imports (row 39 of the imports column) + v0.5e's
#     extra mining imports (the electricity correction moved them out of refined oil: the power plants' coal and, for a small
#     part, gas), so the imports of the rest of mining (crude oil, gas, ores) stay at v0.5's in pesos, and crude's share of them
#     is PSA's 2018 share of non-coal mining imports (infinity_gem.oil.import_shares); trade margins and taxes on products in
#     proportion to coal's share of the mining composite (domestic sales + imports);
#   basic metals (ametl) take the difference, so that the coal account balances: PSA's 2018 tables book 78.5% of intermediate
#     coal in basic iron and steel against 2% in GTAP 10A's IEA-based 2014 volumes (a review note (not included), 1(c)), the least reliable coal cell. At the I-O's share metals would buy more coal than
#     the coal account's supply leaves: v0.5e keeps PSA's coal in basic metals AND adds the power plants' coal to mining
#     imports, so part of its coal is counted twice (the build reports both figures).
# Not changed (open, as in v0.5e): the coal and gas inside the refined-petroleum row (PSA's I-O credits the refining industry
# with 27% of domestic coal and 48% of domestic crude oil and gas, so those shares of their flows sit in cpetr).
# ------------------------------------------------------------------------------------------------------------------------------
COAL_IO, MINING_IO, ELECTRICITY_IO = 39, tuple(range(39, 46)), (172, 173)   # PSA 240-industry codes (psa_activity)
COAL_LABELS = {"acoal": "Activities - Coal and lignite mining (split from mining; Infinity GEM SAM v0.7)",
               "ccoal": "Commodities - Coal and lignite (split from mining; Infinity GEM SAM v0.7)"}
FD_IO = {"gov": "gfce", "s-i": "gcf", "dstk": "inv", "row": "exp"}   # SAM final-demand column -> PSA I-O final-demand column


def _annual(fname: str, col: str, y: int) -> float:
    """Version '0.7': the mean of year y in a monthly file of data/raw/macro (Pink Sheet crude oil, BIS pesos per US$)."""
    x = pd.read_csv(paths.DATA_RAW / "macro" / fname, comment="#")
    return float(x.loc[x["month"].astype(str).str.startswith(str(y)), col].mean())


def coal_io_2018() -> dict:
    """Version '0.7': coal's part of the mining flows in PSA's 2018 240-industry I-O (Table C.1; the table and concordance of
    io_2018), ₱ bn: by SAM user, the coal-mining row (39) and the mining rows (39-45); by SAM input row, the coal-mining column
    and the mining columns; mining's purchases from mining split four ways (coal or the rest, bought by coal mining or the
    rest); gross output, compensation, final demand and imports of coal and of all mining; electricity's purchases of other
    mining products and of all mining."""
    from build_sam_petroleum_split import load_psa, psa_activity
    T, fd, va = load_psa()
    act = [("amric" if k == 57 else "apetr" if k in (107, 108) else psa_activity(k)) for k in range(1, 241)]
    com = ["c" + a[1:] for a in act]
    K, M, E = COAL_IO - 1, [k - 1 for k in MINING_IO], [k - 1 for k in ELECTRICITY_IO]
    R = [k for k in M if k != K]                                       # crude oil and gas, ores, quarrying: codes 40-45
    O = [k for k in R if k != K + 1]                                   # other mining products: codes 41-45
    if {act[k] for k in M} != {"amine"} or {act[k] for k in E} != {"aelec"}:
        raise ValueError("v0.7: PSA codes 39-45 must be mining (amine) and 172-173 electricity (aelec) in the concordance")
    by = lambda v, ix: pd.Series(v / 1e3, index=ix).groupby(level=0).sum()
    X = T.sum(axis=0) + va["COE"] + va["GOS"] + va["T-S"]
    fdk = {k: abs(float(v[K])) / 1e3 if k == "imp" else float(v[K]) / 1e3 for k, v in fd.items()}
    fdm = {k: abs(float(v[M].sum())) / 1e3 if k == "imp" else float(v[M].sum()) / 1e3 for k, v in fd.items()}
    return {"rows": pd.DataFrame({"coal": by(T[K, :], act), "mining": by(T[M, :].sum(axis=0), act)}),
            "columns": pd.DataFrame({"coal (column 39)": by(T[:, K], com), "mining (columns 39-45)": by(T[:, M].sum(axis=1), com)}),
            "mining block": pd.Series({("ccoal", "acoal"): T[K, K], ("cmine", "acoal"): T[R, K].sum(),
                                       ("ccoal", "amine"): T[K, R].sum(), ("cmine", "amine"): T[np.ix_(R, R)].sum()}) / 1e3,
            "final demand": pd.DataFrame({"coal": fdk, "mining": fdm}),
            "output": (float(X[K]) / 1e3, float(X[M].sum()) / 1e3),
            "compensation": (float(va["COE"][K]) / 1e3, float(va["COE"][M].sum()) / 1e3),
            "electricity: other mining, all mining": (float(T[np.ix_(O, E)].sum()) / 1e3, float(T[np.ix_(M, E)].sum()) / 1e3)}


def electricity_gas_2023() -> dict:
    """Version '0.7': natural gas bought by power plants in 2023, ₱ bn = PSA's 2018 Use table (the electricity industry, 172,
    buys crude petroleum and natural gas, product 040: gas for power) x DOE's gas-fired gross generation 2023 / 2018 x Dubai
    crude 2023 / 2018 x pesos per US$ 2023 / 2018 (data/processed/ELEC_FUEL_INPUTS; data/raw/macro). The gas price follows crude
    oil (gas sold under oil-linked contracts): an ASSUMPTION; held constant in US$ instead, the bill is lower (both reported)."""
    d = pd.read_csv(paths.DATA_PROCESSED / ELEC_FUEL_INPUTS, comment="#").set_index("key")["value"]
    gas18 = float(d["PSA 2018 Use table: electricity (172) buys crude petroleum and natural gas (040)"])
    gen = float(d["DOE gross generation Natural Gas 2023"]) / float(d["DOE gross generation Natural Gas 2018"])
    crude = "WorldBank_PinkSheet_crude_oil_monthly_1960-2026.csv", "crude_dubai_usd_bbl"
    peso = "BIS_WS_XRU_PHP_per_USD_monthly_average.csv", "value"
    dub = _annual(*crude, 2023) / _annual(*crude, 2018)
    fx = _annual(*peso, 2023) / _annual(*peso, 2018)
    return {"PSA 2018 Use table: gas bought by electricity (₱ bn)": gas18, "DOE gas-fired generation 2023 / 2018": gen,
            "Dubai crude 2023 / 2018": dub, "pesos per US$ 2023 / 2018": fx, "gas bought by power plants 2023 (₱ bn)": gas18 * gen * dub * fx,
            "the same with the gas price constant in US$ (₱ bn; not used)": gas18 * gen * fx}


def coal_split(t: pd.DataFrame, t5: pd.DataFrame) -> tuple:
    """Version '0.7': v0.5e's table t with the mining activity and commodity split into coal (acoal, ccoal) and the rest
    (amine, cmine), as described above; t5 = v0.5's table (its mining imports and electricity's mining purchases). Returns
    the new table (acoal after amine, ccoal after cmine; every other cell is t's) and a dict of tables for the report."""
    io, gas = coal_io_2018(), electricity_gas_2023()
    codes = list(t.index)
    new = [y for c in codes for y in ((c, "acoal") if c == "amine" else (c, "ccoal") if c == "cmine" else (c,))]
    x = t.reindex(index=new, columns=new, fill_value=0.0)
    H = [c for c in codes if c.startswith("hhd")]
    rows, fdm = io["rows"], io["final demand"]
    sh_fd = lambda k: float(fdm.loc[k, "coal"] / fdm.loc[k, "mining"])
    e_oth, e_all = io["electricity: other mining, all mining"]
    gas23 = gas["gas bought by power plants 2023 (₱ bn)"]
    other_el = e_oth / e_all * float(t5.loc["cmine", "aelec"])
    # 1. the mining commodity's row: coal bought by each user
    coal, basis = {}, {}
    for j in [c for c in codes if float(t.loc["cmine", c]) != 0.0]:
        v = float(t.loc["cmine", j])
        if j in ("amine", "ametl"):
            continue                                                   # the mining block and the balancing cell (below)
        if j == "aelec":
            coal[j], basis[j] = v - gas23 - other_el, "v0.5e's fuel bill less gas and other mining (DOE generation)"
        elif j in H:
            coal[j], basis[j] = v * sh_fd("hfce"), "PSA I-O 2018, household consumption"
        elif j in FD_IO:
            coal[j], basis[j] = v * sh_fd(FD_IO[j]), f"PSA I-O 2018, final demand ({FD_IO[j]})"
        elif j in rows.index:
            r = rows.loc[j]
            coal[j] = v * (float(r["coal"] / r["mining"]) if r["mining"] > 0 else 0.0)
            basis[j] = "PSA I-O 2018, coal-mining row over the mining rows"
        else:
            raise ValueError(f"v0.7: mining purchases by {j} have no coal share")
    blk = io["mining block"] / float(io["mining block"].sum())
    cell = {k: float(t.loc["cmine", "amine"]) * float(s) for k, s in blk.items()}   # mining buys from mining, four ways
    # 2. the mining commodity's column: supply of coal
    out_m = float(t.loc["amine"].sum())
    if abs(out_m - float(t.loc["amine", "cmine"])) > 1e-9 * out_m:
        raise ValueError("v0.7: the mining activity sells other than to its commodity (e.g. home consumption): not handled")
    if set(c for c in codes if float(t.loc[c, "cmine"]) != 0.0) - {"amine", "row", "trc", "stax", "mtax"}:
        raise ValueError("v0.7: the mining commodity's column has rows other than make, imports, margins and taxes")
    dom = out_m * io["output"][0] / io["output"][1]                     # coal mining's output (all of it coal)
    imp5, imp = float(t5.loc["row", "cmine"]), float(t.loc["row", "cmine"])
    imp_k = imp5 * sh_fd("imp") + (imp - imp5)
    comp = (dom - coal["row"] + imp_k) / (out_m - float(t.loc["cmine", "row"]) + imp)   # coal's share of the composite
    sup = {"acoal": dom, "row": imp_k, **{r: float(t.loc[r, "cmine"]) * comp for r in ("trc", "stax", "mtax")
                                          if r in t.index and float(t.loc[r, "cmine"]) != 0.0}}
    r_m = rows.loc["ametl"]
    metals_io = float(t.loc["cmine", "ametl"]) * float(r_m["coal"] / r_m["mining"])
    coal["ametl"] = sum(sup.values()) - sum(coal.values()) - cell[("ccoal", "acoal")] - cell[("ccoal", "amine")]
    basis["ametl"] = "the balancing cell: coal supply less every other coal purchase"
    if not 0.0 <= coal["ametl"] <= float(t.loc["cmine", "ametl"]):
        raise ValueError(f"v0.7: basic metals' coal would be {coal['ametl']:.2f} (its mining purchases {t.loc['cmine', 'ametl']:.2f})")
    # 3. the mining activity's column: coal mining's inputs and factors
    cols = io["columns"]
    lab_sh = io["compensation"][0] / io["compensation"][1]
    col = {}
    for i in [c for c in codes if float(t.loc[c, "amine"]) != 0.0 and c not in ("cmine", "fcap")]:
        v = float(t.loc[i, "amine"])
        if i in P.LABOUR:
            col[i] = v * lab_sh
        elif i.startswith("c") and i in cols.index:
            c_ = cols.loc[i]
            col[i] = v * (float(c_["coal (column 39)"] / c_["mining (columns 39-45)"]) if c_["mining (columns 39-45)"] > 0 else 0.0)
        elif i.startswith("c"):
            col[i] = 0.0
        else:
            raise ValueError(f"v0.7: row {i} of the mining activity's column is not handled")
    col["fcap"] = dom - sum(col.values()) - cell[("ccoal", "acoal")] - cell[("cmine", "acoal")]
    if not 0.0 < col["fcap"] < float(t.loc["fcap", "amine"]):
        raise ValueError(f"v0.7: coal mining's capital income would be {col['fcap']:.2f}")
    # 4. write the split: coal into the new accounts, the rest stays in amine and cmine
    for j, val in coal.items():
        x.loc["ccoal", j], x.loc["cmine", j] = val, float(t.loc["cmine", j]) - val
    for (r, c), val in cell.items():
        x.loc[r, c] = val
    x.loc["acoal", "ccoal"], x.loc["amine", "cmine"] = dom, float(t.loc["amine", "cmine"]) - dom
    for r, val in sup.items():
        if r != "acoal":
            x.loc[r, "ccoal"], x.loc[r, "cmine"] = val, float(t.loc[r, "cmine"]) - val
    for i, val in col.items():
        x.loc[i, "acoal"], x.loc[i, "amine"] = val, float(t.loc[i, "amine"]) - val
    # 5. checks: balance, v0.5e back on aggregation, no sign change
    back = SAM(x).aggregate({"acoal": "amine", "ccoal": "cmine"}).table.loc[codes, codes]
    gap_back = float((back - t).abs().values.max())
    gap_bal = float(np.abs(x.values.sum(axis=1) - x.values.sum(axis=0)).max())
    agg_of = lambda c: "amine" if c == "acoal" else "cmine" if c == "ccoal" else c
    four = ("acoal", "amine", "ccoal", "cmine")
    flip = [(r, c) for r, c in [(r, c) for r in four for c in new] + [(r, c) for r in new for c in four]
            if float(x.loc[r, c]) * float(t.loc[agg_of(r), agg_of(c)]) < 0.0]
    if gap_back > 1e-9 or gap_bal > 1e-8 or flip:
        raise ValueError(f"v0.7: split fails its checks (aggregation {gap_back:.1e}, balance {gap_bal:.1e}, sign changes {flip[:5]})")
    # 5b. tables for the report
    users = pd.DataFrame({"v0.5e mining (cmine)": {j: float(t.loc["cmine", j]) for j in list(coal) + ["amine"]},
                          "coal (ccoal)": {**coal, "amine": cell[("ccoal", "acoal")] + cell[("ccoal", "amine")]},
                          "basis": {**basis, "amine": "PSA I-O 2018, mining block (coal mining and the rest buy coal and the rest)"}})
    users["rest (cmine)"] = users["v0.5e mining (cmine)"] - users["coal (ccoal)"]
    users["coal share"] = users["coal (ccoal)"] / users["v0.5e mining (cmine)"]
    users = users[["v0.5e mining (cmine)", "coal (ccoal)", "rest (cmine)", "coal share", "basis"]]
    supply = pd.DataFrame({"v0.5e mining (cmine)": {r: float(t.loc["amine" if r == "acoal" else r, "cmine"]) for r in sup},
                           "coal (ccoal)": sup,
                           "basis": {"acoal": "PSA I-O 2018: coal mining's share of mining output", "row": "v0.5's mining imports x the I-O's coal "
                                     "share of mining imports + v0.5e's extra mining imports", **{r: "coal's share of the mining composite "
                                     "(domestic sales + imports)" for r in sup if r not in ("acoal", "row")}}})
    supply["rest (cmine)"] = supply["v0.5e mining (cmine)"] - supply["coal (ccoal)"]
    supply = supply[["v0.5e mining (cmine)", "coal (ccoal)", "rest (cmine)", "basis"]]
    activity = pd.DataFrame({"v0.5e mining (amine)": {i: float(t.loc[i, "amine"]) for i in list(col) + ["cmine"]},
                             "coal mining (acoal)": {**col, "cmine": cell[("ccoal", "acoal")] + cell[("cmine", "acoal")]}})
    activity["rest (amine)"] = activity["v0.5e mining (amine)"] - activity["coal mining (acoal)"]
    el = io["electricity: other mining, all mining"]
    d_in = pd.read_csv(paths.DATA_PROCESSED / ELEC_FUEL_INPUTS, comment="#").set_index("key")["value"]
    mtoe = float(d_in["DOE gross generation Coal 2023"]) * float(d_in["GTAP 10A 2014 Philippines ely coal Mtoe"]) / \
        float(d_in["DOE gross generation Coal 2014"])
    usd_gj = coal["aelec"] * 1e9 / _annual("BIS_WS_XRU_PHP_per_USD_monthly_average.csv", "value", 2023) / (mtoe * 1e6 * 41.868)
    inputs = {**gas, "electricity: other mining products, I-O 2018 share of its mining purchases": el[0] / el[1],
              "electricity: other mining products 2023 (₱ bn; that share of v0.5's mining purchases)": other_el,
              "electricity: coal 2023 (₱ bn)": coal["aelec"],
              "coal burnt by power plants 2023 (Mtoe; DOE coal generation x GTAP 2014 Mtoe per GWh)": mtoe,
              "implied coal price 2023 (US$ per GJ)": usd_gj, "implied coal price 2023 (US$ per tonne of 5,000 kcal/kg coal)": usd_gj * 20.934,
              "coal mining's share of mining output, I-O 2018": io["output"][0] / io["output"][1],
              "coal mining's share of mining compensation, I-O 2018": lab_sh,
              "coal's share of mining imports, I-O 2018": sh_fd("imp"), "coal imports: v0.5's mining imports x that share (₱ bn)": imp5 * sh_fd("imp"),
              "coal imports: v0.5e's extra mining imports (₱ bn)": imp - imp5, "coal's share of the mining composite": comp,
              "coal supply = coal use (₱ bn)": sum(sup.values()),
              "basic metals' coal (₱ bn; the balancing cell)": coal["ametl"],
              "basic metals' coal at the I-O's share (₱ bn; not used: more than the coal account leaves)": metals_io,
              "imports of the rest of mining (₱ bn) = v0.5's non-coal mining imports": imp - imp_k,
              "aggregation back to v0.5e (max |difference|, ₱ bn)": gap_back, "balance (max row-column gap, ₱ bn)": gap_bal}
    diag = {"v0.7: electricity's coal, ₱ bn": coal["aelec"], "v0.7: coal imports, ₱ bn": imp_k, "v0.7: domestic coal (acoal output), ₱ bn": dom,
            "v0.7: basic metals' coal (balancing cell), ₱ bn": coal["ametl"], "v0.7: basic metals' coal at the I-O share (not used), ₱ bn": metals_io,
            "v0.7: coal supply = use, ₱ bn": sum(sup.values()), "v0.7: aggregation back to v0.5e, max |difference|": gap_back}
    return x, {"users": users, "supply": supply, "activity": activity, "inputs": inputs, "diag": diag}


def build_v07():
    """Version '0.7': v0.5e (build('0.5e')) with coal split out of mining (coal_split); build()'s outputs, with the split's
    tables in extra['coal split']. The controls (ctl) are v0.5e's: the split leaves every aggregate they constrain unchanged."""
    S, s78, diag, ctl, ind, fg, psa, extra = build("0.5e")
    x, doc = coal_split(S.table, SAM.load(paths.sam_own("0.5")).table)
    S7 = SAM(x, {**S.labels, **COAL_LABELS}, S.source.replace("version 0.5e:", "version 0.7 (v0.5e with coal split from mining):"))
    diag = dict(diag)
    diag["max row-column gap"] = S7.check(verbose=False)["max_row_col_gap"]
    diag.update(doc["diag"])
    return S7, s78, diag, ctl, ind, fg, psa, dict(extra, **{"coal split": doc})


# ------------------------------------------------------------------------------------------------------------------------------
# Version '0.7b' (24 Oct 2026; RESEARCH, opt-in, NOT the default; VERSION stays "0.5"): v0.7 without its coal double
# count (a review note (not included), caveat 1). PSA's 2018 tables book 78.5%
# of intermediate coal in basic iron and steel (IEA volumes, GTAP 10A 2014: 2.0%; power plants 79.5%); v0.5e kept that coal in
# basic metals AND gave electricity the power plants' coal, imported by moving imports from refined oil (cpetr) to mining
# (cmine). The same coal is counted twice: v0.7 shows it as ₱77.4 bn of coal bought by basic metals (the balancing cell of its
# coal account) in a ₱309 bn coal account. v0.7b reads PSA's coal in basic metals as the power plants' coal, as the I-O test (b) of the electricity fuel-mix review does (checks/test_own_sam_v06e.py: 'the coal electricity gains comes out of basic metals' coal and the oil it loses
# goes to the other users of refined petroleum'), to the extent of the double count S (₱ bn):
#   prior (v0.5e's, after electricity_fuel_mix; double_count_prior): basic metals' mining purchases (cmine) less S; imports of
#     cmine less S and of cpetr plus S (PSA's refined-oil imports partly restored; the import total of the two accounts, held at
#     v0.5's by v0.5e's control, unchanged); the S of oil products to the activities that buy them, electricity (its oil is the
#     DOE/IEA bill, controlled) and refining's own use excepted, in proportion to their purchases (test (b));
#   controls (v0.5e's, plus): basic metals' cmine = v0.5e's less S; imports of cmine = v0.5e's less S; value added (labour,
#     land and capital) of each activity = v0.5e's (all but the largest activity of each PSA industry, whose value added then
#     follows from the industry's own controls; refining keeps its own control), so that the correction moves fuel, imports and
#     output, not value added between activities (a trial build without them moved ₱8 bn of value added into basic metals);
#   then v0.7's coal_split: basic metals' coal is again the balancing cell of the coal account, and S is solved (secant) so that
#     it equals metals_coal_2023(), basic metals' coal at IEA volumes. Coal's trade margins and taxes leave the coal account
#     with it (coal's share of the mining composite), so S is about a tenth below the cut in basic metals' coal.
# Coal imports fall by S and the coal account comes to about the DOE/IEA-consistent size; the rest of mining keeps v0.5's
# non-coal mining imports, so crude's share in the oil shock (infinity_gem.oil, crude_in_mining_ex_coal) stays exact. Reads the v0.5
# and v0.5e files. Not changed (open, as in v0.7): cement's coal (PSA's I-O share, below its value at IEA volumes), the coal and
# gas inside the refined-petroleum row, and the rest of basic metals' column (PSA's buys no metal inputs).
# ------------------------------------------------------------------------------------------------------------------------------
V07B_TOL = 1e-8                                                     # ₱ bn: basic metals' coal within this of its target


def metals_coal_2023(coal_el: float) -> dict:
    """Version '0.7b': coal bought by basic metals in 2023 at IEA volumes, ₱ bn = GTAP 10A 2014's coal use by iron and steel
    (IEA energy balances; data/processed/ELEC_FUEL_INPUTS) x PSA's real GVA of basic metals 2023 / 2014 (OpenSTAT 0462B5BMFA1,
    constant 2018 prices), valued at the power plants' implied 2023 coal price per kgoe: coal_el (electricity's coal in the
    split, ₱ bn) / (DOE's 2023 coal generation x GTAP 2014's Mtoe per GWh of coal generation); the method of the electricity fuel-mix evidence (research/electricity_fuel_mix/fuel_mix_evidence.py, power's share of coal in 2018). Cement and the other
    industries the same way, for comparison only."""
    d = pd.read_csv(paths.DATA_PROCESSED / ELEC_FUEL_INPUTS, comment="#").set_index("key")["value"]
    g = pd.read_csv(paths.DATA_RAW / "macro" / "PSA_OpenSTAT_0462B5BMFA1_GVA_manufacturing_by_industry_annual.csv", comment="#")
    name = g.iloc[:, 0].astype(str).str.lstrip(".").str.strip()

    def real(label: str) -> float:
        r = g[name.str.startswith(label)].iloc[0]
        return float(r["At Constant 2018 Prices 2023"]) / float(r["At Constant 2018 Prices 2014"])
    gt = lambda k: float(d[f"GTAP 10A 2014 Philippines coal use, {k} Mtoe"])
    ely = float(d["GTAP 10A 2014 Philippines ely coal Mtoe"])
    power = float(d["DOE gross generation Coal 2023"]) * ely / float(d["DOE gross generation Coal 2014"])
    price = coal_el / power                                           # ₱ bn per Mtoe = ₱ per kgoe
    g_is, g_nmm, g_man = (real(k) for k in ("Manufacture of basic metals", "Manufacture of other non-metallic",
                                            "Gross Value Added in Manufacturing"))
    i_s = gt("i_s (iron and steel)") * g_is
    nmm = gt("nmm (cement etc.)") * g_nmm
    oth = (gt("all sectors") - gt("nmm (cement etc.)") - gt("i_s (iron and steel)") - ely) * g_man
    return {"basic metals' coal 2023 at IEA volumes (₱ bn; the target)": i_s * price,
            "GTAP 10A 2014: iron and steel's coal (Mtoe)": gt("i_s (iron and steel)"),
            "GTAP 10A 2014: iron and steel's share of coal use": gt("i_s (iron and steel)") / gt("all sectors"),
            "GTAP 10A 2014: power plants' share of coal use": ely / gt("all sectors"),
            "PSA real GVA of basic metals 2023 / 2014 (constant 2018 prices)": g_is, "iron and steel's coal 2023 (Mtoe)": i_s,
            "power plants' coal 2023 (Mtoe; DOE coal generation x GTAP 2014 Mtoe per GWh)": power,
            "electricity's coal 2023 (₱ bn)": coal_el, "implied coal price 2023 (₱ per kgoe)": price,
            "cement's coal 2023 at IEA volumes (₱ bn; not used)": nmm * price,
            "other industries' coal 2023 at IEA volumes (₱ bn; not used)": oth * price}


def double_count_prior(t0: pd.DataFrame, s: float, A: list) -> dict:
    """Version '0.7b': in v0.5e's prior (t0, after electricity_fuel_mix) the double-counted coal s (₱ bn) leaves basic metals'
    mining purchases (cmine) and the cmine imports; cpetr imports rise by s and the s of oil products goes to the activities in
    A that buy them, electricity and refining excepted, in proportion to their purchases (the I-O test (b) of the electricity fuel-mix review). Changes t0;
    returns s and the oil users' shares."""
    m0 = float(t0.loc["cmine", "ametl"])
    if not 0.0 < s < m0:
        raise ValueError(f"v0.7b: the double count {s:.2f} must lie between 0 and basic metals' mining purchases in the prior ({m0:.2f})")
    users = [a for a in A if a not in ("aelec", "apetr") and float(t0.loc["cpetr", a]) > 0.0]
    w = t0.loc["cpetr", users].astype(float) / float(t0.loc["cpetr", users].sum())
    t0.loc["cmine", "ametl"] = m0 - s
    t0.loc["row", "cmine"] = float(t0.loc["row", "cmine"]) - s
    t0.loc["row", "cpetr"] = float(t0.loc["row", "cpetr"]) + s
    t0.loc["cpetr", users] = (t0.loc["cpetr", users].astype(float) + s * w).values
    return {"double count (₱ bn)": s, "oil users' shares (prior)": w}


def build_v07b():
    """Version '0.7b': v0.5e's build with the coal double count removed (build('0.5e', double_count=s): double_count_prior and
    three groups of controls in build) and v0.7's coal split, s solved by the secant method so that basic metals' coal (the
    coal account's balancing cell) equals metals_coal_2023(); build()'s outputs, with extra['coal split'] and
    extra['coal double count'] (s, the target and its inputs, the secant steps, the v0.5e-level table before the split)."""
    t5, te = SAM.load(paths.sam_own("0.5")).table, SAM.load(paths.sam_own("0.5e")).table
    x0, d0 = coal_split(te, t5)                                     # v0.7 as built (basic metals' coal ₱77.4 bn)
    coal_el = float(d0["inputs"]["electricity: coal 2023 (₱ bn)"])
    mc = metals_coal_2023(coal_el)
    tgt = mc["basic metals' coal 2023 at IEA volumes (₱ bn; the target)"]

    def run(s):
        out = build("0.5e", double_count=s)
        x, doc = coal_split(out[0].table, t5)
        return out, x, doc, float(x.loc["ccoal", "ametl"]) - tgt
    s_a = 0.9 * (float(x0.loc["ccoal", "ametl"]) - tgt)             # coal's margins and taxes leave with it: slope about -1.1
    o_b, x_b, d_b, f_a = run(s_a)
    hist = [(s_a, f_a)]
    s_b = s_a + f_a
    o_b, x_b, d_b, f_b = run(s_b)
    hist.append((s_b, f_b))
    while abs(f_b) > V07B_TOL:
        if len(hist) >= 10:
            raise RuntimeError(f"v0.7b: the double count did not converge (basic metals' coal off its target by {f_b:.2e} ₱ bn)")
        s_a, f_a, s_b = s_b, f_b, s_b - f_b * (s_b - s_a) / (f_b - f_a)
        o_b, x_b, d_b, f_b = run(s_b)
        hist.append((s_b, f_b))
    if abs(float(d_b["inputs"]["electricity: coal 2023 (₱ bn)"]) - coal_el) > 1e-6:
        raise ValueError("v0.7b: electricity's coal differs from v0.7's (its fuel bill and oil bill are controlled)")
    S, s78, diag, ctl, ind, fg, psa, extra = o_b
    S7 = SAM(x_b, {**S.labels, **COAL_LABELS}, S.source.replace(
        "version 0.5e:", "version 0.7b (v0.5e without the coal double count, coal split from mining):"))
    diag = dict(diag)
    diag["max row-column gap"] = S7.check(verbose=False)["max_row_col_gap"]
    diag.update({k.replace("v0.7:", "v0.7b:"): v for k, v in d_b["diag"].items()})
    diag.update({"v0.7b: double count removed, S (₱ bn)": s_b, "v0.7b: basic metals' coal target (₱ bn)": tgt,
                 "v0.7b: basic metals' coal less its target (₱ bn)": f_b, "v0.7b: builds in the secant": len(hist)})
    fix = dict(extra["coal double count"], **{"S (₱ bn)": s_b, "target": mc, "base": S.table,
                                              "secant": pd.DataFrame(hist, columns=["S (₱ bn)", "basic metals' coal less its target (₱ bn)"])})
    return S7, s78, diag, ctl, ind, fg, psa, dict(extra, **{"coal split": d_b, "coal double count": fix})


def build(version: str = VERSION, double_count: float | None = None):
    # double_count: '0.7b' only (build_v07b calls build("0.5e", double_count=S)): v0.5e's build without the coal double count
    if version == "0.7":                                            # '0.7': v0.5e with coal split from mining (build_v07)
        return build_v07()
    if version == "0.7b":                                           # '0.7b': v0.7 without the coal double count (build_v07b)
        return build_v07b()
    if double_count is not None and version != "0.5e":
        raise ValueError("double_count is the '0.7b' correction of v0.5e's build only")
    s78 = SAM.load(paths.SAM_2023_RICE_PSA)                         #: IFPRI's institutional detail, double count removed
    t0 = io_prior(s78, version)
    A0, C0, H0 = s78.accounts("a"), s78.accounts("c"), s78.accounts("hhd")
    taxes = tax_block(t0, s78.table, A0, C0, H0)
    el_fix = electricity_fuel_mix(t0) if version >= "0.6" and version.endswith("e") else None   # '0.6e' only
    el_base = "0.5" if version == "0.5e" else "0.6"                 # '0.5e': v0.5 with the same correction only
    if version == "0.5e":
        el_fix = electricity_fuel_mix(t0, base="0.5")
    dc = double_count_prior(t0, double_count, A0) if double_count is not None else None   # '0.7b' (build_v07b) only
    codes = list(t0.index)
    ix = {c: i for i, c in enumerate(codes)}
    n = len(codes)
    A, C, H = s78.accounts("a"), s78.accounts("c"), s78.accounts("hhd")
    psa = P.psa_2023()
    T = float(t0.loc[["mtax", "stax"], C].values.sum())
    ind = industry_targets(psa, T)
    v6 = version >= "0.6"
    if v6:      # v0.6: labour income keeps the I-O's industry pattern, at PSA's 2023 compensation of employees (0022B5BCA02)
        coe = float(psa_sector_accounts_2023()["ndi"]["From resident producers"])
        ind["labour income"] *= coe / float(ind["labour income"].sum())
        ind["capital and land income"] = ind["value added at basic prices"] - ind["labour income"]
    if version >= "0.4":                                            # business services and finance labour from LFS pay (v0.4)
        ind = lfs_split(ind)
    fg = fies_groups()
    I = lambda names: [ix[c] for c in names if c in ix]
    if v6:      # v0.6: rest of world, government and direct taxes from PSA's 2023 integrated accounts (before lab_row below)
        fg6 = fies_groups_v06()
        pit, pit_k, pit_tax, pit_n = pit_shares(H)
        inst_doc = rest_of_world_and_government(t0, s78.table, H, fg6, pit, bop=version.endswith("b"))   # '0.6b': BSP's BOP
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
    if v6:      # v0.6: household saving by group (fixed below) and the priors of the cells that balance each account
        sav5 = float(SAM.load(paths.sam_own("0.5")).table.loc["s-i", H].sum())
        hh_doc = household_capital_and_saving(t0, A, H, fg6, hh_lab, psa["hfce"], sav5, psa["gfce"])
        sub_va = subindustry_va(ind)
        land_cr = land_shares_cr()

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
    if v6:
        fix(["s-i"], H)                                                 # v0.6: household saving by group (FIES shares)

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
    if "0.5" <= version < "0.6" and "apetr" in ix:                 # v0.5: refining's value added at PSA's 2023 refining level
        va_ref = float(t0.loc[list(P.LABOUR + P.NONLAB), "apetr"].sum())
        controls.append(("value added: refining (I-O 2018 x PSA refining GVA 2023/2018)", mask(list(P.LABOUR + P.NONLAB), ["apetr"]), va_ref))
    if v6:
        LNL = list(P.LABOUR + P.NONLAB)
        for k, d in sub_va.items():                                # value added by activity group: PSA GVA 2023 by sub-industry
            for g_, r in list(d.iterrows())[:-1]:                  # the last group follows from the industry's own controls
                controls.append((f"value added: {g_} (PSA GVA 2023 by sub-industry, basic prices)", mask(LNL, list(r["activities"])),
                                 float(r["value added at basic prices"])))
        t78 = s78.table
        land_src = {a: (float(r["land share of capital and land income"]), "PSA costs and returns") for a, r in land_cr.iterrows()}
        land_src.update({a: (float(t78.loc["flnd", a] / t78.loc[["flnd", "fcap"], a].sum()), "IFPRI's, kept: no PSA survey")
                         for a in A if a not in land_src and float(t78.loc["flnd", a]) > 0})
        for a, (s_a, src) in land_src.items():                     # land's share of capital and land income by crop
            m = np.zeros((n, n))
            m[ix["flnd"], ix[a]], m[ix["fcap"], ix[a]] = 1.0 - s_a, -s_a
            controls.append((f"land share of capital and land income: {a} = {s_a:.4f} ({src})", m, 0.0))
        land_cr = land_cr.reindex(list(land_src))
        land_cr["land share used"] = [v[0] for v in land_src.values()]
        land_cr["source of the share"] = [v[1] for v in land_src.values()]
        land_cr["v0.5 share (IFPRI's via the PSA-consistent SAM)"] = [float(t78.loc["flnd", a] / t78.loc[["flnd", "fcap"], a].sum()) for a in land_src]
        AG = [a for a in PSA_INDUSTRIES["Agriculture, forestry, and fishing"] if a in ix]
        for name, f_, col in (("land income", "flnd", "crop income"), ("farm capital income", "fcap", "farm income")):
            shh = fg6[col].reindex(H) / float(fg6[col].reindex(H).sum())
            for h in H[:-1]:                                       # nine shares; the tenth follows
                m = np.zeros((n, n))
                m[I(H), ix[f_]] = -float(shh[h])
                m[ix[h], ix[f_]] += 1.0
                controls.append((f"{name} paid to {h} = FIES 2023 share of {col} ({shh[h]:.4f})", m, 0.0))
        m = np.zeros((n, n))
        m[I(H), ix["fcap"]], m[ix["fcap"], I(AG)] = 1.0, -1.0
        controls.append(("farm capital income paid to households = capital income of agriculture, forestry and fishing", m, 0.0))
        for flow, groups in ({} if version.endswith("c") else TRADE_CONTROLLED).items():   # trade by product group (PSA 2023)
            for cs in groups:
                cs = [c for c in cs if c in ix]
                tgt = float(t0.loc[cs, "row"].sum()) if flow == "exports" else float(t0.loc["row", cs].sum())
                controls.append((f"{flow}: {'+'.join(cs)} (PSA 2018 I-O x PSA 2023/2018 growth of the product group)",
                                 mask(cs, ["row"]) if flow == "exports" else mask(["row"], cs), tgt))
    if el_fix is not None:                                          # '0.6e': electricity's fuel mix
        tg_ = el_fix["targets"]
        controls += [("electricity's oil products (cpetr) = DOE/IEA-consistent 2023 oil bill", mask(["cpetr"], ["aelec"]),
                      float(tg_["cpetr"])),
                     (f"electricity's coal, gas and other mining (cmine) = v{el_base}'s fuel bill less the oil bill",
                      mask(["cmine"], ["aelec"]), float(tg_["cmine"]))]
    if version == "0.5e":   # '0.5e': v0.5 has no trade-by-product controls, so hold the two accounts' imports at v0.5's
        controls.append(("imports of cpetr + cmine = v0.5's (imports carry the switch)", mask(["row"], ["cpetr", "cmine"]),
                         float(el_fix["imports of cpetr + cmine v0.5 (₱ bn)"])))
    if dc is not None:      # '0.7b' (build_v07b): basic metals' mining purchases and mining imports at v0.5e's less the double count
        te_ = SAM.load(paths.sam_own("0.5e")).table
        s_ = dc["double count (₱ bn)"]
        controls += [("basic metals' coal, gas and ores (cmine) = v0.5e's less the double-counted coal (v0.7b)",
                      mask(["cmine"], ["ametl"]), float(te_.loc["cmine", "ametl"]) - s_),
                     ("imports of cmine = v0.5e's less the double-counted coal (v0.7b; those of cpetr rise by as much)",
                      mask(["row"], ["cmine"]), float(te_.loc["row", "cmine"]) - s_)]
        F_ = list(P.LABOUR + P.NONLAB)
        for k, acts in PSA_INDUSTRIES.items():                      # value added of each activity = v0.5e's (v0.7b)
            a_ = [a for a in acts if a in ix and float(te_.loc[F_, a].sum()) > 0.0]
            big = max(a_, key=lambda z: float(te_.loc[F_, z].sum())) if a_ else None   # follows from the industry's controls
            for a in a_:
                if a not in (big, "apetr"):                         # apetr: v0.5's refining control already holds it
                    controls.append((f"value added: {a} = v0.5e's (v0.7b)", mask(F_, [a]), float(te_.loc[F_, a].sum())))
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
    if v6:
        diag["income-tax shares: pay gross-up k (PSA compensation / LFS basic pay)"] = pit_k
        diag["income-tax shares: tax computed on FIES-LFS pay, ₱ bn"] = pit_tax
        extra.update({"institutions": inst_doc, "households (priors)": hh_doc, "income-tax shares": pit,
                      "value added by sub-industry": sub_va, "land shares": land_cr, "trade growth": trade_growth()["groups"],
                      "fies v0.6": fg6})
    if el_fix is not None:                                          # '0.6e'
        extra["electricity fuel mix"] = el_fix
        diag[f"v{el_base}e: electricity's oil products, ₱ bn (control)"] = el_fix["targets"]["cpetr"]
        diag[f"v{el_base}e: electricity's fuel bill = v{el_base}'s, ₱ bn (control)"] = el_fix[f"fuel bill v{el_base} (₱ bn)"]
        diag[f"v{el_base}e: fuel moved from cpetr to cmine in the prior, ₱ bn"] = el_fix["moved (₱ bn, prior)"]
        if version == "0.5e":
            diag["v0.5e: imports of cpetr + cmine = v0.5's, ₱ bn (control)"] = el_fix["imports of cpetr + cmine v0.5 (₱ bn)"]
    if dc is not None:                                              # '0.7b' (build_v07b)
        extra["coal double count"] = dc
        diag["v0.7b: double-counted coal taken out in the prior and the controls, ₱ bn"] = dc["double count (₱ bn)"]
    return S, s78, diag, ctl, ind, fg, psa, extra


def main(version: str = VERSION):
    if version == "0.7b":                                           # '0.7b': the SAM file and CSV tables only (main_v07b)
        return main_v07b()
    S, s0, diag, ctl, ind, fg, psa, extra = build(version)
    path = paths.sam_own(version)
    write_ifpri_csv(S, path)
    with open(path, encoding="utf-8-sig") as f:
        txt = f.read()
    title = (f"Infinity GEM 2023 Social Accounting Matrix for the Philippines, version {version} (PSA and FIES controls; IFPRI "
             "structure as prior; Infinity GEM 0.3.9)") if version < "0.6" else (
             f"Infinity GEM 2023 Social Accounting Matrix for the Philippines, version {version} (research, not the default: PSA national "
             "and institutional-sector accounts, GVA by sub-industry, trade by product group, costs and returns, FIES"
             + ("; SENSITIVITY: rest-of-world income flows from BSP's BPM6 balance of payments" if version.endswith("b") else "")
             + ("; DECOMPOSITION FILE: without the trade-by-product block" if version.endswith("c") else "")
             + ("; ELECTRICITY FUEL MIX: oil products at a DOE- and IEA-consistent 2023 level, coal and gas the rest"
                if version.endswith("e") else "")
             + "; Infinity GEM 0.3.13)")
    if version == "0.5e":                                           # '0.5e': v0.5 with the electricity correction only
        title = ("Infinity GEM 2023 Social Accounting Matrix for the Philippines, version 0.5e (research, not the default: v0.5 with the "
                 "ELECTRICITY FUEL MIX correction only: oil products at a DOE- and IEA-consistent 2023 level, coal and "
                 "gas the rest; PSA and FIES controls; IFPRI structure as prior; Infinity GEM 0.3.13)")
    if version == "0.7":                                            # '0.7': v0.5e with coal split from mining
        title = ("Infinity GEM 2023 Social Accounting Matrix for the Philippines, version 0.7 (research, not the default: v0.5e with COAL "
                 "split from mining into its own activity and commodity (acoal, ccoal); v0.5e = v0.5 with the electricity "
                 "fuel-mix correction; PSA and FIES controls; IFPRI structure as prior; Infinity GEM 0.3.13"
                 ")")
    txt = txt.replace("2023 Social Accounting Matrix for Philippines, petroleum split (Infinity GEM 0.3)", title, 1)
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
    sams = (("IFPRI", ifpri.table), ("PSA-consistent", s0.table)) + (
        (("own SAM v0.5", SAM.load(paths.sam_own("0.5")).table),) if version >= "0.6" else ()) + ((f"own SAM v{version}", S1.table),)
    inst = pd.DataFrame({k: {"enterprise saving": t.loc["s-i", "ent"], "household saving": t.loc["s-i", H].sum(),
                             "government saving": t.loc["s-i", "gov"], "foreign saving": t.loc["s-i", "row"],
                             "enterprise payouts to households": t.loc[H, "ent"].sum()}
                         for k, t in sams})
    if version >= "0.6":
        s05 = SAM.load(paths.sam_own("0.5"))
        hh = pd.concat({"IFPRI": P.households(ifpri.table, ifpri), "own SAM v0.5": P.households(s05.table, s05),
                        f"own SAM v{version}": P.households(S1.table, S1)}, axis=1)
    stamp = dt.datetime.now()
    head = (f"**NOT YET THE MODEL'S SAM** (Infinity GEM 0.3.9; opt-in: settings `sam_variant=\"own\"` with "
            f"`rice=True`). Tool: `tools/build_own_sam_2023.py`; design and source table: "
            f"a design note (not included). File: `{path.relative_to(ROOT)}`.") if version < "0.6" else (
            f"**RESEARCH VERSION, NOT THE DEFAULT, NOT FOR CITATION** (Infinity GEM 0.3.13). v0.5 stays the "
            f"default (`paths.SAM_2023_OWN`); this file is reached only by naming it (`paths.sam_own(\"0.6\")`). Tool: "
            f"`tools/build_own_sam_2023.py 0.6`; checks: `checks/test_own_sam_v06.py`. File: `{path.relative_to(ROOT)}`.")
    if version == "0.5e":                                           # '0.5e'
        head = ("**RESEARCH VERSION, NOT THE DEFAULT, NOT FOR CITATION** (Infinity GEM 0.3.13). v0.5 stays the "
                "default (`paths.SAM_2023_OWN`); this file is v0.5 with electricity's fuel-mix correction only (section 9), "
                "reached only by naming it (`paths.sam_own(\"0.5e\")`). Tool: `tools/build_own_sam_2023.py 0.5e`; checks: "
                f"`checks/test_own_sam_v05e.py`. File: `{path.relative_to(ROOT)}`.")
    if version == "0.7":                                            # '0.7': coal split from mining
        head = ("**RESEARCH VERSION, NOT THE DEFAULT, NOT FOR CITATION** (Infinity GEM 0.3.13). v0.5 stays the default "
                "(`paths.SAM_2023_OWN`); this file is v0.5e (v0.5 with electricity's fuel-mix correction, section 9) with coal "
                "split from mining into its own activity and commodity (section 10), reached only by naming it "
                "(`paths.sam_own(\"0.7\")`). Tool: `tools/build_own_sam_2023.py 0.7`; checks: `checks/test_own_sam_v07.py`. "
                f"File: `{path.relative_to(ROOT)}`.")
    L = [f"# Infinity GEM's own 2023 SAM, version {version} ({stamp:%d %B %Y, %H:%M})", "", head, "",
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
        [f"| {k} | {v:,.6g} |" for k, v in diag.items()] + ["", ctl.round(6).to_markdown(), ""]
    if version < "0.6" or version == "0.7":                        # '0.7' is built on v0.5e
        L += ["## 7. Still from IFPRI's structure in this version (design note §4)", "",
              "Government transfers; rest-of-world income flows; the activity mix within each PSA industry; land; the margin "
              "pattern; household direct taxes by group; customs duties by commodity other than rice."]
    else:
        tr = pd.DataFrame({"exports v0.5": s05.table.loc[C, "row"], f"exports v{version}": S1.table.loc[C, "row"],
                           "imports v0.5": s05.table.loc["row", C], f"imports v{version}": S1.table.loc["row", C]})
        fa = lambda t: pd.DataFrame({"labour": t.loc[list(P.LABOUR), A].sum(), "land": t.loc["flnd", A], "capital": t.loc["fcap", A]})
        fac = pd.concat({"v0.5": fa(s05.table), f"v{version}": fa(S1.table)}, axis=1)
        sub = pd.concat({k: d.drop(columns=["activities", "PSA lines"]) for k, d in extra["value added by sub-industry"].items()})
        L += ["## 7. Version 0.6: blocks replaced with Philippine data", "",
              "### 7a. Rest of the world, government and direct taxes: PSA's 2023 integrated accounts (₱ bn)", "",
              *(["**This file is the SENSITIVITY '0.6b': the rest-of-world income and transfer lines below are BSP's BPM6 "
                 "balance of payments (Tables 1.3-1.4, 2023, at BIS's average rate) instead of PSA's external account; "
                 "everything else as v0.6.**", ""] if version.endswith("b") else []),
              "PSA's external account is consistent with PSA's exports and imports, which the SAM already uses; its compensation "
              "from abroad (OFWs, ₱2,880 bn) and transfers to households (₱1,607 bn) go to households by FIES 2023 receipts from "
              "abroad. Foreign saving is the balancing item: PSA's 2023 current external balance is a SURPLUS of ₱909.5 bn (BSP's "
              "BPM6 balance of payments, which treats most OFW income as transfers, shows a deficit of ₱689 bn).", "",
              extra["institutions"].to_markdown(floatfmt=",.1f"), "",
              "### 7b. Households: what each group receives and pays, before balancing (₱ bn)", "",
              "Saving by group = FIES 2023 saving (income less expenditure) shares x v0.5's household saving total (kept: PSA's "
              "household-sector saving, ₱61 bn or 0.3% of disposable income, would leave the model's investment-driven closure, "
              "which scales household saving rates, without traction). Enterprise payouts close each household account.", "",
              extra["households (priors)"].round(1).to_markdown(), "",
              "Income-tax shares (TRAIN 2023 schedule on FIES-LFS 2023 wage earners; licensed file, aggregates only):", "",
              (extra["income-tax shares"] * 100).round(2).to_frame("share (%)").to_markdown(), "",
              "### 7c. Value added by sub-industry: PSA GVA 2023 (₱ bn)", "", sub.round(4).to_markdown(), "",
              "### 7d. Land: PSA costs and returns (per hectare, ₱; share of capital and land income)", "",
              extra["land shares"].round(4).to_markdown(), "",
              "### 7e. Trade by product group: PSA national accounts 2018 -> 2023 growth applied to the 2018 I-O (₱ bn)", "",
              extra["trade growth"].round(4).to_markdown(), "", tr.round(1).to_markdown(), "",
              "### 7f. Factor income by activity, v0.5 and this version (₱ bn)", "", fac.round(1).to_markdown(), "",
              "## 8. Still from IFPRI's structure in this version", "",
              "- trade and transport margins by commodity (PSA's 2018 I-O and SUT are at purchasers' prices with no margin "
              "matrix; the margin total is PSA's, the pattern IFPRI's);",
              "- customs duties by commodity other than rice (BESF gives the total; duties by HS chapter from BOC are not on file);",
              "- home consumption (own produce) by commodity and group (IFPRI from FIES);",
              "- the split of private saving between households and enterprises (see 7b);",
              "- land's share for oil crops, sugarcane, tobacco, abaca and other crops (no PSA costs-and-returns survey on file);",
              "- each group's purchases by commodity within PSA's purpose totals and FIES group totals (IFPRI's FIES-based pattern);",
              "- the skill split of compensation paid abroad (₱60 bn), and IFPRI's GFS taxes on property (ftax, ₱10 bn)."]
    if "electricity fuel mix" in extra:                             # '0.6e'
        ef = extra["electricity fuel mix"]
        eb = "0.5" if version in ("0.5e", "0.7") else "0.6"         # the version the correction is applied to ('0.7': v0.5e's)
        comp = {f"v{version}": S1.table}
        if paths.sam_own(eb).exists():
            comp = {f"v{eb}": SAM.load(paths.sam_own(eb)).table, **comp}
        fin = pd.DataFrame({k: {"electricity buys oil products (cpetr)": t.loc["cpetr", "aelec"],
                                "electricity buys coal, gas and other mining (cmine)": t.loc["cmine", "aelec"],
                                "electricity's total cost": t["aelec"].sum(),
                                "oil products, % of electricity's cost": t.loc["cpetr", "aelec"] / t["aelec"].sum() * 100,
                                "coal, gas and other mining, % of electricity's cost": t.loc["cmine", "aelec"] / t["aelec"].sum() * 100,
                                "imports of cpetr": t.loc["row", "cpetr"], "imports of cmine": t.loc["row", "cmine"]}
                            for k, t in comp.items()})
        if "ccoal" in S1.table.index:                                # '0.7': electricity's coal is in ccoal, its cmine is gas
            fin.loc["electricity buys coal (ccoal; v0.7)", f"v{version}"] = S1.table.loc["ccoal", "aelec"]
            fin.loc["imports of ccoal (v0.7)", f"v{version}"] = S1.table.loc["row", "ccoal"]
        L += ["", f"## 9. Version {version}: electricity's fuel mix", "",
              *(["Version 0.5e is v0.5 (the default) with the correction below and nothing else of v0.6. Three controls hold "
                 "the oil bill, the fuel bill (at v0.5's balanced value) and the imports of cpetr + cmine (at v0.5's) through "
                 "the balancing; tests: `checks/test_own_sam_v05e.py`. The description of the correction as built for 0.6e "
                 "follows.", ""] if version in ("0.5e", "0.7") else []),
              "PSA's 2018 Use table books the electricity industry's fuel as 73% refined petroleum, 20% natural gas and 7% coal; "
              "DOE's 2018 gross generation was 52% coal, 21% gas and 3% oil-based, and PSA's coal row sends 78% of intermediate "
              "coal to basic iron and steel (2% in GTAP 10A's IEA-based 2014 volumes). The 240-industry I-O (the prior) also "
              "moves 48% of electricity's gas into the refined-petroleum row. v0.6e sets electricity's oil products to the "
              "DOE/IEA-consistent 2023 bill below and the rest of its fuel bill to coal and gas (cmine); imports carry the "
              "switch (PSA's import total of the two accounts unchanged); two controls hold the oil bill and the fuel bill "
              "(at v0.6's balanced value) through the balancing. "
              "Evidence: `research/electricity_fuel_mix/fuel_mix_evidence.py`; tests: `checks/test_own_sam_v06e.py`.", "",
              "Prior (₱ bn):", "", ef["table"].round(2).to_markdown(), "",
              "2023 oil bill of power plants:", "", pd.Series(ef["inputs"]).round(4).to_frame("value").to_markdown(), "",
              "Balanced SAM (₱ bn):", "", fin.round(2).to_markdown(), ""]
    if "coal split" in extra:                                       # '0.7': coal split from mining
        cs = extra["coal split"]
        L += ["", "## 10. Version 0.7: coal split from mining (acoal, ccoal)", "",
              "v0.5e with every cell of the mining activity's and commodity's rows and columns split into coal and the rest "
              "(coal_split; sources in the builder's notes): users of mining products by PSA's 2018 I-O coal-mining row, "
              "electricity by DOE's 2023 generation (v0.5e's fuel bill less gas and other mining), coal mining by the I-O's "
              "coal-mining column, imports so that the rest of mining keeps v0.5's imports; basic metals' coal closes the coal "
              "account. acoal + amine and ccoal + cmine give v0.5e back. Tests: `checks/test_own_sam_v07.py`.", "",
              "Coal in the mining commodity's row (₱ bn):", "", cs["users"].round(4).to_markdown(), "",
              "Supply of coal (₱ bn):", "", cs["supply"].round(4).to_markdown(), "",
              "The coal-mining activity's column (₱ bn):", "", cs["activity"].round(4).to_markdown(), "",
              "Inputs and checks:", "", pd.Series(cs["inputs"]).to_frame("value").to_markdown(floatfmt=".6g"), ""]
        for k in ("users", "supply", "activity"):              # the tables also as CSV
            cs[k].to_csv(paths.output_dir() / f"own_sam_2023_v{version}_{stamp:%Y%m%d_%H%M}_coal_{k}.csv")
        pd.Series(cs["inputs"]).to_csv(paths.output_dir() / f"own_sam_2023_v{version}_{stamp:%Y%m%d_%H%M}_coal_inputs.csv")
    rp = paths.output_dir() / f"own_sam_2023_v{version}_{stamp:%Y%m%d_%H%M}.md"
    rp.write_text("\n".join(L), encoding="utf-8")
    print(macro.round(1).to_string()); print(purpose.round(1).to_string()); print(vt.round(1).to_string()); print(hh.round(1).to_string()); print(inst.round(1).to_string())
    print(pd.Series(diag).to_string())
    print("saved", path, "and", rp)
    return S1


def main_v07b():
    """Version '0.7b': writes the SAM file (paths.sam_own('0.7b')) and the build's tables as CSV files in outputs/
    (own_sam_2023_v0.7b_<stamp>_<table>.csv; no report file): macro totals against PSA, the double count's key cells against
    v0.5, v0.5e and v0.7, the target and its inputs, the secant steps, basic metals' column and the users of refined oil against
    v0.7, every cell that moved, the coal split's tables, the balancing and its controls."""
    version = "0.7b"
    S, s0, diag, ctl, ind, fg, psa, extra = build(version)
    path = paths.sam_own(version)
    write_ifpri_csv(S, path)
    with open(path, encoding="utf-8-sig") as f:
        txt = f.read()
    title = ("Infinity GEM 2023 Social Accounting Matrix for the Philippines, version 0.7b (research, not the default: v0.7 without its "
             "COAL DOUBLE COUNT: basic metals' coal at IEA volumes, coal imports lower and refined-oil imports higher by the same "
             "amount, that oil to its other users; v0.7 = v0.5e with coal split from mining; v0.5e = v0.5 with the electricity "
             "fuel-mix correction; PSA and FIES controls; IFPRI structure as prior; Infinity GEM 0.3.13)")
    txt = txt.replace("2023 Social Accounting Matrix for Philippines, petroleum split (Infinity GEM 0.3)", title, 1)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(txt)
    S1 = SAM.load(path)
    t = S1.table
    s7 = SAM.load(paths.sam_own("0.7"))
    sams = {"v0.5": SAM.load(paths.sam_own("0.5")).table, "v0.5e": SAM.load(paths.sam_own("0.5e")).table, "v0.7": s7.table,
            "v0.7b": t}
    t7 = s7.table
    dc, cs = extra["coal double count"], extra["coal split"]
    A, H = S1.accounts("a"), S1.accounts("hhd")
    F_ = list(P.LABOUR + P.NONLAB)
    stamp = dt.datetime.now()
    files = []

    def save(df, name: str):
        f = paths.output_dir() / f"own_sam_2023_v{version}_{stamp:%Y%m%d_%H%M}_{name}.csv"
        df.to_csv(f)
        files.append(f)
    macro = pd.DataFrame({"own SAM v0.7": P.expenditure(t7, s7), "own SAM v0.7b": P.expenditure(t, S1)})
    macro["PSA 2023"] = [psa["hfce"], psa["gfce"], psa["gfcf"], psa["gcf"] - psa["gfcf"], psa["exports"], psa["imports"],
                         psa["gdp"], np.nan, np.nan, psa["gdp"]]
    save(macro, "macro")
    g = lambda tb, r, c: float(tb.loc[r, c].values.sum()) if isinstance(c, list) else (
        float(tb.loc[r, c]) if r in tb.index and c in tb.columns else np.nan)
    C_ = lambda tb: [c for c in tb.columns if c.startswith("c")]
    oil_users = lambda tb: [a for a in tb.columns if a.startswith("a") and a not in ("aelec", "apetr")]
    key = pd.DataFrame({k: {
        "imports of refined oil (cpetr)": g(tb, "row", "cpetr"), "imports of mining other than coal (cmine)": g(tb, "row", "cmine"),
        "imports of coal (ccoal; v0.5 and v0.5e: inside cmine)": g(tb, "row", "ccoal"),
        "imports of cpetr + cmine + ccoal": float(tb.loc["row", [c for c in ("cpetr", "cmine", "ccoal") if c in tb.columns]].sum()),
        "imports, all commodities": float(tb.loc["row", C_(tb)].sum()),
        "basic metals buy coal (ccoal)": g(tb, "ccoal", "ametl"),
        "basic metals buy coal, gas and ores (cmine + ccoal)": float(tb.loc[[r for r in ("cmine", "ccoal") if r in tb.index], "ametl"].sum()),
        "basic metals buy refined oil (cpetr)": g(tb, "cpetr", "ametl"), "basic metals' output": float(tb["ametl"].sum()),
        "basic metals' value added": float(tb.loc[F_, "ametl"].sum()),
        "coal account (supply = use; ccoal)": float(tb["ccoal"].sum()) if "ccoal" in tb.columns else np.nan,
        "electricity buys refined oil (cpetr)": g(tb, "cpetr", "aelec"), "electricity buys coal (ccoal)": g(tb, "ccoal", "aelec"),
        "electricity buys gas and other mining (cmine)": g(tb, "cmine", "aelec"), "electricity's output": float(tb["aelec"].sum()),
        "refined oil bought by activities other than electricity and refining": float(tb.loc["cpetr", oil_users(tb)].sum()),
        "refined oil bought by households": float(tb.loc["cpetr", H].sum()), "refined oil, all uses": float(tb.loc["cpetr"].sum()),
        "refining's output (apetr)": float(tb["apetr"].sum())} for k, tb in sams.items()})
    key.loc["double count removed, S", "v0.7b"] = dc["S (₱ bn)"]
    save(key, "double_count_key_cells")
    save(pd.Series(dc["target"]).to_frame("value"), "metals_coal_target")
    save(dc["secant"], "secant")
    mcol = pd.DataFrame({"v0.7": t7["ametl"], "v0.7b": t["ametl"]})
    mcol["v0.7b - v0.7"] = mcol["v0.7b"] - mcol["v0.7"]
    save(mcol[(mcol[["v0.7", "v0.7b"]].abs().sum(axis=1) > 0)], "metals_column")
    orow = pd.DataFrame({"v0.7": t7.loc["cpetr"], "v0.7b": t.loc["cpetr"],
                         "share of S in the prior (v0.7b)": dc["oil users' shares (prior)"].reindex(t.columns)})
    orow["v0.7b - v0.7"] = orow["v0.7b"] - orow["v0.7"]
    save(orow[(orow[["v0.7", "v0.7b"]].abs().sum(axis=1) > 0)], "refined_oil_users")
    d = (t - t7).stack()
    d = d[d.abs() > 0.05]
    ch = pd.DataFrame({"v0.7": [float(t7.loc[r, c]) for r, c in d.index], "v0.7b": [float(t.loc[r, c]) for r, c in d.index],
                       "v0.7b - v0.7": d.values}, index=pd.MultiIndex.from_tuples(d.index, names=["row", "column"]))
    save(ch.reindex(ch["v0.7b - v0.7"].abs().sort_values(ascending=False).index), "cells_changed_vs_v0.7")
    for k in ("users", "supply", "activity"):
        save(cs[k], f"coal_{k}")
    save(pd.Series(cs["inputs"]).to_frame("value"), "coal_inputs")
    save(pd.Series(diag).to_frame("value"), "balancing")
    save(ctl, "controls")
    pd.set_option("display.width", 250)
    print(macro.round(1).to_string()); print(key.round(2).to_string()); print(pd.Series(dc["target"]).to_string())
    print(dc["secant"].to_string()); print(pd.Series(diag).to_string())
    print("saved", path)
    for f in files:
        print("saved", f)
    return S1


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else VERSION)
