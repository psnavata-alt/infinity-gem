"""DSGE research, milestone 10b (19 Oct 2026, about 8:30 AM): estimate soe_rot.py (rule-of-thumb price setters) on the
Philippine data, with the BSP's PAMPh monetary-policy responses as a system prior.

System prior (Andrle and Benes 2013): besides priors on parameters, a prior on what the model does. Here each PAMPh point
(pamph_targets.py: policy rate, y/y GDP growth, y/y CPI inflation, nominal exchange rate after a policy shock scaled to +0.80 pp)
is a Gaussian prior on the model's response with the tolerances of irf_match.py as standard deviations:
    log posterior = log prior(parameters) + w * (-0.5 * distance to PAMPh) + log likelihood(data),
w = 1 (default) or 0 (data only). Same likelihood, data and shocks as estimate_med.py; indexation replaced by omega_H, omega_F.
Andrle, M., and J. Benes (2013). "System Priors: Formulating Priors about DSGE Models' Properties." IMF Working Paper 13/257.
Run:  py estimate_rot.py [n=20000] [w=1] [model=rot|htm]   (writes outputs/dsge_ph_<model>_estimation_<stamp>_w<w>.md and draws)
model=htm (milestone 11): soe_htm.py, adding the hand-to-mouth share lam_h and the adaptive-expectations weight kappa, both
beta(0.3, 0.15) on [0, 0.9]; the default, model=rot, is milestone 10 unchanged.
prior=ratio (milestone 13, 19 Oct 2026, about 10:25 AM): instead of PAMPh's whole response path (which also imposes PAMPh's fast-
reversing policy rule against the data's persistent rate moves), a system prior on transmission STRENGTH only: after a policy
shock, the CPI y/y trough per pp of the first year's cumulative policy-rate path ~ N(-0.35, 0.10) and the GDP-growth trough per
pp ~ N(-0.20, 0.15). Evidence (outputs/dsge_transmission_benchmarks_20261019_1022.md): PAMPh -0.22, the BSP's 2009 DSGE about
-0.45, the project's local projections -0.50 for inflation; output: PAMPh about -0.19, the BSP 2009 DSGE about -0.2. The rule's
persistence is left to the data. Default prior=pamph (milestone 10's system prior, unchanged).
seed=K start=latest (convergence checks, 19 Oct 2026, about 11:05 AM): skip the mode search; start the chain from an
overdispersed point around the latest posterior of the same model, prior and weight (mean + 2 x its s.d. x noise), with that
posterior's covariance for the proposals and random seed K. Several such chains feed research/dsge/rhat.py.
prior=ratio_cpi (milestone 19c, 20 Oct 2026, about 9:00 AM): the system prior on CPI strength only, N(-0.35, 0.10); output
strength left to the data. Why: soe_htmu's output response to a policy shock is 3-4 times PAMPh's; this run shows how much the
output-strength prior N(-0.20, 0.15) drives it. Outputs carry "_ratiocpi". init=htmu: start the mode search at the converged
soe_htmu posterior (pooled seeds of 2002-2026, STL GDP; milestone 19), for model=htmu.
"""
from __future__ import annotations

import datetime as dt
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import linalg, optimize

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import estimate as E0        # noqa: E402  (kalman_loglik, prior densities)
import estimate_med as EM    # noqa: E402
import klein                 # noqa: E402
import pamph_targets as T    # noqa: E402
import ph_data               # noqa: E402

MODEL = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("model=")), "rot")
PRIOR = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("prior=")), "pamph")
# milestone 18 (19 Oct 2026, about 11:15 PM): sample=long = 2002Q1-2026Q2 with the COVID quarters 2020-2021 missing (ph_data covid="missing");
# default sample=short = 2002Q1-2019Q4, unchanged. Outputs and chains of the long sample carry "_long" in their names.
SAMPLE = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("sample=")), "short")
if SAMPLE not in ("short", "long"):
    raise SystemExit("sample must be short or long")
STAG = "_long" if SAMPLE == "long" else ""
# milestone 18b (19 Oct 2026, about 11:35 PM): gdp=stl = GDP seasonally adjusted by STL before taking growth (ph_data gdp_sa);
# default gdp=raw = fixed quarter means removed, unchanged. Outputs and chains of gdp=stl carry "_stl" in their names.
GDP_SA = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("gdp=")), "raw")
if GDP_SA not in ("raw", "stl"):
    raise SystemExit("gdp must be raw or stl")
