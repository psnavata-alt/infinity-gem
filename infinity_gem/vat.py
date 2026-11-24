"""VAT detail of the taxes on products (0.4.3, 21 Nov 2026). OPT-IN; the engine does not import this
module; no SAM file, engine or default changed. Design note: a design note (not included).

Infinity GEM's own SAM v1.0 has ONE row of taxes on products ('stax', P1,837.3 bn in 2023), which the CGE turns into one rate per commodity
(cge.CGE.tq = stax / base). The SAM builder (tools/build_own_sam_2023.py, tax_block and fuel_tax_v10) built that row from DBM's
BESF 2025 Table C.3 2023 actuals as VAT (BIR VAT net of refunds + BOC VAT on imports, P1,007.257 bn, spread over each commodity's
final demand x VAT_WEIGHT: 0 for raw farm and fish products, milled rice, education, health, finance and public administration,
0.5 for real estate and transport) plus the excises, percentage taxes, documentary stamp and franchise taxes line by line; v1.0 then
set fuel's VAT at P85.136 bn and rescaled the other commodities' VAT so that total VAT stays BESF's. The builder saved that
decomposition (outputs/own_sam_2023_v1.0_20261025_0204_fuel_tax_by_commodity.csv; not in this repository: the v1.0 build
that writes it needs files that are not distributed, so check VT1 reports NOT RUN here). This module reads it back, so the split is the
builder's own, not a new estimate:
  stax_c = VAT_c + other_c      (other = excises, percentage taxes, documentary stamp tax, franchise tax)
Coal ('ccoal', split from mining in v0.7, after the tax block) shares mining's taxes in the file's proportions.

What step 1 gives: (i) the VAT and non-VAT parts of every commodity's tax rate; (ii) vat_rate_shock(): a change of the 12% VAT rate as
a 'tq_scale' shock (the engine's existing sales-tax lever), scaling only each commodity's VAT part. LIMIT (stated, not fixed): the
engine levies tq on ALL purchases of a commodity, intermediate ones included, while a real VAT is credited on registered firms'
inputs; step 1 therefore spreads a VAT change the way the SAM spreads VAT today. A true VAT account (levied on final demand and on
exempt sectors' inputs, zero-rated exports) is step 2: an engine change, parked (design note section 4).
Check: VT1 (checks/test_vat_row162.py).
"""
from __future__ import annotations

import pandas as pd

from . import paths

TABLE = "own_sam_2023_v1.0_20261025_0204_fuel_tax_by_commodity.csv"      # in paths.OUTPUTS; written by the v1.0 build
VAT_2023 = 1007.257          # P bn: BIR 'Gen. Sales, Turnover or VAT (Net of VAT Refunds)' 475.244 + BOC 'VAT on Imports' 532.013
VAT_RATE = 0.12              # NIRC Sec. 106-108 (as amended), the statutory rate in 2023
SPLIT_FROM = {"ccoal": "cmine"}                                             # SAM v0.7: coal split from mining after the tax block


def _outputs():
    return paths.OUTPUTS


def decomposition(sam=None) -> pd.DataFrame:
    """P bn by commodity, 2023: 'stax' (the SAM's row), 'VAT', 'other' (excises, percentage taxes, DST, franchise), 'VAT share'.
    sam: a infinity_gem.sam.SAM (None = the default SAM v1.0). Raises if the builder's table does not belong to this SAM."""
    from .sam import SAM
    S = SAM.load(paths.SAM_2023_OWN) if sam is None else sam
    st = S.table.loc["stax"].astype(float)
    st = st[st.abs() > 1e-12]
    t = pd.read_csv(_outputs() / TABLE, index_col=0)
    bal = t["stax v1.0 (balanced file)"]
    vat = t["VAT part, v1.0"]
    oth = t["excise and other taxes"]
    rows = {}
    for c, v in st.items():
        if c in bal.index:
            if abs(float(bal[c]) - float(v)) > 1e-6:
                raise ValueError(f"vat.decomposition: the builder's table gives stax {bal[c]:.6f} for {c}, the SAM {v:.6f}")
            share = float(vat[c]) / float(vat[c] + oth[c]) if float(vat[c] + oth[c]) != 0 else 0.0
        elif c in SPLIT_FROM:
            p = SPLIT_FROM[c]
            share = float(vat[p]) / float(vat[p] + oth[p])
        else:
            raise ValueError(f"vat.decomposition: {c} has taxes on products in the SAM but no line in {TABLE}")
        rows[c] = {"stax": float(v), "VAT": float(v) * share, "other": float(v) * (1 - share), "VAT share": share}
    d = pd.DataFrame(rows).T
    if abs(float(d["VAT"].sum()) - VAT_2023) > 1e-6:
        raise ValueError(f"vat.decomposition: VAT adds to {d['VAT'].sum():.6f}, BESF 2023 gives {VAT_2023}")
    return d


def vat_rate_shock(model, new_rate, old_rate=VAT_RATE, sam=None) -> dict:
    """A change of the VAT rate from old_rate to new_rate as the engine's sales-tax lever: {'tq_scale': {commodity: factor}} with
    tq_c x factor_c = (other_c + VAT_c x new_rate / old_rate) / base_c, i.e. factor_c = 1 + VAT share_c x (new_rate / old_rate - 1).
    Commodities without VAT keep factor 1. model: a cge.CGE built on the same SAM (its commodity list is used)."""
    d = decomposition(sam)
    r = float(new_rate) / float(old_rate) - 1.0
    out = {}
    for c in model.C:
        f = 1.0 + (float(d.loc[c, "VAT share"]) * r if c in d.index else 0.0)
        if f != 1.0:
            out[c] = f
    return {"tq_scale": out}
