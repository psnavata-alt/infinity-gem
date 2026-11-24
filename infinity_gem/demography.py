"""Demography in labour supply (0.4.3, 21 Nov 2026). OPT-IN; nothing in
the engine imports this module; dynamic.py is NOT edited; no default changed. Design note: a design note (not included).

What the default does (dynamic.psa_labour_growth, unchanged): from 2027 on (2026 with y2026="trend") employment grows at the growth
rate of the population aged 15 and over, every age counted the same, with the skill shares trending.
What this module adds: the same path with the 15+ population replaced by EMPLOYMENT-WEIGHTED population: each age group and sex
counts at its own 2025 employment rate (employed / population). An ageing population then adds fewer workers than its 15+ head
count, because people aged 65 and over work at about a third of the prime-age rate. Age-sex employment rates are held at their
latest annual value (the no-change forecast; no hand-picked trend), so the change is the pure composition effect of PSA's
population projection.

Data (both on disk; nothing downloaded):
  population  PSA OpenSTAT 0021A3BPOP1, projected population based on the 2020 CPH, five-year age groups by sex, 2020-2030
              (data/raw/population/PSA_OpenSTAT_population_projections_2020CPH_2020-2030.csv, the file psa_labour_growth reads)
  employment  PSA OpenSTAT 0051B3FKEI5, employed persons by sex and age group, annual (LFS), 2005-2025
              (data/raw/lfs/PSA_OpenSTAT_0051B3FKEI5_LFS_employed_by_sex_and_age_2005-2026.csv, downloaded from PSA OpenSTAT
              through the PXWeb API on 14 Nov 2026; PSA update stamp 2026-11-06)
Use (opt-in):
  from infinity_gem.demography import documented_baseline_demographic
  DynamicCGE(..., **documented_baseline_demographic())        # instead of **documented_baseline()
Check: DM1 (checks/test_demography.py).
"""
from __future__ import annotations

import pandas as pd

from . import paths

LFS_FILE = "PSA_OpenSTAT_0051B3FKEI5_LFS_employed_by_sex_and_age_2005-2026.csv"
POP_FILE = "PSA_OpenSTAT_population_projections_2020CPH_2020-2030.csv"
# LFS age groups -> the projection's five-year groups
AGE_GROUPS = {"15 - 24 Years Old": ("15-19", "20-24"), "25 - 34 Years Old": ("25-29", "30-34"),
              "35 - 44 Years Old": ("35-39", "40-44"), "45 - 54 Years Old": ("45-49", "50-54"),
              "55 - 64 Years Old": ("55-59", "60-64"),
              "65 Years Old and Over": ("65-69", "70-74", "75-79", "80-84", "85+")}
SEXES = ("Male", "Female")
BASE_YEAR = 2025


def population() -> pd.DataFrame:
    """Projected population (thousands) by LFS age group (rows) and sex (columns Male, Female, Both Sexes), one block per year:
    MultiIndex (year, age group)."""
    pop = pd.read_csv(paths.DATA_RAW / "population" / POP_FILE, comment="#")
    rows = []
    for y in sorted(pop["year"].unique()):
        p = pop[pop["year"] == y]
        for g, five in AGE_GROUPS.items():
            r = {"year": int(y), "age": g}
            for s in SEXES + ("Both Sexes",):
                r[s] = float(p[(p["sex"] == s) & p["age_group"].isin(five)]["population_thousands"].sum())
            rows.append(r)
    return pd.DataFrame(rows).set_index(["year", "age"])


def employed(year=BASE_YEAR) -> pd.DataFrame:
    """LFS employed persons (thousands), annual, by LFS age group (rows) and sex (columns Male, Female, Both Sexes)."""
    d = pd.read_csv(paths.DATA_RAW / "lfs" / LFS_FILE, comment="#", dtype={"Year": str}, na_values=".")
    r = d[(d["Year"] == str(year)) & (d["Month"] == "Annual")]
    if r.empty or r.isna().all(axis=None):
        raise ValueError(f"demography.employed: no LFS annual figures for {year} in {LFS_FILE}")
    r = r.iloc[0]
    return pd.DataFrame({s: {g: float(r[f"{s} {g}"]) for g in AGE_GROUPS} for s in SEXES + ("Both Sexes",)})


def employment_rates(year=BASE_YEAR) -> pd.DataFrame:
    """Employed / projected population by age group and sex in `year` (LFS annual over PSA's 2020-CPH projection)."""
    e, p = employed(year), population().loc[year]
    return e[list(SEXES)] / p[list(SEXES)]


def growth_paths(base_year=BASE_YEAR, rates=None) -> pd.DataFrame:
    """Year-on-year growth, 2021-2030: 'pop15' = population aged 15+, both sexes (the default rule's driver, summed exactly as
    dynamic.psa_labour_growth sums it) and 'weighted' = employment-weighted population (each age-sex group, male and female, at its
    base-year employment rate). rates: a DataFrame like employment_rates() (None = employment_rates(base_year)); a table of equal
    rates gives back the 15+ growth within the projection's rounding (male + female vs both sexes; check DM1 T2)."""
    p = population()
    er = employment_rates(base_year) if rates is None else rates
    years = sorted(p.index.get_level_values(0).unique())
    raw = pd.read_csv(paths.DATA_RAW / "population" / POP_FILE, comment="#")
    p15 = raw[(raw["sex"] == "Both Sexes") & ~raw["age_group"].isin(["All Ages", "0-4", "5-9", "10-14"])].groupby("year")[
        "population_thousands"].sum()                            # = dynamic.psa_labour_growth's p15, line for line
    lvl15 = pd.Series({y: float(p15[y]) for y in years})
    lvlw = pd.Series({y: float((p.loc[y][list(SEXES)] * er).values.sum()) for y in years})
    out = pd.DataFrame({"pop15 level": lvl15, "weighted level": lvlw})
    out["pop15"] = out["pop15 level"] / out["pop15 level"].shift() - 1
    out["weighted"] = out["weighted level"] / out["weighted level"].shift() - 1
    out["difference (pp)"] = (out["weighted"] - out["pop15"]) * 100
    return out


def psa_labour_growth_demographic(base_year=BASE_YEAR, rates=None, **kw) -> dict:
    """dynamic.psa_labour_growth(**kw) with its projection years driven by employment-weighted population instead of the 15+
    head count. Exact: the default's projection step multiplies every labour type's level by the same population ratio, so each
    projected year's rate is rescaled by (1 + weighted) / (1 + pop15); 2024-2026 (observed) are untouched."""
    from .dynamic import psa_labour_growth
    base = psa_labour_growth(**kw)
    g = growth_paths(base_year, rates)
    first = 2026 if kw.get("y2026", "observed") == "trend" else 2027
    out = {}
    for y, d in base.items():
        if y >= first:
            f = (1 + float(g.loc[y, "weighted"])) / (1 + float(g.loc[y, "pop15"]))
            out[y] = {k: float((1 + v) * f - 1) for k, v in d.items()}
        else:
            out[y] = dict(d)
    return out


def documented_baseline_demographic(labour_2026="observed", base_year=BASE_YEAR) -> dict:
    """dynamic.documented_baseline() with labour_growth from psa_labour_growth_demographic (opt-in)."""
    from .dynamic import documented_baseline
    d = documented_baseline(labour="psa", labour_2026=labour_2026)
    d["labour_growth"] = psa_labour_growth_demographic(base_year=base_year, y2026=labour_2026)
    return d
