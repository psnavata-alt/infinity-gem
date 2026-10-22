"""The combined shocks of 2023-2027 and a costed stimulus package that counteracts them (0.3.7,
15 Oct 2026). The aim (15 Oct 2026): a costed response, with additional budget or realignments.

Every shock is our own estimate from data (other estimates are a check, never a target); every size is read from a script or a sourced value, not typed in:
  corruption   public investment at efficiency 0.77 in 2023-2025 (IMF PIMA gap 23%) instead of the best
               performers' 1.0; wasted money adds no capital (scenarios/corruption_efficiency_leakage.py)
  freeze       -₱238.3 bn public construction in 2025 (DBM)
  oil          2026: crude (Dubai) +49%, imported fuel products +77% (conflict period vs Jan-Feb 2026; 15 Oct:
               preshock/oil_shock_size.py); back to the Jan-Feb level from 2027 (an assumption: no lasting shock)
  El Nino      2026 wet-season and 2027 dry-season palay and corn losses (province panel; ONI 2.0 for the 2027 dry
               season), entered as lost effective land in the calendar year of each harvest (preshock/elnino_to_cge.py)
  food prices  2026: world rice +9.8% (Viet Nam 5%) and urea +28.9% (conflict period; preshock/agri_price_shock_size.py)
  typhoons     2026 damage documented by NDRRMC to 16 Sept: infrastructure ₱14.31 bn (public capital destroyed),
               agriculture ₱4.37 bn (crop output lost): an upper bound if the baseline already allows for a normal year
  geopolitics and domestic politics: about zero (our local projections, outputs/geopolitics_task1_comparison_20261015.md;
               BSP DP 2025-19): not entered
Policy common to every run, 2026-2027: the rice tariff at 15% (EO 105; a reference copy (not distributed)).
Reference: the clean path (efficiency 1.0 in 2023-2025, none of the shocks). Shapley (infinity_gem/decompose.py) splits the
combined result exactly among the six shocks (64 runs).

Stimulus (policy-mitigated) scenario, on top of all shocks; each measure from its source:
  A  realign the 2026 aid balance: ₱114.78 bn of released aid unobligated at 30 June 2026 (DBM), paid to
     the bottom 30% in 2026 (no new appropriation: a realignment)
  B  restore the 2027 aid cut: +₱90.21 bn (the 2027 NEP cuts aid from ₱325.69 bn to ₱235.48 bn; DBM), paid
     to the bottom 30% in 2027 (new appropriation)
  C  infrastructure catch-up: +₱208.7 bn public construction in 2027 = DPWH's 2025 carry-over still unobligated at 30 June
     2026 (DBM SAAODB): already appropriated, so it needs a validity extension into 2027, not new money
  D  procurement reform: public investment at the best performers' efficiency (1.0) from 2027 (no budget cost)
Bottom 30% = SAM quintile 1 and half of quintile 2, shared by population (rural and urban). Pesos: the same share of GDP
as in the 2023 SAM (scenarios/_common.to_sam_units, 2025 GDP), reported in 2025 pesos.
Settings: '0.3 recommended' with the rice split and land fixed by crop; hybrid closure (short run, all skill levels can
lose jobs, employment capped at the labour supply; 2023-2027 short run in every run); public capital low (central) and
high. NOT FOR CITATION until reviewed. Run:  py scenarios/combined_2025_2030.py   (about 10 minutes)
"""
import itertools
import sys

from _common import PSA_GDP, SAM_GDP_2023, Report, population_shares, to_sam_units, ROOT
import numpy as np
import pandas as pd

sys.path.insert(0, str(ROOT / "preshock"))
from infinity_gem import paths                                                     # noqa: E402
from infinity_gem.decompose import shapley                                          # noqa: E402
from infinity_gem.dynamic import DynamicCGE, PUBLIC_CAPITAL_DEFAULTS                # noqa: E402
from infinity_gem.microlink import MicroLink                                        # noqa: E402
from infinity_gem.oil import cge_oil_shock, fertilizer_cost_shares, fertilizer_cost_shock   # noqa: E402
from infinity_gem.settings import cge_model, dynamic_kwargs, short_run_closure      # noqa: E402
from oil_shock_size import shock_sizes as oil_sizes                             # noqa: E402
from agri_price_shock_size import shock_sizes as agri_sizes                     # noqa: E402
import elnino_to_cge as EN                                                      # noqa: E402