STAG += "_stl" if GDP_SA == "stl" else ""
# end= (21 Oct 2026, the pseudo-out-of-sample check, forecast_check.py): the estimation sample ends at this quarter instead of
# the sample's own end (e.g. end=2023Q4 with sample=long: 2002Q1-2023Q4, COVID missing). Outputs and chains carry "_to<end>".
END = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("end=")), None)
if END is not None:
    STAG += f"_to{END}"
# obs=inv (milestone 23c, 21 Oct 2026, night; model=htmk only): PSA real investment growth (ph_data.observables_inv) as a fifth
# observable with an estimated measurement error me_inv (% a quarter). Why: soe_htmk's investment curvature phi_i (7.1 on three
# chains) and the theta it implies for the DSGE-CGE link (htmk_theta.py: about 0.8, against the link's 1.9-3.3) were identified
# without any investment data, only through GDP, inflation, the policy rate and the peso. GFCF growth is about five times as
# volatile as GDP growth (public construction, lumpy projects), hence the measurement error; the data then inform phi_i through
# investment's comovement with the rate and output. Outputs and chains carry "_inv"; without obs=inv nothing changes.
OBS_INV = any(a == "obs=inv" for a in sys.argv[1:])
if OBS_INV:
    if MODEL not in ("htmk", "htmki"):
        raise SystemExit("obs=inv needs model=htmk or model=htmki")
    STAG += "_inv"
RATIO_PRIOR = {"infl": (-0.35, 0.10), "growth": (-0.20, 0.15),       # trough per pp of first-year tightening: mean, s.d.
               "persist": (3.0, 2.0)}                                 # ratio2 only: first-year cumulative rate path per pp of impact
if PRIOR not in ("pamph", "ratio", "ratio_cpi", "ratio2"):
    raise SystemExit("prior must be pamph, ratio, ratio_cpi or ratio2")
# prior=ratio2 (21 Oct 2026, overnight): prior=ratio plus a loose prior on the SCALE of the rate path, the first
# year's cumulative policy-rate response per pp of impact, "persist" ~ N(3.0, 2.0). Why: the transmission ratio (trough per pp of
# cumulative path) is scale-free, so it is also matched where both the trough and the cumulative path are absurd. The SMC check
# found such a region: at Calvo 0.80 the chains' candidate has a policy shock whose rate path runs 0.8, 8.7, 17, 24, 27, 29 pp
# (cumulative 62 times the impact; the particles' median 87) with a CPI trough of -17 pp, and the ratio prior is satisfied there
# at -0.35; between that region and the chains' mode (cumulative 4.9 times the impact, a sensible path) the cumulative passes
# through zero and the penalty reaches -115,000 log points, so the posterior is split in two (research/dsge/README.md, 21 Oct).
# Benchmarks for the scale: PAMPh's own path 1.35 (it reverses within the year), a pure AR(1) at the estimated smoothing 0.95
# about 3.7, the chains' mode 4.9; N(3, 2) leaves all three within a standard deviation and excludes the artefact. NOT YET RUN.
RATIO_PRIORS = ("ratio", "ratio_cpi", "ratio2")
RATIO_KEYS = ("infl",) if PRIOR == "ratio_cpi" else (("infl", "growth", "persist") if PRIOR == "ratio2" else ("infl", "growth"))
PTAG = {"ratio": "_ratio", "ratio_cpi": "_ratiocpi", "ratio2": "_ratio2"}.get(PRIOR, "")
if MODEL == "htm":
    import soe_htm as R      # noqa: E402
elif MODEL == "oil":         # milestone 16 (19 Oct 2026): soe_oil.py, Dubai crude as a fifth observable
    import soe_oil as R      # noqa: E402
elif MODEL == "htmu":        # milestone 19 (20 Oct 2026): soe_htmu.py, soe_htm plus a domestic cost-push (markup) shock
    import soe_htmu as R     # noqa: E402
elif MODEL == "oilu":        # milestone 19b (20 Oct 2026): soe_oilu.py, the oil model plus the cost-push shock
    import soe_oilu as R     # noqa: E402
elif MODEL == "oilw":        # milestone 21 (20 Oct 2026): soe_oilw.py, oil supply and world oil demand (chi_o), G3 GDP observed
    import soe_oilw as R     # noqa: E402
elif MODEL == "oilf":        # milestone 22 (21 Oct 2026): soe_oilf.py, soe_oilw plus flexible-price energy-intensive services in the CPI
    import soe_oilf as R     # noqa: E402
