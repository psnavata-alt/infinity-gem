"""Scenario (0.3.6): corruption as lost public-investment efficiency and leakage, not only a
spending fall.

Question: the published runs model corruption only as the 2025 freeze (less construction). The IMF's DIG model (Buffie,
Berg, Pattillo, Portillo and Zanna 2012, IMF WP 12/144) and the IMF's GIMF simulation for the Philippines (Komatsuzaki,
IMF Country Report 15/247, ch. 4) let only a share of each peso of public investment become usable capital, so
corruption also lowers productivity for years, and part of the money is diverted. How large is each part, and what
does reform buy compared with more money? Sources: a reference copy (not distributed).

The pre-CGE ("real-world") model is DIG's public-capital accumulation with an efficiency share (infinity_gem/dynamic.py,
public_capital keys e_path, leakage, leak_to, ig_public_share, waste_lost, absorptive; check CR1). It turns the
efficiency gap into three shocks the CGE receives each year: (1) a productivity shock in every industry,
(1 + dKG/KG)^phi - 1; (2) a smaller general capital stock; (3) changes in construction demand (freeze, catch-up,
leakage). Section 1 of the report prints these shock values.

  Efficiency of public investment, two IMF values for the Philippines (15 Oct 2026):
    0.77   IMF CR 19/137, PIMA (2019): gap of about 23% vs the best-performing emerging markets, "based on perceived
           quality";
    0.60   IMF CR 15/247 (2015), the IMF's own GE model for the Philippines: 40% of public investment wasted, "broadly in
           line with the Philippines' PIE-X and PIMI scores relative to best performers"; also DIG's base case (0.6).
  Reference ("clean") run: 2023-2025 public investment at the best performers' efficiency (1.0).
  Factors (Shapley, infinity_gem/decompose.py; check SH1):
    efficiency  e in 2023-2025 on all public investment;
    freeze      -₱238.3 bn construction in 2025 (DBM);
    leakage     a share l of government construction spending in 2023-2025 taken by the few who diverted it and saved
                (or sent abroad: same result here, see the report) instead of building anything. Bounded by the gap:
                l = 1 - e (no Philippine measurement; Olken 2007 measured 27.7% missing on Indonesian village roads).
  Wasted spending adds no capital to the general stock either (waste_lost; Pritchett 2000; Gupta et al. 2014).
  Policy runs from 2027, against the actual path (efficiency e + freeze):
    catch-up    +₱208.7 bn construction in 2027 (DBM SAAODB) at efficiency e;
    reform      all public investment from 2027 at the best performers' efficiency (1.0), with and without the catch-up;
    more money  no reform: ₱208.7 bn / e at efficiency e (the usable capital ₱208.7 bn buys at 1.0);
    each with and without absorptive-capacity overruns (DIG phi_A = 5, "tight"; 0 = none).
Settings: '0.3 recommended' (hybrid closure, capital tied to its industry, sticky peso wages, short run in which
workers of all skill levels can lose jobs); public capital low and high (phi 0.083 / KG 0.397 GDP; phi 0.122 / KG 0.296
GDP). Government share of construction investment s: PSA OpenSTAT 0542B5BCNQ1, 2023. Years with any shock in any run
(2023, 2024, 2025, 2027) are solved short run in EVERY run, so runs compare like with like.

NOT FOR CITATION. Run:  py scenarios/corruption_efficiency_leakage.py   (about 4 minutes)
"""
import itertools

from _common import PSA_GDP, SAM_GDP_2023, Report, to_sam_units
import pandas as pd

from infinity_gem import paths
from infinity_gem.decompose import shapley
from infinity_gem.dynamic import DynamicCGE, PUBLIC_CAPITAL_DEFAULTS
from infinity_gem.microlink import MicroLink
from infinity_gem.settings import PUBLIC_CAPITAL, dynamic_kwargs

EFFICIENCY = {"0.77 (IMF PIMA 2019)": 0.77, "0.60 (IMF GIMF Philippines 2015)": 0.60}
E_BEST = 1.0
DIG_TIGHT = 5.0                                # DIG's "tight" absorptive-capacity parameter (WP 12/144, p. 22)
SCANDAL = (2023, 2024, 2025)
REFORM = (2027, 2028, 2029, 2030)
FALL25, CATCHUP = 238.3, 208.7
KEYS = (2023, 2024, 2025, 2027)
TO_2025 = PSA_GDP[2025] / SAM_GDP_2023

