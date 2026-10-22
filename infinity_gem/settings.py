"""Named model settings (0.3.1): "0.2 published" and "0.3 recommended".

    from infinity_gem.settings import cge_model, dynamic_model
    m = cge_model("0.3 recommended", closure="keynesian", unemployed=("flab-n", "flab-p"), capital="fixed")
    d = dynamic_model("0.3 recommended", public_capital="low")

Design (8 Oct 2026): a named setting, not flipped code defaults; "0.2 published" stays selectable and check
R0 keeps passing; public capital shown as a low-high range; "all of them".

"0.2 published"   the settings behind every result published up to 7 Oct 2026: combined 2023 SAM, elasticities 0.8 /
                  2.0 / 2.0 for all sectors, Cobb-Douglas household demand, margins on the composite good; dynamic:
                  placeholder baseline, one mobile capital stock, long-run closure every year.
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

SETTINGS = ("0.3 recommended", "0.2 published")
DEFAULT = "0.3 recommended"
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
                        "0.3 recommended": ("flab-n", "flab-p", "flab-s")}
# The 2023 SAM used by "0.3 recommended" runs with the rice-split accounts (rice=True) when no sam_variant is given.
# 0.3.10 (18 Oct 2026): Infinity GEM's own 2023 SAM
# (paths.SAM_2023_OWN, version 0.5; tools/build_own_sam_2023.py). sam_variant="ifpri" gives IFPRI's
# rice-split SAM, the default up to 0.3.9 and the basis of the 2026 scenarios of 18 Oct 2026 (scenarios/combined_revised.py pins it). Runs without
# rice=True (the petroleum-split SAM, e.g. the Simulator's) and runs with sam_year (2024/2025) still use IFPRI-based SAMs:
# Infinity GEM's own SAM has the rice-split accounts and exists for 2023 only. "0.2 published" is unaffected (check R0).
DEFAULT_SAM_VARIANT = "own"


def short_run_closure(setting: str = DEFAULT) -> dict:
    """Closure arguments of the central short run under a named setting."""
    _check(setting)
    return dict(closure="keynesian", unemployed=SHORT_RUN_UNEMPLOYED[setting], capital="fixed")


PUBLIC_CAPITAL = {"off": None,
                  "low": dict(phi=0.083, kg_gdp=0.397),
                  "high": dict(phi=0.122, kg_gdp=0.296)}

DESCRIPTION = {
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
    SAM); 'ifpri' = IFPRI's SAM as published (rice-split, petroleum-split or updated), the default up to 0.3.9."""
    _check(setting)
    if sam_variant not in (None, "ifpri", "psa", "own"):
        raise ValueError(f"Unknown sam_variant '{sam_variant}' (None, 'ifpri', 'psa' or 'own')")
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
    if sam_variant == "own" and sam_year:
        raise ValueError("sam_variant='own' is a 2023 SAM; the 2024 and 2025 SAMs are not built on it yet")
    from .demand import les_briones2023
    from .elasticities import elasticity_set
    if sam_variant == "psa" and sam_year:                     #: 2024/2025 rebased on the PSA-consistent SAM
        path = paths.sam_updated(sam_year, base="psa")
    else:
        path = {"psa": paths.SAM_2023_RICE_PSA, "own": paths.SAM_2023_OWN}[sam_variant] if sam_variant else (
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
    hybrid: None = the setting's own choice (0.2 off, 0.3 on)."""
    _check(setting)
    if setting == "0.2 published":
        if public_capital != "off" or industry_baseline or rice or land != "mobile" or sam_year or sam_variant:
            raise ValueError("public capital, the industry baseline, rice, land, sam_year and sam_variant are 0.3 options")
        return dict(hybrid=bool(hybrid))
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


def dynamic_model(setting: str = DEFAULT, **kw):
    from .dynamic import DynamicCGE
    return DynamicCGE(**dynamic_kwargs(setting, **kw))
