"""Consumer prices on PSA's own CPI weights, from a model solution (0.3.10, 18 Oct 2026, design note §8
point 4 and §10). Reporting only: nothing here changes the model's equilibrium.

Why: the model's CPI weights are its SAM's household purchases. On IFPRI's SAM they follow FIES shares (fuel 4.8% of the
basket); on Infinity GEM's own SAM they follow PSA's national accounts (HFCE by purpose; fuel 2.5-2.7%, plus imputed rent and FISIM).
Official inflation uses PSA's 2018-based CPI weights. This module prices PSA's CPI groups with the model's price changes, so a
run can report "consumer prices" comparable with PSA's CPI whatever SAM it uses, for all households and for the bottom 30%.

Prices: each PSA CPI group takes the change of a MicroLink FIES category, or of a SAM commodity where the oil channel needs
PSA's own split (electricity, LPG and kerosene, wood fuel, water, repairs, vehicles, vehicle fuel, fares). The map is the one
tested in scenarios/oil_passthrough_by_sam.py (18 Oct 2026, about 3 AM), moved here so every scenario can use it.
Weights: data/raw/cpi/PSA_CPI_weights_2018base_{AllHouseholds,Bottom30}_Philippines.csv (PSA; on file since 0.3.5).
Check PC1 (run_all_checks): the mapped weights sum to 100, and a uniform +10% on every price gives +10%.
"""
from __future__ import annotations

import pandas as pd

from . import paths

FILES = {"all households": "PSA_CPI_weights_2018base_AllHouseholds_Philippines.csv",
         "bottom 30%": "PSA_CPI_weights_2018base_Bottom30_Philippines.csv"}
CPI_MAP = {
    "01.1.1": "BREAD", "01.1.2": "MEAT", "01.1.3": "FISH", "01.1.4": "MILK", "01.1.5": "OIL", "01.1.6": "FRUIT",
    "01.1.7": "VEG", "01.1.8": "SUGAR", "01.1.9": "FOOD_NEC",
    "01.2.1": "FRUIT_VEG", "01.2.2": "COFFEE", "01.2.3": "TEA", "01.2.4": "COCOA", "01.2.5": "WATER",
    "01.2.6": "SOFTDRINKS", "01.2.9": "OTHER_NON_ALCOHOL",
    "02.1": "ALCOHOL", "02.3": "TOBACCO", "02.4": "TOBACCO",
    "03": "CLOTH",
    "04.1": "RENT", "04.3": "c:ccons", "04.4": "c:cwatr", "04.5.1": "c:celec", "04.5.2": "c:cpetr", "04.5.3": "c:cpetr",
    "04.5.4": "c:cfore",
    "05": "FURNISHING", "06": "HEALTH",
    "07.1": "c:cmach", "07.2.1": "c:cmach", "07.2.2": "c:cpetr", "07.2.3": "c:cosrv", "07.2.4": "c:cosrv",
    "07.3": "c:ctran", "07.4": "c:ctran",
    "08": "COMMUNICATION", "09": "RECREATION", "10": "EDUCATION", "11.1": "FOOD_OUTSIDE", "11.2": "FOOD_ACCOM_SRVC",
    "12": "INSURANCE", "13": "MISCELLANEOUS",
}


def weights(name: str = "all households") -> pd.Series:
    """PSA's 2018-based CPI weights (Philippines) on the groups of CPI_MAP; they sum to 100."""
    d = pd.read_csv(paths.DATA_RAW / "cpi" / FILES[name], comment="#", encoding="latin-1")
    code = d["Commodity Description"].str.extract(r"^([0-9.]+) - ")[0]
    w = pd.Series(d.iloc[:, -1].values, index=code.values)
    w = w[~w.index.duplicated()]
    out = pd.Series({k: float(w.get(k, 0.0)) for k in CPI_MAP})
    if abs(out.sum() - 100) > 0.01:
        raise ValueError(f"{name}: mapped CPI weights sum to {out.sum():.4f}, not 100")
    return out


def group_prices(link: dict) -> pd.Series:
    """Price change (%) of each PSA CPI group, from a MicroLink link (MicroLink.link_variables(...))."""
    cat = link["fies_categories"]["price_change_pct"]
    dp = link["commodities"]["consumer_price_pq_pct"]
    missing = [v[2:] for v in CPI_MAP.values() if v.startswith("c:") and v[2:] not in dp.index]
    if missing:
        raise ValueError(f"commodities not in the SAM: {missing} (PSA CPI weights need the petroleum-split SAM)")
    return pd.Series({k: float(dp[v[2:]] if v.startswith("c:") else cat[v]) for k, v in CPI_MAP.items()})


def change(link: dict) -> dict:
    """Consumer-price change (%) on PSA's CPI weights: {'all households': ..., 'bottom 30%': ...}."""
    p = group_prices(link)
    return {name: float((weights(name) * p).sum() / 100.0) for name in FILES}
