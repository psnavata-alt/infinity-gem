"""Recursive-dynamic CGE: the static model solved year by year, linked by capital accumulation.

How it works
------------
Year 0 is the SAM year (2023). Each later year t:
  1. Factor supplies are updated:  labour grows at g_L (by type); land is fixed;
     capital:  K[t] = (1 - dep) * K[t-1] + kappa * I[t-1]
     where I is real investment in the previous year and kappa converts investment (pesos at
     benchmark prices) into capital-income units. kappa is calibrated so that, in the benchmark,
     capital grows at `g_K0` (net of depreciation).
  2. Exogenous demand and foreign flows grow with the baseline GDP path: government consumption,
     the investment level, real transfers, foreign savings, remittances and factor income from abroad.
  3. Baseline only: total factor productivity (TFP, uniform across activities) is solved so that
     real GDP grows at the target rate for that year. Scenarios keep the baseline TFP path.
  4. The static model is solved; its investment feeds next year's capital stock.

Hybrid closure (0.3, opt-in: DynamicCGE(hybrid=True))
  The baseline is unchanged (long-run closure every year). In a scenario, every year that carries a shock is
  solved with the SHORT-RUN model (Keynesian closure: real wages of low- and medium-skill labour fixed, so their
  employment follows demand; capital fixed by activity; exchange rate fixed), anchored to that year's baseline
  equilibrium (same capital allocation, real wages, exchange rate and saving rates), so a zero shock reproduces
  the baseline exactly (check Y2). The employment gap it opens closes gradually afterwards: in later years the
  long-run closure is solved with labour supply reduced by the remaining gap, which shrinks by the factor
  `gap_persistence` each year (default 0.5: half the gap is left after one year, an eighth after three).
  One run therefore shows both the first-year demand loss and its persistence.

Short-run consumption rule (0.3.13, 22 Oct 2026, opt-in: DynamicCGE(sr_consumption={"htm": lam});
a design note (not included), sections 3b, 6 and 7)
  Without it a short-run year keeps the baseline year's saving rates (the Keynesian closure takes the saving-rate adjustment
  MPSADJ as given, and _short_run_spec sets the baseline's), so household spending moves one-for-one with disposable income
  within the year: the channel the design note found to over-contract against PSA's household consumption. With the rule,
  total household spending in each short-run year is
      sum_h EH_h = lam x sum_h (1 - s_h) DY_h  +  (1 - lam) x sum_h EHb_h x CPI / CPIb,
  s_h the baseline year's saving rates (mps x (1 + MPSADJ_b), as the model clips them), DY disposable income, EHb and CPIb
  the baseline year's spending and consumer price index. A share lam of spending follows current income at the baseline
  saving rates (hand-to-mouth households: Campbell and Mankiw 1989; Gali, Lopez-Salido and Valles 2007, JEEA 5(1)); the rest
  keeps its baseline REAL value through the year (households that smooth). The rule is met by the year's MPSADJ, one factor
  for every household (so most of the dissaving falls on the top quintiles, which do most of the saving), solved jointly with
  the wage curve's unknowns as one root (_sr_fixed_point; each evaluation a full solve of the short-run model) and re-solved
  after any change of regime of the employment cap, so it holds in the year's final solution. Long-run years are unchanged.
  lam: the project's DSGE hand-to-mouth share, 0.62 central (pooled ratio2 posterior; 0.48-0.85 across the models estimated;
  research/dsge/README.md, 21 Oct 2026); the data check is PSA's household consumption. lam = 1 is the engine without the
  rule to the root's tolerance (about 1e-10); None (default) = as before, results unchanged. Refused: lam outside [0, 1];
  hybrid=False (no short-run years: in the long-run closures the saving rate is not free, it clears savings and investment or
  is held at the baseline's); a scenario 'mpsadj' in a short-run year (the rule sets it). A household-specific lam would
  need MPSADJ by household in cge.py (the design note's later refinement). Prototype: the 'smooth' hook of
  a development script (not in this repository), whose numbers this reproduces. Check CS1.

Public capital (0.3, opt-in: DynamicCGE(public_capital={...}))
  Lost roads and bridges lower the productivity of every industry, not only the capital stock. In a scenario,
  the change in construction investment relative to the baseline is treated as public investment (true for the
  infrastructure scenarios: the shock is to public construction, and the closures fix other investment). It
  changes the public capital stock:   dKG[t+1] = (1 - delta_g) dKG[t] + e * dIG[t]
  and productivity in all activities by the factor  (1 + dKG[t] / KG_base[t]) ** phi,  with
  KG_base[t] = kg_gdp * baseline real GDP[t] (public capital assumed to keep its share of GDP on the baseline).
  Parameters (each needs a source opened before use):
    phi       output elasticity of public capital. Bom and Ligthart (2014, Journal of Economic Surveys 28(5),
              889-916), meta-analysis of 578 estimates: 0.083 short run, 0.122 long run (central government);
              average 0.106. Run as a range. Mostly OECD estimates. One aggregate phi applies to every industry (a road not
              built affects agriculture and finance alike): a stated simplification (review D6, 17 Oct 2026); a sector-specific
              phi is a research item.
    kg_gdp    public capital stock / GDP in the base year (e.g. IMF Investment and Capital Stock Dataset, general
              government, Philippines). NO DEFAULT: must be supplied from a source.
    delta_g   public capital depreciation; default 0.0352 (IMF ICSD 2021 Manual, Table 1: middle-income, 2016;
              a reference copy (not distributed)).
    e         share of public investment that becomes usable capital; default 0.77 (IMF Country Report 19/137,
              Philippines PIMA: efficiency gap about 23%, "based on perceived quality").
  With phi = 0, or no shock, results equal the model without public capital (check Y3).
  general_stock      (0.3.7, 15 Oct 2026 night; default True = the channel above, unchanged.) False: a change in public
                     construction investment changes ONLY public capital (dKG, with phi), not the general rent-earning
                     capital stock K. With True, each peso of public construction is counted twice (as ordinary capital
                     earning a market return AND as public capital whose phi is already the TOTAL output effect in the
                     literature: Bom and Ligthart 2014). Found by the audit of the combined run (an audit note of 15 Oct 2026 (not included)): with phi = 0, 61% of
                     the efficiency-gap effect remained. IMF DIG/DIGNAR (Buffie et al. 2012) and MAMS keep public capital
                     separate from private capital. Check PK1.
  Efficiency by year and leakage (0.3.6; opt-in keys of the same dict; check CR1). The IMF's DIG
  and DIGNAR models (Buffie et al. 2012) let only a share of each peso of public investment become usable capital; a
  corruption episode lowers that share. e above applies only to CHANGES in public investment. Two more keys:
    e_path           {year: e_t}: the share that becomes usable capital in that year, applied to ALL public investment
                     of the year (the baseline's own and any change). Years not listed use e. Then
                       dKG[t+1] = (1 - delta_g) dKG[t] + e_t * (dIG[t] + L[t]) + (e_t - e) * s * IGc_base[t]
                     with IGc_base the baseline's construction investment and s the government's share of it.
    leakage          {year: l_t}: a share l_t of the government's construction spending of the year is diverted as
                     income instead of buying construction: L[t] = l_t * s * IGc_base[t] (₱ bn, base prices) is taken
                     off construction investment (qinv_scale) and paid as a real transfer (trg_h_add) to the household
                     groups in leak_to ({household: share}, shares summing to 1). The disbursement is unchanged; only
                     its use moves, so L[t] is added back in the capital equation: the usable capital per peso disbursed
                     stays e_t (leakage is PART of the efficiency gap, not on top of it). Use l_t <= 1 - e_t.
    ig_public_share  s, government share of construction investment; NO DEFAULT (e.g. PSA OpenSTAT 0542B5BCNQ1,
                     general government / total construction GFCF). Needed with e_path or leakage.
                     leak_to may also name 'saved' (kept and saved by the few who took it: CGE sav_add) and 'abroad'
                     (moved out of the country: CGE grow_out_add). For the 2025 flood-control case the diverted money went to a small group of recipients (the 2025-2026 investigations of flood-control contracts; AMLC freezes), so
                     'saved' and 'abroad' are the two bounds; household quintiles would spread it to millions of families.
    waste_lost       True: the unusable share of public construction spending (1 - e_t) does not add to the GENERAL
                     capital stock either (it adds nothing to public capital anyway). National accounts record public
                     investment at cost, so wasted spending counts as capital there (Pritchett 2000, J. Econ. Growth 5:
                     "CUDIE is not capital"; Gupta, Kangur, Papageorgiou and Wane 2014, World Development 57,
                     efficiency-adjusted public capital). Measured relative to the baseline, which keeps the data's own
                     capital: K[t+1] adds investment less (1 - e_t) D[t] - L[t] - (1 - e) s IGc_base[t], D[t] the year's
                     government construction disbursement. With e_t = e and no change in disbursement, nothing changes.
    absorptive       phi_A >= 0 (default 0 = off): cost overruns when public investment rises faster than usual, as in
                     the IMF's DIG model (Buffie et al. 2012, IMF WP 12/144, p. 15: new investment multiplied by
                     H = 1 + phi_A (I/K - (g + delta)); base case 0, "tight" 5, about 25% overruns on new projects).
                     Here, for spending ABOVE the baseline: the extra spending dIG buys only dIG / (1 + phi_A dIG/KG_base)
                     of construction-value capital; the rest is overrun (no capital; also lost from the general stock with
                     waste_lost). Cuts are not affected. Philippine context: government construction was 5.9-6.1% of GDP
                     in 2023-24 (PSA), near the about 7% at which road unit costs start rising in low-efficiency
                     countries (Gurara, Kpodar, Presbitero and Tessema 2021, World Development 145).
  With every e_t = e and no leakage, results are those of the channel above (check CR1).

Capital by industry ("putty-clay", 0.3, opt-in: DynamicCGE(capital_allocation="putty-clay"))
  Installed capital stays in its industry (each year is solved with capital fixed by activity, rental rates differing
  by activity); only new investment is mobile. New capital is shared out as in IFPRI's recursive dynamic model
  (Thurlow 2004, TIPS WP 1-2004, eqs P-U, pp. 53-54; Diao and Thurlow, eqs 22' and 23):
      share_a = (K_a / sum K) * (omega * (R_a / AR - 1) + 1),   AR = sum(R_a K_a) / sum K
      K_a[t+1] = (1 - d) K_a[t] + share_a * kappa * I[t]
  The shares sum to one by construction; a negative share (an industry with a very low return) is set to zero and the
  rest rescaled. omega = 3.0 is IFPRI's own setting (1dmodel.gms, beta1 = beta2 = 3.00). With omega = 0 new capital
  follows the existing capital shares. Tested 2 Oct 2026: for omega 0-5, higher omega steadily narrows the differences in
  rental rates; for omega 10 or more the linear rule overshoots (many industries get no new capital in some years and
  rental rates oscillate), so use 1-5 for sensitivity.

Documented baseline (0.3, opt-in: DynamicCGE(**documented_baseline())): growth path from the 193rd DBCC statement
  (8 July 2026; midpoints: 2026 4.0%, 2027-2030 5.5%; PSA actuals 2024-2025); depreciation 5.02% (Penn World Table 11.0
  capital detail, Philippines 2023: capital consumption / previous-year net stock); capital stock 1.96 x GDP for
  rent-earning capital (PWT net capital stock 2.42 x GDP less public capital, about 19% in IMF ICSD 2019), which sets
  kappa, the capital added per peso of investment. Labour growth by skill from PSA (below; 2 Oct 2026); the 1.5%
  placeholder is kept with documented_baseline(labour="placeholder").
  Sources and grades: docs/guides/08_PARAMETERS_AND_SOURCES.md.

Labour growth by skill (0.3, opt-in: labour_growth=psa_labour_growth(); in documented_baseline() since 2 Oct 2026)
  labour_growth may be one rate for all labour types (as before) or {year: {labour type: rate}}. psa_labour_growth()
  builds it from PSA data (data/raw/lfs, data/raw/population; OpenSTAT tables 0141B3FEMP7 and 0021A3BPOP1):
    2024, 2025  LFS annual employed persons by highest grade completed, mapped to the SAM's labour types:
                low (flab-n) = no grade completed + elementary undergraduate; medium (flab-p) = elementary graduate
                + junior high undergraduate; high (flab-s) = junior high completed and above (senior high,
                post-secondary, college). The SAM defines high as "finished secondary and/or tertiary schooling".
    2026        LFS January-July 2026 against January-July 2025, same mapping (the latest months published).
    2027-2030   total employment grows with PSA's projected population aged 15+ (2020 CPH-based; constant
                employment rate); the skill shares continue their 2023-2025 average annual change ("trend", default)
                or stay at their 2025 values ("constant", sensitivity).
  In the full-employment closure, labour supply = employment, so observed employment is the right series.

Industry baseline (0.3, opt-in: industry_targets=psa_industry_growth())
  Instead of one productivity rate for all activities, each of PSA's 16 industries (GVA by industry at constant 2018
  prices, OpenSTAT 0052B5BPRA1) grows as it did in 2024 and 2025. The instrument depends on what drives the
  industry in the model:
    construction            real investment demand for construction (the 2025 slump was the public investment cut);
    public administration   real government consumption of public administration;
    trade, financial        input intensity: that service used per unit of output by every industry (and, for trade,
                            per unit of trade margin). In the SAM, trade has no household demand (71% intermediate use,
                            29% margins) and financial services 69% intermediate and 30% government use;
    the other 12 industries productivity (TFP) of their SAM activities (same factor within an industry).
  Construction, public administration, trade and finance are pinned by demand in this closure, so productivity
  cannot move them (tried 2 Oct 2026: trade then needed +28% TFP in 2025). Later years (no industry data) keep the 2025 differences and grow together (one TFP rate,
  solved to hit the growth path); construction investment and public administration keep their 2025 level
  relative to the economy. With this option the baseline CONTAINS the actual 2025 construction slump: use it for
  shocks from 2026 on (e.g. the 2027 catch-up). Do not add a 2025 freeze on top of it (that would count it twice).
  Real GDP is not targeted in those years; it follows from the industries (reported in the baseline table).

A scenario = the baseline exogenous path + shocks in chosen years. Because a shock that lowers
investment lowers the capital stock, its effect on GDP persists after the shock ends; this is the
effect a static model cannot show.

Every parameter below is an ASSUMPTION to be reviewed and documented by the team (see
docs/guides/02_CGE_GUIDE.md, "Calibrating the dynamic baseline").

Usage
-----
>>> from infinity_gem.dynamic import DynamicCGE
>>> d = DynamicCGE()                                   # default assumptions
>>> base = d.baseline()                                # calibrates TFP to the growth path
>>> sim = d.scenario({2025: {"qinv_scale": {"ccons": 0.85}}, 2026: {"qinv_scale": {"ccons": 0.85}}})
>>> d.compare(base, sim)
"""
from __future__ import annotations

