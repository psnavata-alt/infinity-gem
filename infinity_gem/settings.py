"""Named model settings (0.3.1): "0.2 published", "0.3 recommended" and (0.4.0, 13 Nov 2026) "0.4 recommended".

    from infinity_gem.settings import cge_model, dynamic_model
    m = cge_model("0.3 recommended", closure="keynesian", unemployed=("flab-n", "flab-p"), capital="fixed")
    d = dynamic_model("0.3 recommended", public_capital="low")
    d = dynamic_model("0.4.1 recommended", public_capital="low", rice=True, land="fixed")   # the default since 13 Nov 2026, about 5:25 PM

"0.4.2 candidate" (0.4.2, 15 Nov 2026, overnight; OPT-IN, reached only by name or INFINITY_GEM_SETTING="0.4.2
                  candidate"; NOT the default): "0.4.1 recommended" plus exactly six keys changed or added (OPTION_C_042C): the
                  re-fitted "evaluation 11" point (hoarding, sr_consumption htm, sr_markup_gap, sr_oil_pass, read from EVAL11_JSON),
                  the short-run export (CET) elasticities sr_cet = elasticities.short_run_cet(C) (check CET1) and the peso's
                  within-year pass-through into non-oil import prices sr_erpt = dynamic.SR_ERPT_ESTIMATE["phi"] (check ERP1).
                  Check R42 (checks/test_042_candidate.py). Evidence: a review note (not included).
"0.4.1 recommended" (0.4.1, 13 Nov 2026; on the findings on the 0.4 misses): "0.4 recommended" plus exactly two keys (OPTION_C_041): a ceiling of 1 on the markup gap rule's
                  pass-through (sr_markup_ceiling 1, the proportional markup; removes the gap rule's self-fulfilling boom branch,
                  check MC1; no effect on a slump) and the BSP rule with expected inflation = LAST year's gap (rule "pamph",
                  expected "lag": g2 on this year's inflation gap and 1 on last year's, the same adaptive expectation the rule's
                  real-rate gap uses; check MT1). Fitted values (h, lam, s, omega, beta) are 0.4's: no re-fit. Same SAM, closure and
                  rule reference as 0.4. Check R41 (checks/test_041_reference.py).
"0.4 recommended" (0.4.0, 13 Nov 2026): everything "0.3 recommended" has, plus, in the hybrid closure's short-run
                  years, option (c) of the short-run calibration at the "T15" point on Infinity GEM's own SAM v1.0 with the margin floor -1, and the
                  money block (the PAMPh-type BSP rule inside every path, theta 1.5). Values, each with its source:
                  OPTION_C_04 below; evidence: a review note (not included) (8 of 11 targets against 3)
                  and a review note (not included). Option (c) is a set of DYNAMIC short-run
                  assumptions (each anchored to that year's baseline solution), fitted on Infinity GEM's own SAM v1.0 with the rice-split
                  accounts: dynamic_kwargs("0.4 recommended") needs rice=True on that SAM and the hybrid closure. The static CGE
                  (cge_kwargs, cge_model, short_run_closure) is that of "0.3 recommended": option (c) has no fitted static form
                  (its markups, stickiness anchor, slack and pass-through rules are defined against a dynamic baseline year).
                  The BSP rule reacts to gaps against the no-shock path (BSP_RULE_REFERENCE; scenarios/combined_revised.Runs).
                  "0.3 recommended" and "0.2 published" are unchanged and reachable by name (checks R0, S2); the 2026 scenario scripts
                  take INFINITY_GEM_SETTING="0.3 recommended" (scenarios/_common.py) to reproduce the 2026 scenarios of 20 Oct 2026 and the runs of 11 Nov 2026.

Design (8 Oct 2026): a named setting, not flipped code defaults; "0.2 published" stays selectable and check
R0 keeps passing; public capital shown as a low-high range; "all of them".

"0.2 published"   the settings behind every result published up to 7 Oct 2026: combined 2023 SAM, elasticities 0.8 /
                  2.0 / 2.0 for all sectors, Cobb-Douglas household demand, margins on the composite good; dynamic:
                  placeholder baseline, one mobile capital stock, long-run closure every year, a scenario's amounts at
                  the 2023 SAM's scale in every year (transfer_scaling="legacy", 11 Nov 2026).
"0.3 recommended" every sourced 0.3 upgrade that combines with the others:
                  - 2023 SAM with refined petroleum split from chemicals (oil shocks enter as cpetr and crude
                    inside mining, infinity_gem/oil.py);
                  - Philippine elasticity set "ph" (GTAP value added; Kapuscinski and Warr 1999 Armington);
                  - LES household demand, Briones et al. 2023;
                  - IFPRI-style trade margins, margins="split" (verification Phase 3);
                  - sticky peso wages in the short run, wage="nominal" (14 Oct 2026: PSA LFS evidence;
                    removes the job gains from demand cuts that CPI-indexed wages produced; validation/labour_closures/);
                  - the short run lets workers of ALL skill levels lose jobs (0.3.6, 15 Oct 2026; PSA multiplier
                    about 1.1; SHORT_RUN_UNEMPLOYED below), in the static CGE's short run and the dynamic hybrid years;
                  dynamic, in addition: documented baseline (DBCC growth, PWT depreciation and capital, PSA labour growth
                  by skill), capital tied to its industry (putty-clay, omega 3), hybrid closure,
                  and public capital as a low-high range (IMF ICSD 2019, phi 0.083-0.122).
                  NOT included:
                  - home consumption as own produce (home="separate"): not yet combined with LES, and its effect
                    on the September 2026 results is negligible (outputs/home_consumption_sensitivity_20261008.md);
                  - the industry baseline is an OPTION (industry_baseline=True), not the default: it already
                    contains the actual 2025 construction slump, so a 2025 freeze must not be added on top of it.
Not for citation; see the 0.2 vs 0.3 comparison (outputs/settings_comparison_*.md).

Option rice=True (0.3.7; "0.3 recommended" only): the SAM with milled rice and corn split from processed food
(imports at PSA's 2023 customs value, duty = BOC rice tariff collections; tools/build_sam_rice_split.py), with Briones's
"Rice & corn" demand group for milled rice. Needed for El Nino and rice-policy runs; off by default, so results without it
are unchanged. For a drought add land="fixed" (static: CGE closure argument; dynamic: dynamic_kwargs(land="fixed")).
"""
from __future__ import annotations

