"""How big is the 2026 oil shock? (step 1 of the combined run; 0.3.7, 15 Oct 2026)

The CGE takes the world price of petroleum as a % change against a no-shock baseline. Until now the earlier analysis used a round
+20% (an illustration). This script measures the 2026 shock from data instead.

Data (public version): the World Bank Pink Sheet's monthly Dubai crude price (CC BY 4.0) and, for imported fuel
products, US wholesale diesel and gasoline from the EIA Short-Term Energy Outlook (public domain), through
preshock/shock_paths.oil_actual_monthly(). Monthly averages smooth the March 2026 spike.
Baseline (no-shock level): the pre-conflict months January-February 2026; 2025 as a cross-check.
Shock sizes (each against the baseline), for the combined run:
  calendar 2026 so far    the average of every 2026 month on file;
  conflict period         the average from March 2026 (the spike) to the latest month;
  latest four weeks       (the name is kept for the scripts that read it) the latest month: if prices stay there.
NOT FOR CITATION until reviewed. Run:  py preshock/oil_shock_size.py
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

# Philippine oil-product consumption mix, 2023: International Energy Agency, as reported by GMA News (V. A. Ferreras,
# 'Which oil products are consumed in the Philippines?', 16 Apr 2026): gas/diesel oil 47.8%, motor gasoline 29.3%,
# LPG/ethane 10.1%, other products 12.8%. About 98% of fuel is imported (same source, DOE), so it stands in for the import mix.
# Snapshot of the article: a reference copy (not distributed). To verify against the IEA's own balance before release.
MIX = {"diesel": 0.478, "gasoline": 0.293, "LPG and other products": 0.229}


def shock_sizes() -> pd.DataFrame:
    """% changes vs January-February 2026 for each window: crude (Dubai) and imported fuel products (weighted).
    Used by scenarios/oil_2026_measured.py, so the CGE takes exactly what this script measures."""
    return _compute()[4][["crude (Dubai)", "fuel products, weighted"]]


def _compute():
    """Public version (Infinity GEM): the monthly World Bank Pink Sheet Dubai price (CC BY 4.0) for crude, and US
    wholesale diesel and gasoline from the EIA Short-Term Energy Outlook (public domain) as the product-price proxies.
    The development copy used a compiled weekly tracker that may not be redistributed; monthly averages smooth the
    March 2026 spike, so the conflict-period sizes here are smaller than with weekly data."""
    import shock_paths as _SP
    a = _SP.oil_actual_monthly()
    a.index = a.index.to_timestamp()
    s = a["dubai"].dropna()
    base = float(s.loc["2026-01":"2026-02"].mean())
    base25 = float(s.loc["2025-01":"2025-12"].mean()) if len(s.loc["2025"]) else float("nan")
    last = s.index[-1]
    sizes = {"calendar 2026 so far": s.loc["2026-01":].mean(), "conflict period (Mar 2026 to latest)": s.loc["2026-03":].mean(),
             "latest four weeks": s.iloc[-1:].mean()}
    windows = {"calendar 2026 so far": ("2026-01", None), "conflict period (Mar 2026 to latest)": ("2026-03", None),
               "latest four weeks": (None, None)}
    def chg(x, k):
        x = x.dropna()
        a_, _ = windows[k]
        v = x.iloc[-1:].mean() if a_ is None else x.loc[a_:].mean()
        return (v / x.loc["2026-01":"2026-02"].mean() - 1) * 100
    crude_pct = {k: (v / base - 1) * 100 for k, v in sizes.items()}
    ptab = pd.DataFrame({"crude (Dubai)": crude_pct,
                         "diesel import cost": {k: chg(a["diesel"], k) for k in windows},
                         "gasoline import cost": {k: chg(a["gasoline"], k) for k in windows}})
    ptab["fuel products, weighted"] = (MIX["diesel"] * ptab["diesel import cost"] + MIX["gasoline"] * ptab["gasoline import cost"]
                                       + MIX["LPG and other products"] * ptab["crude (Dubai)"])
    tab = pd.DataFrame({"Dubai, US$/bbl": sizes,
                        "% vs Jan-Feb 2026 (pre-conflict)": {k: (v / base - 1) * 100 for k, v in sizes.items()},
                        "% vs 2025 average": {k: (v / base25 - 1) * 100 for k, v in sizes.items()}})
    monthly = a.loc["2025-01":f"{last:%Y-%m}"]
    return s, base, base25, tab, ptab, monthly, last


def main():
    s, base, base25, tab, ptab, monthly, last = _compute()
    print(ptab.round(1).to_string()); print(tab.round(1).to_string()); print(monthly.round(1).to_string())
    md = lambda df: df.to_markdown(floatfmt=",.1f") if hasattr(df, "to_markdown") else df.to_string()
    L = [f"# The 2026 oil shock, measured ({dt.date.today():%d %B %Y})", "",
         "**NOT FOR CITATION** (Infinity GEM 0.3.7). Script: `preshock/oil_shock_size.py`. Data: the World Bank Pink Sheet's monthly Dubai price and EIA STEO US wholesale diesel and gasoline (public; "
         f"{len(s)} months to {last:%B %Y}).", "",
         f"Baseline: January-February 2026 average, US${base:.1f}/bbl (2025 average US${base25:.1f}).", "",
         "## Shock sizes", "", md(tab), "",
         "## Imported fuel products (% vs January-February 2026)", "", md(ptab), "",
         "Diesel and gasoline: US wholesale prices (EIA STEO; a proxy for Singapore product prices). Weights: the Philippine oil-product "
         "consumption mix, 2023 (IEA, as reported by GMA News, 16 Apr 2026): diesel 47.8%, gasoline 29.3%, LPG and other products 22.9% "
         "(these take crude's change: no import price on file). 15 Oct 2026: products at their own measured change, weighted by "
         "what the Philippines imports.", "",
         "## The monthly series", "", md(monthly), "",
         "**For a combined run:** the conflict-period average is the shock that has actually happened since March; "
         "the latest month shows where prices are now; the calendar-year figure dilutes the shock with the pre-conflict months."]
    out = ROOT / "outputs" / f"oil_shock_size_{dt.date.today():%Y%m%d}.md"
    out.write_text(chr(10).join(L), encoding="utf-8")
    print("saved", out)


if __name__ == "__main__":
    main()
