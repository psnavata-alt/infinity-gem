"""The public-construction multiplier, estimated from Philippine data: which model's multiplier do the
data support for the infrastructure freeze?

NOT FOR CITATION until reviewed. Run:  py preshock/freeze_multiplier_lp.py

Method: local projections with the cumulative-multiplier IV of Ramey and Zubairy (2018, JPE; to verify), on PSA quarterly
national accounts at constant 2018 prices, 2000Q1-2026Q2:
  shock[t]  = the part of the change in general-government construction (as a share of trend GDP) not predicted by four
              lags of GDP and public-construction changes and quarter dummies (Blanchard-Perotti timing: public
              construction does not respond to GDP within the quarter);
  for h = 0..8:  sum_{j<=h} (Y[t+j] - Y[t-1]) / Ytr[t-1]  =  m_h * sum_{j<=h} (G[t+j] - G[t-1]) / Ytr[t-1]  + controls + e,
              with the G term instrumented by shock[t]. m_h = pesos of GDP per peso of public construction, cumulated to h.
  Controls: four lags of the GDP and G changes, quarter dummies. Ytr = average GDP over the four quarters to t-1. Newey-West
  standard errors (h + 1 lags). Variants: full sample with 2020-21 dummies; pre-2020 sample (as in the CPBRD robustness checks).

Compared with the models' implied multipliers for the P238.3 bn freeze: arithmetic 1.0 (DEPDev's accounting), I-O domestic
inverse 0.68, SAM multiplier (fixed prices) about 1.6, Infinity GEM CGE short run about 0.33.
"""
import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
MAC = ROOT / "data" / "raw" / "macro"
H = 8
MODELS = {"Arithmetic (DEPDev accounting)": 1.0, "I-O, domestic inverse": 161.5 / 238.3,
          "SAM multiplier (fixed prices)": 1.339 / 100 * 28009.93 / 238.3, "Infinity GEM CGE, short run": 0.279 / 100 * 28009.93 / 238.3}


def load() -> pd.DataFrame:
    g = pd.read_csv(MAC / "PSA_OpenSTAT_GDP_by_expenditure_quarterly_2000-2026.csv", comment="#")
    g = g[(g.valuation.str.contains("Constant")) & (g.expenditure == "Gross Domestic Product")]
    g["v"] = pd.to_numeric(g.value_million_php, errors="coerce")
    y = g.set_index(pd.PeriodIndex(g.year.astype(str) + g.quarter, freq="Q"))["v"].rename("Y")
    c = pd.read_csv(MAC / "PSA_OpenSTAT_0542B5BCNQ1_construction_GFCF_by_sector_quarterly_2000-2026.csv", comment="#")
    row = c[c.iloc[:, 0].str.contains("General government")].iloc[0]
    cols = [k for k in c.columns if "Constant" in k]
    gg = pd.Series(pd.to_numeric(row[cols].replace(".", np.nan), errors="coerce").values,
                   index=pd.PeriodIndex([k.split()[-2] + k.split()[-1] for k in cols], freq="Q"), name="G")
    d = pd.concat([y, gg], axis=1).dropna()
    d["Ytr"] = d["Y"].rolling(4).mean().shift(1)
    d["dy"] = d["Y"].diff() / d["Ytr"]
    d["dg"] = d["G"].diff() / d["Ytr"]
    for q in (2, 3, 4):
        d[f"q{q}"] = (d.index.quarter == q).astype(float)
    d["covid"] = ((d.index >= pd.Period("2020Q1", "Q")) & (d.index <= pd.Period("2021Q4", "Q"))).astype(float)
    return d


def _hac(X, u, L):
    """Newey-West meat for moment vectors X*u."""
    S = X * u[:, None]
    M = S.T @ S
    for l in range(1, L + 1):
        w = 1 - l / (L + 1)
        G = S[l:].T @ S[:-l]
        M += w * (G + G.T)
    return M