elif MODEL == "htmk":        # milestone 23 (21 Oct 2026): soe_htmk.py, the candidate plus capital and investment adjustment costs
    import soe_htmk as R     # noqa: E402
elif MODEL == "htmki":       # milestone 24 (22 Oct 2026): soe_htmki.py, soe_htmk plus an investment-specific (MEI) shock
    import soe_htmki as R    # noqa: E402
else:
    import soe_rot as R      # noqa: E402
OILM = ("oil", "oilu", "oilw", "oilf")                               # the oil models

EST = [e for e in EM.EST if e[0] not in ("gH", "gF")]
i_after = [e[0] for e in EST].index("hab") + 1
EST[i_after:i_after] = [("omega_H", "beta", 0.40, 0.20, 0.0, 0.95), ("omega_F", "beta", 0.40, 0.20, 0.0, 0.95)]
if MODEL in ("htm", "htmu", "htmk", "htmki") + OILM:
    EST[i_after + 2:i_after + 2] = [("lam_h", "beta", 0.30, 0.15, 0.0, 0.90), ("kappa", "beta", 0.30, 0.15, 0.0, 0.90)]
SHOCKS = list(EM.SHOCKS)
FIXED = {}
if MODEL in ("htmk", "htmki"):
    # milestone 23 (21 Oct 2026): capital and investment. phi_i (adjustment-cost curvature) with Smets and Wouters' prior; the
    # shares calibrated (soe_htmk.py's docstring: Infinity GEM's own SAM v0.5 gives capital 0.60 of value added incl. mixed income, so 0.5;
    # investment 0.24 of household consumption plus investment; depreciation 2.5% a quarter)
    EST.insert(i_after + 4, ("phi_i", "normal", 4.0, 1.5, 0.5, 15.0))
    EST.insert(i_after + 5, ("psi_u", "beta", 0.50, 0.15, 0.05, 0.95))      # utilisation-cost elasticity, Smets-Wouters' prior
    FIXED = dict(alpha_k=0.5, i_y=0.24, delta=0.025)
if MODEL in ("htmu", "htmk", "htmki", "oilu", "oilw", "oilf"):  # milestone 19: the cost-push shock's persistence and size (quarterly inflation, %; as sd_v)
    EST.insert([e[0] for e in EST].index("rho_z") + 1, ("rho_u", "beta", 0.50, 0.20, 0.0, 0.99))
    EST.append(("sd_u", "invgamma", 0.25, 1.0, 1e-3, 10.0))
    SHOCKS.append("u")
if MODEL == "htmki":
    # milestone 24 (22 Oct 2026): the investment-specific (MEI) shock's persistence and size (% a quarter), with the same loose
    # priors as the other shocks; it enters the investment Euler equation with unit weight (Smets and Wouters 2007, eq. 3)
    EST.insert([e[0] for e in EST].index("rho_u") + 1, ("rho_ei", "beta", 0.50, 0.20, 0.0, 0.99))
    EST.append(("sd_ei", "invgamma", 0.5, 1.0, 1e-3, 10.0))
    SHOCKS.append("ei")
if MODEL in OILM:
    # calibrated, not estimated: oil's direct CPI weight 0.037 (PSA 2018-based weights: LPG 1.27, kerosene 0.04, vehicle fuels
    # 2.39) and its cost share in production 0.030 (refined petroleum's intermediate use over total output, Infinity GEM's own SAM v0.5);
    # low substitution between core goods and oil (0.2; short-run oil demand is inelastic)
    FIXED = dict(a_o=0.037, s_o=0.030, eps_o=0.2)
    EST.insert([e[0] for e in EST].index("rho_z") + 1, ("rho_o", "beta", 0.80, 0.10, 0.0, 0.99))
    EST.append(("sd_o", "invgamma", 12.0, 6.0, 1e-3, 50.0))
    SHOCKS.append("o")
if MODEL == "oilf":
    # milestone 22 (21 Oct 2026): the flexible-price, energy-intensive services in the CPI, calibrated: a_f = PSA 2018 CPI weights of
    # passenger transport services (4.54%) and electricity (4.55%), data/raw/macro/PSA_OpenSTAT_0012M4ACP25_CPI_weights_2018base.csv;
    # s_f = their fuel cost share, CPI-weighted, from Infinity GEM's own SAM v0.5 (transport: refined petroleum 16.1% of cost; electricity:
    # refined petroleum 17.1% plus coal and gas 5.0%, the DSGE's one oil price standing for all fossil fuels): 0.19 (oil only 0.17)
    FIXED = dict(FIXED, a_f=0.091, s_f=0.19)
