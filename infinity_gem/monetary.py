"""The money block (0.3.12, 20 Oct 2026): policy-rule coefficients for DynamicCGE.monetary_scenario(), by name.

The rule is the quarterly partial adjustment i_q = rho i_{q-1} + (1 - rho)(phi_pi x inflation gap + phi_x x output gap + phi_e x peso
depreciation gap), rates and inflation in pp a year, phi_x in pp a year per % of output gap (DynamicCGE.annual_rule integrates it
over a year). Nothing here is typed in: the coefficients are read from the saved estimation chains or solved from the QPM's match.

- "pamph": the quarterly projection model of research/dsge/qpm.py calibrated to the BSP's PAMPh responses (BSP WPS 2020-12):
  i = g1 i_lag + (1 - g1)(E pi' + g2 pi + g3 ygap). With expected inflation moving with current inflation, the coefficient on the
  inflation gap is 1 + g2; phi_e = 0.
- "dsge": the candidate DSGE research/dsge/soe_htmu.py at the posterior mean of its pooled chains (2002-2026, COVID quarters
  missing, STL-adjusted GDP; milestone 19): rho_i, phi_pi, phi_e as estimated; phi_x times 4, because the model's rate is a
  quarterly rate and its output gap a fraction (4 x phi_x pp a year per % of output).
- "oil0.73", "oil0.85": the oil model research/dsge/soe_oilw.py with the domestic Calvo parameter calibrated at 0.73 (the BSP's
  micro price data, WPS 2020-02) or 0.85 (the middle case; milestone 21b), pooled chains of that specification.
The chain files are outputs/dsge_ph_<model>_draws_<stamp><tag>.npy; the parameter names come from the matching estimation note
outputs/dsge_ph_<model>_estimation_<stamp><tag>.md (its posterior table), so no research module is imported for them.
- "pamph_annex3" (0.4.3, 21 Nov 2026; OPT-IN, no setting uses it): PAMPh's OWN calibrated rule, eq. (9)
  p. 13 with Annex 3 p. 30 of BSP WPS 2020-12 (gamma1 inertia 0.70, gamma2 inflation deviation 1.50, gamma3 output gap 0.50),
  in the same mapping as "pamph" (rho = g1, phi_pi = 1 + g2, phi_x = g3, phi_e = 0). The values are read, not typed: from the
  defaults of the Params dataclass in research/qpm/qpm_ph.py, where they are transcribed with their page; read with
  ast, so nothing is imported or run. "pamph" (above) fits PAMPh's impulse-response CHARTS (g1 0.721, g2 1.05, g3 0.10): its
  output-gap response is a fifth of the table's (research/qpm/RESEARCH_NOTE_row146_QPM_21Nov2026.md, section 5c).
- "pamph_estimated" (same date; OPT-IN, research): PAMPh's structure with g1, g2, g3 ESTIMATED on Philippine data 2002Q1-2026Q3
  (posterior mode, variant E of research/qpm/run_qpm.py; g1 0.92, g2 1.69, g3 0.46), read from the run the research note
  reports, QPM_ESTIMATE below. Same mapping. Not for citation (the note's section 7).
Check MP2 (checks/test_monetary_annex3.py); design note a design note (not included).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
SPECS = {"dsge": ("htmu", "_w1_ratio_long_stl_seed*", ("long", "stl")),
         "oil0.73": ("oilw", "_w1_ratio_long_stl_thfix0.73*", ("long", "stl", "thfix0.73")),
         "oil0.85": ("oilw", "_w1_ratio_long_stl_thfix0.85*", ("long", "stl", "thfix0.85"))}
# 0.4.3 (21 Nov 2026; opt-in): PAMPh's own rule and its estimated variant (module notes; check MP2)
QPM_RULES = ("pamph_annex3", "pamph_estimated")
QPM_PH = ROOT / "research" / "qpm" / "qpm_ph.py"           # Params defaults = PAMPh Annex 3 (BSP WPS 2020-12, pp. 30-31)
QPM_ESTIMATE = ROOT / "research" / "qpm" / "outputs" / "qpm_params_20261121_0109.json"   # a research run (not in this release), variant "E"


def _qpm_rule_values(name: str) -> tuple:
    """g1, g2, g3 of PAMPh's rule for "pamph_annex3" (the Params defaults of research/qpm/qpm_ph.py, read with ast: nothing is
    imported or run) or "pamph_estimated" (variant "E" of QPM_ESTIMATE), and a source line."""
    import ast
    import json
    if not (QPM_PH if name == "pamph_annex3" else QPM_ESTIMATE).exists():   # public version: research/qpm is not included
        raise ValueError(f"rule({name!r}) reads research/qpm/ (PAMPh's Annex 3 values or a research estimate), which is not "
                         "in this release; the default rule is rule('pamph')")
    if name == "pamph_annex3":
        tree = ast.parse(QPM_PH.read_text(encoding="utf-8"))
        cls = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Params"]
        if not cls:
            raise ValueError(f"{QPM_PH}: no Params class (PAMPh's Annex 3 values)")
        vals = {s.target.id: ast.literal_eval(s.value) for s in cls[0].body
                if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name) and s.value is not None}
        g = {k: float(vals[k]) for k in ("g1", "g2", "g3")}
        src = ("PAMPh's own calibration (BSP WPS 2020-12, eq. (9) p. 13, Annex 3 p. 30: gamma1, gamma2, gamma3), read from "
               "research/qpm/qpm_ph.py Params")
    else:
        g = {k: float(json.loads(QPM_ESTIMATE.read_text(encoding="utf-8"))["E"][k]) for k in ("g1", "g2", "g3")}
        src = (f"PAMPh's rule estimated on Philippine data 2002Q1-2026Q3 (posterior mode, variant E; research only, not for "
               f"citation): research/qpm/outputs/{QPM_ESTIMATE.name}")
    if not (0.0 <= g["g1"] < 1.0 and g["g2"] >= 0.0 and g["g3"] >= 0.0):
        raise ValueError(f"{name}: coefficients out of range {g}")
    return g, src


def _names(md: Path) -> list:
    """Parameter names in the order of the chain's columns: the first column of the estimation note's posterior table."""
    names = []
    for ln in md.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*([A-Za-z_][A-Za-z0-9_]*)\s*\|\s*(beta|gamma|normal|invgamma|uniform)\b", ln)
        if m:
            names.append(m.group(1))
    return names


def chains(name: str):
    """The chain files of a named specification and their parameter names (checked against the columns)."""
    model, pat, must = SPECS[name]
    files = [f for f in sorted(OUT.glob(f"dsge_ph_{model}_draws_*{pat}.npy"))
             if all(f"_{t}" in f.stem for t in must) and ("_igrea" not in f.stem) and ("_thhi" not in f.stem)
             and (("_thfix" in f.stem) == any(t.startswith("thfix") for t in must))]
    if not files:
        raise FileNotFoundError(f"no chains for {name!r} in {OUT} (pattern dsge_ph_{model}_draws_*{pat}.npy)")
    md = OUT / files[0].name.replace("_draws_", "_estimation_").replace(".npy", ".md")
    names = _names(md)
    D = np.vstack([np.load(f) for f in files])
    if len(names) != D.shape[1]:
        raise ValueError(f"{md.name}: {len(names)} parameter names for {D.shape[1]} chain columns")
    return files, names, D


def rule(name: str = "pamph", expected: str = "current") -> dict:
    """Coefficients for DynamicCGE.monetary_scenario(rule=...): {"rho", "phi_pi", "phi_x", "phi_e", "freq": "quarterly", "source"}.
    expected (0.4.1, 13 Nov 2026; the QPM rules only: "pamph", and since 21 Nov 2026 "pamph_annex3" and
    "pamph_estimated"; opt-in): how the QPM's expected-inflation term E pi' enters the annual
    target. "current" (default, as before): E pi' moves one-for-one with this year's inflation gap, phi_pi = 1 + g2. "lead": E pi' is
    the path's NEXT-year inflation gap (model-consistent, as in the QPM, where E pi' is the rational expectation): phi_pi = g2 on
    this year's gap and phi_pi_lead = 1 on next year's. "lag": E pi' = LAST year's gap (adaptive): phi_pi = g2, phi_pi_lag = 1."""
    if expected not in ("current", "lead", "lag"):
        raise ValueError("expected must be 'current', 'lead' or 'lag'")
    if name == "pamph":
        sys.path.insert(0, str(ROOT / "research" / "dsge"))
        import qpm
        p, *_ = qpm.match_pamph()
        r = {"rho": float(p.g1), "phi_pi": 1.0 + float(p.g2), "phi_x": float(p.g3), "phi_e": 0.0, "freq": "quarterly",
             "source": "QPM calibrated to PAMPh (research/dsge/qpm.py match_pamph; inflation coefficient 1 + g2)"}
        if expected != "current":
            r["phi_pi"] = float(p.g2)
            r["phi_pi_" + expected] = 1.0
            r["source"] = (f"QPM calibrated to PAMPh (research/dsge/qpm.py match_pamph): g2 on this year's inflation gap and 1 on "
                           f"{'next' if expected == 'lead' else 'last'} year's (E pi' {'model-consistent' if expected == 'lead' else 'adaptive'})")
        return r
    if name in QPM_RULES:                    # 0.4.3 (21 Nov 2026; opt-in, check MP2): the same mapping as "pamph"
        g, src = _qpm_rule_values(name)
        r = {"rho": g["g1"], "phi_pi": 1.0 + g["g2"], "phi_x": g["g3"], "phi_e": 0.0, "freq": "quarterly",
             "source": src + "; inflation coefficient 1 + g2"}
        if expected != "current":
            r["phi_pi"] = g["g2"]
            r["phi_pi_" + expected] = 1.0
            r["source"] = (src + f"; g2 on this year's inflation gap and 1 on {'next' if expected == 'lead' else 'last'} year's "
                                 f"(E pi' {'model-consistent' if expected == 'lead' else 'adaptive'})")
        return r
    if expected != "current":
        raise ValueError("expected='lead'/'lag' applies to the QPM's rules ('pamph', 'pamph_annex3', 'pamph_estimated'); the DSGE "
                         "rules have no expected-inflation term")
    if name not in SPECS:
        raise ValueError(f"rule must be one of pamph, {', '.join(QPM_RULES)}, {', '.join(SPECS)}")
    files, names, D = chains(name)
    mean = dict(zip(names, D.mean(0)))
    return {"rho": float(mean["rho_i"]), "phi_pi": float(mean["phi_pi"]), "phi_x": 4.0 * float(mean["phi_x"]),
            "phi_e": float(mean.get("phi_e", 0.0)), "freq": "quarterly",
            "source": f"posterior mean of {len(files)} chain(s): {', '.join(f.name for f in files)}"}


# ---------------------------------------------------------------------------------------------------------------------------------
# 0.4.1 (13 Nov 2026; opt-in, nothing reads these by default): the BSP's observed 2026 decisions and the within-year
# timing of a shock, for DynamicCGE.monetary_scenario(observed=...) and rule["quarter_weights"]. Check MT1.
BIS_DAILY = (ROOT / "data" / "raw" / "macro" / "BIS_WS_CBPOL_PH_policy_rate_daily_1999-2026_downloaded_2026-11-12"
             / "BIS_WS_CBPOL_D.PH_daily_1999-latest.csv")     # BIS WS_CBPOL, Philippines, daily (the BSP's target RRP rate); SOURCE.md there
PRE_SHOCK_DECISION = ("2026-02-20", 4.25)  # the BSP's last decision before the 2026 oil shock (in the file: 4.50 -> 4.25 on 20 Feb 2026)


def bsp_daily(file: Path = BIS_DAILY):
    """The BSP's policy rate by day (%, forward-filled between decisions) from the BIS file, and the file's last observation."""
    import pandas as pd
    d = pd.read_csv(file, usecols=["TIME_PERIOD", "OBS_VALUE"])
    s = pd.Series(pd.to_numeric(d["OBS_VALUE"], errors="coerce").values, index=pd.to_datetime(d["TIME_PERIOD"])).dropna()
    return s, s.index[-1]


def bsp_observed_gap(year: int = 2026, pre_shock=PRE_SHOCK_DECISION, file: Path = BIS_DAILY) -> dict:
    """The BSP's policy-rate gap in `year` against the rate held at its last pre-shock decision (the convention of a development script; here from the BIS file): the year's daily average of actual less
    counterfactual ("i"), its end-of-year value ("i_end"), the quarterly averages, and the assumption for the days after the file's
    last observation (the last decision held: no decision on file). Before the pre-shock decision's date the gap is zero."""
    import pandas as pd
    s, last = bsp_daily(file)
    days = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    act = s.reindex(s.index.union(days)).ffill().reindex(days)
    cf = act.copy()
    cf[days >= pd.Timestamp(pre_shock[0])] = float(pre_shock[1])
    gap = act - cf
    q = gap.groupby(gap.index.quarter).mean()
    return {"i": float(gap.mean()), "i_end": float(gap.iloc[-1]), "quarters": [float(q.get(k, 0.0)) for k in (1, 2, 3, 4)],
            "last observation": f"{last:%Y-%m-%d} ({float(s.iloc[-1]):.2f}%)", "after it": "last decision held to 31 Dec",
            "counterfactual": f"held at {pre_shock[1]:.2f}% from {pre_shock[0]}", "source": str(file.relative_to(ROOT))}


def quarter_weights(monthly, year: int) -> tuple:
    """Four weights with mean 1 from a monthly profile of a shock in `year` (e.g. the oil shock's % gap by month, the months the CGE
    averages into its annual shock): w_q = the quarter's mean / the year's mean. The year's mean must not be near zero."""
    import pandas as pd
    x = pd.Series(monthly).copy()
    x.index = pd.PeriodIndex(x.index, freq="M")
    x = x[x.index.year == year]
    if len(x) != 12:
        raise ValueError(f"quarter_weights needs the 12 months of {year}; got {len(x)}")
    mean = float(x.mean())
    if abs(mean) < 1e-6:
        raise ValueError("the year's mean is about zero: quarter weights are not defined")
    q = x.groupby(x.index.quarter).mean()
    return tuple(float(q[k] / mean) for k in (1, 2, 3, 4))


if __name__ == "__main__":
    for n in ("pamph", *QPM_RULES, "dsge", "oil0.73", "oil0.85"):
        try:
            print(n, rule(n))
        except (FileNotFoundError, ValueError) as e:
            print(n, "->", e)