from . import paths

SETTINGS = ("0.4.1 recommended", "0.4 recommended", "0.4.2 candidate", "0.3 recommended", "0.2 published")   # 0.4.1 first: 13 Nov 2026
#                                        "0.4.2 candidate" (0.4.2, 15 Nov 2026, overnight; OPT-IN, by name only; check R42): not the default
DEFAULT = "0.4.1 recommended"          # 13 Nov 2026 (0.4.1). Was "0.4 recommended" (0.4.0,
#                                        13 Nov 2026) and "0.3 recommended" (0.3.1 to 0.3.13)
OPTION_C_SETTINGS = ("0.4.1 recommended", "0.4 recommended", "0.4.2 candidate")   # 13 Nov 2026: the settings with
#                                        option (c) and the BSP rule (dynamic, SAM v1.0 only); code that treated "0.4 recommended" specially
#                                        tests membership here (scenarios/_common.py, combined_revised.py, central_case_04.py)
# The Simulator (app/) offers the settings it runs: its one-year CGE and its dynamic page use the petroleum-split IFPRI SAM without
# the rice accounts, where option (c) was not fitted; there "0.4 recommended" would equal "0.3 recommended" (static) or be refused
# (dynamic). Bringing 0.4 to the Simulator's dynamic page is a separate step (13 Nov 2026).
SIMULATOR_SETTINGS = ("0.3 recommended", "0.2 published")
# ---------------------------------------------------------------------------------------------------------------------------------
# "0.4 recommended" (13 Nov 2026): option (c) at the T15 point on Infinity GEM's own SAM v1.0, the margin floor -1 and the BSP rule. THE ONE PLACE
# these values live: dynamic_kwargs() reads them, and so does every 2026 scenario script through scenarios/combined_revised.Runs. Sources:
#   T15  = outputs/row83_refit_v10_2026_20261112_1236_point_T15params.json (the 28 Oct v0.9 optimum's parameters, run on v1.0 on
#          12 Nov 2026; check R4 compares every value below with that file);
#   F    = a review note (not included) (section 2(b): 8 of 11 targets; section 4: the rule);
#   FL   = outputs/row83_refit_v10_2026_20261112_1511_point_T15params_floor-1.csv (the same point with the margin floor -1: 8 of 11);
#   RF   = scenarios/row83_p2_p6_2026.py runs() and apply(): how each key maps onto DynamicCGE (the fits' own mapping).
OPTION_C_04 = {
    "sr_pricing": "markup",                 # RF runs(): markup pricing of non-farm home sales (T15 "pricing": "markup")
    "sr_markup_pass": 0.0,                  # RF runs(): mk_pass 0, the margin per unit fixed in pesos (F 2(a), option (c))
    "sr_stickiness": "sectoral",            # RF runs(): infinity_gem.stickiness.sectoral(the markup activities), resolved by DynamicCGE
    "hoarding": 0.9105515185484747,         # T15 "h": paid labour hoarding (F 2(b): h 0.911)
    "wage_curve": 9.9835205078125,          # T15 "beta" = outputs/wage_curve_calibration_20261111_ownv10.csv, "central (e)" (F 2(a))
    "sr_consumption": {"htm": 0.4770304101267516},   # T15 "lam": P1, the hand-to-mouth share (F 2(b): lam 0.477)
    "sr_markup_gap": 0.48180147831586817,   # T15 "s": P6, the pass-through's slope on the output gap (F 2(b): s 0.482)
    "sr_markup_floor": -1.0,                # FL / F section 3: margins absorb at most the whole markup (mkfloor=-1; 8 of 11)
    "employment_cap": "smooth",             # T15 "cap": "smooth" (check EC1)
    "sr_labour_slack": "lfs",               # T15 "slack": "lfs" = dynamic.lfs_labour_slack(y2026="observed") (RF apply(); check SL1)
    "sr_oil_pass": 0.8780494615572867,      # T15 "oil": omega, the within-year share of the world oil price (F 2(b): 0.878; OP1)
    "monetary": {"rule": "pamph", "theta": 1.5},   # T15 "bsp": 1.5 (the central theta, 23 Oct 2026); RF apply(): rule("pamph")
}
# "0.4.1 recommended" (13 Nov 2026; on the findings on the 0.4 misses):
# OPTION_C_04 plus exactly two keys. Sources: a development run's table (not included) (columns "0.4 + ceil1",
# "0.4 + lag"), checks MC1 and MT1. The fitted values (h, lam, s, omega, beta) are 0.4's (no re-fit under the lag rule yet).
OPTION_C_041 = {
    **OPTION_C_04,
    "sr_markup_ceiling": 1.0,               # MC1: the gap rule's pass-through at most the proportional markup (mk_pass 1); removes the
                                            # static boom branch (+5.9% at s 0.5, +6.1% at s 0.4818); 0.4 central unchanged to 1.1e-9
    "monetary": {"rule": "pamph", "theta": 1.5, "expected": "lag"},   # MT1: infinity_gem.monetary.rule("pamph", expected="lag"): g2 on
                                            # this year's inflation gap, 1 on last year's (E pi' adaptive, as the real-rate gap's);
                                            # 2026 rate 0.644 pp against the BSP's 0.489 average / 1.25 end-2026 (0.4: 1.448)
}
# "0.4.2 candidate" (0.4.2, 15 Nov 2026; OPT-IN, NOT
# the default; check R42, checks/test_042_candidate.py): OPTION_C_041 plus exactly six changes, each READ from its source, none typed:
#   - the re-fitted point "evaluation 11" of the re-fit under the short-run CET (h, lam, s, omega; beta 9.9835 and theta 1.5 held, as
#     0.4.1's): EVAL11_JSON below (scenarios/row134_overnight_items_2026.py refit variant=cet; 9 of 11 targets on the restated
#     investment target; a review note (not included) section 5);
#   - sr_cet: the short-run export (CET) elasticities, elasticities.short_run_cet(C) ("level": goods 0.535, services 0.045; check CET1),
#     resolved over the SAM's commodities in dynamic_kwargs (SR_CET_042C marks it here);
#   - sr_erpt: dynamic.SR_ERPT_ESTIMATE["phi"] (0.296, PSA import deflator; check ERP1).
EVAL11_JSON = "row134_overnight_items_2026_20261114_2321_refit_refit_cet_eval11.json"   # in paths.OUTPUTS
SR_CET_042C = "short_run_cet(C, 'level')"     # resolved by dynamic_kwargs over the SAM's commodities (elasticities.short_run_cet)
CANDIDATE_042 = "0.4.2 candidate"
# the eval-11 file's keys and the DynamicCGE assumption each sets (scenarios/row83_p2_p6_2026.apply, the fits' own mapping)
EVAL11_MAP = {"h": "hoarding", "lam": "sr_consumption", "s": "sr_markup_gap", "oil": "sr_oil_pass"}


