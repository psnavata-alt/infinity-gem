"""Add elasticity rows for the accounts that exist only in the split SAMs (0.3.7, 15 Oct 2026).

Why: tools/build_elasticities.py builds data/processed/elasticities_ph_v1.csv from the accounts of the original 2023 SAM,
so the split SAMs' new accounts had no rows and silently took the CGE's generic defaults (value added 0.8, Armington 2.0,
CET 2.0): refined petroleum (cpetr / apetr, in '0.3 recommended' since 8 Oct) and milled rice and corn (cmric / amric). Each maps to ONE GTAP 9 sector, so no Philippine weights are needed (the main builder's weights come
from MANAGE-WB's gtapData9.gdx through GAMS's gdxdump, which this PC does not have).

Same rules and sources as tools/build_elasticities.py:
  Armington ('ph'): Kapuscinski and Warr (1999) Table 4 ECM where significant and positive; otherwise GTAP 9 ESUBD.
    rice and corn milling = KW 13 (0.614, not significant) -> GTAP PCR 2.6;
    coal and petroleum products = KW 28 (0.558, not significant) -> GTAP P_C 2.1.
  CET: equal to ESUBD (MANAGE-WB's convention). Value added: GTAP ESUBVA = MANAGE-WB 'va_new' / 2 (PCR 1.12, P_C 1.26).
  PCGEM CET: left empty (sensitivity set only; infinity_gem.elasticities drops empty values, so the default applies).
Existing rows are not changed (the script refuses to run if they would be).
Run:  py tools/add_split_elasticities.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "data" / "raw" / "elasticities"
DST = ROOT / "data" / "processed" / "elasticities_ph_v1.csv"
SPLIT = {"petr": ("P_C", 28), "mric": ("PCR", 13)}     # Infinity GEM code -> (GTAP 9 sector, Kapuscinski-Warr commodity)


def main():
    com = pd.read_csv(E / "MANAGE-WB_GTAP9_template_comPar.csv")
    esubd = {c.split("-")[1].upper(): float(v) for c, v in zip(com.commodity, com.sigmam0)}
    act = pd.read_csv(E / "MANAGE-WB_GTAP9_template_actPar.csv")
    esubva = {a.split("-")[1].upper(): float(v) / 2 for a, v in zip(act.activity, act.va_new)}
    kw = pd.read_csv(E / "Kapuscinski_Warr_1999_Table4_ECM.csv", comment="#").set_index("no")
    old = pd.read_csv(DST)
    keep = old[~old.code.isin([k + s for s in SPLIT for k in ("c", "a")])]
    rows = []
    for s, (g, k) in SPLIT.items():
        arm = esubd[g]
        r = kw.loc[k]
        if r.significant == 1 and r.ecm > 0:
            arm_ph, src = float(r.ecm), f"Kapuscinski-Warr 1999 ECM (commodity [{k}])"
        else:
            arm_ph, src = arm, f"GTAP 9 ESUBD ({g}; Kapuscinski-Warr commodity {k} not significant)"
        rows.append(dict(kind="commodity", code="c" + s, gtap=g, sigma_q_gtap=round(arm, 4), sigma_q_ph=round(arm_ph, 4),
                         sigma_q_ph_source=src, omega_t_gtap=round(arm, 4)))
        rows.append(dict(kind="activity", code="a" + s, gtap=g, sigma_va_gtap=round(esubva[g], 4)))
    out = pd.concat([keep, pd.DataFrame(rows)], ignore_index=True)
    if not out.iloc[:len(keep)].equals(keep.reset_index(drop=True)):
        raise RuntimeError("existing rows would change")
    out.to_csv(DST, index=False)
    print(pd.DataFrame(rows).to_string(index=False))
    print(f"{DST}: {len(keep)} existing rows kept, {len(rows)} split-SAM rows written")


if __name__ == "__main__":
    sys.exit(main())
