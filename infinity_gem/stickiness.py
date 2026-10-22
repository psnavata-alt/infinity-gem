"""Sectoral price stickiness for the sticky-price option (0.3.11, 19 Oct 2026, about 11:35 PM; the "sectoral price
stickiness" step of the DSGE plan, applied first to the CGE's short run). Research option: nothing changes unless a run
passes DynamicCGE(sr_pricing="sticky", sr_stickiness=sectoral(...)) or the shock key 'stickiness' as a dict. Check ST1.

Source: Basilio, J. R., and F. C. Cacnio (2020). "Relative Price Changes, Asymmetric Adjustments and Aggregate Inflation:
Evidence from the Philippines." BSP Working Paper Series 2020-02, Table 2 (pp. 8-9): duration between price DECREASES (median
average, months) by CPI commodity group, 2002-M9 2019 (the inflation-targeting period), from the 3-digit CPI items (2012 = 100).
Read 19 Oct 2026 (BSP website, Working Paper Series).

Rule: with a constant chance of a price cut each month and a mean of D months between cuts, the
share of a cost fall at the start of a year NOT yet in that year's average price is (D/12)(1 - exp(-12/D)). All items: D 10.0
-> 0.58, the single value 0.6 used before. Food 3.6 -> 0.29; education 50.7 -> 0.89.

Concordance activity -> CPI group: an ASSUMPTION, with the reason where it is not obvious. Refined petroleum is flexible: pump
prices change weekly under the Downstream Oil Industry Deregulation Act (RA 8479). Activities without a matching consumer group
(producer goods, construction, trade, business services, public administration) take the all-items value.
Caveat: the BSP durations come from item indices, so they measure how often a 3-digit index falls, not how long a single shop's
price stays unchanged; they are used here, as in the 2026 scenarios, only for the share of a cost fall passed on within a year.
"""
from __future__ import annotations

import numpy as np

# Basilio and Cacnio (2020), Table 2, 2002 - M9 2019: duration between price decreases (months)
DECREASE_MONTHS = {
    "All items": 10.0,
    "Food and non-alcoholic beverages": 3.6,
    "Alcoholic beverages, tobacco": 53.3,
    "Clothing and footwear": 23.5,
    "Housing, water, electricity, gas and other fuels": 9.1,
    "Furnishings, household equipment": 18.2,
    "Health": 30.4,
    "Transport": 16.3,
    "Communication": 7.6,
    "Recreation and culture": 13.7,
    "Education": 50.7,
    "Restaurants, miscellaneous goods and services": 42.6,
}

ACTIVITY_GROUP = {                       # ASSUMPTION; None = flexible
    "afood": "Food and non-alcoholic beverages",
    "amric": "Food and non-alcoholic beverages",
    "abeve": "All items",                # soft drinks (food group, 3.6) and alcoholic drinks (53.3) in one activity
    "atext": "Clothing and footwear",
    "awood": "Furnishings, household equipment",
    "achem": "All items",
    "apetr": None,                       # weekly pump-price changes (RA 8479)
    "anmet": "All items",
    "ametl": "All items",
    "amach": "All items",                # mostly exported electronics; appliances and vehicles are only part of it
    "aoman": "All items",
    "aelec": "Housing, water, electricity, gas and other fuels",
    "awatr": "Housing, water, electricity, gas and other fuels",
    "acons": "All items",
    "atrad": "All items",
    "atran": "Transport",
    "ahotl": "Restaurants, miscellaneous goods and services",
    "acomm": "Communication",
    "afsrv": "Restaurants, miscellaneous goods and services",   # insurance and financial services are in this CPI group
    "areal": "Housing, water, electricity, gas and other fuels",  # rents
    "absrv": "All items",
    "apadm": "All items",
    "aeduc": "Education",
    "aheal": "Health",
    "aosrv": "Recreation and culture",
}


def share_not_passed(months: float) -> float:
    """Share of a cost fall at the start of a year not yet in that year's average price, mean D months between price cuts."""
    return float(months / 12 * (1 - np.exp(-12 / months)))


def sectoral(activities) -> dict:
    """{activity: stickiness} for the given activities (e.g. the model's sticky-price ones). Activities not in ACTIVITY_GROUP
    take the all-items value; refined petroleum 0."""
    out = {}
    for a in activities:
        g = ACTIVITY_GROUP.get(a, "All items")
        out[a] = 0.0 if g is None else share_not_passed(DECREASE_MONTHS[g])
    return out