import copy
import numbers
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.optimize import brentq

from .cge import CGE

# Real GDP growth path (%). 2024-2025: PSA actual. 2026 onward: ASSUMPTIONS for illustration
# (2026 near the S&P 2.9% and ADB 3.3% forecasts of September 2026; 2027+ a
# recovery path). Replace with your own or DBCC assumptions before use.
DEFAULT_GROWTH = {2024: 5.7, 2025: 4.4, 2026: 3.0, 2027: 5.0, 2028: 5.5, 2029: 5.5, 2030: 5.5}
# 193rd DBCC statement (8 July 2026): 2026 3.5-4.5%, 2027-2030 5.0-6.0% (midpoints); 2024-2025 PSA actual
DBCC_GROWTH = {2024: 5.7, 2025: 4.4, 2026: 4.0, 2027: 5.5, 2028: 5.5, 2029: 5.5, 2030: 5.5}
DEFAULT_ASSUMPTIONS = dict(
    base_year=2023,
    labour_growth=0.015,          # per year, all labour types (replace with LFS-based projections)
    depreciation=0.05,            # capital depreciation rate
    capital_growth_base=0.05,     # net capital growth in the benchmark year (calibrates kappa)
    closure="investment",         # long-run: full employment, investment-driven
    unemployed=(),
    capital="mobile",
    hybrid=False,                 # 0.3: short-run closure in shock years, gap closing afterwards (opt-in)
    gap_persistence=0.5,          # share of the employment gap left the next year (ASSUMPTION; 0 = closes at once)
    short_run_unemployed=("flab-n", "flab-p"),
    public_capital=None,          # 0.3: dict(phi=..., kg_gdp=..., delta_g=0.0352, e=0.77); None = off
    capital_allocation="mobile",  # 0.3: "putty-clay" = capital fixed by industry, new investment chases returns
    omega=3.0,                    # investment mobility (IFPRI 1dmodel.gms beta = 3.00); used with putty-clay
    vintage_e=0.7,                # 0.3.12: capital_allocation="vintage", release elasticity of old capital
    vintage_e_sr=0.0,             # the same in the hybrid closure's short-run years: 0 = installed capital stays put within the
                                  # year (the usual short-run assumption; only the year's new capital is allocated). With the
                                  # long-run value instead, a 20% construction cut in 2026 cost 0.5% of GDP against 2.8% under
                                  # putty-clay, because released capital re-employed at once (20 Oct 2026 test)
                                  # (MANAGE-WB invElas, bridge-file default 0.7); old capital stays where it was used, new
                                  # capital (last year's investment) is allocated within the year by one rental rate
    capital_output=None,          # 0.3: rent-earning capital stock / GDP; if given, sets kappa (else capital_growth_base)
    industry_targets=None,        # 0.3: {year: {PSA industry: real GVA growth %}}; None = one TFP rate
    les=None,                     # 0.3: LES household demand (infinity_gem.demand.les_briones2023()); None = Cobb-Douglas
    elasticities=None,            # 0.3.1: CGE elasticities (infinity_gem.elasticities.elasticity_set); None = 0.2 defaults
    margins="composite",          # 0.3.1: CGE trade margins ("split" = IFPRI-style); "composite" = 0.2
    wage="real",                  # 0.3.4: short-run wage rule, "real" (CPI-indexed, 0.2) or "nominal" (sticky pesos)
    land="mobile",                # 0.3.7: "fixed" = in the hybrid's short-run years each crop keeps its baseline
                                  # land of that year, and a scenario's 'lscale' {activity: factor} cuts it (e.g. drought)
    employment_cap=True,          # 0.3.7: in the hybrid's short-run years a labour type whose demand would exceed
                                  # its supply is fully employed and its wage rises instead (complementarity); False = old rule
    wage_curve=None,              # 0.3.7 (16 Oct, ~1 AM): beta of a wage curve in the hybrid's short-run years; None = fixed
                                  # wage (as before). Each fixed-wage labour type's wage anchor becomes
                                  # wbar x min(1, EMP/EMP_baseline) ** beta, solved to a fixed point: when work falls, pay gives
                                  # a little, so not all of the adjustment lands on jobs (Blanchflower and Oswald 1994; at 4%
                                  # unemployment, beta 2.4 = their -0.1 elasticity of pay to the unemployment rate). Set beta
                                  # so the model reproduces PSA's output-employment relation (preshock/okun.py,
                                  # scenarios/calibrate_wage_curve.py). Rises above the baseline are left to employment_cap. Check WC1.
    short_run_years=None,         # 0.3.7 (15 Oct night): hybrid short-run years; None = every year that carries a shock (as
                                  # before). A tuple limits the short run to those years, so a lasting shock (e.g. oil prices
                                  # still above the pre-conflict assumption in 2028-2030) is solved in the long-run closure
                                  # in later years instead of keeping wages fixed for as long as the shock lasts. Check SR1.
    investment_closure="baseline",  # 0.3.8 (17 Oct, review D1): "baseline" = real investment on its baseline path in
                                  # every year (as before); "savings" = in a scenario's long-run years household saving rates
                                  # stay at the baseline's and real investment follows savings (a savings-driven closure), so a
                                  # shock that lowers income lowers investment and next year's capital. Check IC1.
    sr_fx="fixed",                # 0.3.8 (review D1): in the hybrid's short-run years "fixed" = the peso at its baseline
                                  # level and the current account absorbing changes (as before); "flexible" = foreign savings
                                  # on the baseline path and the peso adjusting (needs wage="nominal"). Check IC1.
    sr_pricing="flex",            # 0.3.8 (review D2): in the hybrid's short-run years "flex" = zero-profit prices (as
                                  # before); "sticky" = prices of non-farm activities rigid downward (cge.py pricing="sticky"),
                                  # anchored to the baseline year's prices, with the share sr_stickiness of a cost fall not
                                  # passed on. Check PS1. 0.3.13 (22 Oct 2026): "markup" = structuralist
                                  # markup pricing (cge.py pricing="markup"): the activities in markup_acts price their home sales
                                  # at a markup over unit variable cost, with the markups, the installed technology (labour per
                                  # unit of output), the exporters' reference home sales and the stickiness anchor all taken from
                                  # that year's baseline solution (CGE.markup_at), so a zero shock reproduces the baseline; the
                                  # share sr_stickiness of a fall of the markup price is not passed on (sticky_acts; None = the
                                  # markup activities): markup and stickiness together, option (c) of the design. Check MK1.
    sr_stickiness=0.0,            # 0.3.8: share of a fall in unit cost that sticky-price activities do not pass on;
                                  # 0.3.11 (19 Oct 2026): or {activity: share}, e.g. stickiness.sectoral(...) (check ST1)
    sticky_acts=None,             # 0.3.8: activities with sticky prices; None = all but agriculture, forestry, fishing
                                  # and mining (PSA_INDUSTRIES), whose prices clear their markets (with sr_pricing="markup": None =
                                  # the markup activities)
    markup_acts=None,             # 0.3.13: with sr_pricing="markup", the activities with markup prices; None = all but
                                  # agriculture, forestry and fishing (cge.MARKET_PRICE_ACTS) and pure exporters (amach)
    sr_markup_pass=1.0,           # 0.3.13: with sr_pricing="markup", the CGE shock key 'mk_pass': the share of a change in unit
                                  # variable cost on which the markup is charged (1 = proportional markup, the design note's
                                  # equation; 0 = margin per unit fixed in pesos, the input-output cost push); a share or {activity: share}
    hoarding=0.0,                 # 0.3.11: paid labour hoarding in the hybrid's short-run years: the share of an
                                  # activity's fall in labour demand (below the baseline year's labour) that stays employed and
                                  # paid out of profits (CGE 'hoarding'). 0 = none (default, results unchanged)
    energy_nest=None,             # 0.3.11: CGE 'energy_nest' (value added-energy bundle, fuel substitution) in
                                  # every year, e.g. {"energy": ["cpetr", "celec"], "sigma_ve": 0.5, "sigma_e": 1.5}; None = as before
    sr_energy_nest=None,          # 0.3.11: override for the short-run years (lower elasticities: installed capital is
                                  # less flexible, MANAGE-WB's old vintage); None = energy_nest. Its shares are centred on each
                                  # baseline year's input mix (CGE.energy_shares_at), so an unshocked year reproduces the baseline
    interest=None,                # 0.3.11: with closure="interest" (long-run years), CGE 'interest'
                                  # {'theta': ..., 'eps': ...}: a real interest rate clears savings and investment; None = as before
    monetary=None,                # 0.3.12: a BSP policy rule inside the dynamic model: the keyword arguments of
                                  # monetary_scenario() as a dict, e.g. {"rule": infinity_gem.monetary.rule("pamph"), "theta": 2.0};
                                  # scenario() then solves every path with the rule. None = no rule (default, results unchanged)
    sr_consumption=None,          # 0.3.13 (22 Oct 2026, a design note (not included)): in the
                                  # hybrid's short-run years {"htm": lam}, 0 <= lam <= 1: household spending = lam x (1 - baseline
                                  # saving rates) x disposable income + (1 - lam) x baseline spending x CPI / baseline CPI, met by
                                  # the year's saving-rate adjustment MPSADJ, solved jointly with the wage curve (module notes,
                                  # _sr_fixed_point). None = saving rates at the baseline's (default, results unchanged). Check CS1.
)

