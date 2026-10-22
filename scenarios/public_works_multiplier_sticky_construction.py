"""Does the model's public-works multiplier rise if construction prices do not fall? (18 Oct 2026)

18 Oct 2026: a test of construction prices that do not fall. In the 2026 scenarios' setting (combined_revised.py: '0.3
recommended', flexible short-run prices, wage curve beta 7.14), public works take 0.49 point off 2026 GDP for a fall in public
construction of about 2.2% of GDP: a multiplier of about 0.2, against about 1.0-1.1 in PSA's quarterly data
(preshock/freeze_multiplier_lp.py; with budget-cycle controls, preshock/freeze_multiplier_budget_cycle.py). One suspected cause
is that construction gets cheaper in the model when public works are cut (the forward-looking CGE, Build 2c). This runs the public-works shock
ALONE under:
  - the 2026 scenarios' setting (flexible prices);
  - construction's price rigid downward (cge.py pricing='sticky', sticky_acts=['acons']; stickiness 1.0 and 0.6);
  - every non-farm price rigid downward (review D2, high, stickiness 0.6);
  - with the wage curve at the 2026 scenarios' beta (7.14) throughout, so only the price rule changes; and once with no wage curve
    (fixed peso wages) to show the labour rule's weight.
Multiplier = -(GDP effect, % of GDP) / (public-construction fall, % of GDP), 2026 and 2025, from the model's own accounts
(the construction fall is the shock piece's size in the SAM's units, reported by the run). NOT FOR CITATION.
Run:  py scenarios/public_works_multiplier_sticky_construction.py
"""
import datetime as dt
import sys

from _common import ROOT, SCENARIO_SAM, calibration_file, out_tag
import pandas as pd

sys.path.insert(0, str(ROOT / "preshock"))
from infinity_gem import paths                                                     # noqa: E402
import combined_revised as CR                                                   # noqa: E402

# 0.3.10 (18 Oct 2026, evening): on Infinity GEM's own SAM (INFINITY_GEM_SCENARIO_SAM=own) the wage curve is that SAM's own calibration
# (setting of 18 Oct 2026); on IFPRI's SAM the value of 17-18 Oct 2026, 7.1405, as before.
B = 7.1405 if SCENARIO_SAM == "ifpri" else float(pd.read_csv(calibration_file(), index_col=0).loc["central (e)", "beta"])
CASES = {
    f"central setting (flexible prices; beta {B:.2f})": dict(wage_curve=B),
    f"construction rigid downward, stickiness 1.0 (beta {B:.2f})": dict(wage_curve=B, sr_pricing="sticky", sr_stickiness=1.0, sticky_acts=["acons"]),
    f"construction rigid downward, stickiness 0.6 (beta {B:.2f})": dict(wage_curve=B, sr_pricing="sticky", sr_stickiness=0.6, sticky_acts=["acons"]),
    f"all non-farm prices rigid downward, 0.6 (D2 high; beta {B:.2f})": dict(wage_curve=B, sr_pricing="sticky", sr_stickiness=0.6),
    "central prices, no wage curve (fixed peso wages)": dict(wage_curve=None),
}
CUT_PCT = {2025: 263.8 / 28_009.93 * 100, 2026: 674.7 / 30_519.0 * 100}   # PSA construction falls vs 2024 (Note B) / nominal GDP (_common.PSA_GDP; DBCC 2026)


def main():
    rows = {}
    for name, kw in CASES.items():
        R = CR.Runs("low", **kw)
        piece, _ = R.pieces()
        clean, pw = R.run(set(), piece=piece), R.run({"public works"}, piece=piece)
        gap = (pw.table.real_gdp / clean.table.real_gdp - 1) * 100
        inv = (pw.table.real_investment / clean.table.real_investment - 1) * 100 if "real_investment" in pw.table else None
        cpi = (pw.table.cpi / clean.table.cpi - 1) * 100
        r = {"GDP 2025 (%)": float(gap[2025]), "GDP 2026 (%)": float(gap[2026]), "CPI 2026 (%)": float(cpi[2026])}
        if inv is not None:
            r["real investment 2026 (%)"] = float(inv[2026])
        r["multiplier 2026"] = -r["GDP 2026 (%)"] / CUT_PCT[2026]
        rows[name] = r
        print(name, {k: round(v, 3) for k, v in r.items()}, flush=True)
    t = pd.DataFrame(rows).T
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    out = paths.output_dir() / f"public_works_multiplier_sticky_construction_{stamp}{out_tag()}.md"
    out.write_text("\n".join([
        f"# Public-works multiplier with construction prices that do not fall ({dt.date.today():%d %B %Y})", "",
        "**NOT FOR CITATION** (Infinity GEM 0.3.10). Script: `scenarios/public_works_multiplier_sticky_construction.py`. "
        f"SAM: {CR.SAM_VARIANT}. Public-works shock alone (PSA's 2025-26 construction falls), public capital low, against the no-shock path. Multiplier 2026 "
        f"= -(GDP effect) / (2026 construction fall of {CUT_PCT[2026]:.2f}% of GDP). PSA data: about 1.0-1.1 "
        "(`outputs/freeze_multiplier_budget_cycle_20261018_1459.md`).", "", t.to_markdown(floatfmt=".3f")]), encoding="utf-8")
    print("saved", out)


if __name__ == "__main__":
    main()
