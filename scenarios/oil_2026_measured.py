"""Scenario: the 2026 oil shock at its measured size (0.3.7, 15 Oct 2026).

Replaces the earlier illustrative +20%. 15 Oct 2026: +49%, with the range.
Crude (Dubai): +49% (conflict period, March 2026 to the latest week, vs January-February 2026), range +39% (calendar 2026)
to +68% (latest four weeks): preshock/oil_shock_size.py, outputs/oil_shock_size_20261015.md.
Imported fuel products: infinity_gem/oil.py assumes they move one-for-one with crude, but in 2026 they rose more. 15 Oct 2026: crude at +49%, and imported fuel products at their own measured change, weighted by what the Philippines actually
imports": diesel and gasoline import costs (MBIE, in US$) weighted by the 2023 product mix (IEA via GMA News), LPG and other
products at crude's change; all sizes read from preshock/oil_shock_size.py.
Model: '0.3 recommended' (petroleum split from chemicals, Philippine elasticities, LES demand, sticky peso wages); short run
with workers of all skill levels able to lose jobs (settings.short_run_closure), and long run. Households: FIES 2023 via
infinity_gem/microlink.py (group method = Infinity GEM's published method; own baskets = each family's own inflation).
NOT FOR CITATION until reviewed. Run:  py scenarios/oil_2026_measured.py
"""
import datetime as dt
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from infinity_gem.microlink import MicroLink                          # noqa: E402
from infinity_gem.oil import cge_oil_shock                             # noqa: E402
from infinity_gem.settings import cge_model, short_run_closure         # noqa: E402

sys.path.insert(0, str(ROOT / "preshock"))
from oil_shock_size import shock_sizes                            # noqa: E402
SIZES = shock_sizes()                                              # % vs Jan-Feb 2026, measured (no typed-in shock)
CENTRAL = "conflict period (Mar 2026 to latest)"


def main():
    rows = []
    for horizon, closure in (("short run", short_run_closure("0.3 recommended")), ("long run", {})):
        m = cge_model("0.3 recommended", **closure)
        b = m.solve()
        ml = MicroLink(m)
        g0 = m.gdp(b)["real"]
        cases = [(w, "weighted import mix") for w in SIZES.index] + [(CENTRAL, "moving with crude (old assumption)")]
        for window, pname in cases:
            crude = float(SIZES.loc[window, "crude (Dubai)"]) / 100
            prod = float(SIZES.loc[window, "fuel products, weighted"]) / 100
            spec = cge_oil_shock(m, crude)
            if pname == "weighted import mix":
                spec["pwm_scale"]["cpetr"] = 1 + prod
            s = m.solve(spec)
            assert s.ok, f"{horizon} {window} {pname}: {s.message}"
            link = ml.link_variables(m, b, s)
            rows.append({"horizon": horizon, "period": window, "fuel products": pname,
                         "crude (%)": crude * 100, "fuel products (%)": (prod if pname == "weighted import mix" else crude) * 100,
                         "real GDP (%)": (m.gdp(s)["real"] / g0 - 1) * 100,
                         "consumer prices (%)": (float(s["CPI"]) / float(b["CPI"]) - 1) * 100,
                         "real household consumption (%)": (float(s["QH"].sum()) / float(b["QH"].sum()) - 1) * 100,
                         "new poor, group method": float(ml.hd.poverty(link["_g"]).loc["Poor persons", "Change"]),
                         "new poor, own baskets": float(ml.poverty(link, ml.family_inflation(link)).loc["Poor persons", "Change"])})
    t = pd.DataFrame(rows).set_index(["horizon", "period", "fuel products"])
    print(t.round(3).to_string())
    md = t.to_markdown(floatfmt=",.2f") if hasattr(t, "to_markdown") else t.to_string()
    L = [f"# The 2026 oil shock at its measured size ({dt.date.today():%d %B %Y})", "",
         "**NOT FOR CITATION** (Infinity GEM 0.3.7). Script: `scenarios/oil_2026_measured.py`. Shock sizes: "
         "`outputs/oil_shock_size_20261015.md` (15 Oct: crude +49%, range +39% to +68%). '0.3 recommended'; short run = all skill "
         "levels can lose jobs. In the long run the CPI is the model's price anchor, so consumer prices do not move there by construction.", "",
         md, "",
         "**Reading.** 15 Oct 2026: crude at its measured change and imported fuel products at their own measured change, weighted by "
         "the Philippine product mix (preshock/oil_shock_size.py). The 'moving with crude' row shows the old assumption for comparison."]
    out = ROOT / "outputs" / f"oil_2026_measured_{dt.date.today():%Y%m%d}.md"
    out.write_text(chr(10).join(L), encoding="utf-8")
    print("saved", out)


if __name__ == "__main__":
    main()
