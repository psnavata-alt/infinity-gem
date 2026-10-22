"""The money block (0.3.12, 20 Oct 2026): the four 2026 shocks with a BSP policy rule INSIDE the dynamic model
(DynamicCGE.monetary_scenario, the closed loop designed in a design note (not included)), against the central 2026 path without a rule.

Setting: the central 2026 setting of 18 Oct 2026 (Infinity GEM's own SAM, labour hoarding 0.85, the wage-curve beta of the calibration file), as scenarios/qpm_cge_link.py.
For each case (a rule of infinity_gem.monetary.rule: pamph, dsge, oil0.73, oil0.85; an investment response theta, % of real investment
per pp of real-rate gap; expectations "foresight" or "adaptive"), the combined run of the four shocks (public works, oil, El Nino,
world food and fertilizer prices) is solved with the rule and compared with the no-rule run: GDP gaps, consumer prices, new poor, the
cumulative loss, and the rule's own path (inflation gap, output gap, policy rate, expected inflation, real rate, investment scale,
iterations). The policies common to every run (the rice tariff, the 2027 aid cut) are in the no-shock path as in the 2026 scenarios.
Run (Git Bash, repository root):
  export INFINITY_GEM_SCENARIO_SAM=own
  py scenarios/monetary_check.py [rules=oil0.85,oil0.73,dsge,pamph] [thetas=2] [h=0.85] [expectations=adaptive]
                                 [extra=oil0.85:0.55,oil0.85:3.3,oil0.85:2:foresight] [tol=0.01] [max_iter=15]
Output: outputs/monetary_check_<stamp><tag>.md

21 Oct 2026, about 12:45 AM (the CGE's 2026 price response, the reason the closed loop cuts): engine
variants and a rule fed with the observed inflation gap. New arguments (each defaults to none, so the 20 Oct run is reproduced):
  sticky=none|sectoral|0.6|0.3  prices rigid downward in the short-run years (DynamicCGE sr_pricing="sticky"; the sectoral shares of
                                infinity_gem.stickiness, check ST1, or one share). The wage-curve beta is the one recalibrated for that
                                row in the latest engine_sensitivities_*<sam>.csv run WITHOUT engine settings (the sensitivity table's recipe:
                                scenarios/engine_sensitivities.py beta_without_engine); the central beta if no such file.
  energy=none|bundle            the value added-energy bundle with MANAGE-WB's elasticities (check EN1-EN2; the
                                NEST_LR / NEST_SR of scenarios/energy_nest_oil_check.py).
  observed=none|var             the rule fed with the OBSERVED 2026-2027 inflation gap instead of the CGE's own: calendar 2026
                                +1.64 pp and 2027 +0.96 pp above the pre-shock forecast (preshock/inflation_var.py,
                                outputs/inflation_var_20261016.md section 4; 2025 and 2028-2030: 0), with the CGE's own output
                                and peso gaps, solved as a damped fixed point on the rate path through monetary_scenario(path=...).
                                The no-shock path carries no rule in this variant, so the measures are the shocks' alone.
  tag=                          extra suffix for the output name.
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import _common                                                       # noqa: E402
import combined_revised as CR                                        # noqa: E402
from infinity_gem import monetary as MO                                  # noqa: E402
from infinity_gem import paths                                           # noqa: E402
from infinity_gem import stickiness as STK                               # noqa: E402
from infinity_gem.dynamic import PSA_INDUSTRIES                          # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ALL = {"public works", "oil", "El Nino", "world food and fertilizer prices"}
KEYS = ["GDP gap 2026 (%)", "GDP gap 2027 (%)", "GDP gap 2030 (%)", "consumer prices 2026 (%)",
        "new poor 2026 (M, own baskets)", "new poor 2027 (M, own baskets)", "cumulative GDP loss 2025-2030 (₱ bn)"]
# 21 Oct 2026: the sticky-price activities (all but farm and mining, DynamicCGE's default; scenarios/engine_sensitivities.py)
STICKY = [a for k, v in PSA_INDUSTRIES.items() if k not in ("Agriculture, forestry, and fishing", "Mining and quarrying") for a in v]
STICKY_ROW = {"sectoral": "D2, sectoral: stickiness by sector, BSP WPS 2020-02 (beta recalibrated)",
              "0.6": "D2, high: stickiness 0.6 (beta recalibrated)",
              "0.3": "D2, low: prices rigid downward in 2025-2027, stickiness 0.3 (beta recalibrated)"}
# (scenarios/energy_nest_oil_check.py): MANAGE-WB's bridge-file defaults, old vintage 0.1 (short run), new 0.8
NEST_LR = {"energy": ["cpetr", "celec"], "sigma_ve": 0.8, "sigma_e": 0.5}
NEST_SR = {"energy": ["cpetr", "celec"], "sigma_ve": 0.1, "sigma_e": 0.5}
# the observed inflation gap, calendar years, pp above the pre-shock forecast (outputs/inflation_var_20261016.md, section 4:
# 2026 5.99% against 4.35% forecast; 2027 5.21% against 4.25%); nothing observed for 2025 (the forecast starts in 2026) or after 2027
OBSERVED_GAP = {"var": {2026: 1.64, 2027: 0.96}}


def arg(name, default, cast=str):
    return next((cast(a.split("=", 1)[1]) for a in sys.argv[1:] if a.startswith(f"{name}=")), default)


def sticky_engine(opt: str):
    """(engine kwargs, recalibrated beta or None, its source) for sticky=... (none: as before). sticky=farm (21 Oct, about 1:40 AM,
    indicative): every activity rigid downward, the farm and mining activities at the food group's share (0.29, BSP WPS 2020-02:
    a price decrease about every 3.6 months), the rest as sticky=sectoral; the beta of the sectoral row is reused (not recalibrated)."""
    if opt in ("none", "", "no"):
        return {}, None, ""
    if opt == "farm":
        from infinity_gem.settings import cge_model
        acts = list(cge_model("0.3 recommended", rice=True).A)
        shares = STK.sectoral(STICKY)
        food = STK.share_not_passed(STK.DECREASE_MONTHS["Food and non-alcoholic beverages"])
        shares.update({a: food for a in acts if a not in shares})
        kw = dict(sr_pricing="sticky", sr_stickiness=shares, sticky_acts=acts)
        opt = "sectoral"                              # the row whose recalibrated beta is reused
    else:
        kw = dict(sr_pricing="sticky", sr_stickiness=STK.sectoral(STICKY) if opt == "sectoral" else float(opt))
    row = STICKY_ROW.get(opt)
    files = sorted(paths.output_dir().glob("engine_sensitivities_" + "[0-9]" * 8 + "_" + "[0-9]" * 4 + _common.sam_tag() + ".csv"))
    if row is None or not files:
        return kw, None, "no recalibrated beta on file for this stickiness: the central beta is used"
    t = pd.read_csv(files[-1], index_col=0)
    return kw, float(t.loc[row, "wage-curve beta"]), files[-1].name


def run_case(beta, h, monetary=None, tol=None, max_iter=None, engine=None):
    if monetary and tol is not None:
        monetary = dict(monetary, tol=tol)
    if monetary and max_iter is not None:
        monetary = dict(monetary, max_iter=max_iter)
    R = CR.Runs("low", wage_curve=beta, **({"hoarding": h} if h else {}), **({"monetary": monetary} if monetary else {}),
                **(engine or {}))
    piece, _ = R.pieces()
    clean = R.run(set(), piece=piece)
    sim = R.run(ALL, piece=piece)
    M = R.measures(clean, sim)[0]
    cpi = (sim.table.cpi / clean.table.cpi - 1) * 100
    M["consumer prices 2027 (%)"] = float(cpi[2027])
    return R, clean, sim, M


def run_observed(beta, h, rule, theta, gaps, engine=None, tol=0.01, max_iter=12, relax=0.5):
    """21 Oct 2026: the rule fed with observed inflation gaps (pp a year, by calendar year) and the CGE's own output and peso gaps,
    solved as a damped fixed point on the policy-rate path through monetary_scenario(path=...): each step reads the gaps of the
    last path, gives the rule's rate (annual_rule, with adaptive expectations on the OBSERVED gap) and reruns with that rate
    imposed. The no-shock path carries no rule. Returns (R, clean, sim, measures, the rule's table, iterations, converged, deltas)."""
    R = CR.Runs("low", wage_curve=beta, **({"hoarding": h} if h else {}), **(engine or {}))
    piece, _ = R.pieces()
    clean = R.run(set(), piece=piece)
    sim = R.run(ALL, piece=piece)                                  # the path without a rule
    years = [t for t in R.d.years[1:] if t >= 2025]                 # the rule acts from the first year with a shock (2025 works)
    rate = {t: 0.0 for t in years}
    deltas, converged, it = [], False, 0
    for it in range(1, max_iter + 1):
        g = R.d.monetary_gaps(sim)
        new, path, i_end, prev_gap = {}, {}, 0.0, 0.0
        for t in years:
            obs = float(gaps.get(t, 0.0))
            target = (float(rule["phi_pi"]) * obs + float(rule["phi_x"]) * float(g.loc[t, "output_gap_pct"])
                      + float(rule.get("phi_e", 0.0)) * float(g.loc[t, "depreciation_gap_pp"]))
            new[t], i_end = R.d.annual_rule(rule, target, i_end)
            path[t] = {"pi_e": prev_gap}                              # adaptive: last year's observed gap
            prev_gap = obs
        delta = max(abs(new[t] - rate[t]) for t in years)
        deltas.append(delta)
        if delta < tol:
            converged = True
            break
        rate = {t: rate[t] + relax * (new[t] - rate[t]) for t in years}
        for t in years:
            path[t]["i"] = rate[t]
        R.d.a["monetary"] = {"path": path, "theta": theta, "max_iter": 2}
        try:
            sim = R.run(ALL, piece=piece)
        finally:
            R.d.a["monetary"] = None
    M = R.measures(clean, sim)[0]
    cpi = (sim.table.cpi / clean.table.cpi - 1) * 100
    M["consumer prices 2027 (%)"] = float(cpi[2027])
    tab = R.d.monetary_gaps(sim).loc[years].copy()
    tab["observed inflation gap used (pp)"] = pd.Series({t: float(gaps.get(t, 0.0)) for t in years})
    tab["policy_rate_gap_pp"] = pd.Series(rate)
    tab["expected_inflation_gap_pp"] = pd.Series({t: float(gaps.get(years[k - 1], 0.0)) if k > 0 else 0.0 for k, t in enumerate(years)})
    tab["real_rate_gap_pp"] = tab["policy_rate_gap_pp"] - tab["expected_inflation_gap_pp"]
    if getattr(sim, "monetary", None) is not None:
        tab["investment_scale"] = sim.monetary["investment_scale"]
    return R, clean, sim, M, tab, it, converged, deltas


def main():
    rules = [r for r in arg("rules", "oil0.85,oil0.73,dsge,pamph").split(",") if r]
    thetas = [float(x) for x in arg("thetas", "2").split(",")]
    h = float(arg("h", "0.85"))
    exp0 = arg("expectations", "adaptive")
    cases = [(r, th, exp0) for r in rules for th in thetas]
    for e in [x for x in arg("extra", "oil0.85:0.55,oil0.85:3.3,oil0.85:2:foresight").split(",") if x]:
        p = e.split(":")
        cases.append((p[0], float(p[1]), p[2] if len(p) > 2 else exp0))
    tol = float(arg("tol", "0.01"))                   # pp: a 0.01 pp rate difference moves investment by 0.02% at theta 2
    max_iter = int(arg("max_iter", "12"))
    sticky, energy, observed, tag = arg("sticky", "none"), arg("energy", "none"), arg("observed", "none"), arg("tag", "")
    if arg("only_observed", "0") == "1":             # observed=...: skip the rule cases (already on file) and run only the observed ones
        cases = []
    engine, beta_sticky, beta_src = sticky_engine(sticky)
    if energy == "bundle":
        engine.update(energy_nest=NEST_LR, sr_energy_nest=NEST_SR)
    elif energy != "none":
        raise SystemExit("energy must be none or bundle")
    if observed not in ("none",) + tuple(OBSERVED_GAP):
        raise SystemExit(f"observed must be none or one of {', '.join(OBSERVED_GAP)}")
    beta_c = float(pd.read_csv(_common.calibration_file(), index_col=0).loc["central (e)", "beta"])
    beta = beta_sticky if beta_sticky is not None else beta_c
    variant = []
    if sticky != "none":
        variant.append(f"prices rigid downward in the short-run years, stickiness {sticky} (wage-curve beta {beta:.3f}: {beta_src})")
    if energy == "bundle":
        variant.append("value added-energy bundle, MANAGE-WB elasticities (0.1 short run, 0.8 later; 0.5 between carriers)")
    if observed != "none":
        variant.append("the rule fed with the observed inflation gap " + ", ".join(f"{y}: {v:+.2f} pp" for y, v in OBSERVED_GAP[observed].items()))
    print("variant:", "; ".join(variant) or "none (the 20 Oct setting)", flush=True)
    print("no rule ...", flush=True)
    R0, clean0, sim0, M0 = run_case(beta, h, engine=engine)
    rows = {"no rule (the 2026 shocks)": {k: M0.get(k) for k in KEYS + ["consumer prices 2027 (%)"]}}
    rows["no rule (the 2026 shocks)"]["2026 inflation gap the rule sees (pp)"] = float(R0.d.monetary_gaps(sim0).loc[2026, "inflation_gap_pp"])
    paths_ = {}
    coef = {}
    failed = {}
    for name, th, exp in cases:
        rule = MO.rule(name)
        coef[name] = rule
        lab = f"{name}, theta {th:g}, {exp}"
        print(lab, "...", flush=True)
        try:
            R, clean, sim, M = run_case(beta, h, {"rule": rule, "theta": th, "expectations": exp}, tol=tol, max_iter=max_iter,
                                        engine=engine)
        except RuntimeError as e:                    # a case the model cannot solve is recorded, the others go on
            failed[lab] = str(e).splitlines()[0][:200]
            print("FAILED:", failed[lab], flush=True)
            continue
        row = {k: M.get(k) for k in KEYS + ["consumer prices 2027 (%)"]}
        row["iterations"] = sim.monetary.attrs["iterations"]
        row["converged"] = sim.monetary.attrs["converged"]
        row["largest rate change at the last iteration (pp)"] = float(sim.monetary.attrs["deltas"][-1]) if sim.monetary.attrs["deltas"] else 0.0
        row["no-shock path: largest rate gap (pp)"] = float(clean.monetary["policy_rate_gap_pp"].abs().max())
        rows[lab] = row
        paths_[lab] = sim.monetary
        print(pd.Series(row).to_string(), flush=True)
    if observed != "none":
        for name in rules:
            rule = MO.rule(name)
            coef[name] = rule
            for th in thetas:
                lab = f"{name}, theta {th:g}, observed inflation gap ({observed})"
                print(lab, "...", flush=True)
                try:
                    R, clean, sim, M, tab, it, conv, deltas = run_observed(beta, h, rule, th, OBSERVED_GAP[observed], engine=engine,
                                                                            tol=tol, max_iter=max_iter)
                except RuntimeError as e:
                    failed[lab] = str(e).splitlines()[0][:200]
                    print("FAILED:", failed[lab], flush=True)
                    continue
                row = {k: M.get(k) for k in KEYS + ["consumer prices 2027 (%)"]}
                row["iterations"], row["converged"] = it, conv
                row["largest rate change at the last iteration (pp)"] = float(deltas[-1]) if deltas else 0.0
                row["no-shock path: largest rate gap (pp)"] = 0.0
                rows[lab] = row
                tab.attrs.update({"iterations": it, "converged": conv, "deltas": deltas})
                paths_[lab] = tab
                print(pd.Series(row).to_string(), flush=True)
    t = pd.DataFrame(rows)
    diff = t.loc[KEYS + ["consumer prices 2027 (%)"]].sub(t.loc[KEYS + ["consumer prices 2027 (%)"], "no rule (the 2026 shocks)"], axis=0)
    stamp = dt.datetime.now()
    vtag = (f"_sticky{sticky}" if sticky != "none" else "") + ("_energy" if energy == "bundle" else "") \
        + (f"_obs{observed}" if observed != "none" else "") + tag
    out = paths.output_dir() / f"monetary_check_{stamp:%Y%m%d_%H%M}{_common.out_tag()}{vtag}.md"
    L = [f"# The money block: the 2026 shocks with a BSP policy rule inside the dynamic model ({stamp:%d %B %Y, %H:%M})", "",
         f"**NOT FOR CITATION** (Infinity GEM 0.3.12; research). `DynamicCGE.monetary_scenario` (the closed loop: the CGE's own inflation "
         f"and output gaps feed a policy rule within the year, the rule's real-rate gap scales real investment demand by exp(-theta r / 100), "
         f"the path is solved as a fixed point). CGE: central 2026 setting of 18 Oct 2026, SAM `{CR.SAM_VARIANT}`, wage-curve beta {beta:.3f}, "
         f"labour hoarding h = {h:g}; the four shocks of the 2026 scenarios; the rice tariff and the 2027 aid cut in every path. The inflation "
         f"gap the rule sees exists in the short-run years ({', '.join(str(y) for y in CR.SHORT)}; the peso is the numeraire there); in "
         f"the long-run years the CPI is the numeraire, so only the output gap and the peso move the rule. Expectations: 'foresight' = "
         f"next year's inflation gap of the path; 'adaptive' = last year's. Fixed point: tolerance {tol:g} pp on the rate path, at most "
         f"{max_iter} iterations (the last change is reported).", "",
         "**Variant (21 Oct 2026):** " + ("; ".join(variant) if variant else "none: the 20 Oct setting (flexible short-run prices, "
                                                                            "Leontief fuel, the CGE's own inflation gap)") + ".", ""]
    if observed != "none":
        L += ["In the 'observed inflation gap' cases the rule reads the OBSERVED gap (above) in place of the CGE's own, with the CGE's own "
              "output and peso gaps; the rate path is solved by a damped fixed point through `monetary_scenario(path=...)`, expected "
              "inflation = last year's observed gap, and the no-shock path has no rule (so the measures are the shocks' alone).", ""]
    if failed:
        L += ["**Cases the model could not solve** (recorded, not fixed): " + "; ".join(f"{k}: {v}" for k, v in failed.items()), ""]
    L += [
         "## Rules", "",
         pd.DataFrame(coef).T.to_markdown(floatfmt=".3f"), "",
         "## Results (levels) and differences from the no-rule path of this variant", "",
         t.to_markdown(floatfmt=".3f"), "", "Differences (with the rule minus without):", "", diff.to_markdown(floatfmt=".3f"), "",
         "## The rule's path in each case", ""]
    for lab, tab in paths_.items():
        L += [f"### {lab}", "", tab.to_markdown(floatfmt=".3f"), "",
              f"iterations {tab.attrs['iterations']}, converged {tab.attrs['converged']}, largest rate change by iteration (pp): "
              f"{', '.join(f'{x:.4f}' for x in tab.attrs['deltas'])}", ""]
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:14])); print("saved", out)


if __name__ == "__main__":
    main()