def _option_c_042c() -> dict:
    """OPTION_C_041 with the eval-11 point read from EVAL11_JSON, sr_cet (SR_CET_042C) and sr_erpt = dynamic.SR_ERPT_ESTIMATE["phi"].
    The file's other keys must equal 0.4.1's (pricing, beta, bsp, slack, cap, margin floor), so nothing else moves."""
    import json
    from .dynamic import SR_ERPT_ESTIMATE
    j = json.loads((paths.OUTPUTS / EVAL11_JSON).read_text(encoding="utf-8"))
    same = {"pricing": OPTION_C_041["sr_pricing"], "beta": OPTION_C_041["wage_curve"], "bsp": OPTION_C_041["monetary"]["theta"],
            "slack": OPTION_C_041["sr_labour_slack"], "cap": OPTION_C_041["employment_cap"], "mkfloor": OPTION_C_041["sr_markup_floor"]}
    bad = [k for k, v in same.items() if j.get(k) != v]
    if bad:
        raise ValueError(f"'{CANDIDATE_042}': {EVAL11_JSON} differs from 0.4.1 in {bad}: the candidate changes only h, lam, s, omega")
    return {**OPTION_C_041,
            "hoarding": float(j["h"]),
            "sr_consumption": {"htm": float(j["lam"])},
            "sr_markup_gap": float(j["s"]),
            "sr_oil_pass": float(j["oil"]),
            "sr_cet": SR_CET_042C,
            "sr_erpt": float(SR_ERPT_ESTIMATE["phi"])}


