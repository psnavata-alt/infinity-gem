"""Infinity GEM 0.4.1 (18 Nov 2026): one-at-a-time sensitivity of the central 2026 case to each main assumption, the
source of section 6 of the Assumptions page (model/assumptions on the project's website). NOT FOR CITATION.

Each case changes ONE choice from the default "0.4.1 recommended" through existing options only (DynamicCGE keyword arguments
passed through combined_revised.Runs(**engine), existing elasticity sets, existing public-capital options); everything else,
including the other fitted values, is held. The numbers are scenarios/central_case_04.headline() (check R41's function).

Run (from the repository folder; one model process, about 6-7 minutes a case):
  py -X utf8 -u scenarios/sensitivity_oat_041.py [cases=default,hoard0,...]    the Infinity GEM SAM v1.0 cases (CASES below)
  py -X utf8 -u scenarios/sensitivity_oat_041.py sam=ifpri                       the SAM case: IFPRI's 2023 SAM with every
                                                                                0.4.1 value passed explicitly (separate process:
                                                                                the 2026 scenarios SAM is read at import)
Outputs: one JSON per case in outputs/ (sensitivity_oat_041_<stamp>_<case>.json); rows appended to
docs/verification/SENSITIVITY_one_at_a_time_0.4.1_18Nov2026.csv and to the run-log table of the .md beside it.
"""
import gc
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for p in (str(ROOT), str(HERE), str(ROOT / "preshock")):
    if p not in sys.path:
        sys.path.insert(0, p)
ARGS = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a)
# 18 Nov 2026 (FIES 2025 the default base from about 6:15 AM): this table's rows were run on FIES 2023 and its default case is compared
# with R41's reference (FIES 2023), so new rows stay on that base (pinned; a FIES 2025 version needs its own output table)
os.environ["INFINITY_GEM_FIES_BASE"] = "fies2023"
IFPRI = ARGS.get("sam") == "ifpri"
if IFPRI:
    # import the 2026 scenarios modules on IFPRI's SAM FIRST, so central_case_04 (which sets INFINITY_GEM_SCENARIO_SAM=own at import) reuses them
    os.environ["INFINITY_GEM_SCENARIO_SAM"] = "ifpri"
    os.environ["INFINITY_GEM_SETTING"] = "0.3 recommended"      # 0.4.1 is not defined on IFPRI's SAM; its values are passed explicitly
    os.environ["INFINITY_GEM_SCENARIO_ENGINE"] = ""
    os.environ.pop("INFINITY_GEM_SCENARIO_PESO", None)
    os.environ.pop("INFINITY_GEM_OIL_SOURCE", None)
    import _common                                      # noqa: E402,F401
    import combined_revised                             # noqa: E402,F401
import central_case_04 as CC                            # noqa: E402
import combined_revised as CR                           # noqa: E402
from infinity_gem import paths, settings                    # noqa: E402
from infinity_gem.elasticities import elasticity_set        # noqa: E402

SET = "0.4.1 recommended"
OUT_MD = ROOT / "docs" / "verification" / "SENSITIVITY_one_at_a_time_0.4.1_18Nov2026.md"
OUT_CSV = OUT_MD.with_suffix(".csv")
# public version: the central case's reference results (checks/reference_041_central.json) are not in this repository;
# without them the "change vs default" columns are left empty (run the case "default" and compare with it)
_REF_FILE = ROOT / "checks" / "reference_041_central.json"
REF = json.loads(_REF_FILE.read_text(encoding="utf-8")) if _REF_FILE.exists() else None
C41 = settings.OPTION_C_041


def _theta(t):
    mo = settings.option_c_kwargs(SET)["monetary"]
    return dict(mo, theta=float(t))


