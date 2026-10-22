"""The 2025-2027 shocks and a costed response, REVISED after the audit of 15 Oct 2026 night (0.3.7).

Replaces scenarios/combined_2025_2030.py for the 2026 scenarios (that script stays, unchanged, so the first draft's
numbers can be reproduced). Audit and reasons: an audit note of 15 Oct 2026 (not included). 15 Oct 2026: drop public-investment inefficiency as a shock; remove every hand-picked value;
drop double counts; adopt an earlier fiscal block (revenue, deficit, debt); proceed with the revised run.

What changed against the first run:
  1. No 'corruption' efficiency shock. The efficiency gap (IMF PIMA 0.77) is a long-standing condition, already in the data
     and in every forecast; it is kept only as the share of a CHANGE in public construction that becomes usable capital
     (e = 0.77). The measurable 2025-26 effect of the scandal is the construction that was not done ('public works').
  2. Public construction counted once: public capital only (public_capital general_stock=False; check PK1).
  3. Every world price as a calendar-year average of actual months plus a published forecast, against the government's
     pre-conflict assumption (preshock/shock_paths.py): oil to 2030 (actual, EIA STEO 1 Oct 2026, DBCC 193rd; vs DBCC
     192nd US$65), world rice and urea (actual, then no change).
  4. Public works 2026 added: PSA general government construction, H1 2026 actual (-30% on H1 2025), H2 by the
     year-on-year rate (preshock/shock_paths.public_works); 2025 from the same PSA series.
  5. Short-run closure only in 2025-2027 (short_run_years; check SR1); oil above the pre-conflict assumption in 2028-2030
     is solved in the long-run closure.
  6. Typhoons not entered: the baseline already assumes a normal year, and 2026 damage to date is not shown to be above
     normal (no verified average on file).
  7. Policies in every run (the no-shock path too): rice tariff 15% in 2026-2027 (EO 105); the 2027 NEP's cut in aid,
     -₱90.21 bn to the bottom 30% (DBM).
  8. Response measures: A (realign the 2026 aid balance, ₱114.78 bn, E8), B (restore the 2027 aid cut, ₱90.21 bn, E5), C
     (spend DPWH's 2025 carry-over in 2027, ₱208.7 bn, B22). The zero-cost jump to best-practice efficiency (old D) is
     dropped: its size was hand-picked.
  9. Fiscal block (as an earlier fixed-price estimate): government saving from the model; construction not done
     narrows the deficit and the catch-up widens it (the CGE books public construction as investment, not as government
     spending: the Sector's 'routing A'); debt-to-GDP from the cumulative deficit and the change in nominal GDP.
 10. Validation: the pre-shock targets (DBCC June and December 2025) plus the model's effects against what happened (PSA)
     and the government's July 2026 revision.
Second revision (16 Oct 2026, about 1-2 AM):
 11. Jobs: a wage curve in the short-run years (dynamic.py wage_curve), beta calibrated so the model's 2026 job loss equals
     what PSA data imply (scenarios/calibrate_wage_curve.py; preshock/okun.py). Without it every skill level lost work at
     a fixed real wage and labour input fell 8.75% in 2026, about four times what the LFS shows.
 12. Targeting: aid reaches households as 4Ps does (PIDS DP 2024-27, Albert, Orbeta, Melad and Mahmoud, Dec 2024, Table 13:
     beneficiaries by per-capita income decile; 66.6% in the bottom 30%), for measures A and B and the 2027 NEP cut; perfect
     targeting of the bottom 30% is shown as a variant.
 13. Public works in 2027: the programme (central, as the DBCC's growth path assumes) or the 2026 shortfall persisting (no-
     change forecast), as a sensitivity.
Third revision (16 Oct 2026, afternoon: the CGE's price fall as a caveat only; the peso out of the central run; measure A as a range; 2027 public works central, with two recovery scenarios):
 14. Public works in 2027 from the 2027 budget: DPWH's money available in 2027 (NEP ₱643.9 bn + FY2026 money still uncommitted
     at end-2026, valid to end-2027) x DPWH's commitment rate, the latest actual (2025, 78.0%) as central and 2024's (87.9%) as
     recovery; programme and persistence kept as bounds (preshock/shock_paths.public_works_2027).
 15. Measure A as a range: upper bound = the whole ₱114.78 bn as extra 2026 spending (as before); lower bound = only the part
     that 2025's June-to-December pattern says would still be uncommitted at end-2026 is extra (A_LOW_EXTRA), at 4Ps targeting
     . Re-targeting the rest is NOT counted: the first version of this run moved it 'from the SAM's
     transfer pattern to 4Ps', but the SAM's ₱103.7 bn of government transfers is essentially 4Ps itself and more concentrated
     on the poor (88% to the bottom two quintiles, against 78% for PIDS's 4Ps incidence), so that step moved money away from
     the poorest. No study measures the incidence of AICS, TUPAD, MAIFIP or AKAP (searched 16 Oct 2026), so the gain from
     re-targeting them to 4Ps channels is real but unmeasured; it would add to the lower bound.
 16. Caveats added: the CGE's short-run prices fall with demand (public works lower 2026 consumer prices by 2.3%, against
     about 0.3-0.8 points in the data: preshock/inflation_var.py), so the poverty effect of the public-works shock is if
     anything understated; the peso is held at its pre-shock path (sensitivity: scenarios/peso_sensitivity.py).
Fourth revision (17 Oct 2026, after code review of the 2026 scenarios of 16 Oct 2026):
 17. Wage curve (finding C1): beta now calibrated so the model's 2026 job loss equals Okun's e x the model's OWN effect on 2026
     growth (scenarios/calibrate_wage_curve.py), not e x the whole observed shortfall, which had loaded all of the LFS job loss
     onto the four shocks. The 16 Oct calibration is kept as the upper bound (sensitivity row), and a no-COVID Okun row and a
     near-full-employment row are added, because e = 0.71 is identified by the 2020-21 quarters.
 18. Peso amounts (finding I1): every amount of year y is entered as its share of YEAR y's nominal GDP (_common.PSA_GDP: 2025 PSA;
     2026-27 implied by the DBCC 193rd statement), not of 2025's. Results stay in 2025-peso equivalents (the same share of 2025
     GDP); the deficit entries and the cost column are converted the same way, and 'output recovered per peso' is computed on
     that common basis (the nominal cost is also reported).
NOT FOR CITATION until reviewed. Run:  py scenarios/combined_revised.py   (about 25 minutes)
"""
import itertools
import sys

