"""Scenario: the 2026 fertilizer price shock at its measured size (step 2 of the combined run; 0.3.7, 15 Oct 2026).

Size: World Bank Pink Sheet urea, % change vs January-February 2026 (preshock/agri_price_shock_size.py): conflict period
(March 2026 to latest) central, calendar 2026 and the latest month as the range; the same windows as the oil shock.
Channel: each fertilizer user's unit cost rises by its fertilizer cost share (PSA 2018 240-industry table, sector 110)
x the price change (infinity_gem.oil.fertilizer_cost_shock). The I-O shares are at basic prices (palay 1.5%, maize 3.2% of
output), probably below farm cost-and-returns surveys, so the effect is a LOWER bound; the econometric check is
preshock/agri_supply_response.py (palay -2% to -4% for +35% fertilizer; fragile).
Model: '0.3 recommended' with the rice split and land fixed by crop (as the El Nino run), 2026 rice tariff 15%; short run
with all skill levels able to lose jobs; households by infinity_gem.microlink.
NOT FOR CITATION until reviewed. Run:  py scenarios/fertilizer_2026_measured.py
"""
import datetime as dt
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "preshock")]
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from infinity_gem.microlink import MicroLink                          # noqa: E402
from infinity_gem.oil import fertilizer_cost_shares, fertilizer_cost_shock   # noqa: E402
from infinity_gem.settings import cge_model, short_run_closure         # noqa: E402
from agri_price_shock_size import shock_sizes                      # noqa: E402
from elnino_to_cge import policy_2026                              # noqa: E402


def main():
    sizes = shock_sizes()["urea (central)"]
    m = cge_model("0.3 recommended", rice=True, sam_variant="ifpri", **short_run_closure("0.3 recommended"), land="fixed")   # 0.3.10: IFPRI, as run
    base = policy_2026(m)
    b = m.solve(base)
    ml = MicroLink(m)
    shares = fertilizer_cost_shares()
    R = "family inflation, reconciled to the SAM (recommended)"
    rows = {}
    for window, x in sizes.items():
        s = m.solve(dict(base, **fertilizer_cost_shock(m, x / 100, shares)))
        assert s.ok, s.message
        link = ml.link_variables(m, b, s)
        exp = ml.expected_results(link)["value"]
        pct = lambda v, a: (float(s[v][m.A.index(a)]) / float(b[v][m.A.index(a)]) - 1) * 100
        rows[f"{window}: urea {x:+.1f}%"] = {
            "palay output (%)": pct("QA", "arice"), "maize output (%)": pct("QA", "amaiz"),
            "vegetables output (%)": pct("QA", "avege"), "sugarcane output (%)": pct("QA", "asugr"),
            "real GDP (%)": (m.gdp(s)["real"] / m.gdp(b)["real"] - 1) * 100,
            "consumer prices (%)": (float(s["CPI"]) / float(b["CPI"]) - 1) * 100,
            "new poor persons, own baskets": exp[f"{R}: change in poor persons"],
            "new poor persons, group method": exp["group inflation (Infinity GEM published method): change in poor persons"]}
    t = pd.DataFrame(rows)
    print(t.round(3).to_string())
    sh = pd.Series(shares).sort_values(ascending=False)
    L = [f"# The 2026 fertilizer price shock at its measured size ({dt.date.today():%d %B %Y})", "",
         "**NOT FOR CITATION** (Infinity GEM 0.3.7). Script: `scenarios/fertilizer_2026_measured.py`. Urea, World Bank Pink Sheet, "
         "vs January-February 2026 (`outputs/agri_price_shock_size_20261015.md`). One year, short run, 2026 rice tariff; fertilizer alone.", "",
         t.to_markdown(floatfmt=",.3f"), "",
         "## Fertilizer cost per peso of output (PSA 2018 I-O, sector 110), % (activities above 0.1%)", "",
         (sh[sh > 1e-3] * 100).round(2).to_frame("share (%)").to_markdown(), "",
         "**Reading.** At PSA's input-output cost shares the fertilizer shock is small next to oil and El Nino: palay output falls "
         "far less than the econometric check (-2% to -4% for +35%, `outputs/agri_supply_response_20261015.md`), so this is a "
         "lower bound. Urea is back near its January-February level by September 2026 (latest month), so the 2027 crops face "
         "little of it."]
    out = ROOT / "outputs" / f"fertilizer_2026_measured_{dt.date.today():%Y%m%d}.md"
    out.write_text(chr(10).join(L) + chr(10), encoding="utf-8")
    print("saved", out)


if __name__ == "__main__":
    main()
