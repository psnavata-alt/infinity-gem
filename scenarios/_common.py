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
from infinity_gem.sam import SAM                                   # noqa: E402

# 0.3.10 (18 Oct 2026): which 2023 SAM the 2026 scenario scripts run on (about 4:20 PM: the 2026 scenarios on Infinity GEM's own SAM; "mixing SAMs ... would be a great idea"). Environment variable INFINITY_GEM_SCENARIO_SAM = "ifpri" (default: the 2026 scenarios of 17-18 Oct 2026, as before) or
# "own". It sets combined_revised.SAM_VARIANT, the SAM's GDP below, the wage-curve calibration file (calibration_file()) and a
# "_own" tag on every output (out_tag()), so the two sets of results never mix or overwrite each other.
SCENARIO_SAM = os.environ.get("INFINITY_GEM_SCENARIO_SAM", "ifpri").strip().lower()
if SCENARIO_SAM not in ("ifpri", "own"):
    raise ValueError(f"INFINITY_GEM_SCENARIO_SAM must be 'ifpri' or 'own', not {SCENARIO_SAM!r}")
SAM_GDP = {"ifpri": 26160.604,      # nominal GDP in each 2023 SAM (₱ bn), = C + G + I + X - M; checked by the CGE
           "own": 24313.563}       # Infinity GEM's own SAM v0.5 = PSA's 2023 GDP (scenarios/sam_psa_sensitivity.py row, 18 Oct 2026)
SAM_GDP_2023 = SAM_GDP[SCENARIO_SAM]
# 0.3.11 (19 Oct 2026, about 1:45 PM): extra DynamicCGE assumptions for the 2026 scenario scripts, as JSON in the environment variable
# INFINITY_GEM_SCENARIO_ENGINE, e.g. {"hoarding": 0.85}. combined_revised.Runs applies them to every run, and out_tag() adds them to
# every output name (e.g. "_own_hoarding0.85"), so they never overwrite the 2026 scenarios' own results. Unset = as before.
import json                                                    # noqa: E402
SCENARIO_ENGINE = json.loads(os.environ.get("INFINITY_GEM_SCENARIO_ENGINE", "") or "{}")
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
    """"" on IFPRI's SAM (as before), "_own" on Infinity GEM's own SAM."""
    return "" if SCENARIO_SAM == "ifpri" else "_" + SCENARIO_SAM


def out_tag() -> str:
    """Suffix for output files of the 2026 scenario scripts: the SAM tag, plus any INFINITY_GEM_SCENARIO_ENGINE settings (e.g. "_hoarding0.85")."""
    fmt = lambda v: f"{v:g}" if isinstance(v, (int, float)) else str(v)
    return sam_tag() + "".join(f"_{k}{fmt(v)}" for k, v in sorted(SCENARIO_ENGINE.items()))


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
