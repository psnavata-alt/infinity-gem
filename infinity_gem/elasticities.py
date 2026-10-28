"""Elasticity sets for the CGE (added in 0.3).

    from infinity_gem.elasticities import elasticity_set
    m = CGE.from_sam(elasticities=elasticity_set("ph"))

Sets (built by tools/build_elasticities.py into data/processed/elasticities_ph_v1.csv; sources and grades in
docs/guides/08_PARAMETERS_AND_SOURCES.md):
  "default"  Infinity GEM 0.2: value added 0.8, Armington 2.0, CET 2.0 for every sector (common defaults; placeholder).
  "gtap"     GTAP 9 standard parameters (via the World Bank MANAGE-WB template), aggregated to Infinity GEM sectors with
             Philippine weights: value added ESUBVA by activity, Armington ESUBD by commodity; CET set equal to ESUBD
             (MANAGE-WB's convention: no estimated CET exists).
  "ph"       As "gtap", but Armington from Kapuscinski and Warr (1999), the only econometric Philippine estimates, where
             significant, positive and covering at least half of the sector's imports (13 commodities).
  "ph_pcgem_cet"  As "ph", with CET from Cororaton's PCGEM (2000, Table 3; assumed values) — sensitivity only.
The 2018 SAM's commodities are a subset of the 2023 SAM's, so the same table serves both.
"""
from __future__ import annotations

import pandas as pd

from . import paths
from .cge import DEFAULT_ELASTICITIES

TABLE = paths.DATA_PROCESSED / "elasticities_ph_v1.csv"
# Infinity GEM SAM v0.7 (24 Oct 2026): rows for coal split from mining (ccoal, acoal), with their sources, built by
# tools/add_coal_split_elasticities.py; codes no other SAM has, so every other model's elasticities are unchanged
TABLE_COAL = paths.DATA_PROCESSED / "elasticities_ph_v1_coal_split_v0.7.csv"


def elasticity_set(name: str = "default") -> dict:
    if name == "default":
        return dict(DEFAULT_ELASTICITIES)
    t = pd.read_csv(TABLE)
    if TABLE_COAL.exists():                      # Infinity GEM SAM v0.7 only: coal's rows (codes not in TABLE)
        tc = pd.read_csv(TABLE_COAL)
        t = pd.concat([t, tc[~tc["code"].isin(t["code"])]], ignore_index=True)
    com, act = t[t.kind == "commodity"].set_index("code"), t[t.kind == "activity"].set_index("code")
    va = act.sigma_va_gtap.dropna().to_dict()
    # 0.3.7: rows for the split SAMs' accounts (cpetr/apetr, cmric/amric) come from tools/add_split_elasticities.py;
    # an empty value (PCGEM's CET for them) is dropped, so the CGE's default applies to that code.
    if name == "gtap":
        return {"sigma_va": va, "sigma_q": com.sigma_q_gtap.dropna().to_dict(), "omega_t": com.omega_t_gtap.dropna().to_dict()}
    if name == "ph":
        return {"sigma_va": va, "sigma_q": com.sigma_q_ph.dropna().to_dict(), "omega_t": com.omega_t_gtap.dropna().to_dict()}
    if name == "ph_pcgem_cet":
        return {"sigma_va": va, "sigma_q": com.sigma_q_ph.dropna().to_dict(), "omega_t": com.omega_t_pcgem.dropna().to_dict()}
    if name in SENSITIVITY_SETS:                 # 0.3.9: "ph" with ONE Armington value changed; sensitivity only
        el = elasticity_set("ph")
        code, value, _ = SENSITIVITY_SETS[name]
        el["sigma_q"] = dict(el["sigma_q"], **{code: value})
        return el
    if name in SENSITIVITY_SETS_72BC:            # 0.3.13: "ph" with some sigma_va or omega_t values changed
        el = elasticity_set("ph")
        key, values, _ = SENSITIVITY_SETS_72BC[name]
        el[key] = dict(el[key], **values)
        return el
    raise KeyError(f"Unknown elasticity set '{name}' (default, gtap, ph, ph_pcgem_cet, {', '.join(SENSITIVITY_SETS)}, "
                   f"{', '.join(SENSITIVITY_SETS_72BC)})")


