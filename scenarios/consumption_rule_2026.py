"""The central 2026 case with the short-run consumption rule (0.3.13, 22 Oct 2026). NOT FOR CITATION.

Question. The central 2026 case (flexible prices) gets the 2026 GDP slowdown about right but not its composition (development
copy, 22 Oct 2026): household consumption -4.19 points against PSA H1 2026's -2.07 (against trend), exports +0.16 against
+4.06, imports -5.38 against +0.77. How much of the result depends on the consumption channel? Answered with the engine's
short-run consumption rule (dynamic.py sr_consumption={"htm": lam}, check CS1): in the short-run years household spending =
lam x (1 - baseline saving rates) x disposable income + (1 - lam) x baseline spending x CPI / baseline CPI, met by the year's
saving-rate adjustment (one factor for every household), solved with the wage curve as one root. The rule applies in every
path's short-run years (the no-shock path's too).

The case: scenarios/combined_revised.py on Infinity GEM's own SAM v0.5 (set below), flexible prices, paid labour hoarding 0.85
(set below), the wage curve at the central beta of the latest wage-curve calibration on that SAM
(scenarios/calibrate_wage_curve.py; 10.5133 in the calibration of 18 Oct 2026), public capital low, short-run closure in
2025-2027; the four shocks against the no-shock path with the same policies (rice tariff 2026-27, the 2027 NEP aid cut).
Columns: the rule off; lam 0.62 (central: the project's DSGE hand-to-mouth share, pooled ratio2 posterior, 21 Oct 2026), 0.48
and 0.84 (the range across the DSGE models estimated) and 0.80 (added after 0.84 did not solve in the first run, 22 Oct 2026,
22:04: in the no-shock path's 2026 the employment cap's regimes alternate for high-skill labour, which sits at full
employment; a configuration that fails is reported with the paths that fail, never forced); for comparison, option (c):
markup pricing with stickiness by sector (mk_pass 0) at h 0.85 and beta 2.4, without the rule and with lam 0.62; the data.
Rows: growth effects are (1 + gap 2026) / (1 + gap 2025) - 1 (points); gaps against the no-shock path; consumer prices on PSA's
CPI weights; multiplier = -(GDP gap 2026 of public works alone) / (the 2026 public-construction fall, % of 2026 GDP);
construction jobs relative to all jobs and the average wage (industry_pattern_vs_data.model_pattern); new poor with the
families' own baskets (combined_revised.Runs.poor; it needs the FIES microdata, data/raw/fies/README.md).
Data and verification: the data column (PSA H1 2026 by expenditure against the pre-shock trend, and the refit's targets) and
the two verification rows compare with tables that a development script saved in outputs/ (markup_demand_side_2026_*.csv);
that script is not in this repository. Without those tables the measures read from them are reported as not available and
the verification says that it was not run; everything else is computed as before.
Research runs only; no default or named setting changes.
Run (from the repository folder):  python scenarios/consumption_rule_2026.py   (about 15-20 minutes)
Output: outputs/consumption_rule_2026_<YYYYMMDD_HHMM>.md and .csv (the stamp is the start time).
"""
import os

os.environ["INFINITY_GEM_SCENARIO_SAM"] = "own"                  # the central 2026 case; set before _common reads them
os.environ["INFINITY_GEM_SCENARIO_ENGINE"] = '{"hoarding": 0.85}'
import sys                                                                      # noqa: E402
import time                                                                     # noqa: E402

import numpy as np                                                              # noqa: E402
import pandas as pd                                                             # noqa: E402

from _common import PSA_GDP, calibration_file                                   # noqa: E402
import combined_revised as CR                                                   # noqa: E402
from industry_pattern_vs_data import model_pattern                              # noqa: E402
from infinity_gem import paths, psa_cpi                                             # noqa: E402
from infinity_gem import stickiness as STK                                          # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
pd.set_option("display.width", 250)

HEAD = "**NOT FOR CITATION (research; development version).**"
CSV_HEAD = "# NOT FOR CITATION (research; development version: Infinity GEM 0.3.13). scenarios/consumption_rule_2026.py"
CON = "Construction"
H = 0.85                                     # paid labour hoarding: the central 2026 case's
LAMS = (0.62, 0.48, 0.84,                    # the DSGE's hand-to-mouth share: central, and the range across its models;
        0.80)                                # 0.80 added after 0.84 did not solve in the first run (22 Oct 2026, 22:04; see write_md)
