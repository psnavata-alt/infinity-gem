"""Geopolitics: what a rise in geopolitical risk does to the peso, FDI and remittances.

NOT FOR CITATION until reviewed. Run:  py preshock/geopolitics_lp.py

Local projections (Jorda 2005; infinity_gem.svar.local_projection, check LP1), monthly 2013-2026:
  shock = the Caldara-Iacoviello geopolitical risk index for the Philippines (GPR; Caldara and Iacoviello 2022, AER), in
  levels (some months are zero, so no logs), treated as exogenous to the Philippine economy given its own lags and lagged world oil prices;
  responses, cumulated from month t-1 to t+h: the peso per dollar (100 x log), remittances (100 x log), FDI (US$ million,
  level change); controls: 3 lags of each response, the shock and 100 x log oil, plus calendar-month dummies.
Reported per DOUBLING of the GPR from its 2013-2026 average (a rise equal to the mean), with 90% bands (Newey-West).

Data: a compiled monthly panel (not distributed). These are our own
estimates, not a reproduction of the reference VAR.
"""
import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from infinity_gem.stochastic import load_task1_monthly  # noqa: E402
from infinity_gem.svar import local_projection           # noqa: E402



def main():
    m = load_task1_monthly()
    shock = m["gpr"]
    DOUBLING = float(m["gpr"].mean())
    loil = (100 * np.log(m["oil"])).rename("loil")
    months = pd.get_dummies(pd.Series(m.index.month, index=m.index), prefix="m", drop_first=True, dtype=float)
    resp = {"Peso per US$ (%, + = weaker peso)": 100 * np.log(m["fx"]),
            "Remittances (%)": 100 * np.log(m["remit"]),
            "FDI (US$ million a month)": m["fdi"]}
    tabs = {}
    for name, y in resp.items():
        lp = local_projection(y, shock, controls=loil.to_frame(), H=12, lags=3, cumulative=True, extra=months)
        tabs[name] = (lp[["beta", "low90", "high90"]] * DOUBLING).assign(n=lp["n"])
        print("==", name); print(tabs[name].loc[[0, 1, 3, 6, 12]].round(2).to_string())
    stamp = dt.date.today().strftime("%Y%m%d")
    L = [f"# Geopolitical risk and the peso, FDI and remittances: local projections ({dt.date.today():%d %B %Y})", "",
         "**NOT FOR CITATION** until reviewed (Infinity GEM 0.3.5). Script: `preshock/geopolitics_lp.py`. Monthly, "
         f"{m.index.min():%b %Y}-{m.index.max():%b %Y}; a compiled panel (not distributed). Effects of a **doubling** of the "
         "Caldara-Iacoviello GPR index for the Philippines from its average, cumulated from the month before; 90% bands (Newey-West). Controls: three lags of "
         "the response, the GPR and world oil prices; calendar-month dummies.", ""]
    for name, t in tabs.items():
        tt = t.loc[[0, 1, 2, 3, 6, 9, 12]].reset_index().rename(columns={"h": "months after", "beta": "effect", "low90": "90% low", "high90": "90% high"})
        L += [f"## {name}", "", tt.to_markdown(index=False, floatfmt=".2f") if hasattr(tt, "to_markdown") else tt.to_string(index=False), ""]
    L += ["**Into the CGE:** the FDI effect enters investment one for one; a persistent peso effect enters as an exchange-rate "
          "shock only if a closure fixes the exchange rate (the standard CGE lets it adjust). Bands that include zero mean the data do not "
          "pin the effect down.", ""]
    rep = ROOT / "outputs" / f"geopolitics_lp_{stamp}.md"
    rep.write_text("\n".join(L), encoding="utf-8")
    print("saved", rep)


if __name__ == "__main__":
    main()