if MODEL in ("oilw", "oilf"):
    # milestone 21: the oil price's loading on world output (o = o_s + chi_o ystar), positive (world booms raise oil prices);
    # gamma with mean 5 and s.d. 4: a 1% world-output gap moves the real oil price by about 1-13%, the range implied by the
    # comovement of Dubai crude with G3 growth (oil changes s.d. about 15%, G3 growth about 0.6%, correlation 0.2-0.5)
    EST.insert([e[0] for e in EST].index("rho_o") + 1, ("chi_o", "gamma", 5.0, 4.0, 0.0, 40.0))
# the parameters with every one free, before theta_fix= drops the Calvo parameter and obs=inv adds me_inv: the column names of
# init=htmk's source chains (22 Oct 2026, morning: with theta_fix= the old zip over NAMES shifted every column after theta)
NAMES_FREE = [e[0] for e in EST]
# theta_hi= (20 Oct 2026, about 03:25): a higher upper bound for the domestic Calvo parameter (default 0.97). Why: in soe_htmu on
# 2002-2026 (STL GDP) theta sits at 0.954 with its 95th percentile at 0.967, against the bound: a robustness run with 0.99.
THETA_HI = next((float(a.split("=", 1)[1]) for a in sys.argv[1:] if a.startswith("theta_hi=")), None)
if THETA_HI is not None:
    _j = [e[0] for e in EST].index("theta")
    EST[_j] = EST[_j][:5] + (THETA_HI,)
    STAG += f"_thhi{THETA_HI:g}"
# theta_fix= (milestone 21b, 20 Oct 2026, about 10:15 AM): the domestic Calvo parameter CALIBRATED instead of estimated. Why: in the
# cost-push models it is estimated at 0.95 (prices fixed about 5 years; a flat Phillips curve), with which an oil SUPPLY shock
# raises output (fuel costs do not reach domestic prices, so demand switches to home goods). The BSP's micro price data (WPS
# 2020-02, Table 2: all items, a price decrease about every 10 months) give a quarterly Calvo of about (1 - 1/10)**3 = 0.73.
THETA_FIX = next((float(a.split("=", 1)[1]) for a in sys.argv[1:] if a.startswith("theta_fix=")), None)
if THETA_FIX is not None:
    EST = [e for e in EST if e[0] != "theta"]
    FIXED = dict(FIXED, theta=THETA_FIX)
    STAG += f"_thfix{THETA_FIX:g}"
# world= (milestone 21 robustness, 20 Oct 2026): "g3" (default, G3 real GDP growth) or "igrea" (Kilian's index)
WORLD = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("world=")), "g3")
if WORLD != "g3":
    if MODEL not in ("oilw", "oilf"):
        raise SystemExit("world= applies to model=oilw and model=oilf only")
    STAG += f"_{WORLD}"
if OBS_INV:                                                    # milestone 23c: investment's measurement error, % a quarter
    EST.append(("me_inv", "invgamma", 3.0, 2.0, 1e-3, 30.0))
NAMES = [e[0] for e in EST]
TOL = {"growth": 0.02, "infl": 0.02, "rate": 0.05, "fx": 0.05}
TARGET = {"growth": T.GDP_GROWTH_YOY, "infl": T.CPI_INFLATION_YOY, "rate": T.POLICY_RATE_PA, "fx": T.NOMINAL_EXCHANGE_RATE_100LOG}


def prior(theta):
    saved = E0.EST
    try:
        E0.EST = EST
        return E0._prior_logpdf(theta)
    finally:
        E0.EST = saved


def split(theta):
    kw = dict(zip(NAMES, theta))
    kw.pop("me_inv", None)                                     # obs=inv: a measurement error, not a model parameter
    sds = np.array([kw.pop(f"sd_{s}") for s in SHOCKS])
    return kw, sds


def me_kw(theta):
    """kalman_loglik's measurement-error variances: the default 1e-4 for every observable, plus me_inv^2 for investment."""
    if not OBS_INV:
        return {}
    n_obs = {"oil": 5, "oilu": 5, "oilw": 6, "oilf": 6}.get(MODEL, 4) + 1
    me = np.full(n_obs, 1e-4)
    me[-1] = dict(zip(NAMES, theta))["me_inv"] ** 2
    return {"me": me}


