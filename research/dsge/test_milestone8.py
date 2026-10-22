"""DSGE research, milestone 8 tests (19 Oct 2026): the QPM monetary block (qpm.py) calibrated to the BSP's PAMPh.

T26 determinate at the default calibration and at the PAMPh match;
T27 the match: distance below 100 (from about 360 at the textbook defaults); CPI inflation y/y within 0.03 pp of PAMPh in
    quarters 1-8 and the GDP-growth trough within 0.05 pp;
T28 signs of a tightening: output gap and inflation fall, the peso appreciates.
Writes outputs/dsge_qpm_pamph_calibration_<stamp>.md.
"""
import datetime as dt
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pamph_targets as T  # noqa: E402
import qpm                 # noqa: E402

results = []


def check(name, ok, detail):
    results.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


qpm.irf(qpm.Params(), "e_i")
p, d, d0, m, tgt = qpm.match_pamph()
qpm.irf(p, "e_i")
check("T26 determinate (defaults and the PAMPh match)", True, "")
e_inf = max(abs(m["infl"][q] - tgt["infl"][q]) for q in (1, 2, 3, 4, 5, 6, 7, 8))
e_gr = abs(min(m["growth"].values()) - min(tgt["growth"].values()))
check("T27 matches PAMPh's monetary responses", d < 100 and e_inf < 0.03 and e_gr < 0.05,
      f"distance {d:.1f} (defaults {d0:.1f}); inflation max gap {e_inf:.3f} pp; growth trough gap {e_gr:.3f} pp")
r = qpm.irf(p, "e_i", 1.0)
check("T28 signs of a tightening", r["ygap"][1] < 0 and r["pi"][2] < 0 and r["z"][0] < 0,
      f"output gap q2 {r['ygap'][1]:.3f}, inflation q3 {r['pi'][2]:.3f}, real exchange rate q1 {r['z'][0]:.3f} (per 1 pp)")
rows = []
for k, lab in (("rate", "policy rate (pp p.a.)"), ("growth", "GDP growth (pp y/y)"), ("infl", "CPI inflation (pp y/y)"), ("fx", "nominal exchange rate (100 log)")):
    rows += [{"variable": lab, "source": "PAMPh", **{f"q{q}": tgt[k][q] for q in T.QUARTERS}},
             {"variable": lab, "source": "QPM", **{f"q{q}": m[k][q] for q in T.QUARTERS}}]
out = HERE.parents[1] / "outputs" / f"dsge_qpm_pamph_calibration_{dt.datetime.now():%Y%m%d_%H%M}.md"
out.write_text("\n".join([
    f"# Milestone 8: the QPM monetary block calibrated to the BSP's PAMPh ({dt.datetime.now():%d %B %Y, %H:%M})", "",
    "**NOT FOR CITATION** (research code, `research/dsge/qpm.py`). Targets read off PAMPh's charts (BSP WPS 2020-12, Annex 1.A; "
    f"`pamph_targets.py`). Distance {d:.1f} (textbook defaults {d0:.1f}).", "",
    "## Calibrated parameters", "", pd.Series(asdict(p)).to_frame("value").to_markdown(floatfmt=".3f"), "",
    "## Monetary-policy responses (+0.80 pp policy rate in quarter 1)", "",
    pd.DataFrame(rows).set_index(["variable", "source"]).to_markdown(floatfmt=".2f")]) + "\n", encoding="utf-8")
n_pass = sum(ok for _, ok, _ in results)
print(f"\n{n_pass}/{len(results)} passed; saved {out.name}")
sys.exit(0 if n_pass == len(results) else 1)
