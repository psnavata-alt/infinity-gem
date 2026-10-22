"""Value added-energy bundle, diagnostic (19 Oct 2026, night): why the oil shock's 2027-2030 GDP loss is a little larger with the value
added-energy bundle than with Leontief fuel. Year-by-year paths of the oil-alone run against the no-shock path, with and
without the bundle, in the central 2026 setting of 20 Oct 2026 (Infinity GEM's own SAM, hoarding 0.85, the 2026 scenarios' wage curve, public capital low).

Research output, NOT FOR CITATION.
Run:  INFINITY_GEM_SCENARIO_SAM=own  py scenarios/energy_nest_oil_paths.py   (about 10 minutes)
"""
import numpy as np
import pandas as pd

import _common
import combined_revised as CR
from energy_nest_oil_check import NEST_LR, NEST_SR
from infinity_gem import paths


def pct(a, b):
    return (float(b) / float(a) - 1) * 100


def oil_paths(R, piece):
    clean, oil = R.run(set(), piece=piece), R.run({"oil"}, piece=piece)
    C = list(R.m.C)
    ip, ie, ic = C.index("cpetr"), C.index("celec"), C.index("ccons")
    rows = {}
    for y in clean.table.index:
        a, b, ta, tb = clean.solutions[y], oil.solutions[y], clean.table.loc[y], oil.table.loc[y]
        rows[y] = {
            "closure": tb.get("closure", ""),
            "real GDP": pct(ta.real_gdp, tb.real_gdp),
            "real consumption": pct(ta.real_consumption, tb.real_consumption),
            "real investment": pct(ta.real_investment, tb.real_investment),
            "capital stock": pct(ta.capital_stock_index, tb.capital_stock_index),
            "real exports": pct(np.sum(a["QE"]), np.sum(b["QE"])),
            "real imports": pct(np.sum(a["QM"]), np.sum(b["QM"])),
            "petroleum imports": pct(a["QM"][ip], b["QM"][ip]),
            "petroleum used by industries": pct(a["QINT"][ip], b["QINT"][ip]),
            "electricity used by industries": pct(a["QINT"][ie], b["QINT"][ie]),
            "real value added": pct(np.sum(a["QVA"]), np.sum(b["QVA"])),
            "employment, all labour": pct(np.sum(a["EMP"][[k for k, f in enumerate(R.m.F) if f.startswith("flab")]]),
                                          np.sum(b["EMP"][[k for k, f in enumerate(R.m.F) if f.startswith("flab")]])),
            "consumer prices": pct(ta.cpi, tb.cpi),
            "peso per dollar (EXR)": pct(ta.exr, tb.exr),
            "price of construction (PQ)": pct(a["PQ"][ic], b["PQ"][ic]),
            "price of electricity (PQ)": pct(a["PQ"][ie], b["PQ"][ie]),
            "foreign saving (₱, SAM units, change)": float(b["FSAV"]) - float(a["FSAV"]),
            "government saving (change)": float(b["GSAV"]) - float(a["GSAV"]),
            # decomposition (SAM units): real GDP = real value added + taxes on products and activities (benchmark prices)
            "real GDP (change, SAM units)": float(tb.real_gdp) - float(ta.real_gdp),
            "real value added (change, SAM units)": float(np.sum(b["QVA"])) - float(np.sum(a["QVA"])),
            "taxes on petroleum, sales + imports (change, SAM units)": float(b["STAX"][ip] + b["MTAX"][ip]) - float(a["STAX"][ip] + a["MTAX"][ip]),
            "all taxes on products and activities (change, SAM units)": float(np.sum(b["STAX"]) + np.sum(b["MTAX"]) + np.sum(b["ATAX"]))
                                                                        - float(np.sum(a["STAX"]) + np.sum(a["MTAX"]) + np.sum(a["ATAX"])),
            "household saving-rate adjustment (MPSADJ, change)": float(b["MPSADJ"]) - float(a["MPSADJ"]),
            "no-shock run against the baseline: real GDP (%)": pct(R.d.base.table.loc[y, "real_gdp"], ta.real_gdp),
        }
    return pd.DataFrame(rows).T


def main():
    if _common.SCENARIO_SAM != "own":
        raise SystemExit("run with INFINITY_GEM_SCENARIO_SAM=own (the SAM of the central 2026 setting)")
    beta = float(pd.read_csv(_common.calibration_file(), index_col=0).loc["central (e)", "beta"])
    parts = []
    for label, kw in (("Leontief fuel", {}), ("bundle", dict(energy_nest=NEST_LR, sr_energy_nest=NEST_SR))):
        R = CR.Runs("low", wage_curve=beta, hoarding=0.85, **kw)
        piece, _ = R.pieces()
        t = oil_paths(R, piece)
        t.index = [f"{label} {y}" for y in t.index]
        parts.append(t)
        print(label, "done", flush=True)
    t = pd.concat(parts)
    stamp = pd.Timestamp.today()
    f = paths.output_dir() / f"energy_nest_oil_paths_{stamp:%Y%m%d_%H%M}{_common.sam_tag()}_hoarding0.85.md"
    f.write_text("\n".join([f"# Value added-energy bundle: oil alone, year by year, with and without the value added-energy bundle ({stamp:%d %B %Y, %H:%M})", "",
                            "**NOT FOR CITATION** (Infinity GEM 0.3.11). Oil-alone run minus the no-shock run, % unless stated. "
                            f"Bundle elasticities (MANAGE-WB defaults): 2028-2030 {NEST_LR}; 2025-2027 {NEST_SR}. Infinity GEM's own SAM; "
                            f"hoarding 0.85; wage-curve beta {beta:.3f}; public capital low. Script `scenarios/energy_nest_oil_paths.py`.",
                            "", t.T.to_markdown(floatfmt=".3f")]), encoding="utf-8")
    print("saved", f)


if __name__ == "__main__":
    main()
