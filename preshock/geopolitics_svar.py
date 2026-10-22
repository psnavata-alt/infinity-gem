"""Geopolitics: a structural VAR on Philippine data in the manner of Caldara and Iacoviello (2022, AER 112(4))
(15 Oct 2026; run 16 Oct 2026 evening).

NOT FOR CITATION until reviewed. Run:  py preshock/geopolitics_svar.py      (a few minutes: 1,000 bootstrap draws x 6 models)

Question: does a rise in geopolitical risk for the Philippines move the peso, output or investment? This is the second
robustness check on the 2026 scenarios' finding "no measurable effect on output; the peso weakens somewhat" (the first, panel local
projections across emerging economies, is preshock/geopolitics_panel_lp.py).

Design (Caldara and Iacoviello 2022, section on macroeconomic effects: a VAR in log levels with the GPR index ordered first,
identified recursively, so that within the quarter the GPR affects everything and nothing else affects the GPR):
  Main model, quarterly 2000 Q1 - 2026 Q2 (the latest quarter with every series):
    y = [ln GPR (Philippines), ln Dubai oil (US$), ln pesos per US$, ln real GDP, ln real fixed investment (GFCF)], x 100
    two lags; constant, quarter dummies, and one dummy each for 2020 Q2 and 2020 Q3 (the COVID lockdown); Cholesky in that
    order. Responses to a one-standard-deviation GPR shock, 90% bands from a residual bootstrap (1,000 draws; recursive design).
  Robustness:
    R1 oil first and block-exogenous (a small open economy cannot move world oil prices), GPR second;
    R2 the GPR in levels instead of logs (the index is a count of articles; several months are low);
    R3 sample from 2010 Q1;  R4 four lags.
  Extended model, quarterly 2013 Q1 on: adds remittances and FDI (US$, quarterly sums, ln x 100) after the peso, from the
    a compiled monthly panel (not distributed). About 45 quarters for seven
    variables: indicative only.
What 2025-26 cost: the decomposition from 2025 Q1 (infinity_gem.svar.decomposition_since, check VD1): actual = the forecast from
  data to 2024 Q4 + the effect of each structural shock since; the GPR column is the effect of geopolitical-risk shocks.

Data: data/raw/macro/ (Caldara-Iacoviello GPR for the Philippines, GPRHC_PHL; World Bank Pink Sheet Dubai crude; BIS peso per
US$), PSA OpenSTAT national accounts at constant 2018 prices (not seasonally adjusted: the quarter dummies take the seasons).
Loaded with preshock/domestic_politics_lp.quarterly_panel() so the two scripts use the same series.
"""
import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "preshock"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from infinity_gem import svar                                  # noqa: E402
from infinity_gem.stochastic import load_task1_monthly        # noqa: E402
from domestic_politics_lp import quarterly_panel           # noqa: E402

H, REPS, SEED = 12, 1000, 1
SHOW = [0, 1, 2, 4, 8, 12]
LABEL = {"gpr": "GPR", "oil": "Oil (Dubai)", "fx": "Peso per US$ (+ = weaker)", "remit": "Remittances", "fdi": "FDI",
         "gdp": "Real GDP", "gfcf": "Fixed investment (GFCF)"}


def deterministic(idx):
    qd = pd.get_dummies(pd.Series(idx.quarter, index=idx), prefix="q", drop_first=True, dtype=float)
    for qq in ("2020Q2", "2020Q3"):
        qd[f"d{qq}"] = (idx == pd.Period(qq, "Q")).astype(float)
    return qd


def data_main(gpr_logs=True, start="2000Q1"):
    q = quarterly_panel()
    d = pd.DataFrame({"gpr": 100 * np.log(q["gpr"]) if gpr_logs else q["gpr"], "oil": 100 * np.log(q["oil"]),
                      "fx": 100 * np.log(q["fx"]), "gdp": 100 * np.log(q["gdp"]), "gfcf": 100 * np.log(q["gfcf"])})
    return d.loc[start:].dropna()


def data_extended():
    d = data_main(start="2013Q1")
    m = load_task1_monthly()
    m.index = pd.PeriodIndex(m.index, freq="M")
    qs = m[["remit", "fdi"]].groupby(m.index.asfreq("Q")).agg(lambda s: s.sum() if s.notna().sum() == 3 else np.nan)
    d = d.join(100 * np.log(qs), how="inner").dropna()
    return d[["gpr", "oil", "fx", "remit", "fdi", "gdp", "gfcf"]]


def estimate(d, p=2, order=None, exog_block=()):
    d = d[order] if order else d
    m = svar.fit(d, p, deterministic=deterministic(d.index), exog_block=exog_block, sigma_dof="ols")
    b = svar.bootstrap_irf(m, H, reps=REPS, seed=SEED)
    return m, b


def table(m, b, shock="gpr", scale=1.0):
    """Responses to a one-s.d. shock to `shock`, in % (variables are 100 x ln), at the SHOW horizons."""
    j = m.names.index(shock)
    rows = []
    for v in m.names:
        i = m.names.index(v)
        for h in SHOW:
            pt, lo, hi = b["point"][h, i, j] * scale, b["lower"][h, i, j] * scale, b["upper"][h, i, j] * scale
            rows.append({"variable": LABEL[v], "quarters after": h, "effect (%)": pt, "90% low": lo, "90% high": hi,
                         "significant": "yes" if lo > 0 or hi < 0 else ""})
    return pd.DataFrame(rows)