try:                                          # a missing or changed source file makes only this setting unusable (dynamic_kwargs says why)
    OPTION_C_042C = _option_c_042c()
    OPTION_C_042C_ERROR = None
except Exception as _e:                       # noqa: BLE001
    OPTION_C_042C, OPTION_C_042C_ERROR = None, repr(_e)
OPTION_C = {"0.4 recommended": OPTION_C_04, "0.4.1 recommended": OPTION_C_041}   # 13 Nov 2026
if OPTION_C_042C is not None:
    OPTION_C[CANDIDATE_042] = OPTION_C_042C   # 15 Nov 2026 (opt-in; check R42)
# Not in option (c) at T15 (T15 "phi": null, "peso": null): sr_erpt (P2(b)) and the oil shock's own peso path (P2(a)) stay off.
# The BSP rule's reference (13 Nov 2026; a review note, not included): the rule reacts to the gaps of a path
# against the NO-SHOCK path (the counterfactual every result is measured against), so the no-shock path itself has zero gaps and a
# zero rate path. The engine measures gaps against its baseline (DynamicCGE.monetary_gaps); where the no-shock path is the baseline
# (a plain DynamicCGE) the two agree; scenarios/combined_revised.Runs passes the no-shock path with the policies as the reference.
BSP_RULE_REFERENCE = "no-shock path"
# public capital: the two extreme (phi, public capital / GDP) pairs span the guide's range (09, step E).
# phi: output elasticity of public capital, Bom and Ligthart (2014) meta-analysis, 0.083 short run, 0.122 long run;
# KG/GDP: IMF ICSD, 2019, 0.296 (constant 2017 PPP) and 0.397 (current pesos) (guide 08). The marginal return on public
# capital rises with phi / KG, so low = (0.083, 0.397) and high = (0.122, 0.296).
# Who can lose jobs in the short run (Keynesian closure). 0.3.6 (15 Oct 2026): under
# "0.3 recommended" workers of ALL skill levels can become unemployed, because PSA data favour it: the public-construction
# multiplier estimated from PSA quarterly accounts is about 1.1 after a year (preshock/freeze_multiplier_lp.py,
# pre-2020 sample, 90% band 0.85-1.37); '0.3 recommended' gives 0.94 with all skills and 0.36 with low and medium
# skills only (outputs/settings_comparison_20261015.md). "0.2 published" keeps low and medium skills (check R0).
SHORT_RUN_UNEMPLOYED = {"0.2 published": ("flab-n", "flab-p"),
                        "0.3 recommended": ("flab-n", "flab-p", "flab-s"),
                        "0.4 recommended": ("flab-n", "flab-p", "flab-s"),     # 13 Nov 2026: as 0.3 (the fits' closure)
                        "0.4.1 recommended": ("flab-n", "flab-p", "flab-s"),   # 13 Nov 2026: as 0.4
                        "0.4.2 candidate": ("flab-n", "flab-p", "flab-s")}     # 15 Nov 2026 (opt-in): as 0.4.1
