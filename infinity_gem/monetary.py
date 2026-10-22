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


def rule(name: str = "pamph") -> dict:
    """Coefficients for DynamicCGE.monetary_scenario(rule=...): {"rho", "phi_pi", "phi_x", "phi_e", "freq": "quarterly", "source"}."""
    if name == "pamph":
        sys.path.insert(0, str(ROOT / "research" / "dsge"))
        import qpm
        p, *_ = qpm.match_pamph()
        return {"rho": float(p.g1), "phi_pi": 1.0 + float(p.g2), "phi_x": float(p.g3), "phi_e": 0.0, "freq": "quarterly",
                "source": "QPM calibrated to PAMPh (research/dsge/qpm.py match_pamph; inflation coefficient 1 + g2)"}
    if name not in SPECS:
        raise ValueError(f"rule must be one of pamph, {', '.join(SPECS)}")
    files, names, D = chains(name)
    mean = dict(zip(names, D.mean(0)))
    return {"rho": float(mean["rho_i"]), "phi_pi": float(mean["phi_pi"]), "phi_x": 4.0 * float(mean["phi_x"]),
            "phi_e": float(mean.get("phi_e", 0.0)), "freq": "quarterly",
            "source": f"posterior mean of {len(files)} chain(s): {', '.join(f.name for f in files)}"}


if __name__ == "__main__":
    for n in ("pamph", "dsge", "oil0.73", "oil0.85"):
        try:
            print(n, rule(n))
        except (FileNotFoundError, ValueError) as e:
            print(n, "->", e)
