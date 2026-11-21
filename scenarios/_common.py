"""Shared helpers for scenario scripts: paths, GDP-share conversion, household allocations, reports."""
from __future__ import annotations

import datetime as dt
import os
import sys
import tempfile
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from infinity_gem import paths                                     # noqa: E402
from infinity_gem import settings as _settings                     # noqa: E402
from infinity_gem.sam import SAM                                   # noqa: E402

# 0.3.10 (18 Oct 2026): which 2023 SAM the 2026 scenario scripts run on (about 4:20 PM: the 2026 scenarios on Infinity GEM's own SAM; "mixing SAMs ... would be a great idea"). Environment variable INFINITY_GEM_SCENARIO_SAM = "ifpri" (default: the 2026 scenarios of 17-18 Oct 2026, as before) or
# "own". It sets combined_revised.SAM_VARIANT, the SAM's GDP below, the wage-curve calibration file (calibration_file()) and a
# "_own" tag on every output (out_tag()), so the two sets of results never mix or overwrite each other.
SCENARIO_SAM = os.environ.get("INFINITY_GEM_SCENARIO_SAM", "ifpri").strip().lower()
# 0.4.0 (13 Nov 2026): the named setting the 2026 scenario scripts run under
# (combined_revised.Runs). Environment variable INFINITY_GEM_SETTING = a name in infinity_gem.settings.SETTINGS. Unset = settings.DEFAULT
# ("0.4 recommended": option (c) and the BSP rule) on the SAM it was fitted on, the project's v1.0 (INFINITY_GEM_SCENARIO_SAM=own: the 2026 scenarios'
# current case); on the other SAMs of the 2026 scenarios ("ifpri": the 2026 scenarios of 17-18 Oct 2026 and the static scripts; "own-0.5": the 2026 scenarios of 18-20 Oct 2026 and the runs of 11 Nov 2026) 0.4 is not defined, so they stay on "0.3 recommended", as before. INFINITY_GEM_SETTING="0.3 recommended" with INFINITY_GEM_SCENARIO_SAM=own
# (and INFINITY_GEM_SCENARIO_ENGINE={"hoarding": 0.85}) gives the central 2026 case on v1.0 as it was before 13 Nov 2026.
# 13 Nov 2026: settings.DEFAULT is now "0.4.1 recommended", so unset on SAM v1.0 = 0.4.1 (this
# line is unchanged: it reads DEFAULT); INFINITY_GEM_SETTING="0.4 recommended" reproduces the 0.4.0 runs of 13 Nov 2026 (check R4).
SETTING = os.environ.get("INFINITY_GEM_SETTING", "").strip() or (_settings.DEFAULT if SCENARIO_SAM == "own" else "0.3 recommended")
if SETTING not in _settings.SETTINGS:
    raise ValueError(f"INFINITY_GEM_SETTING must be one of {_settings.SETTINGS}, not {SETTING!r}")
# 6 Nov 2026: "own" now means Infinity GEM's own SAM v1.0, with its own tag "_ownv10", so it can never read v0.5's wage-curve calibration or outputs;
# "own-0.5" keeps v0.5 and its "_own" files (the 2026 scenarios of 18-20 Oct 2026).
if SCENARIO_SAM not in ("ifpri", "own", "own-0.5"):
    raise ValueError(f"INFINITY_GEM_SCENARIO_SAM must be 'ifpri', 'own' or 'own-0.5', not {SCENARIO_SAM!r}")
SAM_GDP = {"ifpri": 26160.604,      # nominal GDP in each 2023 SAM (₱ bn), = C + G + I + X - M; checked by the CGE
           "own": 24313.563,       # Infinity GEM's own SAM v1.0 = PSA's 2023 GDP (outputs/own_sam_v10_brief_row_1.0_coal+lng_psa_sam_20261025_0221.csv)
           "own-0.5": 24313.563}   # Infinity GEM's own SAM v0.5 = PSA's 2023 GDP (scenarios/sam_psa_sensitivity.py row, 18 Oct 2026)
