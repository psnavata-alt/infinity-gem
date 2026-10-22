"""Value added-energy bundle: the central 2026 case with and without the value added-energy bundle (19 Oct 2026, night).

Research output, NOT FOR CITATION: the elasticities are MANAGE-WB's defaults (see NEST_LR below). The central 2026 setting of 20 Oct 2026
(Infinity GEM's own SAM, hoarding 0.85, the 2026 scenarios' wage curve); oil alone and all four shocks, public capital low. Energy = refined
petroleum and electricity. Short-run years (2025-2027) use lower elasticities than later years (installed capital is less
flexible: MANAGE-WB's old vintage).
Run:  INFINITY_GEM_SCENARIO_SAM=own  py scenarios/energy_nest_oil_check.py   (about 10-20 minutes)
"""
import pandas as pd

import _common
import combined_revised as CR
from infinity_gem import paths

# Sourced (19 Oct 2026, about 11 PM): MANAGE-WB's default elasticities, `external/MANAGE-WB-main/dat/BridgeFile_GTAP_9_template.xlsx`:
# sheet actPar, bundle cap_labsk_ener (capital, skilled labour, energy): old vintage 0.1, new vintage 0.8; sheet pnest, ener (between
# energy carriers) 0.5. Infinity GEM's bundle puts energy with all of value added, so 0.1 (short run, installed capital) and 0.8 (later
# years, new capital) are an approximation of MANAGE-WB's capital-skilled labour-energy node.
NEST_LR = {"energy": ["cpetr", "celec"], "sigma_ve": 0.8, "sigma_e": 0.5}
NEST_SR = {"energy": ["cpetr", "celec"], "sigma_ve": 0.1, "sigma_e": 0.5}
# MANAGE-WB gives 0.8 to NEW capital only; by 2028-2030 about a third of the stock is new (investment of 2025-2030 against
# depreciation), so a capital-weighted blend 0.1 + 0.7 x 0.36 = about 0.35 is the closer value for those years (approximation)
NEST_BLEND = {"energy": ["cpetr", "celec"], "sigma_ve": 0.35, "sigma_e": 0.5}
KEYS = ("GDP gap 2026 (%)", "GDP gap 2027 (%)", "GDP gap 2030 (%)", "cumulative GDP loss 2025-2030 (₱ bn)",
        "consumer prices 2026 (%)", "new poor 2026 (M, own baskets)", "new poor 2027 (M, own baskets)")


def main():
    if _common.SCENARIO_SAM != "own":
        raise SystemExit("run with INFINITY_GEM_SCENARIO_SAM=own (the SAM of the central 2026 setting)")
    beta = float(pd.read_csv(_common.calibration_file(), index_col=0).loc["central (e)", "beta"])
    rows = {}
    for label, kw in (("Leontief fuel (setting of 20 Oct 2026)", {}), ("value added-energy bundle (MANAGE-WB elasticities)",
                                                           dict(energy_nest=NEST_LR, sr_energy_nest=NEST_SR)),
                      ("bundle, 2028-2030 at the old/new capital blend 0.35", dict(energy_nest=NEST_BLEND, sr_energy_nest=NEST_SR))):
        R = CR.Runs("low", wage_curve=beta, hoarding=0.85, **kw)
        piece, src = R.pieces()
        pw = src["public works"]
        works = {2025: pw["2025"], 2026: pw["2026 central"], 2027: pw["2027 NEP x 2025 rate (central)"]}
        clean = R.run(set(), piece=piece)
        for shocks, name in (({"oil"}, "oil alone"), (set(CR.SHOCKS), "all four shocks")):
            out = R.measures(clean, R.run(shocks, piece=piece), works=works if "public works" in shocks else {}, poor=True)[0]
            rows[f"{label}: {name}"] = {k: out[k] for k in KEYS}
            print(label, name, {k: round(out[k], 3) for k in KEYS}, flush=True)
    t = pd.DataFrame(rows).T
    stamp = pd.Timestamp.today()
    f = paths.output_dir() / f"energy_nest_oil_check_{stamp:%Y%m%d_%H%M}{_common.sam_tag()}_hoarding0.85.md"
    f.write_text("\n".join([f"# Value added-energy bundle: the central 2026 case with a value added-energy bundle ({stamp:%d %B %Y, %H:%M})", "",
                            "**NOT FOR CITATION** (Infinity GEM 0.3.11). Elasticities from MANAGE-WB's bridge-file defaults "
                            "(capital-skilled labour-energy bundle old 0.1 / new 0.8; energy carriers 0.5): "
                            f"2028-2030 {NEST_LR} (blend row: {NEST_BLEND['sigma_ve']}); 2025-2027 {NEST_SR}, centred on each baseline "
                            f"year (CGE.energy_shares_at). Infinity GEM's own SAM; hoarding 0.85; wage-curve beta {beta:.3f}; "
                            "public capital low. Script `scenarios/energy_nest_oil_check.py`.", "", t.to_markdown(floatfmt=".3f")]),
                 encoding="utf-8")
    print("saved", f)


if __name__ == "__main__":
    main()
