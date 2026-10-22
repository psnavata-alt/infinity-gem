"""Interest-rate closure: the central 2026 case with an interest rate clearing savings and investment (20 Oct 2026, about 9:55 AM).

Research output, NOT FOR CITATION. In the 2026 scenarios of 20 Oct 2026 the long-run years (2028-2030) keep real investment on its baseline path
(closure 'investment'): when the shocks cut incomes, saving rates adjust and private investment does not respond. With
closure='interest' (cge.py, MANAGE-WB's bond market) a real interest rate clears savings and investment: investment demand
moves by exp(-theta r / 100), saving rates by (1 + eps r / 100). theta 2 is the central value of the DSGE-CGE link (the CGE link's matched
values 1.9-3.3; research/dsge/README.md, milestone 20b), 3.3 its upper value; eps 0.3 (% of saving rates per pp) is an
ASSUMPTION (household saving is barely interest-elastic in most studies). The short-run years (2025-2027) are unchanged:
they use the Keynesian closure. The central 2026 setting of 20 Oct 2026 otherwise (Infinity GEM's own SAM, hoarding 0.85, the 2026 scenarios' wage curve), all four
shocks, public capital low.
Run:  INFINITY_GEM_SCENARIO_SAM=own  py scenarios/interest_closure_check.py   (about 15 minutes)
"""
import numpy as np
import pandas as pd

import _common
import combined_revised as CR
from infinity_gem import paths

KEYS = ("GDP gap 2026 (%)", "GDP gap 2027 (%)", "GDP gap 2030 (%)", "cumulative GDP loss 2025-2030 (₱ bn)",
        "consumer prices 2026 (%)", "new poor 2026 (M, own baskets)", "new poor 2027 (M, own baskets)")


def rint(sol):
    try:
        return float(sol["RINT"])
    except (KeyError, TypeError):
        return np.nan


def main():
    if _common.SCENARIO_SAM != "own":
        raise SystemExit("run with INFINITY_GEM_SCENARIO_SAM=own (the SAM of the central 2026 setting)")
    beta = float(pd.read_csv(_common.calibration_file(), index_col=0).loc["central (e)", "beta"])
    rows = {}
    for label, kw in (("investment closure (setting of 20 Oct 2026)", {}),
                      ("interest closure, theta 2, eps 0.3", dict(closure="interest", interest={"theta": 2.0, "eps": 0.3})),
                      ("interest closure, theta 3.3, eps 0.3", dict(closure="interest", interest={"theta": 3.3, "eps": 0.3}))):
        R = CR.Runs("low", wage_curve=beta, hoarding=0.85, **kw)
        piece, src = R.pieces()
        pw = src["public works"]
        works = {2025: pw["2025"], 2026: pw["2026 central"], 2027: pw["2027 NEP x 2025 rate (central)"]}
        clean = R.run(set(), piece=piece)
        sim = R.run(set(CR.SHOCKS), piece=piece)
        out = R.measures(clean, sim, works=works, poor=True)[0]
        row = {k: out[k] for k in KEYS}
        for y in (2028, 2030):
            row[f"real investment {y} (%)"] = (float(sim.solutions[y]["QINV"].sum()) / float(clean.solutions[y]["QINV"].sum()) - 1) * 100
            row[f"real interest rate {y} (pp vs baseline)"] = rint(sim.solutions[y]) - rint(clean.solutions[y])
        rows[label] = row
        print(label, {k: round(v, 3) for k, v in row.items()}, flush=True)
    t = pd.DataFrame(rows).T
    stamp = pd.Timestamp.today()
    f = paths.output_dir() / f"interest_closure_check_{stamp:%Y%m%d_%H%M}{_common.sam_tag()}_hoarding0.85.md"
    f.write_text("\n".join([f"# Interest-rate closure: the central 2026 case with an interest rate clearing savings and investment ({stamp:%d %B %Y, %H:%M})", "",
                            "**NOT FOR CITATION** (Infinity GEM 0.3.11). Long-run years (2028-2030) in closure 'interest' (cge.py; real "
                            "investment x exp(-theta r/100), saving rates x (1 + eps r/100)); short-run years unchanged (Keynesian). "
                            f"Infinity GEM's own SAM; hoarding 0.85; wage-curve beta {beta:.3f}; public capital low; all four shocks. theta from the DSGE-CGE link "
                            "(matched values 1.9-3.3); eps 0.3 an assumption. Script `scenarios/interest_closure_check.py`.", "",
                            t.to_markdown(floatfmt=".3f")]), encoding="utf-8")
    print("saved", f)


if __name__ == "__main__":
    main()
