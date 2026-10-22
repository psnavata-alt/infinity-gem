"""The central 2026 combined run on the PSA-consistent 2023 SAM (step 2) and on Infinity GEM's own 2023 SAM,
version 0.1; 18 Oct 2026.

The IFPRI 2023 SAM counts taxes on products twice, so its GDP is ₱1,847 bn and its household consumption ₱1,799 bn above
PSA's (tools/build_sam_psa_consistent.py; outputs/sam_psa_consistent_2023_*.md). This script runs scenarios/combined_revised.py's
central case (public capital low, flexible prices) twice with the same code: on the PSA-consistent variant (settings
sam_variant="psa") and on IFPRI's SAM, which must reproduce the central 2026 numbers (outputs/engine_sensitivities_parts/
variant_0.csv). The wage curve is recalibrated on each SAM to the central target (labour input 2026 = Okun's e x the model's
own 2026 growth effect). Peso amounts enter as shares of their year's GDP times the base SAM's GDP, so _common.SAM_GDP_2023
and combined_revised.TO_2025 are set to the SAM's own GDP for each run. NOT FOR CITATION.
Run:  py scenarios/sam_psa_sensitivity.py [psa] [own] [ifpri]   (about 10 minutes per SAM; default: psa and ifpri). The
table compares the latest saved row of each SAM (outputs/sam_psa_sensitivity_*_<sam>_row.csv), all from this script.
Option --raw-fies (18 Oct 2026, about 3 AM, the CPI-weights question): the same runs, but the poor are counted with
each family's raw FIES 2023 basket instead of the basket reconciled to the SAM (MicroLink's other variant, already computed in
every run). Option --fuel-split-map: MicroLink(fuel_split_map=True), chemicals out of UTILITIES and TRANSPORT (check ML2;
outputs/oil_passthrough_by_sam_20261018_0300.md). Since 18 Oct 2026, about 8:20 AM, that map is MicroLink's DEFAULT;
option --old-map (fuel_split_map=False) reproduces the 2026 scenario numbers of 17 Oct 2026. Every row records the map it used in 'base SAM'. Rows
are saved as *_<sam>[_fsmap|_oldmap][_rawfies]_row.csv; with any option the table outputs/sam_sensitivity_fies_baskets_<date>.md
sets every saved basket variant of each SAM side by side.
"""
import functools
import inspect
import sys

from _common import ROOT
import pandas as pd

sys.path.insert(0, str(ROOT / "preshock"))
import _common                                                                  # noqa: E402
from infinity_gem import paths, settings                                           # noqa: E402
import calibrate_wage_curve as CW                                               # noqa: E402
import combined_revised as CR                                                   # noqa: E402
import okun                                                                     # noqa: E402

KEYS = ("GDP gap 2025 (%)", "GDP gap 2026 (%)", "GDP gap 2027 (%)", "GDP gap 2030 (%)", "cumulative GDP loss 2025-2030 (₱ bn)",
        "consumer prices 2026 (%)", "new poor 2025 (M, own baskets)", "new poor 2026 (M, own baskets)",
        "new poor 2027 (M, own baskets)", "debt-to-GDP change 2030 (pp)")
NAMES = {"psa": "PSA-consistent 2023 SAM",
         "own": f"Infinity GEM's own 2023 SAM {paths.SAM_2023_OWN.stem.split('_own_')[-1]}",   # the version in use
         None: "IFPRI 2023 SAM (central 2026 setting)"}
RAW = "family inflation, raw FIES shares"
POOR_KEYS = ("new poor 2025 (M, own baskets)", "new poor 2026 (M, own baskets)", "new poor 2027 (M, own baskets)",
             "A: poor protected 2026 (M)", "B: poor protected 2027 (M)", "C: poor protected 2027 (M)",
             "consumer prices 2026 (%)", "GDP gap 2026 (%)", "wage-curve beta")


def _poor_raw(self, ref, sim, y):
    """As combined_revised.Runs.poor, with each family's raw FIES 2023 basket instead of the one reconciled to the SAM."""
    link = self.ml.link_variables(self.d.ms, ref.solutions[y], sim.solutions[y])
    e = self.ml.expected_results(link)["value"]
    return (e[f"{RAW}: change in poor persons"], e["group inflation (Infinity GEM published method): change in poor persons"],
            e[f"{RAW}: Bottom 30% (deciles 1-3): total loss per family (PHP a year)"])