# case: (choice, value tried, default value, Runs public-capital name, engine keyword arguments as a function)
CASES = {
    "default": ("default (0.4.1 recommended)", "-", "-", "low", lambda: {}),
    "hoard0": ("labour hoarding", "0 (none)", f"{C41['hoarding']:.3f}", "low", lambda: {"hoarding": 0.0}),
    "hoard099": ("labour hoarding", "0.99 (the engine allows h < 1)", f"{C41['hoarding']:.3f}", "low", lambda: {"hoarding": 0.99}),
    "htm03": ("hand-to-mouth share", "0.3", f"{C41['sr_consumption']['htm']:.3f}", "low", lambda: {"sr_consumption": {"htm": 0.3}}),
    "htm06": ("hand-to-mouth share", "0.6", f"{C41['sr_consumption']['htm']:.3f}", "low", lambda: {"sr_consumption": {"htm": 0.6}}),
    "oil06": ("within-year oil pass-through", "0.6", f"{C41['sr_oil_pass']:.3f}", "low", lambda: {"sr_oil_pass": 0.6}),
    "oil10": ("within-year oil pass-through", "1.0", f"{C41['sr_oil_pass']:.3f}", "low", lambda: {"sr_oil_pass": 1.0}),
    "bspoff": ("BSP policy rule", "off", "on (theta 1.5)", "low", lambda: {"monetary": None}),
    "theta07": ("BSP rule: link theta", "0.7", "1.5", "low", lambda: {"monetary": _theta(0.7)}),
    "theta2": ("BSP rule: link theta", "2", "1.5", "low", lambda: {"monetary": _theta(2.0)}),
    "unemp_lm": ("who can lose jobs", "low and medium skills only", "all skills", "low",
                 lambda: {"short_run_unemployed": settings.SHORT_RUN_UNEMPLOYED["0.2 published"]}),
    "arm_gtap": ("import substitution (Armington) elasticities", "GTAP set", "Philippine set", "low",
                 lambda: {"elasticities": elasticity_set("gtap")}),
    "cobbd": ("household demand", "Cobb-Douglas (fixed budget shares)", "LES (Briones et al. 2023)", "low", lambda: {"les": None}),
    "pc_high": ("return on public capital", "high (phi 0.122, KG/GDP 0.296)", "low (phi 0.083, KG/GDP 0.397)", "high", lambda: {}),
    "pc_off": ("return on public capital", "off (phi 0: no output effect)", "low (phi 0.083, KG/GDP 0.397)", "low",
               lambda: {"public_capital": dict(phi=0.0, kg_gdp=settings.PUBLIC_CAPITAL["low"]["kg_gdp"])}),
}
IFPRI_CASE = ("SAM", "IFPRI 2023 SAM (rice split), 0.4.1 values held", "Infinity GEM SAM v1.0", "low")
KEYS = ("GDP gap 2026 (%)", "inflation 2026, PSA weights (pp)", "policy-rate gap 2026 (pp)", "new poor 2026 (M)",
        "GDP gap 2027 (%)", "public-works multiplier 2026")
STAMP = time.strftime("%Y%m%d_%H%M")
LOG = paths.output_dir() / f"sensitivity_oat_041_{STAMP}{'_ifpri' if IFPRI else ''}.log"


def log(s):
    print(s, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(s + "\n")


def build(case):
    if case == "ifpri":
        kw = settings.option_c_kwargs(SET)
        beta = kw.pop("wage_curve")
        return CR.Runs("low", setting="0.3 recommended", wage_curve=beta, rule_reference="no-shock path", **kw), kw
    _, _, _, pc, eng = CASES[case]
    kw = eng()
    return CR.Runs(pc, setting=SET, **kw), kw


def _fmt(v):
    return f"{v:.3f}" if isinstance(v, float) else str(v)


def record(case, meta, kw, out, secs):
    choice, tried, dflt = meta[:3]
    js = paths.output_dir() / f"sensitivity_oat_041_{STAMP}_{case}.json"
    row = {"case": case, "choice": choice, "value tried": tried, "default value": dflt,
           "engine arguments": "; ".join(f"{k}={'(set)' if k == 'elasticities' else v}" for k, v in kw.items()) if case != "ifpri"
           else "INFINITY_GEM_SCENARIO_SAM=ifpri, setting '0.3 recommended' + option_c_kwargs('0.4.1 recommended'), rule_reference no-shock path",
           "SAM": CR.SAM_VARIANT, **{k: out.get(k) for k in KEYS}}
    for k in KEYS:
        row[f"change vs default: {k}"] = (out[k] - REF[k]) if isinstance(out.get(k), float) and REF is not None else None
    row["BSP rule: iterations, converged"] = out.get("BSP rule: iterations, converged")
    row["employment-cap fallback years (EF1)"] = out.get("employment-cap fallback years (EF1)")
    row["seconds"] = round(secs)
    row["output file"] = "outputs/" + js.name
    js.write_text(json.dumps({"row": row, "headline": out}, indent=1, default=str), encoding="utf-8")
    import csv
    new = not OUT_CSV.exists()
    with open(OUT_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(row))
        if new:
            w.writeheader()
        w.writerow(row)
    cells = [case, choice, f"{tried} ({dflt})"] + [_fmt(out.get(k)) for k in KEYS] + ["`outputs/" + js.name + "`"]
    with open(OUT_MD, "a", encoding="utf-8") as f:
        f.write("| " + " | ".join(cells) + " |\n")
    log(f"  recorded {case}: " + ", ".join(f"{k} {_fmt(out.get(k))}" for k in KEYS[:4]) + f" ({secs:.0f} s)")


def main():
    cases = ["ifpri"] if IFPRI else (ARGS["cases"].split(",") if "cases" in ARGS else list(CASES))
    log(f"sensitivity_oat_041 {STAMP}: SAM {CR.SAM_VARIANT}, cases {cases}")
    for case in cases:
        t0 = time.time()
        log(f"--- {case}")
        try:
            R, kw = build(case)
            log(f"  model and baseline: {time.time() - t0:.0f} s")
            out = CC.headline(R, log)
            record(case, IFPRI_CASE if case == "ifpri" else CASES[case], kw, out, time.time() - t0)
        except Exception as e:                       # noqa: BLE001  a case that the engine refuses or that fails: logged, skipped
            log(f"  FAILED {case}: {e!r}")
            with open(OUT_MD, "a", encoding="utf-8") as f:
                f.write(f"| {case} | (failed: {str(e)[:160].replace('|', '/')}) | | | | | | | | `outputs/{LOG.name}` |\n")
        R = None
        gc.collect()
    log("done")


if __name__ == "__main__":
    main()