from _common import PSA_GDP, SAM_GDP_2023, Report, equiv_2025, population_shares, to_sam_units, ROOT
import numpy as np
import pandas as pd

sys.path.insert(0, str(ROOT / "preshock"))
from infinity_gem import paths                                                     # noqa: E402
from infinity_gem.decompose import shapley                                          # noqa: E402
from infinity_gem.dynamic import DynamicCGE, PUBLIC_CAPITAL_DEFAULTS                # noqa: E402
from infinity_gem.microlink import MicroLink                                        # noqa: E402
from infinity_gem.oil import cge_oil_shock, fertilizer_cost_shares, fertilizer_cost_shock   # noqa: E402
from infinity_gem.settings import cge_model, dynamic_kwargs, short_run_closure      # noqa: E402
import shock_paths as SP                                                        # noqa: E402
import elnino_to_cge as EN                                                      # noqa: E402

SHORT = (2025, 2026, 2027)
YEARS = (2025, 2026, 2027, 2028, 2029, 2030)
AID_2026, AID_2027, CATCHUP = 114.78, 90.21, 208.7
# Measure A, lower bound (DBM SAAODB By Agency, FY2025 Q2 and Q4): share of what each agency had not committed in
# June 2025 that was still uncommitted in December 2025, applied to the June 2026 unobligated aid by agency (E7: MAIFIP 16.55,
# DOH; E8: TUPAD 15.18, DOLE; the rest of the ₱114.78 bn at DSWD's share, an assumption for the other aid agencies).
_STILL_OPEN_DEC25 = {"DSWD": (265.9 - 255.3) / (215.9 - 149.7), "DOLE": (58.6 - 50.5) / (52.7 - 22.9), "DOH": 37.1 / 135.0}
A_LOW_EXTRA = 16.55 * _STILL_OPEN_DEC25["DOH"] + 15.18 * _STILL_OPEN_DEC25["DOLE"] + (AID_2026 - 16.55 - 15.18) * _STILL_OPEN_DEC25["DSWD"]
A_LOW_RETARGET = AID_2026 - A_LOW_EXTRA                               # re-targeted, gain not counted (see note 15)
TO_2025 = PSA_GDP[2025] / SAM_GDP_2023
SHOCKS = ["public works", "oil", "El Nino", "world food and fertilizer prices"]
# 0.3.10 (18 Oct 2026): the 2026 scenarios of 17-18 Oct 2026 are built on IFPRI's 2023 SAM; Infinity GEM's default for rice=True runs is now the project's
# own SAM (settings.DEFAULT_SAM_VARIANT), so this script pins IFPRI's to keep reproducing the 2026 scenarios. Other SAMs: set this, or use
# scenarios/sam_psa_sensitivity.py (which overrides it and recalibrates the wage curve on that SAM).
from _common import SCENARIO_SAM                                                    # noqa: E402
SAM_VARIANT = SCENARIO_SAM          # "ifpri" unless INFINITY_GEM_SCENARIO_SAM=own (the 2026 scenarios of 18 Oct 2026 on Infinity GEM's own SAM; scenarios/_common.py)
# Validation targets (pre-shock and revised official paths; actual data)
PRE_SHOCK_GROWTH = {2025: 6.0, 2026: 5.5, 2027: 6.0}     # DBCC 26 Jun 2025 (2025: 5.5-6.5); DBCC 192nd, 9 Dec 2025 (2026-27)
REVISED_GROWTH = {2025: "4.4 (PSA actual)", 2026: "3.5-4.5 (DBCC 193rd, Jul 2026); H1 actual 2.6", 2027: "5.0-6.0 (DBCC 193rd)"}
PRE_SHOCK_CPI = {2026: 3.0}                               # DBCC 192nd: 2.0-4.0
# NG debt end-June 2026 as used earlier (BTr) - not yet verified
NG_DEBT, DEBT_SOURCE = 19070.0, "₱19,070 bn, end-June 2026 (BTr, as used earlier; to verify)"

