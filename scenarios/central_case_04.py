"""Infinity GEM 0.4 (0.4.0, 13 Nov 2026): the central 2026 case under the setting "0.4 recommended" (option (c) of the
short-run calibration at the T15 point on the own SAM v1.0, margin floor -1, the PAMPh-type BSP rule at theta 1.5;
infinity_gem/settings.py OPTION_C_04) against the same case under "0.3 recommended" as it ran on SAM v1.0 before 13 Nov 2026
(paid labour hoarding 0.85, the wage curve of the latest calibration on that SAM: scenarios/calibrate_wage_curve.py).
NOT FOR CITATION until reviewed.

The case: scenarios/combined_revised.Runs, public capital low, the four shocks (public works, oil, El Nino, world rice and
fertilizer) against the no-shock path with the same policies (the 2026-27 rice tariff, the 2027 NEP aid cut); public works alone
for the multiplier. Under 0.4 the BSP rule reacts to each path's gaps against the no-shock path (settings.BSP_RULE_REFERENCE).
headline() is what checks R4, R41, R42 and R41F recompute and compare with their reference results (those standalone tests and
reference files are not in this repository: docs/STATUS.md). The case counts the new poor with PSA's FIES microdata, which you
download yourself (data/raw/fies/README.md).

Run (from the repository folder; one model process; up to an hour):
  python -X utf8 scenarios/central_case_04.py compare        old (0.3) and new (0.4), table to outputs/
  python -X utf8 scenarios/central_case_04.py verify oil=tracker [ref=baseline|no-shock path]   0.4 on the oil series of the
                                                       fits of 12 Nov 2026 (in this repository "tracker" reads public World Bank
                                                       and EIA series instead); ref=baseline (default): the rule read against the
                                                       baseline in every path (the fits' convention)
  python -X utf8 scenarios/central_case_04.py ref041         "0.4.1 recommended" (the default since 13 Nov 2026) beside "0.4 recommended"
  python -X utf8 -u scenarios/central_case_04.py accelerator [variants=off,central,lo,hi,gdp,gdplo,gdphi] [tag=..]   "0.4.1
                                                       recommended" with the opt-in private-investment accelerator (check ACC1)
  python -X utf8 -u scenarios/central_case_04.py cand042 [tag=..]   the opt-in setting "0.4.2 candidate" beside "0.4.1
                                                       recommended" (it needs a saved re-fit result that is not in this repository)
  python -X utf8 -u scenarios/central_case_04.py ref041F     the 0.4.1 case on the default FIES base (FIES 2025), beside the
                                                       FIES 2023 reference checks/reference_041_central.json (not in this repository)
  save_reference=1 (with compare, ref041, cand042 or ref041F) writes a reference file of your own in checks/.
FIES base (18 Nov 2026): new poor and the PSA-weight inflation rows are on _common.FIES_BASE (INFINITY_GEM_FIES_BASE, else the
default, FIES 2025). A reference file on FIES 2023 is refused unless INFINITY_GEM_FIES_BASE=fies2023.
Outputs: outputs/central_case_04_<YYYYMMDD_HHMM>_<mode>.csv and .md.
"""
import gc
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
os.environ["INFINITY_GEM_SCENARIO_SAM"] = "own"            # Infinity GEM's own SAM v1.0 (the only SAM "0.4 recommended" is defined on)
os.environ["INFINITY_GEM_SCENARIO_ENGINE"] = ""             # nothing added: each case names its own engine settings below
os.environ.pop("INFINITY_GEM_SCENARIO_PESO", None)          # the peso basis of 12 Nov 2026 ("year"; not used by the measures here)
# the oil series: the default (public MBIE since 12 Nov 2026, 10 PM) unless oil=<source> is given (verify oil=tracker: the series the short-run fits of 12 Nov 2026 ran on); read by preshock/shock_paths.py at import
_OIL = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("oil=")), None)
if _OIL:
    os.environ["INFINITY_GEM_OIL_SOURCE"] = _OIL
else:
    os.environ.pop("INFINITY_GEM_OIL_SOURCE", None)
for p in (str(ROOT), str(HERE), str(ROOT / "preshock")):
    if p not in sys.path:
        sys.path.insert(0, p)
import numpy as np                                                              # noqa: E402
import pandas as pd                                                             # noqa: E402

