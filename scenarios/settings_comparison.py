"""The September 2026 policy scenarios under the two named settings, "0.2 published" and "0.3 recommended".

Static CGE (short and long run): infrastructure freeze (-₱238.3 bn construction), world oil prices +20%, Ayuda cut
(-₱90.21 bn to the bottom 40%), remittances -10%. Dynamic CGE, 2025-2030: freeze in 2025, and freeze plus the 2027
catch-up (+₱208.7 bn); under 0.3 with public capital off, low and high. 2025 pesos (same share of GDP as in the 2023 SAM).
Everything runs through app/engines.py, the same code as the Simulator.
Reviewed 16 Oct 2026: "0.3 recommended" is the citable setting; "0.2 published" reproduces past results.
Run:  py scenarios/settings_comparison.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pandas as pd                                   # noqa: E402

from _common import Report                            # noqa: E402
from app import engines as E                          # noqa: E402
from infinity_gem.settings import SETTINGS                # noqa: E402

SHOCKS = {"Infrastructure freeze (−₱238.3 bn)": E.Shocks(construction_bn=-238.3),
          "World oil prices +20%": E.Shocks(oil_pct=20.0),
          "Ayuda cut (−₱90.21 bn, bottom 40%)": E.Shocks(transfers_bn=-90.21),
          "Remittances −10%": E.Shocks(remit_pct=-10.0)}
KEYS = ["Real GDP (%)", "Real GDP (₱ bn)", "Consumer prices, CPI (%)", "Real household consumption (%)",
        "Employment, low-skill (%)", "New poor (persons, FIES 2023 base)"]

rows = []
for name, s in SHOCKS.items():
    for closure in E.CLOSURES:
        for st in reversed(SETTINGS):                 # 0.2 first
            r = E.run_cge(s, closure, None, st)
            row = {"shock": name, "horizon": closure, "setting": st}
            row.update({k: r["summary"][k] for k in KEYS} if r["ok"] else {"note": r["message"]})
            rows.append(row)
            print(name, closure, st, "ok" if r["ok"] else r["message"], flush=True)
static = pd.DataFrame(rows).set_index(["shock", "horizon", "setting"])

DYN = [("0.2 published", "off", False), ("0.3 recommended", "off", True), ("0.3 recommended", "low", True),
       ("0.3 recommended", "high", True)]
drows = []
for st, pc, hyb in DYN:
    for path, by_year in {"freeze only": {2025: -238.3}, "freeze + 2027 catch-up": {2025: -238.3, 2027: 208.7}}.items():
        r = E.run_dynamic(by_year, hybrid=hyb, setting=st, public_capital=pc)
        row = {"setting": st + ("" if st.startswith("0.2") else f", public capital {pc}"),
               "closure": "hybrid" if hyb else "long run every year", "path": path}
        row.update(r["summary"] if r["ok"] else {"note": r["message"]})
        drows.append(row)
        print(row, flush=True)
dyn = pd.DataFrame(drows).set_index(["setting", "closure", "path"])

rep = Report("September 2026 policy scenarios: Infinity GEM settings 0.2 published vs 0.3 recommended", "settings_comparison")
rep.p("**Reviewed 16 Oct 2026: \"0.3 recommended\" is the citable setting.** '0.2 published' reproduces the results "
      "published up to 7 Oct 2026 (check R0). '0.3 recommended' (infinity_gem/settings.py): petroleum split from chemicals, "
      "Philippine elasticities, LES household demand (Briones et al. 2023), IFPRI-style trade margins; over time also the "
      "documented baseline, capital tied to its industry, the hybrid closure and public capital (low: phi 0.083, KG 0.397 x GDP; "
      "high: phi 0.122, KG 0.296 x GDP). Home consumption is not included (not yet combined with LES; negligible "
      "effect). 2025 pesos.")
rep.h("Static CGE")
rep.table(static, floatfmt=",.3f")
rep.h("Dynamic CGE, cumulative 2025-2030")
rep.p("0.2 published: the method of the submitted slides (long-run closure every year, placeholder baseline); guide 09 step A "
      "gave −₱336 bn for the freeze. 0.3 rows add every upgrade at once; guide 09 steps D and E (without the static upgrades) "
      "gave −₱491 bn and −₱691 to −₱887 bn.")
rep.table(dyn, floatfmt=",.3f")
rep.save()
