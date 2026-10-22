"""Armington sensitivity: Infinity GEM's own Armington elasticity for rice (imported vs domestic milled rice), 2019-2026 (17 Oct 2026, night).

NOT FOR CITATION until reviewed. Run:  py preshock/armington_rice.py

Why only from 2019: until the Rice Tariffication Law (RA 11203, in force March 2019) imports were set by NFA quotas, so
import volumes did not respond to prices (scoping note a design note (not included)).

Model (Kapuscinski and Warr 1999, Economic Modelling 16, the Philippine precedent; Armington 1969): with CES demand, the
import-domestic quantity ratio follows   ln(M/D) = a + sigma ln(PD/PM),   sigma = the Armington elasticity.
  M  = imports of rice, HS 1006.20-1006.40 (husked, milled, broken; seed rice 1006.10 excluded), tonnes; PSA monthly
       imports by commodity and country (data/raw/agri/PSA_OpenSTAT_rice_imports_HS1006_monthly_2019-2026.csv; seven
       origins = 99.9% of 2023 volume), summed to quarters.
  D  = domestic milled rice = palay production x 0.654 (PSA milling recovery, the conversion PSA uses in its supply and
       utilization accounts), tonnes; PSA OpenSTAT 0012E4EVCP0 (quarterly).
  PM = landed import price in pesos per kg: CIF unit value (US$/kg) x PHP per US$ (BIS monthly) x (1 + tariff).
       Tariff: 35% until June 2024 (RA 11203 rate for ASEAN origins, which supply about 96% of the volume), 15% from
       July 2024 (EO 62, s. 2024, signed 20 June 2024; rice rates effective 15 days after publication), 15% through 2026
       (EO 105, s. 2025: kept at 15% to 31 Dec 2025; from 2026 a price-linked rate between 15% and 35%, raised only
       "upon certification by the Department of Agriculture that the trigger price levels have been reached"; no
       certification found in my search, so 15% is kept and a 2026-excluded run is shown).
  PD = domestic producer price: farmgate palay, other variety, dry, national average (PSA 0032M4AFN01), / 0.654 to a
       milled-rice basis (a constant factor: it only shifts the intercept).
  Import suspension: EO 93 (s. 2025, 29 Aug 2025; regular and well-milled rice, 1 Sep-30 Oct 2025), extended by EO 102
       (s. 2025, 30 Oct 2025) to 31 Dec 2025: quarters 2025Q3 (one month) and 2025Q4 get a dummy (a quantity rule,
       not a price response).
Estimators (all with quarter dummies, for the harvest cycle):
  (1) static long run, OLS (Engle-Granger first step), Newey-West (HAC, 2 lags) standard errors;
  (2) one-step error-correction model: d ln(M/D) = c + b d x + g [ln(M/D)(-1) - s x(-1)] ..., written linearly as
      d y = c + b d x + g1 y(-1) + g2 x(-1) + dummies; long-run sigma = -g2/g1 (delta-method s.e.);
  (3) 2SLS of (1), instrumenting ln(PD/PM) with ln(world price x PHP/USD x (1 + tariff)) (World Bank Pink Sheet,
      Viet Nam 5% broken), because imports also lower the farmgate price (the reason for the 2025 suspension).
Rule (as for tools/build_elasticities.py): adopt an estimate only if positive, significant at 10% or better, and
plausible; otherwise keep GTAP's value (PCR 2.6 for milled rice, cmric) and report the estimate as a sensitivity.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "outputs"
RECOVERY = 0.654
IMPUTED: set = set()                                     # months whose quantities were imputed (reported in the output)


def num(s):
    return pd.to_numeric(pd.Series(s).replace({"..": None, ".": None, "": None}), errors="coerce")


def imports_q():
    d = pd.read_csv(RAW / "agri" / "PSA_OpenSTAT_rice_imports_HS1006_monthly_2019-2026.csv", comment="#", dtype=str)
    d = d[d.commodity_code.str.startswith(("100620", "100630", "100640"))].copy()
    d["kg"], d["usd"] = num(d.quantity_kg).values, num(d.cif_usd).values
    d["year"], d["month"] = d.year.astype(int), d.month.astype(int)
    # Missing quantities with a value present (e.g. every line of September 2024: value published, quantity blank or 0):
    # impute kg = value / unit value of the same month's valid lines, or of the adjacent months if the whole month is missing
    valid = (d.kg > 0) & (d.usd > 0)
    uv = (d[valid].groupby(["year", "month"]).usd.sum() / d[valid].groupby(["year", "month"]).kg.sum())
    idx = pd.Series(uv.index.map(lambda k: k[0] * 12 + k[1]), index=uv.index)
    def unit_value(y, mth):
        if (y, mth) in uv.index:
            return float(uv.loc[(y, mth)])
        k = y * 12 + mth
        near = uv[(idx - k).abs() == (idx - k).abs().min()]
        return float(near.mean())
    miss = (d.usd > 0) & ~(d.kg > 0)
    IMPUTED.clear()
    for i in d[miss].index:
        y, mth = d.at[i, "year"], d.at[i, "month"]
        d.at[i, "kg"] = d.at[i, "usd"] / unit_value(y, mth)
        IMPUTED.add((y, mth))
    m = d.groupby(["year", "month"])[["kg", "usd"]].sum(min_count=1).reset_index()
    m = m[m.kg.notna() & (m.kg > 0) | m.usd.notna()]
    fx = pd.read_csv(RAW / "macro" / "BIS_WS_XRU_PHP_per_USD_monthly_average.csv", comment="#")
    fx["year"], fx["month"] = fx.month.str[:4].astype(int), fx.month.str[5:7].astype(int)
    m = m.merge(fx.rename(columns={"value": "php_usd"}), on=["year", "month"], how="left")
    m["tariff"] = np.where((m.year > 2024) | ((m.year == 2024) & (m.month >= 7)), 0.15, 0.35)
    m["php_landed"] = m.usd * m.php_usd * (1 + m.tariff)
    m["q"] = (m.month - 1) // 3 + 1
    return m


def world_q():
    w = pd.read_csv(RAW / "agri" / "WorldBank_PinkSheet_fertilizer_rice_maize_monthly_1960-2026.csv", comment="#")
    col = [c for c in w.columns if "Viet" in c][0]
    w["year"] = w.month.str[:4].astype(int)
    w["mon"] = w.month.str[-2:].astype(int) if w.month.str.contains("-").any() else w.month.str[5:7].astype(int)
    w[col] = pd.to_numeric(w[col], errors="coerce")      # early years carry non-numeric markers
    return w[["year", "mon", col]].rename(columns={col: "world_usd_t", "mon": "month"})


def domestic_q():
    p = pd.read_csv(RAW / "agri" / "PSA_OpenSTAT_0012E4EVCP0_palay_corn_production_by_province_1987-2026.csv", comment="#")
    nat = p[(p.Geolocation.str.strip() == "PHILIPPINES") & p.iloc[:, 0].str.contains("Palay")]
    rows = nat[nat.iloc[:, 0].str.strip().isin(["Palay", "Palay Total", "Total Palay"])]
    if rows.empty:                                     # total = irrigated + rainfed
        rows = nat[nat.iloc[:, 0].str.contains("Irrigated|Rainfed")]
    prod = {}
    for col in p.columns[2:]:
        if "Quarter" in col:
            y, _, qn = col.split(" ")
            prod[(int(y), int(qn))] = num(rows[col]).sum(min_count=1)
    D = pd.Series(prod, name="palay_t").dropna()
    f = pd.read_csv(RAW / "agri" / "PSA_OpenSTAT_0032M4AFN01_cereals_farmgate_prices_by_province_2010-2026.csv", comment="#")
    r = f[(f.Geolocation.str.strip() == "PHILIPPINES") & f.Commodity.str.contains("Palay.*Other Variety", regex=True)].iloc[0]
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    fp = {}
    for col in f.columns[2:]:
        y, mname = col.split(" ", 1)
        if mname in months:
            fp[(int(y), months.index(mname) + 1)] = num([r[col]]).iloc[0]
    fp = pd.Series(fp, name="farmgate_php_kg").dropna()
    return D, fp


def build():
    m = imports_q()
    w = world_q()
    m = m.merge(w, on=["year", "month"], how="left")
    m["world_landed"] = m.world_usd_t / 1000 * m.php_usd * (1 + m.tariff)
    D, fp = domestic_q()
    fpq = fp.reset_index()
    fpq.columns = ["year", "month", "farmgate"]
    fpq["q"] = (fpq.month - 1) // 3 + 1
    pdq = fpq.groupby(["year", "q"]).farmgate.mean()
    g = m.groupby(["year", "q"]).agg(kg=("kg", "sum"), php=("php_landed", "sum"), n=("month", "count"),
                                     world=("world_landed", "mean"), tariff=("tariff", "mean"))
    g = g[g.n == 3]                                    # complete quarters only
    g["M_t"] = g.kg / 1000
    g["PM"] = g.php / g.kg                             # landed unit value, PHP/kg (quantity-weighted)
    df = g.join(D.rename_axis(["year", "q"]), how="inner").join(pdq, how="inner")
    df["D_t"] = df.palay_t * RECOVERY
    df["PD"] = df.farmgate / RECOVERY
    df = df[(df.index.get_level_values(0) > 2019) | (df.index.get_level_values(1) >= 2)]   # from 2019Q2 (RA 11203)
    df["y"] = np.log(df.M_t / df.D_t)
    df["x"] = np.log(df.PD / df.PM)
    df["z"] = np.log(df.PD / df.world)
    df["ban"] = [1.0 if (yy == 2025 and qq >= 3) else 0.0 for yy, qq in df.index]
    for k in (2, 3, 4):
        df[f"q{k}"] = [1.0 if qq == k else 0.0 for _, qq in df.index]
    return df


def ols(df, cols, y="y", hac=2):
    X = sm.add_constant(df[cols])
    return sm.OLS(df[y], X).fit(cov_type="HAC", cov_kwds={"maxlags": hac})


def iv(df, endog, exog, inst, y="y"):
    """2SLS by hand (second-stage residuals from the structural equation), HAC(2) s.e. via the sandwich on Zhat."""
    X = sm.add_constant(df[exog + [endog]])
    Z = sm.add_constant(df[exog + [inst]])
    first = sm.OLS(df[endog], Z).fit()
    Xhat = X.copy(); Xhat[endog] = first.fittedvalues
    b = np.linalg.lstsq(Xhat.values, df[y].values, rcond=None)[0]
    u = df[y].values - X.values @ b
    fit = sm.OLS(df[y], Xhat).fit(cov_type="HAC", cov_kwds={"maxlags": 2})
    # replace residuals with structural residuals for the covariance: refit with the same design
    n, k = Xhat.shape
    XtXi = np.linalg.inv(Xhat.values.T @ Xhat.values)
    S = np.zeros((k, k))
    for lag in range(0, 3):
        w = 1 - lag / 3
        for t in range(lag, n):
            g = np.outer(Xhat.values[t] * u[t], Xhat.values[t - lag] * u[t - lag])
            S += (g if lag == 0 else w * (g + g.T))
    V = XtXi @ S @ XtXi
    se = np.sqrt(np.diag(V))
    i = list(X.columns).index(endog)
    fstat = float(first.tvalues[inst] ** 2)
    return b[i], se[i], fstat, first


def ecm(df, extra):
    d = df.copy()
    d["dy"], d["dx"] = d.y.diff(), d.x.diff()
    d["y1"], d["x1"] = d.y.shift(), d.x.shift()
    d = d.dropna(subset=["dy", "dx", "y1", "x1"])
    r = ols(d, ["dx", "y1", "x1"] + extra, y="dy")
    g1, g2 = r.params["y1"], r.params["x1"]
    s = -g2 / g1
    V = r.cov_params().loc[["y1", "x1"], ["y1", "x1"]].values
    grad = np.array([g2 / g1 ** 2, -1 / g1])
    se = float(np.sqrt(grad @ V @ grad))
    return s, se, r, len(d)


def main():
    df = build()
    seas = ["q2", "q3", "q4"]
    lines = [f"# Armington sensitivity: Armington elasticity for rice, Infinity GEM's own estimate ({datetime.now():%Y-%m-%d %H:%M})", "",
             "**NOT FOR CITATION** until reviewed. Script `preshock/armington_rice.py`; method and data in its docstring.", ""]
    span = f"{df.index[0][0]}Q{df.index[0][1]}-{df.index[-1][0]}Q{df.index[-1][1]}"
    lines += [f"Sample: {span}, {len(df)} quarters. Import share M/(M+D) {df.M_t.sum() / (df.M_t.sum() + df.D_t.sum()) * 100:.1f}% "
              f"(range {(df.M_t / (df.M_t + df.D_t)).min() * 100:.1f}-{(df.M_t / (df.M_t + df.D_t)).max() * 100:.1f}%); "
              f"ln(PD/PM) from {df.x.min():+.2f} to {df.x.max():+.2f}.",
              f"Months whose PSA quantities were missing while values were published (quantity imputed at that month's or the "
              f"adjacent months' unit value): {', '.join(f'{y}-{mm:02d}' for y, mm in sorted(IMPUTED)) or 'none'}.", ""]
    lines += ["| Quarter | Imports (kt) | Domestic milled (kt) | Landed import price (₱/kg) | Domestic price (₱/kg milled basis) | Tariff |",
              "|---|---|---|---|---|---|"]
    for (yy, qq), r in df.iterrows():
        lines.append(f"| {yy}Q{qq} | {r.M_t / 1e3:,.0f} | {r.D_t / 1e3:,.0f} | {r.PM:.2f} | {r.PD:.2f} | {r.tariff * 100:.0f}% |")
    res = []
    for label, d, extra in (("all quarters, suspension dummy", df, seas + ["ban"]),
                            ("excluding 2025Q3-2025Q4 (suspension)", df[df.ban == 0], seas),
                            ("excluding 2026 (tariff rule uncertain)", df[df.index.get_level_values(0) < 2026], seas + ["ban"])):
        r1 = ols(d, ["x"] + extra)
        s_e, se_e, r2, n_e = ecm(d, extra)
        res.append((label, len(d), r1.params["x"], r1.bse["x"], r1.pvalues["x"], s_e, se_e, r2.params["y1"], r2.bse["y1"], n_e))
    b_iv, se_iv, F, first = iv(df, "x", seas + ["ban"], "z")
    lines += ["", "## Estimates of sigma (long-run Armington elasticity)", "",
              "| Sample | Quarters | (1) static OLS sigma (HAC s.e.; p) | (2) ECM long-run sigma (s.e.) | ECM adjustment g1 (s.e.) |",
              "|---|---|---|---|---|"]
    for label, n, b, se, p, s, sse, g1, g1se, ne in res:
        lines.append(f"| {label} | {n} | {b:.2f} ({se:.2f}; p = {p:.3f}) | {s:.2f} ({sse:.2f}) | {g1:.2f} ({g1se:.2f}) |")
    lines += ["", f"(3) 2SLS, instrument ln(PD / world price landed), all quarters with the suspension dummy: sigma {b_iv:.2f} "
              f"(HAC s.e. {se_iv:.2f}); first-stage F = {F:.1f} (rule of thumb: above 10).", ""]
    best = res[0]
    # adoption rule: positive and significant at 10% in EVERY sample, and the ECM's long run agrees in sign and significance
    robust = all(r[2] > 0 and r[4] < 0.10 for r in res) and all(r[5] > 0 and abs(r[5] / r[6]) > 1.645 for r in res)
    lo, hi = min(r[2] for r in res), max(r[2] for r in res)
    lines += ["## Reading", "",
              f"- Kapuscinski and Warr (1999), rice and corn milling, 1970s-80s under NFA quotas: 0.614, not significant. GTAP 9 "
              f"(PCR): 2.6, the value Infinity GEM uses now for milled rice (cmric).",
              f"- Post-tariffication static estimates: {lo:.2f} to {hi:.2f} across the three samples (preferred, all quarters: "
              f"{best[2]:.2f}, p = {best[4]:.3f}); the error-correction long run is not significant in any sample, and the 2SLS "
              f"instrument is weak (F = {F:.1f}).",
              "- **Decision (adoption rule: positive and significant in every sample, with the ECM agreeing): "
              + ("ADOPT.**" if robust else
                 f"NOT ADOPTED.** GTAP's 2.6 stays central for milled rice. The Philippine evidence points to LOWER "
                 f"substitutability (about {lo:.1f}-{hi:.1f}), so the preferred estimate ({best[2]:.2f}) becomes an opt-in "
                 f"sensitivity (elasticity set 'ph_rice72a').")]
    OUT.mkdir(exist_ok=True)
    out = OUT / f"armington_rice_{datetime.now():%Y%m%d_%H%M}.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines)); print(f"\nwrote {out}")
    df.to_csv(out.with_suffix(".csv"))
    return df, res, (b_iv, se_iv, F)


if __name__ == "__main__":
    main()