# PSA GVA industries (OpenSTAT 0052B5BPRA1) -> activities of the IFPRI 2023 SAM
PSA_INDUSTRIES = {
    "Agriculture, forestry, and fishing": ["amaiz", "arice", "apuls", "aoils", "aroot", "avege", "asugr", "atoba", "acott",
                                           "afrui", "acoff", "aocrp", "acatt", "apoul", "aoliv", "afore", "afish"],
    "Mining and quarrying": ["amine"],
    "Manufacturing": ["afood", "abeve", "atext", "awood", "achem", "apetr", "anmet", "ametl", "amach", "aoman", "amric"],   # apetr, amric: split SAMs only
    "Electricity, steam, water and waste management": ["aelec", "awatr"],
    "Construction": ["acons"],
    "Wholesale and retail trade; repair of motor vehicles and motorcycles": ["atrad"],
    "Transportation and storage": ["atran"],
    "Accommodation and food service activities": ["ahotl"],
    "Information and communication": ["acomm"],
    "Financial and insurance activities": ["afsrv"],
    "Real estate and ownership of dwellings": ["areal"],
    "Professional and business services": ["absrv"],
    "Public administration and defense; compulsory social activities": ["apadm"],
    "Education": ["aeduc"],
    "Human health and social work activities": ["aheal"],
    "Other services": ["aosrv"],
}
# industries whose output is pinned by demand in the model, and the lever used for them: (instrument, commodity)
#   qinv: real investment demand; qg: real government consumption; use: input intensity of that service for all
#   industries (and per unit of trade margin). Trade has no household demand in the SAM (71% intermediate use,
#   29% margins); financial services 69% intermediate, 30% government. Productivity cannot move them.
INDUSTRY_DEMAND_INSTRUMENT = {"Construction": ("qinv", "ccons"),
                              "Public administration and defense; compulsory social activities": ("qg", "cpadm"),
                              "Wholesale and retail trade; repair of motor vehicles and motorcycles": ("use", "ctrad"),
                              "Financial and insurance activities": ("use", "cfsrv")}
LABOUR_EDUCATION = {"flab-n": ["No grade completed", "Elementary Undergraduate"],
                    "flab-p": ["Elementary Graduate", "Junior High Undergraduate"],
                    "flab-s": ["Junior High Completed", "Senior High School", "Post Secondary", "College"]}


def psa_industry_growth(years=(2024, 2025)) -> dict:
    """{year: {PSA industry: real GVA growth %}} from PSA OpenSTAT 0052B5BPRA1 (constant 2018 prices)."""
    from . import paths
    df = pd.read_csv(paths.DATA_RAW / "macro" / "PSA_OpenSTAT_GVA_by_industry_annual_2000-2025.csv", comment="#")
    df = df[(df["valuation"] == "At Constant 2018 Prices") & df["industry"].isin(list(PSA_INDUSTRIES))]
    v = df.pivot(index="year", columns="industry", values="value_million_php")
    return {y: {k: float((v.loc[y, k] / v.loc[y - 1, k] - 1) * 100) for k in PSA_INDUSTRIES} for y in years}


def psa_labour_growth(shares="trend", last_year=2030, y2026="observed") -> dict:
    """{year: {labour type: growth rate}} from PSA LFS (2024-2026) and population projections (2027 on).
    y2026: "observed" (default, as before: LFS January-July 2026 against the same months of 2025) or "trend" (0.3.9, review
    D3, 17 Oct 2026: 2026 follows the 2027-2030 projection rule, so the no-shock path does not contain the shock year's own
    employment; check LG1)."""
    from . import paths
    lfs = pd.read_csv(paths.DATA_RAW / "lfs" / "PSA_OpenSTAT_LFS_employed_by_highest_grade_2023-2026.csv", comment="#")
    by_type = lambda d: np.array([d[d["highest_grade_completed"].isin(v)]["employed_thousands"].sum()
                                  for v in LABOUR_EDUCATION.values()])
    ann = {y: by_type(lfs[(lfs["year"] == y) & (lfs["month"] == "Annual")]) for y in (2023, 2024, 2025)}
    months = ["January", "February", "March", "April", "May", "June", "July"]
    jj = {y: by_type(lfs[(lfs["year"] == y) & lfs["month"].isin(months)]) for y in (2025, 2026)}
    keys = list(LABOUR_EDUCATION)
    out = {y: dict(zip(keys, ann[y] / ann[y - 1] - 1)) for y in (2024, 2025)}
    out[2026] = dict(zip(keys, jj[2026] / jj[2025] - 1))
    if y2026 not in ("observed", "trend"):
        raise ValueError("y2026 must be 'observed' or 'trend'")
    pop = pd.read_csv(paths.DATA_RAW / "population" / "PSA_OpenSTAT_population_projections_2020CPH_2020-2030.csv", comment="#")
    p15 = pop[(pop["sex"] == "Both Sexes") & ~pop["age_group"].isin(["All Ages", "0-4", "5-9", "10-14"])]
    p15 = p15.groupby("year")["population_thousands"].sum()
    dsh = (ann[2025] / ann[2025].sum() - ann[2023] / ann[2023].sum()) / 2 if shares == "trend" else np.zeros(3)
    if shares not in ("trend", "constant"):
        raise ValueError("shares must be 'trend' or 'constant'")
    if y2026 == "trend":                                        # 2026 by the projection rule, from the 2025 level
        level, sh, first = ann[2025].astype(float), ann[2025] / ann[2025].sum(), 2026
    else:
        level = ann[2025] * (1 + np.array(list(out[2026].values())))      # 2026 level by type
        sh, first = level / level.sum(), 2027
    for y in range(first, last_year + 1):
        new_sh = np.clip(sh + dsh, 0.01, None)
        new_sh = new_sh / new_sh.sum()
        new_level = level.sum() * float(p15[y] / p15[y - 1]) * new_sh
        out[y] = dict(zip(keys, new_level / level - 1))
        level, sh = new_level, new_sh
    return {y: {k: float(v) for k, v in d.items()} for y, d in out.items()}


def documented_baseline(labour="psa", labour_2026="observed") -> dict:
    """The sourced baseline assumptions (0.3): DBCC growth path, PWT depreciation and capital stock, and (since
    2 Oct 2026) PSA labour growth by skill. labour="placeholder" keeps the 1.5% for all types (results of 2 Oct, 1:45 PM)."""
    d = dict(growth=dict(DBCC_GROWTH), depreciation=0.0502, capital_output=1.96)
    if labour == "psa":
        d["labour_growth"] = psa_labour_growth(y2026=labour_2026)       # 0.3.9: labour_2026="trend" (review D3)
    elif labour != "placeholder":
        raise ValueError("labour must be 'psa' or 'placeholder'")
    return d
PUBLIC_CAPITAL_DEFAULTS = dict(delta_g=0.0352, e=0.77)


_ADDITIVE = ("trg_h_add", "sav_add", "grow_out_add", "mpsadj")      # shocks that are amounts (0 = none), not factors


def _scale_shock(extra: dict, lam: float) -> dict:
    """A share lam of a year's shock (0.3.7): factors move lam of the way from 1, amounts lam of
    the way from 0. lam = 1 returns the shock unchanged."""
    out = {}
    for k, v in extra.items():
        f = (lambda a: lam * a) if k in _ADDITIVE else (lambda a: 1 + lam * (a - 1))
        out[k] = {i: f(a) for i, a in v.items()} if isinstance(v, dict) else f(v)
    return out


class _SolveFailed(Exception):
    """A trial solve inside the TFP search did not converge."""


def _robust_root(f, x0, xtol=1e-10):
    """Root of f near x0: widen a bracket outward (1%, 2%, 4%, ... up to 40%) using only points where the model
    solves, then brentq inside it. Used when the wide default bracket hits points where the model cannot solve."""
    f0 = f(x0)
    if f0 == 0:
        return x0
    for step in (0.01, 0.02, 0.04, 0.08, 0.16, 0.32, 0.4):
        for x1 in (x0 * (1 + step), x0 * (1 - step)):
            try:
                f1 = f(x1)
            except _SolveFailed:
                continue
            if np.sign(f1) != np.sign(f0):
                lo, hi = sorted((x0, x1))
                return brentq(f, lo, hi, xtol=xtol)
    raise RuntimeError("TFP search: no bracket found within +-40% of last year's value")


@dataclass
class Path:
    years: list
    solutions: dict
    tfp: dict
    capital: dict
    table: pd.DataFrame = field(default=None)
    demand: dict = field(default=None)            # industry baseline levers: {year: {"qinv:ccons": f, ...}}
    monetary: pd.DataFrame = field(default=None)  # 0.3.12: the BSP rule's path (monetary_scenario); None = rule off