STICKY = dict(sr_pricing="sticky", sr_stickiness=0.6)   # review D2, high (scenarios/engine_sensitivities.py)


def run(variant, stamp, baskets="reconciled", fuel_split_map=None, engine=None):
    """fuel_split_map: None = MicroLink's default (the fuel-split map since 18 Oct 2026); True or False = that map.
    engine: DynamicCGE options for every run (option --sticky = the high setting of review D2, prices rigid downward in the short run)."""
    base_dyn, base_cge, base_poor, base_ml = settings.dynamic_kwargs, settings.cge_model, CR.Runs.poor, CR.MicroLink
    gdp0, to0 = _common.SAM_GDP_2023, CR.TO_2025
    CR.dynamic_kwargs = lambda *a, **k: base_dyn(*a, **{**k, "sam_variant": variant or "ifpri"})   # 0.3.10: None = IFPRI explicitly
    CR.cge_model = lambda *a, **k: base_cge(*a, **{**k, "sam_variant": variant or "ifpri"})
    if baskets == "raw":
        CR.Runs.poor = _poor_raw
    if fuel_split_map is not None:
        CR.MicroLink = functools.partial(base_ml, fuel_split_map=fuel_split_map)
    used = fuel_split_map if fuel_split_map is not None else inspect.signature(base_ml).parameters["fuel_split_map"].default
    try:
        m = base_cge("0.3 recommended", rice=True, sam_variant=variant or "ifpri")
        b0 = m.solve()
        if not b0.ok:                                    # rigging audit part E: never use an unsolved benchmark
            raise RuntimeError(f"benchmark on {NAMES[variant]} did not solve ({b0.message}, residual {b0.residual_max:.2e})")
        sam_gdp = float(m.gdp(b0)["nominal_expenditure"])
        sam_c = float(m.gdp(b0)["C"])
        _common.SAM_GDP_2023 = sam_gdp                   # this run only: the base SAM's GDP
        CR.TO_2025 = CR.PSA_GDP[2025] / sam_gdp
        e = float(okun.estimates().loc["2006-2026, all quarters", "elasticity e"])
        R = CR.Runs("low", **(engine or {}))
        piece, src = R.pieces()
        if _common.SCENARIO_ENGINE:       # 19 Oct 2026: e.g. hoarding, where the Okun target is out of reach (hoarded workers stay employed);
            if (variant or "ifpri") != _common.SCENARIO_SAM:   # keep the SAM's calibration without it, as combined_revised's central run does
                raise SystemExit("with INFINITY_GEM_SCENARIO_ENGINE, run only the SAM named in INFINITY_GEM_SCENARIO_SAM (its wage-curve calibration is used)")
            beta = float(pd.read_csv(_common.calibration_file(), index_col=0).loc["central (e)", "beta"])
        else:
            beta = CW.calibrate(lambda s: s[0] - e * s[3], R, piece)
        R.d.a["wage_curve"] = beta
        pw = src["public works"]
        works = {2025: pw["2025"], 2026: pw["2026 central"], 2027: pw["2027 NEP x 2025 rate (central)"]}
        clean = R.run(set(), piece=piece)
        out = R.measures(clean, R.run(set(CR.SHOCKS), piece=piece), works=works, poor=True)[0]
        row = {"base SAM": NAMES[variant], "SAM nominal GDP (₱ bn)": sam_gdp, "SAM household consumption (₱ bn)": sam_c,
               "household consumption / GDP (%)": sam_c / sam_gdp * 100, "wage-curve beta": beta, **{k: out[k] for k in KEYS}}
        for ms in ("A", "B", "C"):
            p = R.measures(clean, R.run(set(CR.SHOCKS), ms, piece=piece), works=works,
                           extra_spend={2027: CR.CATCHUP} if ms == "C" else None)[0]
            cost = {"A": CR.equiv_2025(CR.AID_2026, 2026), "B": CR.equiv_2025(CR.AID_2027, 2027),
                    "C": CR.equiv_2025(CR.CATCHUP, 2027)}[ms]
            yr = 2026 if ms == "A" else 2027
            row[f"{ms}: poor protected {yr} (M)"] = out[f"new poor {yr} (M, own baskets)"] - p[f"new poor {yr} (M, own baskets)"]
            row[f"{ms}: output recovered per peso"] = (out["cumulative GDP loss 2025-2030 (₱ bn)"]
                                                       - p["cumulative GDP loss 2025-2030 (₱ bn)"]) / cost
    finally:
        CR.dynamic_kwargs, CR.cge_model, CR.Runs.poor, CR.MicroLink = base_dyn, base_cge, base_poor, base_ml
        _common.SAM_GDP_2023, CR.TO_2025 = gdp0, to0
    tag = ((variant or "ifpri") + {True: "_fsmap", False: "_oldmap", None: ""}[fuel_split_map] + ("_rawfies" if baskets == "raw" else "")
           + ("_sticky" if engine == STICKY else "") + _common.out_tag()[len(_common.sam_tag()):])   # + INFINITY_GEM_SCENARIO_ENGINE settings, if any
    row["base SAM"] += ", fuel-split FIES map" if used else ", old FIES map (setting of 17 Oct 2026)"
    if _common.SCENARIO_ENGINE:
        row["base SAM"] += f", INFINITY_GEM_SCENARIO_ENGINE {_common.SCENARIO_ENGINE} (wage curve as calibrated without it)"
    if engine:
        row["base SAM"] += ", sticky prices (D2 high)" if engine == STICKY else ", engine " + str(engine)
    if baskets == "raw":
        row["base SAM"] += ", raw FIES baskets"
    pd.Series(row).to_csv(paths.output_dir() / f"sam_psa_sensitivity_{stamp:%Y%m%d_%H%M}_{tag}_row.csv")   # saved first
    return row


