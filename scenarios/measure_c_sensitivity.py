"""Measure C under slower delivery and lower public-investment efficiency (17 Oct 2026).

17 Oct 2026: two quick checks on measure C (an outside AI review's points (3)-(4)):
  (3) delivery: half of C's ₱208.7 bn is built in 2027 and half in 2028 (vetting and audits slow spending), against all in 2027;
  (4) efficiency: the share of public investment that becomes usable capital is 0.6 (IMF DIG model's base case, Buffie et al.
      2012, a reference copy (not distributed)) instead of 0.77 (IMF PIMA). This applies to every change in public
      construction, so the public-works shortfall itself also costs less lasting output.
The central 2026 combined run otherwise (public capital low, wage curve at the central beta). Output per peso as in the 2026 scenarios (output recovered 2025-30, 2025-peso equivalents, over C's cost). NOT FOR CITATION.
Run:  py scenarios/measure_c_sensitivity.py   (about 5 minutes)
"""
import sys

from _common import ROOT, equiv_2025, to_sam_units
import pandas as pd

sys.path.insert(0, str(ROOT / "preshock"))
from infinity_gem import paths                                                     # noqa: E402
import combined_revised as CR                                                   # noqa: E402
import elnino_to_cge as EN                                                      # noqa: E402


def run_with(R, piece, extra):
    """CR.Runs.run with all four shocks and extra shock specs {year: spec} merged in (no named measures)."""
    m = R.m
    tariff = {"tm_scale": {"cmric": EN.TARIFF_2026 / float(m.tm[m.C.index("cmric")])}}
    aid = lambda bn, y: {"trg_h_add": {h: to_sam_units(bn, CR.PSA_GDP[y]) * w for h, w in R.alloc.items()}}
    sh = {2025: {}, 2026: dict(tariff), 2027: CR.merge(tariff, aid(-CR.AID_2027, 2027))}
    for f in CR.SHOCKS:
        for t, sp in piece[f].items():
            sh[t] = CR.merge(sh.get(t, {}), sp)
    for t, sp in extra.items():
        sh[t] = CR.merge(sh.get(t, {}), sp)
    return R.d.scenario(sh)


def c_spec(R, bn, year):
    return {"qinv_scale": {"ccons": 1 + to_sam_units(bn, CR.PSA_GDP.get(year, CR.PSA_GDP[2027])) / R.q0}}


def main():
    cal = pd.read_csv(__import__("_common").calibration_file(), index_col=0)
    beta = float(cal.loc["central (e)", "beta"])
    rows = {}
    for label, eff in (("efficiency 0.77 (central)", None), ("efficiency 0.6 (IMF DIG base)", 0.6)):
        kw = {} if eff is None else {"public_capital": dict(phi=0.083, kg_gdp=0.397, e=eff)}
        R = CR.Runs("low", wage_curve=beta, **kw)
        piece, src = R.pieces()
        pw = src["public works"]
        works = {2025: pw["2025"], 2026: pw["2026 central"], 2027: pw["2027 NEP x 2025 rate (central)"]}
        clean = R.run(set(), piece=piece)
        base = R.measures(clean, run_with(R, piece, {}), works=works, poor=True)[0]
        cost = equiv_2025(CR.CATCHUP, 2027)
        for timing, extra, spend in (("all in 2027", {2027: c_spec(R, CR.CATCHUP, 2027)}, {2027: CR.CATCHUP}),
                                     ("half 2027, half 2028", {2027: c_spec(R, CR.CATCHUP / 2, 2027), 2028: c_spec(R, CR.CATCHUP / 2, 2027)},
                                      {2027: CR.CATCHUP / 2})):
            p = R.measures(clean, run_with(R, piece, extra), works=works, extra_spend=spend, poor=True)[0]
            rows[f"{label}; C {timing}"] = {
                "shocks: output lost 2025-30 (₱ bn)": base["cumulative GDP loss 2025-2030 (₱ bn)"],
                "shocks: new poor 2026 (M)": base["new poor 2026 (M, own baskets)"],
                "C: output recovered 2025-30 (₱ bn)": base["cumulative GDP loss 2025-2030 (₱ bn)"] - p["cumulative GDP loss 2025-2030 (₱ bn)"],
                "C: output recovered per peso": (base["cumulative GDP loss 2025-2030 (₱ bn)"] - p["cumulative GDP loss 2025-2030 (₱ bn)"]) / cost,
                "C: poor protected 2027 (M)": base["new poor 2027 (M, own baskets)"] - p["new poor 2027 (M, own baskets)"],
                "C: GDP gap 2027 (pp change)": p["GDP gap 2027 (%)"] - base["GDP gap 2027 (%)"]}
            print(label, timing, {k: round(v, 3) for k, v in rows[f"{label}; C {timing}"].items()}, flush=True)
    t = pd.DataFrame(rows).T
    stamp = pd.Timestamp.today()
    f = paths.output_dir() / f"measure_c_sensitivity_{stamp:%Y%m%d_%H%M}{__import__('_common').out_tag()}"
    f = f.with_name(f.name + ".x")      # 19 Oct 2026: with_suffix() below must not eat the ".85" of a tag such as "_hoarding0.85"
    t.to_csv(f.with_suffix(".csv"))
    L = [f"# Measure C: slower delivery and lower efficiency ({stamp:%d %B %Y, %H:%M})", "",
         "**NOT FOR CITATION** (Infinity GEM 0.3.8(3)-(4)). Script: `scenarios/measure_c_sensitivity.py`. The "
         "the central 2026 run with C (₱208.7 bn of DPWH's lapsing 2025 money) built all in 2027 or half in 2027 and half in 2028, "
         "and with the share of public investment that becomes usable capital at 0.77 (IMF PIMA, central) or 0.6 (IMF DIG base, "
         "Buffie et al. 2012). 2028 is a long-run year in the model (no idle labour), so money spent then adds capital, not demand.",
         "", t.to_markdown(floatfmt=".3f")]
    f.with_suffix(".md").write_text("\n".join(L), encoding="utf-8")
    print("saved", f.with_suffix(".md"))


if __name__ == "__main__":
    main()