class DynamicCGE:
    def __init__(self, growth=None, sam=None, **assumptions):
        if growth is None:                       # 0.3.9 (review D7): the placeholder path is for illustration only
            import warnings
            warnings.warn("DynamicCGE(): placeholder growth path DEFAULT_GROWTH (2026 at 3.0%); for sourced results use "
                          "settings.dynamic_kwargs(...) or documented_baseline() (DBCC path)", stacklevel=2)
        a = dict(DEFAULT_ASSUMPTIONS)
        a.update(assumptions)
        self.a = a
        self.growth = dict(DEFAULT_GROWTH if growth is None else growth)
        self.putty = a["capital_allocation"] == "putty-clay"
        self.vintage = a["capital_allocation"] == "vintage"      # 0.3.12
        self.by_act = self.putty or self.vintage                 # capital kept by activity between years
        if a["capital_allocation"] not in ("mobile", "putty-clay", "vintage"):
            raise ValueError("capital_allocation must be 'mobile', 'putty-clay' or 'vintage'")
        self._check_sr_consumption(a)                # 0.3.13: checked here, before any model is built
        kw = dict(closure=a["closure"], unemployed=a["unemployed"],
                  capital="fixed" if self.putty else ("vintage" if self.vintage else a["capital"]),
                  les=a["les"], elasticities=a["elasticities"], margins=a["margins"], wage=a["wage"])
        if a["energy_nest"] is not None:          # 0.3.11; not passed when None, so the call is as before
            kw["energy_nest"] = a["energy_nest"]
        if a["interest"] is not None:             # 0.3.11; not passed when None
            kw["interest"] = a["interest"]
        if self.vintage:
            kw["vintage"] = {"e": float(a["vintage_e"])}
        self.m = CGE(sam, **kw) if sam is not None else CGE.from_sam(**kw)
        if a["public_capital"] is not None:
            pc = dict(PUBLIC_CAPITAL_DEFAULTS, **a["public_capital"])
            missing = [k for k in ("phi", "kg_gdp") if k not in pc]
            if missing:
                raise ValueError(f"public_capital needs {missing}: take them from a source (see the module notes)")
            if (pc.get("e_path") or pc.get("leakage")) and "ig_public_share" not in pc:
                raise ValueError("public_capital: e_path and leakage need ig_public_share (government share of "
                                 "construction investment) from a source (see the module notes)")
            if pc.get("leakage"):
                lt = pc.get("leak_to") or {}
                if not lt or abs(sum(lt.values()) - 1) > 1e-9 or any(h not in self.m.H and h not in ("saved", "abroad") for h in lt):
                    raise ValueError("public_capital: leakage needs leak_to = {'saved' | 'abroad' | household group: share}, "
                                     "shares summing to 1")
            self.pc = pc
        if a["investment_closure"] not in ("baseline", "savings"):
            raise ValueError("investment_closure must be 'baseline' or 'savings'")
        if a["monetary"] is not None:                # 0.3.12: checked here so a wrong setting fails before any solve
            mo = a["monetary"]
            if not isinstance(mo, dict) or not (isinstance(mo.get("rule"), dict) or isinstance(mo.get("path"), dict)):
                raise ValueError("monetary must be a dict with 'rule' (rho, phi_pi, phi_x, ...) or 'path' ({year: {'i': ...}}); "
                                 "see DynamicCGE.monetary_scenario and infinity_gem.monetary.rule")
            if isinstance(mo.get("rule"), dict) and any(k not in mo["rule"] for k in ("rho", "phi_pi", "phi_x")):
                raise ValueError("monetary['rule'] needs rho, phi_pi and phi_x (phi_e and freq optional)")
        self.mL = None                               # 0.3.8: savings-driven model for a scenario's long-run years
        if a["investment_closure"] == "savings":
            kwL = dict(kw, closure="savings")
            self.mL = CGE(sam, **kwL) if sam is not None else CGE.from_sam(**kwL)
        if a["hybrid"]:
            sticky = a["sticky_acts"]
            if a["sr_pricing"] == "sticky" and sticky is None:
                flexible = set(PSA_INDUSTRIES["Agriculture, forestry, and fishing"] + PSA_INDUSTRIES["Mining and quarrying"])
                sticky = [x for x in self.m.A if x not in flexible]
            kw_sr = dict(closure="keynesian", unemployed=a["short_run_unemployed"],
                         capital="vintage" if (self.vintage and float(a["vintage_e_sr"]) > 0) else "fixed", les=a["les"],
                         elasticities=a["elasticities"], margins=a["margins"], wage=a["wage"], land=a["land"],
                         fx=a["sr_fx"], pricing=a["sr_pricing"], sticky_acts=sticky if a["sr_pricing"] == "sticky" else None,
                         hoarding=float(a["hoarding"]))
            if a["sr_pricing"] == "markup":       # 0.3.13: not passed otherwise, so the call is as before
                kw_sr.update(sticky_acts=a["sticky_acts"], markup_acts=a["markup_acts"])
            elif a["markup_acts"] is not None:
                raise ValueError("markup_acts needs sr_pricing='markup'")
            en_sr = a["sr_energy_nest"] if a["sr_energy_nest"] is not None else a["energy_nest"]
            if en_sr is not None:                 # 0.3.11
                kw_sr["energy_nest"] = en_sr
            if self.vintage and float(a["vintage_e_sr"]) > 0:   # e_sr = 0: the short-run model is plain fixed capital at the
                kw_sr["vintage"] = {"e": float(a["vintage_e_sr"])}   # anchored old capital (same economics, no spare unknowns)
            self.ms = CGE(sam, **kw_sr) if sam is not None else CGE.from_sam(**kw_sr)
            self._sam_sr, self._kw_sr = sam, kw_sr
            self._ms_cache = {tuple(self.ms.unemployed): self.ms}
        m = self.m
        self.kc = m.F.index("fcap")
        self.K0 = m.QFS0[self.kc]
        self.K0a = m.QF0[self.kc].copy()             # capital by activity (capital-income units, base rental 1)
        I0 = m.qinv.sum()
        if a["capital_output"]:
            b0 = m.solve()
            if not b0.ok:                            # 0.3.3 (rigging audit finding 3): never use an unsolved benchmark
                raise RuntimeError(f"Benchmark did not solve ({b0.message}, residual {b0.residual_max:.2e})")
            gdp0 = m.gdp(b0)["nominal_expenditure"]
            self.kappa = self.K0 / (a["capital_output"] * gdp0)   # capital units added per peso of real investment
        else:
            self.kappa = (a["capital_growth_base"] + a["depreciation"]) * self.K0 / I0
        self.years = [a["base_year"]] + sorted(self.growth)
        # labour by type (0.3): one rate (as before) or {year: {labour type: rate}}
        lg = a["labour_growth"]
        self.labs = [f for f in m.F if f.startswith("flab")]
        if isinstance(lg, dict):
            missing = [t for t in self.years[1:] if t not in lg]
            if missing:
                raise ValueError(f"labour_growth has no rates for {missing}")
            self.L_path, idx = {self.years[0]: {f: 1.0 for f in self.labs}}, {f: 1.0 for f in self.labs}
            for t in self.years[1:]:
                idx = {f: idx[f] * (1 + lg[t][f]) for f in self.labs}
                self.L_path[t] = idx
        else:
            self.L_path = None
        # industry baseline (0.3)
        self.ind_targets = a["industry_targets"] or {}
        self.groups = []
        if self.ind_targets:
            for name, acts in PSA_INDUSTRIES.items():
                inst = INDUSTRY_DEMAND_INSTRUMENT.get(name, ("tfp", None))
                self.groups.append((name, inst, np.array([m.A.index(x) for x in acts if x in m.A])))   # apetr: split SAM only

    # ------------------------------------------------------------------ one year
    def _spec(self, t, K, L_index, Y_index, tfp, extra=None, dem=None):
        m = self.m
        if isinstance(L_index, dict):
            qfs = {f: L_index[f] for f in m.F if f.startswith("flab")}
        else:
            qfs = {f: L_index for f in m.F if f.startswith("flab")}
        if self.by_act:
            qfs["fcap"] = 1.0
        else:
            qfs["fcap"] = K / self.K0
        if np.ndim(tfp):                               # productivity by activity (industry baseline)
            tfp = {a: float(tfp[i]) for i, a in enumerate(m.A)}
        spec = {"qfs_scale": qfs, "tfp_scale": tfp, "qg_scale": Y_index, "iadj": Y_index,
                "trg_scale": Y_index, "fsav_scale": Y_index, "remit_scale": Y_index, "frow_in_scale": Y_index}
        items_of = {"qfs_scale": m.F, "tfp_scale": m.A, "qg_scale": m.C, "remit_scale": m.H, "frow_in_scale": m.F}
        for k, v in (extra or {}).items():
            if k in spec and not isinstance(v, dict) and not isinstance(spec[k], dict):
                spec[k] = spec[k] * v                  # scenario factors multiply the baseline level
            elif k in spec and k in items_of:
                # 0.3.1: a scenario dict (by commodity, activity, factor or household) multiplies the
                # baseline path too, instead of replacing it (before, e.g. a TFP shock for one industry wiped the
                # baseline productivity path; no published run used such a shock: they all shock qinv_scale only)
                base = spec[k] if isinstance(spec[k], dict) else {i: float(spec[k]) for i in items_of[k]}
                vv = v if isinstance(v, dict) else {i: float(v) for i in items_of[k]}
                spec[k] = {i: base.get(i, 1.0) * vv.get(i, 1.0) for i in dict.fromkeys(list(base) + list(vv))}
            else:
                spec[k] = v
        for key, f in (dem or {}).items():             # industry baseline levers, times any scenario factor
            inst, com = key.split(":")
            if inst == "qinv":
                q = dict(spec.get("qinv_scale") or {})
                q[com] = q.get(com, 1.0) * f
                spec["qinv_scale"] = q
            elif inst == "qg":
                g = spec["qg_scale"]
                g = dict(g) if isinstance(g, dict) else {c: float(g) for c in m.C}
                g[com] = g.get(com, 1.0) * f
                spec["qg_scale"] = g
            elif inst == "use":
                for k in ("ica_scale", "sm_scale"):
                    u = dict(spec.get(k) or {})
                    u[com] = u.get(com, 1.0) * f
                    spec[k] = u
        if self.by_act:
            spec["kscale"] = {a: float(K[i] / self.K0a[i]) for i, a in enumerate(m.A) if self.K0a[i] > 0}
        if self.vintage:                               # 0.3.12: the year's pool of new capital, share of the benchmark stock
            spec["knew"] = float(self._knew / self.K0)
        return spec

    def _calibrate_industries(self, t, K, L_index, Y_index, extra, x, va_prev, tf_prev, dem_prev):
        """Industry baseline: productivity by industry and the two demand levels so each PSA industry's real value added grows
        as PSA reports for year t."""
        from scipy.optimize import root
        m, target = self.m, self.ind_targets[t]
        prev = np.full(len(m.A), float(tf_prev)) if np.ndim(tf_prev) == 0 else np.asarray(tf_prev, float)

        def unpack(z):
            tfv, dem = prev.copy(), dict(dem_prev)
            for j, (name, (inst, com), idx) in enumerate(self.groups):
                if inst == "tfp":
                    tfv[idx] = prev[idx] * np.exp(z[j])
                else:
                    key = f"{inst}:{com}"
                    dem[key] = dem_prev.get(key, 1.0) * np.exp(z[j])
            return tfv, dem

        state = {"x": x}

        def resid(z):
            tfv, dem = unpack(z)
            s = m.solve(self._spec(t, K, L_index, Y_index, tfv, extra, dem), x_start=state["x"])
            if not s.ok:
                return np.full(len(self.groups), 1e3)
            state["x"] = s.x
            va = s["QVA"]
            return np.array([va[idx].sum() / va_prev[idx].sum() - 1 - target[name] / 100
                             for name, _, idx in self.groups])

        g_all = self.growth[t] / 100
        z0 = np.array([np.log((1 + target[name] / 100) / (1 + g_all)) for name, _, _ in self.groups])
        out = root(resid, z0, method="hybr", options={"xtol": 1e-12})
        if np.abs(out.fun).max() > 1e-7:
            raise RuntimeError(f"Year {t}: industry calibration failed (max gap {np.abs(out.fun).max():.2e})")
        self._calib_x = state["x"]                    # a solution near the calibrated point (restart for the final solve)
        return unpack(out.x)

    def _ms_for(self, unemployed):
        """The short-run model with a given set of labour types on fixed wages, built once and kept."""
        key = tuple(unemployed)
        if key not in self._ms_cache:
            kw = dict(self._kw_sr, unemployed=key)
            if kw.get("fx") == "flexible" and not key:   # 0.3.8: every labour type at full employment leaves no peso
                kw["fx"] = "fixed"                       # wage to anchor prices: the peso goes back to its baseline (numeraire)
            self._ms_cache[key] = CGE(self._sam_sr, **kw) if self._sam_sr is not None else CGE.from_sam(**kw)
        return self._ms_cache[key]

    def _wage_curve(self, sol, model, spec, t, K):
        """0.3.7 (16 Oct 2026): in a short-run year, each fixed-wage labour type's wage anchor is lowered to
        wbar x min(1, EMP/EMP_baseline) ** beta, where EMP is the employment it produces: a fixed point (each evaluation
        a full solve of the short-run model). Returns (solution, model).
        Solved with scipy's hybrid Powell method on x = ln(anchor / baseline anchor), one per fixed-wage labour type."""
        from scipy.optimize import root
        beta = float(self.a["wage_curve"])
        m, b = self.m, self.base.solutions[t]
        idx = float(b["CPI"]) if model.wage == "real" else 1.0
        fs = list(model.unemployed)
        w0 = np.array([float(b["WF"][m.F.index(f)] / idx) for f in fs])
        e0 = np.array([float(b["EMP"][m.F.index(f)]) for f in fs])
        state = {"sol": sol}

        def resid(x):
            self._wbar_override[t] = dict(zip(fs, w0 * np.exp(x)))
            s = model.solve(self._short_run_spec(spec, t, K, model), x_start=state["sol"].x)
            if not s.ok:
                raise RuntimeError(f"Year {t}: wage-curve solve failed ({s.message})")
            state["sol"] = s
            e = np.array([float(s["EMP"][m.F.index(f)]) for f in fs])
            return x - beta * np.log(np.minimum(1.0, e / e0))

        try:
            r = root(resid, np.zeros(len(fs)), method="hybr", options={"xtol": 1e-12})
            res, msg = resid(r.x), r.message     # leave the model at the root's solution
        except RuntimeError as err:
            res, msg = None, str(err)
        if res is None or not np.all(np.abs(res) < 1e-8):   # 0.3.8, 17 Oct: was 1e-9; at beta >= 60 the root's residual reached 2.1e-9
            # 0.3.13 (22 Oct 2026): where the fixed point is the anchor itself (a short-run year with no shock), hybr's relative
            # step test may never stop: the iterates shrink geometrically towards 0 until they underflow to NaN (seen in a markup-
            # pricing run, 2025, no-shock path). Reached only where the code above failed, so every run that converged is unchanged:
            # x = 0 is accepted if it is the fixed point (gap below 1e-10).
            r0 = resid(np.zeros(len(fs)))
            if np.all(np.abs(r0) < 1e-10):
                return state["sol"], model
            gap = np.abs(res).max() if res is not None else float("nan")
            raise RuntimeError(f"Year {t}: the wage curve did not converge (largest gap {gap:.1e}; {msg})")
        return state["sol"], model

    @staticmethod
    def _check_sr_consumption(a):
        """0.3.13 (22 Oct 2026): refuse an sr_consumption assumption the rule is not defined for (at construction, and
        again before a scenario path, since scripts may set assumptions afterwards, as they set wage_curve). Returns lam or None."""
        sc = a["sr_consumption"]
        if sc is None:
            return None
        lam = sc.get("htm") if isinstance(sc, dict) else None
        if (not isinstance(sc, dict) or set(sc) != {"htm"} or isinstance(lam, bool) or not isinstance(lam, numbers.Real)
                or not np.isfinite(float(lam)) or not 0.0 <= float(lam) <= 1.0):
            raise ValueError("sr_consumption must be None or {'htm': lam} with 0 <= lam <= 1, the hand-to-mouth share of "
                             "household spending in short-run years (lam = 1 is the engine without the rule)")
        if not a["hybrid"]:
            raise ValueError("sr_consumption is a rule of the hybrid closure's short-run years and needs hybrid=True: without "
                             "it every year is solved in a long-run closure, where the saving rate is not free (it clears "
                             "savings and investment, or is held at the baseline's)")
        return float(lam)

    def _sr_consumption_ref(self, t, model):
        """0.3.13 (22 Oct 2026; sr_consumption): the consumption rule's reference in short-run year t, from the baseline
        year's solution: the hand-to-mouth share lam, the baseline saving-rate adjustment, the baseline saving rates by household
        (mps x (1 + MPSADJ_b), clipped to [-1, 1] as cge.py clips them), and the baseline spending EH (by household) and CPI."""
        b = self.base.solutions[t]
        mpsadj_b = float(b["MPSADJ"])
        return {"lam": float(self.a["sr_consumption"]["htm"]), "mpsadj": mpsadj_b,
                "mps": np.clip(np.asarray(model.mps, float) * (1.0 + mpsadj_b), -1.0, 1.0),
                "EH": np.asarray(b["EH"], float), "CPI": float(b["CPI"])}

    def _sr_consumption_target(self, s, ref):
        """0.3.13: the rule's household spending at solution s, by household: lam x (1 - baseline saving rate) x
        disposable income + (1 - lam) x baseline spending x CPI / baseline CPI (the share 1 - lam keeps its baseline real value;
        check CS1 recomputes it independently, and its tamper test drops the CPI term here)."""
        lam = ref["lam"]
        return (lam * (1.0 - ref["mps"]) * np.asarray(s["DY"], float)
                + (1.0 - lam) * ref["EH"] * (float(s["CPI"]) / ref["CPI"]))

    def _sr_fixed_point(self, sol, model, spec, t, K, wage=True):
        """0.3.13 (22 Oct 2026, a design note (not included), section 7; check CS1): the
        short-run consumption rule (sr_consumption) of year t, solved jointly with the wage curve (as _wage_curve: each fixed-wage
        labour type's anchor wbar x min(1, EMP/EMP_baseline) ** beta) as ONE root, with scipy's hybrid Powell method; each
        evaluation is a full solve of the short-run model. Unknowns: x = ln(anchor / baseline anchor) for each fixed-wage labour
        type (when the wage curve is on, the model has fixed-wage types and wage is True), and v, with the year's saving-rate
        adjustment 1 + MPSADJ = (1 + MPSADJ_b)(1 + v). Residuals: the wage curve's, and the rule's (the rule's household spending
        less household spending, summed over households, over household saving at the baseline rates: algebraically the
        prototype's residual, the 'smooth' hook of a development script (not in this repository), but measured on the solution's own
        spending). Start: the baseline anchors (x = 0) and the year's last v (0, the baseline saving rates, before the first
        solve), as the prototype. wage=False (the employment cap's re-solve after a change of regime, when the cap is not solving
        the wage curve jointly) keeps the anchors as they are and solves v alone. As _wage_curve, a start that is already the
        fixed point (a year with no shock) is accepted when the root does not stop (gap below 1e-10). Refused after the root: a
        saving rate the rule would push outside [-1, 1] (cge.py clips them). Returns (solution, model)."""
        from scipy.optimize import root
        m, b = self.m, self.base.solutions[t]
        ref = self._sr_consumption_ref(t, model)
        use_wc = bool(wage) and bool(self.a["wage_curve"]) and bool(model.unemployed)
        fs = list(model.unemployed) if use_wc else []
        nf = len(fs)
        if use_wc:
            beta = float(self.a["wage_curve"])
            idx = float(b["CPI"]) if model.wage == "real" else 1.0
            w0 = np.array([float(b["WF"][m.F.index(f)] / idx) for f in fs])
            e0 = np.array([float(b["EMP"][m.F.index(f)]) for f in fs])
        mo = self._mps_override.get(t)
        v0 = 0.0 if mo is None else (1.0 + float(mo)) / (1.0 + ref["mpsadj"]) - 1.0
        state = {"sol": sol}

        def resid(z):
            x, v = z[:nf], float(z[nf])
            if use_wc:
                self._wbar_override[t] = dict(zip(fs, w0 * np.exp(x)))
            self._mps_override[t] = ref["mpsadj"] if v == 0.0 else (1.0 + ref["mpsadj"]) * (1.0 + v) - 1.0
            s = model.solve(self._short_run_spec(spec, t, K, model), x_start=state["sol"].x)
            if not s.ok:
                raise RuntimeError(f"Year {t}: consumption-rule solve failed ({s.message})")
            state["sol"] = s
            out = []
            if use_wc:
                e = np.array([float(s["EMP"][m.F.index(f)]) for f in fs])
                out += list(x - beta * np.log(np.minimum(1.0, e / e0)))
            DY = np.asarray(s["DY"], float)
            out.append(float(self._sr_consumption_target(s, ref).sum() - np.sum(s["EH"])) / float(ref["mps"] @ DY))
            return np.array(out)

        z0 = np.concatenate([np.zeros(nf), [v0]])
        try:
            r = root(resid, z0, method="hybr", options={"xtol": 1e-12})
            res, msg = resid(r.x), r.message         # leave the model at the root's solution
        except RuntimeError as err:
            res, msg = None, str(err)
        if res is None or not np.all(np.abs(res) < 1e-8):
            r0 = resid(z0)                           # the start may itself be the fixed point (no shock): see _wage_curve
            if not np.all(np.abs(r0) < 1e-10):
                gap = np.abs(res).max() if res is not None else float("nan")
                raise RuntimeError(f"Year {t}: the consumption rule{' and the wage curve' if use_wc else ''} did not converge "
                                   f"(largest gap {gap:.1e}; {msg})")
        s = state["sol"]
        rate = np.asarray(model.mps, float) * (1.0 + float(s["MPSADJ"]))
        if np.any(np.abs(rate) >= 1.0):
            raise RuntimeError(f"Year {t}: the consumption rule needs a saving rate outside [-1, 1] (largest "
                               f"{float(np.abs(rate).max()):.2f}); the model clips saving rates there")
        return s, model

    def _cap_employment(self, sol, model, spec, t, K, L_index):
        """0.3.7: employment of a fixed-wage labour type may not exceed its supply. Types whose demand would
        exceed it are re-solved at full employment with a flexible wage; a capped type whose market wage falls below its
        fixed wage goes back on the fixed wage (complementarity). Returns (solution, model, capped types).

        0.3.10 (18 Oct 2026, evening; review D4): with the wage curve on, the anchors of the types left on fixed wages
        come from the wage-curve fixed point solved before the cap, which the loop does not re-solve. Capping one type can
        then make another flip for ever between 'just above its supply on its old anchor' and 'capped, with a market wage
        just below its full-employment wage' (Infinity GEM's own SAM, 2027, public works back to the 2024 programme: high-skill labour
        at 1.0007 and 0.998). A regime seen twice means exactly that cycle, which made the old loop fail; from then on the
        wage-curve fixed point is re-solved after each change of regime (the joint solution). Runs whose regimes never repeat,
        every run that settled before, are unchanged; years solved jointly are listed in self.cap_joint_years."""
        m, b = self.m, self.base.solutions[t]
        Lv = np.array([L_index.get(f, 1.0) for f in m.F]) if isinstance(L_index, dict) else np.where(
            [f.startswith("flab") for f in m.F], L_index, 1.0)
        supply = m.QFS0 * Lv
        allu = list(self.a["short_run_unemployed"])
        idx = float(b["CPI"]) if self.ms.wage == "real" else 1.0
        wbar = {f: float(b["WF"][m.F.index(f)] / idx) for f in allu}
        joint, seen = False, {tuple(sorted(model.unemployed))}
        for _ in range(4 * len(allu) + 2):
            fixed_w = lambda f: wbar[f] * (float(sol["CPI"]) if self.ms.wage == "real" else 1.0)
            over = [f for f in model.unemployed if sol["EMP"][m.F.index(f)] > supply[m.F.index(f)] * (1 + 1e-9)]
            back = [f for f in allu if f not in model.unemployed and sol["WF"][m.F.index(f)] < fixed_w(f) * (1 - 1e-9)]
            if not over and not back:
                if joint:
                    self.cap_joint_years = getattr(self, "cap_joint_years", set()) | {t}
                return sol, model, [f for f in allu if f not in model.unemployed]
            keep = [f for f in allu if (f in model.unemployed and f not in over) or f in back]
            key = tuple(sorted(keep))
            if key in seen and self.a["wage_curve"] and not joint:
                joint = True                             # the regimes cycle (see above): solve the wage curve with the cap
            seen.add(key)
            model = self._ms_for(keep)
            sol = model.solve(self._short_run_spec(spec, t, K, model), x_start=self._short_run_start(t, model))
            if not sol.ok:
                raise RuntimeError(f"Year {t}: solve with employment capped at supply failed ({sol.message})")
            if self.a["sr_consumption"] is not None:     # 0.3.13: the consumption rule re-solved in the new regime,
                sol, model = self._sr_fixed_point(sol, model, spec, t, K, wage=joint)   # with the wage curve when joint
            elif joint and model.unemployed:
                sol, model = self._wage_curve(sol, model, spec, t, K)
        raise RuntimeError(f"Year {t}: the employment cap did not settle")

    def _short_run_spec(self, spec, t, K, ms=None):
        """Anchor the short-run model to the baseline equilibrium of year t (hybrid closure)."""
        ms = ms or self.ms
        bsol = self.base.solutions[t]
        kc = ms.F.index("fcap")
        kshare = np.where(ms.QF0[kc] > 0, bsol["QF"][kc] / np.where(ms.QF0[kc] > 0, ms.QF0[kc], 1), 1.0)
        spec = dict(spec)
        spec["qfs_scale"] = dict(spec["qfs_scale"], fcap=1.0)
        if self.vintage:                         # 0.3.12: in a short-run year the year's new capital is
            # placed where the baseline placed it (investment plans made before the shock); the scenario's capital path enters
            # as its deviation from the baseline's old capital and pool; no pool is re-allocated within the year, and installed
            # capital moves only through vintage_e_sr (0 by default: fixed, as in the usual short run). Zero shock = baseline.
            kold = np.asarray(bsol["QF"], float)[kc].copy()
            kb = np.asarray(self.base.capital[t], float)
            nkb = np.asarray(bsol["NK"], float)
            nkb = nkb / nkb.sum() if nkb.sum() > 0 else np.ones_like(nkb) / max(len(nkb), 1)
            dpool = self._knew - self.base_knew[t]
            for j, i in enumerate(ms.iK):
                kold[i] += (K[i] - kb[i]) + dpool * nkb[j]
            spec["kscale"] = {a: float(kold[i] / self.K0a[i]) for i, a in enumerate(ms.A) if self.K0a[i] > 0}
            spec.pop("knew", None)                       # the long-run spec's pool does not apply here
            if ms.capital == "vintage":
                spec["knew"] = 0.0
        elif self.by_act:
            spec["kscale"] = {a: float(K[i] / self.K0a[i]) for i, a in enumerate(ms.A) if self.K0a[i] > 0}
        else:
            spec["kscale"] = {a: float(kshare[i] * K / self.base.capital[t]) for i, a in enumerate(ms.A)}
        exr_scale = float(spec.pop("exr_scale", 1.0))
        if ms.fx == "flexible" and abs(exr_scale - 1.0) > 1e-12:
            raise ValueError(f"Year {t}: 'exr_scale' (a peso shock) needs the fixed peso of sr_fx='fixed'")
        spec["exr"] = float(bsol["EXR"]) * exr_scale                   # 0.3.7: peso shock (check EX1)
        if ms.pricing == "sticky":               # 0.3.8 (review D2): prices anchored to the baseline year's, rigid downward
            spec["pa_anchor"] = {x: float(bsol["UNITREV"][i]) for i, x in enumerate(ms.A)}
            s_ = self.a["sr_stickiness"]
            spec["stickiness"] = dict(s_) if isinstance(s_, dict) else float(s_)
        elif ms.pricing == "markup":             # 0.3.13: markups, installed technology, exporters' reference home sales and the
            spec.update(ms.markup_at(bsol, self.base.tfp[t]))   # stickiness anchor from the baseline year (zero shock = baseline)
            s_, p_ = self.a["sr_stickiness"], self.a["sr_markup_pass"]
            spec["stickiness"] = dict(s_) if isinstance(s_, dict) else float(s_)
            spec["mk_pass"] = dict(p_) if isinstance(p_, dict) else float(p_)
        if ms.en is not None:                    # 0.3.11: installed technology centred on the baseline year
            spec["en_shares"] = ms.energy_shares_at(bsol["PQ"], bsol["PVA"], bsol["QA"], self.m)
        if ms.hoarding > 0:                      # 0.3.11: hoarding relative to the baseline year's labour by activity
            spec["hoard_ref"] = np.asarray(bsol["QF"], float)
        if self.a["sr_consumption"] is not None:     # 0.3.13: the consumption rule sets the year's saving-rate adjustment
            if "mpsadj" in spec:                     # (_sr_fixed_point); before its first solve, the baseline's
                raise ValueError(f"Year {t}: a scenario 'mpsadj' (saving-rate shock) is not defined with sr_consumption, whose "
                                 "rule sets the saving rate of short-run years")
            mo = (getattr(self, "_mps_override", None) or {}).get(t)
            spec["mpsadj"] = float(bsol["MPSADJ"]) if mo is None else float(mo)
        else:
            spec["mpsadj"] = float(bsol["MPSADJ"])
        if self.m.closure == "interest":         # 0.3.11: the baseline's real investment includes its
            spec["iadj"] = spec["iadj"] * float(np.exp(-self.m.interest["theta"] / 100 * float(bsol["RINT"])))   # r term
        idx = float(bsol["CPI"]) if ms.wage == "real" else 1.0          # 0.3.4: sticky pesos = the baseline peso wage
        spec["wbar"] = {f: float(bsol["WF"][k] / idx) for k, f in enumerate(ms.F) if f in ms.unemployed}
        ov = (getattr(self, "_wbar_override", None) or {}).get(t)   # 0.3.7: wage curve (see _wage_curve)
        if ov:
            spec["wbar"].update({f: v for f, v in ov.items() if f in spec["wbar"]})
        if ms.land == "fixed":                   # 0.3.7: each crop keeps its baseline land of year t, times any 'lscale'
            kl = ms.klnd
            lshare = bsol["QF"][kl] / np.where(ms.QF0[kl] > 0, ms.QF0[kl], 1.0)
            cut = dict(spec.get("lscale") or {})
            spec["lscale"] = {ms.A[i]: float(lshare[i]) * float(cut.get(ms.A[i], 1.0)) for i in ms.iL}
        elif spec.get("lscale"):
            raise ValueError("'lscale' (land lost) needs DynamicCGE(land='fixed', hybrid=True)")
        return spec

    def _short_run_start(self, t, ms=None):
        """Starting point for the short-run solver: the baseline solution of year t in its layout."""
        ms = ms or self.ms
        b = self.base.solutions[t]
        x = ms.x0()
        x[ms.slices["QA"]] = b["QA"] / ms.QA0
        x[ms.slices["PDS"]] = b["PDS"][ms.iD]
        x[ms.slices["PQ"]] = b["PQ"][ms.iQ]
        x[ms.slices["WF"]] = b["WF"][ms.iFM]
        x[ms.slices["RK"]] = b["W"][ms.kcap, ms.iK]
        if ms.capital == "vintage":              # 0.3.12
            x[ms.slices["NK"]], x[ms.slices["RN"]] = b["NK"], b["RN"]
        if ms.land == "fixed":
            x[ms.slices["RL"]] = b["W"][ms.klnd, ms.iL]
        x[ms.slices["EXR"]] = b["EXR"] if ms.fx == "flexible" else b["FSAV"] / ms.fsav   # 0.3.8: the slot's unknown
        x[ms.slices["WALRAS"]] = 0.0
        return x

    def _lr_start(self, t):
        """0.3.8: the baseline solution of year t as a starting point for the savings-driven long-run model (the closure
        slot holds the investment level instead of the saving-rate adjustment)."""
        b = self.base.solutions[t]
        x = b.x.copy()
        x[self.mL.slices["CLOS"]] = float(b["IADJ"])
        return x

    def _run(self, shocks=None, tfp_path=None, calibrate=False):
        m = self.m
        sav_lr = self.mL is not None and shocks is not None and not calibrate   # 0.3.8 (D1): savings-driven long run
        hybrid = bool(self.a["hybrid"]) and shocks is not None and not calibrate
        unemp = [k for k, f in enumerate(m.F) if f in self.a["short_run_unemployed"]]
        gap = np.zeros(len(m.F))                     # employment gap carried into the year (share of supply)
        pubcap = self.a["public_capital"] is not None and shocks is not None and not calibrate
        dKG = 0.0                                    # public capital relative to the baseline (₱ bn, SAM prices)
        self._wbar_override = {}                     # 0.3.7: wage-curve anchors of this path only
        self._mps_override = {}                      # 0.3.13: the consumption rule's saving-rate adjustments, this path only
        if shocks is not None and not calibrate and self.a["sr_consumption"] is not None:
            self._check_sr_consumption(self.a)       # 0.3.13: also when set after construction
        icons = m.C.index("ccons")
        sols, tfps, caps, rows, dems = {}, {}, {}, [], {}
        K = self.K0a.copy() if self.by_act else self.K0
        Ktot0 = float(np.sum(self.K0a)) if self.by_act else self.K0
        self._knew = 0.0                             # 0.3.12 (vintage): no new capital in the benchmark year
        self._knew_path = {}                         # the pool of each year, kept for the short-run anchoring
        Y_index = 1.0
        x = None
        real0 = None
        for i, t in enumerate(self.years):
            if self.L_path is not None:
                L_index = self.L_path[t]
            else:
                L_index = (1 + self.a["labour_growth"]) ** i
            if i > 0:
                Y_index *= 1 + self.growth[t] / 100
            extra = (shocks or {}).get(t)
            self._knew_path[t] = self._knew
            leak = 0.0                                   #: government construction spending diverted as income
            if pubcap and self.pc.get("leakage", {}).get(t):
                igb = float(self.base.solutions[t]["QINV"][icons])
                share = self.pc["leakage"][t] * self.pc["ig_public_share"]
                leak = share * igb
                extra = dict(extra or {})
                q = dict(extra.get("qinv_scale") or {})
                q["ccons"] = q.get("ccons", 1.0) - share   # = baseline construction less L[t], before any other factor
                extra["qinv_scale"] = q
                add = dict(extra.get("trg_h_add") or {})
                for h, w in self.pc["leak_to"].items():
                    if h in ("saved", "abroad"):         # 0.3.6: kept by a few people and saved, or moved out of the country
                        k_ = "sav_add" if h == "saved" else "grow_out_add"
                        extra[k_] = extra.get(k_, 0.0) + w * leak
                    else:
                        add[h] = add.get(h, 0.0) + w * leak
                if add:
                    extra["trg_h_add"] = add
            dem = {}
            if calibrate and i > 0:
                prev_t = self.years[i - 1]
                dem = dict(dems[prev_t])
                if t in self.ind_targets:
                    tf, dem = self._calibrate_industries(t, K, L_index, Y_index, extra, x, sols[prev_t]["QVA"],
                                                         tfps[prev_t], dems[prev_t])
                elif np.ndim(tfps[prev_t]) == 0:
                    target = real_prev * (1 + self.growth[t] / 100)
                    def gap(tf):
                        s = m.solve(self._spec(t, K, L_index, Y_index, tf, extra, dem), x_start=x)
                        if not s.ok:
                            raise _SolveFailed
                        return m.gdp(s)["real"] - target
                    try:
                        tf = brentq(gap, tfps[prev_t] * 0.8, tfps[prev_t] * 1.3, xtol=1e-10)
                    except _SolveFailed:             # 0.3: search outward from last year's value instead
                        tf = _robust_root(gap, tfps[prev_t], xtol=1e-10)
                else:                                # industry baseline after the data years: one common TFP rate
                    target = real_prev * (1 + self.growth[t] / 100)
                    tprev = np.asarray(tfps[prev_t], float)
                    def gap(sc):
                        s = m.solve(self._spec(t, K, L_index, Y_index, sc * tprev, extra, dem), x_start=x)
                        if not s.ok:
                            raise _SolveFailed
                        return m.gdp(s)["real"] - target
                    tf = _robust_root(gap, 1.0, xtol=1e-12) * tprev
            else:
                tf = 1.0 if i == 0 else tfp_path[t]
                if i > 0 and not calibrate and getattr(self, "base", None) is not None and self.base.demand:
                    dem = dict(self.base.demand[t])
            tf_used = tf
            dKG_start = dKG
            if pubcap and dKG:
                KGb = self.pc["kg_gdp"] * float(self.base.table.loc[t, "real_gdp"])
                tf_used = tf * (1 + dKG / KGb) ** self.pc["phi"]
            spec = self._spec(t, K, L_index, Y_index, tf_used, extra, dem)
            short = hybrid and t in shocks and (self.a["short_run_years"] is None or t in self.a["short_run_years"])
            if short:
                model = self.ms
                sol = model.solve(self._short_run_spec(spec, t, K), x_start=self._short_run_start(t))
            else:
                model = self.mL if sav_lr else m
                if abs(float(spec.pop("exr_scale", 1.0)) - 1.0) > 1e-12:
                    raise ValueError(f"Year {t}: 'exr_scale' (a peso shock) applies only in short-run years, where the peso "
                                     "is held at its baseline; in long-run years the peso is determined by the model")
                if hybrid and gap.any():
                    spec["qfs_scale"] = {f: v * (1 - gap[m.F.index(f)]) for f, v in spec["qfs_scale"].items()}
                if sav_lr:                               # 0.3.8 (D1): saving rates at the baseline's; investment follows
                    spec["mpsadj"] = float(self.base.solutions[t]["MPSADJ"])
                    sol = model.solve(spec, x_start=x if x is not None else self._lr_start(t))
                    if not sol.ok:
                        sol = model.solve(spec, x_start=self._lr_start(t))
                else:
                    sol = m.solve(spec, x_start=x)
                if not sol.ok and calibrate and t in self.ind_targets:     # 0.3: restart from the calibration's point
                    sol = m.solve(spec, x_start=self._calib_x)
                if not sol.ok and not calibrate and not sav_lr and getattr(self, "base", None) is not None:
                    sol = m.solve(spec, x_start=self.base.solutions[t].x)  # 0.3: restart from the baseline's solution
            if not sol.ok and not calibrate and extra and getattr(self, "base", None) is not None:
                # 0.3.7: very large shocks, solved in steps (25%, 50%, 75%, 100% of the year's shock),
                # each step starting from the last solution (continuation). The final step is the full shock, solved to
                # the usual tolerance, so the result is the same equilibrium, only reached more safely.
                xs = self._short_run_start(t) if short else (self._lr_start(t) if sav_lr else self.base.solutions[t].x)
                for lam in (0.25, 0.5, 0.75, 1.0):
                    sp = self._spec(t, K, L_index, Y_index, tf_used, _scale_shock(extra, lam), dem)
                    if short:
                        sp = self._short_run_spec(sp, t, K)
                    else:
                        sp.pop("exr_scale", None)             # already refused above if it was not 1
                        if sav_lr:
                            sp["mpsadj"] = float(self.base.solutions[t]["MPSADJ"])
                        if hybrid and gap.any():
                            sp["qfs_scale"] = {f: v * (1 - gap[m.F.index(f)]) for f, v in sp["qfs_scale"].items()}
                    sol = model.solve(sp, x_start=xs)
                    if not sol.ok:
                        break
                    xs = sol.x
            if not sol.ok:
                raise RuntimeError(f"Year {t}: solve failed ({sol.message}, residual {sol.residual_max:.2e})")
            capped = []
            if short and self.a["sr_consumption"] is not None:   # 0.3.13: the consumption rule, solved with the wage
                sol, model = self._sr_fixed_point(sol, model, spec, t, K)   # curve as one root (check CS1)
            elif short and self.a["wage_curve"]:         # 0.3.7 (16 Oct): pay gives a little when work falls (check WC1)
                sol, model = self._wage_curve(sol, model, spec, t, K)
            if short and self.a["employment_cap"]:      # 0.3.7: employment at most the labour supply
                sol, model, capped = self._cap_employment(sol, model, spec, t, K, L_index)
                if capped and self.a["wage_curve"]:     # 0.3.9 (review D4): not solved jointly; flag it
                    import warnings
                    if t in getattr(self, "cap_joint_years", set()):     # 0.3.10: the cycle fallback solved it jointly
                        warnings.warn(f"Year {t}: the employment cap binds for {capped}; the regimes cycled, so the wage curve "
                                      "was re-solved with the cap (joint solution; review D4)")
                    else:
                        warnings.warn(f"Year {t}: the employment cap binds for {capped} while the wage curve is on; the "
                                      "wage-curve fixed point is not re-solved for the other labour types (review D4)")
            if not short:
                x = sol.x
            if hybrid:
                if short:                            # gap opened this year, relative to the labour supply
                    Lv = (np.array([L_index.get(f, 1.0) for f in m.F]) if isinstance(L_index, dict) else L_index)
                    supply = m.QFS0 * Lv
                    gap = np.zeros(len(m.F))
                    gap[unemp] = 1 - sol["EMP"][unemp] / supply[unemp]
                gap_now = gap.copy()
                gap = gap * self.a["gap_persistence"]
            waste_adj = 0.0                              # 0.3.6: wasted public spending kept out of the general stock
            if pubcap:
                igb = float(self.base.solutions[t]["QINV"][icons])
                dIG = float(sol["QINV"][icons]) - igb
                if model is self.mL:                     # 0.3.8 (D1): only the shock's change is public investment; the
                    dIG = float(sol["QINV"][icons]) * Y_index / float(sol["IADJ"]) - igb   # savings-driven part is private
                e_t = (self.pc.get("e_path") or {}).get(t, self.pc["e"])
                overrun = 0.0                            # 0.3.6: absorptive capacity (DIG): extra spending buys less
                if self.pc.get("absorptive", 0.0) and dIG > 0:
                    KGb_t = self.pc["kg_gdp"] * float(self.base.table.loc[t, "real_gdp"])
                    overrun = dIG - dIG / (1 + self.pc["absorptive"] * dIG / KGb_t)
                dIGk = dIG - overrun
                if e_t == self.pc["e"] and not leak:     # the 0.3 channel exactly (check CR1)
                    dKG = (1 - self.pc["delta_g"]) * dKG + self.pc["e"] * dIGk
                else:                                    #: efficiency of the year on all public investment
                    dKG = ((1 - self.pc["delta_g"]) * dKG + e_t * (dIGk + leak)
                           + (e_t - self.pc["e"]) * self.pc["ig_public_share"] * igb)
                if (self.pc.get("kg_loss") or {}).get(t):    # 0.3.7: public capital destroyed in year t (₱ bn, SAM units),
                    dKG -= self.pc["kg_loss"][t]                 # e.g. typhoon damage to public infrastructure (NDRRMC)
                if self.pc.get("waste_lost"):            # 0.3.6: wasted public spending is not capital in the general stock
                    s_ = self.pc["ig_public_share"]
                    disb = s_ * igb + dIG + leak         # government construction disbursement of the year
                    waste_adj = (1 - e_t) * disb - leak - (1 - self.pc["e"]) * s_ * igb + e_t * overrun
                if not self.pc.get("general_stock", True):   # 0.3.7: public construction builds public capital only (check PK1)
                    waste_adj = dIG                          # the change vs the baseline stays out of the general stock
            g = model.gdp(sol)
            real_prev = g["real"]
            if real0 is None:
                real0 = g["real"]
            sols[t], tfps[t], caps[t], dems[t] = sol, tf, (K.copy() if self.by_act else K), dem
            Ktot = (float(np.sum(K)) + (self._knew if self.vintage else 0.0)) if self.by_act else K
            rows.append(dict(year=t, real_gdp=g["real"], nominal_gdp=g["nominal_expenditure"],
                             real_consumption=float(sol["QH"].sum()), real_investment=float(sol["QINV"].sum()),
                             capital_stock_index=Ktot / Ktot0, tfp=tf, cpi=sol["CPI"], exr=sol["EXR"],
                             walras=sol["WALRAS"],
                             **({"closure": "short run" if short else "long run",
                                 "employment_gap_low_skill_pct": -gap_now[unemp[0]] * 100 if unemp else 0.0,
                                 "employment_capped": ",".join(capped)}
                                if hybrid else {}),
                             **({"public_capital_gap_pct": dKG_start / (self.pc["kg_gdp"] * float(self.base.table.loc[t, "real_gdp"])) * 100}
                                if pubcap else {})))
            # capital for next year from this year's real investment
            inv_k = float(sol["QINV"].sum()) - waste_adj     # 0.3.6: less any wasted public spending (waste_lost)
            if self.putty:
                K = (1 - self.a["depreciation"]) * K + self.allocation(sol) * self.kappa * inv_k
            elif self.vintage:                       # 0.3.12: old capital stays where it was used this
                K = (1 - self.a["depreciation"]) * np.asarray(sol["QF"][self.kc], float)   # year (new hired included), depreciated
                self._knew = self.kappa * inv_k        # this year's investment becomes next year's pool of new capital
            else:
                K = (1 - self.a["depreciation"]) * K + self.kappa * inv_k
        df = pd.DataFrame(rows).set_index("year")
        df["real_gdp_growth_pct"] = df["real_gdp"].pct_change() * 100
        return Path(self.years, sols, tfps, caps, df, dems if any(dems.values()) else None)

    def allocation(self, sol) -> np.ndarray:
        """Shares of new capital by activity (Thurlow 2004, eq. Q; IFPRI recursive dynamic model)."""
        QF = np.asarray(sol["QF"][self.kc], float)
        R = np.asarray(sol["W"][self.kc], float)
        AR = float((R * QF).sum() / QF.sum())
        share = QF / QF.sum() * (self.a["omega"] * (R / AR - 1) + 1)
        share = np.clip(share, 0.0, None)
        return share / share.sum()

    # ------------------------------------------------------------------ public API
    def baseline(self) -> Path:
        """Calibrate the TFP path so real GDP follows `growth`."""
        self.base = self._run(calibrate=True)
        self.base_knew = dict(self._knew_path)       # 0.3.12 (vintage): the baseline's pool by year
        return self.base

    def scenario(self, shocks: dict) -> Path:
        """shocks = {year: CGE shock spec}. Uses the baseline TFP path (run baseline() first). With the assumption monetary={...}
        (0.3.12) every path is solved with the BSP rule inside: monetary_scenario(shocks, **monetary)."""
        if not hasattr(self, "base"):
            self.baseline()
        if self.a["monetary"] is not None:
            return self.monetary_scenario(shocks, **self.a["monetary"])
        return self._run(shocks=shocks, tfp_path=self.base.tfp)

    # ------------------------------------------------------------------ (0.3.12, 20 Oct 2026): a BSP rule inside the model
    def monetary_gaps(self, sim: Path) -> pd.DataFrame:
        """A path's gaps against the baseline, year by year, as the rule reads them: the output gap (%), the inflation gap (the
        scenario's CPI inflation less the baseline's, pp a year) and the peso's depreciation gap (pp a year). The inflation gap
        exists only in short-run years, where the peso is the numeraire and the CPI moves; in long-run years the CPI is the
        numeraire (the price level is not modelled), so the gap is zero there, and a short-run year after a long-run year starts
        from a price-level ratio of one."""
        b, s = self.base.table, sim.table
        g = pd.DataFrame(index=s.index)
        g["output_gap_pct"] = (s["real_gdp"] / b["real_gdp"] - 1) * 100
        short = (s["closure"] == "short run") if "closure" in s.columns else pd.Series(False, index=s.index)
        infl, depr, prev, prevx = {}, {}, 1.0, 1.0
        for t in s.index:
            lvl = float(s.loc[t, "cpi"] / b.loc[t, "cpi"]) if bool(short[t]) else 1.0
            infl[t] = (lvl / prev - 1) * 100 if bool(short[t]) else 0.0
            prev = lvl
            lx = float(s.loc[t, "exr"] / b.loc[t, "exr"])
            depr[t] = (lx / prevx - 1) * 100
            prevx = lx
        g["inflation_gap_pp"], g["depreciation_gap_pp"] = pd.Series(infl), pd.Series(depr)
        return g

    @staticmethod
    def annual_rule(rule: dict, target: float, i_end_prev: float) -> tuple:
        """The year's average policy-rate gap and its end-of-year value (pp a year) from last year's end value and the year's target
        T = phi_pi x inflation gap + phi_x x output gap + phi_e x depreciation gap. freq="quarterly" (default): the rule is the
        quarterly partial adjustment i_q = rho i_{q-1} + (1 - rho) T with T constant within the year (the gaps are annual), so
        after four quarters i_end = T + (i_end_prev - T) rho^4 and the year's average is T + (i_end_prev - T) rho (1 - rho^4) /
        (4 (1 - rho)): the quarterly coefficients are used unchanged. freq="annual": i = rho i_prev + (1 - rho) T."""
        rho = float(rule["rho"])
        if not 0.0 <= rho < 1.0:
            raise ValueError("rule['rho'] must be in [0, 1)")
        if rule.get("freq", "quarterly") == "annual":
            i = rho * i_end_prev + (1 - rho) * target
            return i, i
        i_end = target + (i_end_prev - target) * rho ** 4
        i_avg = target + (i_end_prev - target) * (rho * (1 - rho ** 4) / (4 * (1 - rho)))
        return i_avg, i_end

    def monetary_scenario(self, shocks: dict, rule: dict = None, theta: float = 2.0, fx_per_pp: float = 0.0,
                          expectations: str = "adaptive", path: dict = None, years=None, tol: float = 0.01,
                          max_iter: int = 15, accelerate: bool = True, relax: float = 0.5) -> Path:
        """The money block (0.3.12, 20 Oct 2026): the path with a BSP policy rule inside the model, solved as a fixed point over the
        whole path (each iteration is one scenario run; the rule's feedback on the gaps is weak, so two to four iterations
        usually suffice). Opt-in; with no rule the model is as before.
        - rule: {"rho", "phi_pi", "phi_x" (pp a year per % of output gap), "phi_e" (optional), "freq" (optional)}: the policy-rate
          gap of year t follows annual_rule() from the gaps of year t itself (monetary_gaps), so the rule acts within the year.
          infinity_gem.monetary.rule(name) gives PAMPh's and the project's estimated coefficients.
        - theta: real investment demand is scaled by exp(-theta x real-rate gap / 100) in every year the rule acts (the CGE link's
          channel, scenarios/qpm_cge_link.py; theta is not identified by Philippine data, 1.9-3.3 matched, 2 central). The
          real-rate gap is the policy-rate gap less the expected inflation gap: expectations="adaptive" (default) = last year's
          inflation gap (backward-looking, as the hand-to-mouth candidate's households), "current" = the same year's (an ex post
          real rate), "foresight" = next year's gap of the path (model-consistent, as in the DSGE; zero after the last year).
          In the 2026 scenarios' setting, where three short-run years carry shocks, "foresight" couples the years through expectations
          and the fixed point does not settle (20 Oct 2026 diagnostic: the change in the rate path crept up from 0.09 to 0.16 pp
          over 15 iterations under damping, while "adaptive" converged in 5); use it only where the path converges.
        - fx_per_pp: the peso's change (%) per pp of real-rate gap in short-run years (needs sr_fx="fixed"); 0 (default) = the
          peso stays at its baseline (uncovered interest parity is not imposed).
        - path: {year: {"i": policy-rate gap (pp, the year's average), "pi_e": expected inflation gap (pp)}} replaces the rule
          (a DSGE's path, or a rate held up one point for a year); years not listed get zero.
        - years: the years the rule acts in; None = every year from the first year that carries a shock (an empty placeholder
          year before the shocks is left alone, so the rule cannot anticipate them; only the shock years themselves when the
          hybrid closure's short_run_years is None, so that the rule creates no new short-run year).
        - relax, accelerate, tol: the path used in the next iteration is a damped step towards the rule's rate (relax 0.5; the plain
          map can diverge in the 2026 scenarios' setting, where the years are coupled through expectations), replaced after two iterations by
          a secant step on the residual, year by year, where the last two paths differ by at least ten times tol (the slope is
          clipped to [-0.9, 0.5]; near the solver's noise floor the secant would amplify noise). Convergence = the largest change
          between the rate the rule gives and the rate the path was run with is below tol (0.01 pp: at theta 2 that is 0.02% of
          investment, below the model's own solve noise); the result does not depend on the step scheme.
        Returns a Path whose .monetary table carries the gaps, the policy-rate gap, expected inflation, the real-rate gap and
        the scales applied, with attrs 'iterations', 'converged' and 'deltas' (the largest change of the rate path, pp, by
        iteration). Limits: the rule sees an inflation gap only in short-run years (monetary_gaps); the lag between the rule
        and investment is within the year. Check MP1."""
        if not hasattr(self, "base"):
            self.baseline()
        if path is None and not rule:
            raise ValueError("monetary_scenario needs rule={rho, phi_pi, phi_x, ...} or path={year: {'i': ...}}")
        if expectations not in ("foresight", "adaptive", "current"):
            raise ValueError("expectations must be 'foresight', 'adaptive' or 'current'")
        if fx_per_pp and self.a["hybrid"] and self.a["sr_fx"] != "fixed":
            raise ValueError("fx_per_pp (a peso response) needs sr_fx='fixed'")
        if max_iter < 1:
            raise ValueError("max_iter must be at least 1")
        m = self.m
        inv = [c for i, c in enumerate(m.C) if m.qinv[i] > 0]
        hybrid = bool(self.a["hybrid"])
        srfix = self.a["short_run_years"]
        if years is None:                            # from the first year that carries a shock (an empty placeholder year, e.g.
            shocked = [t for t in shocks if shocks[t]]   # {2025: {}}, is before the shocks: the rule must not anticipate them)
            first = min(shocked) if shocked else self.years[-1]
            years = [t for t in self.years[1:] if t >= first]
            if hybrid and srfix is None:
                years = [t for t in years if t in shocks]
        years = list(years)
        rate, pie = {t: 0.0 for t in years}, {t: 0.0 for t in years}
        rule_rate = dict(rate)                       # the rate the rule gives (the path is run with `rate`, extrapolated when accelerated)
        prev = None                                  # (path used, rate the rule gave) of the previous iteration, for the secant step
        scale, fxs = {t: 1.0 for t in years}, {t: 1.0 for t in years}
        sim = self._run(shocks=shocks, tfp_path=self.base.tfp)      # the path without the rule
        g = self.monetary_gaps(sim)
        deltas, converged, it = [], False, 0
        for it in range(1, max_iter + 1):
            new_rate, new_pie, i_end = {}, {}, 0.0
            for k, t in enumerate(years):
                if path is not None:
                    pt = path.get(t) or {}
                    i_avg, pi_e = float(pt.get("i", 0.0)), float(pt.get("pi_e", 0.0))
                    i_end = i_avg
                else:
                    target = (float(rule["phi_pi"]) * float(g.loc[t, "inflation_gap_pp"])
                              + float(rule["phi_x"]) * float(g.loc[t, "output_gap_pct"])
                              + float(rule.get("phi_e", 0.0)) * float(g.loc[t, "depreciation_gap_pp"]))
                    i_avg, i_end = self.annual_rule(rule, target, i_end)
                    if expectations == "foresight":
                        pi_e = float(g.loc[years[k + 1], "inflation_gap_pp"]) if k + 1 < len(years) else 0.0
                    elif expectations == "adaptive":
                        pi_e = float(g.loc[years[k - 1], "inflation_gap_pp"]) if k > 0 else 0.0
                    else:
                        pi_e = float(g.loc[t, "inflation_gap_pp"])
                new_rate[t], new_pie[t] = i_avg, pi_e
            delta = max((abs(new_rate[t] - rate[t]) for t in years), default=0.0)
            deltas.append(delta)
            rule_rate, pie = new_rate, new_pie
            if delta < tol:                           # the path already carries this rate (within tol): done
                converged = True
                break
            damped = {t: rate[t] + relax * (new_rate[t] - rate[t]) for t in years}
            if path is not None:
                prev, rate, plain = (rate, new_rate), dict(new_rate), None
            elif accelerate and prev is not None:
                # a secant step on the residual G(x) - x, year by year: with the slope lam of G between the last two paths used
                # (signed, so an oscillating map is damped and a monotone one is extrapolated; clipped to [-0.9, 0.5]) the root
                # of the linearised residual is x + (G(x) - x) / (1 - lam); where the two paths are too close for a slope
                # (less than ten times tol apart) the damped step is kept, because the slope would be solver noise
                nxt = {}
                for t in years:
                    dx = rate[t] - prev[0][t]
                    if abs(dx) >= 10 * tol:
                        lam = min(max((new_rate[t] - prev[1][t]) / dx, -0.9), 0.5)
                        nxt[t] = rate[t] + (new_rate[t] - rate[t]) / (1 - lam)
                    else:
                        nxt[t] = damped[t]
                prev, rate, plain = (rate, new_rate), nxt, damped
            else:
                prev, rate, plain = (rate, new_rate), damped, None
            sh = self._monetary_shocks(shocks, years, rate, pie, theta, fx_per_pp, inv, hybrid, srfix, scale, fxs)
            try:
                sim = self._run(shocks=sh, tfp_path=self.base.tfp)
            except RuntimeError:
                if plain is None:
                    raise
                rate = plain                          # the secant step overshot into a path the model cannot solve: plain step
                sh = self._monetary_shocks(shocks, years, rate, pie, theta, fx_per_pp, inv, hybrid, srfix, scale, fxs)
                sim = self._run(shocks=sh, tfp_path=self.base.tfp)
            g = self.monetary_gaps(sim)
        tab = g.loc[years].copy()
        tab["policy_rate_gap_pp"] = pd.Series(rule_rate)
        tab["expected_inflation_gap_pp"] = pd.Series(pie)
        tab["real_rate_gap_pp"] = tab["policy_rate_gap_pp"] - tab["expected_inflation_gap_pp"]
        tab["investment_scale"] = pd.Series(scale)
        tab["exr_scale"] = pd.Series(fxs)
        tab.attrs.update({"iterations": it, "converged": converged, "deltas": deltas, "theta": theta, "expectations": expectations,
                          "fx_per_pp": fx_per_pp, "rule": dict(rule) if rule else None, "path": path})
        sim.monetary = tab
        return sim

    @staticmethod
    def _monetary_shocks(shocks, years, rate, pie, theta, fx_per_pp, inv, hybrid, srfix, scale, fxs):
        """The scenario's shocks with the rule's response added: real investment demand scaled by exp(-theta r / 100) in every
        year the rule acts (multiplying any scale the scenario already carries) and, in short-run years with a peso response, the
        peso by 1 + fx_per_pp r / 100. Fills `scale` and `fxs` in place."""
        sh = copy.deepcopy(shocks)
        for t in years:
            r = rate[t] - pie[t]
            scale[t] = float(np.exp(-theta * r / 100))
            d = dict(sh.get(t) or {})
            q = dict(d.get("qinv_scale") or {})
            for c in inv:
                q[c] = q.get(c, 1.0) * scale[t]
            d["qinv_scale"] = q
            short = hybrid and (srfix is None or t in srfix)
            fxs[t] = (1 + fx_per_pp * r / 100) if (fx_per_pp and short) else 1.0
            if fxs[t] != 1.0:
                d["exr_scale"] = float(d.get("exr_scale", 1.0)) * fxs[t]
            sh[t] = d
        return sh

    @staticmethod
    def compare(base: Path, sim: Path) -> pd.DataFrame:
        b, s = base.table, sim.table
        out = pd.DataFrame({
            "base_growth_pct": b["real_gdp_growth_pct"],
            "sim_growth_pct": s["real_gdp_growth_pct"],
            "gdp_gap_pct": (s["real_gdp"] / b["real_gdp"] - 1) * 100,
            "gdp_gap_bn": s["real_gdp"] - b["real_gdp"],
            "consumption_gap_pct": (s["real_consumption"] / b["real_consumption"] - 1) * 100,
            "capital_gap_pct": (s["capital_stock_index"] / b["capital_stock_index"] - 1) * 100,
        })
        out.loc["cumulative", "gdp_gap_bn"] = out["gdp_gap_bn"].sum()
        return out