ps = population_shares()
B30 = {"hhd-r1": ps["hhd-r1"], "hhd-u1": ps["hhd-u1"], "hhd-r2": ps["hhd-r2"] / 2, "hhd-u2": ps["hhd-u2"] / 2}
B30 = {h: v / sum(B30.values()) for h, v in B30.items()}
# 4Ps beneficiaries by per-capita income decile, % (PIDS DP 2024-27, Table 13: 2024 PIDS-SWS veracity survey, 2018 FIES deciles)
PIDS_4PS_DECILES = [24.15, 23.86, 18.61, 11.22, 10.02, 6.91, 2.95, 1.54, 0.70, 0.04]
_q = [sum(PIDS_4PS_DECILES[2 * i:2 * i + 2]) / 100 for i in range(5)]             # SAM quintile groups = decile pairs
AID_4PS = {}
for i, share in enumerate(_q, start=1):
    r, u = ps[f"hhd-r{i}"], ps[f"hhd-u{i}"]                                     # rural/urban split by population
    AID_4PS[f"hhd-r{i}"], AID_4PS[f"hhd-u{i}"] = share * r / (r + u), share * u / (r + u)
AID_4PS = {h: v / sum(AID_4PS.values()) for h, v in AID_4PS.items()}
CALIB = None                                                                    # wage-curve beta: read in main()


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


def land_cuts(oni):
    """El Nino land factors by calendar year, sized in the one-year short-run model with the 2026 tariff."""
    m = cge_model("0.3 recommended", rice=True, sam_variant=SAM_VARIANT, **short_run_closure("0.3 recommended"), land="fixed")
    base = EN.policy_2026(m)
    b = m.solve(base)
    if not b.ok:
        raise RuntimeError(f"2026 policy baseline did not solve ({b.message})")
    cal = EN.calendar_year_losses(oni)
    return cal, {y: EN.land_cuts(m, b, cal[y], base) for y in cal}


