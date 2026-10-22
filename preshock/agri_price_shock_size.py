"""How big are the 2026 world rice and fertilizer price shocks? (and step 2 of the combined run;
0.3.7, 15 Oct 2026)

Same windows as preshock/oil_shock_size.py (15 Oct 2026: crude at the conflict-period change, with the range), each
against the pre-conflict months January-February 2026:
  calendar 2026 so far    the average of every 2026 month on file;
  conflict period         the average from March 2026 to the latest month (central);
  latest month            if prices stay where they are now.
Data: World Bank Commodity Markets ('Pink Sheet') monthly prices, nominal US$ (data/raw/agri/WorldBank_PinkSheet_...csv;
CC BY 4.0; downloaded 14 Oct 2026, to September 2026):
  rice   Viet Nam 5% broken, the benchmark of the Philippines' main supplier (78% of 2023 rice imports by value, PSA:
         data/raw/agri/PSA_OpenSTAT_0032L4DMFD2_...csv) and the reference price of EO 105's rice tariff (USDA FAS
         GAIN RP2026-0004); Thai 5% shown as a cross-check;
  urea   Urea (the main nitrogen fertilizer; DAP shown as a cross-check).
NOT FOR CITATION until reviewed. Run:  py preshock/agri_price_shock_size.py
"""
import datetime as dt
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from infinity_gem import paths                                             # noqa: E402

PINK = paths.DATA_RAW / "agri" / "WorldBank_PinkSheet_fertilizer_rice_maize_monthly_1960-2026.csv"
SERIES = {"rice, Viet Nam 5% (central)": "Rice, Viet Namese 5% (($/mt))", "rice, Thai 5% (check)": "Rice, Thai 5% (($/mt))",
          "urea (central)": "Urea (($/mt))", "DAP (check)": "DAP (($/mt))"}
WINDOWS = ("calendar 2026 so far", "conflict period (Mar 2026 to latest)", "latest month")


def prices() -> pd.DataFrame:
    d = pd.read_csv(PINK, comment="#")
    d["month"] = pd.PeriodIndex(d["month"], freq="M")
    d = d.set_index("month")[list(SERIES.values())]
    return d.apply(pd.to_numeric, errors="coerce").rename(columns={v: k for k, v in SERIES.items()})


def shock_sizes() -> pd.DataFrame:
    """% change vs January-February 2026, by window (rows) and series (columns)."""
    p = prices()
    p26 = p[p.index.year == 2026].dropna(how="all")
    base = p26.loc["2026-01":"2026-02"].mean()
    last = p26.index.max()
    w = {WINDOWS[0]: p26.mean(), WINDOWS[1]: p26.loc["2026-03":].mean(), WINDOWS[2]: p26.loc[last]}
    out = pd.DataFrame({k: (v / base - 1) * 100 for k, v in w.items()}).T
    out.attrs["latest"] = str(last)
    return out


def main():
    p = prices()
    t = shock_sizes()
    print(t.round(2).to_string())
    L = [f"# The 2026 world rice and fertilizer price shocks ({dt.date.today():%d %B %Y})", "",
         "**NOT FOR CITATION** (Infinity GEM 0.3.7). Script: `preshock/agri_price_shock_size.py`. World Bank Pink Sheet, monthly, "
         f"nominal US$, to {t.attrs['latest']}; % change against the January-February 2026 average (as the oil shock, "
         "`outputs/oil_shock_size_*.md`).", "",
         t.round(2).to_markdown(), "",
         "## Monthly prices, 2025-2026 (US$/t)", "",
         p.loc["2025-01":].round(1).to_markdown(), "",
         "**Reading.** Rice: the Viet Nam 5% price (the Philippines' main supplier; EO 105's tariff reference) rose through 2026; "
         "since EO 105 lowers the tariff when world prices rise and it is already at its 15% floor, the tariff stays at 15%. "
         "Urea: a spike in March-May 2026 (the conflict period), back near its January-February level by July-September; the "
         "conflict-period average is the central fertilizer shock, the latest month the low end."]
    out = ROOT / "outputs" / f"agri_price_shock_size_{dt.date.today():%Y%m%d}.md"
    out.write_text(chr(10).join(L), encoding="utf-8")
    print("saved", out)


if __name__ == "__main__":
    main()