SAM_GDP_2023 = SAM_GDP[SCENARIO_SAM]
# 0.3.11 (19 Oct 2026, about 1:45 PM): extra DynamicCGE assumptions for the 2026 scenario scripts, as JSON in the environment variable
# INFINITY_GEM_SCENARIO_ENGINE, e.g. {"hoarding": 0.85}. combined_revised.Runs applies them to every run, and out_tag() adds them to
# every output name (e.g. "_own_hoarding0.85"), so they never overwrite the 2026 scenarios' own results. Unset = as before.
import json                                                    # noqa: E402
SCENARIO_ENGINE = json.loads(os.environ.get("INFINITY_GEM_SCENARIO_ENGINE", "") or "{}")
# 0.4.2 (Wed 18 Nov 2026, about 6:15 AM: "yes, FIES 2025 becomes the default base for poverty figures"): the household
# survey of the 2026 scenario scripts' poverty figures (combined_revised.Runs builds its MicroLink on it). Environment variable INFINITY_GEM_FIES_BASE
# = "fies2023" or "fies2025"; unset = settings.DEFAULT_FIES_BASE ("fies2025"; infinity_gem/fies_base.default()). Every figure published before 18 Nov 2026 is on the FIES 2023 base: reproduce them with INFINITY_GEM_FIES_BASE=fies2023 (beside the other
# variables in CHANGELOG.md). out_tag() adds "_fies25" on the 2025 base, so the two never overwrite each other.
from infinity_gem import fies_base as _fies_base                   # noqa: E402
FIES_BASE = _fies_base.default()
PSA_GDP = {2025: 28009.93, "H1_2025": 13546.555,   # PSA nominal GDP (₱ bn): 2025 full year; H1 2025 (Q2 2026 NAP, Table 1.1)
           2026: 30519.0, 2027: 33180.0}           # nominal GDP implied by the DBCC 193rd joint statement (8 Jul 2026):
#   2026 disbursements ₱6.47 trillion = 21.2% of GDP (p. 4); FY 2027 budget ₱7.2 trillion =
#   21.7% of GDP (p. 4). 17 Oct 2026 (code review, finding I1): a peso amount of year y is the share of YEAR y's GDP, not 2025's;
#   before this every 2026-27 amount was divided by 2025 GDP, 8-14% too large relative to its year's economy.


def to_sam_units(amount_bn: float, gdp_bn: float) -> float:
    """Express a peso shock from another year as the same share of GDP in the 2023 SAM.
    (A shock of 0.85% of 2025 GDP becomes 0.85% of the SAM's GDP.) Pass the GDP of the amount's own year: PSA_GDP[y]."""
    return amount_bn / gdp_bn * SAM_GDP_2023


def equiv_2025(amount_bn: float, year: int) -> float:
    """A peso amount of `year` in 2025-peso equivalents: the same share of GDP, times 2025 GDP (the unit of every result)."""
    return amount_bn * PSA_GDP[2025] / PSA_GDP[year]


# 13 Nov 2026 (12 Nov; 13 Nov 3:15 AM: "bring the six research
# scripts onto the new peso conversion"): a model change in year y is valued as its share of year y's no-shock economy times 2025
# GDP (note 18's basis), not at the SAM year's scale. The same rule as combined_revised.peso_factor. INFINITY_GEM_SCENARIO_PESO=legacy keeps
# the constant factor (to_2025) of the runs before 12 Nov 2026. scenarios/combined_2025_2030.py stays on the constant factor on
# purpose (it reproduces the first draft).
PESO_BASIS = os.environ.get("INFINITY_GEM_SCENARIO_PESO", "year")
if PESO_BASIS not in ("year", "legacy"):
    raise ValueError(f"INFINITY_GEM_SCENARIO_PESO must be 'year' or 'legacy', not {PESO_BASIS!r}")


def peso_factor(base_table, year, to_2025: float) -> float:
    """2025-peso equivalents per model unit of a change in `year`. base_table: the no-shock run's table (first row = the SAM's
    own year, whose real GDP is the SAM's GDP); to_2025: the script's constant PSA_GDP[2025] / SAM GDP."""
    if PESO_BASIS == "legacy":
        return to_2025
    return to_2025 * float(base_table["real_gdp"].iloc[0]) / float(base_table.loc[year, "real_gdp"])


def gap_pesos_2025(compare_table, base_table, to_2025: float, years=None) -> float:
    """Sum of DynamicCGE.compare()'s gdp_gap_bn over `years` (default: every year row), each year at peso_factor."""
    rows = [y for y in compare_table.index if y != "cumulative" and (years is None or y in years)]
    return float(sum(float(compare_table.loc[y, "gdp_gap_bn"]) * peso_factor(base_table, y, to_2025) for y in rows))