import _common                                                                  # noqa: E402
import combined_revised as CR                                                   # noqa: E402
from infinity_gem import paths, psa_cpi, settings                                   # noqa: E402

REF_FILE = ROOT / "checks" / "reference_04_central.json"
REF_FILE_041 = ROOT / "checks" / "reference_041_central.json"   # 13 Nov 2026 (check R41)
REF_FILE_042C = ROOT / "checks" / "reference_042c_central.json"  # 15 Nov 2026 (opt-in "0.4.2 candidate"; check R42)
REF_FILE_041F = ROOT / "checks" / "reference_041F_central.json"  # 18 Nov 2026 (FIES 2025 the default base; check R41F)
PESO_KEY = "peso 1% weaker in 2026 alone: consumer prices 2026, PSA weights (%)"
T15_JSON = paths.output_dir() / "row83_refit_v10_2026_20261112_1236_point_T15params.json"
FLOOR_CSV = paths.output_dir() / "row83_refit_v10_2026_20261112_1511_point_T15params_floor-1.csv"
HEADLINE = ("GDP gap 2026 (%)", "GDP gap 2027 (%)", "growth effect 2026 (pp)", "inflation 2026, PSA weights (pp)",
            "policy-rate gap 2026 (pp)", "policy-rate gap 2027 (pp)", "new poor 2026 (M)", "new poor 2027 (M)",
            "public-works multiplier 2026")


def beta_v10() -> float:
    """The wage-curve beta of Infinity GEM's own SAM v1.0 (scenarios/calibrate_wage_curve.py), the central 2026 setting before 13 Nov 2026."""
    return float(pd.read_csv(_common.calibration_file(), index_col=0).loc["central (e)", "beta"])


def runs(setting: str, rule_reference=None):
    """The central 2026 model under a setting: 0.4 as the setting defines it; 0.3 as the 2026 scenarios ran it on v1.0 (hoarding 0.85, beta)."""
    if setting in settings.OPTION_C_SETTINGS:      # 13 Nov 2026: 0.4.1 as 0.4 (was == "0.4 ...")
        return CR.Runs("low", setting=setting, rule_reference=rule_reference)
    return CR.Runs("low", setting=setting, wage_curve=beta_v10(), hoarding=0.85)


def _agg(m, sol):
    return {"C": float(np.sum(sol["QH"])), "I": float(np.sum(sol["QINV"]) + np.sum(m.qdst))}


def _jobs(m, b, s):
    """All jobs at base wages, hoarded workers included (scenarios/industry_pattern_vs_data.model_pattern's total)."""
    labs = [i for i, f in enumerate(m.F) if f.startswith("flab")]
    emp = lambda sol: np.asarray(sol["QF"], float)[labs] + (np.asarray(sol["QFH"], float)[labs] if "QFH" in sol else 0.0)
    W0 = np.asarray(b["W"], float)[labs]
    return float(((W0 * emp(s)).sum() / (W0 * emp(b)).sum() - 1) * 100)


