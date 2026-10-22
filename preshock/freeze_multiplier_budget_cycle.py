"""Does the public-construction multiplier of about 1.1 survive budget-cycle controls? (18 Oct 2026)

18 Oct 2026: a test of "whether the data's 1.1 partly reflects budget cycles that move public and private
construction together". The baseline is preshock/freeze_multiplier_lp.py (Ramey-Zubairy LP-IV on PSA quarterly data; pre-2020
about 1.1 after a year). If elections or the budget calendar move public construction AND private activity at the same time,
part of the 1.1 is the cycle, not the multiplier. This script adds controls for the predictable parts of those cycles, which
are then partialled out of the instrument and the outcomes:
  - national and local elections (second Monday of May: 2001, 2004, 2007, 2010, 2013, 2016, 2019, 2022, 2025):
      Q1 of an election year (works rushed before the ban) and Q2 (the 45-day ban on public works before election day,
      Omnibus Election Code Sec. 261(v)); one dummy each;
  - reenacted budgets (no GAA at the start of the year): 2001 and 2004 (whole year), 2006 (whole year), 2019 Q1 (GAA signed
      15 April 2019); one dummy;
  - optionally private construction's own growth (lags) as an extra control: if private construction moves with public
      construction through a common cycle, controlling it lowers the multiplier.
Same estimator, horizons, standard errors and samples as the baseline. NOT FOR CITATION until reviewed.
Run:  py preshock/freeze_multiplier_budget_cycle.py
"""
import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "preshock"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import freeze_multiplier_lp as B                                              # noqa: E402

ELECTIONS = (2001, 2004, 2007, 2010, 2013, 2016, 2019, 2022, 2025)
REENACTED = [f"{y}Q{q}" for y in (2001, 2004, 2006) for q in (1, 2, 3, 4)] + ["2019Q1"]


def private_construction(d: pd.DataFrame) -> pd.Series:
    """Private construction GFCF (constant 2018 prices), change as a share of trend GDP, from the same PSA table."""
    c = pd.read_csv(B.MAC / "PSA_OpenSTAT_0542B5BCNQ1_construction_GFCF_by_sector_quarterly_2000-2026.csv", comment="#")
    rows = c[c.iloc[:, 0].str.contains("Private|Financial|Non-financial|Households", case=False, regex=True)]
    cols = [k for k in c.columns if "Constant" in k]
    vals = rows[cols].replace(".", np.nan).apply(pd.to_numeric, errors="coerce")
    tot = vals.sum(axis=0, min_count=1) if len(rows) > 1 else vals.iloc[0]
    s = pd.Series(tot.values, index=pd.PeriodIndex([k.split()[-2] + k.split()[-1] for k in cols], freq="Q"))
    return (s.diff() / d["Ytr"]).reindex(d.index), list(rows.iloc[:, 0])


def lp_iv(d, covid=True, extra=()):
    """freeze_multiplier_lp.lp_iv with extra control columns (already in d)."""
    lags = pd.concat({f"dy_l{k}": d["dy"].shift(k) for k in range(1, 5)} | {f"dg_l{k}": d["dg"].shift(k) for k in range(1, 5)}, axis=1)
    W = pd.concat([pd.Series(1.0, index=d.index, name="c"), lags, d[["q2", "q3", "q4"] + (["covid"] if covid else []) + list(extra)]], axis=1)
    ok = W.notna().all(axis=1) & d["dg"].notna()
    Wm, dg = W[ok].values, d.loc[ok, "dg"].values
    shock = pd.Series(dg - Wm @ np.linalg.lstsq(Wm, dg, rcond=None)[0], index=d.index[ok])
    out = []
    for h in range(B.H + 1):
        Ycum = sum((d["Y"].shift(-j) - d["Y"].shift(1)) for j in range(h + 1)) / d["Ytr"]
        Gcum = sum((d["G"].shift(-j) - d["G"].shift(1)) for j in range(h + 1)) / d["Ytr"]
        z = pd.concat([Ycum.rename("y"), Gcum.rename("x"), shock.rename("z"), W], axis=1).dropna()
        Wz = z[W.columns].values
        P = lambda v: v - Wz @ np.linalg.lstsq(Wz, v, rcond=None)[0]
        yt, xt, zt = P(z["y"].values), P(z["x"].values), P(z["z"].values)
        m = (zt @ yt) / (zt @ xt)
        u = yt - m * xt
        se = np.sqrt(B._hac(zt[:, None], u, h + 1)[0, 0]) / abs(zt @ xt)
        b1 = (zt @ xt) / (zt @ zt)
        e1 = xt - b1 * zt
        F = b1 ** 2 / (B._hac(zt[:, None], e1, h + 1)[0, 0] / (zt @ zt) ** 2)
        out.append({"h": h, "multiplier": m, "s.e.": se, "90% low": m - 1.645 * se, "90% high": m + 1.645 * se, "F": F, "obs": len(yt)})
    return pd.DataFrame(out)


