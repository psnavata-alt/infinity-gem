"""World oil-price shocks with sourced shares (added in 0.3).

With the petroleum-split SAM (paths.SAM_2023_PETR; tools/build_sam_petroleum_split.py) a world oil-price change enters the
CGE where it happens:
  refined petroleum imports (cpetr)   world import price x (1 + oil change)  [product prices assumed to move one-for-one
                                       with crude; Dubai and Singapore product prices co-move]
  crude imports (inside mining, cmine) world import price x (1 + oil change x crude share of mining imports)
The combined 2023 SAM (published results) keeps the old approximation: cchem import price x (1 + oil x 0.6), 0.6 being an
assumed petroleum share of cchem imports. PSA 2018 puts that share at 0.512 (imports column, sectors 107-108 of 107-118).

For the I-O price model the refined-petroleum price change is set directly (IOTable.price). Its pass-through from a world
oil-price change, from PSA's 80-industry table (industry 35, coke and refined petroleum; industry 21, crude petroleum and
natural gas) and the 2018 Supply table (imports of refined petroleum, sector 107):
    p = s_m + (1 - s_m) (c + o p)   ->   p = (s_m + (1 - s_m) c) / (1 - (1 - s_m) o)
s_m = imported share of refined-petroleum supply; c = crude input per peso of refinery output; o = refined petroleum
used per peso of refinery output (blending and own use, whose price also rises). Replaces the assumed 0.6.

Infinity GEM SAM v0.7 (24 Oct 2026; tools/build_own_sam_2023.py 0.7; research, opt-in): coal has its own commodity (ccoal), split
from mining. On a model that has it, the oil shock raises the import price of the rest of mining (cmine: crude oil, gas and
ores) by crude's share of NON-coal mining imports (import_shares()['crude_in_mining_ex_coal'], PSA 2018) and leaves coal
alone. Coal and LNG prices are an opt-in part of the shock: cge_oil_shock(..., coal=, lng=) for one run, coal_lng_shock(m,
year) for a year of coal_lng_paths() (data/processed/coal_lng_price_paths_2026-2030.csv, research/coal_lng_prices/
coal_lng_paths.py). A model without ccoal gets exactly what it got before.
"""
from __future__ import annotations

import numpy as np
import openpyxl
import pandas as pd

from . import paths

PSA_240 = paths.DATA_RAW / "io" / "240-Industry20Table202018.xlsx"
PSA_SUT = paths.DATA_RAW / "io" / "2018 Supply and Use Tables.xlsx"
COAL_LNG_PATHS = paths.DATA_PROCESSED / "coal_lng_price_paths_2026-2030.csv"   # Infinity GEM SAM v0.7 (opt-in coal and LNG prices)


def _imports_240() -> np.ndarray:
    ws = openpyxl.load_workbook(PSA_240, read_only=True, data_only=True)["240 TT"]
    rows = list(ws.iter_rows(values_only=True))
    j = [str(h).strip() if h else "" for h in rows[9]].index("Imports of Goods and Services")
    return np.array([float(rows[9 + i][j] or 0) for i in range(1, 241)])


# The three shares below, computed by import_shares() from PSA's 2018 240-industry input-output table (imports
# column, data/raw/io). Stored so that a copy without PSA's tables still runs; recomputed from the table when it is there.
IMPORT_SHARES_PSA2018 = {"crude_in_mining": 0.6765750743551517, "fertilizer_in_chemicals": 0.025993988387202443,
                         "petroleum_in_chem_and_petroleum": 0.5122653869965557}


def import_shares() -> dict:
    """Shares in PSA 2018 imports (240-industry table, imports column)."""
    if not PSA_240.exists():
        return dict(IMPORT_SHARES_PSA2018)
    m = _imports_240()
    mining = m[38:45].sum()                       # sectors 39-45
    chem = m[108:118].sum()                       # sectors 109-118
    return {"crude_in_mining": float(m[39] / mining),                 # sector 40 crude petroleum and natural gas
            "crude_in_mining_ex_coal": float(m[39] / (mining - m[38])),   # Infinity GEM SAM v0.7: of mining imports less coal (39)
            "fertilizer_in_chemicals": float(m[109] / chem),          # sector 110 fertilizers and nitrogen compounds
            "petroleum_in_chem_and_petroleum": float(m[106:108].sum() / (m[106:108].sum() + chem))}


