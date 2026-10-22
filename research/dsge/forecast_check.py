"""DSGE research (Stage 3) (21 Oct 2026, about 1:50 AM): a pseudo-out-of-sample forecast check
of an estimated DSGE.

The model is estimated on data to a cut-off quarter (estimate_rot.py ... end=2023Q4; its chains carry "_to2023Q4"). From the
cut-off it forecasts the observables 1 to h quarters ahead, and the forecasts are compared with what happened (2024Q1-2026Q2,
which includes the 2026 oil shock). Two exercises:
  1. multi-step forecasts from the cut-off: the state filtered to the cut-off, then the model's own dynamics (the posterior
     predictive mean over `draws` random posterior draws; 90% bands at the posterior mean from the state-forecast covariance,
     which carries the shocks and the filtering uncertainty but not the parameters' spread, reported separately);
  2. one-step-ahead forecasts updated quarter by quarter through the evaluation period (the Kalman filter's predictions at the
     posterior mean), the usual test of a model's short-run dynamics.
Benchmarks: the unconditional mean (zero in the demeaned units of the estimation sample) and an AR(1) per series fitted on the
estimation sample. A root mean squared error (RMSE) ratio below one means the model beat the benchmark.
Units: the observables are demeaned (and GDP growth and inflation de-seasonalised) with the ESTIMATION sample's means
(ph_data adjust_end=<cut-off>), so the evaluation quarters are measured as the model saw its sample; the STL seasonal adjustment
of GDP uses all quarters on file (a small leak of later data into the seasonal factors, noted in the report).
Run: py forecast_check.py model=htmu prior=ratio sample=long gdp=stl end=2023Q4 [h=10] [draws=200] [seed=0] [w=1]
     (the model arguments as for estimate_rot.py; the chains of that specification must exist)
Writes outputs/dsge_forecast_check_<stamp>_<model><tags>.md
"""
from __future__ import annotations

import datetime as dt
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import linalg

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import estimate as E0        # noqa: E402
import estimate_rot as ER    # noqa: E402  (reads model=, prior=, sample=, gdp=, end=, theta_fix= ...)
import ph_data               # noqa: E402
from smc import matching_chains   # noqa: E402

OUT = HERE.parents[1] / "outputs"
LABELS = {"dy": "GDP growth (% a quarter)", "pi": "CPI inflation (% a quarter)", "i": "policy rate (% a quarter)",
          "de": "peso depreciation (% a quarter)", "doil": "Dubai crude change (%)", "dystar": "world GDP growth (%)"}


def _arg(name, default, cast=str):
    return next((cast(a.split("=", 1)[1]) for a in sys.argv[1:] if a.startswith(f"{name}=")), default)


def full_data() -> pd.DataFrame:
    """The observables of estimate_rot.observables(), to the sample's own end, in the units of the estimation sample (adjust_end)."""
    kw = dict(end=ph_data.LONG_END, covid="missing") if ER.SAMPLE == "long" else {}
    if ER.GDP_SA == "stl":
        kw["gdp_sa"] = "stl"
    kw["adjust_end"] = ER.END
    if ER.MODEL in ("oilw", "oilf"):
        return ph_data.observables_oilw(world=ER.WORLD, **kw)[E0.OBS + ["doil", "dystar"]]
    if ER.MODEL in ("oil", "oilu"):
        return ph_data.observables_oil(**kw)[E0.OBS + ["doil"]]
    return ph_data.observables(**kw)[E0.OBS]


def kalman_filter(Pm, Rm, Q, H, Z, me=1e-4):
    """estimate.kalman_loglik's recursion (missing entries skipped), returning the predicted state and covariance for the quarter
    after the last row, and the one-step-ahead prediction of every row (made before that row is seen)."""
    n = Pm.shape[0]
    RQR = Rm @ Q @ Rm.T
    Sig = linalg.solve_discrete_lyapunov(Pm, RQR)
    x = np.zeros(n)
    Me = np.eye(H.shape[0]) * me
    preds = []
    for z in Z:
        preds.append(H @ x)
        ok = np.isfinite(z)
        if ok.all():
            Hk, zk, Mk = H, z, Me
        elif not ok.any():
            x = Pm @ x
            Sig = Pm @ Sig @ Pm.T + RQR
            continue
        else:
            Hk, zk, Mk = H[ok], z[ok], Me[np.ix_(ok, ok)]
        Fm = Hk @ Sig @ Hk.T + Mk
        e = zk - Hk @ x
        cf = linalg.cho_factor(Fm)
        K = Pm @ Sig @ Hk.T @ linalg.cho_solve(cf, np.eye(len(zk)))
        x = Pm @ x + K @ e
        Sig = Pm @ Sig @ Pm.T + RQR - K @ Fm @ K.T
    return x, Sig, RQR, np.array(preds)