def population_shares(year=2023) -> dict:
    p = paths.DATA_RAW / "sam" / f"003_IFPRI_SAM_PHL_{year}_POP.csv"
    df = pd.read_csv(p, encoding="utf-8-sig", skiprows=1 if year == 2023 else 0)
    df.columns = ["name", "code", "num", "shr"][: len(df.columns)]
    out = {}
    for _, r in df.iterrows():
        c = str(r["code"]).lower()
        for a, full in (("r", "rur"), ("u", "urb")):
            for q in range(1, 6):
                if c in (f"h_{full}{q}", f"hhd-{a}{q}"):
                    out[f"hhd-{a}{q}"] = float(str(r["num"]).replace(",", ""))
    tot = sum(out.values())
    return {k: v / tot for k, v in out.items()}


def bottom40_allocation() -> dict:
    ps = population_shares()
    q12 = ["hhd-r1", "hhd-u1", "hhd-r2", "hhd-u2"]
    return {h: ps[h] / sum(ps[k] for k in q12) for h in q12}


def sam_tag() -> str:
    """"" on IFPRI's SAM (as before), "_ownv10" on Infinity GEM's own SAM v1.0, "_own" on v0.5. No dot in the tag: with_suffix would eat it."""
    return {"ifpri": "", "own": "_ownv10", "own-0.5": "_own"}[SCENARIO_SAM]


def out_tag() -> str:
    """Suffix for output files of the 2026 scenario scripts: the SAM tag, "_set04" under the setting "0.4 recommended" (13 Nov 2026), plus any
    INFINITY_GEM_SCENARIO_ENGINE settings (e.g. "_hoarding0.85")."""
    fmt = lambda v: f"{v:g}" if isinstance(v, (int, float)) else str(v)
    st = {"0.4 recommended": "_set04", "0.4.1 recommended": "_set041", "0.4.2 candidate": "_set042c"}.get(SETTING, "")   # 0.4.0 (13 Nov 2026): 0.4 outputs never
    #                                        overwrite 0.3 ones; "_set041" (13 Nov 2026): nor 0.4's
    fb = "_fies25" if FIES_BASE == "fies2025" else ""          # 18 Nov 2026: new poor on the FIES 2025 base (the default)
    return sam_tag() + st + "".join(f"_{k}{fmt(v)}" for k, v in sorted(SCENARIO_ENGINE.items())) + fb


def calibration_file() -> Path:
    """The latest wage-curve calibration for SCENARIO_SAM (scenarios/calibrate_wage_curve.py): IFPRI's are named by date only
    (wage_curve_calibration_YYYYMMDD.csv), the project's carry the tag (wage_curve_calibration_YYYYMMDD_own.csv)."""
    pat = "wage_curve_calibration_" + "[0-9]" * 8 + sam_tag() + ".csv"
    f = sorted(paths.output_dir().glob(pat))
    if not f:
        raise FileNotFoundError(f"no wage-curve calibration for SAM {SCENARIO_SAM!r} ({pat}): run scenarios/calibrate_wage_curve.py first")
    return f[-1]


class Report:
    def __init__(self, title: str, slug: str):
        self.title, self.slug = title, slug
        self.lines = [f"# {title}", "", f"Generated {dt.datetime.now():%Y-%m-%d %H:%M} by `scenarios/{slug}.py` (Infinity GEM).",
                      "Model results, not forecasts: read them with the assumptions listed. Validation status: run "
                      "`checks/run_all_checks.py` first; do not use results if any check fails.", ""]

    def h(self, text):
        self.lines += ["", f"## {text}", ""]

    def p(self, text):
        self.lines += [text, ""]

    def table(self, df: pd.DataFrame, floatfmt=".3f"):
        self.lines += [df.to_markdown(floatfmt=floatfmt), ""]

    def save(self):
        out = paths.output_dir() / f"{self.slug}_{dt.date.today():%Y%m%d}{out_tag()}.md"   # 0.3.2: own folder if read-only; 0.3.10: SAM tag
        out.write_text("\n".join(self.lines), encoding="utf-8")
        print(f"Report saved: {out}")
        try:                     # tells "Run a scenario.bat" which report to open
            (Path(tempfile.gettempdir()) / "infinity_gem_last_report.txt").write_text(str(out), encoding="utf-8")
        except OSError:
            pass
        return out