def io_refined_passthrough(io=None) -> dict:
    """Pass-through of a world oil-price change to the price of refined petroleum in the I-O price model."""
    from .iomodel import IOTable
    io = io or IOTable()
    k = next(i for i, n in enumerate(io.names) if n.startswith("Coke and refined petroleum"))
    cr = next(i for i, n in enumerate(io.names) if n.startswith("Crude petroleum"))
    X = io.Z.sum(axis=0) if not hasattr(io, "X") else io.X
    c = float(io.Z[cr, k] / X[k])
    o = float(io.Z[k, k] / X[k])
    ws = openpyxl.load_workbook(PSA_SUT, read_only=True, data_only=True)["240_Supply"]
    rows = list(ws.iter_rows(values_only=True))
    hdr = [str(h).strip() if h else "" for h in rows[9]]
    jd, jm = hdr.index("Total Domestic Production"), hdr.index("Total Imports")
    r107 = next(r for r in rows if r[3] is not None and str(r[3]).strip() == "107")
    s_m = float(r107[jm]) / (float(r107[jd]) + float(r107[jm]))
    p = (s_m + (1 - s_m) * c) / (1 - (1 - s_m) * o)
    return {"passthrough": p, "import_share": s_m, "crude_coef": c, "own_use_coef": o}


def cge_oil_shock(m, oil: float, fertilizer: float = 0.0, combined_share: float = 0.6, coal: float | None = None,
                  lng: float | None = None) -> dict:
    """CGE shock spec for a world oil-price change `oil` (0.40 = +40%) and optionally a fertilizer price change.
    Uses the split SAM's accounts when the model has 'cpetr'; otherwise the old combined approximation.
    Infinity GEM SAM v0.7 (a model with coal split from mining, 'ccoal'; 24 Oct 2026): mining's import price moves by crude's share of
    non-coal mining imports and coal's not at all, unless the opt-in changes are given: coal (0.30 = +30%) raises coal's world
    import price; lng (0.30 = +30%) power plants' gas (lng_cost_shock). Both need 'ccoal'. Without them, and on any model
    without 'ccoal', the result is exactly as before."""
    sh = import_shares()
    pwm = {}
    if "cpetr" in m.C:
        pwm["cpetr"] = 1 + oil
        pwm["cmine"] = 1 + oil * sh["crude_in_mining_ex_coal" if "ccoal" in m.C else "crude_in_mining"]
        if fertilizer:
            pwm["cchem"] = 1 + fertilizer * sh["fertilizer_in_chemicals"]
    else:
        pwm["cchem"] = 1 + oil * combined_share
    out = {"pwm_scale": pwm}
    if coal is not None or lng is not None:                         # Infinity GEM SAM v0.7 only (opt-in)
        if "ccoal" not in m.C:
            raise ValueError("coal and LNG price changes need a SAM with coal split from mining ('ccoal': Infinity GEM SAM v0.7)")
        if coal is not None:
            pwm["ccoal"] = 1 + coal
        if lng is not None:
            out.update(lng_cost_shock(m, lng))
    return out


def lng_cost_shock(m, change: float) -> dict:
    """Infinity GEM SAM v0.7 (opt-in, 24 Oct 2026): a change in the world price of LNG (0.30 = +30%) borne by power plants' natural
    gas. In v0.7 electricity's purchases from the mining account (cmine) are its natural gas (₱29.5 bn) with a little other
    mining (₱4.3 bn; its coal is ccoal), and the 2023 SAM's mining imports hold almost no LNG (imports began in 2023), so the
    change cannot enter as an import price. As fertilizer_cost_shock does for fertilizer, electricity's unit cost rises by
    its gas cost share (all of its cmine purchases: an overstatement by the other mining, about an eighth) x the change,
    entered as the equivalent loss of value-added productivity, tfp' = 1 / (1 + s x / iva); the extra gas bill itself goes to
    no one (an approximation: in 2026 it went abroad for LNG and to the gas producers under oil-linked contracts)."""
    if "ccoal" not in m.C or "aelec" not in m.A:
        raise ValueError("lng_cost_shock needs a SAM with coal split from mining ('ccoal': Infinity GEM SAM v0.7)")
    t = m.sam.table
    s = float(t.loc["cmine", "aelec"]) / float(t["aelec"].sum())
    return {"tfp_scale": {"aelec": 1.0 / (1.0 + s * change / float(m.iva[m.A.index("aelec")]))}}


