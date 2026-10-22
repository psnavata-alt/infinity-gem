"""Labour hoarding (19 Oct 2026, about 2 AM): the central 2026 case under paid labour hoarding, scored against PSA's data.

For each hoarding share h (cge.py 'hoarding'; 0 = the 2026 scenarios), with the 2026 scenarios' wage curve (Infinity GEM's own SAM calibration):
- the central 2026 measures (combined_revised.Runs.measures): GDP gap 2026 and 2027, new poor 2026 and 2027 (group method);
- new poor 2026 with the FIES-LFS earnings link (each family's earnings by its members' industries);
- the 2026 labour market: jobs (persons, hoarded included), labour income, average wage, all against the no-shock path;
- the public-works multiplier: GDP effect of public works alone in 2026 / the 2026 construction fall (2.21% of GDP; PSA's data
  give about 1.0-1.1);
- the industry pattern against PSA (scenarios/industry_pattern_vs_data.py): slope of relative jobs on relative output (data
  -0.31) and the correlations of the output and jobs patterns.
Run (Git Bash):  export INFINITY_GEM_SCENARIO_SAM=own; py scenarios/hoarding_grid.py 0 0.5 0.75 0.85 0.95
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import _common                                                       # noqa: E402
import combined_revised as CR                                        # noqa: E402
from industry_pattern_vs_data import model_pattern, psa_gva_h1_2026  # noqa: E402
from lfs_link_row import lfs_2026_by_industry                        # noqa: E402
from infinity_gem import paths                                           # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PW_FALL_2026 = 2.21          # the 2026 public-construction fall, % of GDP (outputs/public_works_multiplier_sticky_construction_*)


def row(h, beta):
    R = CR.Runs("low", wage_curve=beta, **({"hoarding": h} if h else {}))
    piece, _ = R.pieces()
    clean, sim = R.run(set(), piece=piece), R.run(set(CR.SHOCKS), piece=piece)
    pw = R.run({"public works"}, piece=piece)
    M, Mpw = R.measures(clean, sim)[0], R.measures(clean, pw, poor=False)[0]      # measures() returns (results, gap by year)
    b, s = clean.solutions[2026], sim.solutions[2026]
    link = R.ml.link_variables(R.d.ms, b, s)
    pi = R.ml.family_inflation(link)
    lfs_poor = float(R.ml.poverty(link, pi, lfs=True).loc["Poor persons", "Change"]) / 1e6
    mp, mt = model_pattern(R.d.ms, b, s)
    gva, gdp = psa_gva_h1_2026()
    lfs = lfs_2026_by_industry()
    rel_mo, rel_po = mp["model output (%)"] - mt["output"], gva - gdp
    rel_mj, rel_lj = mp["model jobs (%)"] - mt["jobs"], lfs["LFS employment 2026 (% y/y, Jan-Aug)"] - lfs.attrs["total employment 2026 (% y/y)"]
    ok = pd.concat([rel_mo, rel_po, rel_mj, rel_lj], axis=1).dropna()
    return {"hoarding h": h,
            "GDP 2026 (%)": M["GDP gap 2026 (%)"], "GDP 2027 (%)": M["GDP gap 2027 (%)"],
            "new poor 2026 (M)": M["new poor 2026 (M, own baskets)"], "new poor 2027 (M)": M["new poor 2027 (M, own baskets)"],
            "new poor 2026, FIES-LFS link (M)": lfs_poor,
            "jobs 2026 (%)": mt["jobs"], "labour income 2026 (%)": mt["labour income"],
            "average wage 2026 (%)": ((1 + mt["labour income"] / 100) / (1 + mt["jobs"] / 100) - 1) * 100,
            "public-works multiplier 2026": -Mpw["GDP gap 2026 (%)"] / PW_FALL_2026,
            "industry slope, jobs on output (data -0.31)": float(np.polyfit(ok.iloc[:, 0], ok.iloc[:, 2], 1)[0]),
            "corr. output pattern": float(np.corrcoef(ok.iloc[:, 0], ok.iloc[:, 1])[0, 1]),
            "corr. jobs pattern": float(np.corrcoef(ok.iloc[:, 2], ok.iloc[:, 3])[0, 1])}


def main():
    hs = [float(a) for a in sys.argv[1:] if not a.startswith("beta=")] or [0.0, 0.5, 0.75, 0.85, 0.95]
    beta = float(pd.read_csv(_common.calibration_file(), index_col=0).loc["central (e)", "beta"])
    beta = next((float(a.split("=", 1)[1]) for a in sys.argv[1:] if a.startswith("beta=")), beta)   # wage-curve slope override
    t = pd.DataFrame([row(h, beta) for h in hs]).set_index("hoarding h")
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    out = paths.output_dir() / f"hoarding_grid_{stamp}{_common.out_tag()}_beta{beta:.2f}_{'_'.join(f'{h:g}' for h in hs)}.md"
    L = [f"# The central 2026 case under paid labour hoarding ({dt.datetime.now():%d %B %Y, %H:%M})", "",
         f"**NOT FOR CITATION** (Infinity GEM 0.3.11). SAM `{CR.SAM_VARIANT}`; wage-curve beta {beta:.3f} (the 2026 scenarios'); "
         "h = 0 is the central 2026 case of 18 Oct 2026. Data targets: industry slope about 0 (PSA GVA H1 2026, LFS Jan-Aug); public-works "
         "multiplier about 1.0-1.1 (PSA local projections); labour income and wages close to trend (LFS pay +9.0% in 2026 after "
         "+7.3% in 2025); H1 2026 growth 2.6% against the pre-shock 5.5%. Script `scenarios/hoarding_grid.py`.", "",
         t.T.to_markdown(floatfmt=".3f")]
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L)); print("saved", out)


if __name__ == "__main__":
    main()
