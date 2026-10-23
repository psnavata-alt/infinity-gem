"""DSGE research and the money block (20 Oct 2026, about 10 PM). The question (20 Oct 2026, evening): do the "+0.1 to +0.75 million poor" from the
BSP's response to the 2026 oil shock count only the output cost of the tightening, or also the benefit of lower prices for the poor?

Answer by decomposition, each part one CGE run (central 2026 setting of 18 Oct 2026 on Infinity GEM's own SAM, labour hoarding 0.85; the link of
scenarios/qpm_cge_link.py mode=elastic). The BSP's response (the estimated rule minus the rate held for a year, from the oil DSGE of
research/dsge/oil_policy.py) enters the CGE through two channels: (1) real investment demand, scaled by 1 - theta x (real-rate gap,
pp) / 100; (2) the peso, scaled by the DSGE's real-exchange-rate gap. The CGE then gives prices and incomes, and the microsimulation
counts the poor from each family's OWN basket inflation and its group's nominal income change (infinity_gem.microlink.MicroLink.poverty:
PCI x nominal spending change / (1 + family inflation)). So the published count already nets the two. This script shows the parts:
- runs: both channels (the published link), the investment channel only, the peso channel only;
- within each run, three poverty counts: (a) incomes and prices (the published measure, "own baskets"); (b) incomes only, every
  family's prices held at the baseline; (c) prices only, nominal incomes held. (b) + (c) is not exactly (a): the counts are
  nonlinear (families cross the line), so the table shows all three.
Run (Git Bash, repository root):
  export INFINITY_GEM_SCENARIO_SAM=own
  py scenarios/bsp_oil_response_netting.py model=oilw theta_fix=0.73 spec=_long_stl_thfix0.73 oil=36 h=0.85 thetas=0.7,1.5,2
(23 Oct 2026: the default thetas follow the link's new central, 1.5, with 0.7 low and 2 high (DSGE milestone 25, the decision); the 20 Oct 2026 runs used thetas=0.55,2,3.3.)
(model=, theta_fix= and spec= as for qpm_cge_link.py source=dsge_oil; they select the DSGE chains. Output:
outputs/bsp_oil_response_netting_<stamp><tag>_oil<oil><spec>.md.)
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import _common                                                       # noqa: E402
import combined_revised as CR                                        # noqa: E402
import qpm_cge_link as QL                                            # noqa: E402  (its dsge_oil_annual reads model=/theta_fix= from argv)
from infinity_gem import paths                                           # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
YEARS = QL.YEARS                                                     # (2026, 2027): the years the DSGE's response feeds
RUNS = {"both channels (the published link)": ("inv", "fx"), "investment channel only": ("inv",), "peso channel only": ("fx",)}


def counts(R, ref, sim, y):
    """Three poverty counts for year y (persons): (a) incomes and prices, as MicroLink.poverty; (b) incomes only; (c) prices only.
    Also the spending-weighted mean of family inflation (pp)."""
    link = R.ml.link_variables(R.d.ms, ref.solutions[y], sim.solutions[y])
    pi = R.ml.family_inflation(link)                                 # each family's own basket, reconciled to the SAM
    f, g = R.ml.hd.f, link["_g"]
    eh = f["grp"].map(g["real_factor"] * (1 + g["inflation_pct"] / 100)).fillna(1.0)     # the group's nominal spending change
    chg = lambda pci: float(R.ml.hd._before_after(pci).loc["Poor persons", "Change"])
    both = chg(f["PCI"] * eh / (1 + pi / 100))
    income = chg(f["PCI"] * eh)
    price = chg(f["PCI"] / (1 + pi / 100))
    w = f["RFACT"] * f["TOTEX"]
    return both, income, price, float(np.average(pi, weights=w))


def main():
    oil = QL.arg("oil", 36.0)
    spec = QL.arg("spec", "", str)
    h = QL.arg("h", 0.85)
    thetas = [float(x) for x in QL.arg("thetas", "0.7,1.5,2", str).split(",")]
    tgt, src = QL.dsge_oil_annual(oil, spec)                         # the BSP's response: rule minus held, by year
    beta = float(pd.read_csv(_common.calibration_file(), index_col=0).loc["central (e)", "beta"])
    R = CR.Runs("low", wage_curve=beta, **({"hoarding": h} if h else {}))
    piece, _ = R.pieces()
    m = R.m
    inv = [c for i, c in enumerate(m.C) if m.qinv[i] > 0]
    print("no-shock path ...", flush=True)
    clean = R.run(set(), piece=piece)
    rows = []
    cache = {}
    for theta in thetas:
        for label, ch in RUNS.items():
            key = (theta if "inv" in ch else None, ch)              # the peso-only run does not depend on theta
            if key in cache:
                sim, M = cache[key]
            else:
                sc = {y: (1.0 - theta / 100 * tgt[y]["real_rate_gap_pp"]) if "inv" in ch else 1.0 for y in YEARS}
                fx = {y: (1 + tgt[y]["real_fx_gap_pct"] / 100) if "fx" in ch else 1.0 for y in YEARS}
                piece["qpm"] = {y: {"exr_scale": fx[y], "qinv_scale": {c: sc[y] for c in inv}} for y in YEARS}
                print(f"theta {theta:g}, {label}: investment scale {sc}, peso {fx} ...", flush=True)
                sim = R.run({"qpm"}, piece=piece)
                M = R.measures(clean, sim)[0]
                cache[key] = (sim, M)
            cpi = (sim.table.cpi / clean.table.cpi - 1) * 100
            r = {"theta (% of real investment per pp)": theta, "run": label}
            for y in YEARS:
                both, income, price, fam = counts(R, clean, sim, y)
                r.update({f"GDP gap {y} (%)": M[f"GDP gap {y} (%)"], f"consumer prices {y} (%)": float(cpi[y]),
                          f"family inflation {y}, mean (pp)": fam,
                          f"new poor {y}: incomes and prices (M)": both / 1e6,
                          f"new poor {y}: incomes only (M)": income / 1e6,
                          f"new poor {y}: prices only (M)": price / 1e6})
            rows.append(r)
            print(pd.Series(r).to_string(), flush=True)
    t = pd.DataFrame(rows).set_index(["theta (% of real investment per pp)", "run"]).T
    stamp = dt.datetime.now()
    out = paths.output_dir() / f"bsp_oil_response_netting_{stamp:%Y%m%d_%H%M}{_common.out_tag()}_oil{oil:g}{spec}.md"
    inp = pd.DataFrame(tgt).rename(index={"output_gap_pct": "DSGE output gap (%)", "real_fx_gap_pct": "DSGE real exchange rate (%)",
                                          "policy_rate_pp": "DSGE policy rate (pp)", "inflation_pp": "DSGE inflation (pp a year)",
                                          "real_rate_gap_pp": "DSGE real-rate gap (pp)"})
    oilmod = getattr(sys.modules.get("oil_policy"), "_M", "oil")
    L = [f"# The BSP's response to a {oil:g}% oil-price rise, through the CGE: the output cost and the price benefit for the poor, "
         f"separated ({stamp:%d %B %Y, %H:%M})", "",
         f"**NOT FOR CITATION** (Infinity GEM 0.3.12; research). The project's DSGE `research/dsge/soe_{oilmod}.py` (posterior mean; "
         f"`{src}`): the BSP's response = the estimated rule minus the rate held for a year (`research/dsge/oil_policy.py`), by year "
         f"below. CGE: central 2026 setting of 18 Oct 2026, SAM `{CR.SAM_VARIANT}`, wage-curve beta {beta:.3f}, labour hoarding h = {h:g}; the "
         f"link of `scenarios/qpm_cge_link.py mode=elastic`: real investment demand moves by theta % per pp of the DSGE's real-rate "
         f"gap (the investment channel), the peso by the DSGE's real exchange rate (the peso channel).", "",
         "**How the poor are counted** (`infinity_gem.microlink.MicroLink.poverty`, the 2026 scenarios' \"own baskets\" measure): each FIES 2023 "
         "family's per-capita income is scaled by its household group's nominal spending change from the CGE and deflated by its "
         "own basket's price change (its FIES budget shares x the CGE's category price changes), then compared with the official "
         "2023 poverty line. So the published count nets the price benefit against the income loss. \"Incomes only\" holds every "
         "family's prices at the baseline; \"prices only\" holds nominal incomes. The three counts do not add exactly: families "
         "cross the line one at a time.", "",
         "## The DSGE's response (inputs to the CGE link)", "", inp.to_markdown(floatfmt=".3f"), "",
         "## Decomposition", "", t.to_markdown(floatfmt=".3f"), ""]
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L)); print("saved", out)


if __name__ == "__main__":
    main()
