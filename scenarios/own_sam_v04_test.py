"""Own SAM: the central 2026 case on a candidate version of Infinity GEM's own SAM (v0.4 by default; 18 Oct 2026). NOT FOR CITATION.

v0.4 (tools/build_own_sam_2023.py, design note §10) spreads business services' and finance's labour income by FIES-LFS
2023 pay. This runs scenarios/sam_psa_sensitivity.py's central case (wage curve recalibrated to the Okun target on the SAM,
MicroLink's default map) with settings' 'own' variant pointed at the v0.4 file for this process only; settings, paths and
check S6 still mean v0.3. The row is saved as outputs/sam_psa_sensitivity_<stamp>_own04_row.csv, so the 'own' rows of
sam_psa_sensitivity.py's tables stay v0.3. Compare with v0.3 (2.43 M, beta 10.8) and IFPRI (3.16 M, beta 7.1).
Run:  py scenarios/own_sam_v04_test.py [version]   (default 0.4; e.g. 0.5; about 10 minutes; row tag _own04, _own05)
"""
import datetime as dt
import sys

from _common import ROOT
import pandas as pd

sys.path.insert(0, str(ROOT / "preshock"))
from infinity_gem import paths                                                     # noqa: E402

VERSION = sys.argv[1] if len(sys.argv) > 1 else "0.4"
paths.SAM_2023_OWN = paths.sam_own(VERSION)                                  # this process only
import sam_psa_sensitivity as S                                                # noqa: E402  (after the switch: its label reads v0.4)


def main():
    stamp = dt.datetime.now()
    row = S.run("own", stamp)
    f = paths.output_dir() / f"sam_psa_sensitivity_{stamp:%Y%m%d_%H%M}_own_row.csv"
    f.rename(f.with_name(f.name.replace("_own_row", "_own" + VERSION.replace(".", "") + "_row")))
    print(pd.Series(row).to_string())


if __name__ == "__main__":
    main()
