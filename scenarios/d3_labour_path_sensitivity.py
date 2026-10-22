"""Review D3 (17 Oct 2026): the central 2026 run with the no-shock 2026 labour path from the trend rule
(psa_labour_growth(y2026="trend")) instead of observed 2026 employment. Wage curve at the central beta. NOT FOR CITATION.
Run:  py scenarios/d3_labour_path_sensitivity.py"""
import pandas as pd
from _common import ROOT  # noqa: F401
import combined_revised as CR
from infinity_gem import paths
from infinity_gem.dynamic import psa_labour_growth

beta = float(pd.read_csv(__import__("_common").calibration_file(), index_col=0).loc["central (e)", "beta"])
R = CR.Runs("low", wage_curve=beta, labour_growth=psa_labour_growth(y2026="trend"))
piece, src = R.pieces()
pw = src["public works"]
works = {2025: pw["2025"], 2026: pw["2026 central"], 2027: pw["2027 NEP x 2025 rate (central)"]}
out = R.measures(R.run(set(), piece=piece), R.run(set(CR.SHOCKS), piece=piece), works=works, poor=True)[0]
keys = ["GDP gap 2026 (%)", "GDP gap 2027 (%)", "GDP gap 2030 (%)", "cumulative GDP loss 2025-2030 (₱ bn)",
        "new poor 2026 (M, own baskets)", "new poor 2027 (M, own baskets)"]
t = pd.Series({k: out[k] for k in keys}, name="2026 labour path: trend rule")
f = paths.output_dir() / f"d3_labour_path_sensitivity_{pd.Timestamp.today():%Y%m%d_%H%M}.md"
f.write_text("# Review D3: no-shock 2026 labour path from the trend rule\n\n**NOT FOR CITATION** (0.3.9). Central (observed 2026 path): "
             "2026 GDP -1.22%, 2027 -0.97%, 2030 -0.69%, loss ₱1,654 bn, new poor 3.14 / 1.76 M.\n\n" + t.to_frame().to_markdown(floatfmt=".3f"), encoding="utf-8")
print(t.round(3).to_string()); print("saved", f.name)