BETA_C = 2.4                                 # option (c)'s point: Blanchflower and Oswald's slope (a design note, not included)
OUT = paths.output_dir()
DATA_FILE = OUT / "markup_demand_side_2026_20261022_1934_own_hoarding0.85_data.csv"
DIAG_FILE = OUT / "markup_demand_side_2026_20261022_1934_own_hoarding0.85_diag.csv"
PROTO_FILE = OUT / "markup_demand_side_2026_20261022_1945_own_hoarding0.85_search_smooth.csv"
DIAG_COL, PROTO_COL = "flexible (the central 2026 setting, h 0.85, beta 10.5)", "smoothing 0.62, h 0.85, beta 2.4"
QUINTILES = {"Q1 (poorest fifth)": ("hhd-r1", "hhd-u1"), "Q2": ("hhd-r2", "hhd-u2"), "Q5 (richest fifth)": ("hhd-r5", "hhd-u5")}
# the main table's rows, in order (labels as in the development script that saved the data table)
MAIN = ["GDP 2026 (%)", "growth effect 2026 (pp)", "C growth effect 2026 (pp)", "X growth effect 2026 (pp)",
        "M growth effect 2026 (pp)", "I growth effect 2026 (pp)", "four shocks: on 2026 inflation, PSA weights (pp)",
        "public-works multiplier 2026", "construction jobs, relative to all jobs (pp)", "average wage 2026 (%)",
        "new poor 2026 (M, own baskets)", "GDP 2027 (%)", "new poor 2027 (M, own baskets)"]


def central_beta():
    """The central wage-curve beta: the central row of the latest calibration on the own SAM (as combined_revised.main reads it)."""
    f = calibration_file()
    return float(pd.read_csv(f, index_col=0).loc["central (e)", "beta"]), f.name


def build(pricing):
    """The central model (flexible prices) or option (c): markup pricing with stickiness by sector, mk_pass 0."""
    t0 = time.time()
    if pricing == "markup":
        R = CR.Runs("low", sr_pricing="markup", sr_markup_pass=0.0, hoarding=H)
        acts = [a for i, a in enumerate(R.d.ms.A) if R.d.ms.isMK[i]]
        R.d.a["sr_stickiness"] = STK.sectoral(acts)
    else:
        R = CR.Runs("low", hoarding=H)
    piece, src = R.pieces()
    print(f"  model {pricing}: {time.time() - t0:.0f} s", flush=True)
    return R, piece, src


def _agg(m, sol):
    """Real expenditure at base prices; exports and imports with re-exports, as PSA's."""
    rex = float(np.sum(m.rex))
    return {"C": float(np.sum(sol["QH"])), "G": float(np.sum(sol["QG"])), "I": float(np.sum(sol["QINV"]) + np.sum(m.qdst)),
            "X": float(np.sum(sol["QE"])) + rex, "M": float(np.sum(sol["QM"])) + rex}


def _real_spending(m, sol, groups):
    """Real household spending of some household groups: nominal spending deflated by each group's own price index (its budget
    shares x consumer prices, as HouseholdDetail.group_effects)."""
    return sum(float(sol["EH"][m.H.index(h)]) / float(m.beta[:, m.H.index(h)] @ np.asarray(sol["PQ"], float)) for h in groups)