COAL_LNG_PATHS_PSA = paths.DATA_PROCESSED / "coal_lng_price_paths_2026-2030_psa_coal.csv"   # coal_series="psa" (24 Oct 2026)


def coal_lng_paths(coal_series: str = "world_bank") -> pd.DataFrame:
    """Infinity GEM SAM v0.7 (opt-in): world coal and LNG price changes by calendar year, % against their pre-conflict level
    (COAL_LNG_PATHS, written by research/coal_lng_prices/coal_lng_paths.py; its '#' lines give the sources and say whether
    the World Bank's own coal and LNG series were on disk or a stated proxy was used). coal_series="psa" (opt-in, 24 Oct
    2026): coal from PSA's Philippine import unit values (HS 2701, CIF/kg) instead of Newcastle, LNG unchanged
    (COAL_LNG_PATHS_PSA, written by coal_lng_paths.py --coal psa). The default reads exactly what it read before."""
    if coal_series not in ("world_bank", "psa"):
        raise ValueError("coal_series must be 'world_bank' (the default: Newcastle) or 'psa' (Philippine coal imports)")
    return pd.read_csv(COAL_LNG_PATHS_PSA if coal_series == "psa" else COAL_LNG_PATHS, comment="#").set_index("year")


def coal_lng_shock(m, year: int, coal: bool = True, lng: bool = True, coal_series: str = "world_bank") -> dict:
    """Infinity GEM SAM v0.7 (opt-in): the coal and LNG part of the oil shock in calendar year `year` (coal_lng_paths()), as CGE
    shock keys to merge with cge_oil_shock's: coal's world import price (pwm_scale) and power plants' gas (lng_cost_shock,
    tfp_scale). A year the paths do not cover gives no shock. Needs a model with 'ccoal'. coal_series: as in coal_lng_paths."""
    if "ccoal" not in m.C:
        raise ValueError("coal_lng_shock needs a SAM with coal split from mining ('ccoal': Infinity GEM SAM v0.7)")
    p = coal_lng_paths(coal_series)
    if year not in p.index:
        return {}
    out = {}
    if coal:
        out["pwm_scale"] = {"ccoal": 1 + float(p.loc[year, "coal"]) / 100}
    if lng:
        out.update(lng_cost_shock(m, float(p.loc[year, "lng"]) / 100))
    return out


def fertilizer_cost_shares() -> dict:
    """Fertilizer cost per peso of output by SAM activity, PSA 2018 240-industry table (0.3.7, 15 Oct 2026): purchases
    from sector 110 (fertilizers and nitrogen compounds) / the activity's output (intermediate inputs + compensation +
    operating surplus + net taxes), summed over the PSA sectors of each activity. Only activities that use fertilizer."""
    import sys as _sys
    _sys.path.insert(0, str(paths.ROOT / "tools"))
    from build_sam_petroleum_split import load_psa, psa_activity
    T, fd, va = load_psa()
    out = T.sum(axis=0) + va["COE"] + va["GOS"] + va["T-S"]
    by = {}
    for k in range(1, 241):
        a = psa_activity(k)
        f, o = by.get(a, (0.0, 0.0))
        by[a] = (f + T[109, k - 1], o + out[k - 1])
    return {a: f / o for a, (f, o) in by.items() if o > 0 and f / o > 1e-4}


def fertilizer_cost_shock(m, change: float, shares: dict | None = None) -> dict:
    """CGE shock spec for a fertilizer price change `change` (0.29 = +29%) borne by the activities that use fertilizer
    (0.3.7). The SAM has no fertilizer account (it is inside chemicals, cchem), and raising the price of all chemicals
    would spread the shock over plastics and medicines. Instead each user's unit cost rises by its fertilizer cost share
    (PSA 2018) x the change, entered as the equivalent loss of value-added productivity: tfp' = 1 / (1 + s x / iva), so
    that iva x PVA / tfp' rises by exactly s x per unit of output at base prices. The extra import bill itself is not in
    the balance of payments (fertilizer imports are small next to oil). Returns {'tfp_scale': {activity: factor}}."""
    shares = fertilizer_cost_shares() if shares is None else shares
    return {"tfp_scale": {a: 1.0 / (1.0 + s * change / float(m.iva[m.A.index(a)]))
                          for a, s in shares.items() if a in m.A and m.iva[m.A.index(a)] > 0}}
