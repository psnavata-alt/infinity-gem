"""Write the macro-micro link file for a scenario (0.3.5, 14 Oct 2026).

    py scenarios/micro_link_export.py                          # the five September 2026 shocks (specs/five_shocks_2026_central.json)
    py scenarios/micro_link_export.py specs/<other>.json       # any saved spec: {"closure": {...}, "spec": {...}}

Output: outputs/Infinity_GEM_micro_link_<spec name>_<date>.xlsx and a folder of the same name with one CSV per table (for the
a Stata do-file, a Stata do-file (not included)). The run stops if the model does not solve, or if the September 2026 spec no longer reproduces the published September 2026 GDP and new-poor figures.
"""
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from infinity_gem.cge import CGE            # noqa: E402
from infinity_gem.microlink import MicroLink  # noqa: E402
from infinity_gem.microsim import Microsim  # noqa: E402

# The reproduction test of the September 2026 spec is check ML1 (checks/run_all_checks.py), not this script (15 Oct 2026).


def run(spec_file: Path):
    d = json.loads(spec_file.read_text(encoding="utf-8"))
    closure = {k: (tuple(v) if isinstance(v, list) else v) for k, v in d["closure"].items()}
    m = CGE.from_sam(**closure)
    b = m.solve()
    s = m.solve(d["spec"])
    assert b.ok and s.ok, f"the model did not solve ({s.message}); no file written"
    g0, g1 = m.gdp(b)["real"], m.gdp(s)["real"]
    gdp_pct = (g1 / g0 - 1) * 100
    new_poor = Microsim().from_cge(m, b, s)["new_poor"]
    print(f"{spec_file.stem}: real GDP {gdp_pct:+.4f}%, new poor {new_poor:,.0f}")
    ml = MicroLink(m)
    link = ml.link_variables(m, b, s, scenario=f"{spec_file.stem}: " + " ".join(d.get("_about", [""])[:1]),
                             settings="Infinity GEM default ('0.2 published'), closure " + json.dumps(d["closure"]))
    out = ROOT / "outputs" / f"Infinity_GEM_micro_link_{spec_file.stem}_{dt.date.today():%Y%m%d}.xlsx"
    ml.write(link, out)
    print("saved", out)
    return ml, link


if __name__ == "__main__":
    f = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "specs" / "five_shocks_2026_central.json"
    if not f.is_absolute() and not f.exists():
        f = Path(__file__).resolve().parent / f
    ml, link = run(f)
    print(ml.expected_results(link).round(2).to_string())
