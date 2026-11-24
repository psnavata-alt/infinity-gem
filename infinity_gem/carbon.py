"""Carbon tax and the electricity-fuels energy bundle: sourced inputs (0.4.3, 21 Nov 2026; opt-in).

Ideas from OPEN-GEM (E3Modelling 2025, github.com/e3modelling/OPEN-GEM, licence AGPL 3.0 with the Commons Clause: read, cited,
NOT copied; MODEL/05_Model_Equations.gms lines 33-36, 115-125, 370-383) and MANAGE-WB (World Bank PRWP 11258, 2025), written
as Infinity GEM's own code in infinity_gem/cge.py (CGE(energy_nest=..., carbon=...), shock key 'ctax'). Design note:
a design note (not included). RESEARCH, NOT FOR CITATION; nothing here is a default.

What is here
  intensities_2023()      CO2 per peso of each fuel bought on Infinity GEM SAM v1.0 (carbon= argument of CGE), read from
                          data/processed/carbon_intensities_2023_row160.csv, which is NOT in this repository: it holds GTAP
                          10A 2014 CO2 and energy volumes for the Philippines (GTAP licence), with DOE generation, DOE/PSA
                          energy supply and the SAM; pass your own table with the same keys (intensities_2023(path)).
  NEST_SPLIT_*            two-level energy bundles with sourced elasticities (MANAGE-WB's bridge-file defaults; OPEN-GEM's as a
                          sensitivity).
  rate_from_rmb(rmb)      a carbon price in RMB per tonne of CO2 in 2023 pesos (BIS 2023 annual averages), for the cited
                          illustrative rates RMB 30, 60 and 90 (Zhou et al. 2011, as reported by Castillo et al. 2018, PIDS DP
                          2018-41, p. 27).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import paths

INTENSITY_FILE = paths.DATA_PROCESSED / "carbon_intensities_2023_row160.csv"

# The bundle's commodities on Infinity GEM SAM v1.0: electricity (celec) and the fuels it separates, refined petroleum (cpetr) and coal
# (ccoal). Natural gas sits inside mining products (cmine) with crude oil and ores, so it stays a Leontief input (its CO2 is
# taxed through 'ef_act' on the power plants' cmine; see the design note, "Parked").
ENERGY = ["celec", "cpetr", "ccoal"]
FUELS = ["cpetr", "ccoal"]

# MANAGE-WB bridge-file defaults (external/MANAGE-WB-main/dat/BridgeFile_GTAP_9_template.xlsx, sheet 'pnest': 'ener' 0.5,
# 'ener_fossil' 0.5, 'ener_gasoil' 0.7;: 'ener' holds electricity (ely_tnd), petroleum products (c-p_c) and the fossil
# bundle, 'ener_fossil' holds coal and the gas-oil bundle; sheet 'actPar': 'cap_labsk_ener' old capital 0.1, new capital 0.8,
# every activity; 'ener' Eps for a-OTP, land transport; printed in World Bank PRWP 11258 (2025), Figure 2.2, p. 13). Restricted
# to electricity, petroleum products and coal, MANAGE-WB's tree is one CES at 0.5, so sigma_e = sigma_f = 0.5 here. Land
# transport's 'Eps' (GAMS: zero) is approximated by 0.01, the Leontief limit check EN1 uses; on Infinity GEM's own SAM it goes to all of
# transport (atran), whose fuel is mostly road fuel.
_TRANSPORT_LEONTIEF = {"atran": 0.01}
NEST_SPLIT_MWB_LR = {"energy": ENERGY, "fuels": FUELS, "sigma_ve": 0.8, "sigma_e": 0.5, "sigma_f": 0.5,
                     "sigma_e_act": dict(_TRANSPORT_LEONTIEF)}
NEST_SPLIT_MWB_SR = {**NEST_SPLIT_MWB_LR, "sigma_ve": 0.1}
# MANAGE-WB applies these values in its 'additive' (volume-preserving) CES (PRWP 11258, eq. 3-4, pp. 14-15); Infinity GEM's bundle is
# the standard CES, as its; the parameter is the same, the forms differ off the benchmark in how the parent volume is counted.
# OPEN-GEM: sn5 (electricity vs the fuel bundle) 0.90 and sn6 (between fuels) 0.90 (MODEL/03_Calibration.gms lines 387-388; no
# source given in the file). A sensitivity only; it, too, is one level (sn5 = sn6).
NEST_SPLIT_OPENGEM_LR = {"energy": ENERGY, "fuels": FUELS, "sigma_ve": 0.8, "sigma_e": 0.9, "sigma_f": 0.9}

# Illustrative carbon prices: RMB 30, 60 and 90 per tonne of CO2, the rates Zhou et al. (2011) simulated for China, as reported by
# Castillo, Clarete, Muyrong, Tuano and Banaag (2018), PIDS Discussion Paper 2018-41, p. 27 (a reference copy (not distributed)
# Castillo_et_al_2018_PIDS_DP2018-41_TRAIN_coal_and_petroleum_excise_taxes_CGE_2012_IO.pdf). Not a Philippine proposal: the
# Philippines has no carbon tax; these are the only carbon prices with a page in the project's files (design note, "Tax rates").
ILLUSTRATIVE_RMB = (30.0, 60.0, 90.0)


def intensities_2023(path: Path | None = None) -> dict:
    """The carbon= argument of CGE for Infinity GEM SAM v1.0: {'ef': {'cpetr', 'ccoal'}, 'ef_act': {'cmine': {'aelec'}}, 'source'}, in
    Mt CO2 per PHP bn bought at benchmark prices (= kg CO2 per peso)."""
    f = Path(path) if path else INTENSITY_FILE
    d = pd.read_csv(f, comment="#").set_index("key")["value"]
    get = lambda k: float(d[k])
    return {"ef": {"cpetr": get("CO2 per peso of oil products bought (cpetr, every domestic buyer)"),
                   "ccoal": get("CO2 per peso of coal bought (ccoal, every buyer)")},
            "ef_act": {"cmine": {"aelec": get("CO2 per peso of mining products bought by electricity (cmine, aelec only: its gas)")}},
            "source": f"{f.name} (research/carbon_row160/emission_factors_2023.py)"}


def _bis_2023(area: str) -> float:
    """BIS WS_XRU, local currency per US$, 2023 average of the monthly averages (data/raw/macro/panel_bis)."""
    p = paths.DATA_RAW / "macro" / "panel_bis" / "BIS_WS_XRU_panel_monthly_average.csv"
    d = pd.read_csv(p, comment="#")
    s = d[(d["REF_AREA"] == area) & d["TIME_PERIOD"].astype(str).str.startswith("2023")]["OBS_VALUE"].astype(float)
    if len(s) != 12:
        raise ValueError(f"BIS 2023 monthly rates for {area}: {len(s)} months on file, need 12")
    return float(s.mean())


def rate_from_rmb(rmb: float) -> float:
    """RMB per tonne of CO2 -> PHP per tonne at the 2023 BIS annual averages (PHP per US$ / CNY per US$). 2023 pesos, the SAM's."""
    return float(rmb) * _bis_2023("PH") / _bis_2023("CN")