g = pd.read_csv(paths.DATA_RAW / "macro" / "PSA_OpenSTAT_0542B5BCNQ1_construction_GFCF_by_sector_quarterly_2000-2026.csv",
                comment="#").set_index("Institutional Sector")
c23 = g[[c for c in g.columns if c.startswith("At Current Prices 2023")]].apply(pd.to_numeric).sum(axis=1)
S_PUB = float(c23["..General government"] / c23["Gross Fixed Capital Formation in Construction"])
cut25, catch = (to_sam_units(x, PSA_GDP[2025]) for x in (FALL25, CATCHUP))

rep = Report("Corruption as lost efficiency and leakage: infrastructure 2023-2030 (Infinity GEM 0.3.6)", "corruption_efficiency_leakage")
rep.p("**NOT FOR CITATION** (opt-in 0.3 upgrades and the efficiency and leakage channel, check CR1). Pesos are 2025 pesos "
      "(same share of GDP as in the 2023 SAM).")
rep.p(f"Inputs: efficiency 0.77 (IMF PIMA) or 0.60 (IMF GIMF for the Philippines) vs 1.0 for the best performers; government "
      f"share of construction investment s = {S_PUB:.3f} (PSA 0542B5BCNQ1, 2023: ₱{c23['..General government'] / 1e3:,.1f} bn of "
      f"₱{c23['Gross Fixed Capital Formation in Construction'] / 1e3:,.1f} bn); freeze -₱{FALL25} bn (2025); catch-up "
      f"+₱{CATCHUP} bn (2027); leakage bound l = 1 - e; DIG overruns phi_A = {DIG_TIGHT:g}.")

ret = pd.DataFrame({k: {"phi": v["phi"], "public capital / GDP (recorded, IMF ICSD)": v["kg_gdp"],
                        "implied return on recorded public capital": v["phi"] / v["kg_gdp"],
                        "implied return on usable capital, e 0.77": v["phi"] / (0.77 * v["kg_gdp"]),
                        "implied return on usable capital, e 0.60": v["phi"] / (0.60 * v["kg_gdp"])}
                    for k, v in PUBLIC_CAPITAL.items() if v}).T
rep.h("0. Cross-check: the return on public capital the settings imply (DIG calibrates this, 15-30%)")
rep.table(ret, floatfmt=".3f")
rep.p("Marginal product of public capital = phi x GDP / public capital. DIG (Buffie et al. 2012, pp. 21-22) sets it at 0.25 from "
      "World Bank project returns and macro estimates (15-30%) and deduces the elasticity. On recorded capital the 'low' setting "
      "(0.21) is inside that range and the 'high' setting (0.41) above it; on usable capital both are higher. Read 'high' as an "
      "upper bound.")

shock_rows, summary, shap_rows, policy_rows, years_tab = [], [], [], [], {}