BASKETS = {"": "reconciled to the SAM (MicroLink's map when run: the old one before 18 Oct 2026, 8:20 AM)",
           "_oldmap": "reconciled, old map (setting of 17 Oct 2026)", "_fsmap": "reconciled, fuel-split map",
           "_rawfies": "raw FIES baskets (map when run)", "_oldmap_rawfies": "raw FIES baskets, old map",
           "_fsmap_rawfies": "raw FIES baskets, fuel-split map"}


def baskets_table(stamp):
    """Every saved basket variant of each SAM side by side (options --raw-fies, --fuel-split-map)."""
    cols = {}
    for v in (None, "psa", "own"):
        for suffix, lab in BASKETS.items():
            r = latest_row((v or "ifpri") + suffix)
            if r and (suffix or any(latest_row((v or "ifpri") + s) for s in BASKETS if s)):
                name = str(r["base SAM"]).split(", ")[0].replace(" (central 2026 setting)", "")   # the label saved with the row
                cols[f"{name}: {lab}"] = {k: float(r[k]) for k in POOR_KEYS}
    t = pd.DataFrame(cols)
    print(t.to_string())
    f = paths.output_dir() / f"sam_sensitivity_fies_baskets_{stamp:%Y%m%d_%H%M}"
    t.to_csv(f.with_suffix(".csv"))
    L = [f"# The central 2026 run: poor counted with baskets reconciled to the SAM or with raw FIES baskets ({stamp:%d %B %Y, %H:%M})",
         "", "**NOT FOR CITATION** (Infinity GEM 0.3.9, the CPI-weights question). Script: "
         "`scenarios/sam_psa_sensitivity.py --raw-fies`. Same runs as `outputs/sam_psa_sensitivity_*`; only the household "
         "baskets used to count the poor differ. Reconciled (the method of the 2026 scenarios): every family's FIES 2023 spending on each "
         "category is rescaled so that the national basket equals the SAM's household consumption (MicroLink, default). Raw: "
         "each family's own FIES 2023 shares, the weighting behind PSA's CPI. Why it matters: "
         "`outputs/oil_passthrough_by_sam_20261018_0252.md`.", "", t.to_markdown(floatfmt=",.3f")]
    f.with_suffix(".md").write_text("\n".join(L), encoding="utf-8")
    print("saved", f.with_suffix(".md"))