def state_space(sol, sds, chi_o=0.0):
    nk = len(R.STATES)
    ixk, ixd = {n: j for j, n in enumerate(R.STATES)}, {n: j for j, n in enumerate(R.JUMPS)}
    Pbig = np.block([[sol.P, np.zeros((nk, nk))], [np.eye(nk), np.zeros((nk, nk))]])
    Rm = np.zeros((nk, len(SHOCKS)))
    for j, s in enumerate(SHOCKS):
        Rm[ixk[s], j] = 1.0
    if chi_o:                                                  # milestone 21: a world-output innovation also moves the oil price
        Rm[ixk["o"], SHOCKS.index("ystar")] = chi_o
    Rbig = np.vstack([Rm, np.zeros((nk, len(SHOCKS)))])
    Q = np.diag((sds / 100.0) ** 2)
    F = sol.F
    H = np.zeros(({"oil": 5, "oilu": 5, "oilw": 6, "oilf": 6}.get(MODEL, 4) + (1 if OBS_INV else 0), 2 * nk))
    if OBS_INV:                                                # milestone 23c: investment growth = inv - inv(-1), the last row
        H[-1, :nk], H[-1, nk:] = F[ixd["inv"]], -F[ixd["inv"]]
    H[0, :nk], H[0, nk:] = F[ixd["y"]], -F[ixd["y"]]
    H[1, :nk], H[2, :nk], H[3, :nk] = F[ixd["pi"]], F[ixd["i"]], F[ixd["de"]]
    if MODEL in OILM:                                          # Dubai crude in dollars: o - o_lag + pistar (states at t)
        H[4, ixk["o"]], H[4, ixk["o_lag"]], H[4, ixk["pistar"]] = 1.0, -1.0, 1.0
    if MODEL in ("oilw", "oilf"):                              # milestone 21: world output growth = ystar - ystar_lag
        H[5, ixk["ystar"]], H[5, ixk["ystar_lag"]] = 1.0, -1.0
    return Pbig, Rbig, Q, 100.0 * H


def observables():
    """The estimation data: four series, plus Dubai crude for model=oil (ph_data.observables_oil)."""
    kw = dict(end=ph_data.LONG_END, covid="missing") if SAMPLE == "long" else {}
    if END is not None:
        kw["end"] = END
    if GDP_SA == "stl":
        kw["gdp_sa"] = "stl"
    if MODEL in ("oilw", "oilf"):
        return ph_data.observables_oilw(world=WORLD, **kw)[E0.OBS + ["doil", "dystar"]].to_numpy()
    if MODEL in ("oil", "oilu"):
        return ph_data.observables_oil(**kw)[E0.OBS + ["doil"]].to_numpy()
    if OBS_INV:                                                # milestone 23c: investment growth as the fifth observable
        return ph_data.observables_inv(**kw)[E0.OBS + ["dinv"]].to_numpy()
    return ph_data.observables(**kw)[E0.OBS].to_numpy()


def pamph_responses(sol, T_=21):
    """irf_match.model_irf from an already solved model: a policy shock scaled to +0.80 pp (annualized) on impact."""
    ixk = {n: j for j, n in enumerate(R.STATES)}
    ixd = {n: j for j, n in enumerate(R.JUMPS)}
    e = np.zeros(len(R.STATES)); e[ixk["v"]] = 0.001
    k, d = sol.irf(np.eye(len(R.STATES)), e, T=T_)
    i_, y_, pi_, de_ = d[:, ixd["i"]], d[:, ixd["y"]], d[:, ixd["pi"]], d[:, ixd["de"]]
    s = 0.80 / (400 * i_[0])
    y = 100 * s * np.concatenate([[0.0], y_])
    pi = 100 * s * np.concatenate([[0.0], pi_])
    de = 100 * s * np.concatenate([[0.0], de_])
    out = {"growth": {}, "infl": {}, "rate": {}, "fx": {}}
    for q in T.QUARTERS:
        out["growth"][q] = y[q] - (y[q - 4] if q >= 4 else 0.0)
        out["infl"][q] = pi[max(q - 3, 0):q + 1].sum()
        out["rate"][q] = 400 * s * i_[q - 1]
        out["fx"][q] = de[1:q + 1].sum()
    return out


def distance(resp):
    return sum(((resp[k][q] - TARGET[k][q]) / TOL[k]) ** 2 for k in TARGET for q in T.QUARTERS)


