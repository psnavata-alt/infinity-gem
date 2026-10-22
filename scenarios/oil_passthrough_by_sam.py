"""Oil pass-through to consumer prices and to the poor's baskets on the three 2023 SAMs ("the CPI-weights
question"; 18 Oct 2026, about 3 AM). NOT FOR CITATION. No model code or default is changed.

Why. On Infinity GEM's own SAM v0.2 the 2026 scenarios' 2026 new poor fall by a quarter and the model's consumer
prices respond weakly to oil. Two candidate reasons:
  1. WEIGHTS. Infinity GEM's own SAM follows national-accounts concepts: households' fuel and electricity match FIES pesos but are small
     shares of PSA's household consumption (HFCE is about twice FIES spending). PSA's CPI weighs them by FIES budget shares
     (fuel 3.7%, electricity 4.6%, 2018 base). The model CPI uses the SAM's weights, and MicroLink's "reconciled" family
     baskets (the method of the 2026 scenarios) are rescaled so that the national basket equals the SAM's.
  2. COST STRUCTURE. Fuel, electricity and transport prices may themselves respond less on Infinity GEM's own SAM.
This script separates the two for one static shock: world oil +30% (infinity_gem.oil.cge_oil_shock), the central short-run
closure of "0.3 recommended" (Keynesian, fixed exchange rate, capital and land fixed), the rice-split SAM layout. It reports:
  - consumer-price indices on the same price changes with different weights: the model CPI (SAM weights); PSA's 2018 CPI
    weights (all households; bottom 30%), mapped to MicroLink's FIES categories, with fuel, electricity, water, repairs,
    vehicles and fares taken at commodity level; the FIES 2023 national basket (raw shares);
  - the price changes of the commodities in the oil channel;
  - new poor with family baskets reconciled to the SAM (the method of the 2026 scenarios), with raw FIES shares, and by group inflation.
Benchmark: the inflation VAR (replication model 05): +0.18% on the official CPI after 12 months per 10% on crude, so about
+0.54% per 30%.
Concordance check (about 3 AM): MicroLink's CATEGORY_MAP still puts chemicals ('cchem') in UTILITIES and TRANSPORT, which
was right before refined petroleum was split out of chemicals (fuel was inside 'cchem'). On the split SAMs the 2026 scenarios use, it
attributes soaps, medicines and other chemicals to utilities and transport in proportion to FIES spending. The second table
reruns the same shock with 'cchem' removed from those two categories (MicroLink's opt-in fuel_split_map=True, added after
this finding; the DEFAULT since 18 Oct 2026, about 8:20 AM). The first table uses the old map
explicitly (the 17 Oct 2026 scenario set's), so its numbers stay comparable with the runs of 18 Oct night.
Run:  py scenarios/oil_passthrough_by_sam.py        Output: outputs/oil_passthrough_by_sam_<date>.md (and .csv)
"""
import sys

from _common import ROOT                                                        # noqa: F401 (puts the package on the path)
import pandas as pd

from infinity_gem import paths                                                       # noqa: E402
from infinity_gem.microlink import MicroLink                                         # noqa: E402
from infinity_gem.oil import cge_oil_shock                                           # noqa: E402
from infinity_gem.settings import cge_model, short_run_closure                       # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OIL = 0.30
VAR_PER_10 = 0.18                                     # replication model 05 (inflation VAR): % on the CPI after 12 months
SAMS = {None: "IFPRI 2023 SAM (central 2026 setting)", "psa": "PSA-consistent",
        "own": f"Infinity GEM's own {paths.SAM_2023_OWN.stem.split('_own_')[-1]}"}         # the version in use
CPI_FILES = {"all households": "PSA_CPI_weights_2018base_AllHouseholds_Philippines.csv",
             "bottom 30%": "PSA_CPI_weights_2018base_Bottom30_Philippines.csv"}