# The 2023 SAM used by "0.3 recommended" runs with the rice-split accounts (rice=True) when no sam_variant is given.
# 0.3.10 (18 Oct 2026): Infinity GEM's own 2023 SAM
# (paths.SAM_2023_OWN, version 0.5 then; version 1.0 since 6 Nov 2026; tools/build_own_sam_2023.py). sam_variant="ifpri" gives IFPRI's
# rice-split SAM, the default up to 0.3.9 and the basis of the 2026 scenarios of 18 Oct 2026 (scenarios/combined_revised.py pins it). Runs without
# rice=True (the petroleum-split SAM, e.g. the Simulator's) and runs with sam_year (2024/2025) still use IFPRI-based SAMs:
# Infinity GEM's own SAM has the rice-split accounts and exists for 2023 only. "0.2 published" is unaffected (check R0).
DEFAULT_SAM_VARIANT = "own"
# 0.3.13 (23 Oct 2026): Infinity GEM's own 2023 SAM version 0.6 (tools/build_own_sam_2023.py; PSA's 2023 sector
# accounts for the rest of the world, government and corporations; a review note (not included)) is a
# research option reached only by naming it: sam_variant="own-0.6" (rice=True, 2023 only; check S7).
# 6 Nov 2026: the 'own' variant and so the default are now version 1.0 (paths.SAM_2023_OWN). sam_variant="own-0.5" keeps version 0.5, the
# basis of the 2026 scenarios of 18-20 Oct 2026, reachable by name.
SAM_VARIANTS = (None, "ifpri", "psa", "own", "own-0.5", "own-0.6")
# 0.4.2 (Wed 18 Nov 2026, about 6:15 AM: "yes, FIES 2025 becomes the default base for poverty figures"):
# the household survey every poverty figure starts from when no base is named (HouseholdDetail, MicroLink, Microsim and the scenario
# helpers that call them; infinity_gem/fies_base.py). "fies2025" = PSA's FIES 2025 public-use file and PSA's 2025 lines (check FB1);
# "fies2023" = PSA's FIES-LFS 2023 public-use file and PSA's 2023 lines, the base of EVERY figure published before 18 Nov 2026.
# Environment variable INFINITY_GEM_FIES_BASE (= "fies2023" or "fies2025") overrides it, as INFINITY_GEM_SETTING does for the setting
# (fies_base.default()); checks/run_all_checks.py and every reference check set INFINITY_GEM_FIES_BASE="fies2023", so the published and frozen
# results are reproduced unchanged; check R41F holds the new default's central case. The LFS earnings link needs PSA's FIES-LFS 2023
# member file and is refused on the 2025 base (pass base="fies2023").
DEFAULT_FIES_BASE = "fies2025"


def short_run_closure(setting: str = DEFAULT) -> dict:
    """Closure arguments of the central short run under a named setting."""
    _check(setting)
    return dict(closure="keynesian", unemployed=SHORT_RUN_UNEMPLOYED[setting], capital="fixed")


