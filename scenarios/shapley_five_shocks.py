"""Waterfall: the contribution of each shock to the combined five-shock result, by Shapley decomposition.

NOT FOR CITATION until reviewed. Run:  py scenarios/shapley_five_shocks.py   (32 CGE solves + poverty counts; a few minutes)

Inputs: scenarios/specs/five_shocks_2026_subsets_central.json (every subset of the five September 2026 shocks; a test of the
machinery on a known scenario, not Infinity GEM's own scenario, which will come from the shock estimates in preshock/).
Outcomes: real GDP (%), new poor persons (group inflation, Infinity GEM's published method) and new poor persons (each family's
own basket, reconciled; infinity_gem.microlink). Also shown: each shock run ALONE, and the naive sum of the separate runs.
"""
import datetime as dt
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from infinity_gem.cge import CGE              # noqa: E402
from infinity_gem.decompose import shapley    # noqa: E402
from infinity_gem.microlink import MicroLink  # noqa: E402

SPEC = ROOT / "scenarios" / "specs" / "five_shocks_2026_subsets_central.json"
LABEL = {"oil": "Oil", "geopolitics": "Geopolitics (FDI)", "corruption": "Infrastructure freeze", "disasters": "Disasters", "psei": "Stock market (PSEi)"}


def main():
    d = json.loads(SPEC.read_text(encoding="utf-8"))
    m = CGE.from_sam(**{k: (tuple(v) if isinstance(v, list) else v) for k, v in d["closure"].items()})
    b = m.solve()
    g0 = m.gdp(b)["real"]
    ml = MicroLink(m)
    res = {}
    for key, spec in d["subsets"].items():
        s = m.solve(spec) if spec else b
        assert s.ok, f"subset {key} did not solve"
        link = ml.link_variables(m, b, s)
        res[frozenset(k for k in key.split("|") if k)] = {
            "Real GDP (%)": (m.gdp(s)["real"] / g0 - 1) * 100,
            "New poor, group inflation": float(ml.hd.poverty(link["_g"]).loc["Poor persons", "Change"]),
            "New poor, own baskets": float(ml.poverty(link, ml.family_inflation(link)).loc["Poor persons", "Change"])}
    shocks = d["shocks"]
    rows = {}
    for out in ("Real GDP (%)", "New poor, group inflation", "New poor, own baskets"):
        phi = shapley(lambda S: res[S][out], shocks)
        alone = {k: res[frozenset([k])][out] for k in shocks}
        rows[out] = pd.DataFrame({"Shapley contribution": phi, "Run alone": pd.Series(alone)}).rename(index=LABEL)
        rows[out].loc["Sum"] = [phi.sum(), sum(alone.values())]
        rows[out].loc["All five together"] = [phi.attrs["total"], phi.attrs["total"]]
        print("==", out); print(rows[out].round(3).to_string())
    stamp = dt.date.today().strftime("%Y%m%d")
    md = lambda t: t.to_markdown(floatfmt=",.3f") if hasattr(t, "to_markdown") else t.to_string()
    L = [f"# Five shocks: contribution of each shock (Shapley decomposition) ({dt.date.today():%d %B %Y})", "",
         "**NOT FOR CITATION** (Infinity GEM 0.3.5). Script: `scenarios/shapley_five_shocks.py`. The five September 2026 shocks "
         "(an earlier estimate specification, central short run) as a **test of the method**; Infinity GEM's own scenario will use the shock estimates in preshock/.", "",
         "The Shapley contributions add up exactly to the combined result ('Sum' = 'All five together'). The separate runs do not: their sum "
         "differs from the combined run because effects interact, most of all in the poverty count (families pushed over the line only by "
         "the shocks together).", ""]
    for k, t in rows.items():
        L += [f"## {k}", "", md(t), ""]
    rep = ROOT / "outputs" / f"shapley_five_shocks_{stamp}.md"
    rep.write_text("\n".join(L), encoding="utf-8")
    print("saved", rep)


if __name__ == "__main__":
    main()