# 0.3.9(a) (17 Oct 2026): Infinity GEM's own Armington evidence for rice and fuel, as opt-in sensitivity sets.
# Neither estimate met the adoption rule, so "ph" keeps GTAP's values (cmric 2.6, cpetr 2.1); these sets change one value.
SENSITIVITY_SETS = {
    "ph_rice72a": ("cmric", 1.24, "milled rice: the project's post-tariffication estimate, 2019Q2-2026Q2, static OLS with quarter dummies and "
                   "an import-suspension dummy (p = 0.096; 0.78-1.24 across samples; not robust); outputs/armington_rice_*.md, "
                   "preshock/armington_rice.py"),
    "ph_fuel_low": ("cpetr", 0.558, "refined petroleum: Kapuscinski and Warr (1999) ECM, coal and petroleum products (not significant); "
                    "the fuel Armington cannot be estimated from the available data (import-parity pricing at Singapore benchmark prices)"),
    "ph_fuel_high": ("cpetr", 4.2, "refined petroleum: GTAP's import-import elasticity ESUBM for P_C (twice ESUBD 2.1, GTAP's rule "
                     "of two), an upper bound for imported versus domestically refined fuel"),
}


# 0.3.13 (24 Oct 2026): own value-added and export (CET) elasticities estimated from PSA data, as opt-in sensitivity
# sets (the estimation scripts and their standalone test are not in this repository; the 18 PSA OpenSTAT tables they read
# are in data/raw/elasticities/PSA_OpenSTAT_72bc_downloaded_2026-10-24/). "ph" keeps GTAP's values either way; these sets
# change only the codes listed. Kept apart from SENSITIVITY_SETS, whose entries (one Armington value each) check E2 reads.
AGRI_ACTIVITIES = ("amaiz", "arice", "apuls", "aoils", "aroot", "avege", "asugr", "atoba", "acott", "afrui", "acoff", "aocrp",
                   "acatt", "apoul", "aoliv", "afore", "afish")
_VA_AGRI = 0.29      # annual ACMS 2005-2025, PSA GVA, LFS employment, farm wage rates (s.e. 0.05; 0.26-0.30 across samples)
SENSITIVITY_SETS_72BC = {
    "ph_va72b": ("sigma_va", {**{a: _VA_AGRI for a in AGRI_ACTIVITIES}, "acons": 1.06},
                 "value added: agriculture, forestry and fishing 0.29 (the project's annual time-series estimate, = GTAP's 0.26 within "
                 "its s.e.); construction 1.06 (ASPBI 2015-2017 establishment cross-section, s.e. 0.21; the time series do not "
                 "identify it); research/elasticities_72bc/va72b.py"),
    "ph_va72b_low": ("sigma_va", {**{a: _VA_AGRI for a in AGRI_ACTIVITIES}, "acons": 0.74},
                     "as ph_va72b, construction 0.74 (ASPBI cross-section with industry fixed effects, s.e. 0.22): the low end "
                     "for the disaster result"),
    "ph_cet72c": ("omega_t", {"cbsrv": 0.20, "chotl": 4.36, "cfrui": 0.49},
                  "export CET: the project's 2SLS point estimates (PHP/USD as instrument, first-stage F >= 10, 2000Q1-2026Q2) where "
                  "positive: business services 0.20 (s.e. 0.79), travel 4.36 (2.76), fresh fruit (bananas) 0.49 (0.39); none "
                  "significant, and OLS is negative or insignificant in every group: the data do not identify the CET (GTAP's values "
                  "stay; electronics' CET is inactive, home sales 0 in the SAMs); research/elasticities_72bc/cet72c.py"),
}
