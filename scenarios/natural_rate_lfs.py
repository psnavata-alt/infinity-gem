"""The natural rate of unemployment from PSA's Labour Force Survey, and the slack at the start of the dynamic model's short-run years
(0.3.13, 23 Oct 2026; step 1 of a design note (not included), section 3). NOT FOR CITATION.

The engine's estimate is infinity_gem.dynamic.lfs_natural_rate() (used by lfs_labour_slack() for DynamicCGE(sr_labour_slack=...)):
  data     PSA OpenSTAT 0021B3FKEI2, Rates of Key Employment Indicators (data/raw/lfs; downloaded 14 Oct 2026), the unemployment rate
           of the four full-sample quarterly rounds (January, April, July, October), April 2005 to July 2026: the 2005 definition of
           unemployment (availability criterion) throughout, and one survey design (since 2021 PSA also runs smaller monthly
           surveys between the rounds and its annual rate averages all twelve months, which ran 0.2-0.5 points below the rounds'
           mean in 2023-2025; this script reports both).
  method   Hodrick-Prescott trend (lam 1600) with fixed quarter effects, estimated together by penalised least squares; the
           COVID quarters 2020Q2-2021Q4 are left out of the fit; data to 2025Q4 (before the 2026 shocks the model simulates). The
           natural rate is the trend at 2025Q4.
  check    BSP DP 2024-11 (Espano, Lemence, Tabin and Armas, June 2024; a reference library's BSP Discussion Papers folder,
           DP202411.pdf), Table 2: a Phillips curve with a time-varying NAIRU estimated by the Kalman filter, 1990Q3-2019Q4: NAIRU
           5.02-5.19% (four inflation measures); with the pandemic quarters added (to 2022Q4) 7.36-7.45%; its HP trends put the
           unemployment gap below zero from 2022Q1. A statistical trend is a cruder NAIRU than BSP's Phillips curve; the test is
           that it lands inside BSP's pre-pandemic band at 2019Q4.
Reported: the estimate under other smoothing (lam 400, 6400), another COVID window (to 2022Q1), the sample to the latest round
(2026Q3, which then carries the 2026 shocks), the baseline's unemployment rate by year on the same basis and the slack
s_t = max(0, (1 - u_n) / (1 - u_t) - 1), with two alternatives for 2026 (the same-months ratio of PSA's levels, as the baseline
builds its 2026 employment; and the twelve-month annual basis).

Run (from the repository folder):  py -X utf8 scenarios/natural_rate_lfs.py
Outputs: outputs/natural_rate_lfs_<YYYYMMDD_HHMM>.csv (variants), _slack.csv (by year) and _summary.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from infinity_gem import dynamic as D                                               # noqa: E402
from infinity_gem import paths                                                      # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CSV_HEAD = "# NOT FOR CITATION (research; development version: Infinity GEM 0.3.13). scenarios/natural_rate_lfs.py"
BSP_DP_2024_11 = {"1990Q3-2019Q4, NAIRU at 2019Q4 (%)": (5.018, 5.187), "1990Q3-2022Q4, NAIRU (%)": (7.357, 7.450)}


def variants():
    rows = {}
    for label, kw in (("central: lam 1600, COVID 2020Q2-2021Q4 out, to 2025Q4", {}),
                      ("lam 400", {"lam": 400.0}), ("lam 6400", {"lam": 6400.0}),
                      ("COVID window to 2022Q1", {"covid": (2020.25, 2022.0)}),
                      ("to the latest round (2026Q3; carries the 2026 shocks)", {"end": 2026}),
                      ("no COVID window (pandemic quarters fitted)", {"covid": None})):
        e = D.lfs_natural_rate(**kw)
        tr = e["trend"]
        rows[label] = {"natural rate at the last quarter (%)": e["rate"] * 100, "last quarter": e["last"],
                       "trend 2019Q4 (%)": float(tr.loc[2019.75]), "trend 2022Q4 (%)": float(tr.loc[2022.75]),
                       "trend 2024Q4 (%)": float(tr.loc[2024.75]), "trend 2025Q4 (%)": float(tr.loc[2025.75]),
                       **{f"quarter effect Q{q} (pp)": v for q, v in e["seasonal"].items()}}
    return pd.DataFrame(rows)


def annual_basis():
    """PSA's annual unemployment rate (twelve-month average since 2021) against the four rounds' mean."""
    d = pd.read_csv(paths.DATA_RAW / "lfs" / D.LFS_RATES_FILE, comment="#", na_values=".")
    a = d[d["Month"] == "Annual"].set_index("Year")["Unemployment Rate Both sexes"].astype(float)
    q = D.lfs_unemployment_rounds()
    r = q.groupby("year")["u"].agg(["mean", "size"])
    out = pd.DataFrame({"PSA annual (%)": a, "four rounds' mean (%)": r["mean"], "rounds on file": r["size"]}).loc[2016:2026]
    out["rounds less annual (pp)"] = out["four rounds' mean (%)"] - out["PSA annual (%)"]
    return out


def levels_2026():
    """The same-months alternative for 2026: the baseline builds 2026 employment as 2025 x (Jan-Jul 2026 / Jan-Jul 2025, PSA levels);
    the labour force built the same way gives u_2026 = 1 - (1 - u_2025) x [(1 - u_JJ26) / (1 - u_JJ25)]."""
    f = paths.DATA_RAW / "lfs" / "PSA_OpenSTAT_0011B3FKEI1_LFS_key_employment_levels_2005-2026.csv"
    d = pd.read_csv(f, comment="#", na_values=".")
    months = ["January", "February", "March", "April", "May", "June", "July"]
    jj = lambda y: d[(d["Year"] == y) & d["Month"].isin(months)][["Persons in the Labor Force Both sexes",
                                                                   "Employed Persons Both sexes"]].sum()
    a, b = jj(2026), jj(2025)
    u26, u25 = 1 - a.iloc[1] / a.iloc[0], 1 - b.iloc[1] / b.iloc[0]
    return float(u26), float(u25)


def main():
    stamp = pd.Timestamp.today()
    out = paths.output_dir()
    v = variants()
    est = D.lfs_natural_rate()
    un = est["rate"]
    ub_o, ub_t = D.lfs_baseline_unemployment("observed"), D.lfs_baseline_unemployment("trend")
    sl_o, sl_t = D.lfs_labour_slack(y2026="observed"), D.lfs_labour_slack(y2026="trend")
    u26, u25 = levels_2026()
    alt26 = 1 - (1 - ub_o[2025]) * (1 - u26) / (1 - u25)
    ab = annual_basis()
    gap_ann = float(ab.loc[2022:2025, "rounds less annual (pp)"].mean())
    rows = {}
    for y in sorted(ub_o):
        rows[y] = {"baseline unemployment, observed 2026 (%)": ub_o[y] * 100, "slack, observed 2026 (%)": sl_o[y] * 100,
                   "baseline unemployment, trend 2026 (%)": ub_t[y] * 100, "slack, trend 2026 (%)": sl_t[y] * 100}
    sl = pd.DataFrame(rows).T
    alt = {"2026 by the same-months ratio of PSA levels: baseline unemployment (%)": alt26 * 100,
           "2026 by the same-months ratio of PSA levels: slack (%)": max(0.0, (1 - un) / (1 - alt26) - 1) * 100,
           "annual (twelve-month) basis: natural rate less the 2022-2025 mean gap of rounds over annual (%)": (un * 100 - gap_ann),
           "annual basis: 2025 slack (%)": max(0.0, (1 - (un - gap_ann / 100)) / (1 - float(ab.loc[2025, "PSA annual (%)"]) / 100) - 1) * 100}
    print(v.round(3).to_string())
    print()
    print(sl.round(3).to_string())
    print()
    print(ab.round(3).to_string())
    print()
    print(pd.Series(alt).round(3).to_string())
    f = out / f"natural_rate_lfs_{stamp:%Y%m%d_%H%M}"
    f.with_name(f.name + ".csv").write_text(CSV_HEAD + "\n" + v.to_csv(), encoding="utf-8")
    f.with_name(f.name + "_slack.csv").write_text(CSV_HEAD + "\n" + sl.to_csv(), encoding="utf-8")
    f.with_name(f.name + "_annual_basis.csv").write_text(CSV_HEAD + "\n" + ab.to_csv(), encoding="utf-8")
    summ = {"natural rate (share, trend at 2025Q4)": un, "method": "HP trend lam 1600 with quarter effects, COVID quarters 2020Q2-2021Q4 "
            "out, four quarterly LFS rounds, April 2005-October 2025 (infinity_gem.dynamic.lfs_natural_rate)",
            "data": f"data/raw/lfs/{D.LFS_RATES_FILE} (PSA OpenSTAT 0021B3FKEI2, downloaded 14 Oct 2026)",
            "trend at 2019Q4 (%)": float(est["trend"].loc[2019.75]), "BSP DP 2024-11, Table 2 (%)": BSP_DP_2024_11,
            "quarter effects (pp)": est["seasonal"], "slack by year, observed 2026": sl_o, "slack by year, trend 2026": sl_t,
            "alternatives": alt, "variants": json.loads(v.to_json())}
    f.with_name(f.name + "_summary.json").write_text(json.dumps(summ, indent=1, default=float), encoding="utf-8")
    print("saved", f.with_name(f.name + ".csv"))


if __name__ == "__main__":
    main()
