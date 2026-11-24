"""National government debt after a change in the deficit (0.4.3, 19 Nov 2026, opt-in; check DB1).

Adapted from GEM-Core (Cicowiez and Lofgren 2017, World Bank Policy Research Working Paper 8272, p. 9 and p. 48 fn 15),
which post-calculates domestic and foreign government debt from initial stocks, the financing flows and interest rates,
and reports debt in % of GDP each year (Table C.2, p. 62). See a design note (not included).

Data: the Bureau of the Treasury's NG Debt Indicators, 1986-2025 (the Treasury's workbook
Debt-Indicator-Annual-1986-2025.xlsx, downloaded 14 Nov 2026; not distributed with this repository: save it in data/raw/fiscal/btr/,
see data/raw/macro/README.md):
  sheet 'NG OS Debt 1986-2025': outstanding debt, domestic and external (P million), and GDP;
  sheet 'Debt Service 2004-2025': interest payments, domestic and external (P million).
Rows are found by their labels, not by row numbers, so a re-filed copy with an extra row still reads correctly.
The effective interest rate of year t = interest paid in t / the mean of the stocks at the end of t - 1 and t.

The module does not change any model result. It turns a deficit path that a scenario already produces (for example the
fiscal block of scenarios/combined_revised.py) into extra debt, extra interest and the change in debt-to-GDP.

>>> b = btr_debt_base()                       # end-2025 stocks and 2025 effective rates
>>> t = debt_path({2026: 100.0, 2027: 50.0}, base=b, foreign_share=0.3)

21 Nov 2026 (opt-in, check GF2): scenario_debt(d, sim) applies debt_path to a DynamicCGE
scenario path: the change in government saving against the baseline, year by year, in pesos of the year (scaled by the nominal
GDP path: BTr/PSA to 2025, then the GDP the 193rd DBCC fiscal program implies, dbcc_nominal_gdp()), financed at the path's
foreign share (DynamicCGE gfin's, else BTr's net financing mix of 2025, btr_financing_mix()). Post-calculated, as GEM-Core does:
the extra interest is borrowed and does not feed back into the CGE. a design note (not included).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# The Treasury's workbook is not distributed with this repository: save it here (data/raw/macro/README.md).
BTR_ANNUAL = Path(__file__).resolve().parent.parent / "data" / "raw" / "fiscal" / "btr" / "Debt-Indicator-Annual-1986-2025.xlsx"


def _label(row, ncols=4):
    return " ".join(str(v).strip() for v in row[:ncols] if pd.notna(v) and str(v).strip())


def _find(df, label, start=0, stop=None, ncols=4):
    """First row at or after `start` whose label cells read exactly `label` (case and spaces ignored)."""
    want = " ".join(label.lower().split())
    for i in range(start, len(df) if stop is None else min(stop, len(df))):
        if " ".join(_label(df.iloc[i].tolist(), ncols).lower().split()) == want:
            return i
    raise KeyError(f"row '{label}' not found in the BTr sheet")


def _year_cols(df, header_row):
    cols = {}
    for j, v in enumerate(df.iloc[header_row].tolist()):
        s = str(v).replace("CY", "").strip()
        try:
            y = int(float(s))
        except ValueError:
            continue
        if 1900 < y < 2100:
            cols[y] = j
    return cols


def btr_debt_base(path=None, year=None):
    """BTr's NG debt at the end of `year` (default: the latest year in the file) and that year's effective interest rates.
    Amounts in P billion; rates as fractions. Returns a dict with the source recorded."""
    path = Path(path or BTR_ANNUAL)
    st = pd.read_excel(path, sheet_name="NG OS Debt 1986-2025", header=None)
    hs = next(i for i in range(10) if len(_year_cols(st, i)) > 10)
    ys = _year_cols(st, hs)
    year = int(year or max(ys))
    r_tot, r_dom, r_ext = _find(st, "OUTSTANDING DEBT (P Million)"), _find(st, "Domestic (P Million)"), _find(st, "External (P Million)")
    r_gdp = _find(st, "GDP", start=r_ext)
    val = lambda r, y: float(st.iat[r, ys[y]])
    ds = pd.read_excel(path, sheet_name="Debt Service 2004-2025", header=None)
    hd = next(i for i in range(10) if len(_year_cols(ds, i)) > 10)
    yd = _year_cols(ds, hd)
    r_int = _find(ds, "Total Interest Payments", ncols=3)
    r_idom = _find(ds, "Domestic", start=r_int + 1, stop=r_int + 4, ncols=3)
    r_iext = _find(ds, "External", start=r_int + 1, stop=r_int + 4, ncols=3)
    out = dict(year=year,
               stock=val(r_tot, year) / 1e3, stock_dom=val(r_dom, year) / 1e3, stock_ext=val(r_ext, year) / 1e3,
               stock_dom_prev=val(r_dom, year - 1) / 1e3, stock_ext_prev=val(r_ext, year - 1) / 1e3,
               gdp=val(r_gdp, year) / 1e3,
               int_dom=float(ds.iat[r_idom, yd[year]]) / 1e3, int_ext=float(ds.iat[r_iext, yd[year]]) / 1e3,
               source=f"BTr, NG Debt Indicators 1986-2025 ({path.name}), end-{year} stocks and {year} interest payments")
    out["rate_dom"] = out["int_dom"] / ((out["stock_dom"] + out["stock_dom_prev"]) / 2)
    out["rate_ext"] = out["int_ext"] / ((out["stock_ext"] + out["stock_ext_prev"]) / 2)
    out["ratio"] = out["stock"] / out["gdp"]
    return out


def debt_path(deficit_chg, base=None, foreign_share=0.0, rate_dom=None, rate_ext=None, inflation=None, exr=None,
              baseline_gdp=None, gdp_ratio=None, base_ratio=None):
    """Extra NG debt from a change in the deficit.

    deficit_chg: {year: P bn}, + = a larger deficit (the change before extra interest; extra interest is added here).
    base: btr_debt_base() (default: read it). foreign_share: the share of each year's extra borrowing taken abroad (as
      CGE(gfin={'foreign': phi})); it is held in foreign currency and revalued by `exr` ({year: peso per US$ index,
      1 = the base year}; default 1).
    rate_dom, rate_ext: interest rates (default BTr's effective rates of the base year, nominal). inflation: {year: rate}
      or one rate; if given the rates are made real, (1 + i) / (1 + pi) - 1, for a deficit path in constant prices (GEM-Core
      uses real rates, PRWP 8272 p. 48 fn 15). Each year t: D_t = D_{t-1} x (1 + r) + new borrowing.
    baseline_gdp: {year: nominal GDP of the baseline, P bn}; gdp_ratio: {year: scenario GDP / baseline GDP} (default 1);
      base_ratio: {year: baseline debt-to-GDP} or one number (default: BTr's latest ratio held). With baseline_gdp the
      table adds the change in debt-to-GDP in percentage points: (b Y_b + extra debt) / (Y_b g) - b.
    Returns a DataFrame by year (P bn): extra_dom, extra_ext, extra_interest, extra_debt (and ratio_change_pp); since 21 Nov 2026
     also new_borrowing (the year's deficit change) and valuation (last year's extra foreign debt x the change in exr), so
    that extra_debt_t = extra_debt_t-1 + new_borrowing_t + extra_interest_t + valuation_t exactly."""
    base = base or btr_debt_base()
    years = sorted(int(y) for y in deficit_chg)
    years = list(range(years[0], years[-1] + 1))
    rd = base["rate_dom"] if rate_dom is None else float(rate_dom)
    re_ = base["rate_ext"] if rate_ext is None else float(rate_ext)
    phi = float(foreign_share)
    if not 0.0 <= phi <= 1.0:
        raise ValueError("foreign_share must be in [0, 1]")
    get = lambda d, y, dflt: (d.get(y, dflt) if isinstance(d, dict) else (dflt if d is None else float(d)))
    dd, de_fc, rows = 0.0, 0.0, []
    e_prev = None
    for y in years:
        pi = get(inflation, y, 0.0)
        rdy, rey = (1 + rd) / (1 + pi) - 1, (1 + re_) / (1 + pi) - 1
        e = get(exr, y, 1.0)
        new = float(deficit_chg.get(y, 0.0))
        extra_int = rdy * dd + rey * de_fc * e
        valuation = 0.0 if e_prev is None else de_fc * (e - e_prev)   # 21 Nov 2026: last year's foreign debt revalued
        dd = dd * (1 + rdy) + (1 - phi) * new
        de_fc = de_fc * (1 + rey) + phi * new / e
        e_prev = e
        row = dict(year=y, extra_dom=dd, extra_ext=de_fc * e, extra_interest=extra_int, extra_debt=dd + de_fc * e,
                   new_borrowing=new, valuation=valuation)   # 21 Nov 2026 (check GF2 T5): extra_debt_t - extra_debt_t-1 =
        # new_borrowing + extra_interest + valuation (the stock-flow identity)
        if baseline_gdp is not None:
            yb, g = float(baseline_gdp[y]), get(gdp_ratio, y, 1.0)
            b = get(base_ratio, y, base["ratio"])
            row["ratio_change_pp"] = ((b * yb + row["extra_debt"]) / (yb * g) - b) * 100
        rows.append(row)
    return pd.DataFrame(rows).set_index("year")


# ---------------------------------------------------------------------------------------------------------------------------------
# 21 Nov 2026 (opt-in, check GF2): debt_path on a DynamicCGE scenario path
# ---------------------------------------------------------------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
# The 193rd DBCC joint statement (8 Jul 2026; the PDF is not distributed with this repository: save it in data/raw/oil/forecasts/)
# and its SHA-256.
DBCC_193 = ROOT / "data" / "raw" / "oil" / "forecasts" / "DBCC_193rd_8Jul2026_joint_statement.pdf"
DBCC_193_SHA256 = "b2b11b56da912dd966345b8eff027ed1c15d09e21bcbc0989c0352377f48657b"
# Its "Medium-Term Fiscal Program" table, p. 3 (P billion and % of GDP, as printed; the deficit as a positive amount). Used when pypdf
# cannot be imported; otherwise the table is read from the PDF itself (dbcc_fiscal_program) and check GF2 T6 compares the two.
DBCC_193_FISCAL = {
    "revenues": {2026: (4807.0, 15.8), 2027: (5205.5, 15.7), 2028: (5524.4, 15.4), 2029: (5993.5, 15.5), 2030: (6519.9, 15.6)},
    "disbursements": {2026: (6465.9, 21.2), 2027: (6900.5, 20.8), 2028: (7246.5, 20.2), 2029: (7614.1, 19.7), 2030: (7978.3, 19.1)},
    "deficit": {2026: (1658.9, 5.4), 2027: (1694.9, 5.1), 2028: (1722.1, 4.8), 2029: (1620.6, 4.2), 2030: (1458.4, 3.5)},
}
BTR_FINANCING = ROOT / "data" / "raw" / "fiscal" / "btr" / "COR-Financing_Annual_1986-2025-1.xlsx"   # not distributed (as BTR_ANNUAL)


def dbcc_fiscal_program(pdf=None) -> dict:
    """The 193rd DBCC fiscal program table (p. 3) read from the PDF's text with pypdf: {'revenues' | 'disbursements' | 'deficit':
    {year: (P bn, % of GDP)}}. The file's SHA-256 is checked first. Raises ImportError without pypdf."""
    import hashlib
    import re
    from pypdf import PdfReader
    pdf = Path(pdf or DBCC_193)
    if hashlib.sha256(pdf.read_bytes()).hexdigest() != DBCC_193_SHA256:
        raise ValueError(f"{pdf.name} is not the 193rd DBCC joint statement of 8 Jul 2026 that the transcription was checked against (SHA-256 differs)")
    text = "\n".join(p.extract_text() or "" for p in PdfReader(str(pdf)).pages)
    lines = [" ".join(l.split()) for l in text.splitlines()]
    years = None
    for l in lines:
        if l.startswith("PARTICULARS"):
            years = [int(y) for y in re.findall(r"\b20\d\d\b", l)]
            break
    if not years or len(years) != 5:
        raise ValueError("the fiscal program table's header (PARTICULARS 2026 ... 2030) was not found")
    num = lambda s: float(s.replace(",", "").replace("(", "").replace(")", "").replace("%", "").replace("-", ""))
    out, want = {}, {"Revenues": "revenues", "Disbursements": "disbursements", "Deficit": "deficit"}
    for i, l in enumerate(lines):
        head = l.split(" ")[0]
        if head in want and want[head] not in out:
            amts = re.findall(r"\(?[\d,]+\.\d\)?", l)
            pct = re.findall(r"-?[\d.]+%", lines[i + 1]) if i + 1 < len(lines) and lines[i + 1].startswith("% of GDP") else []
            if len(amts) == 5 and len(pct) == 5:
                out[want[head]] = {y: (num(a), num(p)) for y, a, p in zip(years, amts, pct)}
    if set(out) != set(want.values()):
        raise ValueError(f"the fiscal program table was not read in full (found {sorted(out)})")
    return out


def dbcc_nominal_gdp(source="pdf") -> dict:
    """Nominal GDP (P bn) the 193rd DBCC fiscal program implies, 2026-2030: for each year the GDP consistent with all three printed
    lines (revenues, disbursements, deficit), each amount / its share of GDP rounded to 0.1 pp, so GDP lies in
    [amount / (share + 0.05 pp), amount / (share - 0.05 pp)]; the midpoint of the three intervals' intersection (DBCC prints no GDP
    level). source 'pdf' reads the table from the PDF (needs pypdf; falls back to the transcription DBCC_193_FISCAL with a warning),
    'table' uses the transcription. Returns {year: GDP} with attrs-like keys '_interval' {year: (lo, hi)} and '_source'."""
    tab, src = DBCC_193_FISCAL, "transcription DBCC_193_FISCAL (p. 3)"
    if source == "pdf":
        try:
            tab, src = dbcc_fiscal_program(), f"{DBCC_193.name}, p. 3, read with pypdf"
        except ImportError:
            import warnings
            warnings.warn("pypdf is not installed: the DBCC table is taken from the transcription DBCC_193_FISCAL", stacklevel=2)
    elif source != "table":
        raise ValueError("source must be 'pdf' or 'table'")
    out, iv = {}, {}
    for y in sorted(tab["revenues"]):
        lo, hi = 0.0, float("inf")
        for line in ("revenues", "disbursements", "deficit"):
            amt, pct = tab[line][y]
            lo, hi = max(lo, amt / ((pct + 0.05) / 100)), min(hi, amt / ((pct - 0.05) / 100))
        if lo > hi:
            raise ValueError(f"{y}: the DBCC's rounded shares admit no common GDP ({lo:,.0f} > {hi:,.0f})")
        out[y], iv[y] = (lo + hi) / 2, (lo, hi)
    out["_interval"], out["_source"] = iv, src
    return out


def nominal_gdp_path(years, base=None) -> dict:
    """{year: nominal GDP, P bn}: BTr's (PSA's) GDP for the years in the BTr file (to 2025), the DBCC-implied GDP for 2026-2030."""
    path = Path((base or {}).get("path") or BTR_ANNUAL)
    st = pd.read_excel(path, sheet_name="NG OS Debt 1986-2025", header=None)
    hs = next(i for i in range(10) if len(_year_cols(st, i)) > 10)
    ys = _year_cols(st, hs)
    r_gdp = _find(st, "GDP", start=_find(st, "External (P Million)"))
    dbcc = dbcc_nominal_gdp()
    out = {}
    for y in years:
        y = int(y)
        if y in ys:
            out[y] = float(st.iat[r_gdp, ys[y]]) / 1e3
        elif y in dbcc:
            out[y] = float(dbcc[y])
        else:
            raise ValueError(f"no nominal GDP for {y}: BTr's file ends in {max(ys)}, the DBCC's program in 2030")
    return out


def btr_financing_mix(year=2025, path=None) -> dict:
    """The NG's net financing of `year` (BTr, National Government Financing, GFSM 2014, P million): net external and net domestic
    borrowings and the external share, external / (external + domestic). A sourced default for the share of a deficit change
    borrowed abroad (2023 0.350, 2024 0.307, 2025 0.214 in the file of 14 Nov 2026)."""
    path = Path(path or BTR_FINANCING)
    df = pd.read_excel(path, sheet_name="2004-2025", header=None)
    hs = next(i for i in range(10) if len(_year_cols(df, i)) > 10)
    ys = _year_cols(df, hs)
    r_ext, r_dom = _find(df, "Net External Borrowings", ncols=3), _find(df, "Net Domestic Borrowings", ncols=3)
    r_fin = _find(df, "FINANCING", ncols=3)
    ext, dom, fin = (float(df.iat[r, ys[int(year)]]) / 1e3 for r in (r_ext, r_dom, r_fin))
    return dict(year=int(year), net_external=ext, net_domestic=dom, financing=fin, foreign_share=ext / (ext + dom),
                source=f"BTr, National Government Financing ({path.name}), {year}")


def _borrowing_by_year(d, sim):
    """{year: the path's extra government borrowing, model units at the path's prices}: the gfin column gov_borrowing when the path
    was solved with gfin, else CPI x the baseline's real government saving less the path's government saving (the same quantity)."""
    if "gov_borrowing" in sim.table.columns:
        return {int(t): float(v) for t, v in sim.table["gov_borrowing"].items()}
    out = {}
    for t, s in sim.solutions.items():
        b = d.base.solutions[t]
        out[int(t)] = float(s["CPI"]) * float(b["GSAV"]) / float(b["CPI"]) - float(s["GSAV"])
    return out


def scenario_debt(d, sim, foreign_share=None, base=None, nominal_gdp=None, rate_dom=None, rate_ext=None, exr="model",
                  base_ratio=None, years=None, prices="real") -> pd.DataFrame:
    """National government debt after a DynamicCGE scenario path (opt-in; nothing in the model changes).
    d: the DynamicCGE whose baseline the path was run against; sim: the Path (scenario(), monetary_scenario()).
    The year's extra borrowing (model units: P bn of the 2023 SAM's scale x the year's index) is turned into pesos of the year by the
    ratio of the year's nominal GDP (nominal_gdp, default nominal_gdp_path: BTr/PSA, then the DBCC's program) to the baseline's
    nominal GDP in the model, and financed by debt_path: foreign_share = gfin's share when the model ran with gfin (the same split
    the model used), else BTr's net financing mix of 2025 (btr_financing_mix); exr 'model' = the path's peso against the baseline's
    (revalues the extra foreign debt; 1 in short-run years with the fixed peso), None = no revaluation; rates: BTr's 2025 effective
    rates (nominal: the baseline's nominal GDP path carries the baseline's inflation); base_ratio: the baseline debt-to-GDP (default
    BTr's end-2025 ratio held).
    prices: 'real' (default) = the borrowing at the BASELINE's prices (the path's borrowing / its CPI x the baseline's CPI) and
    gdp_ratio = the path's real GDP / the baseline's; 'path' = the borrowing at the path's prices and gdp_ratio = nominal GDP / the
    baseline's. Why 'real': in the model a short-run year moves the price level (the peso is the numeraire there) and the next
    long-run year resets it (the CPI is the numeraire there; the price level is not modelled across years), so 'path' would put a
    one-year price jump into the debt ratio's denominator and take it out the next year (in the GF2 test case 0.13 pp in 2026 against
    1.45 pp in 2027). 'real' leaves a shock's own effect on the price level out of the debt arithmetic (a limit, noted in the design
    note); in long-run years the two agree.
    Returns debt_path's table plus borrowing_model, scale (P bn of the year per model unit), deficit_chg_pct_gdp and the inputs;
    .attrs records the sources and the foreign share used."""
    if prices not in ("real", "path"):
        raise ValueError("prices must be 'real' (at the baseline's prices, default) or 'path'")
    gf = (getattr(d, "a", {}) or {}).get("gfin")
    if foreign_share is None:
        if gf is not None:
            foreign_share, fs_src = float(gf.get("foreign", 0.0)), "DynamicCGE gfin (the share the model ran with)"
        else:
            mix = btr_financing_mix()
            foreign_share, fs_src = mix["foreign_share"], mix["source"]
    else:
        foreign_share, fs_src = float(foreign_share), "given"
        if gf is not None and abs(foreign_share - float(gf.get("foreign", 0.0))) > 1e-12:
            raise ValueError("foreign_share differs from the share the model ran with (gfin): leave it None")
    base = base or btr_debt_base()
    bor = _borrowing_by_year(d, sim)
    bt, st = d.base.table, sim.table
    if prices == "real":                     # at the baseline's prices of the year
        bor = {y: v / float(st.loc[y, "cpi"]) * float(bt.loc[y, "cpi"]) for y, v in bor.items()}
    years = sorted(bor) if years is None else sorted(int(y) for y in years)
    ngdp = nominal_gdp or nominal_gdp_path(years)
    scale = {y: float(ngdp[y]) / float(bt.loc[y, "nominal_gdp"]) for y in years}
    chg = {y: bor[y] * scale[y] for y in years}
    gcol = "real_gdp" if prices == "real" else "nominal_gdp"
    gdp_ratio = {y: float(st.loc[y, gcol]) / float(bt.loc[y, gcol]) for y in years}
    ex = None if exr is None else ({y: float(st.loc[y, "exr"]) / float(bt.loc[y, "exr"]) for y in years} if exr == "model" else exr)
    tab = debt_path(chg, base=base, foreign_share=foreign_share, rate_dom=rate_dom, rate_ext=rate_ext, exr=ex,
                    baseline_gdp={y: float(ngdp[y]) for y in years}, gdp_ratio=gdp_ratio, base_ratio=base_ratio)
    tab.insert(0, "borrowing_model", pd.Series(bor).reindex(tab.index))
    tab.insert(1, "scale", pd.Series(scale).reindex(tab.index))
    tab.insert(2, "deficit_chg_pct_gdp", pd.Series({y: chg[y] / (float(ngdp[y]) * gdp_ratio[y]) * 100 for y in years}).reindex(tab.index))
    tab["nominal_gdp_base"] = pd.Series({y: float(ngdp[y]) for y in years}).reindex(tab.index)
    tab["gdp_ratio"] = pd.Series(gdp_ratio).reindex(tab.index)
    tab["exr_index"] = pd.Series(ex if isinstance(ex, dict) else {y: 1.0 for y in years}).reindex(tab.index)
    tab.attrs.update({"foreign_share": foreign_share, "foreign_share_source": fs_src, "debt_base": base["source"], "prices": prices,
                      "rate_dom": base["rate_dom"] if rate_dom is None else float(rate_dom),
                      "rate_ext": base["rate_ext"] if rate_ext is None else float(rate_ext),
                      "nominal_gdp": "given" if nominal_gdp is not None else
                      f"BTr GDP to {base['year']}; then {dbcc_nominal_gdp()['_source']}"})
    return tab
