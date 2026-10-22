"""Infrastructure freeze and 2027 catch-up with the full 0.3 dynamic model, built up one upgrade at a time.

Steps (each adds one upgrade to the previous one):
  A  0.2 method: long-run closure every year, one mobile capital stock, placeholder baseline (as in the 1 Oct slides)
  B  + documented baseline: DBCC growth path, PWT depreciation 5.02% and capital stock 1.96 x GDP
  C  + capital by industry (putty-clay, omega 3.0, IFPRI)
  D  + hybrid closure: job losses in the shock year, gap halving each year
  E  + public capital: productivity value of infrastructure: range over phi 0.083-0.122 and public capital
       0.296-0.397 x GDP (IMF ICSD 2019)
Shocks: -₱238.3 bn construction investment in 2025; +₱208.7 bn in 2027 (catch-up). 2025 pesos (same share of GDP).
NOT FOR CITATION until reviewed. Sources: docs/guides/08_PARAMETERS_AND_SOURCES.md.
Run:  py scenarios/infrastructure_full_dynamic.py
"""
from _common import PSA_GDP, SAM_GDP_2023, Report, to_sam_units
import pandas as pd

from infinity_gem import paths
from infinity_gem.dynamic import DynamicCGE, documented_baseline, PUBLIC_CAPITAL_DEFAULTS

ICSD = paths.DATA_RAW / "macro" / "IMF_ICSD_2025-07_all_countries_downloaded_2026-10-02.csv"
icsd = pd.read_csv(ICSD)
ph = icsd[icsd["COUNTRY"] == "Philippines"].set_index("SERIES_CODE")
KG = {"PPP": float(ph.loc["PHL.CAPSTCK_S13_Q_POGDP_PT.A", "2019"]) / 100,
      "pesos": float(ph.loc["PHL.CAPSTCK_S13_V_XDC.A", "2019"] / ph.loc["PHL.B1GQ_V_XDC.A", "2019"])}
cut, catch = to_sam_units(238.3, PSA_GDP[2025]), to_sam_units(208.7, PSA_GDP[2025])
TO_2025 = PSA_GDP[2025] / SAM_GDP_2023

STEPS = {
    "A  0.2 method": dict(),
    "B  + documented baseline": dict(**documented_baseline()),
    "C  + capital by industry": dict(capital_allocation="putty-clay", **documented_baseline()),
    "D  + hybrid closure": dict(capital_allocation="putty-clay", hybrid=True, **documented_baseline()),
}
rows, industry = [], None


def run(d, label, pc=None):
    global industry
    q0 = d.m.qinv[d.m.C.index("ccons")]
    qs = lambda x: {"qinv_scale": {"ccons": 1 + x / q0}}
    d.a["public_capital"] = pc
    if pc is not None:
        d.pc = dict(PUBLIC_CAPITAL_DEFAULTS, **pc)
    for name, sh in {"freeze only": {2025: qs(-cut)}, "freeze + 2027 catch-up": {2025: qs(-cut), 2027: qs(catch)}}.items():
        sim = d.scenario(sh)
        c = d.compare(d.base, sim)
        rows.append({"step": label, "path": name,
                     "cumulative GDP gap 2025-2030 (₱ bn, 2025 pesos)": c.loc["cumulative", "gdp_gap_bn"] * TO_2025,
                     "GDP gap 2030 (%)": c.loc[2030, "gdp_gap_pct"], "capital gap 2030 (%)": c.loc[2030, "capital_gap_pct"]})
        if label.startswith("D") and name == "freeze only":
            b30, s30 = d.base.solutions[2030], sim.solutions[2030]
            industry = pd.DataFrame({
                "output gap 2030 (%)": (s30["QA"] / b30["QA"] - 1) * 100,
                "capital gap 2030 (%)": (sim.capital[2030] / d.base.capital[2030] - 1) * 100,
                "rental rate gap 2030 (%)": (s30["W"][d.kc] / b30["W"][d.kc] - 1) * 100},
                index=[d.m.sam.labels.get(a, a).replace("Activities - ", "") for a in d.m.A])


last = None
for label, kw in STEPS.items():
    d = DynamicCGE(**kw)
    d.baseline()
    run(d, label)
    last = d
for kn, kg in KG.items():
    for phi in (0.083, 0.122):
        run(last, f"E  + public capital (phi {phi}, KG/GDP {kg:.3f} {kn})", {"phi": phi, "kg_gdp": kg})

tab = pd.DataFrame(rows)
rep = Report("Infrastructure freeze and catch-up with the full 0.3 dynamic model (Infinity GEM 0.3 options)", "infrastructure_full_dynamic")
rep.p("**Uses Infinity GEM 0.3 opt-in upgrades; not for citation.** Each step adds one upgrade. 2025 pesos (same share of GDP as in the "
      "2023 SAM). Shocks: -₱238.3 bn construction investment in 2025; +₱208.7 bn in 2027.")
rep.h("Summary")
rep.table(tab.set_index(["step", "path"]), floatfmt=",.3f")
fz = tab[tab.path == "freeze only"].set_index("step")["cumulative GDP gap 2025-2030 (₱ bn, 2025 pesos)"]
bt = tab[tab.path != "freeze only"].set_index("step")["cumulative GDP gap 2025-2030 (₱ bn, 2025 pesos)"]
rep.h("Share of the freeze's cumulative loss recovered by the catch-up")
rep.table(((bt - fz) / -fz * 100).rename("recovered (%)").to_frame(), floatfmt=",.1f")
rep.h("By industry, freeze only, step D (2030 vs baseline)")
rep.table(industry.sort_values("output gap 2030 (%)"), floatfmt=",.3f")
rep.save()
pd.set_option("display.width", 220)
print(tab.round(3).to_string(index=False))
print(((bt - fz) / -fz * 100).round(1).to_string())
print(industry.sort_values("output gap 2030 (%)").round(3).head(10).to_string())
