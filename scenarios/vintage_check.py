"""Capital vintages: the central 2026 case with within-year capital vintages (20 Oct 2026).

Research output, NOT FOR CITATION. The central 2026 setting of 20 Oct 2026 (Infinity GEM's own SAM, hoarding 0.85, the 2026 scenarios' wage curve, public capital
low); all four shocks, public capital low. Three capital settings:
- putty-clay (the 2026 scenarios): capital fixed by industry within the year; last year's investment placed by last year's returns;
- vintage, release 0.7 in long-run years only (MANAGE-WB's invElas default): in the hybrid closure's short-run years (2025-2027)
  installed capital stays put and the year's new capital is placed as in the baseline (plans made before the shock);
- vintage with release 0.7 in the short-run years too: a contracting industry sheds installed capital within the shock year and
  other industries hire it at once (an upper bound on within-year mobility).
Run:  INFINITY_GEM_SCENARIO_SAM=own  py scenarios/vintage_check.py   (about 10-20 minutes)
"""
import pandas as pd

import _common
import combined_revised as CR
from infinity_gem import paths

KEYS = ("GDP gap 2026 (%)", "GDP gap 2027 (%)", "GDP gap 2030 (%)", "cumulative GDP loss 2025-2030 (₱ bn)",
        "consumer prices 2026 (%)", "new poor 2026 (M, own baskets)", "new poor 2027 (M, own baskets)")
CASES = (("putty-clay (setting of 20 Oct 2026)", {}),
         ("vintages, release 0.7 after 2027 only (installed capital fixed in 2025-2027)", dict(capital_allocation="vintage")))
# The upper bound with release 0.7 in the short-run years too (vintage_e_sr=0.7) is left out by default: under the full 2026 setting (wage curve, hoarding) its 2026 wage-curve solve failed on 20 Oct 2026 (the vintage short-run model is fragile when
# iterated); on a plain 20% construction cut it gave 2026 GDP -0.96% against -2.79%. Run with the argument all to try it.
EXTRA_CASES = (("vintages, release 0.7 in every year (upper bound on within-year mobility)",
                dict(capital_allocation="vintage", vintage_e_sr=0.7)),)


def main():
    if _common.SCENARIO_SAM != "own":
        raise SystemExit("run with INFINITY_GEM_SCENARIO_SAM=own (the 2026 scenarios' SAM)")
    beta = float(pd.read_csv(_common.calibration_file(), index_col=0).loc["central (e)", "beta"])
    rows = {}
    import sys
    for label, kw in CASES + (EXTRA_CASES if "all" in sys.argv[1:] else ()):
        R = CR.Runs("low", wage_curve=beta, hoarding=0.85, **kw)
        piece, src = R.pieces()
        pw = src["public works"]
        works = {2025: pw["2025"], 2026: pw["2026 central"], 2027: pw["2027 NEP x 2025 rate (central)"]}
        clean = R.run(set(), piece=piece)
        out = R.measures(clean, R.run(set(CR.SHOCKS), piece=piece), works=works, poor=True)[0]
        rows[label] = {k: out[k] for k in KEYS}
        print(label, {k: round(out[k], 3) for k in KEYS}, flush=True)
    t = pd.DataFrame(rows).T
    stamp = pd.Timestamp.today()
    f = paths.output_dir() / f"vintage_check_{stamp:%Y%m%d_%H%M}{_common.sam_tag()}_hoarding0.85.md"
    f.write_text("\n".join([f"# Capital vintages: the central 2026 case with within-year capital vintages ({stamp:%d %B %Y, %H:%M})", "",
                            "**NOT FOR CITATION** (Infinity GEM 0.3.12; `cge.py capital='vintage'`, `dynamic.py capital_allocation='vintage'`, "
                            "check VN1). Release elasticity of installed capital e = 0.7 (MANAGE-WB's invElas, bridge-file default); the year's "
                            "new capital (last year's investment) is placed within the year by one rental rate, except in short-run years, "
                            "where it is placed as in the baseline. Infinity GEM's own SAM; hoarding 0.85; wage-curve beta "
                            f"{beta:.3f}; public capital low. Script `scenarios/vintage_check.py`.", "", t.to_markdown(floatfmt=".3f")]),
                 encoding="utf-8")
    print("saved", f)


if __name__ == "__main__":
    main()
