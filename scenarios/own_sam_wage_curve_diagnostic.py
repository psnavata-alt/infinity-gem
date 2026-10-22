"""Why Infinity GEM's own SAM needs a steeper wage curve than IFPRI's for the same Okun target (18 Oct 2026, about
7 AM). NOT FOR CITATION. No model code or default is changed.

The central 2026 case recalibrates the short-run wage curve on each SAM so that the 2026 change in labour input equals
Okun's e (0.71, preshock/okun.py) times the model's own 2026 growth effect (scenarios/calibrate_wage_curve.py). On IFPRI's SAM
that gives beta 7.14; on the project's v0.2 11.1 and v0.3 10.8, and with the steeper curve consumer prices fall about 1.9% in 2026,
which is why Infinity GEM's own SAM gives fewer new poor (design note §8-9). This script runs the same combined shocks on both SAMs at the
SAME betas and reports, for 2026:
  - labour input, the GDP gaps and the growth effect, and the Okun target e x growth effect;
  - employment and wages by PSA industry (MicroLink.industries), at beta 7.14;
  - each industry's labour share of value added in each SAM.
If Infinity GEM's own SAM loses more labour input per point of output at the same beta, the steeper calibrated curve follows; the
industry table shows where.
Run:  py scenarios/own_sam_wage_curve_diagnostic.py      Output: outputs/own_sam_wage_curve_diagnostic_<date>.md
"""
import sys

from _common import ROOT
import pandas as pd

sys.path.insert(0, str(ROOT / "preshock"))
import _common                                                                  # noqa: E402
from infinity_gem import paths, settings                                           # noqa: E402
from infinity_gem.dynamic import PSA_INDUSTRIES                                     # noqa: E402
from infinity_gem.microlink import MicroLink                                        # noqa: E402
from infinity_gem.sam import SAM                                                    # noqa: E402
import calibrate_wage_curve as CW                                               # noqa: E402
import combined_revised as CR                                                   # noqa: E402
import okun                                                                     # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BETAS = (0.0, 7.14, 10.77)
SAMS = {None: ("IFPRI 2023 SAM", paths.SAM_2023_RICE), "own": (f"Infinity GEM's own {paths.SAM_2023_OWN.stem.split('_own_')[-1]}",
                                                                 paths.SAM_2023_OWN)}


def labour_shares(path):
    """Labour income / value added (factor payments) by PSA industry, %."""
    s = SAM.load(path)
    t = s.table
    labs = [f for f in t.index if f.startswith("flab")]
    facs = [f for f in t.index if f.startswith(("flab", "fcap", "flnd"))]
    out = {}
    for k, acts in PSA_INDUSTRIES.items():
        a = [x for x in acts if x in t.columns]
        va = float(t.loc[facs, a].values.sum())
        out[k] = float(t.loc[labs, a].values.sum()) / va * 100 if va else float("nan")
    return pd.Series(out)


def run(variant):
    base_dyn, base_cge = settings.dynamic_kwargs, settings.cge_model
    gdp0, to0 = _common.SAM_GDP_2023, CR.TO_2025
    CR.dynamic_kwargs = lambda *a, **k: base_dyn(*a, **{**k, "sam_variant": variant or "ifpri"})   # 0.3.10: None = IFPRI explicitly
    CR.cge_model = lambda *a, **k: base_cge(*a, **{**k, "sam_variant": variant or "ifpri"})
    try:
        m = base_cge("0.3 recommended", rice=True, sam_variant=variant or "ifpri")
        b0 = m.solve()
        if not b0.ok:
            raise RuntimeError("benchmark did not solve")
        _common.SAM_GDP_2023 = float(m.gdp(b0)["nominal_expenditure"])
        CR.TO_2025 = CR.PSA_GDP[2025] / _common.SAM_GDP_2023
        e = float(okun.estimates().loc["2006-2026, all quarters", "elasticity e"])
        R = CR.Runs("low")
        piece, _ = R.pieces()
        rows, ind = {}, None
        for beta in BETAS:
            lab, g26, g25, ge = CW.stats(R, piece, beta)
            rows[beta] = {"labour input 2026 (%)": lab, "GDP gap 2025 (%)": g25, "GDP gap 2026 (%)": g26,
                          "growth effect 2026 (pp)": ge, "Okun target e x growth effect (%)": e * ge,
                          "labour input minus target (pp)": lab - e * ge,
                          "labour input per point of growth effect": lab / ge if ge else float("nan")}
            if beta == 7.14:
                R.d.a["wage_curve"] = beta
                clean, adv = R.run(set(), piece=piece), R.run(set(CR.SHOCKS), piece=piece)
                ind = MicroLink.industries(R.d.ms, clean.solutions[2026], adv.solutions[2026])
    finally:
        CR.dynamic_kwargs, CR.cge_model = base_dyn, base_cge
        _common.SAM_GDP_2023, CR.TO_2025 = gdp0, to0
    return pd.DataFrame(rows), ind


def main():
    stamp = pd.Timestamp.today()
    tabs, inds, shares = {}, {}, {}
    for v, (name, path) in SAMS.items():
        t, ind = run(v)
        tabs[name], inds[name], shares[name] = t, ind, labour_shares(path)
        print(name); print(t.round(3).to_string()); print(ind.round(3).to_string())
    macro = pd.concat(tabs, axis=1)
    macro.columns = [f"{n}, beta {b:g}" for n, b in macro.columns]
    emp = pd.concat({n: d["employment_pct"] for n, d in inds.items()}, axis=1)
    wage = pd.concat({n: d["avg_wage_pct"] for n, d in inds.items()}, axis=1)
    ls = pd.DataFrame(shares)
    f = paths.output_dir() / f"own_sam_wage_curve_diagnostic_{stamp:%Y%m%d_%H%M}"
    L = [f"# Why Infinity GEM's own SAM needs a steeper wage curve ({stamp:%d %B %Y, %H:%M})", "",
         "**NOT FOR CITATION** (Infinity GEM 0.3.9). Script: `scenarios/own_sam_wage_curve_diagnostic.py`. "
         "The combined 2025-2027 shocks (public capital low, flexible prices), the same code on both SAMs, the wage-curve "
         "beta fixed at the values shown (0 = fixed peso wages; 7.14 = IFPRI's calibration; 10.77 = own SAM v0.3's).", "",
         "## 1. Labour input against the Okun target, 2026", "", macro.round(3).to_markdown(), "",
         "## 2. Employment by PSA industry, 2026, beta 7.14 (% against the no-shock path)", "", emp.round(3).to_markdown(), "",
         "Average wage (%):", "", wage.round(3).to_markdown(), "",
         "## 3. Labour share of value added by PSA industry in each SAM (%)", "", ls.round(1).to_markdown()]
    f.with_suffix(".md").write_text("\n".join(L), encoding="utf-8")
    print("saved", f.with_suffix(".md"))


if __name__ == "__main__":
    main()
