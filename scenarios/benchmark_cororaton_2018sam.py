"""Benchmark 2 rerun on both SAMs (added in 0.3).

Cororaton (DLSU-AKI Policy Brief 2026-04-066), Sim1: oil +65%, fertiliser +50%, import volumes of oil, petroleum and
fertiliser -20%. Infinity GEM has one commodity for chemicals, petroleum and fertiliser (cchem), so the shock is the
same single world-import-price factor used in the 30 Sept benchmark (x1.64; its shares are ASSUMPTIONS, see
an internal benchmark note section 3). The only change here is the base: the IFPRI 2018 SAM (balanced, see
SAM.balance) beside the 2023 SAM. Cororaton's SAM year is not stated; the working assumption (30 Sept) is 2018.
"""
from _common import Report
from infinity_gem import paths
from infinity_gem.cge import CGE
import pandas as pd

SHOCK = {"pwm_scale": {"cchem": 1.64}}
CLOSURES = {"long run": {}, "short run": dict(closure="keynesian", unemployed=("flab-n", "flab-p"), capital="fixed")}
COROR = {"Real GDP (%)": -4.49, "Wage, skilled (%)": -6.32, "Wage, unskilled (%)": -5.66, "Return to capital (%)": -5.61,
         "Land rent (%)": -6.64, "Government revenue (%)": -4.10}

rows = {}
for yr, path in ((2018, paths.SAM_2018), (2023, paths.SAM_2023)):
    for cl, kw in CLOSURES.items():
        m = CGE.from_sam(path, **kw)
        b, s = m.solve(), m.solve(SHOCK)
        assert s.ok, f"{yr} {cl} did not solve"
        F = m.F
        wf = lambda sol, f: float((sol["W"][F.index(f)] * sol["QF"][F.index(f)]).sum() / sol["QF"][F.index(f)].sum())
        pct = lambda a, z: (z / a - 1) * 100
        r = {"Real GDP (%)": pct(m.gdp(b)["real"], m.gdp(s)["real"]),
             "CPI (%)": pct(b["CPI"], s["CPI"]),
             "Wage, skilled (%)": pct(wf(b, "flab-s"), wf(s, "flab-s")),
             "Wage, unskilled (%)": pct(wf(b, "flab-n"), wf(s, "flab-n")),
             "Return to capital (%)": pct(wf(b, "fcap"), wf(s, "fcap")),
             "Land rent (%)": pct(wf(b, "flnd"), wf(s, "flnd")),
             "Government revenue (%)": pct(b["YG"], s["YG"]),
             "Employment, low-skill (%)": pct(b["EMP"][F.index("flab-n")], s["EMP"][F.index("flab-n")]),
             "Real household consumption (%)": pct(b["QH"].sum(), s["QH"].sum())}
        for h in ("hhd-r1", "hhd-u5"):
            i = m.H.index(h)
            r[f"Real consumption {h} (%)"] = pct(b["EH"][i] / b["CPI"], s["EH"][i] / s["CPI"])
        rows[f"{yr} SAM, {cl}"] = r
df = pd.DataFrame(rows)
df["Cororaton Sim1"] = pd.Series(COROR)

# 0.3.3 (rigging audit finding 4): the facts quoted in the text below are computed here, not typed in
from infinity_gem.sam import SAM                                                   # noqa: E402
raw = {yr: SAM.load(p).table for yr, p in ((2018, paths.SAM_2018), (2023, paths.SAM_2023))}


def _gdp(t):
    F = [f for f in ("flab-n", "flab-p", "flab-s", "flnd", "fcap") if f in t.index]
    A = [a for a in t.columns if a.startswith("a")]
    return float(t.loc[F, A].values.sum() + sum(t.loc[x].sum() for x in ("mtax", "stax", "atax") if x in t.index))


hh = {yr: [h for h in t.index if h.startswith("hhd")] for yr, t in raw.items()}
hh_cchem = {yr: float(raw[yr].loc["cchem", hh[yr]].sum()) for yr in raw}
hh_spend23 = float(raw[2023].loc[[c for c in raw[2023].index if c.startswith("c")], hh[2023]].values.sum())
imp_gdp = {yr: float(raw[yr].loc["row", "cchem"]) / _gdp(raw[yr]) * 100 for yr in raw}
bal18 = SAM.load_for_model(paths.SAM_2018).table
bal_max = float((bal18 - raw[2018].loc[bal18.index, bal18.columns]).abs().values.max())
g = {k: v["Real GDP (%)"] for k, v in rows.items()}
gl, gs = g["2018 SAM, long run"], g["2018 SAM, short run"]
hl, hs = g["2023 SAM, long run"], g["2023 SAM, short run"]

rep = Report("Benchmark 2 on the 2018 SAM: Cororaton-type oil shock (Infinity GEM 0.3 options)", "benchmark_cororaton_2018sam")
rep.p("**Uses Infinity GEM 0.3 opt-in upgrades; not for citation.** Shock: world import price of `cchem` x1.64 (oil +65%, "
      "fertiliser +50%, import disruption as a +20% price wedge; shares ASSUMED, as in the 30 Sept benchmark). "
      "Factor prices and revenue are nominal; in the long run the CPI is the numeraire, in the short run the exchange rate is. "
      "Cororaton's numeraire, closures and demand system are not stated in his brief, so nominal factor prices are not "
      "strictly comparable; real GDP is.")
rep.table(df, ".2f")
rep.p("2018 SAM: IFPRI Nexus 2018 (PSA 2012 I-O, 2015 FIES), published in whole billions and balanced by weighted least "
      f"squares (`SAM.balance`; largest cell change ₱{bal_max:.1f} bn; 'other cereals' balanced to zero and dropped).")
rep.h("Finding: the 2018 SAM is not a usable base for an oil-price benchmark")
rep.p(f"In IFPRI's published 2018 SAM, households buy {'**no**' if hh_cchem[2018] == 0 else f'only ₱{hh_cchem[2018]:,.0f} bn of'} "
      "chemicals and petroleum (`cchem`) and no fish: those cells are "
      f"blank in the raw file (checked 1 Oct 2026), against ₱{hh_cchem[2023]:,.0f} bn of household `cchem` purchases "
      f"({hh_cchem[2023] / hh_spend23:.1%} of household "
      f"spending) in the 2023 SAM. `cchem` imports are also {imp_gdp[2018]:.1f}% of GDP in 2018 against {imp_gdp[2023]:.1f}% "
      "in 2023. So the same shock "
      "cannot raise consumer prices through fuel, and the short-run CPI even falls (demand loss with a fixed exchange "
      f"rate). The 2018 base gives a **smaller** GDP loss than the 2023 base ({gl:.1f}% / {gs:.1f}% against {hl:.1f}% / "
      f"{hs:.1f}%), so a "
      f"2018 SAM cannot settle why Cororaton's loss ({COROR['Real GDP (%)']:.2f}%) is about "
      f"{COROR['Real GDP (%)'] / hl:.0f} times ours: on it the gap widens, but the SAM lacks "
      "household fuel purchases, so it is not a clean test (IFPRI's 2018 data paper says household consumption was split with "
      "the 2015 FIES, so the blank cells are unexplained). "
      "Remaining leads: Cororaton's own SAM and technical paper (not located), the bundling of petroleum with chemicals "
      ", closures and elasticities, and how the import disruption enters.")
rep.save()
print(df.round(2).to_string())
