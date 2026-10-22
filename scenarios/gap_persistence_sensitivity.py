"""Engine sensitivity D5 of code review of dynamic.py (17 Oct 2026): gap_persistence.

The hybrid closure carries a share `gap_persistence` (default 0.5, NO SOURCE) of each short-run year's employment gap into
the next long-run year, halving it each year after. In the 2026 scenarios' run the short-run years are 2025-2027, so it acts only
from 2028. This script runs the central combined 2026 run (public capital low, wage curve at the central beta) with
gap_persistence 0 (the gap closes at once), 0.5 (central) and 1 (the gap never closes: full hysteresis, an upper bound;
Blanchard and Summers 1986, a reference copy (not distributed)), and the measures A, B, C.
NOT FOR CITATION. Run:  py scenarios/gap_persistence_sensitivity.py   (about 10 minutes)
"""
import sys

from _common import ROOT
import pandas as pd

sys.path.insert(0, str(ROOT / "preshock"))
from infinity_gem import paths                                                     # noqa: E402
import combined_revised as CR                                                   # noqa: E402

VALUES = (0.0, 0.5, 1.0)


def main():
    cal = pd.read_csv(__import__("_common").calibration_file(), index_col=0)
    beta = float(cal.loc["central (e)", "beta"])
    rows = {}
    for gp in VALUES:
        R = CR.Runs("low", wage_curve=beta, gap_persistence=gp)
        piece, src = R.pieces()
        pw = src["public works"]
        works = {2025: pw["2025"], 2026: pw["2026 central"], 2027: pw["2027 NEP x 2025 rate (central)"]}
        clean = R.run(set(), piece=piece)
        out = R.measures(clean, R.run(set(CR.SHOCKS), piece=piece), works=works, poor=True)[0]
        row = {k: out[k] for k in ("GDP gap 2026 (%)", "GDP gap 2027 (%)", "GDP gap 2028 (%)", "GDP gap 2029 (%)",
                                   "GDP gap 2030 (%)", "cumulative GDP loss 2025-2030 (₱ bn)", "new poor 2026 (M, own baskets)",
                                   "new poor 2027 (M, own baskets)", "debt-to-GDP change 2030 (pp)")}
        for ms in ("A", "B", "C"):
            p = R.measures(clean, R.run(set(CR.SHOCKS), ms, piece=piece), works=works,
                           extra_spend={2027: CR.CATCHUP} if ms == "C" else None, poor=False)[0]
            cost = {"A": CR.equiv_2025(CR.AID_2026, 2026), "B": CR.equiv_2025(CR.AID_2027, 2027),
                    "C": CR.equiv_2025(CR.CATCHUP, 2027)}[ms]
            row[f"{ms}: output recovered per peso"] = (out["cumulative GDP loss 2025-2030 (₱ bn)"]
                                                       - p["cumulative GDP loss 2025-2030 (₱ bn)"]) / cost
        rows[f"gap_persistence {gp}"] = row
        print(f"gap_persistence {gp}:", pd.Series(row).round(3).to_dict(), flush=True)
    t = pd.DataFrame(rows)
    stamp = pd.Timestamp.today()
    f = paths.output_dir() / f"gap_persistence_sensitivity_{stamp:%Y%m%d_%H%M}{__import__('_common').out_tag()}"
    f = f.with_name(f.name + ".x")      # 19 Oct 2026: with_suffix() below must not eat the ".85" of a tag such as "_hoarding0.85"
    t.to_csv(f.with_suffix(".csv"))
    L = [f"# Engine sensitivity D5: how much of the job gap carries into 2028-2030 ({stamp:%d %B %Y, %H:%M})", "",
         "**NOT FOR CITATION** (Infinity GEM 0.3.8 D5). Script: `scenarios/gap_persistence_sensitivity.py`. "
         "The central 2026 combined run (public capital low; wage curve at the central beta) with the share of each "
         "year's employment gap carried into the next long-run year set to 0 (closes at once), 0.5 (central; no source) and "
         "1 (never closes: full hysteresis, Blanchard and Summers 1986). The short-run years are 2025-2027, so 2025-2027 "
         "results cannot move.", "", t.to_markdown(floatfmt=".3f")]
    f.with_suffix(".md").write_text("\n".join(L), encoding="utf-8")
    print("saved", f.with_suffix(".md"))


if __name__ == "__main__":
    main()