def evaluate(R, piece, src, beta, lam):
    """One column: the measures for the four shocks against the no-shock path, with the rule at lam (None = off)."""
    d, m = R.d, R.d.ms
    d.a["wage_curve"] = float(beta)
    d.a["sr_consumption"] = None if lam is None else {"htm": float(lam)}
    d.a["monetary"] = None
    t0 = time.time()
    clean = R.run(set(), piece=piece)
    sim = R.run(set(CR.SHOCKS), piece=piece)
    pw = R.run({"public works"}, piece=piece)
    cut_pct = -float(src["public works"]["2026 central"]) / PSA_GDP[2026] * 100
    gap = lambda p, y: float(p.table.real_gdp[y] / clean.table.real_gdp[y] - 1) * 100
    ge = lambda a, b: ((1 + a / 100) / (1 + b / 100) - 1) * 100
    g25, g26, g27 = gap(sim, 2025), gap(sim, 2026), gap(sim, 2027)
    pc = {y: psa_cpi.change(R.ml.link_variables(m, clean.solutions[y], sim.solutions[y]))["all households"] for y in (2025, 2026)}
    b26, s26 = clean.solutions[2026], sim.solutions[2026]
    mp, mt = model_pattern(m, b26, s26)
    rel_mj = mp["model jobs (%)"] - mt["jobs"]
    wage = ((1 + mt["labour income"] / 100) / (1 + mt["jobs"] / 100) - 1) * 100
    cpi26 = (float(s26["CPI"]) / float(b26["CPI"]) - 1) * 100
    row = {"wage-curve beta": float(beta), "hand-to-mouth share lam (None = rule off)": np.nan if lam is None else float(lam),
           "GDP 2025 (%)": g25, "GDP 2026 (%)": g26, "growth effect 2026 (pp)": ge(g26, g25), "GDP 2027 (%)": g27,
           "public-works multiplier 2026": -gap(pw, 2026) / cut_pct,
           "four shocks: on 2026 inflation, PSA weights (pp)": ge(pc[2026], pc[2025]),
           "consumer prices 2026, PSA weights (%)": pc[2026], "CPI 2026, SAM weights (%)": cpi26,
           "construction jobs, relative to all jobs (pp)": float(rel_mj[CON]),
           "jobs 2026 (%)": mt["jobs"], "average wage 2026 (%)": wage}
    a = {y: (_agg(m, clean.solutions[y]), _agg(m, sim.solutions[y])) for y in (2025, 2026)}
    for k in ("C", "G", "I", "X", "M"):
        l25 = (a[2025][1][k] / a[2025][0][k] - 1) * 100
        l26 = (a[2026][1][k] / a[2026][0][k] - 1) * 100
        row[f"{k} 2026 (%)"] = l26
        row[f"{k} growth effect 2026 (pp)"] = ge(l26, l25)
    # how the rule works: the saving-rate adjustment and household saving, disposable income and spending by quintile
    row["saving-rate adjustment 2026, MPSADJ (four shocks)"] = float(s26["MPSADJ"])
    row["saving-rate adjustment 2026, MPSADJ (no-shock path)"] = float(b26["MPSADJ"])
    row["household saving 2026 (%, nominal)"] = (float(np.sum(s26["HSAV"])) / float(np.sum(b26["HSAV"])) - 1) * 100
    row["household disposable income 2026 (%, real, SAM CPI)"] = ((float(np.sum(s26["DY"])) / float(np.sum(b26["DY"])))
                                                                  / (1 + cpi26 / 100) - 1) * 100
    row["household spending 2026 (%, real, SAM CPI)"] = ((float(np.sum(s26["EH"])) / float(np.sum(b26["EH"])))
                                                         / (1 + cpi26 / 100) - 1) * 100
    for q, grp in QUINTILES.items():
        row[f"real spending 2026, {q} (%, own prices)"] = (_real_spending(m, s26, grp) / _real_spending(m, b26, grp) - 1) * 100
        row[f"disposable income 2026, {q} (%, nominal)"] = (sum(float(s26["DY"][m.H.index(h)]) for h in grp)
                                                            / sum(float(b26["DY"][m.H.index(h)]) for h in grp) - 1) * 100
    capped = {y: str(sim.table.loc[y, "employment_capped"]) for y in CR.SHORT if "employment_capped" in sim.table.columns}
    row["employment cap binds (four shocks; years: types)"] = "; ".join(f"{y}: {v}" for y, v in capped.items() if v) or "none"
    row["new poor 2026 (M, own baskets)"] = R.poor(clean, sim, 2026)[0] / 1e6
    row["new poor 2027 (M, own baskets)"] = R.poor(clean, sim, 2027)[0] / 1e6
    row["seconds"] = time.time() - t0
    print(f"    {time.time() - t0:.0f} s; growth {row['growth effect 2026 (pp)']:+.3f}, C {row['C growth effect 2026 (pp)']:+.3f}, "
          f"new poor 2026 {row['new poor 2026 (M, own baskets)']:.3f} M", flush=True)
    return row


