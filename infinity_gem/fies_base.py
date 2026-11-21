"""Which household survey the poverty microsimulation starts from (0.4.2, 18 Nov 2026).

    from infinity_gem.microlink import MicroLink
    ml = MicroLink(model)                     # the default base: FIES 2025 since 18 Nov 2026 (settings.DEFAULT_FIES_BASE; check R41F)
    ml = MicroLink(model, base="fies2023")    # FIES 2023: every new-poor figure published before 18 Nov 2026 (checks R0, R4, R41, R42)
    ml = MicroLink(model, base="fies2025")    # PSA's FIES 2025 public-use file, PSA's 2025 lines (check FB1)

The default (0.4.2, 18 Nov 2026):
base=None means default(): the environment variable INFINITY_GEM_FIES_BASE if set ("fies2023" or "fies2025"), else
settings.DEFAULT_FIES_BASE ("fies2025"). It is read at each call, so a script (or a check) that sets INFINITY_GEM_FIES_BASE before it
builds its households gets that base. Published and frozen results are reproduced with INFINITY_GEM_FIES_BASE="fies2023" (the check suite
sets it) or base="fies2023". Up to 18 Nov 2026 the default was "fies2023" and "fies2025" was opt-in.
The LFS earnings link (HouseholdDetail.earnings_by_industry, lfs=True) needs PSA's FIES-LFS member file of the same survey; only
FIES-LFS 2023 exists, so on the 2025 base it raises an error that says to pass base="fies2023". It never falls back silently.

Bases
  "fies2023" (the default up to 18 Nov 2026): PSA's FIES-LFS 2023 public-use file, household summary (paths.FIES_PUF), and the
             extract with PSA's official 2023 per-capita poverty and food thresholds (paths.FIES_POVLINES); per-capita
             income = TOINC / FSIZE; 17.54 M poor (check P1).
  "fies2025": PSA's FIES 2025 public-use file, Volume 1 (paths.FIES_2025_PUF; each user downloads it from PSA), and PSA's
             2025 thresholds by province x urban/rural (PSA, 2025 Full Year Official Poverty Statistics, rev. 30 Oct 2026,
             Table 16), matched to each family's province and urban/rural area (paths.FIES_2025_POVLINES: columns w_prov,
             urban, pline_2025, fline_2025; the tool that builds and checks it is not in this repository); per-capita income = PERCAPITA (PSA's own variable); 11.08 M poor, 9.73% (PSA 9.7%).

The 2025 file is read with the 2023 file's variable names, so every rule in household.py and microlink.py applies
unchanged. What differs between the two surveys (dictionary: PSA's metadata workbook of the FIES 2025 Volume 1 file):
  SEQNO -> SEQ_NO, URBAN -> URB (1 urban, 2 rural in both);
  four beverage categories renamed by PSA: FRUIT_VEG_JUICES -> FRUIT_VEG, MINERAL -> WATER (mineral/bottled water),
    SOFT_DRINKS -> SOFTDRINKS, OTHER_NON_ALCOHOLIC -> OTHER_NON_ALCOHOL (same contents: COICOP 01.2 sub-classes);
  entrepreneurial income: 2023 has seven named activities and three 'not elsewhere classified' items (NET_NEC_A8, A9,
    A10); 2025 names 23 activities (adds mining, solar electricity, construction, accommodation, food service, ICT,
    finance, real estate, professional, administrative, education, health, social work, arts, other services, and
    NET_NEC). The seven 2023 activities (crops, livestock, fishing, forestry, retail, manufacturing, transport) are the
    same variables; the 2025-only activities and NET_NEC are summed into NET_NEC_A8 (NET_NEC_A9 = NET_NEC_A10 = 0).
    Only the LFS link reads NET_NEC_*, and it is not available on the 2025 base (no FIES-LFS 2025 member file);
    the net-seller adjustment reads NET_CFG, NET_LPR and NET_FISH, which are the same in both;
  per-capita income: PSA's PERCAPITA (it differs from TOINC / FSIZE by at most PHP 0.21, a rounding in PSA's file;
    the lines are compared with PERCAPITA in PSA's published 2025 count, so the 2025 base uses it);
  W_REGN has 18 regions in 2025 (Negros Island Region, 18); the microsimulation does not use the region.
Households are put in the SAM's ten groups the same way on both bases: urban/rural (URB) x national per-capita income
quintile from PSA's decile NPCINC (2025 deciles on the 2025 base).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import paths

BASES = ("fies2023", "fies2025")
ENV = "INFINITY_GEM_FIES_BASE"                        # 18 Nov 2026: the environment override of settings.DEFAULT_FIES_BASE (default())
LABEL = {"fies2023": "FIES 2023", "fies2025": "FIES 2025"}
DESCRIPTION = {"fies2023": "FIES 2023 public-use file (PSA), Household Sum",
               "fies2025": "FIES 2025 public-use file (PSA), Volume 1; PSA 2025 thresholds (Table 16, rev. 30 Oct 2026)"}

# PSA's published figures that each base must reproduce before any shock (check P1 for 2023; check FB1 for 2025).
# 2025: PSA, 2025 Full Year Official Poverty Statistics (press release 2026-272, 21 Aug 2026; tables rev. 30 Oct 2026):
# 9.7% of the population, 6.4% of families; magnitudes 11,083.03 thousand persons, 1,904.87 thousand families (Tables 5-6),
# subsistence 2,295.02 thousand persons, 361.09 thousand families (Tables 7-8).
OFFICIAL = {"fies2023": {"Poor persons": 17_540_000},
            "fies2025": {"Poor persons": 11_083_030, "Poor families": 1_904_870, "Food-poor persons": 2_295_020,
                         "Food-poor families": 361_090, "incidence, population (%)": 9.7, "incidence, families (%)": 6.4}}

RENAME_2025 = {"SEQNO": "SEQ_NO", "URBAN": "URB", "FRUIT_VEG_JUICES": "FRUIT_VEG", "MINERAL": "WATER",
               "SOFT_DRINKS": "SOFTDRINKS", "OTHER_NON_ALCOHOLIC": "OTHER_NON_ALCOHOL"}
NET_2025_ONLY = ["NET_MIN", "NET_SOLAR", "NET_CONS", "NET_ACCOM", "NET_FOOD", "NET_ICT", "NET_FIN", "NET_REAL", "NET_PROF",
                 "NET_ADMIN", "NET_EDUC", "NET_HEALTH", "NET_SOCIAL", "NET_ARTS", "NET_OTHERS", "NET_NEC"]

_CACHE: dict = {}


def check(base: str) -> str:
    if base not in BASES:
        raise ValueError(f"base must be one of {BASES}, not {base!r}")
    return base


def default() -> str:
    """The base used when none is named (18 Nov 2026): environment INFINITY_GEM_FIES_BASE if set, else settings.DEFAULT_FIES_BASE."""
    import os
    from .settings import DEFAULT_FIES_BASE
    env = os.environ.get(ENV, "").strip().lower()
    if env and env not in BASES:
        raise ValueError(f"{ENV} must be one of {BASES}, not {env!r}")
    return env or check(DEFAULT_FIES_BASE)


def resolve(base: str | None) -> str:
    """base as given (checked), or default() when None."""
    return default() if base is None else check(base)


def lfs_refusal(base: str) -> str:
    """The message when the LFS earnings link is asked for on a base without a FIES-LFS member file (18 Nov 2026)."""
    from .settings import DEFAULT_FIES_BASE
    return (f"the LFS earnings link needs PSA's FIES-LFS member file of the same survey, and only FIES-LFS 2023 exists; this run is on "
            f"the {LABEL.get(base, base)} base. Pass base=\"fies2023\" (HouseholdDetail, MicroLink) or set {ENV}=fies2023 to use the "
            f"LFS link (the default base is {LABEL.get(DEFAULT_FIES_BASE, DEFAULT_FIES_BASE)} since 18 Nov 2026)")


def __getattr__(name):                         # DEFAULT, as before 18 Nov 2026: the base used when none is named
    if name == "DEFAULT":
        return default()
    raise AttributeError(name)


def poverty_lines_2025(path=None) -> pd.DataFrame:
    """PSA's 2025 annual per-capita poverty and food thresholds by FIES province code (w_prov) x urban (1) / rural (2)."""
    return pd.read_csv(path or paths.FIES_2025_POVLINES)


