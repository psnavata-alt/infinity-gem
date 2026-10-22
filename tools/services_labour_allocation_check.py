"""Own SAM: which SAM spreads labour income across industries as LFS pay does? (18 Oct 2026). NOT FOR CITATION.

Why: on Infinity GEM's own SAM v0.3 the Okun-calibrated wage curve is steeper than on IFPRI's because labour income is spread
differently: PSA's compensation of employees (COE) puts 11% in professional and business services against IFPRI's 17%,
and more in finance (8.6% vs 4.4%) and public administration (11.2% vs 8.8%)
(outputs/mixed_income_diagnostic_20261018_1129.md). This script sets both against an independent measure: the basic pay
employees report in the LFS (FIES-LFS 2023 member file, licensed by PSA to each user; only aggregates leave it), by PSA industry.
Basic pay excludes the 13th-month pay, bonuses, allowances, overtime and employers' social contributions, so COE should
exceed it everywhere; what matters is whether the COE-to-basic-pay ratio is plausible and similar across industries.
Employees = classes of worker 0, 1, 2, 5 (private household, private establishment, government, paid family work).
Annual pay = weekly basic pay (daily basic pay x days worked in the reference week) x 52, weighted (PWGTPRV).
Run:  py tools/services_labour_allocation_check.py      Output: outputs/services_labour_allocation_check_<stamp>.md
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from infinity_gem import paths                                          # noqa: E402
from infinity_gem.sam import SAM                                        # noqa: E402
from infinity_gem.dynamic import PSA_INDUSTRIES                          # noqa: E402
from infinity_gem.household import PSA16                                 # noqa: E402
import mixed_income_diagnostic as MI                                 # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GOVT = 2


def main():
    m = MI.lfs_workers()
    we = m[m["cls"].isin(MI.WAGE_CLASSES) & (m["earn"] > 0)]
    pay = (we["earn"] * 52 * we["w"]).groupby(we["industry"]).sum().reindex(PSA16) / 1e9          # ₱ bn a year
    n = we.groupby("industry")["w"].sum().reindex(PSA16) / 1e3                                       # thousand employees
    gov_share = ((we["cls"] == GOVT) * we["earn"] * we["w"]).groupby(we["industry"]).sum().reindex(PSA16) / 1e9 * 52 / pay * 100
    lab = {}
    for k, p in {"own SAM v0.3 (PSA COE)": paths.SAM_2023_OWN, "IFPRI 2023": paths.SAM_2023_RICE}.items():
        t = SAM.load(p).table
        L = [f for f in t.index if f.startswith("flab")]
        lab[k] = pd.Series({i: float(t.loc[L, [a for a in acts if a in t.columns]].values.sum()) for i, acts in PSA_INDUSTRIES.items()}).reindex(PSA16)
    s, f = lab["own SAM v0.3 (PSA COE)"], lab["IFPRI 2023"]
    t = pd.DataFrame({
        "employees (thousand)": n,
        "LFS basic pay (₱ bn a year)": pay,
        "of which government (%)": gov_share,
        "own SAM labour (₱ bn)": s, "IFPRI labour (₱ bn)": f,
        "own SAM / LFS pay": s / pay, "IFPRI / LFS pay": f / pay,
        "LFS share (%)": pay / pay.sum() * 100, "own SAM share (%)": s / s.sum() * 100, "IFPRI share (%)": f / f.sum() * 100,
    })
    t.loc["Total"] = [n.sum(), pay.sum(), float(((we["cls"] == GOVT) * we["earn"] * 52 * we["w"]).sum() / 1e9 / pay.sum() * 100),
                      s.sum(), f.sum(), s.sum() / pay.sum(), f.sum() / pay.sum(), 100.0, 100.0, 100.0]
    # How far each SAM's industry ratio strays from its own overall ratio (1.0 = same mark-up over LFS pay as the economy)
    t["own SAM ratio / its average"] = t["own SAM / LFS pay"] / t.loc["Total", "own SAM / LFS pay"]
    t["IFPRI ratio / its average"] = t["IFPRI / LFS pay"] / t.loc["Total", "IFPRI / LFS pay"]
    dev = lambda c: float((abs(t.loc[PSA16, c] - 1) * t.loc[PSA16, "LFS share (%)"]).sum() / 100)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    out = paths.output_dir() / f"services_labour_allocation_check_{stamp}.md"
    L = [f"# Labour income by industry: Infinity GEM's own SAM, IFPRI's SAM and LFS pay ({dt.datetime.now():%d %B %Y, %H:%M})", "",
         "**NOT FOR CITATION** (Infinity GEM 0.3.9). Script: `tools/services_labour_allocation_check.py`. LFS = FIES-LFS "
         "2023 member file (licensed by PSA to each user; aggregates only): employees' weekly basic pay x 52, weighted. Basic pay leaves out "
         "the 13th month, bonuses, allowances, overtime and employers' contributions, so a SAM's labour income should exceed it "
         "by a similar factor in every industry.", "",
         t.to_markdown(floatfmt=",.2f"), "",
         f"Pay-weighted mean absolute deviation of the industry ratio from the SAM's own average: the project {dev('own SAM ratio / its average'):.3f}, "
         f"IFPRI {dev('IFPRI ratio / its average'):.3f} (0 = labour spread across industries exactly as LFS pay is)."]
    out.write_text("\n".join(L), encoding="utf-8")
    print(t.round(2).to_string())
    print(f"\nMAD from own average: the project {dev('own SAM ratio / its average'):.3f}, IFPRI {dev('IFPRI ratio / its average'):.3f}")
    print("saved", out)


if __name__ == "__main__":
    main()