CONFLICT = "conflict period (Mar 2026 to latest)"
E_PH, E_BEST = 0.77, 1.0
SCANDAL, REFORM = (2023, 2024, 2025), (2027, 2028, 2029, 2030)
KEYS = (2023, 2024, 2025, 2026, 2027)
FALL25, CATCHUP, AID_2026, AID_2027 = 238.3, 208.7, 114.78, 90.21
TYPHOON = {"infrastructure": 14.31, "agriculture": 4.37}                     # NDRRMC to 16 Sept 2026 (a reference copy (not distributed))
TO_2025 = PSA_GDP[2025] / SAM_GDP_2023
SHOCKS = ["corruption", "freeze", "oil", "El Nino", "food and fertilizer prices", "typhoons"]

oil = oil_sizes().loc[CONFLICT]
CRUDE, PRODUCTS = float(oil["crude (Dubai)"]) / 100, float(oil["fuel products, weighted"]) / 100
agri = agri_sizes().loc[CONFLICT]
RICE_W, UREA = float(agri["rice, Viet Nam 5% (central)"]) / 100, float(agri["urea (central)"]) / 100

ps = population_shares()
B30 = {"hhd-r1": ps["hhd-r1"], "hhd-u1": ps["hhd-u1"], "hhd-r2": ps["hhd-r2"] / 2, "hhd-u2": ps["hhd-u2"] / 2}
B30 = {h: v / sum(B30.values()) for h, v in B30.items()}

g = pd.read_csv(paths.DATA_RAW / "macro" / "PSA_OpenSTAT_0542B5BCNQ1_construction_GFCF_by_sector_quarterly_2000-2026.csv",
                comment="#").set_index("Institutional Sector")
c23 = g[[c for c in g.columns if c.startswith("At Current Prices 2023")]].apply(pd.to_numeric).sum(axis=1)
S_PUB = float(c23["..General government"] / c23["Gross Fixed Capital Formation in Construction"])


def merge(*specs):
    """Combine CGE shock specs: factors multiply, amounts (trg_h_add) add."""
    out = {}
    for s in specs:
        for k, v in s.items():
            if k == "trg_h_add":
                cur = dict(out.get(k) or {})
                for h, a in v.items():
                    cur[h] = cur.get(h, 0.0) + a
                out[k] = cur
            elif isinstance(v, dict):
                cur = dict(out.get(k) or {})
                for i, f in v.items():
                    cur[i] = cur.get(i, 1.0) * f
                out[k] = cur
            else:
                out[k] = out.get(k, 1.0) * v
    return out


def static_land_cuts():
    """El Nino (and typhoon agriculture) land factors, sized in the one-year short-run model with the 2026 tariff."""
    m = cge_model("0.3 recommended", rice=True, sam_variant="ifpri", **short_run_closure("0.3 recommended"), land="fixed")   # 0.3.10: IFPRI, as run
    base = EN.policy_2026(m)
    b = m.solve(base)
    if not b.ok:                                   # never size the drought on an unsolved baseline
        raise RuntimeError(f"2026 policy baseline did not solve ({b.message})")
    cal = EN.calendar_year_losses(2.0)
    crops = ["arice", "amaiz"]
    out_crop = sum(float(b["QA"][m.A.index(a)] * b["PA"][m.A.index(a)]) for a in crops)
    ty = to_sam_units(TYPHOON["agriculture"], PSA_GDP[2025]) / out_crop          # share of rice and maize output lost
    cuts = {y: EN.land_cuts(m, b, cal[y], base) for y in cal}
    typh = EN.land_cuts(m, b, {a: ty for a in crops}, base)
    return cal, cuts, typh, ty, m