class Runs:
    """One public-capital setting: the model, its no-shock path and every path asked for."""

    def __init__(self, pcname, growth=None, wage_curve=None, targeting="4Ps", **engine):
        kw = dynamic_kwargs("0.3 recommended", public_capital=pcname, rice=True, land="fixed", sam_variant=SAM_VARIANT)
        kw["wage_curve"] = wage_curve
        kw.update(__import__("_common").SCENARIO_ENGINE)   # 0.3.11 (19 Oct 2026): INFINITY_GEM_SCENARIO_ENGINE, e.g. {"hoarding": 0.85}; unset = {}
        kw.update(engine)                            # 0.3.8: engine sensitivities (scenarios/engine_sensitivities.py)
        self.alloc = AID_4PS if targeting == "4Ps" else B30
        if growth:
            kw["growth"] = {**kw["growth"], **growth}
        kw["public_capital"] = dict(kw["public_capital"], general_stock=False)
        kw["short_run_years"] = SHORT
        self.d = DynamicCGE(**kw)
        self.d.baseline()
        self.m = m = self.d.m
        self.q0 = m.qinv[m.C.index("ccons")]
        self.trg_pattern = {h: float(v) / float(m.trg_h.sum()) for h, v in zip(m.H, m.trg_h)}   # current transfers by household
        self.fshares = fertilizer_cost_shares()
        self.ml = MicroLink(self.d.ms)
        self.cache = {}

    def pieces(self, oil_nc="central", oil_fc="EIA", pw="2026 central", oni="central", pw2027="2027 NEP x 2025 rate (central)"):
        m = self.m
        oil = SP.oil_paths(oil_nc, oil_fc)
        food = SP.food_paths()
        pw_ = SP.public_works()
        pw_.update({k: v for k, v in SP.public_works_2027().items() if k.startswith("2027 NEP")})
        _, cuts = land_cuts(EN.ONI_S1[oni])
        o = {}
        for t in range(2026, 2031):
            s = cge_oil_shock(m, float(oil.loc[t, "crude (Dubai)"]) / 100)
            s["pwm_scale"]["cpetr"] = 1 + float(oil.loc[t, "fuel products, weighted"]) / 100
            o[t] = s
        f = {t: merge({"pwm_scale": {"cmric": 1 + float(food.loc[t, "world rice"]) / 100}},
                      fertilizer_cost_shock(m, float(food.loc[t, "urea"]) / 100, self.fshares)) for t in range(2026, 2031)}
        cut = lambda bn, y: {"qinv_scale": {"ccons": 1 + to_sam_units(bn, PSA_GDP[y]) / self.q0}}   # share of year y's GDP (note 18)
        works = {2025: cut(pw_["2025"], 2025), 2026: cut(pw_[pw], 2026)}
        if pw2027 == "no change":                   # the 2026 shortfall persists through 2027 (same pesos, 2027's GDP)
            works[2027] = cut(pw_[pw], 2027)
        elif pw2027.startswith("2027 NEP"):          # third revision: the 2027 budget x DPWH's commitment rate
            works[2027] = cut(pw_[pw2027], 2027)
        return {"public works": works,
                "oil": o,
                "El Nino": {2026: {"lscale": cuts[2026]}, 2027: {"lscale": cuts[2027]}},
                "world food and fertilizer prices": f}, {"oil": oil, "food": food, "public works": pw_}

    def run(self, S, measures="", piece=None):
        d, m = self.d, self.m
        tariff = {"tm_scale": {"cmric": EN.TARIFF_2026 / float(m.tm[m.C.index("cmric")])}}
        aid = lambda bn, y, alloc=None: {"trg_h_add": {h: to_sam_units(bn, PSA_GDP[y]) * w for h, w in (alloc or self.alloc).items()}}
        sh = {2025: {}, 2026: dict(tariff), 2027: merge(tariff, aid(-AID_2027, 2027))}   # policies in every run (note 18: year y's GDP)
        for f in S:
            for t, sp in piece[f].items():
                sh[t] = merge(sh.get(t, {}), sp)
        if "A" in measures:
            sh[2026] = merge(sh[2026], aid(AID_2026, 2026, B30 if "*" in measures else None))
        if "a" in measures:                          # A, lower bound: only the extra spending (re-targeting gain unmeasured)
            sh[2026] = merge(sh[2026], aid(A_LOW_EXTRA, 2026))
        if "B" in measures:
            sh[2027] = merge(sh[2027], aid(AID_2027, 2027))
        if "C" in measures:
            sh[2027] = merge(sh[2027], {"qinv_scale": {"ccons": 1 + to_sam_units(CATCHUP, PSA_GDP[2027]) / self.q0}})
        return d.scenario(sh)

    def poor(self, ref, sim, y):
        link = self.ml.link_variables(self.d.ms, ref.solutions[y], sim.solutions[y])
        e = self.ml.expected_results(link)["value"]
        R, G = "family inflation, reconciled to the SAM (recommended)", "group inflation (Infinity GEM published method)"
        return (e[f"{R}: change in poor persons"], e[f"{G}: change in poor persons"],
                e[f"{R}: Bottom 30% (deciles 1-3): total loss per family (PHP a year)"])

    def measures(self, ref, sim, works=None, extra_spend=None, poor=True, deflator_dev=None):
        r, s = ref.table, sim.table
        gap = (s.real_gdp / r.real_gdp - 1) * 100
        cpi = (s.cpi / r.cpi - 1) * 100
        out = {f"GDP gap {y} (%)": float(gap[y]) for y in YEARS}
        loss = -float((s.real_gdp - r.real_gdp).sum()) * TO_2025
        out["cumulative GDP loss 2025-2030 (₱ bn)"] = loss
        out["cumulative GDP loss 2025-2030 (% of 2025 GDP)"] = loss / PSA_GDP[2025] * 100
        out["consumer prices 2026 (%)"] = float(cpi[2026])
        out["inflation effect 2026 (pp)"] = float(((1 + cpi[2026] / 100) / (1 + cpi[2025] / 100) - 1) * 100)
        for y in (2026, 2027):
            out[f"employment gap {y} (pp of labour supply)"] = float(s.employment_gap_low_skill_pct[y] - r.employment_gap_low_skill_pct[y])
        # fiscal block: deficit change (+ = larger), ₱ bn in 2025-peso equivalents (the same share of GDP; note 18)
        dg = {y: -(float(sim.solutions[y]["GSAV"]) - float(ref.solutions[y]["GSAV"])) * TO_2025 for y in YEARS}
        for y, bn in (works or {}).items():          # construction not done: spending not made (routing A); bn in year y's pesos
            dg[y] = dg.get(y, 0.0) + equiv_2025(bn, y)  # bn < 0 narrows the deficit
        for y, bn in (extra_spend or {}).items():    # catch-up spending, year y's pesos
            dg[y] = dg.get(y, 0.0) + equiv_2025(bn, y)
        for y in (2026, 2027):
            out[f"deficit change {y} (₱ bn)"] = dg[y]
            out[f"deficit change {y} (% of GDP)"] = dg[y] / (PSA_GDP[2025] * float(s.nominal_gdp[y] / r.nominal_gdp[2025])) * 100
        # review D8 (17 Oct 2026): nominal GDP here is real GDP at model prices (no inflation path), so the debt ratio's
        # denominator catches real-GDP changes only; an oil shock that raises the price level would lower the ratio in reality.
        # 21 Oct 2026 (0.3.12; D8 as a reporting Oct 2026): (i) the
        # sensitivity the 2026 scenarios quote is computed here (the ratio's fall per 1% on the GDP deflator, at the debt stock
        # over 2026 nominal GDP); (ii) deflator_dev={year: % deviation of the GDP deflator from its pre-shock path} is an opt-in
        # input that scales the scenario's nominal GDP in the denominator (no sourced value yet; None leaves every result as before)
        d0 = NG_DEBT / PSA_GDP[2025]
        pdev = {y: 1.0 + (deflator_dev or {}).get(y, 0.0) / 100 for y in YEARS}
        for y in (2027, 2030):
            cum = sum(dg[t] for t in YEARS if t <= y)
            ngdp = PSA_GDP[2025] * float(s.nominal_gdp[y] / r.nominal_gdp[2025]) * pdev[y]
            out[f"debt-to-GDP change {y} (pp)"] = (cum / ngdp - d0 * (float(s.nominal_gdp[y] / r.nominal_gdp[y]) * pdev[y] - 1)) * 100
        out["debt-to-GDP: fall per 1% on the GDP deflator (pp; D8)"] = -NG_DEBT / PSA_GDP[2026]
        if poor:
            for y in SHORT:
                own, grp, l30 = self.poor(ref, sim, y)
                out[f"new poor {y} (M, own baskets)"] = own / 1e6
                out[f"new poor {y} (M, group method)"] = grp / 1e6
                out[f"bottom-30% loss per family {y} (₱ a year)"] = l30
                try:                                 # 0.3.10: consumer prices on PSA's CPI weights (reporting only)
                    from infinity_gem import psa_cpi
                    pc = psa_cpi.change(self.ml.link_variables(self.d.ms, ref.solutions[y], sim.solutions[y]))
                    out[f"consumer prices {y}, PSA CPI weights (%)"] = pc["all households"]
                    out[f"consumer prices {y}, PSA CPI weights, bottom 30% (%)"] = pc["bottom 30%"]
                except ValueError:                   # a SAM without the petroleum split: the PSA map does not apply
                    pass
        return out, gap