PUBLIC_CAPITAL = {"off": None,
                  "low": dict(phi=0.083, kg_gdp=0.397),
                  "high": dict(phi=0.122, kg_gdp=0.296)}

DESCRIPTION = {
    "0.4.2 candidate": "A CANDIDATE, not the default (15 Nov 2026): everything in 0.4.1 recommended, plus short-run export responses "
                       "estimated from PSA data (exports react less to prices within the year), a partial within-year pass-through "
                       "of the peso into non-oil import prices estimated from PSA's import prices, and the four fitted values (labour "
                       "hoarding, the consumption rule, the margin slope, the oil pass-through) re-fitted with them. Dynamic runs on "
                       "Infinity GEM's own SAM v1.0 only. Not for citation until reviewed.",
    "0.4.1 recommended": "Everything in 0.4 recommended, plus two corrections (13 Nov 2026): margins may rise at most in proportion "
                         "to cost in a boom (which removes a self-fulfilling boom solution), and the BSP rule's expected inflation "
                         "is last year's (so the policy rate rises gradually, as the BSP's did in 2026). Dynamic runs on Infinity GEM's own SAM "
                         "v1.0 only. Not for citation until reviewed.",
    "0.4 recommended": "Everything in 0.3 recommended, plus, in shock years, prices that keep their margins (markup pricing, sticky "
                       "falls, a margin floor), the short-run consumption rule, labour hoarding, LFS slack, a partial within-year "
                       "oil pass-through and the BSP's policy rule inside every path (option (c) of the short-run calibration at the T15 point on "
                       "Infinity GEM's own SAM v1.0; 8 of 11 data targets). Dynamic runs on Infinity GEM's own SAM v1.0 only. Not for citation until reviewed.",
    "0.3 recommended": "Sourced upgrades on: petroleum split from chemicals, Philippine elasticities, LES household demand, "
                       "IFPRI-style trade margins; over time also the documented baseline, capital tied to its industry, "
                       "job losses in shock years, and public capital as a low-high range. Not for citation until reviewed.",
    "0.2 published": "The settings behind the results published up to 7 October 2026 (check R0 reproduces them exactly).",
}


def _check(setting):
    if setting not in SETTINGS:
        raise KeyError(f"Unknown setting '{setting}' ({', '.join(SETTINGS)})")