def main():
    cal, cuts, typh_cut, ty_share, m1 = static_land_cuts()
    rep = Report("The combined shocks of 2023-2027 and a stimulus package (Infinity GEM 0.3.7)", "combined_2025_2030")
    rep.p("**NOT FOR CITATION**. Reference: the clean path (public investment at efficiency 1.0 in 2023-2025, "
          "none of the shocks). Pesos are 2025 pesos (same share of GDP as in the 2023 SAM).")
    inputs = pd.DataFrame({
        "shock": ["corruption", "freeze", "oil", "oil", "El Nino 2026", "El Nino 2027", "food and fertilizer prices",
                  "food and fertilizer prices", "typhoons", "typhoons", "policy in every run"],
        "what": ["public investment efficiency 2023-2025", "public construction 2025 (₱ bn)", "crude, 2026 (%)",
                 "imported fuel products, 2026 (%)", "palay / corn lost, % of a year (land left)", "palay / corn lost, % of a year (land left)",
                 "world rice price, 2026 (%)", "urea, 2026 (%)", "infrastructure damage 2026 (₱ bn)", "agriculture damage 2026 (₱ bn; % of rice and maize output)",
                 "rice tariff 2026-2027"],
        "value": [f"{E_PH} vs {E_BEST}", f"-{FALL25}", f"{CRUDE * 100:+.1f}", f"{PRODUCTS * 100:+.1f}",
                  f"{cal[2026]['arice'] * 100:.2f} / {cal[2026]['amaiz'] * 100:.2f} ({cuts[2026]['arice']:.3f} / {cuts[2026]['amaiz']:.3f})",
                  f"{cal[2027]['arice'] * 100:.2f} / {cal[2027]['amaiz'] * 100:.2f} ({cuts[2027]['arice']:.3f} / {cuts[2027]['amaiz']:.3f})",
                  f"{RICE_W * 100:+.1f}", f"{UREA * 100:+.1f}", f"{TYPHOON['infrastructure']}",
                  f"{TYPHOON['agriculture']} ({ty_share * 100:.2f}%)",
                  f"{EN.TARIFF_2026:.0%} (EO 105) instead of {float(m1.tm[m1.C.index('cmric')]):.1%} (2023: BOC collections / PSA imports)"],
        "source": ["IMF CR 19/137", "DBM", "preshock/oil_shock_size.py (15 Oct)", "same",
                   "preshock/elnino_to_cge.py", "same", "preshock/agri_price_shock_size.py", "same",
                   "NDRRMC to 16 Sept 2026", "same", "USDA FAS GAIN RP2026-0004"]})
    rep.h("0. Inputs")
    rep.table(inputs.set_index("shock"))

    summary, shap_rows, pol_rows, years = [], [], [], {}
    for pcname in ("low", "high"):
        kw = dynamic_kwargs("0.3 recommended", public_capital=pcname, rice=True, land="fixed", sam_variant="ifpri")   # 0.3.10: IFPRI, as run
        pc0 = dict(kw["public_capital"])
        d = DynamicCGE(**kw)
        base = d.baseline()
        m = d.m
        ic = m.C.index("ccons")
        q0 = m.qinv[ic]
        tariff = {"tm_scale": {"cmric": EN.TARIFF_2026 / float(m.tm[m.C.index("cmric")])}}
        fert = fertilizer_cost_shock(m, UREA, fertilizer_cost_shares())
        oil26 = cge_oil_shock(m, CRUDE)
        oil26["pwm_scale"]["cpetr"] = 1 + PRODUCTS
        piece = {
            "freeze": {2025: {"qinv_scale": {"ccons": 1 - to_sam_units(FALL25, PSA_GDP[2025]) / q0}}},
            "oil": {2026: oil26},
            "El Nino": {2026: {"lscale": cuts[2026]}, 2027: {"lscale": cuts[2027]}},
            "food and fertilizer prices": {2026: merge({"pwm_scale": {"cmric": 1 + RICE_W}}, fert)},
            "typhoons": {2026: {"lscale": typh_cut}},
        }
        mls = {"short": MicroLink(d.ms), "long": MicroLink(m)}

        def run(S, measures=(), e_reform=False):
            """One path: the shocks in S plus stimulus measures (subset of 'ABCD')."""
            pc = dict(pc0, e=E_PH, ig_public_share=S_PUB, waste_lost=True,
                      e_path={**({} if "corruption" in S else {t: E_BEST for t in SCANDAL}),
                              **({t: E_BEST for t in REFORM} if "D" in measures else {})},
                      kg_loss={2026: to_sam_units(TYPHOON["infrastructure"], PSA_GDP[2025])} if "typhoons" in S else {})
            d.a["public_capital"], d.pc = pc, dict(PUBLIC_CAPITAL_DEFAULTS, **pc)
            sh = {t: dict(tariff) if t in (2026, 2027) else {} for t in KEYS}
            for f in S:
                for t, sp in piece.get(f, {}).items():
                    sh[t] = merge(sh[t], sp)
            if "A" in measures:
                a = to_sam_units(AID_2026, PSA_GDP[2025])
                sh[2026] = merge(sh[2026], {"trg_h_add": {h: a * w for h, w in B30.items()}})
            if "B" in measures:
                a = to_sam_units(AID_2027, PSA_GDP[2025])
                sh[2027] = merge(sh[2027], {"trg_h_add": {h: a * w for h, w in B30.items()}})
            if "C" in measures:
                sh[2027] = merge(sh[2027], {"qinv_scale": {"ccons": 1 + to_sam_units(CATCHUP, PSA_GDP[2025]) / q0}})
            return d.scenario(sh)

        def poor(ref, sim, year):
            short = year in KEYS
            ml, model = (mls["short"], d.ms) if short else (mls["long"], m)
            link = ml.link_variables(model, ref.solutions[year], sim.solutions[year])
            exp = ml.expected_results(link)["value"]
            R, G = "family inflation, reconciled to the SAM (recommended)", "group inflation (Infinity GEM published method)"
            return (exp[f"{R}: change in poor persons"], exp[f"{G}: change in poor persons"],
                    exp[f"{R}: Bottom 30% (deciles 1-3): total loss per family (PHP a year)"])

        def measures_of(ref, sim):
            r, s = ref.table, sim.table
            gap = (s.real_gdp / r.real_gdp - 1) * 100
            out = {"cumulative GDP loss 2023-2030 (₱ bn)": -float((s.real_gdp - r.real_gdp).sum()) * TO_2025,
                   "GDP gap 2025 (%)": float(gap[2025]), "GDP gap 2026 (%)": float(gap[2026]),
                   "GDP gap 2027 (%)": float(gap[2027]), "GDP gap 2030 (%)": float(gap[2030]),
                   "consumer prices 2026 (%)": float((s.cpi[2026] / r.cpi[2026] - 1) * 100),
                   "employment gap 2026 (pp)": float(s.employment_gap_low_skill_pct[2026] - r.employment_gap_low_skill_pct[2026]),
                   "employment gap 2027 (pp)": float(s.employment_gap_low_skill_pct[2027] - r.employment_gap_low_skill_pct[2027])}
            for y in (2025, 2026, 2027):
                own, grp, loss = poor(ref, sim, y)
                out[f"new poor {y}, own baskets"], out[f"new poor {y}, group method"] = own, grp
                out[f"bottom-30% loss per family {y} (₱ a year)"] = loss
            return out, gap

        clean = run(set())
        cache = {}

        def res_of(S):
            k = frozenset(S)
            if k not in cache:
                cache[k] = measures_of(clean, run(S))[0]
            return cache[k]

        for r_ in range(1, len(SHOCKS) + 1):
            for S in itertools.combinations(SHOCKS, r_):
                res_of(S)
        allon = res_of(SHOCKS)
        summary.append({"public capital": pcname, **allon})
        adverse = run(set(SHOCKS))
        years[pcname] = measures_of(clean, adverse)[1]
        if pcname == "low":
            for meas in ("cumulative GDP loss 2023-2030 (₱ bn)", "GDP gap 2026 (%)", "GDP gap 2027 (%)", "GDP gap 2030 (%)",
                         "new poor 2026, own baskets", "new poor 2027, own baskets", "new poor 2026, group method"):
                phi = shapley(lambda S: 0.0 if not S else res_of(S)[meas], SHOCKS)
                shap_rows.append({"measure": meas, **phi.to_dict(), "total": phi.attrs["total"]})
        # stimulus, against the adverse path; cost in 2025 pesos
        cost = {"A": AID_2026, "B": AID_2027, "C": CATCHUP, "D": 0.0}
        new_money = {"A": 0.0, "B": AID_2027, "C": 0.0, "D": 0.0}        # A realigned; C re-uses 2025 authority
        packages = {f"A: realign 2026 aid balance to the bottom 30% (₱{AID_2026} bn)": "A",
                    f"B: restore the 2027 aid cut (₱{AID_2027} bn)": "B",
                    f"C: infrastructure catch-up 2027 (₱{CATCHUP} bn)": "C",
                    "D: procurement reform from 2027 (no budget cost)": "D",
                    "A + B (aid)": "AB", "C + D (infrastructure with reform)": "CD",
                    "A + B + C + D (full package)": "ABCD"}
        adv_m = measures_of(clean, adverse)[0]
        for name, ms in packages.items():
            p = run(set(SHOCKS), ms)
            pm, pgap = measures_of(clean, p)
            if ms in ("CD", "ABCD"):
                years[f"{pcname}, with {name.split(' (')[0]}"] = pgap
            c, nm = sum(cost[k] for k in ms), sum(new_money[k] for k in ms)
            gain = adv_m["cumulative GDP loss 2023-2030 (₱ bn)"] - pm["cumulative GDP loss 2023-2030 (₱ bn)"]
            row = {"public capital": pcname, "package": name, "cost (₱ bn)": c, "of which new appropriations (₱ bn)": nm,
                   "cost (% of 2025 GDP)": c / PSA_GDP[2025] * 100,
                   "GDP gap 2026 (%)": pm["GDP gap 2026 (%)"], "GDP gap 2027 (%)": pm["GDP gap 2027 (%)"], "GDP gap 2030 (%)": pm["GDP gap 2030 (%)"],
                   "cumulative GDP recovered 2023-2030 (₱ bn)": gain, "GDP recovered per peso spent": gain / c if c else np.nan,
                   "share of the cumulative loss recovered (%)": gain / adv_m["cumulative GDP loss 2023-2030 (₱ bn)"] * 100,
                   "new poor 2026, own baskets": pm["new poor 2026, own baskets"], "new poor 2027, own baskets": pm["new poor 2027, own baskets"],
                   "bottom-30% loss per family 2027 (₱ a year)": pm["bottom-30% loss per family 2027 (₱ a year)"],
                   "employment gap 2027 (pp)": pm["employment gap 2027 (pp)"]}
            pol_rows.append(row)
        print(pcname, "done")

    rep.h("1. The combined shocks against the clean path")
    rep.table(pd.DataFrame(summary).set_index("public capital").T, floatfmt=",.3f")
    rep.p("GDP gaps: % of the clean path; employment gap: percentage points of the labour supply (negative = jobs lost); new "
          "poor: persons, FIES 2023 families ('own baskets' = each family's own inflation, recommended; 'group method' = Infinity GEM's "
          "published method); bottom-30% loss: ₱ a year per family, own baskets.")
    rep.h("2. Each shock's share (Shapley; public capital low; contributions add up exactly to the total)")
    rep.table(pd.DataFrame(shap_rows).set_index("measure"), floatfmt=",.3f")
    rep.h("3. Year by year: real GDP gap vs the clean path (%)")
    rep.table(pd.DataFrame(years), floatfmt=",.3f")
    rep.h("4. The stimulus package, measure by measure (against the clean path; the adverse path is in section 1)")
    rep.table(pd.DataFrame(pol_rows).set_index(["public capital", "package"]), floatfmt=",.3f")
    rep.p("Cost: ₱ bn of 2026-2027 spending (A is a realignment of money already released; C re-uses DPWH's 2025 authority through a "
          "validity extension; only B needs a new appropriation; D "
          "costs nothing in the budget but needs procurement and audit reform). GDP recovered per peso: cumulative 2023-2030 GDP "
          "recovered / cost. The model takes the financing from government saving (a larger deficit), with no crowding out in "
          "the short-run years; the fiscal cost must be read beside it.")
    rep.p("Assumptions to review: oil back to its January-February level from 2027; the 2027 dry-season ONI 2.0; typhoon damage "
          "documented to 16 Sept 2026, entered as a shock (upper bound if the baseline allows for a normal year); efficiency 0.77 "
          "and no leakage (the efficiency and leakage channel gives the higher bounds); public capital low (central) and high; employment capped at the "
          "labour supply in short-run years.")
    rep.save()
    # the same tables as CSV, for the figures (nothing typed in)
    stem = paths.output_dir() / f"combined_2025_2030_{pd.Timestamp.today():%Y%m%d}"
    pd.DataFrame(summary).set_index("public capital").T.to_csv(f"{stem}_summary.csv")
    pd.DataFrame(shap_rows).set_index("measure").to_csv(f"{stem}_shapley.csv")
    pd.DataFrame(years).to_csv(f"{stem}_gdp_gap_by_year.csv")
    pd.DataFrame(pol_rows).to_csv(f"{stem}_stimulus.csv", index=False)
    inputs.to_csv(f"{stem}_inputs.csv", index=False)
    print(pd.DataFrame(summary).set_index("public capital").T.round(3).to_string())
    print(pd.DataFrame(shap_rows).set_index("measure").round(3).to_string())
    print(pd.DataFrame(pol_rows).set_index(["public capital", "package"]).round(3).to_string())


if __name__ == "__main__":
    main()