for pcname in ("low", "high"):
    kw = dynamic_kwargs("0.3 recommended", public_capital=pcname)
    pc0 = dict(kw["public_capital"])
    d = DynamicCGE(**kw)
    base = d.baseline()
    ic = d.m.C.index("ccons")
    q0 = d.m.qinv[ic]
    mls = {"short": MicroLink(d.ms), "long": MicroLink(d.m)}

    def poor(ref, sim, year):
        ml = mls["short" if year in KEYS else "long"]
        model = d.ms if year in KEYS else d.m
        link = ml.link_variables(model, ref.solutions[year], sim.solutions[year])
        return (float(ml.hd.poverty(link["_g"]).loc["Poor persons", "Change"]),
                float(ml.poverty(link, ml.family_inflation(link)).loc["Poor persons", "Change"]))

    def measures(ref, sim):
        r, s = ref.table, sim.table
        gap = (s.real_gdp / r.real_gdp - 1) * 100
        out = {"cumulative GDP loss 2023-2030 (₱ bn)": -float((s.real_gdp - r.real_gdp).sum()) * TO_2025,
               "GDP gap 2025 (%)": float(gap[2025]), "GDP gap 2030 (%)": float(gap[2030]),
               "public capital gap 2030 (%)": float(s.public_capital_gap_pct[2030] - r.public_capital_gap_pct[2030]),
               "employment gap 2025 (pp)": float(s.employment_gap_low_skill_pct[2025] - r.employment_gap_low_skill_pct[2025])}
        for y in (2025, 2030):
            grp, own = poor(ref, sim, y)
            out[f"new poor {y}, group method"], out[f"new poor {y}, own baskets"] = grp, own
        return out, gap

    for ename, E_PH in EFFICIENCY.items():
        LEAK = round(1 - E_PH, 2)

        def run(e_path=None, leak=0.0, extra=None, absorptive=0.0):
            pc = dict(pc0, e=E_PH, ig_public_share=S_PUB, leak_to={"saved": 1.0}, e_path=dict(e_path or {}), waste_lost=True,
                      leakage={t: leak for t in SCANDAL} if leak else {}, absorptive=absorptive)
            d.a["public_capital"], d.pc = pc, dict(PUBLIC_CAPITAL_DEFAULTS, **pc)
            sh = {t: {} for t in KEYS}
            for t, x in (extra or {}).items():
                sh[t] = {"qinv_scale": {"ccons": 1 + x / q0}}
            return d.scenario(sh)

        clean = run(e_path={t: E_BEST for t in SCANDAL})
        cache = {}

        def path_of(S):
            key = frozenset(S)
            if key not in cache:
                cache[key] = run(e_path=None if "efficiency" in S else {t: E_BEST for t in SCANDAL},
                                 leak=LEAK if "leakage" in S else 0.0, extra={2025: -cut25} if "freeze" in S else None)
            return cache[key]

        # the shocks the efficiency gap hands the CGE, year by year (efficiency only, against the clean run)
        eff = path_of({"efficiency"}).table
        for t in eff.index:
            kg_gap = float(eff.public_capital_gap_pct[t] - clean.table.public_capital_gap_pct[t])
            shock_rows.append({"public capital": pcname, "efficiency": ename, "year": t,
                               "public capital gap (%)": kg_gap,
                               "productivity shock, all industries (%)": ((1 + kg_gap / 100) ** pc0["phi"] - 1) * 100,
                               "general capital stock gap (%)": float(eff.capital_stock_index[t] / clean.table.capital_stock_index[t] - 1) * 100,
                               "leakage at the bound (₱ bn, 2025 pesos)": (LEAK * S_PUB * float(base.solutions[t]["QINV"][ic]) * TO_2025
                                                                           if t in SCANDAL else 0.0),
                               "freeze (₱ bn)": -FALL25 if t == 2025 else 0.0})

        for leak_on in (False, True):
            factors = ["efficiency", "freeze"] + (["leakage"] if leak_on else [])
            case = f"e {E_PH:.2f}, leakage {'0' if not leak_on else f'{LEAK:.2f} (bound)'}"
            res = {}
            for r_ in range(1, len(factors) + 1):
                for S in itertools.combinations(factors, r_):
                    res[frozenset(S)] = measures(clean, path_of(S))[0]
            for meas in ("cumulative GDP loss 2023-2030 (₱ bn)", "GDP gap 2030 (%)", "new poor 2025, own baskets", "new poor 2030, own baskets"):
                phi = shapley(lambda S: 0.0 if not S else res[S][meas], factors)
                shap_rows.append({"public capital": pcname, "case": case, "measure": meas,
                                  **{f: phi[f] for f in ("efficiency", "freeze", "leakage") if f in phi}, "total": phi.attrs["total"]})
            allon, gap_all = measures(clean, path_of(set(factors)))
            summary.append({"public capital": pcname, "case": case, **allon})
            years_tab[(pcname, case)] = gap_all

        actual = path_of({"efficiency", "freeze"})
        more = to_sam_units(CATCHUP / E_PH, PSA_GDP[2025])
        for absorb in (0.0, DIG_TIGHT):
            pol = {"catch-up ₱208.7 bn": run(extra={2025: -cut25, 2027: catch}, absorptive=absorb),
                   "reform from 2027 (e 1.0), no catch-up": run(e_path={t: E_BEST for t in REFORM}, extra={2025: -cut25}, absorptive=absorb),
                   "catch-up ₱208.7 bn + reform from 2027": run(e_path={t: E_BEST for t in REFORM}, extra={2025: -cut25, 2027: catch}, absorptive=absorb),
                   f"more money, no reform: ₱{CATCHUP / E_PH:.1f} bn": run(extra={2025: -cut25, 2027: more}, absorptive=absorb)}
            for name, p in pol.items():
                m_, _ = measures(actual, p)
                policy_rows.append({"public capital": pcname, "efficiency": f"{E_PH:.2f}", "overruns (DIG phi_A)": absorb, "policy": name,
                                    "cumulative GDP GAIN 2023-2030 (₱ bn)": -m_["cumulative GDP loss 2023-2030 (₱ bn)"],
                                    "GDP 2030 (%)": m_["GDP gap 2030 (%)"], "public capital 2030 (%)": m_["public capital gap 2030 (%)"],
                                    "new poor 2030, own baskets": m_["new poor 2030, own baskets"]})
        print(pcname, ename, "done")

