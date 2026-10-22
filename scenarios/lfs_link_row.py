"""The central 2026 case with the FIES-LFS earnings link switched on (18 Oct 2026). NOT FOR CITATION.

Why: the 2026 scenarios count the poor with each family's own inflation (its FIES basket) and its household group's income change
from the CGE (10 groups: urban/rural x income quintile; wages and jobs by skill level, capital and land income, transfers).
The macro-micro link also passes the CGE's labour income by PSA's 16 industries; with PSA's FIES-LFS 2023 file (licensed by PSA to each user) each family's earnings can follow the industries its own members work in (HouseholdDetail's LFS link: within each
group, a family in a hard-hit industry loses more than its group's average, others less; group totals unchanged). This
script reports the 2026 scenarios' 2026 and 2027 new poor both ways, on the SAM the 2026 scenarios use (INFINITY_GEM_SCENARIO_SAM; scenarios/_common.py).
Run:  py lfs_link_row.py      (Git Bash, for Infinity GEM's own SAM: export INFINITY_GEM_SCENARIO_SAM=own; py lfs_link_row.py)
Output: outputs/lfs_link_row_<stamp><tag>.md
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]
import _common                                                       # noqa: E402
import combined_revised as CR                                        # noqa: E402
from infinity_gem import paths                                           # noqa: E402
from infinity_gem.household import HouseholdDetail                       # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LFS = HERE.parent / "data" / "raw" / "lfs"
EMP_FILE = LFS / "PSA_OpenSTAT_0101B3FEMP2_LFS_employed_by_major_industry_2012-2026.csv"     # downloaded 18 Oct 2026
PAY_FILE = LFS / "PSA_OpenSTAT_0161B3FADB2_LFS_average_daily_basic_pay_by_industry_2016-2026.csv"
# LFS major industry groups (2009 PSIC) -> the 16 industries of the model's link (household.PSA16)
TO_PSA16 = {"AGRICULTURE": "Agriculture, forestry, and fishing", "Mining and quarrying": "Mining and quarrying",
            "Manufacturing": "Manufacturing",
            "Electricity, gas, steam, and air conditioning supply": "Electricity, steam, water and waste management",
            "Water supply; sewerage, waste management  and remediation activities": "Electricity, steam, water and waste management",
            "Construction": "Construction",
            "Wholesale and retail trade; repair of motor vehicles and motorcycles": "Wholesale and retail trade; repair of motor vehicles and motorcycles",
            "Transportation and storage": "Transportation and storage",
            "Accommodation and food service activities": "Accommodation and food service activities",
            "Information and communication": "Information and communication",
            "Financial and insurance activities": "Financial and insurance activities",
            "Real estate activities": "Real estate and ownership of dwellings",
            "Professional, scientific and technical activities": "Professional and business services",
            "Administrative and support service activities": "Professional and business services",
            "Public administration and defense; compulsory social security": "Public administration and defense; compulsory social activities",
            "Education": "Education", "Human health and social work activities": "Human health and social work activities",
            "Arts, entertainment and recreation": "Other services", "Other service activities": "Other services",
            "Activities of Households as Employers": "Other services",
            "Activities of extraterritorial organizations and bodies": "Other services"}


def lfs_2026_by_industry() -> pd.DataFrame:
    """PSA LFS: employment January-August 2026 against January-August 2025 by the 16 industries (%), and the change
    against total employment's (pp); wage and salary workers' average daily basic pay, January/April/July rounds (%)."""
    d = pd.read_csv(EMP_FILE, comment="#")
    d["Year"] = d["Year"].astype(str)
    months = ["January", "February", "March", "April", "May", "June", "July", "August"]
    mean = lambda y: d[(d["Year"] == y) & d["Month"].isin(months)].set_index("Month").apply(pd.to_numeric, errors="coerce").mean()
    a, b = mean("2025"), mean("2026")
    grp = lambda s: s[[c for c in TO_PSA16 if c in s.index]].groupby(TO_PSA16).sum()
    emp = (grp(b) / grp(a) - 1) * 100
    tot = float((b["TOTAL"] / a["TOTAL"] - 1) * 100)
    out = pd.DataFrame({"LFS employment 2026 (% y/y, Jan-Aug)": emp, "LFS relative to all employment (pp)": emp - tot})
    p = pd.read_csv(PAY_FILE, comment="#")
    p.index = p.iloc[:, 0].str.strip(". ").str.lower()
    rounds = ["January", "April", "July"]
    chg = (p[[f"2026 {r}" for r in rounds]].apply(pd.to_numeric, errors="coerce").values
           / p[[f"2025 {r}" for r in rounds]].apply(pd.to_numeric, errors="coerce").values - 1).mean(axis=1) * 100
    pay = pd.Series(chg, index=p.index)
    one = {"construction": "Construction", "manufacturing": "Manufacturing", "transportation and storage": "Transportation and storage",
           "accommodation and food service activities": "Accommodation and food service activities", "education": "Education",
           "whosale and retail trade; repair of motor vehicles and motorcycles": "Wholesale and retail trade; repair of motor vehicles and motorcycles"}
    out["LFS daily basic pay 2026 (% y/y, Jan/Apr/Jul)"] = pd.Series({v: float(pay[k]) for k, v in one.items() if k in pay.index})
    out.attrs["total employment 2026 (% y/y)"] = tot
    out.attrs["total daily pay 2026 (% y/y)"] = float(pay["total"])
    return out


def main():
    if not HouseholdDetail.lfs_available():
        sys.exit("The FIES-LFS 2023 member file is not on this machine (paths.FIES_LFS_DIR): the LFS link cannot run.")
    cal = pd.read_csv(_common.calibration_file(), index_col=0)
    beta = float(cal.loc["central (e)", "beta"])
    R = CR.Runs("low", wage_curve=beta)
    piece, _ = R.pieces()
    clean, sim = R.run(set(), piece=piece), R.run(set(CR.SHOCKS), piece=piece)
    rows = {}
    for y in (2025, 2026, 2027):
        link = R.ml.link_variables(R.d.ms, clean.solutions[y], sim.solutions[y])
        pi = R.ml.family_inflation(link)
        for lab, lfs in (("the method of the 2026 scenarios (group incomes)", False), ("with the FIES-LFS earnings link", True)):
            p = R.ml.poverty(link, pi, lfs=lfs)
            rows.setdefault(lab, {})[f"new poor {y} (M)"] = float(p.loc["Poor persons", "Change"]) / 1e6
            rows[lab][f"new poor families {y} (M)"] = float(p.loc["Poor families", "Change"]) / 1e6
        ind = pd.Series(link["_g"].attrs["industry_pct"])
        rows.setdefault("CGE labour income by industry", {})[f"{y}: range across the 16 industries (%)"] = f"{ind.min():.1f} to {ind.max():.1f}"
        if y == 2026:                                  # the model's industry pattern of 2026 against PSA's LFS
            ci = R.ml.industries(R.d.ms, clean.solutions[y], sim.solutions[y])
            b_, s_ = clean.solutions[y], sim.solutions[y]
            labs = [i for i, f_ in enumerate(R.d.ms.F) if f_.startswith("flab")]
            W0, Q0, Q1 = (np.asarray(x, float)[labs] for x in (b_["W"], b_["QF"], s_["QF"]))
            emp_all = ((W0 * Q1).sum() / (W0 * Q0).sum() - 1) * 100
            cmp_ = pd.DataFrame({"CGE labour income 2026 (% vs no-shock path)": ci["labour_income_pct"],
                                 "CGE employment 2026 (% vs no-shock path)": ci["employment_pct"],
                                 "CGE relative to all employment (pp)": ci["employment_pct"] - emp_all,
                                 "CGE average wage 2026 (%)": ci["avg_wage_pct"]})
            lfs_ = lfs_2026_by_industry()
            cmp_ = cmp_.join(lfs_)
            share = R.ml.hd.earnings_by_industry().mul(R.ml.hd.f["RFACT"], axis=0).sum()
            cmp_["share of FIES-LFS earnings (%)"] = (share / share.sum() * 100).reindex(cmp_.index)
    t = pd.DataFrame({k: v for k, v in rows.items() if k != "CGE labour income by industry"}).T
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    out = paths.output_dir() / f"lfs_link_row_{stamp}{_common.out_tag()}.md"
    L = [f"# The central 2026 case with the FIES-LFS earnings link ({dt.datetime.now():%d %B %Y, %H:%M})", "",
         f"**NOT FOR CITATION** (Infinity GEM 0.3.10). SAM: `{CR.SAM_VARIANT}`; wage-curve beta {beta:.3f} "
         f"(`{_common.calibration_file().name}`); script `scenarios/lfs_link_row.py`. Same two runs (no-shock path with the "
         "same policies; all four shocks), counted two ways. Family inflation: each family's own FIES basket, reconciled to "
         "the SAM (the method of the 2026 scenarios) in both rows.", "",
         t.to_markdown(floatfmt=",.3f"), "",
         "CGE labour income by PSA industry (the link variable the FIES-LFS link uses): " +
         "; ".join(f"{k} {v}" for k, v in rows["CGE labour income by industry"].items()) + ".", "",
         "## Is the model's industry pattern in PSA's 2026 data?", "",
         f"CGE: all four shocks against the no-shock path, 2026; economy-wide employment (labour at base wages) {emp_all:.2f}%. "
         f"LFS (`{EMP_FILE.name}`, `{PAY_FILE.name}`): January-August 2026 against January-August 2025; total employment "
         f"{lfs_.attrs['total employment 2026 (% y/y)']:+.2f}%, wage and salary workers' daily basic pay "
         f"{lfs_.attrs['total daily pay 2026 (% y/y)']:+.2f}% (January, April, July rounds). The LFS change mixes the shocks with "
         "normal growth, so compare the 'relative to all employment' columns: they remove what is common to every industry.", "",
         cmp_.to_markdown(floatfmt=",.2f")]
    out.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))
    print("\nsaved", out)


if __name__ == "__main__":
    main()