def strength(resp):
    """Troughs of CPI y/y inflation and GDP y/y growth per pp of the first year's cumulative policy-rate path."""
    cum = sum(resp["rate"][q] for q in (1, 2, 3, 4))
    return {"infl": min(resp["infl"].values()) / cum, "growth": min(resp["growth"].values()) / cum,
            "persist": cum / resp["rate"][1]}                   # ratio2: the scale of the rate path itself


def ratio_distance(resp):
    s = strength(resp)
    return sum(((s[k] - m) / sd) ** 2 for k, (m, sd) in RATIO_PRIOR.items() if k in RATIO_KEYS)


def pieces(theta, Z):
    """(log prior, log likelihood, PAMPh distance, strength distance, strength) or None if outside the prior or indeterminate."""
    lp = prior(theta)
    if not np.isfinite(lp):
        return None
    kw, sds = split(theta)
    try:
        sol, _ = R.solve(R.Params(rule="output", **{**kw, **FIXED}))
        ll = E0.kalman_loglik(*state_space(sol, sds, kw.get("chi_o", 0.0)), Z, **me_kw(theta))
        resp = pamph_responses(sol)
        dist, rdist, st = distance(resp), ratio_distance(resp), strength(resp)
    except (klein.BlanchardKahnError, linalg.LinAlgError, ValueError, ZeroDivisionError):
        return None
    return lp, ll, dist, rdist, st


def log_post(theta, Z, w):
    p = pieces(theta, Z)
    if p is None:
        return -np.inf
    return p[0] + p[1] - 0.5 * w * (p[3] if PRIOR in RATIO_PRIORS else p[2])