def data_column():
    """PSA H1 2026 against the pre-shock trend (a development script's table, 22 Oct 2026, 19:34) and the refit's targets.
    Public version: that table is not in this repository; without it the measures read from it are reported as not available."""
    t = pd.read_csv(DATA_FILE, index_col=0, comment="#")["H1 2026 less trend (pp)"] if DATA_FILE.exists() else None
    v = (lambda k: f"{t[k]:+.2f}") if t is not None else (lambda k: "not available")
    return {"GDP 2026 (%)": "not observed (a level gap needs the no-shock path)",
            "growth effect 2026 (pp)": f"about -2.9 (H1 growth 2.6% against the pre-shock 5.5%); {v('GDP')} against the H1 trend",
            "C growth effect 2026 (pp)": v("household consumption (C)"),
            "X growth effect 2026 (pp)": v("exports (X)"),
            "M growth effect 2026 (pp)": v("imports (M)"),
            "I growth effect 2026 (pp)": f"{v('gross capital formation (I)')} (gross capital formation)",
            "four shocks: on 2026 inflation, PSA weights (pp)": "+1.64 (1.06-2.27), inflation VAR; like-for-like +1.98 (1.40-2.61)",
            "public-works multiplier 2026": "1.11 (0.85-1.37); 0.99 (0.68-1.29) with budget-cycle controls",
            "construction jobs, relative to all jobs (pp)": "-1.69 (LFS Jan-Aug 2026)",
            "average wage 2026 (%)": "no fall against trend (LFS daily basic pay +9.0% after +7.3%)",
            "new poor 2026 (M, own baskets)": "not observed (FIES 2026 not yet out)",
            "GDP 2027 (%)": "", "new poor 2027 (M, own baskets)": ""}


def compare(row, file, col):
    """Largest absolute difference between this script's row and a saved row of a development script's table, over common
    measures."""
    t = pd.read_csv(file, index_col=0, comment="#")
    ref = pd.to_numeric(t[col], errors="coerce")
    common = [k for k in ref.index if k in row and np.isfinite(ref[k]) and isinstance(row[k], (int, float, np.floating))
              and np.isfinite(float(row[k])) and k not in ("seconds", "wage-curve beta", "hoarding h")]
    diff = {k: float(row[k]) - float(ref[k]) for k in common}
    k_max = max(diff, key=lambda k: abs(diff[k]))
    return pd.Series(diff), k_max


VER = "verification: rule off, beta 10.513"
DATA = "data (PSA H1 2026 against trend; targets)"
CAP = "employment cap binds (four shocks; years: types)"
OFF, C62 = "the central 2026 setting (flexible): rule off", "the central 2026 setting: rule lam 0.62"
OPT_OFF, OPT_62 = f"option (c), h {H:g}, beta {BETA_C:g}: rule off", f"option (c), h {H:g}, beta {BETA_C:g}: rule lam 0.62"


def main():
    """Every configuration, saved to the CSV as soon as all have run; the report is then written from the CSV (write_md)."""
    stamp = pd.Timestamp.today()
    beta_c, _ = central_beta()
    cols = {}

    def col(label, R, piece, src, beta, lam):
        print(f"--- {label}", flush=True)
        try:
            cols[label] = evaluate(R, piece, src, beta, lam)
        except RuntimeError as err:                  # reported, not hidden (no tolerance is loosened): which path fails?
            print(f"    FAILED: {err}", flush=True)
            paths_ = []
            for name, S in (("no-shock path", set()), ("four shocks", set(CR.SHOCKS)), ("public works alone", {"public works"})):
                try:
                    R.run(S, piece=piece)
                    paths_.append(f"{name} solves")
                except RuntimeError as e2:
                    paths_.append(f"{name}: {e2}")
            cols[label] = {"failed": f"{str(err)[:200]} ({'; '.join(paths_)})"}
            print(f"    {cols[label]['failed']}", flush=True)

    R, piece, src = build("flex")
    col(VER, R, piece, src, 10.513, None)
    col(OFF, R, piece, src, beta_c, None)
    for lam in LAMS:
        col(f"the central 2026 setting: rule lam {lam:g}", R, piece, src, beta_c, lam)
    del R
    R, piece, src = build("markup")
    col(OPT_OFF, R, piece, src, BETA_C, None)
    col(OPT_62, R, piece, src, BETA_C, 0.62)
    T = pd.DataFrame(cols)
    T[DATA] = pd.Series(data_column())
    path = OUT / f"consumption_rule_2026_{stamp:%Y%m%d_%H%M}.csv"
    path.write_text(CSV_HEAD + "\n" + T.to_csv(), encoding="utf-8")
    print("saved", path, flush=True)
    write_md(path, stamp)


