"""The central 2026 combined run on the updated SAM (17 Oct 2026).

Runs scenarios/combined_revised.py's central case (public capital low) with the model calibrated to the 2024 SAM
(tools/update_sam.py: the IFPRI 2023 rice-split SAM moved to PSA's 2024 nominal totals by cross-entropy), the path starting
in 2024, the year before the shocks. The wage curve is recalibrated to the central target (labour input 2026 = Okun's e x the
model's own 2026 growth effect). Peso amounts enter as shares of their year's GDP times the base SAM's GDP, as in the central
run; here the base SAM is 2024's, so _common.SAM_GDP_2023 and combined_revised.TO_2025 are set to the 2024 SAM's GDP for this
run only. Compared with the 2023-SAM central run (outputs/engine_sensitivities_parts/variant_0.csv). NOT FOR CITATION.
Run:  py scenarios/sam_year_sensitivity.py [2024]   (about 10 minutes)
"""
import sys

from _common import ROOT
import pandas as pd

sys.path.insert(0, str(ROOT / "preshock"))
import _common                                                                  # noqa: E402
from infinity_gem import paths, settings                                           # noqa: E402
import calibrate_wage_curve as CW                                               # noqa: E402
import combined_revised as CR                                                   # noqa: E402
import okun                                                                     # noqa: E402

YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
KEYS = ("GDP gap 2025 (%)", "GDP gap 2026 (%)", "GDP gap 2027 (%)", "GDP gap 2030 (%)", "cumulative GDP loss 2025-2030 (₱ bn)",
        "consumer prices 2026 (%)", "new poor 2025 (M, own baskets)", "new poor 2026 (M, own baskets)",
        "new poor 2027 (M, own baskets)", "debt-to-GDP change 2030 (pp)")


def main():
    base_dyn, base_cge = settings.dynamic_kwargs, settings.cge_model
    CR.dynamic_kwargs = lambda *a, **k: base_dyn(*a, sam_year=YEAR, **k)
    CR.cge_model = lambda *a, **k: base_cge(*a, sam_year=YEAR, **k)
    m = base_cge("0.3 recommended", rice=True, sam_year=YEAR)
    b0 = m.solve()
    if not b0.ok:                                        # rigging audit part E: never use an unsolved benchmark
        raise RuntimeError(f"benchmark on the {YEAR} SAM did not solve ({b0.message}, residual {b0.residual_max:.2e})")
    sam_gdp = float(m.gdp(b0)["nominal_expenditure"])
    _common.SAM_GDP_2023 = sam_gdp                       # this run only: the base SAM's GDP
    CR.TO_2025 = CR.PSA_GDP[2025] / sam_gdp
    e = float(okun.estimates().loc["2006-2026, all quarters", "elasticity e"])
    R = CR.Runs("low")
    piece, src = R.pieces()
    beta = CW.calibrate(lambda s: s[0] - e * s[3], R, piece)
    R.d.a["wage_curve"] = beta
    pw = src["public works"]
    works = {2025: pw["2025"], 2026: pw["2026 central"], 2027: pw["2027 NEP x 2025 rate (central)"]}
    clean = R.run(set(), piece=piece)
    out = R.measures(clean, R.run(set(CR.SHOCKS), piece=piece), works=works, poor=True)[0]
    row = {"base SAM": f"{YEAR} (updated)", "SAM nominal GDP (₱ bn)": sam_gdp, "wage-curve beta": beta, **{k: out[k] for k in KEYS}}
    for ms in ("A", "B", "C"):
        p = R.measures(clean, R.run(set(CR.SHOCKS), ms, piece=piece), works=works,
                       extra_spend={2027: CR.CATCHUP} if ms == "C" else None)[0]
        cost = {"A": CR.equiv_2025(CR.AID_2026, 2026), "B": CR.equiv_2025(CR.AID_2027, 2027), "C": CR.equiv_2025(CR.CATCHUP, 2027)}[ms]
        yr = 2026 if ms == "A" else 2027
        row[f"{ms}: poor protected {yr} (M)"] = out[f"new poor {yr} (M, own baskets)"] - p[f"new poor {yr} (M, own baskets)"]
        row[f"{ms}: output recovered per peso"] = (out["cumulative GDP loss 2025-2030 (₱ bn)"] - p["cumulative GDP loss 2025-2030 (₱ bn)"]) / cost
    stamp = pd.Timestamp.today()
    pd.Series(row).to_csv(paths.output_dir() / f"sam_year_sensitivity_{YEAR}_{stamp:%Y%m%d_%H%M}_row.csv")   # saved first
    ref = pd.read_csv(paths.output_dir() / "engine_sensitivities_parts" / "variant_0.csv", index_col=0).iloc[:, 0]
    left = {k: ref.get(k) for k in row}
    left["base SAM"], left["SAM nominal GDP (₱ bn)"] = "2023 (IFPRI)", 26160.604
    t = pd.DataFrame({"central (2023 SAM, 17 Oct 2026)": pd.Series(left, dtype=object), f"{YEAR} SAM": pd.Series(row, dtype=object)})
    print(t.to_string())
    f = paths.output_dir() / f"sam_year_sensitivity_{YEAR}_{stamp:%Y%m%d_%H%M}"
    t.to_csv(f.with_suffix(".csv"))
    L = [f"# The central 2026 run on the updated {YEAR} SAM ({stamp:%d %B %Y, %H:%M})", "",
         "**NOT FOR CITATION** (Infinity GEM 0.3.8). Script: `scenarios/sam_year_sensitivity.py`; SAM: "
         f"`tools/update_sam.py` (`outputs/sam_update_{YEAR}_*.md`). The path starts in {YEAR}; the wage curve is recalibrated to the "
         "central target; everything else as the central 2026 run (public capital low).", "", t.to_markdown()]
    f.with_suffix(".md").write_text("\n".join(L), encoding="utf-8")
    print("saved", f.with_suffix(".md"))


if __name__ == "__main__":
    main()
