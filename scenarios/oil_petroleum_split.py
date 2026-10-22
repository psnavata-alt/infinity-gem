"""Oil shocks with refined petroleum separated from chemicals (added in 0.3).

Compares, for world oil prices +20%, +40%, +60% (short and long run):
  A  combined SAM (published method): cchem import price x (1 + oil x 0.6)
  B  combined SAM, sourced share: cchem import price x (1 + oil x 0.512) (PSA 2018 petroleum share of the group's imports)
  C  split SAM: refined petroleum imports x (1 + oil); crude (in mining) imports x (1 + oil x 0.677) (infinity_gem/oil.py)
and the I-O price model with the assumed pass-through 0.6 against the sourced 0.634.
Benchmark 2 (Cororaton, DLSU-AKI 2026, Sim1: oil +65%, fertiliser +50%; real GDP -4.49%): combined SAM (x1.64, as on
30 Sept) against the split SAM (oil +65% on refined and crude imports, fertiliser +50% on its 2.6% share of chemical
imports). Import-volume cuts (-20%) are not imposed, as before.
NOT FOR CITATION until reviewed. Sources: docs/guides/08_PARAMETERS_AND_SOURCES.md.
Run:  py scenarios/oil_petroleum_split.py
"""
from _common import Report
import pandas as pd

from infinity_gem import paths
from infinity_gem.cge import CGE
from infinity_gem.iomodel import IOTable
from infinity_gem.microsim import Microsim
from infinity_gem.oil import cge_oil_shock, import_shares, io_refined_passthrough

CLOSURES = {"short run": dict(closure="keynesian", unemployed=("flab-n", "flab-p"), capital="fixed"), "long run": {}}
ms = Microsim()
sh = import_shares()
pt = io_refined_passthrough()

rows = []
for cl, kw in CLOSURES.items():
    mc, msp = CGE.from_sam(paths.SAM_2023, **kw), CGE.from_sam(paths.SAM_2023_PETR, **kw)
    bc, bs = mc.solve(), msp.solve()
    for oil in (0.2, 0.4, 0.6):
        variants = {"A combined SAM, share 0.6 (published)": (mc, bc, cge_oil_shock(mc, oil, combined_share=0.6)),
                    f"B combined SAM, share {sh['petroleum_in_chem_and_petroleum']:.3f} (PSA)": (mc, bc, cge_oil_shock(mc, oil, combined_share=sh["petroleum_in_chem_and_petroleum"])),
                    "C split SAM (refined + crude)": (msp, bs, cge_oil_shock(msp, oil))}
        for name, (m, b, spec) in variants.items():
            s = m.solve(spec)
            assert s.ok, (cl, oil, name)
            pct = lambda a, z: (z / a - 1) * 100
            rows.append({"closure": cl, "oil": f"+{oil:.0%}", "variant": name,
                         "real GDP (%)": pct(m.gdp(b)["real"], m.gdp(s)["real"]),
                         "CPI (%)": pct(b["CPI"], s["CPI"]),
                         "real household consumption (%)": pct(b["QH"].sum(), s["QH"].sum()),
                         "low-skill employment (%)": pct(b["EMP"][0], s["EMP"][0]),
                         "new poor (FIES 2023)": ms.from_cge(m, b, s)["new_poor"]})
cge = pd.DataFrame(rows)

io = IOTable()
ref = next(n for n in io.names if n.startswith("Coke and refined petroleum"))
iorows = []
for oil in (0.2, 0.4, 0.6):
    for lab, p in (("assumed 0.6", 0.6), (f"sourced {pt['passthrough']:.3f}", pt["passthrough"])):
        r = io.price_summary({ref: oil * p})
        iorows.append({"oil": f"+{oil:.0%}", "pass-through": lab, "refined petroleum price (%)": oil * p * 100,
                       **{k: (v * 100 if isinstance(v, float) and abs(v) < 1 else v) for k, v in r.items() if isinstance(v, (int, float))}})
iot = pd.DataFrame(iorows)

COROR = -4.49
bm = []
for cl, kw in CLOSURES.items():
    for name, path, spec_fn in (("combined SAM, cchem x1.64 (30 Sept)", paths.SAM_2023, lambda m: {"pwm_scale": {"cchem": 1.64}}),
                                ("split SAM, oil +65%, fertiliser +50%", paths.SAM_2023_PETR, lambda m: cge_oil_shock(m, 0.65, fertilizer=0.50))):
        m = CGE.from_sam(path, **kw)
        b, s = m.solve(), m.solve(spec_fn(m))
        assert s.ok, (cl, name)
        g = (m.gdp(s)["real"] / m.gdp(b)["real"] - 1) * 100
        bm.append({"closure": cl, "Infinity GEM": name, "real GDP (%)": g, "Cororaton Sim1 (%)": COROR,
                   "Infinity GEM / Cororaton": g / COROR})
bmt = pd.DataFrame(bm)

rep = Report("Oil shocks with refined petroleum separated (Infinity GEM 0.3 options)", "oil_petroleum_split")
rep.p("**Uses Infinity GEM 0.3 opt-in upgrades; not for citation.** Split SAM: `tools/build_sam_petroleum_split.py` "
      f"(`outputs/sam_petroleum_split_*.md`). Sourced shares (PSA 2018 imports): petroleum in chemicals-and-petroleum "
      f"{sh['petroleum_in_chem_and_petroleum']:.3f}; crude in mining {sh['crude_in_mining']:.3f}; fertiliser in chemicals "
      f"{sh['fertilizer_in_chemicals']:.3f}. I-O pass-through {pt['passthrough']:.3f} (import share {pt['import_share']:.3f}, "
      f"crude {pt['crude_coef']:.3f}, own use {pt['own_use_coef']:.3f}).")
rep.h("CGE: world oil prices +20/40/60%")
rep.table(cge.set_index(["closure", "oil", "variant"]), floatfmt=",.3f")
rep.h("I-O price model: assumed and sourced pass-through")
rep.table(iot.set_index(["oil", "pass-through"]), floatfmt=",.3f")
rep.h("Benchmark 2: Cororaton (DLSU-AKI 2026), Sim1")
rep.table(bmt.set_index(["closure", "Infinity GEM"]), floatfmt=",.3f")
rep.save()
pd.set_option("display.width", 230)
print(cge.round(3).to_string(index=False))
print(iot.round(3).to_string(index=False))
print(bmt.round(3).to_string(index=False))