# PSA 2018-based CPI groups -> the price that moves them: a MicroLink FIES category, or "c:<SAM commodity>" where the oil
# channel needs PSA's own split (electricity, LPG and kerosene, wood fuel, water, repairs, vehicles, vehicle fuel, fares).
CPI_MAP = {
    "01.1.1": "BREAD", "01.1.2": "MEAT", "01.1.3": "FISH", "01.1.4": "MILK", "01.1.5": "OIL", "01.1.6": "FRUIT",
    "01.1.7": "VEG", "01.1.8": "SUGAR", "01.1.9": "FOOD_NEC",
    "01.2.1": "FRUIT_VEG", "01.2.2": "COFFEE", "01.2.3": "TEA", "01.2.4": "COCOA", "01.2.5": "WATER",
    "01.2.6": "SOFTDRINKS", "01.2.9": "OTHER_NON_ALCOHOL",
    "02.1": "ALCOHOL", "02.3": "TOBACCO", "02.4": "TOBACCO",
    "03": "CLOTH",
    "04.1": "RENT", "04.3": "c:ccons", "04.4": "c:cwatr", "04.5.1": "c:celec", "04.5.2": "c:cpetr", "04.5.3": "c:cpetr",
    "04.5.4": "c:cfore",
    "05": "FURNISHING", "06": "HEALTH",
    "07.1": "c:cmach", "07.2.1": "c:cmach", "07.2.2": "c:cpetr", "07.2.3": "c:cosrv", "07.2.4": "c:cosrv",
    "07.3": "c:ctran", "07.4": "c:ctran",
    "08": "COMMUNICATION", "09": "RECREATION", "10": "EDUCATION", "11.1": "FOOD_OUTSIDE", "11.2": "FOOD_ACCOM_SRVC",
    "12": "INSURANCE", "13": "MISCELLANEOUS",
}
OIL_CHANNEL = ["cpetr", "celec", "ctran", "cchem", "cfood", "cmric"]


def cpi_weights(name):
    d = pd.read_csv(paths.DATA_RAW / "cpi" / CPI_FILES[name], comment="#", encoding="latin-1")
    code = d["Commodity Description"].str.extract(r"^([0-9.]+) - ")[0]
    w = pd.Series(d.iloc[:, -1].values, index=code.values)
    w = w[~w.index.duplicated()]
    out = pd.Series({k: float(w.get(k, 0.0)) for k in CPI_MAP})
    if abs(out.sum() - 100) > 0.01:
        raise ValueError(f"{name}: mapped CPI weights sum to {out.sum():.4f}, not 100")
    return out


def run(variant, fix_map=False):
    m = cge_model("0.3 recommended", rice=True, sam_variant=variant or "ifpri", **short_run_closure("0.3 recommended"), land="fixed")
    b = m.solve()
    s = m.solve(cge_oil_shock(m, OIL))
    if not (b.ok and s.ok):
        raise RuntimeError(f"{SAMS[variant]}: not solved ({b.residual_max:.1e}, {s.residual_max:.1e})")
    if fix_map and "cpetr" not in m.C:
        raise ValueError("the concordance check needs a SAM with refined petroleum split from chemicals")
    ml = MicroLink(m, fuel_split_map=fix_map)            # fix_map: microlink.category_map(..., fuel_split_map=True)
    link = ml.link_variables(m, b, s)
    e = ml.expected_results(link)["value"]
    cat = link["fies_categories"]["price_change_pct"]
    com = link["commodities"]
    dp = com["consumer_price_pq_pct"]
    missing = [v[2:] for v in CPI_MAP.values() if v.startswith("c:") and v[2:] not in dp.index]
    if missing:
        raise ValueError(f"{SAMS[variant]}: commodities not in the SAM: {missing}")
    price = pd.Series({k: (dp[v[2:]] if v.startswith("c:") else cat[v]) for k, v in CPI_MAP.items()})
    row = {"model CPI, SAM weights (%)": (float(s["CPI"]) / float(b["CPI"]) - 1) * 100}
    for name in CPI_FILES:
        w = cpi_weights(name)
        row[f"CPI with PSA's 2018 weights, {name} (%)"] = float((w * price).sum() / w.sum())
    nat = ml.national
    row["FIES 2023 national basket, raw shares (%)"] = float((nat * cat).sum() / nat.sum())
    R, F, G = ("family inflation, reconciled to the SAM (recommended)", "family inflation, raw FIES shares",
               "group inflation (Infinity GEM published method)")
    row["families, reconciled to the SAM: mean weighted by spending (%)"] = float(
        e["family inflation (reconciled): mean, families weighted by spending (pp)"])
    for lab, key in (("reconciled to the SAM", R), ("raw FIES shares", F)):
        row[f"bottom 30% families, {lab} (%)"] = float(e[f"{key}: Bottom 30% (deciles 1-3): inflation (pp)"])
    for lab, key in (("reconciled to the SAM (the method of the 2026 scenarios)", R), ("raw FIES shares", F), ("group inflation", G)):
        row[f"new poor, {lab} (thousand)"] = float(e[f"{key}: change in poor persons"]) / 1e3
    for c in OIL_CHANNEL:
        if c in dp.index:
            row[f"price {c} (%)"] = float(dp[c])
            row[f"household budget share {c}, SAM (%)"] = float(com.loc[c, "household_budget_share_pct"])
    for k in ("UTILITIES", "TRANSPORT"):
        row[f"FIES category {k}: price (%)"] = float(cat[k])
        row[f"FIES category {k}: reconciliation factor"] = float(link["fies_categories"].loc[k, "reconciliation_factor"])
    row["real GDP (%)"] = (m.gdp(s)["real"] / m.gdp(b)["real"] - 1) * 100
    fc = link["fies_categories"]
    cats = pd.DataFrame({"price (%)": fc["price_change_pct"], "FIES share (%)": fc["budget_share_pct"],
                         "share after reconciliation (%)": fc["budget_share_pct"] * fc["reconciliation_factor"]
                         / (fc["budget_share_pct"] * fc["reconciliation_factor"]).sum() * 100})
    return row, cats