def headline(R, log=print, keep=None) -> dict:
    """The central case's numbers, each against the no-shock path: four shocks (GDP, growth effect, inflation on PSA weights, the
    policy-rate gap, jobs, consumption, investment, new poor on the FIES 2023 base) and the public-works multiplier.
    keep (14 Nov 2026): a dict that receives the three paths (clean, sim, pw); None = as before."""
    piece, src = R.pieces()
    m = R.d.ms
    t0 = time.time()
    clean = R.run(set(), piece=piece)
    log(f"  no-shock path: {time.time() - t0:.0f} s")
    t0 = time.time()
    sim = R.run(set(CR.SHOCKS), piece=piece)
    log(f"  four shocks: {time.time() - t0:.0f} s")
    t0 = time.time()
    pw = R.run({"public works"}, piece=piece)
    log(f"  public works alone: {time.time() - t0:.0f} s")
    gap = lambda p, y: float(p.table.real_gdp[y] / clean.table.real_gdp[y] - 1) * 100
    ge = lambda a, b: ((1 + a / 100) / (1 + b / 100) - 1) * 100
    pc = lambda p, y: psa_cpi.change(R.ml.link_variables(m, clean.solutions[y], p.solutions[y]))["all households"]
    cut_pct = -float(src["public works"]["2026 central"]) / CR.PSA_GDP[2026] * 100
    out = {"GDP gap 2025 (%)": gap(sim, 2025), "GDP gap 2026 (%)": gap(sim, 2026), "GDP gap 2027 (%)": gap(sim, 2027)}
    out["growth effect 2026 (pp)"] = ge(out["GDP gap 2026 (%)"], out["GDP gap 2025 (%)"])
    out["inflation 2026, PSA weights (pp)"] = ge(pc(sim, 2026), pc(sim, 2025))
    out["consumer prices 2026, PSA weights (%)"] = pc(sim, 2026)
    out["inflation 2026, SAM CPI (pp)"] = ge(float(sim.table.cpi[2026] / clean.table.cpi[2026] - 1) * 100,
                                             float(sim.table.cpi[2025] / clean.table.cpi[2025] - 1) * 100)
    mo = sim.monetary
    for y in (2026, 2027):
        out[f"policy-rate gap {y} (pp)"] = float(mo.loc[y, "policy_rate_gap_pp"]) if mo is not None else 0.0
        out[f"real-rate gap {y} (pp)"] = float(mo.loc[y, "real_rate_gap_pp"]) if mo is not None else 0.0
    out["BSP rule: iterations, converged"] = "-" if mo is None else f"{mo.attrs.get('iterations')}, {mo.attrs.get('converged')}"
    b26, s26 = clean.solutions[2026], sim.solutions[2026]
    out["jobs 2026 (%)"] = _jobs(m, b26, s26)
    out["employment gap 2026, low skill (pp of labour supply)"] = float(sim.table.employment_gap_low_skill_pct[2026]
                                                                        - clean.table.employment_gap_low_skill_pct[2026])
    a0, a1 = _agg(m, b26), _agg(m, s26)
    out["household consumption 2026 (%)"] = (a1["C"] / a0["C"] - 1) * 100
    out["investment 2026 (%)"] = (a1["I"] / a0["I"] - 1) * 100
    for y in (2026, 2027):
        out[f"new poor {y} (M)"] = R.poor(clean, sim, y)[0] / 1e6
    out["public-works multiplier 2026"] = -gap(pw, 2026) / cut_pct
    fb = sorted(getattr(R.d, "cap_fallback_years", set()))
    out["employment-cap fallback years (EF1)"] = ", ".join(map(str, fb)) or "none"
    if keep is not None:
        keep.update(clean=clean, sim=sim, pw=pw)
    return out


# 14 Nov 2026: the opt-in accelerator's variants (DynamicCGE sr_accelerator), from
# outputs/accelerator_estimate_20261113_2351.md (preshock/accelerator_estimate.py): "demand" = QCX, private investment's y/y growth on
# household + government consumption + exports lagged one quarter, 1.323 (s.e. 0.481); "gdp" = the 12 Nov main equation's coefficient
# on GDP lagged one quarter, 2.937 (s.e. 0.839), reproduced. lag 0.25 = the one-quarter lag read annually (module notes of dynamic.py).
ACC_A = {"demand": (1.323, 0.481), "gdp": (2.937, 0.839)}
ACC_VARIANTS = {
    "off": None,
    "central": {"a": ACC_A["demand"][0], "lag": 0.25, "driver": "demand"},
    "lo": {"a": ACC_A["demand"][0] - ACC_A["demand"][1], "lag": 0.25, "driver": "demand"},
    "hi": {"a": ACC_A["demand"][0] + ACC_A["demand"][1], "lag": 0.25, "driver": "demand"},
    "gdp": {"a": ACC_A["gdp"][0], "lag": 0.25, "driver": "gdp"},
    "gdplo": {"a": ACC_A["gdp"][0] - ACC_A["gdp"][1], "lag": 0.25, "driver": "gdp"},
    "gdphi": {"a": ACC_A["gdp"][0] + ACC_A["gdp"][1], "lag": 0.25, "driver": "gdp"},
}