def cge_kwargs(setting: str = DEFAULT, rice: bool = False, sam_year: int | None = None, sam_variant: str | None = None) -> dict:
    """Keyword arguments for CGE.from_sam(path, **kw) (without closure arguments). 'path' is the SAM file.
    rice: the rice-split SAM (0.3.7, "0.3 recommended" only).
    sam_year: None = the 2023 SAM (as before); 2024 or 2025 = the rice-split SAM updated to that year's PSA totals
    (0.3.8; tools/update_sam.py; needs rice=True).
    sam_variant: None = IFPRI's SAM as published (as before); "psa" = the PSA-consistent variant of the rice-split 2023 SAM
    (0.3.9: taxes on products counted once, household consumption = PSA's 2023 HFCE;
    tools/build_sam_psa_consistent.py); "own" = Infinity GEM's own 2023 SAM, version 0.1 (0.3.9: PSA's 2018 I-O moved
    to 2023, PSA national accounts and FIES 2023 as controls; tools/build_own_sam_2023.py; now version 0.3, household consumption by purpose = PSA's). Both need
    rice=True. With sam_year, 'psa' gives the 2024 or 2025 SAM updated from the PSA-consistent one (tools/update_sam.py --base psa); 'own' is 2023 only.
    0.3.10 (18 Oct 2026): with rice=True and no sam_year, None now means DEFAULT_SAM_VARIANT ('own', Infinity GEM's own
    SAM); 'ifpri' = IFPRI's SAM as published (rice-split, petroleum-split or updated), the default up to 0.3.9.
    0.3.13 (23 Oct 2026): 'own-0.6' = Infinity GEM's own 2023 SAM version 0.6 (paths.sam_own("0.6"); research, opt-in; rice=True,
    2023 only). 6 Nov 2026: 'own' (and the default) = version 1.0; 'own-0.5' = version 0.5 by name.
    13 Nov 2026: "0.4 recommended" = "0.3 recommended" here (option (c) is a set of dynamic short-run assumptions; module notes);
    "0.4.1 recommended" too (13 Nov 2026)."""
    _check(setting)
    if setting in OPTION_C_SETTINGS:
        setting = "0.3 recommended"
    if sam_variant not in SAM_VARIANTS:
        raise ValueError(f"Unknown sam_variant '{sam_variant}' (None, 'ifpri', 'psa', 'own', 'own-0.5' or 'own-0.6')")
    if setting == "0.2 published":
        if rice or sam_year or sam_variant:
            raise ValueError("rice=True, sam_year and sam_variant are 0.3 options")
        return dict(path=None)
    if sam_variant is None and rice and not sam_year:      # 0.3.10: Infinity GEM's own 2023 SAM by default (18 Oct 2026)
        sam_variant = DEFAULT_SAM_VARIANT
    if sam_variant == "ifpri":                             # IFPRI's SAM, as every run used up to 0.3.9
        sam_variant = None
    if sam_year and not rice:
        raise ValueError("sam_year needs rice=True (the updated SAMs are built from the rice-split SAM)")
    if sam_variant and not rice:
        raise ValueError("sam_variant needs rice=True (the variants have the rice-split SAM's accounts)")
    if sam_variant in ("own", "own-0.5", "own-0.6") and sam_year:
        raise ValueError(f"sam_variant='{sam_variant}' is a 2023 SAM; the 2024 and 2025 SAMs are not built on it yet")
    from .demand import les_briones2023
    from .elasticities import elasticity_set
    if sam_variant == "psa" and sam_year:                     #: 2024/2025 rebased on the PSA-consistent SAM
        path = paths.sam_updated(sam_year, base="psa")
    else:
        path = {"psa": paths.SAM_2023_RICE_PSA, "own": paths.SAM_2023_OWN,
                "own-0.5": paths.sam_own("0.5"), "own-0.6": paths.sam_own("0.6")}[sam_variant] if sam_variant else (   # 0.3.13: v0.6 by name only
            paths.sam_updated(sam_year) if sam_year else (paths.SAM_2023_RICE if rice else paths.SAM_2023_PETR))
    return dict(path=path, elasticities=elasticity_set("ph"),
                les=les_briones2023(rice_split=rice), margins="split", wage="nominal")


def cge_model(setting: str = DEFAULT, rice: bool = False, sam_year: int | None = None, sam_variant: str | None = None,
              **closure):
    """A calibrated CGE under a named setting; closure arguments (closure, unemployed, capital, land) pass through."""
    from .cge import CGE
    kw = cge_kwargs(setting, rice, sam_year, sam_variant)
    return CGE.from_sam(kw.pop("path"), **kw, **closure)