def main():
    n = int(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("n=")), 20000))
    w = float(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("w=")), 1.0))
    seed = int(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("seed=")), 11))
    # start=pooled (20 Oct 2026, about 01:35): as start=latest, but the start and the proposal covariance come from every saved
    # chain of the same specification (the first run and its seeds), not only the first run: a first run that mixed badly
    # (2002-2026, STL GDP: acceptance 0.06) gives too narrow a covariance and the seeds then move slowly (R-hat 1.56)
    from_pooled = any(a == "start=pooled" for a in sys.argv[1:])
    from_latest = from_pooled or any(a == "start=latest" for a in sys.argv[1:])
    t0 = time.time()
    Z = observables()
    rng = np.random.default_rng(seed)
    x_init = None
    if from_latest:                                            # convergence check: no mode search; overdispersed start
        ptag = f"_w{w:g}" + PTAG + STAG
        allf = sorted((HERE.parents[1] / "outputs").glob(f"dsge_ph_{MODEL}_draws_*{ptag}*.npy"))
        if from_pooled:
            import re
            prev = [f for f in allf if re.search(re.escape(ptag) + r"(_seed\d+)?$", f.stem)]
            Dp = np.vstack([np.load(f) for f in prev])
            print(f"pooled start from {len(prev)} chains: {', '.join(f.name for f in prev)}", flush=True)
        else:
            prev = [f for f in allf if f.stem.endswith(ptag)]
            Dp = np.load(prev[-1])
        m = Dp.mean(0)
        scale = (2.38 ** 2 / len(m)) * np.cov(Dp.T) + 1e-10 * np.eye(len(m))
        for _ in range(200):
            cand = m + 2.0 * Dp.std(0) * rng.standard_normal(len(m))
            if np.isfinite(log_post(cand, Z, w)):
                x_init = cand
                break
        x_init = m.copy() if x_init is None else x_init
    else:
        x0 = np.array([e[2] for e in EST])
        if any(a == "init=htm" for a in sys.argv[1:]):        # model=oil: start the mode search at milestone 13's posterior
            from transmission_benchmarks import HTM_NAMES
            prev = sorted((HERE.parents[1] / "outputs").glob("dsge_ph_htm_draws_*_w1_ratio_seed*.npy"))
            mh = dict(zip(HTM_NAMES, np.mean([np.load(f).mean(0) for f in prev], axis=0)))
            x0 = np.array([mh.get(e[0], e[2]) for e in EST])
        if any(a == "init=oilu" for a in sys.argv[1:]):       # milestone 21: start at the converged soe_oilu posterior
            prev = sorted((HERE.parents[1] / "outputs").glob("dsge_ph_oilu_draws_*_w1_ratio_long_stl_seed*.npy"))
            if MODEL != "oilw" or not prev:
                raise SystemExit("init=oilu needs model=oilw and the converged soe_oilu chains")
            mo = dict(zip([n for n in NAMES if n != "chi_o"], np.vstack([np.load(f) for f in prev]).mean(0)))
            x0 = np.array([mo.get(e[0], e[2]) for e in EST])
        if any(a == "init=oilw" for a in sys.argv[1:]):       # milestone 22 (21 Oct 2026): start at the converged soe_oilw posterior
            import re                                          # (theta estimated; the first run and its seeds; not thfix/igrea)
            prev = [f for f in sorted((HERE.parents[1] / "outputs").glob("dsge_ph_oilw_draws_*_w1_ratio_long_stl*.npy"))
                    if re.search(r"_w1_ratio_long_stl(_seed\d+)?$", f.stem)]
            if MODEL != "oilf" or not prev:
                raise SystemExit("init=oilw needs model=oilf and the converged soe_oilw chains")
            mo = dict(zip(NAMES, np.vstack([np.load(f) for f in prev]).mean(0)))
            x0 = np.array([mo.get(e[0], e[2]) for e in EST])
        if any(a == "init=htmu" for a in sys.argv[1:]):       # milestone 19c: start at the converged soe_htmu posterior
            prev = sorted((HERE.parents[1] / "outputs").glob("dsge_ph_htmu_draws_*_w1_ratio_long_stl_seed*.npy"))
            if MODEL not in ("htmu", "htmk") or not prev:
                raise SystemExit("init=htmu needs model=htmu or model=htmk and the converged soe_htmu chains")
            mu = np.vstack([np.load(f) for f in prev]).mean(0)
            if MODEL == "htmu":
                x0 = mu
            else:                                              # milestone 23 (21 Oct 2026, morning): soe_htmk carries soe_htmu's
                mh = dict(zip([nm for nm in NAMES if nm not in ("phi_i", "psi_u")], mu))   # parameters in the same order, plus
                x0 = np.array([mh.get(e[0], e[2]) for e in EST])                            # phi_i and psi_u at their prior means
        if any(a == "init=htmk" for a in sys.argv[1:]):       # milestone 23c (21 Oct 2026, night): obs=inv starts at the parameters'
            import re                                          # pooled MEDIAN of soe_htmk's three ratio2 chains (without
            prev = [f for f in sorted((HERE.parents[1] / "outputs").glob("dsge_ph_htmk_draws_*_w1_ratio2_long_stl*.npy"))
                    if re.search(r"_w1_ratio2_long_stl(_seed\d+)?$", f.stem)]          # investment data); me_inv at its prior
            if MODEL != "htmk" or not OBS_INV or not prev:     # mean. The median, not the mean: at the mean the rate path
                raise SystemExit("init=htmk needs model=htmk obs=inv and soe_htmk's ratio2 chains")   # reverses (strength -0.73)
            mk = dict(zip(NAMES_FREE, np.median(np.vstack([np.load(f) for f in prev]), 0)))
            x0 = np.array([mk.get(e[0], e[2]) for e in EST])
        best = None
        for start in (x0, 0.5 * (x0 + np.array([max(e[4], min(e[5], e[2] * 1.2)) for e in EST]))):
            x = start
            for _ in range(2):
                res = optimize.minimize(lambda t: -log_post(t, Z, w), x, method="Nelder-Mead",
                                        options=dict(maxiter=15000, xatol=1e-5, fatol=1e-6, adaptive=True))
                x = res.x
            best = res if best is None or res.fun < best.fun else best
        m = best.x
        scale = np.diag((0.12 * np.minimum([e[3] for e in EST], np.maximum(np.abs(m), 0.05))) ** 2)
    for it in range(4):
        Lc = np.linalg.cholesky(scale)
        start_x = x_init if (x_init is not None and it == 0) else m
        x, lx, draws, acc = start_x.copy(), log_post(start_x, Z, w), np.empty((n, len(m))), 0
        for t in range(n):
            y = x + Lc @ rng.standard_normal(len(x))
            ly = log_post(y, Z, w)
            if np.log(rng.uniform()) < ly - lx:
                x, lx, acc = y, ly, acc + 1
            draws[t] = x
        acc /= n
        if 0.2 < acc < 0.4 or it == 3:
            break
        scale = (2.38 ** 2 / len(m)) * np.cov(draws[n // 4:].T) * (0.6 if acc < 0.2 else 1.4) + 1e-10 * np.eye(len(m))
    d = draws[n // 4:]
    lo, hi = np.array([e[4] for e in EST]), np.array([e[5] for e in EST])
    near = (np.abs(d.mean(0) - lo) < 0.02 * (hi - lo)) | (np.abs(d.mean(0) - hi) < 0.02 * (hi - lo))
    tab = pd.DataFrame({"prior": [f"{e[1]} ({e[2]}, {e[3]})" for e in EST], "mode": m, "mean": d.mean(0),
                        "5%": np.percentile(d, 5, 0), "95%": np.percentile(d, 95, 0),
                        "at a bound?": np.where(near, "YES", "")}, index=NAMES)
    pm = pieces(d.mean(0), Z)
    pmode = pieces(m, Z)
    kw, sds = split(d.mean(0))
    sol, _ = R.solve(R.Params(rule="output", **{**kw, **FIXED}))
    resp = pamph_responses(sol)
    rows = []
    for k, lab in (("rate", "policy rate (pp p.a.)"), ("growth", "GDP growth (pp y/y)"), ("infl", "CPI inflation (pp y/y)"),
                   ("fx", "nominal exchange rate (100 log)")):
        rows.append({"variable": lab, "source": "PAMPh", **{f"q{q}": TARGET[k][q] for q in T.QUARTERS}})
        rows.append({"variable": lab, "source": f"soe_{MODEL} (posterior mean)", **{f"q{q}": resp[k][q] for q in T.QUARTERS}})
    rtab = pd.DataFrame(rows).set_index(["variable", "source"])
    p = R.Params(rule="output", **{**kw, **FIXED})
    gb, gf, lam = p.gg(p.theta, p.omega_H)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    outd = HERE.parents[1] / "outputs"
    tag = f"_w{w:g}" + PTAG + STAG + (f"_seed{seed}" if from_latest else "")
    np.save(outd / f"dsge_ph_{MODEL}_draws_{stamp}{tag}.npy", d)
    which = ({"ratio": "a system prior on transmission strength", "ratio_cpi": "a system prior on CPI transmission strength only",
              "ratio2": "a system prior on transmission strength plus a loose prior on the rate path's scale"}
             .get(PRIOR, "PAMPh as a system prior")) if w else "data only"
    L = [f"# DSGE research, milestone {10 if MODEL == 'rot' else 11}{', 13' if PRIOR == 'ratio' else ''}: soe_{MODEL}, "
         f"estimated on Philippine data, {which} ({dt.datetime.now():%d %B %Y, %H:%M})", "",
         f"**NOT FOR CITATION** (research code, Infinity GEM 0.3.11 `research/dsge/`). Model `soe_{MODEL}.py` (Gali-Gertler price "
         f"setters, habits, risk premium, Lubik-Schorfheide rule{'; hand-to-mouth households, partly adaptive expectations' if MODEL == 'htm' else ''}); data `ph_data.py` ({'2002Q1-2026Q2, the COVID quarters 2020Q1-2021Q4 missing (milestone 18)' if SAMPLE == 'long' else '2002Q1-2019Q4'}{'; GDP seasonally adjusted by STL (milestone 18b)' if GDP_SA == 'stl' else ''}); system-prior weight "
         f"w = {w:g}. Random-walk Metropolis {n:,} draws, 25% burn-in, acceptance {acc:.2f}; {time.time() - t0:.0f} s.", "",
         f"- At the mode: log prior {pmode[0]:.1f}, log likelihood {pmode[1]:.1f}, distance to PAMPh {pmode[2]:.1f}.",
         f"- At the posterior mean: log likelihood {pm[1]:.1f}, distance to PAMPh {pm[2]:.1f} "
         "(milestone 7's soe_med match: 60, with parameters at bounds; the QPM: 60).",
         f"- Transmission strength at the posterior mean (trough per pp of first-year tightening): CPI y/y {pm[4]['infl']:.2f}, "
         f"GDP growth {pm[4]['growth']:.2f} (system prior on strength: "
         f"{'N(-0.35, 0.10) on CPI only' if PRIOR == 'ratio_cpi' else 'N(-0.35, 0.10) and N(-0.20, 0.15)'}; evidence -0.22 to "
         "-0.50 for inflation).",
         f"- Domestic Phillips curve at the posterior mean: gamma_b {gb:.2f}, gamma_f {gf:.2f}, slope {lam:.3f}.",
         f"- Parameters at a bound of their prior range: {', '.join(np.array(NAMES)[near]) or 'none'}.", "",
         "## Posterior", "", tab.to_markdown(floatfmt=".3f"), "",
         "## Monetary-policy responses against PAMPh (quarter after the shock)", "", rtab.to_markdown(floatfmt=".2f")]
    (outd / f"dsge_ph_{MODEL}_estimation_{stamp}{tag}.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