def lp_iv(d: pd.DataFrame, covid=True):
    lags = pd.concat({f"dy_l{k}": d["dy"].shift(k) for k in range(1, 5)} | {f"dg_l{k}": d["dg"].shift(k) for k in range(1, 5)}, axis=1)
    W = pd.concat([pd.Series(1.0, index=d.index, name="c"), lags, d[["q2", "q3", "q4"] + (["covid"] if covid else [])]], axis=1)
    ok = W.notna().all(axis=1) & d["dg"].notna()
    Wm, dg = W[ok].values, d.loc[ok, "dg"].values
    shock = pd.Series(dg - Wm @ np.linalg.lstsq(Wm, dg, rcond=None)[0], index=d.index[ok])
    out = []
    for h in range(H + 1):
        Ycum = sum((d["Y"].shift(-j) - d["Y"].shift(1)) for j in range(h + 1)) / d["Ytr"]
        Gcum = sum((d["G"].shift(-j) - d["G"].shift(1)) for j in range(h + 1)) / d["Ytr"]
        z = pd.concat([Ycum.rename("y"), Gcum.rename("x"), shock.rename("z"), W], axis=1).dropna()
        Wz = z[W.columns].values
        P = lambda v: v - Wz @ np.linalg.lstsq(Wz, v, rcond=None)[0]           # partial out the controls (FWL)
        yt, xt, zt = P(z["y"].values), P(z["x"].values), P(z["z"].values)
        m = (zt @ yt) / (zt @ xt)
        u = yt - m * xt
        n = len(yt)
        se = np.sqrt(_hac(zt[:, None], u, h + 1)[0, 0]) / abs(zt @ xt)
        b1 = (zt @ xt) / (zt @ zt)                                                 # first stage
        e1 = xt - b1 * zt
        F = b1 ** 2 / (_hac(zt[:, None], e1, h + 1)[0, 0] / (zt @ zt) ** 2)
        out.append({"h (quarters)": h, "cumulative multiplier": m, "s.e.": se, "90% low": m - 1.645 * se, "90% high": m + 1.645 * se,
                    "first-stage F (HAC)": F, "obs": n})
    return pd.DataFrame(out)


def main():
    d = load()
    print(f"Data: {d.index.min()} to {d.index.max()}; public construction share of GDP, mean {(d['G'] / d['Y']).mean() * 100:.1f}%")
    res = {"Full sample, 2020-21 dummy": lp_iv(d, covid=True),
           "Pre-2020 sample": lp_iv(d[d.index < pd.Period("2020Q1", "Q")], covid=False)}
    for k, v in res.items():
        print("==", k); print(v.round(3).to_string(index=False))
    stamp = dt.date.today().strftime("%Y%m%d")
    md = lambda df: df.to_markdown(index=False, floatfmt=".3f") if hasattr(df, "to_markdown") else df.to_string(index=False)
    comp = pd.DataFrame({"model": list(MODELS), "implied multiplier (GDP per peso of public construction)": list(MODELS.values())})
    L = [f"# The public-construction multiplier from Philippine data: local projections ({dt.date.today():%d %B %Y})", "",
         "**NOT FOR CITATION** until reviewed (Infinity GEM 0.3.5). Script: `preshock/freeze_multiplier_lp.py`. Data: PSA "
         "OpenSTAT 0012B5BEXQ1 (GDP) and 0542B5BCNQ1 (construction GFCF by institutional sector), constant 2018 prices, quarterly, "
         f"{d.index.min()}-{d.index.max()}.", "",
         "Method: cumulative-multiplier local projections with an instrument (Ramey and Zubairy 2018), the instrument being the "
         "unpredicted part of public construction (Blanchard-Perotti timing). Multiplier = pesos of GDP per peso of public construction, "
         "both cumulated over h quarters. Newey-West standard errors; 90% bands.", ""]
    for k, v in res.items():
        L += [f"## {k}", "", md(v), ""]
    L += ["## The models' implied multipliers for the P238.3 bn freeze", "", md(comp), "",
          "**How to read.** If the estimated multiplier at 4-8 quarters lies near a model's figure, the data support that model's "
          "transmission. A weak first stage (F below about 10) means the instrument is weak and the multiplier is imprecise. Quarterly "
          "public construction is lumpy and partly seasonal (quarter dummies are included); 105 quarters is short for this method.", ""]
    rep = ROOT / "outputs" / f"freeze_multiplier_lp_{stamp}.md"
    rep.write_text("\n".join(L), encoding="utf-8")
    print(comp.round(3).to_string(index=False)); print("saved", rep)


if __name__ == "__main__":
    main()