def households_2025(puf=None, povlines=None) -> pd.DataFrame:
    """The FIES 2025 public-use file in the 2023 file's variable names (module notes), one row per family in the file's
    order, with PLINE and FLINE (PSA's 2025 lines, by province x urban/rural) and PCI = PERCAPITA. Read once per
    session (a copy is returned)."""
    key = (str(puf or paths.FIES_2025_PUF), str(povlines or paths.FIES_2025_POVLINES))
    if key not in _CACHE:
        f = pd.read_csv(key[0]).rename(columns=RENAME_2025)
        f = pd.concat([f, pd.DataFrame({"NET_NEC_A8": f[NET_2025_ONLY].sum(axis=1), "NET_NEC_A9": 0.0, "NET_NEC_A10": 0.0},
                                       index=f.index)], axis=1)
        lines = poverty_lines_2025(key[1])
        n = len(f)
        f = f.merge(lines[["w_prov", "urban", "pline_2025", "fline_2025"]].rename(columns={"w_prov": "W_PROV", "urban": "URB"}),
                    on=["W_PROV", "URB"], how="left", validate="m:1")
        if len(f) != n or f["pline_2025"].isna().any():
            raise ValueError(f"FIES 2025: {int(f['pline_2025'].isna().sum())} families without a PSA threshold")
        f = f.copy().assign(PLINE=f["pline_2025"].astype(float), FLINE=f["fline_2025"].astype(float), PCI=f["PERCAPITA"].astype(float))
        _CACHE[key] = f
    return _CACHE[key].copy()