def main():
    d = B.load()
    yr, q = d.index.year, d.index.quarter
    d["elec_q1"] = (np.isin(yr, ELECTIONS) & (q == 1)).astype(float)
    d["elec_q2"] = (np.isin(yr, ELECTIONS) & (q == 2)).astype(float)
    d["reenacted"] = np.isin(d.index.astype(str), REENACTED).astype(float)
    dp, prows = private_construction(d)
    for k in (1, 2):
        d[f"dp_l{k}"] = dp.shift(k)
    pre = d.index < pd.Period("2020Q1", "Q")
    cyc = ("elec_q1", "elec_q2", "reenacted")
    runs = {"Pre-2020, baseline (as freeze_multiplier_lp.py)": lp_iv(d[pre], covid=False),
            "Pre-2020, + election and reenacted-budget dummies": lp_iv(d[pre], covid=False, extra=cyc),
            "Pre-2020, + cycle dummies + private construction (2 lags)": lp_iv(d[pre], covid=False, extra=cyc + ("dp_l1", "dp_l2")),
            "Full sample (2020-21 dummy), + cycle dummies": lp_iv(d, covid=True, extra=cyc)}
    keep = [4, 8]
    summ = pd.DataFrame({k: {f"h={h}": f"{v.loc[h, 'multiplier']:.2f} [{v.loc[h, '90% low']:.2f}, {v.loc[h, '90% high']:.2f}] F {v.loc[h, 'F']:.0f}"
                             for h in keep} for k, v in runs.items()}).T
    for k, v in runs.items():
        print("==", k); print(v.round(3).to_string(index=False))
    print(summ.to_string())
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    L = [f"# Public-construction multiplier with budget-cycle controls ({dt.date.today():%d %B %Y})", "",
         "**NOT FOR CITATION** (Infinity GEM 0.3.10). Script: `preshock/freeze_multiplier_budget_cycle.py`; baseline "
         "`preshock/freeze_multiplier_lp.py` (Ramey-Zubairy LP-IV; PSA quarterly, constant 2018 prices). Controls added: election-year "
         "Q1 and Q2 dummies (elections " + ", ".join(map(str, ELECTIONS)) + "; Q2 holds the 45-day public-works ban), a reenacted-budget "
         "dummy (" + ", ".join(REENACTED) + "), and, in one row, two lags of private construction's change (PSA rows: "
         + "; ".join(prows) + ").", "", "**Summary (cumulative multiplier at 4 and 8 quarters, 90% band, first-stage F):**", "",
         summ.to_markdown(), ""]
    for k, v in runs.items():
        L += [f"## {k}", "", v.to_markdown(index=False, floatfmt=".3f"), ""]
    out = ROOT / "outputs" / f"freeze_multiplier_budget_cycle_{stamp}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print("saved", out)


if __name__ == "__main__":
    main()