def sticky_table(stamp):
    """Flexible against sticky short-run prices (review D2, high), each SAM, from the latest saved rows."""
    cols = {}
    for v in (None, "psa", "own"):
        for suffix, lab in (("_fsmap", "flexible prices"), ("_sticky", "sticky prices (D2 high)")):   # both with the fuel-split map
            r = latest_row((v or "ifpri") + suffix)
            if r and latest_row((v or "ifpri") + "_sticky"):
                cols[str(r["base SAM"]).split(", ")[0].replace(" (central 2026 setting)", "") + ": " + lab] = {k: float(r[k]) for k in POOR_KEYS}
    t = pd.DataFrame(cols)
    print(t.to_string())
    f = paths.output_dir() / f"sam_sensitivity_sticky_prices_{stamp:%Y%m%d_%H%M}"
    t.to_csv(f.with_suffix(".csv"))
    L = [f"# The central 2026 run with prices rigid downward in the short run, by SAM ({stamp:%d %B %Y, %H:%M})", "",
         "**NOT FOR CITATION** (Infinity GEM 0.3.9; own SAM; review D2). Script: `scenarios/sam_psa_sensitivity.py --sticky`. "
         "Sticky = DynamicCGE(sr_pricing='sticky', sr_stickiness=0.6), the high setting of review D2; the wage curve is recalibrated on each "
         "SAM and setting. Question: is Infinity GEM's own SAM's 2026 price fall (about -1.9% with flexible prices) a flexible-price result?",
         "", t.to_markdown(floatfmt=",.3f")]
    f.with_suffix(".md").write_text("\n".join(L), encoding="utf-8")
    print("saved", f.with_suffix(".md"))


def latest_row(tag):
    f = sorted(paths.output_dir().glob(f"sam_psa_sensitivity_*_{tag}_row.csv"))
    return pd.read_csv(f[-1], index_col=0).iloc[:, 0].to_dict() if f else None


def main():
    stamp = pd.Timestamp.today()
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    want = [None if a == "ifpri" else a for a in args] or ["psa", None]
    known = {"--raw-fies", "--fuel-split-map", "--old-map", "--sticky"}
    if flags - known or {"--fuel-split-map", "--old-map"} <= flags:
        raise SystemExit(f"options: {sorted(known)}; --fuel-split-map and --old-map exclude each other")
    if flags:
        fsm = True if "--fuel-split-map" in flags else False if "--old-map" in flags else None
        for v in want:
            run(v, stamp, baskets="raw" if "--raw-fies" in flags else "reconciled", fuel_split_map=fsm,
                engine=STICKY if "--sticky" in flags else None)
        if _common.SCENARIO_ENGINE:       # the tables compare rows without engine settings: rows only (tagged), no table
            return print("rows saved with the INFINITY_GEM_SCENARIO_ENGINE tag; tables not rebuilt")
        if "--sticky" in flags:
            return sticky_table(stamp)
        return baskets_table(stamp)
    for v in want:
        run(v, stamp)
    rows = {v: latest_row(v or "ifpri") for v in ("psa", "own", None)}
    rows = {v: {k: (x if k == "base SAM" else float(x)) for k, x in r.items()} for v, r in rows.items() if r}
    t = pd.DataFrame({str(r["base SAM"]): pd.Series(r, dtype=object) for v, r in rows.items()})   # labels saved with the rows
    num = [k for k in rows[None] if k != "base SAM"]
    for v in ("psa", "own"):
        if v in rows:
            t[f"difference ({v} minus IFPRI)"] = pd.Series({k: rows[v][k] - rows[None][k] for k in num}, dtype=object)
    ref = pd.read_csv(paths.output_dir() / "engine_sensitivities_parts" / "variant_0.csv", index_col=0).iloc[:, 0]
    t["saved central run (setting of 17 Oct 2026)"] = pd.Series({k: ref.get(k) for k in rows[None]}, dtype=object)
    print(t.to_string())
    f = paths.output_dir() / f"sam_psa_sensitivity_{stamp:%Y%m%d_%H%M}"
    t.to_csv(f.with_suffix(".csv"))
    L = [f"# The central 2026 run on the PSA-consistent 2023 SAM ({stamp:%d %B %Y, %H:%M})", "",
         "**NOT FOR CITATION** (Infinity GEM 0.3.9). Script: `scenarios/sam_psa_sensitivity.py`; "
         "SAMs: `tools/build_sam_psa_consistent.py` and `tools/build_own_sam_2023.py` (`outputs/sam_psa_consistent_2023_*.md`, "
         "`outputs/own_sam_2023_v0.1_*.md`). All columns run with the same code; "
         "the wage curve is recalibrated on each SAM to the central target; public capital low, flexible prices. The last "
         "column is the 2026 scenarios' saved central run, which the IFPRI column must reproduce.", "", t.to_markdown()]
    f.with_suffix(".md").write_text("\n".join(L), encoding="utf-8")
    print("saved", f.with_suffix(".md"))


if __name__ == "__main__":
    main()