def headline_acc(R, acc, log=print) -> dict:
    """14 Nov 2026: headline() with the accelerator `acc` (None = off) and the investment detail: total investment 2025 and
    2026 against the no-shock path, its growth effect 2026, PRIVATE investment (the part the accelerator moves: its gap = the BSP
    rule's investment scale x the accelerator's scale - 1, the model's private investment being otherwise on the no-shock path) and
    the accelerator's own table."""
    R.d.a["sr_accelerator"] = acc
    try:
        kp = {}
        out = headline(R, log, keep=kp)
    finally:
        R.d.a["sr_accelerator"] = None
    clean, sim = kp["clean"], kp["sim"]
    m = R.d.ms
    ig = {y: (_agg(m, sim.solutions[y])["I"] / _agg(m, clean.solutions[y])["I"] - 1) * 100 for y in (2025, 2026, 2027)}
    for y in (2025, 2026, 2027):
        out[f"investment {y} (%)"] = ig[y]
    out["investment growth effect 2025 (pp)"] = ig[2025]
    out["investment growth effect 2026 (pp)"] = ((1 + ig[2026] / 100) / (1 + ig[2025] / 100) - 1) * 100
    mo, ac = sim.monetary, getattr(sim, "accelerator", None)
    for y in (2025, 2026, 2027):
        ms_ = float(mo.loc[y, "investment_scale"]) if mo is not None and y in mo.index else 1.0
        as_ = float(ac.loc[y, "accelerator_scale"]) if ac is not None and y in ac.index else 1.0
        out[f"private investment {y} (%)"] = (ms_ * as_ - 1) * 100
        out[f"accelerator scale {y}"] = as_
        out[f"accelerator driver gap {y} (%)"] = float(ac.loc[y, "accelerator_driver_gap_pct"]) if ac is not None and y in ac.index else 0.0
    out["accelerator"] = "off" if acc is None else ", ".join(f"{k} {v}" for k, v in acc.items())
    out["accelerator: iterations, converged"] = "-" if ac is None else f"{ac.attrs.get('iterations')}, {ac.attrs.get('converged')}"
    pw = kp["pw"]
    pa = getattr(pw, "accelerator", None)
    out["public works alone: accelerator scale 2026"] = float(pa.loc[2026, "accelerator_scale"]) if pa is not None else 1.0
    return out


def peso_alone(R, log=print) -> dict:
    """15 Nov 2026 (the "0.4.2 candidate"): the peso 1% weaker in 2026 alone (exr_scale 1 + 1/100, as
    scenarios/row83_p2_p6_2026.pieces_for's diagnostic piece) against the no-shock path: consumer prices on PSA's weights, 2026, and
    GDP 2026; the BSP rule reacts as in every path."""
    piece, _ = R.pieces()
    piece = dict(piece, **{"peso alone": {2026: {"exr_scale": 1 + 1 / 100}}})   # the peso 1% weaker (the same float as its piece)
    t0 = time.time()
    clean = R.run(set(), piece=piece)
    pa = R.run({"peso alone"}, piece=piece)
    log(f"  peso 1% weaker in 2026 alone: {time.time() - t0:.0f} s")
    m = R.d.ms
    return {PESO_KEY: psa_cpi.change(R.ml.link_variables(m, clean.solutions[2026], pa.solutions[2026]))["all households"],
            "peso 1% weaker in 2026 alone: GDP 2026 (%)": float(pa.table.real_gdp[2026] / clean.table.real_gdp[2026] - 1) * 100}


def run_case(setting, rule_reference=None, log=print, peso=False):
    t0 = time.time()
    R = runs(setting, rule_reference)
    log(f"  model and baseline ({setting}): {time.time() - t0:.0f} s")
    out = headline(R, log)
    if peso:                                     # 15 Nov 2026 (cand042 mode, check R42); absent = as before
        out.update(peso_alone(R, log))
        from infinity_gem.elasticities import short_run_cet
        c = R.d.a.get("sr_cet")
        out["sr_cet = short_run_cet over the model's commodities"] = "off" if c is None else str(c == short_run_cet(R.d.ms.C, "level"))
        out["sr_erpt"] = "off" if R.d.a.get("sr_erpt") is None else float(R.d.a["sr_erpt"])
    out["setting"] = setting + ("" if rule_reference is None else f" (BSP rule against the {rule_reference})")
    out["wage-curve beta"] = float(R.d.a["wage_curve"])
    out["hoarding"] = float(R.d.a["hoarding"])
    out["FIES base"] = R.ml.base                 # 18 Nov 2026: the survey of the new-poor and PSA-weight rows (check R41F)
    out["minutes"] = (time.time() - t0) / 60
    del R
    gc.collect()
    return out


def stamp_path(mode, ext):
    return paths.output_dir() / f"central_case_04_{time.strftime('%Y%m%d_%H%M')}_{mode}{ext}"


def reference_values(new: dict) -> dict:
    return {k: float(new[k]) for k in HEADLINE}