def write_md(path, stamp=None):
    """The report from a saved CSV (also: py scenarios/consumption_rule_2026.py md <csv>)."""
    from pathlib import Path
    path = Path(path)
    stamp = stamp or pd.to_datetime(path.stem.split("consumption_rule_2026_")[1][:13], format="%Y%m%d_%H%M")
    beta_c, cal_name = central_beta()
    T = pd.read_csv(path, index_col=0, comment="#")
    data = T[DATA]
    models = [c for c in T.columns if c != DATA]
    failed = {c: T.loc["failed", c] for c in models if "failed" in T.index and isinstance(T.loc["failed", c], str)}
    ok = [c for c in models if c not in failed]
    text_rows = [r for r in (CAP, "failed") if r in T.index]
    Tn = T.loc[[r for r in T.index if r not in text_rows and r != "seconds"], ok].apply(pd.to_numeric, errors="coerce")
    show = [c for c in ok if c != VER]
    main_t = Tn.loc[MAIN, show].copy()
    main_t[DATA] = data.reindex(MAIN).fillna("")
    rest = [k for k in Tn.index if k not in MAIN]
    g = lambda c, k: float(Tn.loc[k, c])
    L = [HEAD, "", f"# The central 2026 case with the short-run consumption rule ({stamp:%d %B %Y, %H:%M})", "",
         "Infinity GEM 0.3.13; engine option `DynamicCGE(sr_consumption={'htm': lam})` (dynamic.py, check CS1). Script: "
         "`scenarios/consumption_rule_2026.py`; every number below is in `" + path.name + "`. No default or named setting "
         "changed.", "",
         f"**Case.** The central 2026 case: Infinity GEM's own SAM v0.5, flexible prices, paid labour hoarding {H:g}, the wage curve at beta "
         f"{beta_c:.4f} (central row of `outputs/{cal_name}`), public capital low, short-run closure 2025-2027; the four shocks "
         "against the no-shock path with the same policies. The rule applies in the short-run years of every path (the no-shock "
         "path's too): household spending = lam x (1 - baseline saving rates) x disposable income + (1 - lam) x baseline spending "
         "x CPI / baseline CPI, met by one saving-rate factor for all households. lam 0.62 = the project's DSGE hand-to-mouth "
         "share (pooled ratio2 posterior); 0.48 and 0.84 its range across the models estimated"
         + ("; 0.80 was added after 0.84 did not solve in the first run (section 4)" if "the central 2026 setting: rule lam 0.8" in T.columns
            else "") + ". Option (c) = markup pricing with "
         f"stickiness by sector, `mk_pass` 0, at h {H:g} and beta {BETA_C:g}.", "",
         "Growth effects: (1 + gap 2026) / (1 + gap 2025) - 1, points; gaps against the no-shock path. Data: PSA H1 2026 "
         "against the pre-shock trend (mean of H1 2024 and H1 2025 growth; "
         + (f"`outputs/{DATA_FILE.name.replace('.csv', '.md')}`" if DATA_FILE.exists()      # public version: a development
            else "a development script's table, not in this repository, so not available here")   # script's table
         + ") and the refit's targets (a design note, not included).", "",
         "## 1. The 2026 results", "", main_t.to_markdown(floatfmt=".3f"), "",
         "## 2. How the rule works (2026, four shocks against the no-shock path)", "",
         Tn.loc[rest, show].to_markdown(floatfmt=".4f"), ""]
    if CAP in T.index:
        L += ["Employment cap (four-shock path; short-run years where it binds): "
              + "; ".join(f"{c}: {T.loc[CAP, c]}" for c in show) + ".", ""]
    if OFF in ok and C62 in ok:
        lams = [c for c in ok if c.startswith("the central 2026 setting: rule lam")]
        rng = [g(c, "new poor 2026 (M, own baskets)") for c in lams]
        p0, p62 = g(OFF, "new poor 2026 (M, own baskets)"), g(C62, "new poor 2026 (M, own baskets)")
        q0, q62 = g(OFF, "new poor 2027 (M, own baskets)"), g(C62, "new poor 2027 (M, own baskets)")
        solved = ", ".join(c.split("rule lam ")[1] for c in lams)
        L += ["## 3. What the numbers say (computed)", "",
              f"- New poor 2026: {p0:.2f} M without the rule; {p62:.2f} M at lam 0.62 ({p62 - p0:+.2f} M, {(p62 - p0) / p0 * 100:+.0f}% "
              f"of the count); {min(rng):.2f}-{max(rng):.2f} M across the values of lam that solved ({solved}). 2027: {q0:.2f} M "
              f"against {q62:.2f} M ({q62 - q0:+.2f} M).",
              f"- Household consumption, 2026 growth effect: {g(OFF, 'C growth effect 2026 (pp)'):+.2f} points without the rule, "
              f"{g(C62, 'C growth effect 2026 (pp)'):+.2f} at lam 0.62 (data {data['C growth effect 2026 (pp)']}). The 2026 growth "
              f"effect: {g(OFF, 'growth effect 2026 (pp)'):+.2f} against {g(C62, 'growth effect 2026 (pp)'):+.2f} (data about -2.9).",
              f"- Exports {g(OFF, 'X growth effect 2026 (pp)'):+.2f} against {g(C62, 'X growth effect 2026 (pp)'):+.2f} (data "
              f"{data['X growth effect 2026 (pp)']}); imports {g(OFF, 'M growth effect 2026 (pp)'):+.2f} against "
              f"{g(C62, 'M growth effect 2026 (pp)'):+.2f} (data {data['M growth effect 2026 (pp)']}).", ""]
    L += ["## 4. Verification", ""]
    if VER in ok:
        if DIAG_FILE.exists():                       # public version: a development script's table (not in this repository)
            dd, kd = compare(Tn[VER], DIAG_FILE, DIAG_COL)
            L += [f"- The rule off at beta 10.513 against the flexible row of a development script's table "
                  f"(`outputs/{DIAG_FILE.name}`, column \"{DIAG_COL}\"): largest absolute difference over {len(dd)} common "
                  f"measures {abs(dd[kd]):.1e} ({kd})."]
        else:
            L += [f"- The rule off at beta 10.513 is not compared with the flexible row of `outputs/{DIAG_FILE.name}`: that "
                  "table is saved by a development script that is not in this repository."]
        if OFF in ok:
            L += [f"- The rule off at the calibration's beta {beta_c:.4f} against beta 10.513: growth effect "
                  f"{g(OFF, 'growth effect 2026 (pp)') - g(VER, 'growth effect 2026 (pp)'):+.1e} points, new poor 2026 "
                  f"{g(OFF, 'new poor 2026 (M, own baskets)') - g(VER, 'new poor 2026 (M, own baskets)'):+.1e} M."]
    if OPT_62 in ok and not PROTO_FILE.exists():     # public version: a development script's table (not in this repository)
        L += [f"- Option (c) with lam 0.62 is not compared with the prototype's row (`outputs/{PROTO_FILE.name}`): that table "
              "is saved by a development script that is not in this repository."]
    elif OPT_62 in ok:
        dv, kv = compare(Tn[OPT_62], PROTO_FILE, PROTO_COL)
        L += [f"- Option (c) with lam 0.62 through the engine against the prototype (`outputs/{PROTO_FILE.name}`, column "
              f"\"{PROTO_COL}\"): largest absolute difference over {len(dv)} common measures {abs(dv[kv]):.1e} ({kv}); growth effect "
              f"{g(OPT_62, 'growth effect 2026 (pp)'):+.4f} (prototype -2.9910), household consumption "
              f"{g(OPT_62, 'C growth effect 2026 (pp)'):+.4f} (prototype -2.8165)."]
    L += [("- Did not solve: " + "; ".join(f"{c}: {v}" for c, v in failed.items())) if failed else "- Every configuration solved.",
          "", "## 5. Caveats", "",
          "- The data's composition gap is not all the four shocks': the 2026 export upturn (the world electronics cycle) and part of "
          "the peso's weakness are shocks outside the four-shock counterfactual and do not belong in it. A model that fitted the "
          "expenditure data exactly would be wrong.",
          "- The peso channel is not in this run: the oil shock's own depreciation (+1.92% in 2026 against "
          "the pre-shock forecast in the inflation VAR) raised the peso value of remittances and of other foreign-currency income "
          "(remittances in pesos +8.2% in January-August 2026, BSP); the central 2026 case holds the peso at its pre-shock path.",
          "- One saving-rate factor for every household: the dissaving falls mostly on the top quintiles, which do most of the "
          "saving; the poorest groups' spending still follows their income. The rule therefore changes the poverty count through "
          "the economy-wide demand it keeps (jobs, pay, profits) and through prices, not by letting the poor dissave. A "
          "household-specific lam needs MPSADJ by household in cge.py (a later refinement).",
          "- The smoothers keep their baseline real spending in each short-run year (2025, 2026 and 2027 separately); household "
          "wealth is not modelled, so the dissaving is not paid back later. lam is a quarterly DSGE's share used for whole years.",
          "- Real investment stays fixed apart from public works (PSA's gross capital formation fell 11 points against trend); "
          "government consumption is real. Research only."]
    out = path.with_name(path.stem + ".md")
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(main_t.to_string())
    print("saved", out)


if __name__ == "__main__":
    if sys.argv[1:2] == ["md"]:
        write_md(sys.argv[2])
    else:
        main()