def decomp_2025(m, start="2025Q1"):
    B0 = svar.cholesky(m)
    row = list(m.index).index(pd.Period(start, "Q"))
    dc = svar.decomposition_since(m, B0, row)
    j = m.names.index("gpr")
    idx = m.index[row:]
    out = pd.DataFrame({LABEL[v]: dc["contribution"][:len(idx), m.names.index(v), j] for v in ("fx", "gdp", "gfcf")}, index=idx)
    out["GPR, actual minus forecast (%)"] = dc["actual"][:len(idx), j] - dc["forecast"][:len(idx), j]
    return out


def main():
    stamp = dt.date.today().strftime("%Y%m%d")
    runs = {}
    d0 = data_main()
    print("main sample", d0.index.min(), d0.index.max(), len(d0))
    runs["Main: GPR first, log levels, 2 lags, 2000 Q1-"] = estimate(d0)
    runs["R1: oil first and block-exogenous, then GPR"] = estimate(d0, order=["oil", "gpr", "fx", "gdp", "gfcf"], exog_block=["oil"])
    runs["R2: GPR in levels"] = estimate(data_main(gpr_logs=False))
    runs["R3: sample from 2010 Q1"] = estimate(data_main(start="2010Q1"))
    runs["R4: four lags"] = estimate(d0, p=4)
    dx = data_extended()
    print("extended sample", dx.index.min(), dx.index.max(), len(dx))
    runs["Extended: + remittances and FDI, 2013 Q1-"] = estimate(dx)

    tabs = {}
    for name, (m, b) in runs.items():
        t = table(m, b)
        tabs[name] = t
        print(f"== {name} | stable: {m.stable()} | T = {len(m.U)}")
        print(t[t["quarters after"].isin([0, 4, 8])].round(2).to_string(index=False))
    main_m, main_b = runs["Main: GPR first, log levels, 2 lags, 2000 Q1-"]
    gsd = float(np.sqrt(main_m.Sigma[0, 0]))
    dec = decomp_2025(main_m)
    print(dec.round(2).to_string())

    # summary: the main result and how robust it is, at 4 and 8 quarters
    summ = []
    for name, t in tabs.items():
        for v in ("Peso per US$ (+ = weaker)", "Real GDP", "Fixed investment (GFCF)"):
            for h in (4, 8):
                r = t[(t["variable"] == v) & (t["quarters after"] == h)].iloc[0]
                summ.append({"model": name, "variable": v, "quarters after": h, "effect (%)": r["effect (%)"],
                             "90% band": f"{r['90% low']:.2f} to {r['90% high']:.2f}", "significant": r["significant"]})
    S = pd.DataFrame(summ)
    pd.concat({k: v for k, v in tabs.items()}, names=["model"]).to_csv(OUT_DIR / f"geopolitics_svar_{stamp}_responses.csv")
    dec.to_csv(OUT_DIR / f"geopolitics_svar_{stamp}_decomposition_2025.csv")

    L = [f"# Geopolitical risk in a structural VAR on Philippine data ({dt.date.today():%d %B %Y})", "",
         "**NOT FOR CITATION** until reviewed (Infinity GEM 0.3.7(a)). Script: `preshock/geopolitics_svar.py` "
         "(design and sources in its notes). Caldara and Iacoviello (2022, AER) design: log levels, the GPR ordered first, recursive "
         "identification, two lags; quarterly, constant 2018 prices, quarter and 2020 Q2-Q3 dummies; 90% bands from a residual "
         f"bootstrap ({REPS:,} draws). Responses to a one-standard-deviation GPR shock (main model: {gsd:.0f}% of the index).", "",
         "## Summary (effects in %, cumulative levels)", "", S.to_markdown(index=False, floatfmt=".2f"), "",
         "## Main model: all responses", "",
         tabs["Main: GPR first, log levels, 2 lags, 2000 Q1-"].to_markdown(index=False, floatfmt=".2f"), "",
         "## Extended model (remittances and FDI, from 2013; indicative)", "",
         tabs["Extended: + remittances and FDI, 2013 Q1-"].to_markdown(index=False, floatfmt=".2f"), "",
         "## What geopolitical-risk shocks did in 2025-26 (main model; % effect on the level, from 2025 Q1)", "",
         dec.reset_index().rename(columns={"index": "quarter"}).to_markdown(index=False, floatfmt=".2f"), "",
         "## Notes", "",
         f"- Samples: main {d0.index.min()}-{d0.index.max()} ({len(d0)} quarters); extended {dx.index.min()}-{dx.index.max()} "
         f"({len(dx)} quarters).",
         "- Stability: " + "; ".join(f"{k.split(':')[0]} {'stable' if m.stable() else 'NOT stable'}" for k, (m, b) in runs.items()) + ".",
         "- Comparison: panel local projections (`outputs/geopolitics_panel_lp_20261016.md`): own-country GPR moves ASEAN-5 currencies "
         "about +0.2% at 12 months (not significant) and prices +0.16% (significant). Caldara and Iacoviello find, for the United "
         "States, that higher geopolitical risk lowers investment and employment.", ""]
    rep = OUT_DIR / f"geopolitics_svar_{stamp}.md"
    rep.write_text("\n".join(L), encoding="utf-8")
    print("saved", rep)


OUT_DIR = ROOT / "outputs"

if __name__ == "__main__":
    main()