def dynamic_kwargs(setting: str = DEFAULT, public_capital: str = "off", industry_baseline: bool = False,
                   hybrid: bool | None = None, rice: bool = False, land: str = "mobile", sam_year: int | None = None,
                   sam_variant: str | None = None) -> dict:
    """Keyword arguments for DynamicCGE(**kw). public_capital: 'off', 'low' or 'high' (0.3 only).
    industry_baseline: PSA industry growth 2024-2025 (contains the 2025 slump: do not add a 2025 freeze).
    hybrid: None = the setting's own choice (0.2 off, 0.3 on).
    13 Nov 2026, "0.4 recommended": the "0.3 recommended" arguments plus option_c_kwargs() (OPTION_C_04, resolved); needs rice=True
    on Infinity GEM's own SAM v1.0 (sam_variant None or 'own', no sam_year) and the hybrid closure, where the values were fitted.
    "0.4.1 recommended" (13 Nov 2026): the same, with OPTION_C_041."""
    _check(setting)
    if setting in OPTION_C_SETTINGS:              # 13 Nov 2026: 0.4.1 as 0.4 (was == "0.4 recommended")
        if not rice or sam_year or sam_variant not in (None, "own") or hybrid is False:
            raise ValueError(f"'{setting}' (option (c) and the BSP rule) is fitted on Infinity GEM's own SAM v1.0 with the rice-split accounts "
                             "in the hybrid closure: use rice=True, sam_variant None or 'own', no sam_year, hybrid None or True; "
                             "for other SAMs or closures name '0.3 recommended'")
        if "v1.0" not in paths.SAM_2023_OWN.name:
            raise ValueError(f"'{setting}' is fitted on Infinity GEM's own SAM v1.0; paths.SAM_2023_OWN is {paths.SAM_2023_OWN.name} "
                             "(name '0.3 recommended' for another version)")
        d = dynamic_kwargs("0.3 recommended", public_capital, industry_baseline, hybrid, rice, land, sam_year, sam_variant)
        d.update(option_c_kwargs(setting))
        if d.get("sr_cet") == SR_CET_042C:        # 15 Nov 2026 ("0.4.2 candidate"): the short-run CET over the SAM's commodities
            from .elasticities import short_run_cet
            d["sr_cet"] = short_run_cet(d["sam"].accounts("c"), "level")
        return d
    if setting == "0.2 published":
        if public_capital != "off" or industry_baseline or rice or land != "mobile" or sam_year or sam_variant:
            raise ValueError("public capital, the industry baseline, rice, land, sam_year and sam_variant are 0.3 options")
        # 11 Nov 2026: 0.2's own treatment of a scenario's amounts (at the 2023 SAM's scale in every year; dynamic.py transfer_scaling)
        return dict(hybrid=bool(hybrid), transfer_scaling="legacy")
    from .dynamic import documented_baseline, psa_industry_growth
    from .sam import SAM
    kw = cge_kwargs(setting, rice, sam_year, sam_variant)
    d = dict(sam=SAM.load_for_model(kw.pop("path")), **kw, **documented_baseline(), land=land,
             capital_allocation="putty-clay", hybrid=True if hybrid is None else bool(hybrid),
             public_capital=PUBLIC_CAPITAL[public_capital],
             short_run_unemployed=SHORT_RUN_UNEMPLOYED[setting])            # 0.3.6: all skill levels
    if industry_baseline:
        d["industry_targets"] = psa_industry_growth()
    if sam_year:                                  # 0.3.8: the path starts in the SAM's own year
        d["base_year"] = sam_year
        d["growth"] = {y: g for y, g in d["growth"].items() if y > sam_year}
        if industry_baseline:
            d["industry_targets"] = {y: v for y, v in d["industry_targets"].items() if y > sam_year}
    return d


def option_c_kwargs(setting: str = "0.4 recommended") -> dict:
    """13 Nov 2026: OPTION_C_04 as DynamicCGE keyword arguments (fresh copies): the LFS slack computed (lfs_labour_slack, y2026
    "observed", as scenarios/row83_p2_p6_2026.apply), the BSP rule's coefficients read (infinity_gem.monetary.rule); "sectoral"
    stickiness is resolved by DynamicCGE once its short-run model is built (the markup activities).
    setting (13 Nov 2026): "0.4 recommended" (default, OPTION_C_04, as before) or
    "0.4.1 recommended" (OPTION_C_041: its monetary "expected" is passed to infinity_gem.monetary.rule; the ceiling passes as given)."""
    import copy
    from .dynamic import lfs_labour_slack
    from .monetary import rule
    if setting == CANDIDATE_042 and OPTION_C_042C is None:   # 15 Nov 2026: its source file is missing or changed
        raise ValueError(f"'{CANDIDATE_042}' cannot be built: {OPTION_C_042C_ERROR}")
    if setting not in OPTION_C:
        raise KeyError(f"option_c_kwargs: '{setting}' has no option (c) values ({', '.join(OPTION_C)})")
    kw = copy.deepcopy(OPTION_C[setting])
    if kw["sr_labour_slack"] == "lfs":
        kw["sr_labour_slack"] = dict(lfs_labour_slack(y2026="observed"))
    mo = kw["monetary"]
    r = rule(mo["rule"]) if "expected" not in mo else rule(mo["rule"], expected=mo["expected"])   # 0.4: the call as before
    kw["monetary"] = {"rule": r, "theta": float(mo["theta"])}
    return kw


def dynamic_model(setting: str = DEFAULT, **kw):
    from .dynamic import DynamicCGE
    return DynamicCGE(**dynamic_kwargs(setting, **kw))