def system_at(theta):
    kw, sds = ER.split(theta)
    sol, _ = ER.R.solve(ER.R.Params(rule="output", **{**kw, **ER.FIXED}))
    return ER.state_space(sol, sds, kw.get("chi_o", 0.0))


def forecast(theta, Z_est, h, me=1e-4):
    """(point forecasts h x m, their s.d. h x m) from the state filtered through Z_est."""
    Pm, Rm, Q, H = system_at(theta)
    x, Sig, RQR, _ = kalman_filter(Pm, Rm, Q, H, Z_est, me)
    f, s = [], []
    for _ in range(h):
        f.append(H @ x)
        s.append(np.sqrt(np.diag(H @ Sig @ H.T) + me))
        x, Sig = Pm @ x, Pm @ Sig @ Pm.T + RQR
    return np.array(f), np.array(s)


def ar1(y: np.ndarray) -> float:
    a, b = y[1:], y[:-1]
    ok = np.isfinite(a) & np.isfinite(b)
    return float((a[ok] * b[ok]).sum() / (b[ok] ** 2).sum())


def rmse(err: np.ndarray) -> float:
    e = err[np.isfinite(err)]
    return float(np.sqrt(np.mean(e ** 2))) if e.size else float("nan")


def main():
    h, draws, seed, w = int(_arg("h", 10)), int(_arg("draws", 200)), int(_arg("seed", 0)), float(_arg("w", 1.0))
    if ER.END is None:
        raise SystemExit("forecast_check needs end=<cut-off quarter> (the estimation sample's end), e.g. end=2023Q4")
    t0 = time.time()
    df = full_data()
    cut = pd.Period(ER.END, "Q")
    Z_est, Z_eval = df.loc[:cut].to_numpy(), df.loc[cut + 1:].to_numpy()
    eval_idx = df.loc[cut + 1:].index
    h = min(h, len(Z_eval))
    Z_check = ER.observables()
    same = Z_check.shape == Z_est.shape and np.allclose(np.nan_to_num(Z_check, nan=-9e9), np.nan_to_num(Z_est, nan=-9e9))
    files = matching_chains(ER, w, None)
    if not files:
        raise SystemExit(f"no chains for this specification (tag _w{w:g}{ER.PTAG}{ER.STAG}); run estimate_rot.py with end={ER.END} first")
    D = np.vstack([np.load(f) for f in files])
    mean = D.mean(0)
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(D), size=min(draws, len(D)), replace=False)
    F = []
    for i in idx:
        try:
            F.append(forecast(D[i], Z_est, h)[0])
        except (ValueError, linalg.LinAlgError):
            continue
    F = np.array(F)
    f_mean, f_lo, f_hi = F.mean(0), np.percentile(F, 5, 0), np.percentile(F, 95, 0)
    f_pm, s_pm = forecast(mean, Z_est, h)
    cols = list(df.columns)
    m = len(cols)
    A = Z_eval[:h]
    # benchmarks
    rho = np.array([ar1(Z_est[:, j]) for j in range(m)])
    last = Z_est[-1]
    ar_multi = np.array([rho ** k * last for k in range(1, h + 1)])
    err_model, err_mean, err_ar = A - f_mean, A - 0.0, A - ar_multi
    # one-step-ahead through the evaluation period (posterior mean): filter the whole sample, read the predictions
    Pm, Rm, Q, H = system_at(mean)
    _, _, _, preds = kalman_filter(Pm, Rm, Q, H, np.vstack([Z_est, Z_eval]))
    p1 = preds[len(Z_est):len(Z_est) + h]
    prev = np.vstack([Z_est[-1:], Z_eval[:h - 1]])
    e1_model, e1_ar, e1_mean = A - p1, A - rho * prev, A - 0.0
    rows = []
    for j, c in enumerate(cols):
        for name, sl in (("horizons 1-4", slice(0, 4)), (f"horizons 5-{h}", slice(4, h)), (f"all 1-{h}", slice(0, h))):
            rm, rb, ra = rmse(err_model[sl, j]), rmse(err_mean[sl, j]), rmse(err_ar[sl, j])
            rows.append({"series": LABELS.get(c, c), "horizons": name, "model RMSE": rm, "mean-forecast RMSE": rb, "AR(1) RMSE": ra,
                         "model / mean": rm / rb if rb else np.nan, "model / AR(1)": rm / ra if ra else np.nan})
    T1 = pd.DataFrame(rows).set_index(["series", "horizons"])
    rows = []
    for j, c in enumerate(cols):
        rm, rb, ra = rmse(e1_model[:, j]), rmse(e1_mean[:, j]), rmse(e1_ar[:, j])
        rows.append({"series": LABELS.get(c, c), "model RMSE": rm, "mean-forecast RMSE": rb, "AR(1) RMSE": ra,
                     "model / mean": rm / rb if rb else np.nan, "model / AR(1)": rm / ra if ra else np.nan})
    T2 = pd.DataFrame(rows).set_index("series")
    paths = {}
    for j, c in enumerate(cols):
        paths[(LABELS.get(c, c), "actual")] = A[:, j]
        paths[(LABELS.get(c, c), "forecast, predictive mean")] = f_mean[:, j]
        paths[(LABELS.get(c, c), "90% band, posterior mean (low)")] = f_pm[:, j] - 1.645 * s_pm[:, j]
        paths[(LABELS.get(c, c), "90% band, posterior mean (high)")] = f_pm[:, j] + 1.645 * s_pm[:, j]
        paths[(LABELS.get(c, c), "point forecasts across draws, 5%-95%")] = [f"{a:.2f} to {b:.2f}" for a, b in zip(f_lo[:, j], f_hi[:, j])]
        paths[(LABELS.get(c, c), "one-step-ahead (filter)")] = p1[:, j]
    T3 = pd.DataFrame(paths, index=[str(q) for q in eval_idx[:h]]).T
    cover = {LABELS.get(c, c): float(np.mean(np.abs(A[:, j] - f_pm[:, j]) <= 1.645 * s_pm[:, j])) for j, c in enumerate(cols)}
    # the inflation and GDP-growth sums over the evaluation period, in the sample's units (what the model foresaw in total)
    tot = {LABELS.get(c, c): (float(np.nansum(A[:, j])), float(f_mean[:, j].sum())) for j, c in enumerate(cols)}
    stamp = dt.datetime.now()
    tag = f"_{ER.MODEL}_w{w:g}{ER.PTAG}{ER.STAG}"
    path = OUT / f"dsge_forecast_check_{stamp:%Y%m%d_%H%M}{tag}.md"
    L = [f"# Pseudo-out-of-sample forecast check: soe_{ER.MODEL} estimated to {ER.END} ({stamp:%d %B %Y, %H:%M})", "",
         f"**NOT FOR CITATION** (research code, `research/dsge/forecast_check.py`). Model `soe_{ER.MODEL}.py`, prior {ER.PRIOR}, sample "
         f"{ER.SAMPLE} to {ER.END}, GDP {ER.GDP_SA}, calibrated {ER.FIXED or 'none'}; chains {', '.join(f.name for f in files)} "
         f"({D.shape[0]:,} draws; {len(F)} used for the predictive mean). Evaluation quarters: {eval_idx[0]} to {eval_idx[h - 1]} "
         f"({h} quarters). Units: % a quarter, demeaned and de-seasonalised with the estimation sample's means (the evaluation data "
         f"equal `estimate_rot.observables()` on the estimation quarters: {same}). {time.time() - t0:.0f} s.", "",
         "- **Reading:** a ratio below one means the DSGE's forecast beat the benchmark (the unconditional mean, or an AR(1) per series "
         "fitted on the estimation sample). Multi-step forecasts from the cut-off cannot know the 2026 oil shock; the one-step-ahead "
         "test, updated each quarter, shows how the model's dynamics track the data once the shocks are in.",
         "- **90% band coverage** (posterior mean; shocks and filtering uncertainty): " + ", ".join(f"{k} {v:.0%}" for k, v in cover.items()) + ".",
         "- **Totals over the evaluation period** (actual against the predictive mean, same units): "
         + "; ".join(f"{k} {a:+.2f} against {b:+.2f}" for k, (a, b) in tot.items()) + ".",
         "- The STL seasonal adjustment of GDP uses all quarters on file (a small leak of later data into the seasonal factors).", "",
         "## 1. Multi-step forecasts from the cut-off: RMSE against the benchmarks", "", T1.to_markdown(floatfmt=".3f"), "",
         "## 2. One-step-ahead forecasts through the evaluation period (posterior mean): RMSE", "", T2.to_markdown(floatfmt=".3f"), "",
         "## 3. Paths: actual, forecasts and bands", "", T3.to_markdown(floatfmt=".2f"), ""]
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:9]))
    print(T1.to_string(float_format=lambda v: f"{v:.3f}"))
    print("saved", path)


if __name__ == "__main__":
    main()
