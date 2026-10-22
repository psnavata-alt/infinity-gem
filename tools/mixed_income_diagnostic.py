"""Own SAM: the self-employed's labour inside mixed income, by industry (18 Oct 2026, about 11:40 AM). NOT FOR CITATION.

Why: Infinity GEM's own SAM v0.3 takes labour income by industry from PSA's compensation of employees (COE); the earnings of own-account
workers and unpaid family workers stay in capital (mixed) income. IFPRI spreads labour with FIES earnings including farm and
non-farm enterprise income (data paper p. 24). That difference drives the steeper wage curve on Infinity GEM's own SAM
(outputs/own_sam_wage_curve_diagnostic_20261018_0654.md). This script measures the gap before any SAM is rebuilt.
Method (Gollin 2002, JPE 110(2), "adjustment 2"): each own-account worker (class of worker 3) and unpaid family worker (6)
is given the average weekly earnings of wage-and-salary workers (classes 0, 1, 2, 5) of the same PSA industry and skill
level (FIES-LFS 2023 member file; licensed, aggregates only). Their imputed labour, as a ratio to employees' earnings in the
industry, scales the SAM's COE. Employers (class 4) are left in capital: their income is largely return to their firm.
The imputation is capped at 90% of the industry's non-labour value added (the self-employed also own capital and land).
Run:  py tools/mixed_income_diagnostic.py        Output: outputs/mixed_income_diagnostic_<date>.md
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from infinity_gem import paths                                          # noqa: E402
from infinity_gem.sam import SAM                                        # noqa: E402
from infinity_gem.dynamic import PSA_INDUSTRIES                          # noqa: E402
from infinity_gem.household import psic_to_psa16, PSA16                  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CAP = 0.90
WAGE_CLASSES, OWN_ACCOUNT, EMPLOYER, UNPAID = (0, 1, 2, 5), 3, 4, 6


def lfs_workers() -> pd.DataFrame:
    cols = ["LC07_GRADE", "LC16_PKB", "LC19_PDAYS", "LC23_PCLASS", "LC25_PBASIC", "NEWEMPSTAT", "PWGTPRV"]
    m = pd.read_csv(paths.FIES_LFS_MEMBERS, usecols=cols, dtype=str, encoding="utf-8-sig")
    m = m[m["NEWEMPSTAT"].str.strip() == "1"].copy()
    g = pd.to_numeric(m["LC07_GRADE"], errors="coerce")
    m["skill"] = np.select([g < 10018, g < 24015, g >= 24015], ["flab-n", "flab-p", "flab-s"], default="")
    m["cls"] = pd.to_numeric(m["LC23_PCLASS"], errors="coerce")
    m["ind"] = m["LC16_PKB"].map(psic_to_psa16)
    m["w"] = pd.to_numeric(m["PWGTPRV"], errors="coerce")
    pay = pd.to_numeric(m["LC25_PBASIC"], errors="coerce")
    days = pd.to_numeric(m["LC19_PDAYS"], errors="coerce")
    days = days.where(days > 0).fillna(days[days > 0].median())
    m["earn"] = pay * days                                       # weekly earnings of wage-and-salary workers
    m = m[(m["ind"] >= 0) & (m["skill"] != "") & m["cls"].notna()]
    m["industry"] = m["ind"].astype(int).map(lambda i: PSA16[i])
    return m


def main():
    m = lfs_workers()
    we = m[m["cls"].isin(WAGE_CLASSES) & (m["earn"] > 0)]
    avg = (we.assign(x=we["earn"] * we["w"]).groupby(["industry", "skill"])["x"].sum()
           / we.groupby(["industry", "skill"])["w"].sum())                       # mean weekly earnings, industry x skill
    avg_ind = (we["earn"] * we["w"]).groupby(we["industry"]).sum() / we.groupby("industry")["w"].sum()
    cnt = m.pivot_table(index="industry", columns="cls", values="w", aggfunc="sum").fillna(0) / 1e3   # thousand persons
    se = m[m["cls"].isin([OWN_ACCOUNT, UNPAID])].copy()
    se["wage"] = [avg.get((i, s), avg_ind.get(i, np.nan)) for i, s in zip(se["industry"], se["skill"])]
    imputed = (se["wage"] * se["w"]).groupby(se["industry"]).sum()
    employees = (we["earn"] * we["w"]).groupby(we["industry"]).sum()
    ratio = (imputed / employees).reindex(PSA16).fillna(0)
    # the SAMs (₱ bn)
    sams = {"IFPRI": paths.SAM_2023_RICE, "own SAM v0.3": paths.SAM_2023_OWN}
    lab, nonlab = {}, {}
    for k, p in sams.items():
        t = SAM.load(p).table
        L = [f for f in t.index if f.startswith("flab")]
        N = [f for f in t.index if f.startswith(("fcap", "flnd"))]
        lab[k] = pd.Series({n: float(t.loc[L, [a for a in acts if a in t.columns]].values.sum()) for n, acts in PSA_INDUSTRIES.items()})
        nonlab[k] = pd.Series({n: float(t.loc[N, [a for a in acts if a in t.columns]].values.sum()) for n, acts in PSA_INDUSTRIES.items()})
    coe = lab["own SAM v0.3"].reindex(PSA16)
    se_peso = (ratio * coe).clip(upper=CAP * nonlab["own SAM v0.3"].reindex(PSA16))
    capped = (ratio * coe) > CAP * nonlab["own SAM v0.3"].reindex(PSA16)
    t = pd.DataFrame({
        "employed (thousand)": cnt.sum(axis=1).reindex(PSA16),
        "own-account (thousand)": cnt.get(OWN_ACCOUNT, 0).reindex(PSA16),
        "unpaid family (thousand)": cnt.get(UNPAID, 0).reindex(PSA16),
        "employers (thousand)": cnt.get(EMPLOYER, 0).reindex(PSA16),
        "imputed / employees' earnings": ratio,
        "own SAM v0.3 labour = COE (₱ bn)": coe,
        "imputed self-employed labour (₱ bn)": se_peso,
        "capped at 90% of non-labour VA": capped,
        "own SAM with mixed-income split (₱ bn)": coe + se_peso,
        "IFPRI labour (₱ bn)": lab["IFPRI"].reindex(PSA16),
    })
    t.loc["Total"] = t.sum(numeric_only=True)
    t.loc["Total", "capped at 90% of non-labour VA"] = int(capped.sum())
    share = pd.DataFrame({"own SAM v0.3 (COE)": coe / coe.sum() * 100,
                          "own SAM with split": (coe + se_peso) / (coe + se_peso).sum() * 100,
                          "IFPRI": lab["IFPRI"].reindex(PSA16) / lab["IFPRI"].sum() * 100})
    va = (lab["own SAM v0.3"] + nonlab["own SAM v0.3"]).reindex(PSA16)
    lshare = pd.DataFrame({"own SAM v0.3": coe / va * 100, "own SAM with split": (coe + se_peso) / va * 100,
                           "IFPRI": (lab["IFPRI"] / (lab["IFPRI"] + nonlab["IFPRI"])).reindex(PSA16) * 100})
    f = pd.read_csv(paths.FIES_PUF, usecols=["URB", "NPCINC", "RFACT", "WAGES", "EAINC", "TOINC"])
    f["grp"] = np.where(f["URB"] == 1, "hhd-u", "hhd-r") + np.ceil(f["NPCINC"] / 2).astype(int).astype(str)
    fg = pd.DataFrame({k: (f[k] * f["RFACT"]).groupby(f["grp"]).sum() / 1e9 for k in ("WAGES", "EAINC", "TOINC")})
    fg["entrepreneurial share of wages + entrepreneurial (%)"] = fg["EAINC"] / (fg["EAINC"] + fg["WAGES"]) * 100
    stamp = pd.Timestamp.today()
    out = paths.output_dir() / f"mixed_income_diagnostic_{stamp:%Y%m%d_%H%M}.md"
    L = [f"# Own SAM: the self-employed's labour inside mixed income ({stamp:%d %B %Y, %H:%M})", "",
         "**NOT FOR CITATION** (Infinity GEM 0.3.9). Script: `tools/mixed_income_diagnostic.py`. FIES-LFS 2023 member file "
         "(licensed by PSA to each user; only these aggregates leave it). Own-account and unpaid family workers get the average weekly "
         "earnings of employees of the same industry and skill (Gollin 2002, adjustment 2); employers stay in capital; cap 90% "
         "of the industry's non-labour value added.", "",
         "## 1. By PSA industry", "", t.round(2).to_markdown(floatfmt=",.2f"), "",
         "## 2. Distribution of labour income across industries (%)", "", share.round(1).to_markdown(floatfmt=",.1f"), "",
         "## 3. Labour share of value added (%)", "", lshare.round(1).to_markdown(floatfmt=",.1f"), "",
         "## 4. FIES 2023 by household group (₱ bn): wages and entrepreneurial income", "", fg.round(1).to_markdown(floatfmt=",.1f")]
    out.write_text("\n".join(L), encoding="utf-8")
    print(t.round(2).to_string()); print(share.round(1).to_string()); print(lshare.round(1).to_string()); print(fg.round(1).to_string())
    print("saved", out)


if __name__ == "__main__":
    main()
