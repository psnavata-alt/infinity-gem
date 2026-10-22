"""Own SAM: which goods make consumer prices fall more on Infinity GEM's own SAM than on IFPRI's? (18 Oct 2026). NOT FOR CITATION.

The central 2026 case gives 2026 consumer prices of -0.19% on IFPRI's SAM, -1.85% on the project's v0.3 and -1.65% on v0.4
(outputs/sam_psa_sensitivity_*_own*_row.csv). The lower poor count on Infinity GEM's own SAM follows from that price fall, not from the
wage-curve slope alone: v0.4 corrects the services labour allocation (design note §10), its beta falls from 10.8 to 9.7, yet
the poor count does not move. The model's CPI is cwts @ PQ (household market purchases as weights, infinity_gem/cge.py), so its
2026 change splits exactly into commodity contributions:  sum_c cwts_c (PQ_c shock - PQ_c no-shock) / CPI no-shock.
This script runs the combined 2025-27 shocks on each SAM at its own calibrated beta (IFPRI 7.14, v0.3 10.77, v0.4 9.72;
the calibrations of 17-18 Oct) and reports, for 2026, each commodity's weight, price change and contribution, and the
contributions grouped by kind of good. No model code or default is changed.
Run:  py scenarios/own_sam_cpi_decomposition.py      Output: outputs/own_sam_cpi_decomposition_<stamp>.md
"""
import sys

from _common import ROOT
import pandas as pd

sys.path.insert(0, str(ROOT / "preshock"))
import _common                                                                  # noqa: E402
from infinity_gem import paths, settings                                           # noqa: E402
import combined_revised as CR                                                   # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
YEAR = 2026
RUNS = {"IFPRI 2023": (None, paths.SAM_2023_RICE, 7.1405), "own SAM v0.3": ("own", paths.sam_own("0.3"), 10.77),
        "own SAM v0.4": ("own", paths.sam_own("0.4"), 9.7174)}
KIND = {**{c: "food and farm" for c in ("crice", "cmaiz", "cocer", "cpuls", "coils", "croot", "cvege", "csugr", "cfrui", "ccoff",
                                         "cocrp", "ccatt", "cpoul", "coliv", "cfish", "cfood", "cmric", "cbeve", "ctoba", "cfore")},
        "cpetr": "fuel", "celec": "utilities", "cwatr": "utilities",
        **{c: "other manufactures" for c in ("ccott", "ctext", "cwood", "cchem", "cnmet", "cmetl", "cmine", "cmach", "coman")},
        "creal": "housing", "ccons": "housing",
        **{c: "services" for c in ("ctrad", "ctran", "chotl", "ccomm", "cfsrv", "cbsrv", "cpadm", "ceduc", "cheal", "cosrv")}}


def run(variant, path, beta):
    base_dyn, base_cge, sam0 = settings.dynamic_kwargs, settings.cge_model, paths.SAM_2023_OWN
    gdp0, to0 = _common.SAM_GDP_2023, CR.TO_2025
    paths.SAM_2023_OWN = path if variant == "own" else sam0
    CR.dynamic_kwargs = lambda *a, **k: base_dyn(*a, **{**k, "sam_variant": variant or "ifpri"})   # 0.3.10: None = IFPRI explicitly
    CR.cge_model = lambda *a, **k: base_cge(*a, **{**k, "sam_variant": variant or "ifpri"})
    try:
        m = base_cge("0.3 recommended", rice=True, sam_variant=variant or "ifpri")
        b0 = m.solve()
        if not b0.ok:
            raise RuntimeError("benchmark did not solve")
        _common.SAM_GDP_2023 = float(m.gdp(b0)["nominal_expenditure"])
        CR.TO_2025 = CR.PSA_GDP[2025] / _common.SAM_GDP_2023
        R = CR.Runs("low", wage_curve=beta)
        piece, _ = R.pieces()
        clean, adv = R.run(set(), piece=piece), R.run(set(CR.SHOCKS), piece=piece)
        mm = R.d.m
        b, s = clean.solutions[YEAR], adv.solutions[YEAR]
        pq0, pq1 = pd.Series(b["PQ"], index=mm.C), pd.Series(s["PQ"], index=mm.C)
        w = pd.Series(mm.cwts, index=mm.C)
        cpi0 = float((w * pq0).sum())
        t = pd.DataFrame({"weight (%)": w * 100, "price change (%)": (pq1 / pq0 - 1) * 100,
                          "contribution (pp)": w * (pq1 - pq0) / cpi0 * 100})
        cpi = (float((w * pq1).sum()) / cpi0 - 1) * 100
    finally:
        CR.dynamic_kwargs, CR.cge_model, paths.SAM_2023_OWN = base_dyn, base_cge, sam0
        _common.SAM_GDP_2023, CR.TO_2025 = gdp0, to0
    return t, cpi


def main():
    stamp = pd.Timestamp.now()
    tabs, cpis = {}, {}
    for name, (v, p, beta) in RUNS.items():
        tabs[name], cpis[name] = run(v, p, beta)
        print(name, "CPI 2026 change", round(cpis[name], 3), flush=True)
    big = pd.concat(tabs, axis=1)
    big["kind"] = [KIND.get(c, "other") for c in big.index]
    contrib = big.xs("contribution (pp)", axis=1, level=1)
    grouped = contrib.groupby(big["kind"]).sum()
    grouped.loc["Total (= CPI change, %)"] = grouped.sum()
    wts = big.xs("weight (%)", axis=1, level=1).groupby(big["kind"]).sum()
    diff = (contrib["own SAM v0.4"] - contrib["IFPRI 2023"]).sort_values()
    top = big.loc[diff.index[:12]]
    L = [f"# Consumer prices in 2026 by commodity: IFPRI's SAM and the project's ({stamp:%d %B %Y, %H:%M})", "",
         "**NOT FOR CITATION** (Infinity GEM 0.3.9). Script: `scenarios/own_sam_cpi_decomposition.py`. The combined "
         "2025-27 shocks, public capital low, each SAM at its own calibrated wage-curve beta (IFPRI 7.14, own SAM v0.3 10.77, v0.4 "
         "9.72). Contribution = CPI weight x price change against the no-shock path; contributions add up to the CPI change.", "",
         "CPI change 2026 (%): " + ", ".join(f"{k} {v:.2f}" for k, v in cpis.items()), "",
         "## 1. By kind of good: contributions (pp)", "", grouped.round(3).to_markdown(), "",
         "CPI weights by kind (%):", "", wts.round(1).to_markdown(), "",
         "## 2. The twelve commodities that pull own SAM v0.4's CPI furthest below IFPRI's", "", top.round(3).to_markdown(), "",
         "## 3. Every commodity", "", big.round(3).to_markdown()]
    out = paths.output_dir() / f"own_sam_cpi_decomposition_{stamp:%Y%m%d_%H%M}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print(grouped.round(3).to_string())
    print(wts.round(1).to_string())
    print(top.round(3).to_string())
    print("saved", out)


if __name__ == "__main__":
    main()