def main():
    stamp = pd.Timestamp.today()
    out = {SAMS[v]: run(v) for v in SAMS}
    t = pd.DataFrame({k: r for k, (r, _) in out.items()})
    cats = pd.concat({k: c for k, (_, c) in out.items()}, axis=1)
    fixed = {SAMS[v]: run(v, fix_map=True)[0] for v in SAMS}
    keep = [k for k in t.index if k.startswith(("families", "bottom 30%", "new poor", "FIES 2023", "CPI with", "FIES category"))]
    t2 = pd.concat({"old map (setting of 17 Oct 2026)": t.loc[keep], "fuel-split map (default since 18 Oct 2026)": pd.DataFrame(fixed).loc[keep]}, axis=1)
    t2 = t2.swaplevel(axis=1).sort_index(axis=1, level=0, sort_remaining=False)
    print(t.to_string(float_format=lambda x: f"{x:,.3f}"))
    print(t2.to_string(float_format=lambda x: f"{x:,.3f}"))
    f = paths.output_dir() / f"oil_passthrough_by_sam_{stamp:%Y%m%d_%H%M}"
    t.to_csv(f.with_suffix(".csv"))
    cats.to_csv(f.parent / (f.name + "_fies_categories.csv"))
    t2.to_csv(f.parent / (f.name + "_concordance_check.csv"))
    L = [f"# Oil pass-through on the three 2023 SAMs: weights or cost structure? ({stamp:%d %B %Y, %H:%M})", "",
         "**NOT FOR CITATION** (Infinity GEM 0.3.9, the CPI-weights question). Script: "
         "`scenarios/oil_passthrough_by_sam.py`. One static shock, world oil +30%, central short-run closure of "
         "'0.3 recommended' (Keynesian, fixed exchange rate, capital and land fixed). Every index in a column uses the SAME "
         "price changes; only the weights differ. The first table uses MicroLink's old map (the 17 Oct 2026 scenario set's); the default since 18 Oct "
         "2026, 8:20 AM, is the fuel-split map of the last table.", "",
         f"Benchmark: the inflation VAR (replication model 05) gives +{VAR_PER_10:.2f}% on the official CPI after 12 months "
         f"per 10% on crude, about +{VAR_PER_10 * OIL * 10:.2f}% per 30%.", "",
         t.to_markdown(floatfmt=",.3f"), "",
         "## FIES categories: price change and weight, by SAM", "",
         "'FIES share' is the category's share of national FIES 2023 spending (raw); 'after reconciliation' is the share "
         "once MicroLink rescales the national basket to the SAM's (the method of the 2026 scenarios).", "",
         cats.to_markdown(floatfmt=",.3f"), "",
         "## Concordance check: chemicals out of UTILITIES and TRANSPORT", "",
         "MicroLink's CATEGORY_MAP keeps 'cchem' in UTILITIES and TRANSPORT although refined petroleum ('cpetr') is its own "
         "commodity in these SAMs. The same shock, with 'cchem' shared only among FURNISHING, HEALTH and MISCELLANEOUS:", "",
         t2.to_markdown(floatfmt=",.3f")]
    f.with_suffix(".md").write_text("\n".join(L), encoding="utf-8")
    print("saved", f.with_suffix(".md"))


if __name__ == "__main__":
    main()