def main():
    rep = Report("The 2025-2027 shocks and a costed response, fourth revision (Infinity GEM 0.3.8)", "combined_revised")
    rep.p("**NOT FOR CITATION** (audit of 15 Oct 2026 night; code review of 16 Oct 2026, findings C1 and I1 applied). Reference: "
          "the no-shock path with the same policies (rice tariff 15% in 2026-27; the 2027 NEP aid cut). Pesos: an amount of year y "
          "enters as its share of year y's nominal GDP (2025 PSA; 2026-27 implied by the DBCC 193rd statement: ₱30.5 and ₱33.2 "
          "trillion); results are in 2025-peso equivalents (the same share of 2025 GDP). Every shock size comes from data or a "
          "published forecast (preshock/shock_paths.py); what is still an assumption is listed in section 8.")
    if __import__("_common").SCENARIO_ENGINE:
        rep.p(f"**Engine settings added for this run (INFINITY_GEM_SCENARIO_ENGINE): {__import__('_common').SCENARIO_ENGINE}.** Not the 2026 scenarios' own "
              "setting; e.g. hoarding = paid labour hoarding (a review note (not included)).")
    rows_tot, shap_rows, years, pol_rows, sens = [], [], {}, [], {}
    cal = pd.read_csv(__import__("_common").calibration_file(), index_col=0)
    BETA = {"central": float(cal.loc["central (e)", "beta"]), "smaller job loss": float(cal.loc["smaller job loss (e - 2 s.e.)", "beta"]),
            "larger job loss": float(cal.loc["larger job loss (e + 2 s.e.)", "beta"]),
            "observed shortfall": float(cal.loc["observed shortfall (previous central; upper bound)", "beta"]),
            "no-COVID": float(cal.loc["no-COVID Okun (2020-2021 dropped)", "beta"])}
    if "hours-inclusive Okun (2020-2021 dropped)" in cal.index:     # 0.3.10: calibrations from 18 Oct 2026 on carry it
        BETA["hours"] = float(cal.loc["hours-inclusive Okun (2020-2021 dropped)", "beta"])
    for pcname in ("low", "high"):
        R = Runs(pcname, wage_curve=BETA["central"])
        piece, src = R.pieces()
        pw = src["public works"]
        works = {2025: pw["2025"], 2026: pw["2026 central"], 2027: pw["2027 NEP x 2025 rate (central)"]}
        clean = R.run(set(), piece=piece)
        cache = {}

        def res(S):
            k = frozenset(S)
            if k not in cache:
                w = works if "public works" in S else {}
                cache[k] = R.measures(clean, R.run(S, piece=piece), works=w, poor=(pcname == "low" or len(S) == len(SHOCKS)))[0]
            return cache[k]

        if pcname == "low":
            for r_ in range(1, len(SHOCKS) + 1):
                for S in itertools.combinations(SHOCKS, r_):
                    res(S)
            for meas in ("cumulative GDP loss 2025-2030 (₱ bn)", "GDP gap 2026 (%)", "GDP gap 2027 (%)", "GDP gap 2030 (%)",
                         "consumer prices 2026 (%)", "new poor 2026 (M, own baskets)", "new poor 2027 (M, own baskets)"):
                phi = shapley(lambda S: 0.0 if not S else res(S)[meas], SHOCKS)
                shap_rows.append({"measure": meas, **phi.to_dict(), "total": phi.attrs["total"]})
            singles = pd.DataFrame({s_: res((s_,)) for s_ in SHOCKS}).T      # 17 Oct (review, I3): each shock alone, like-for-like
            singles.index.name = "shock alone"                               # with single-shock benchmarks (World Bank, PIDS)
            inputs = src
        allon = res(SHOCKS)
        rows_tot.append({"public capital": pcname, **allon})
        adverse = R.run(set(SHOCKS), piece=piece)
        years[f"{pcname}: shocks"] = R.measures(clean, adverse, poor=False)[1]
        packages = {f"A, upper bound: realign the 2026 aid balance (₱{AID_2026} bn, all extra)": "A",
                    f"A, lower bound: ₱{A_LOW_EXTRA:.1f} bn extra (re-targeting of the other ₱{A_LOW_RETARGET:.1f} bn not counted)": "a",
                    f"B: restore the 2027 aid cut (₱{AID_2027} bn)": "B",
                    f"C: spend DPWH's 2025 carry-over in 2027 (₱{CATCHUP} bn)": "C", "A + B (A upper)": "AB", "A + B (A lower)": "aB",
                    "A + B + C (A upper)": "ABC", "A + B + C (A lower)": "aBC",
                    "variant: A with perfect targeting (bottom 30% only)": "A*"}
        for name, ms in packages.items():
            p = R.run(set(SHOCKS), ms, piece=piece)
            pm, pgap = R.measures(clean, p, works=works, extra_spend={2027: CATCHUP} if "C" in ms else None)
            if ms == "ABC":
                years[f"{pcname}: shocks + A + B + C"] = pgap
            cost = (AID_2026 if ("A" in ms or "a" in ms) else 0) + (AID_2027 if "B" in ms else 0) + (CATCHUP if "C" in ms else 0)
            cost_eq = ((equiv_2025(AID_2026, 2026) if ("A" in ms or "a" in ms) else 0) + (equiv_2025(AID_2027, 2027) if "B" in ms else 0)
                       + (equiv_2025(CATCHUP, 2027) if "C" in ms else 0))        # note 18: the same basis as the output recovered
            new_money = AID_2027 if "B" in ms else 0.0
            gain = allon["cumulative GDP loss 2025-2030 (₱ bn)"] - pm["cumulative GDP loss 2025-2030 (₱ bn)"]
            pol_rows.append({"public capital": pcname, "measure": name, "cost (₱ bn)": cost, "of which new appropriation (₱ bn)": new_money,
                             "cost (₱ bn, 2025-peso equivalent)": cost_eq,
                             "GDP gap 2026 (%)": pm["GDP gap 2026 (%)"], "GDP gap 2027 (%)": pm["GDP gap 2027 (%)"],
                             "GDP gap 2030 (%)": pm["GDP gap 2030 (%)"], "output recovered 2025-2030 (₱ bn)": gain,
                             "output recovered per peso": gain / cost_eq if cost_eq else np.nan,
                             "output recovered per nominal peso": gain / cost if cost else np.nan,
                             "new poor 2026 (M)": pm["new poor 2026 (M, own baskets)"], "new poor 2027 (M)": pm["new poor 2027 (M, own baskets)"],
                             "poor protected 2026 (M)": allon["new poor 2026 (M, own baskets)"] - pm["new poor 2026 (M, own baskets)"],
                             "poor protected 2027 (M)": allon["new poor 2027 (M, own baskets)"] - pm["new poor 2027 (M, own baskets)"],
                             "deficit change 2026 (₱ bn)": pm["deficit change 2026 (₱ bn)"] - allon["deficit change 2026 (₱ bn)"],
                             "deficit change 2027 (₱ bn)": pm["deficit change 2027 (₱ bn)"] - allon["deficit change 2027 (₱ bn)"],
                             "debt-to-GDP change 2030 (pp)": pm["debt-to-GDP change 2030 (pp)"] - allon["debt-to-GDP change 2030 (pp)"]})
        if pcname == "low":                         # sensitivities of the combined result (central public capital)
            for label, kw in (("oil: no-conflict US$60 (DBCC low)", dict(oil_nc="low")),
                              ("oil: no-conflict US$70 (DBCC high)", dict(oil_nc="high")),
                              ("oil: no-change forecast (stays at the latest month to end-2027)", dict(oil_fc="no change")),
                              ("public works 2026: lower bound (H2 2026 = H2 2025)", dict(pw="2026 low")),
                              ("El Nino: ONI 1.5", dict(oni="low")), ("El Nino: ONI 2.5", dict(oni="high")),
                              ("public works 2027: NEP x 2024 commitment rate (recovery)", dict(pw2027="2027 NEP x 2024 rate (recovery)")),
                              ("public works 2027: programme, back to the 2024 level (second revision's central; upper bound)", dict(pw2027="programme")),
                              ("public works 2027: the 2026 shortfall persists (no-change forecast; lower bound)", dict(pw2027="no change"))):
                pc_, s_ = R.pieces(**kw)
                w = {2025: s_["public works"]["2025"], 2026: s_["public works"][kw.get("pw", "2026 central")]}
                p27 = kw.get("pw2027", "2027 NEP x 2025 rate (central)")
                if p27 == "no change":
                    w[2027] = w[2026]
                elif p27.startswith("2027 NEP"):
                    w[2027] = s_["public works"][p27]
                sens[label] = R.measures(clean, R.run(set(SHOCKS), piece=pc_), works=w, poor=True)[0]
            for label, b_ in (("jobs: wage curve for a smaller job loss (Okun e - 2 s.e.)", BETA["smaller job loss"]),
                              ("jobs: wage curve for a larger job loss (Okun e + 2 s.e.)", BETA["larger job loss"]),
                              ("jobs: wage curve matched to the whole observed LFS fall (16 Oct central; upper bound)", BETA["observed shortfall"]),
                              ("jobs: wage curve with the no-COVID Okun elasticity (2020-2021 dropped)", BETA["no-COVID"]),
                              *((("jobs: wage curve set to the hours-inclusive Okun elasticity (2020-2021 dropped)", BETA["hours"]),)
                                if "hours" in BETA else ()),                 # 0.3.10 (18 Oct 2026)
                              ("jobs: near-full employment (beta 40)", 40.0),
                              ("jobs: no wage curve (first revised run: fixed real wages)", None)):
                Rw = Runs("low", wage_curve=b_)
                pw_, sw_ = Rw.pieces()
                sens[label] = Rw.measures(Rw.run(set(), piece=pw_), Rw.run(set(SHOCKS), piece=pw_),
                                          works={2025: sw_["public works"]["2025"], 2026: sw_["public works"]["2026 central"],
                                                 2027: sw_["public works"]["2027 NEP x 2025 rate (central)"]}, poor=True)[0]
    # baseline check: the pre-shock DBCC growth path instead of the July 2026 path (deviations should barely move)
    Rg = Runs("low", growth={2026: 5.5, 2027: 6.0, 2028: 6.5, 2029: 6.5, 2030: 6.5}, wage_curve=BETA["central"])
    pg, sg = Rg.pieces()
    sens["baseline growth: DBCC December 2025 path (5.5 / 6.0 / 6.5%)"] = Rg.measures(
        Rg.run(set(), piece=pg), Rg.run(set(SHOCKS), piece=pg), works={2025: sg["public works"]["2025"], 2026: sg["public works"]["2026 central"],
                                                                        2027: sg["public works"]["2027 NEP x 2025 rate (central)"]}, poor=True)[0]

    # ---- report
    oil, food, pw = inputs["oil"], inputs["food"], inputs["public works"]
    rep.p(f"Jobs: wage curve beta {BETA['central']:.3f} (scenarios/calibrate_wage_curve.py). Aid: 4Ps incidence (PIDS DP 2024-27).")
    rep.h("1. Shock sizes (from data and published forecasts)")
    rep.p(f"Oil, % against the DBCC's pre-conflict Dubai assumption (US$65, 9 Dec 2025); actual weekly prices to {oil.attrs['latest']}, "
          "then the EIA Short-Term Energy Outlook (1 Oct 2026) to end-2027, then the DBCC's July 2026 path (US$70).")
    rep.table(oil.round(1))
    rep.p(f"World rice (Viet Nam 5%) and urea, % against January-February 2026; actual to {food.attrs['latest']}, then no change.")
    rep.table(food.round(1))
    rep.p(f"Public works (general government construction, PSA, vs the same period of 2024, ₱ bn): 2025 {pw['2025']:,.1f}; 2026 "
          f"{pw['2026 central']:,.1f} (H1 2026 {pw['H1 2026 vs H1 2025 (%)']:+.1f}% on H1 2025; H2 at the same rate), lower bound "
          f"{pw['2026 low']:,.1f}; 2027 {pw['2027 NEP x 2025 rate (central)']:,.1f} (2027 budget x DPWH's 2025 commitment rate; recovery at "
          f"2024's rate {pw['2027 NEP x 2024 rate (recovery)']:,.1f}; preshock/shock_paths.public_works_2027). El Nino: palay and corn lost as land, 2026 wet season and 2027 dry season (ONI {EN.ONI_S1['central']}, "
          "read from the IRI plume of 21 Sept 2026; range 1.5-2.5).")
    tot = pd.DataFrame(rows_tot).set_index("public capital").T
    rep.h("2. Validation: the model's effects added to the pre-shock official path, against what happened")
    g = years["low: shocks"]
    eff = {y: ((1 + g[y] / 100) / (1 + (g[y - 1] if y > 2025 else 0) / 100) - 1) * 100 for y in SHORT}
    val = pd.DataFrame({"pre-shock official growth (%)": PRE_SHOCK_GROWTH, "model: effect of the shocks on growth (pp)": eff,
                        "pre-shock + effect (%)": {y: PRE_SHOCK_GROWTH[y] + eff[y] for y in SHORT},
                        "actual or revised official": REVISED_GROWTH})
    rep.table(val, floatfmt=".2f")
    infl = tot.loc["inflation effect 2026 (pp)", "low"]
    rep.p(f"Inflation 2026: pre-shock official 2.0-4.0% (midpoint {PRE_SHOCK_CPI[2026]}) + model effect {infl:+.2f} pp = "
          f"{PRE_SHOCK_CPI[2026] + infl:.1f}%, against actual January-September 5.4% (PSA) and the July 2026 official 6.0-7.0%. "
          "The model has no money, exchange-rate or wage-price round in the short run (exchange rate fixed), so it is expected "
          "to explain only part of the rise in prices. Jobs: unemployment 5.3% in August 2026 against 3.9% a year earlier (PSA LFS).")
    rep.h("3. The combined shocks against the no-shock path")
    rep.table(tot, floatfmt=",.3f")
    rep.h("4. Each shock's share (Shapley; public capital low; the shares add up exactly to the total)")
    rep.table(pd.DataFrame(shap_rows).set_index("measure"), floatfmt=",.3f")
    rep.h("4b. Each shock alone (standalone runs, public capital low): the like-for-like figures for single-shock benchmarks")
    rep.p("A Shapley share includes the shock's interaction with the others; a standalone run does not. Outside estimates of one "
          "shock (the World Bank's and PIDS's oil-shock poverty counts) compare with this table, not with the shares above.")
    rep.table(singles[["GDP gap 2026 (%)", "GDP gap 2027 (%)", "cumulative GDP loss 2025-2030 (₱ bn)", "consumer prices 2026 (%)",
                       "new poor 2026 (M, own baskets)", "new poor 2027 (M, own baskets)"]], floatfmt=",.3f")
    rep.h("5. Year by year: real GDP gap against the no-shock path (%)")
    rep.table(pd.DataFrame(years).loc[list(YEARS)], floatfmt=",.3f")
    rep.h("6. Sensitivity of the combined result (public capital low)")
    keep = ["GDP gap 2026 (%)", "GDP gap 2027 (%)", "GDP gap 2030 (%)", "cumulative GDP loss 2025-2030 (% of 2025 GDP)",
            "consumer prices 2026 (%)", "new poor 2026 (M, own baskets)", "new poor 2027 (M, own baskets)"]
    sdf = pd.DataFrame({"central": {k: tot.loc[k, "low"] for k in keep}, **{k: {m: v[m] for m in keep} for k, v in sens.items()}}).T
    rep.table(sdf, floatfmt=",.3f")
    rep.h("7. Response measures, each against the shocks-only path")
    rep.table(pd.DataFrame(pol_rows).set_index(["public capital", "measure"]), floatfmt=",.3f")
    rep.p("Cost: ₱ bn as appropriated (2026 or 2027 pesos) and in 2025-peso equivalents (the same share of GDP), the basis of 'output "
          "recovered per peso'. A realigns money already released (no new appropriation). FY 2026 money stays available to end-2027 (RA 12314 "
          "Sec. 77) and aid agencies commit 86-96% of it by December (DBM), so A is shown as a range: upper bound, all of it extra in 2026; "
          f"lower bound, only ₱{A_LOW_EXTRA:.1f} bn extra (the part 2025's pattern says would stay uncommitted), at 4Ps targeting; the gain "
          "from re-targeting the rest to 4Ps channels is not counted (no incidence data for AICS, TUPAD, MAIFIP). C re-appropriates DPWH's lapsing 2025 money in the FY 2027 GAA (decided 1 Oct 2026). "
          "B is new money. Fiscal: + = a larger deficit; debt-to-GDP from the cumulative deficit and nominal GDP, "
          f"debt {DEBT_SOURCE}. The model has no inflation path: its nominal GDP is real GDP at model prices (with the model's own "
          "price change in the short-run years), so the denominator effect leaves out any rise in the price level; each 1% on the GDP "
          f"deflator would lower the ratio by a further {-allon['debt-to-GDP: fall per 1% on the GDP deflator (pp; D8)']:.2f} point "
          "(engine review D8, 17 Oct 2026; the opt-in deflator_dev input of measures() applies a given deviation; 21 Oct 2026).")
    rep.h("8. What is still an assumption (not data, not a published forecast)")
    for a in ("Public works in 2027: the 2027 budget (NEP) x DPWH's latest commitment rate; FY2026 money carried into 2027 assumes 2026 H2 "
              "commits at 2025's H2 pace; construction moves with DPWH commitments relative to 2024 (backtest 2025: 4% high). H2 2026 "
              "public construction is a forecast (the year-on-year rate of H1).",
              "Prices: in the short-run years the model's prices fall with demand (public works lower 2026 consumer prices by 2.3%, "
              "against about 0.3-0.8 points below forecast in the data, preshock/inflation_var.py). Firms in practice keep their margins, "
              "so the price relief is overstated and the poverty effect of the public-works shock is, if anything, understated "
              "(16 Oct: caveat only).",
              "The peso is held at its pre-shock path in 2025-2027 (16 Oct): in the model a weaker peso is expansionary and passes "
              "fully into prices, which the data do not show; sensitivity in scenarios/peso_sensitivity.py.",
              "Fuel products move with crude from 2028 (margins back to pre-conflict); LPG and other products move with crude.",
              "World rice and urea after the latest month: no change (no official forecast exists).",
              "El Nino index for the 2027 dry season read from a chart (IRI no longer publishes the numbers).",
              "The share of a change in public construction that becomes usable capital (0.77, IMF PIMA) and the output elasticity of "
              "public capital (0.083 low, 0.122 high; Bom and Ligthart 2014).",
              f"Short-run closure in 2025-2027 (all skill levels can lose work; 15 Oct) with a wage curve, beta {BETA['central']:.2f} "
              f"(range {BETA['smaller job loss']:.2f}-{BETA['larger job loss']:.2f}), calibrated so the model's 2026 job loss equals "
              "Okun's elasticity x the model's own effect on 2026 growth (17 Oct; persons only: the LFS hours series is not on file). "
              f"The 16 Oct calibration to the whole observed LFS fall (beta {BETA['observed shortfall']:.2f}) is the upper bound. The "
              "Okun elasticity (0.71, all quarters 2006-2026) is identified by the 2020-21 quarters: without them it is 0.15 "
              f"(sensitivity row, beta {BETA['no-COVID']:.2f}). Half the job gap is left each later year (gap_persistence 0.5: no source yet).",
              "Aid reaches households as 4Ps does (PIDS DP 2024-27, Table 13: 66.6% in the bottom 30%); A's lower bound assumes aid agencies "
              "other than DOH and DOLE behave as DSWD did in 2025, and leaves out the unmeasured gain from re-targeting.",
              "Geopolitics and domestic politics at zero for output: our local projections (preshock/geopolitics_panel_lp.py, "
              "domestic_politics_lp.py) and BSP DP 2025-19 find no significant effect on GDP; both weaken the peso somewhat.",
              "Typhoons not entered: neither 2025 nor 2026 to mid-September is above a normal year (preshock/typhoons_normal_year.py).",
              f"Debt stock: {DEBT_SOURCE}."):
        rep.p(f"- {a}")
    rep.save()
    stem = paths.output_dir() / f"combined_revised_{pd.Timestamp.today():%Y%m%d}{__import__('_common').out_tag()}"   # 0.3.10: SAM tag
    tot.to_csv(f"{stem}_summary.csv")
    pd.DataFrame(shap_rows).set_index("measure").to_csv(f"{stem}_shapley.csv")
    singles.to_csv(f"{stem}_single_shocks.csv")
    pd.DataFrame(years).to_csv(f"{stem}_gdp_gap_by_year.csv")
    pd.DataFrame(pol_rows).to_csv(f"{stem}_measures.csv", index=False)
    sdf.to_csv(f"{stem}_sensitivity.csv")
    val.to_csv(f"{stem}_validation.csv")
    pd.set_option("display.width", 250)
    print(tot.round(3).to_string()); print(val.round(2).to_string()); print(pd.DataFrame(shap_rows).set_index("measure").round(3).to_string())
    print(sdf.round(3).to_string()); print(pd.DataFrame(pol_rows).set_index(["public capital", "measure"]).round(3).to_string())


if __name__ == "__main__":
    main()