def main(argv):
    mode = (argv or ["compare"])[0]
    flags = dict(a.split("=", 1) for a in argv[1:])
    path = stamp_path(mode + (f"_{flags['tag']}" if "tag" in flags else ""), ".csv")   # tag: 14 Nov 2026; absent = as before
    logf = path.with_suffix(".log")

    def log(s):
        print(s, flush=True)
        with open(logf, "a", encoding="utf-8") as fh:
            fh.write(f"{time.strftime('%H:%M:%S')} {s}\n")
    fb_label = {"fies2023": "FIES 2023 base", "fies2025": "FIES 2025 base (the default since 18 Nov 2026)"}[_common.FIES_BASE]
    head = ["**NOT FOR CITATION** (Infinity GEM 0.4.0; `scenarios/central_case_04.py`). Infinity GEM's own SAM v1.0, public capital low; the four "
            f"shocks against the no-shock path with the same policies. New poor on the {fb_label} (own baskets)."]
    # 18 Nov 2026: the references of R4, R41 and R42 are on the FIES 2023 base; writing them on another base is refused
    if flags.get("save_reference") == "1" and mode in ("compare", "ref041", "cand042") and _common.FIES_BASE != "fies2023":
        raise SystemExit(f"{mode} save_reference=1: its reference is on the FIES 2023 base; set INFINITY_GEM_FIES_BASE=fies2023 "
                         f"(this run is on {_common.FIES_BASE!r})")
    if mode == "compare":
        log("--- new: \"0.4 recommended\" (the default)")
        new = run_case("0.4 recommended", log=log)
        pd.DataFrame({"0.4 recommended (new default)": new}).to_csv(path.with_name(path.stem + "_partial.csv"))
        log("--- old: \"0.3 recommended\" as the 2026 scenarios ran it on v1.0 (hoarding 0.85, beta of the v1.0 calibration)")
        old = run_case("0.3 recommended", log=log)
        t = pd.DataFrame({"0.3 recommended (central setting before 13 Nov 2026)": old, "0.4 recommended (new default)": new})
        t["change (new less old)"] = [
            (float(n) - float(o)) if isinstance(n, (int, float, np.floating)) and isinstance(o, (int, float, np.floating)) else ""
            for o, n in zip(t.iloc[:, 0], t.iloc[:, 1])]
        if flags.get("save_reference") == "1":
            ref = {"_meta": {"what": "check R4: the 0.4 central case's main results (scenarios/central_case_04.headline)",
                             "computed": time.strftime("%Y-%m-%d %H:%M"), "by": "scenarios/central_case_04.py compare save_reference=1",
                             "infinity_gem": __import__("infinity_gem").__version__, "SAM": paths.SAM_2023_OWN.name,
                             "setting": "0.4 recommended", "tolerance": "relative and absolute 1e-9 (as R0)"},
                   **reference_values(new)}
            REF_FILE.write_text(json.dumps(ref, indent=1), encoding="utf-8")
            log(f"saved {REF_FILE}")
    elif mode == "verify":
        ref_ = flags.get("ref", "baseline")
        log(f"--- 0.4 recommended with the BSP rule read against the {ref_} (oil series: {os.environ.get('INFINITY_GEM_OIL_SOURCE', 'default')})")
        t = pd.DataFrame({f"0.4 recommended, rule against the {ref_}, oil {_OIL or 'default'}": run_case("0.4 recommended", ref_, log=log)})
        fl = pd.read_csv(FLOOR_CSV, index_col=0, comment="#").iloc[:, 0]
        cmp_ = {"GDP gap 2026 (%)": "GDP 2026 (%)", "GDP gap 2027 (%)": "GDP 2027 (%)",
                "inflation 2026, PSA weights (pp)": "four shocks: on 2026 inflation, PSA weights (pp)",
                "policy-rate gap 2026 (pp)": "BSP rule: policy-rate gap 2026 (pp)",
                "new poor 2026 (M)": "new poor 2026 (M, own baskets)", "new poor 2027 (M)": "new poor 2027 (M, own baskets)",
                "public-works multiplier 2026": "public-works multiplier 2026", "jobs 2026 (%)": "jobs 2026 (%)",
                "growth effect 2026 (pp)": "growth effect 2026 (pp)"}
        t[f"findings: {FLOOR_CSV.name}"] = pd.Series({k: float(fl[v]) for k, v in cmp_.items() if v in fl.index})
        t["difference"] = pd.to_numeric(t.iloc[:, 0], errors="coerce") - pd.to_numeric(t.iloc[:, 1], errors="coerce")
    elif mode == "ref041":                       # 13 Nov 2026: "0.4.1 recommended" and check R41
        log("--- \"0.4.1 recommended\" (the default since 13 Nov 2026, about 5:25 PM)")
        new = run_case("0.4.1 recommended", log=log)
        log("--- \"0.4 recommended\" (0.4.0)")
        old = run_case("0.4 recommended", log=log)
        t = pd.DataFrame({"0.4 recommended (0.4.0)": old, "0.4.1 recommended (new default)": new})
        t["change (new less old)"] = [
            (float(n) - float(o)) if isinstance(n, (int, float, np.floating)) and isinstance(o, (int, float, np.floating)) else ""
            for o, n in zip(t.iloc[:, 0], t.iloc[:, 1])]
        if flags.get("save_reference") == "1":
            ref = {"_meta": {"what": "check R41: the 0.4.1 central case's main results (scenarios/central_case_04.headline)",
                             "computed": time.strftime("%Y-%m-%d %H:%M"), "by": "scenarios/central_case_04.py ref041 save_reference=1",
                             "run file": path.name, "infinity_gem": __import__("infinity_gem").__version__, "SAM": paths.SAM_2023_OWN.name,
                             "setting": "0.4.1 recommended", "tolerance": "relative and absolute 1e-9 (as R0)"},
                   **reference_values(new)}
            REF_FILE_041.write_text(json.dumps(ref, indent=1), encoding="utf-8")
            log(f"saved {REF_FILE_041}")
    elif mode == "ref041F":                      # 18 Nov 2026 (about 6:15 AM: FIES 2025 the default base; check R41F): the R41 case
        from infinity_gem import fies_base          # on the DEFAULT base; run with INFINITY_GEM_FIES_BASE unset (refused otherwise)
        if os.environ.get(fies_base.ENV) or _common.FIES_BASE != "fies2025" or fies_base.default() != "fies2025":
            raise SystemExit(f"ref041F: run with {fies_base.ENV} unset (the default base, fies2025); it is "
                             f"{os.environ.get(fies_base.ENV)!r}, _common.FIES_BASE {_common.FIES_BASE!r}")
        log("--- \"0.4.1 recommended\" on the default FIES base (fies2025)")
        new = run_case("0.4.1 recommended", log=log)
        if new["FIES base"] != "fies2025":
            raise SystemExit(f"ref041F: the run's MicroLink is on {new['FIES base']!r}")
        r41 = json.loads(REF_FILE_041.read_text(encoding="utf-8"))
        t = pd.DataFrame({"FIES 2023 base (check R41 reference)": pd.Series({k: r41[k] for k in HEADLINE}),
                          "FIES 2025 base (the default; this run)": pd.Series(reference_values(new))})
        t["change (2025 less 2023)"] = t.iloc[:, 1] - t.iloc[:, 0]
        if flags.get("save_reference") == "1":
            ref = {"_meta": {"what": "check R41F: the 0.4.1 central case's main results on the DEFAULT FIES base, FIES 2025 "
                                     "(scenarios/central_case_04.headline; same model run as R41, households and lines of FIES 2025)",
                             "computed": time.strftime("%Y-%m-%d %H:%M"), "by": "scenarios/central_case_04.py ref041F save_reference=1",
                             "run file": path.name, "infinity_gem": __import__("infinity_gem").__version__, "SAM": paths.SAM_2023_OWN.name,
                             "setting": "0.4.1 recommended", "FIES base": new["FIES base"],
                             "decision": "18 Nov 2026: FIES 2025 becomes the default base for poverty figures",
                             "tolerance": "relative and absolute 1e-9 (as R0)"},
                   **reference_values(new)}
            REF_FILE_041F.write_text(json.dumps(ref, indent=1), encoding="utf-8")
            log(f"saved {REF_FILE_041F}")
    elif mode == "accelerator":                  # 14 Nov 2026: 0.4.1 with and without the opt-in accelerator
        names = flags.get("variants", "off,central,lo,hi").split(",")
        bad = [n for n in names if n not in ACC_VARIANTS]
        if bad:
            raise SystemExit(f"unknown accelerator variant(s) {bad} ({', '.join(ACC_VARIANTS)})")
        head[0] = head[0].replace("Infinity GEM 0.4.0", f"Infinity GEM {__import__('infinity_gem').__version__}") + (
            " Setting \"0.4.1 recommended\"; the accelerator is an OPT-IN research option (DynamicCGE sr_accelerator), not in any setting.")
        t0 = time.time()
        R = runs("0.4.1 recommended")
        log(f"  model and baseline (0.4.1 recommended): {time.time() - t0:.0f} s")
        cols = {}
        for n in names:
            log(f"--- 0.4.1 recommended, accelerator {n}: {ACC_VARIANTS[n]}")
            t1 = time.time()
            try:
                col = headline_acc(R, ACC_VARIANTS[n], log)
            except Exception as err:             # a variant that fails is reported, not hidden
                log(f"    FAILED: {err!r}")
                col = {"failed": repr(err)[:300]}
            col["minutes"] = (time.time() - t1) / 60
            cols[f"0.4.1 + accelerator {n}" if n != "off" else "0.4.1 recommended (no accelerator)"] = col
            t = pd.DataFrame(cols)
            path.with_name(path.stem + "_partial.csv").write_text("# " + head[0] + "\n" + t.to_csv(), encoding="utf-8")
        t = pd.DataFrame(cols)
        if "0.4.1 recommended (no accelerator)" in t.columns:
            base_ = t["0.4.1 recommended (no accelerator)"]
            for c in [c for c in t.columns if c != base_.name]:
                t[f"{c}: change"] = [(float(n_) - float(o_)) if isinstance(n_, (int, float, np.floating)) and
                                     isinstance(o_, (int, float, np.floating)) else "" for o_, n_ in zip(base_, t[c])]
    elif mode == "cand042":                      # 15 Nov 2026 (overnight): the OPT-IN "0.4.2 candidate" beside 0.4.1 (check R42)
        head[0] = head[0].replace("Infinity GEM 0.4.0", f"Infinity GEM {__import__('infinity_gem').__version__}") + (
            " \"0.4.2 candidate\" is an OPT-IN setting (infinity_gem/settings.py OPTION_C_042C), not the default.")
        log("--- \"0.4.2 candidate\" (opt-in)")
        new = run_case(settings.CANDIDATE_042, log=log, peso=True)
        pd.DataFrame({"0.4.2 candidate": new}).to_csv(path.with_name(path.stem + "_partial.csv"))
        log("--- \"0.4.1 recommended\" (the default)")
        old = run_case("0.4.1 recommended", log=log, peso=True)
        t = pd.DataFrame({"0.4.1 recommended (default)": old, "0.4.2 candidate (opt-in)": new})
        t["change (candidate less 0.4.1)"] = [
            (float(n) - float(o)) if isinstance(n, (int, float, np.floating)) and isinstance(o, (int, float, np.floating)) else ""
            for o, n in zip(t.iloc[:, 0], t.iloc[:, 1])]
        if flags.get("save_reference") == "1":
            ref = {"_meta": {"what": "check R42: the 0.4.2 candidate's central-case main results (scenarios/central_case_04.headline) "
                                     "and the peso diagnostic (peso_alone)",
                             "computed": time.strftime("%Y-%m-%d %H:%M"), "by": "scenarios/central_case_04.py cand042 save_reference=1",
                             "run file": path.name, "infinity_gem": __import__("infinity_gem").__version__, "SAM": paths.SAM_2023_OWN.name,
                             "setting": settings.CANDIDATE_042, "tolerance": "relative and absolute 1e-9 (as R0)"},
                   **reference_values(new), PESO_KEY: float(new[PESO_KEY])}
            REF_FILE_042C.write_text(json.dumps(ref, indent=1), encoding="utf-8")
            log(f"saved {REF_FILE_042C}")
    else:
        raise SystemExit("mode must be 'compare', 'verify', 'ref041', 'ref041F', 'accelerator' or 'cand042'")
    path.write_text("# " + head[0] + "\n" + t.to_csv(), encoding="utf-8")
    path.with_suffix(".md").write_text("\n".join([f"# Infinity GEM 0.4: the central 2026 case ({mode}, {time.strftime('%d %B %Y, %H:%M')})",
                                                  "", head[0], "", t.to_markdown(floatfmt=".4f")]) + "\n", encoding="utf-8")
    log(t.to_string())
    log(f"saved {path}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main(sys.argv[1:])
