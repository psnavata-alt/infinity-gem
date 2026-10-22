"""GTAP 10 (2014) household demand for the Philippines: the third benchmark for the LES.

Source: GTAP 10A Data Base, reference year 2014 (Aguiar, Chepeliev, Corong, McDougall and van der Mensbrugghe 2019, "The
GTAP Data Base: Version 10", Journal of Global Economic Analysis 4(1): 1-27); archived release, free to use with citation
(gtap.agecon.purdue.edu/databases/archives.asp). Package downloaded 2-3 Oct 2026:
the GTAP 10A archive (licensed; not distributed) Read with the open-source `harpy3` reader (no GTAP software run;
harpy3 is licensed under the GNU GPL v3, is imported only by this tool, and is not a requirement of Infinity GEM).

GTAP's household demand is CDE (constant difference of elasticities). Its elasticities follow from SUBPAR, INCPAR (GTAP's parameter file)
and the budget shares, with the formulas of the GTAP model code (gtapv7.tab, in a reference copy (not distributed)):
  ALPHA = 1 - SUBPAR;  CONSHR = VPP / sum VPP, VPP = household purchases (domestic + imported, agents' prices: VDPA + VIPA)
  EY(c)   = [1 / sum_n CONSHR_n INCPAR_n] [INCPAR_c (1 - ALPHA_c) + sum_n CONSHR_n INCPAR_n ALPHA_n] + [ALPHA_c - sum_n CONSHR_n ALPHA_n]
  APE(c,c) = 2 ALPHA_c - sum_n CONSHR_n ALPHA_n - ALPHA_c / CONSHR_c
  EP(c,c) = [APE(c,c) - EY(c)] CONSHR_c        (uncompensated own-price elasticity)
Output: the GTAP 10 parameter extract (not distributed: GTAP licence) (one row per GTAP commodity, with the SAM
commodity it maps to). Run:  py tools/gtap10_philippines.py
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "docs" / "references" / "cge_models" / "gtap" / "GTAP10A_GTAP_AY.pkg"
OUT = ROOT / "data" / "raw" / "elasticities" / "GTAP10_2014_Philippines_household_demand.csv"
TMP = ROOT / "data" / "raw" / "gtap10_2014"

# GTAP 65 commodities -> IFPRI 2023 SAM commodities (split SAM: p_c -> cpetr). Follows IFPRI's ISIC concordance
# (2023 data paper, Table A1) and Cororaton's PSA-GTAP mapping (12059.pdf, Table 8.87).
GTAP_TO_SAM = {
    "pdr": "crice", "wht": "cocer", "gro": "cmaiz", "v_f": "cvege", "osd": "coils", "c_b": "csugr", "pfb": "ccott",
    "ocr": "cocrp", "ctl": "ccatt", "oap": "coliv", "rmk": "ccatt", "wol": "coliv", "frs": "cfore", "fsh": "cfish",
    "coa": "cmine", "oil": "cmine", "gas": "cmine", "oxt": "cmine", "cmt": "cfood", "omt": "cfood", "vol": "cfood",
    "mil": "cfood", "pcr": "cfood", "sgr": "cfood", "ofd": "cfood", "b_t": "cbeve", "tex": "ctext", "wap": "ctext",
    "lea": "ctext", "lum": "cwood", "ppp": "cwood", "p_c": "cpetr", "chm": "cchem", "bph": "cchem", "rpp": "cchem",
    "nmm": "cnmet", "i_s": "cmetl", "nfm": "cmetl", "fmp": "cmetl", "ele": "cmach", "eeq": "cmach", "ome": "cmach",
    "mvh": "cmach", "otn": "cmach", "omf": "coman", "ely": "celec", "gdt": "celec", "wtr": "cwatr", "cns": "ccons",
    "trd": "ctrad", "afs": "chotl", "otp": "ctran", "wtp": "ctran", "atp": "ctran", "whs": "ctran", "cmn": "ccomm",
    "ofi": "cfsrv", "ins": "cfsrv", "rsa": "creal", "obs": "cbsrv", "ros": "cosrv", "osg": "cpadm", "edu": "ceduc",
    "hht": "cheal", "dwe": "creal"}
FOOD = {"pdr", "wht", "gro", "v_f", "osd", "c_b", "ocr", "ctl", "oap", "rmk", "fsh", "cmt", "omt", "vol", "mil", "pcr",
        "sgr", "ofd", "b_t"}


def main():
    import harpy
    TMP.mkdir(parents=True, exist_ok=True)
    z = zipfile.ZipFile(PKG)
    for n in ("default.prm", "sets.har", "basedata.har"):
        (TMP / n).write_bytes(z.read(f"GTAP10A/GTAP/2014/{n}"))
    get = lambda f, h: harpy.HarFileObj.loadFromDisk(str(TMP / f)).getHeaderArrayObj(h).get("array")
    reg = [str(x).strip() for x in get("sets.har", "H1")]
    com = [str(x).strip() for x in get("sets.har", "H2")]
    r = reg.index("phl")
    sub = np.asarray(get("default.prm", "SUBP"))[:, r].astype(float)
    inc = np.asarray(get("default.prm", "INCP"))[:, r].astype(float)
    bd = harpy.HarFileObj.loadFromDisk(str(TMP / "basedata.har"))
    vpp = (np.asarray(bd.getHeaderArrayObj("VDPA").get("array"))[:, r]
           + np.asarray(bd.getHeaderArrayObj("VIPA").get("array"))[:, r]).astype(float)
    esbd = np.asarray(get("default.prm", "ESBD")).astype(float)
    (TMP / "basedata.har").unlink()                     # 94 MB; it stays inside the .pkg
    s = vpp / vpp.sum()
    alpha = 1 - sub
    ey = (1 / (s @ inc)) * (inc * (1 - alpha) + (s * inc * alpha).sum()) + (alpha - s @ alpha)
    ape_cc = np.where(s > 0, 2 * alpha - s @ alpha - alpha / np.where(s > 0, s, 1), np.nan)
    ep = (ape_cc - ey) * s
    df = pd.DataFrame({"gtap": com, "sam": [GTAP_TO_SAM[c] for c in com], "food": [c in FOOD for c in com],
                       "budget_share": s, "SUBPAR": sub, "INCPAR": inc, "income_elasticity": ey,
                       "own_price_uncompensated": ep, "ESBD_armington": esbd})
    head = ("# GTAP 10A Data Base, 2014, region phl (Aguiar et al. 2019, JGEA 4(1)); CDE parameters SUBPAR/INCPAR and ESBD from "
            "default.prm, household purchases VDPA+VIPA from basedata.har; elasticities by the formulas of gtapv7.tab. Built by "
            "tools/gtap10_philippines.py from the GTAP 10A archive (licensed; not distributed)\n")
    OUT.write_text(head + df.to_csv(index=False, float_format="%.6f"), encoding="utf-8")
    return df


if __name__ == "__main__":
    df = main()
    pd.set_option("display.width", 200)
    print(df.round(3).to_string(index=False))
    w = df.budget_share
    print("\nfood + beverages: budget share %.3f, income elasticity %.3f, own-price %.3f" %
          (w[df.food].sum(), (w * df.income_elasticity)[df.food].sum() / w[df.food].sum(),
           (w * df.own_price_uncompensated)[df.food].sum() / w[df.food].sum()))
    print("check: sum of budget-share-weighted income elasticities = %.6f (Engel aggregation)" % (w * df.income_elasticity).sum())