rep.h("1. The shocks the pre-CGE model hands the CGE (efficiency gap 2023-2025 only, against the clean reference)")
rep.table(pd.DataFrame(shock_rows).set_index(["public capital", "efficiency", "year"]), floatfmt=",.3f")
rep.p("The efficiency gap opens a public-capital gap from 2024 (investment builds capital the next year); the productivity shock "
      "is (1 + gap)^phi - 1 in every industry; the general capital stock is smaller by the wasted spending. The CGE turns these "
      "into GDP, jobs, prices and poverty. The freeze and leakage are spending shocks (₱ bn) entered directly.")
rep.h("2. The whole episode against the clean reference")
rep.table(pd.DataFrame(summary).set_index(["public capital", "case"]), floatfmt=",.3f")
rep.p("Losses are positive; gaps are % of the reference. New poor: persons, FIES 2023 households; 'group method' = Infinity GEM's "
      "published method; 'own baskets' = each family's own inflation (infinity_gem/microlink.py). 2025 is a short-run year.")
rep.h("3. How much is efficiency, the freeze and leakage (Shapley; contributions add up to the total)")
rep.table(pd.DataFrame(shap_rows).set_index(["public capital", "case", "measure"]).reindex(columns=["efficiency", "freeze", "leakage", "total"]),
          floatfmt=",.3f")
rep.p("Leakage saved or sent abroad gives the same results here (checked; check CR1): it happens only in short-run years with a "
      "fixed exchange rate, where both take the money out of domestic spending. Known model limit: in short-run "
      "years employment can exceed the labour force, which gives leakage a small spurious gain in 2027-2030.")
rep.h("4. What reform buys compared with more money (against the actual path: efficiency e and the freeze)")
rep.table(pd.DataFrame(policy_rows).set_index(["public capital", "efficiency", "overruns (DIG phi_A)", "policy"]), floatfmt=",.3f")
rep.p("Overruns (DIG phi_A = 5): extra spending above the baseline buys less (cost overruns when scaling up fast); reform alone "
      "adds no spending, so it is not affected.")
rep.h("5. Year by year: real GDP gap vs the clean reference (%), all factors on")
rep.table(pd.DataFrame({f"{k[0]}, {k[1]}": v for k, v in years_tab.items()}), floatfmt=",.3f")
rep.p("Assumptions to review: both efficiency values rest on indices (perceived quality; PIE-X and PIMI), not on measured "
      "Philippine projects; the leakage share has no Philippine measurement (a bound); phi and KG as in the 0.3 range (section 0); "
      "gap persistence 0.5; DIG's overrun parameter is a low-income-country setting.")
rep.save()
print(pd.DataFrame(shock_rows).set_index(["public capital", "efficiency", "year"]).round(3).to_string())
print(pd.DataFrame(summary).set_index(["public capital", "case"]).round(3).to_string())
print(pd.DataFrame(policy_rows).round(3).to_string())
