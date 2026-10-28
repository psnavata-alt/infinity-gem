"""Infinity GEM validation suite. Run before using any result, after any change to code or data,
and at least monthly.   py checks/run_all_checks.py

Each check prints PASS or FAIL and the report is saved to outputs/validation_report_<date>_<time>.md
(users who cannot write to the repository folder: their Documents folder, "Infinity GEM - my runs").
A FAIL means: do not use model results until it is explained and fixed.
NOT RUN (0.3.3, rigging audit finding 1): a check whose input is not on this computer (H3: the licensed FIES-LFS file) is
neither passed nor failed; the report counts it separately, e.g. "37 of 37 checks passed (1 not run on this computer: H3)".

Checks
  D1  Data files match their recorded checksums (data/DATA_INVENTORY.md): SHA-256 of the file for CSVs,
      SHA-256 of the cell values for Excel files (a file-sharing service rewrites Office file bytes).
  D2  Both SAMs balance (row totals = column totals).
  M1  SAM multipliers reproduce the September 2026 results: 2.170 / 2.200 (2018 / 2023 SAM, cut allocated 50/30/20 to
      rural Q1, rural Q2, urban Q1) and 2.162 / 2.197 (allocated to the bottom 40% by population).
  C1  CGE benchmark: every equation holds at the SAM values (max residual < 1e-7).
  C2  CGE replication: the SAM rebuilt from the benchmark solution equals the SAM (max gap < 1e-5).
  C3  Homogeneity: doubling the numeraire doubles all prices and leaves all quantities unchanged.
  C4  Walras' law: the savings-investment slack is zero after a large shock, in every closure.
  C5  GDP identity: GDP by expenditure = GDP by income in every shocked solution.
  C6  Direction: a 20% rise in world petroleum/chemical import prices lowers real GDP and real
      household consumption; a remittance cut lowers consumption; a construction-investment cut lowers
      real GDP under the short-run closure.
  C7  Bounds: the CGE's short-run GDP multiplier for construction investment is positive and below the
      SAM (fixed-price) multiplier.
  Y1  Dynamic: the baseline hits the target growth path; a zero-shock scenario reproduces it exactly.
  P1  Microsimulation: the FIES 2023 baseline reproduces PSA's official 17.54 million poor (within 0.1%).
  V1  VAR module: regression guard on the reference VAR's OLS coefficients that Infinity GEM's geopolitics shock uses (fx +0.0078;
      fdi -0.0600). A replication of an existing estimate, not an outside benchmark (outside: V7, statsmodels).
  I1  I-O model (infinity_gem.iomodel): VALIDATION: the Leontief inverse equals PSA's published Table B.3. REGRESSION
      VALUES (guard against unintended change; not validation): refined petroleum +10% gives CPI +0.6832 pp, PPI
      +0.8051 pp; a ₱238.3 bn construction cut gives a domestic-inverse GDP loss of ₱161.5 bn. The price model's
      correctness is tested by identities (I3, I4). (15 Oct 2026: earlier wording called the price values a
      reproduction of an earlier workbook; that shows equal arithmetic, not a sound method.)
  I2  I-O job-equivalents: regression values for the ₱242.93 bn infrastructure shock within 0.5% (construction
      -254,226; all industries -320,934). Job-equivalents are a fixed-price upper bound, not a forecast of job losses.
  A1  Simulator engines (app/engines.py) reproduce the scenario scripts: infrastructure short-run CGE (GDP -0.279%,
      497,479 new poor), SAM multiplier (-₱350.22 bn in SAM units), Ayuda SAM household income (-₱185.06 bn); the
      SAM GDP identity gives the 2023 SAM's GDP.
  I3  I-O identity (tolerance 1e-7 because PSA's published table rounds: inputs plus value
      added differ from output by up to 3e-8 of output): raising every primary-input cost by 10% raises every industry's price by
      exactly 10% (imported inputs are inside A in PSA's table, so value added is the only primary input).
  I4  I-O identity: with PSA's total inverse, one peso of final demand in any industry returns
      exactly one peso of value added; with the domestic inverse, value added plus imported inputs (direct and
      indirect) return exactly one peso. Value added per output is positive and below one in every industry.
  C8  CGE on the IFPRI 2018 SAM: after balancing (SAM.balance), the benchmark solves (C1), the SAM is
      reproduced (C2), homogeneity holds (C3), and a large shock satisfies Walras' law and the GDP identity (C4, C5),
      in all three closures. The 2018 SAM has an activity tax ('atax') instead of the capital tax ('ftax').
  Y2  Hybrid dynamic closure: a zero shock in a short-run year reproduces the baseline path exactly;
      a construction-investment cut opens a low-skill employment gap in the shock year that shrinks by the
      persistence factor each later year; and the cumulative GDP loss is larger than with the long-run closure alone.
  Y3  Public capital channel: with phi = 0 the path equals the model without the channel; a zero
      shock reproduces the baseline; with phi > 0 a construction cut lowers 2030 GDP by more, and the extra loss is
      close to proportional to phi. Uses kg_gdp = 1.0 as a TEST VALUE only (not a Philippine estimate).
  V2  IFPRI benchmark: on the condensed Philippine SAM, Infinity GEM's real GDP and real household
      consumption are within 0.01 pp of IFPRI's own standard CGE model (results saved from GAMS in
      validation/ifpri/gams_ph/ifpri_results.csv) for four shocks and two closures; at least 95% of all 232 compared
      results are within 0.1 pp and none differs by more than 0.6 pp (trade-margin treatment; validation/ifpri/README.md).
  V3  IFPRI-style trade margins (verification Phase 3; CGE(margins='split'), opt-in): the option reproduces the
      full 2023 SAM and passes the homogeneity test; on the condensed SAM, real GDP and consumption are within
      0.001 pp of IFPRI's model, at least 99% of the 232 results are within 0.1 pp and none differs by more than
      0.15 pp (the rest: CPI-weight and import-unit conventions, validation/ifpri/README.md).
  V4  Home consumption (0.3.1; CGE(home='separate'), opt-in; book eq. 18 and 34): the option reproduces the
      published 2023 SAM WITH its activity -> household cells, is homogeneous and keeps the GDP identity; against
      IFPRI's own model run on the condensed SAM with home consumption kept (validation/ifpri_home/), real GDP and
      consumption are within 0.01 pp and home consumption within 0.01 pp (default margins), or within 0.001 and
      0.002 pp with 99% of 240 results within 0.1 pp (margins='split').
  V5  Hosoe cross-check (0.3.1 options gov='cd', inv='value_shares', sigma_va=1, opt-in): on
      Hosoe et al.'s stdcge SAM, Infinity GEM reproduces the SAM and, after abolishing tariffs, every compared result of
      pycge (a human-written Python port of stdcge.gms; results saved in validation/hosoe/pycge_results.json) to
      within 1e-9 in levels and 1e-8 pp in % changes; sigma_va 0.9999 and 1.0001 land within 1e-5 of it.
  S2  Named settings (infinity_gem/settings.py): "0.2 published" builds exactly the default model; under
      "0.3 recommended" (petroleum split, Philippine elasticities, LES, IFPRI-style margins) the short- and long-run
      models reproduce their SAM (C2), are homogeneous (C3) and satisfy Walras' law and the GDP identity after a large
      shock (C4, C5); the 0.3 dynamic model (documented baseline, putty-clay, hybrid) hits its growth path and a
      zero shock reproduces it (Y1).
  H2  Household detail (infinity_gem/household.py): baseline 2,992,013 poor families and 17,538,864
      persons (= PSA); persons pushed into poverty equal infinity_gem.microsim's new poor; the net-seller adjustment leaves
      the national loss unchanged. Regression values (arithmetic agreement with earlier runs, not validation):
      decile table from saved group effects (validation/household_detail/); the price-only arithmetic (oil +1.54:
      156,329 families / 835,400 persons poor, 53,395 / 319,894 food-poor, ₱225.11 a month).
  H3  LFS link (PSA's FIES-LFS 2023 member file, licensed, read from paths.FIES_LFS_DIR; "NOT RUN" where
      absent): every member matches a FIES household; weighted employment within 2% of PSA's January 2024 LFS total;
      every employed member's PSIC code maps to a PSA industry; earnings by industry add up to FIES wages plus
      entrepreneurial income; the within-group redistribution keeps group totals; a zero shock changes nothing.
  A2  Simulator levers (0.3.1): every lever of the "Any other shock" table maps to a CGE shock key (zero rows do
      nothing); all five closures solve a mixed shock; rows that do not fit a lever are refused; in the dynamic model
      a zero lever leaves the freeze path unchanged and a TFP cut lowers GDP.
  D3  An edited SAM is refused (0.3.3, rigging audit finding 2): a copy of the 2023 SAM with one cell raised by ₱1 bn
      cannot be loaded for the model; only the 2018 SAM, published in rounded figures, is balanced automatically.
  W1  Saving when the outputs folder is read-only (0.3.2): with the outputs folder writable, results are saved there; made
      read-only by a real permission (Windows deny rule, or chmod on a Mac), Infinity GEM detects it, saves in the
      person's own folder (paths.MY_RUNS) and reads saved results from both; the write test leaves no file behind.
  V6  Structural VARs (0.3.3; infinity_gem/svar.py): regression guard against an existing estimation (the reference monthly VAR; outside validation is V7, statsmodels), reproducing it with
      block exogeneity (8 Oct 2026; validation/var_task1/): all 130 cumulated responses, total and with the peso held
      fixed, and their 1,000-draw bootstrap bands.
  V7  Structural VARs: unrestricted estimates and Cholesky responses equal statsmodels' (1e-12); block exogeneity is exact;
      the historical decomposition adds back to the data; the held variable stays at baseline in the counterfactual;
      sign-restriction draws satisfy their signs; a very loose Minnesota prior gives OLS.
  M2  VAR-to-CGE link (0.3.3; infinity_gem/macrolink.py): a zero change gives the base; an FDI change enters as foreign
      savings by its share of GDP and lowers investment in the savings closure; the keynesian closure refuses it.
  E1  Elasticity sets: each sourced set (gtap, ph, ph_pcgem_cet; infinity_gem/elasticities.py) loads
      for every sector, reproduces the SAM at the benchmark and passes the homogeneity test in both closures.
  Y4  Capital by industry (putty-clay, documented baseline): the baseline hits the DBCC growth path;
      a zero shock reproduces it exactly; new-capital shares sum to one and are never negative; baseline capital growth
      in 2024 is within 5-9% (PWT/ICSD range); within the stable range omega 0, 1, 3, 5, a higher investment mobility
      leaves rental rates closer together by 2030 (above about 5 the linear rule overshoots: see dynamic.py); a
      construction cut lowers construction's own capital relative to the baseline.
  Y5  Industry baseline: each of PSA's 16 industries grows exactly as PSA reports for 2024 and 2025
      (real GVA, OpenSTAT 0052B5BPRA1); real GDP then grows within 0.2 pp of PSA; a zero shock reproduces the baseline;
      the levers stay plausible (productivity changes within +-15% a year; demand and intensity factors within 0.8-1.25).
  L1  Labour growth by skill: psa_labour_growth() reproduces PSA LFS employment growth by skill for 2024 and 2025, and
      total employment from 2027 grows with PSA's projected population aged 15+; the dynamic model's labour supply
      follows the path exactly.
  H1  LES household demand: with Briones et al. (2023) elasticities, both closures reproduce the SAM
      at the benchmark and pass the homogeneity test; Engel aggregation holds (marginal budget shares sum to one);
      subsistence quantities are below benchmark quantities; the Frisch parameters are between -0.5 and -3; under an
      oil-price rise processed-food consumption falls less than with Cobb-Douglas (food is a necessity); the USDA ERS
      benchmark variant (Muhammad et al. 2011) also calibrates, with its implied Frisch in the same range.
  S1  Petroleum-split SAM: rebuilding it with tools/build_sam_petroleum_split.py reproduces the
      processed file; it balances; every account other than chemicals and petroleum is identical to the IFPRI 2023 SAM;
      the CGE reproduces it (benchmark residual, SAM gap) and passes homogeneity; with world oil +20% the refined-
      petroleum price rises by more than the import-weighted direct effect alone would be negative (>5%).
  S3  Rice-split SAM (0.3.7): tools/build_sam_rice_split.py reproduces the processed file; it balances; milled-
      rice imports equal PSA's 2023 customs value and their duty the BOC's certified rice tariff collections; maize imports
      are placed; fixed land (land='fixed') reproduces the benchmark of mobile land; a land shock is refused with mobile
      land; less rice land lowers rice output and raises milled-rice imports.
  Y6  Employment cap (0.3.7): in hybrid short-run years a zero shock changes nothing; a very large demand
      shock leaves employment of every fixed-wage labour type at or below its supply (without the cap it exceeds it).
  PK1 Public capital not counted twice (0.3.7, 15 Oct night): with public_capital general_stock=False a cut in public
      construction leaves the general capital stock on its baseline path; with phi > 0 its lasting GDP loss is smaller
      than with the old double channel; leaving the key out gives exactly the old results.
  SR1 Short-run years (0.3.7, 15 Oct night): short_run_years limits the hybrid's short-run closure to the years given;
      a shock in a later year is solved in the long-run closure; None keeps the old rule exactly.
  WC1 Wage curve (0.3.7, 16 Oct): with wage_curve=beta a demand cut in a short-run year costs fewer jobs and lowers the
      real wage; the fixed point holds (wage = baseline x (employment ratio) ** beta); a zero shock changes nothing; None
      gives the old results exactly.
  IC1 Investment closure and the peso (0.3.8, 17 Oct 2026 D1): investment_closure='savings' and
      sr_fx='flexible' each reproduce the no-shock path under a zero shock; with savings-driven long-run years a 2026
      construction cut lowers 2030 investment and leaves a larger 2030 GDP loss; with a flexible peso foreign savings stay on
      the baseline path; leaving the options out gives exactly the old results; a flexible peso is refused with CPI-indexed
      wages and a peso shock is refused with a flexible peso.
  PS1 Prices rigid downward (0.3.8, review D2): with pricing='sticky' the benchmark is reproduced; stickiness 0 gives
      exactly the flexible-price results; with stickiness 0.7 a construction cut lowers consumer prices less, and an import
      price rise passes through to consumer prices as with flexible prices (within 1%); the accounts close (Walras); in the
      dynamic model a zero shock reproduces the no-shock path.
  S4  Updated SAM (0.3.8, 17 Oct 2026): tools/update_sam.py rebuilds the 2024 and 2025 files exactly;
      each balances; every control total (value added of PSA's 16 industries; household and government consumption, fixed
      capital formation, exports, imports, each = the 2023 SAM value x PSA nominal growth) is met; the CGE ("0.3 recommended",
      rice split, sam_year) reproduces each SAM at its benchmark; leaving sam_year out gives the 2023 SAM exactly.
  S5  PSA-consistent SAM (0.3.9, 18 Oct 2026): tools/build_sam_psa_consistent.py rebuilds the file
      exactly; it balances; household consumption equals PSA's 2023 HFCE; labour income, taxes on products, government
      consumption, investment, exports and imports equal the IFPRI SAM's; capital and land income fall by exactly the fall in
      household consumption; the CGE ("0.3 recommended", rice split, sam_variant='psa') calibrates and reproduces the SAM;
      leaving sam_variant out gives IFPRI's SAM. The 2024 and 2025 SAMs updated from it (update_sam.py --base
      psa) rebuild exactly, meet their controls and calibrate (sam_variant='psa' with sam_year).
  S6  Infinity GEM's own 2023 SAM, latest version (0.5 since 0.3.10, the DEFAULT for rice=True runs; 18 Oct 2026): tools/build_own_sam_2023.py rebuilds the
      file exactly; it balances; PSA's 2023 GDP and its six expenditure items are reproduced; value added and labour income
      equal their targets for each of PSA's 16 industries; each household group's consumption, wages and transfers from
      abroad equal its FIES 2023 share; household consumption by COICOP division equals PSA's 2023 HFCE by purpose (v0.3);
      the CGE (sam_variant='own') calibrates and reproduces the SAM; and in the 2026 scenarios' short-run closure a 10% cut in construction investment solves with a real GDP fall between 0 and 3% (a first build
      with a degenerate pulses activity failed this).
  LG1 Labour path option (0.3.9, review D3): psa_labour_growth's default (y2026='observed') is unchanged; with
      y2026='trend' total 2026 employment grows with PSA's projected population 15+ (the 2027-2030 rule).
  ML2 MicroLink concordance (0.3.9, 18 Oct 2026; the default since that morning): on the "0.3
      recommended" split SAM the default map gives chemicals no weight in UTILITIES and TRANSPORT (fuel_split_map=False still
      gives the old map, CATEGORY_MAP itself, for the 2026 scenario numbers of 17 Oct 2026); with the default, all household consumption is
      still attributed, and every price +10% moves every category and family +10%; on a SAM without refined petroleum
      the map is the same either way.
  PC1 Consumer prices on PSA's CPI weights (0.3.10, 18 Oct 2026; reporting only, infinity_gem/psa_cpi.py): the
      mapped 2018-based weights sum to 100 (all households, bottom 30%); a no-shock link gives zero; every price +10% gives
      +10%.
  X3  DSGE research code (0.3.11, 19 Oct 2026; research/dsge/, not used by any Infinity GEM result): the QZ
      solver against closed forms (Gali's NK model, Brock-Mirman), the Gali-Monacelli small open economy (isomorphism, UIP),
      import-price pass-through (Monacelli 2005), and the Kalman likelihood against the exact Gaussian likelihood; also milestones
      5, 6, 8, 10 (rule-of-thumb price setters, Gali and Gertler 1999: omega = 0 = soe_med, paths obey the hybrid curve) and 11
      (hand-to-mouth households and partly adaptive expectations: both 0 = soe_rot; identities; signs; determinacy).
  HD1 Paid labour hoarding (0.3.11, 19 Oct 2026; cge.py 'hoarding', dynamic.py 'hoarding'): with no reference
      labour the option changes nothing; with h = 0.8 and a 20% cut in construction investment (Keynesian closure) the
      model solves, Walras' law holds, the rebuilt SAM balances (hoarded wages paid out of capital income), construction
      sheds fewer workers than without hoarding, and a tampered SAM (hoarded wages not taken from capital) is caught.
  IR1 Interest-rate closure (0.3.11, 20 Oct 2026; cge.py closure='interest', MANAGE-WB's bond
      market): at the benchmark r = 0 and the solution equals the investment closure's; with eps = 0 it equals the savings
      closure and with theta = 0 the investment closure (r re-labels the adjustment); a 10% construction cut lowers r and
      crowds in other investment; in the dynamic model a zero shock reproduces the baseline.
  MK1 Markup pricing in the short run (0.3.13, 22 Oct 2026; cge.py pricing='markup', dynamic.py
      sr_pricing='markup'; design note a design note (not included), tests 1-3): the
      benchmark and the SAM are reproduced; in the dynamic hybrid a zero shock reproduces the baseline (markup with sectoral
      stickiness); after an oil shock every nominal anchor +10% gives every price +10% and quantities unchanged; the markup
      prices' response to the world price of refined petroleum equals the input-output price model's written on the SAM's own
      coefficients (given the flexible prices; with mk_pass 0, the margin per unit fixed, the plain cost-push model of I1's
      formula), and a demand change moves them only through the flexible prices; Walras' law,
      the GDP identity and the rebuilt SAM hold; a tampered SAM (capital paid its benchmark rent, not the residual) is caught;
      a construction cut lowers prices less and GDP more than with flexible prices. With the option off: check R0.
  CS1 Short-run consumption rule (0.3.13, 22 Oct 2026, a design note (not included); dynamic.py
      sr_consumption={"htm": lam}): on Infinity GEM's own SAM with the 2026 scenarios' engine (wage curve, hoarding 0.85) and a 2026 oil and
      construction shock, lam 1 reproduces the engine without the rule (every year); a zero shock with the rule reproduces the
      baseline; at lam 0.62 total household spending equals the rule's formula (recomputed here) and the wage curve's fixed point
      holds jointly, consumption falls less and households save less; with the employment cap binding the rule still holds;
      homogeneity: the year's nominal anchors (peso, peso wage anchors, world prices in pesos, the rule's baseline spending and
      price reference) +10% give every price +10% with quantities and later years unchanged, also with the rule's reference held
      at its real value; a tampered rule (CPI term dropped) is caught; the guards refuse what the rule is not defined for.
  ER1 Incomplete pass-through of the peso to import prices (0.3.13, 23 Oct 2026, P2(b) of docs/design/MARKUP_DEMAND_SIDE_
      PROPOSAL_22Oct2026.md; cge.py shock keys 'erpt' and 'exr_ref', dynamic.py sr_erpt): in the static short-run model (flexible
      and markup prices) and in the dynamic hybrid (Infinity GEM's own SAM, the 2026 scenarios' engine), phi 1 reproduces the option off and a zero
      shock the baseline; after a depreciation with an oil shock every import price equals pwm x exr_ref x (EXR / exr_ref) ** phi
      x (1 + tm) (recomputed here; oil and crude at phi 1) and the current account pays the suppliers' US$ price for imports sold
      here and the world price for re-exports; Walras' law, the GDP identity and the rebuilt SAM hold; consumer prices rise less
      than with full pass-through, and phi 0 leaves non-oil import prices where they were; homogeneity (every nominal anchor,
      the reference peso among them, +10%: prices +10%, quantities unchanged; in the dynamic model via the baseline year solved
      at a 10% higher price level); a tampered rule (suppliers anchored to the benchmark peso, not the year's) is caught; the
      guards refuse what the option is not defined for.
  MG1 A markup pass-through that depends on the output gap (0.3.13, 23 Oct 2026, P6 of the same note; cge.py shock keys
      'mk_gap' and 'mk_gdp', dynamic.py sr_markup_gap): in the static short-run model with markup pricing, slope 0 is the option
      off, the reference real GDP is the benchmark's (as gdp()), the rule with slope s at its solved output gap equals the constant
      pass-through mk_pass + s x gap (the same solution), and after an oil shock every markup home price equals AVC + mu x (A /
      (1 + mu) + (mk_pass + s x gap) x (AVC - A / (1 + mu))) (recomputed here, unit variable cost too); consumer prices rise less
      and GDP falls less than with slope 0; Walras' law, the GDP identity, the rebuilt SAM and homogeneity hold. In the dynamic
      hybrid (option (c): markup with stickiness by sector, mk_pass 0, the 2026 scenarios' engine) a zero shock with every new option on
      (the consumption rule, partial pass-through of the peso, this rule) reproduces the baseline; the rule holds in the solved
      year against the baseline year's real GDP; homogeneity with every option on; a tampered rule (the gap measured against the
      benchmark's GDP, not the year's baseline) is caught; the guards refuse what the option is not defined for.
  SL1 Slack at the start of short-run years (0.3.13, 23 Oct 2026, step 1 of a design note (not included),
      section 3; dynamic.py sr_labour_slack, lfs_natural_rate, lfs_labour_slack): the natural rate of unemployment (the HP trend
      with quarter effects of PSA's four quarterly LFS rounds, COVID quarters out, to 2025Q4) recomputed here as one stacked
      least-squares problem, and its regression value 4.510% (the 2019Q4 trend at the top of BSP DP 2024-11's NAIRU band); the
      baseline's unemployment and the slack by year recomputed; in the dynamic hybrid (Infinity GEM's own SAM, the 2026 scenarios' engine) slack 0 is
      the option off exactly and a zero shock with the slack reproduces the baseline; after a demand boom every capped labour type
      is employed at the baseline's employment x (1 + s), none above; a 1% weaker peso raises consumer prices less and GDP more
      than with the cap at the baseline's employment; homogeneity; a tampered engine that ignores the slack is caught; the guards
      refuse what the option is not defined for.
  EC1 An employment cap that settles (0.3.13, 23 Oct 2026, step 2 of the same note; cge.py labour_cap, dynamic.py
      employment_cap='smooth'): in the static short-run model (Infinity GEM's own SAM, all skills on fixed wages) the benchmark is reproduced
      with no premium; below the cap the model equals the model without the option; after a demand boom every capped type's
      productive employment equals its supply, the wage premium is positive, and the solution equals the market-clearing model
      (those types off fixed wages; exact without paid hoarding, within hoarding's smoothing, eps / 2 of supply, with it);
      complementarity, Walras' law, the GDP identity and homogeneity hold. In the dynamic hybrid (the 2026 scenarios' engine) a zero shock
      reproduces the baseline and the smooth cap equals the switching cap after a slump and a boom, also with the consumption rule
      (whose rule still holds with the cap binding); homogeneity; under option (c) with the consumption rule the BSP rule inside
      the path converges (monetary_scenario); a tampered cap (left at the benchmark's labour supply, not the year's) is caught; the
      guards refuse what the option is not defined for.
  OP1 A within-year share of the world oil price reaching domestic prices (0.3.13, 23 Oct 2026, next step 1 in a review note (not included); cge.py shock keys 'oil_pass' and 'oil_ref', dynamic.py sr_oil_pass): in
      the static short-run model (Infinity GEM's own SAM, flexible and markup prices) and in the dynamic hybrid (the 2026 scenarios' engine), omega 1
      reproduces the option off exactly and a zero shock the baseline (in the dynamic model also with sr_erpt on); after an oil
      shock with a weaker peso the import prices of oil and crude equal R x (pwm x EXR / R) ** omega x (1 + tm) plus the margin
      (recomputed here; R the benchmark's world price in pesos, in the dynamic model the baseline year's), every other import price is
      the world price, the government's absorption equals (pwm x EXR - domestic price) x QM and the import tax the tariff on the
      domestic price less it, and the current account pays world prices; Walras' law, the GDP identity and the rebuilt SAM hold; the
      fuel price rises less and government saving falls; omega 0 holds the domestic price at R; homogeneity (every nominal anchor, R
      among them, +10%; in the dynamic model via the baseline year solved at a 10% higher price level); a tampered reference (the
      benchmark's world price instead of the baseline year's) is caught; the guards refuse what the option is not defined for.
  S7  Infinity GEM's own 2023 SAM, version 0.6 (0.3.13, 23 Oct 2026; research, opt-in: settings sam_variant=
      'own-0.6' or paths.sam_own("0.6"); a review note (not included), section 3): runs
      checks/test_own_sam_v06.py (20 checks: the builder rebuilds the file, it balances, every balancing control is met, PSA's
      GDP, spending items, value added, labour and sector accounts, FIES group shares and consumption by purpose hold, saving
      positive in every group, the CGE calibrates and reproduces it, a short-run construction cut lowers GDP; v0.5 still the
      default).
  S10 Infinity GEM's own 2023 SAM, version 0.7 (0.3.13, 24 Oct 2026; research, opt-in: paths.sam_own("0.7"), reached only by naming it):
      v0.5e with coal split out of mining into its own activity and commodity (acoal, ccoal), so the oil shock no longer moves coal
      at crude's share; runs checks/test_own_sam_v07.py (every Infinity GEM SAM file the builder makes rebuilds exactly and the older files
      keep their sha256; v0.7 balances and gives v0.5e back when coal is added to mining; PSA's totals, value added and labour by
      industry, FIES shares and consumption by purpose hold on it; the coal account; the CGE calibrates and reproduces it and the
      dynamic model's zero shock reproduces its baseline; the engine's coal entries (oil shock, elasticities, LES, MicroLink,
      dynamic lists) leave every other SAM's numbers as they were; the opt-in coal and LNG prices and their refusals; v0.5 still
      the default).
  S11 Infinity GEM's own 2023 SAM, version 0.7b (0.3.13, 24 Oct 2026; research, opt-in: paths.sam_own("0.7b"), reached only by naming
      it): v0.7 without its coal double count (basic metals' coal at IEA volumes; coal imports lower and refined-oil imports
      higher by the same amount, that oil to its other users; value added by activity as v0.5e's); runs checks/test_own_sam_v07b.py
      (every Infinity GEM SAM file the builder makes, v0.7 included, rebuilds exactly and keeps its sha256; v0.7b rebuilds, balances and
      gives its own v0.5e-level table back when coal is added to mining; every control, PSA's totals, value added and labour by
      industry, FIES shares and purposes hold; the double count's targets; the CGE calibrates and reproduces it, the dynamic
      model's zero shock; the World Bank coal and LNG paths and their shock; the v0.5 coal-and-LNG equivalent; v0.5 still the
      default).
  S12 Infinity GEM's own 2023 SAM, version 0.9 (0.3.13, 24 Oct 2026; research, opt-in: paths.sam_own("0.9"), reached only by naming
      it): a customs-anchored coal and fuel account built from v0.7 (coal, crude, LNG and refined imports and coal exports
      at PSA's 2023 customs records; v0.7's coal reallocated to power plants, exports and cement; one coal price for the
      IEA-volume users); runs checks/test_own_sam_v09.py (earlier SAM files keep their sha256 and rebuild; v0.9 rebuilds,
      balances, meets the customs targets; v0.7 back with the step off; the CGE calibrates and reproduces it; the dynamic
      model's zero shock; v0.5 still the default).
  SD1 Stochastic outlook, opt-in typhoon draw (0.3.13, 23 Oct 2026 (d); infinity_gem/stochastic.py
      DisasterDraw; a review note (not included), section 2): runs
      validation/stochastic_disasters/test_disaster_draw.py (9 tests: off by default, calibration recomputed from the PAGASA
      file, tail check against PAGASA's rankings, zero variance = baseline, one typhoon year = the hand-built scenario, refusals).
  X2  (18 Oct 2026: also the Keynesian year of Build 2 against cge.py's Keynesian closure, with a tamper test, and Build 1's
      foreign-saving bridge: 2023 borrows the SAM's temporary excess of foreign saving, the debt stays bounded.)
  X2  Forward-looking CGE (0.3.9, the forward-looking CGE; research/intertemporal/, not used by any Infinity GEM result): the
      stacked solver matches the Brock-Mirman closed form and the Blanchard-Kahn linear solution (second order); the
      9-sector model's steady state reproduces the condensed 2023 SAM and a no-shock path stays put (defaults, the data
      calibration with ten household groups, and with public capital); its within-year block equals cge.py (closure
      'investment', capital 'fixed') for an oil-price and a remittance shock.
  R0  With default settings, 21 key results (SAM multiplier, I-O, static CGE in three closures, dynamic freeze
      path, Simulator short-run CGE and poverty) equal those of Infinity GEM 0.2, the version behind every result
      published up to 7 Oct 2026 (frozen in checks/reference_live.json, computed with 0.2 on 1 Oct 2026;
      0.2 itself is kept in an archived copy of the earlier version). Upgrades must be opt-in.
"""
from __future__ import annotations

import datetime as dt
import re
import sys
import traceback
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):   # 0.3.4 (14 Oct 2026): a '₱' in a detail line crashed the run when output went to a file
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from infinity_gem import paths                                     # noqa: E402
from infinity_gem.sam import SAM, file_checksum                    # noqa: E402

results = []


def _label(ok):
    return "NOT RUN" if ok is None else "PASS" if ok else "FAIL"


# Public version (Infinity GEM): some inputs may not be redistributed (licensed microdata, compiled panels and reference
# tables). A check that needs one of them is reported NOT RUN, with the file and where to get it, until you add the file
# yourself; everything else about the check is unchanged (a crash is still a failure). PSA's input-output tables and the
# LFS employment file are included; the entries for them stay, so a copy without them reports NOT RUN instead of failing.
_UNDISTRIBUTED = {
    "FIES": ([lambda: paths.FIES_PUF, lambda: paths.FIES_POVLINES],
             "PSA's FIES 2023 public-use file and poverty-line extract (licensed by PSA to each user; data/raw/fies/README.md)"),
    "FIES-LFS": ([lambda: paths.FIES_LFS_MEMBERS],
                 "PSA's FIES-LFS 2023 household-member file (licensed by PSA to each user; data/raw/fies/README.md)"),
    "IO80": ([lambda: paths.IO_2018, lambda: paths.DATA_RAW / "io" / "80-Industry20Matrix202018.xlsx"],
             "PSA's 2018 80-industry input-output tables B.1 and B.3 (download from PSA; data/raw/io/README.md)"),
    "IO16": ([lambda: paths.IO_2018_16, lambda: paths.DATA_RAW / "io" / "16-Industry20Matrix202018.xlsx"],
             "PSA's 2018 16-industry input-output tables A.1 and A.3 (download from PSA; data/raw/io/README.md)"),
    "IO240": ([lambda: paths.DATA_RAW / "io" / "240-Industry20Table202018.xlsx"],
              "PSA's 2018 240-industry input-output table C.1 (download from PSA; data/raw/io/README.md)"),
    "LFS-IND": ([lambda: paths.DATA_RAW / "lfs" / "LFS_2025_employed_by_major_industry.csv"],
                "PSA LFS 2025 employment by major industry group (compile it from PSA OpenSTAT; data/raw/lfs/README.md)"),
    "MACRO-Q": ([lambda: paths.MACRO_QUARTERLY],
                "a quarterly macro panel compiled from PSA, BSP and world series (not distributed; data/raw/macro/README.md)"),
    "MACRO-M": ([lambda: paths.MACRO_MONTHLY],
                "a monthly macro panel compiled from BSP and world series (not distributed; data/raw/macro/README.md)"),
    "REF-H2": ([lambda: ROOT / "validation" / "household_detail" / "reference_task2_group_effects_central.csv"],
               "an earlier decile table and PSA retail prices used as references (not distributed)"),
    "REF-V6": ([lambda: ROOT / "validation" / "var_task1" / "reproduce_task1_var.py"],
               "an earlier VAR estimate used as a regression reference (not distributed)"),
    "ELEC-FUEL": ([lambda: paths.DATA_PROCESSED / "electricity_fuel_mix_inputs_2014-2023.csv"],
                  "the electricity fuel-mix inputs of own SAM v0.6e and later (they include GTAP 10A energy volumes, which the "
                  "GTAP licence does not allow us to distribute; research/electricity_fuel_mix/fuel_mix_evidence.py writes them)"),
    "SAM-TESTS": ([lambda v=v: ROOT / "checks" / f"test_own_sam_v{v}.py" for v in ("05e", "06", "06e", "07", "07b", "08", "09")],
                  "the own SAM's standalone rebuild tests (not in this repository: they rebuild the SAM files from the "
                  "licensed FIES and FIES-LFS aggregates; the SAM files themselves are in data/processed)"),
    "PAGASA": ([lambda: paths.DATA_RAW / "disasters" / "PAGASA_ARTC_typhoon_damage_events_and_seasons_2017-2023.csv"],
               "a table of typhoon damage compiled from PAGASA's Annual Reports on Philippine Tropical Cyclones (PAGASA's terms "
               "ask for written permission to reproduce them; data/raw/disasters/README.md)"),
}
_NEEDS = {"P1": ["FIES"], "V1": ["MACRO-Q"], "I1": ["IO80"], "I2": ["IO80", "LFS-IND"], "A1": ["FIES"],
          "I3": ["IO80"], "I4": ["IO80"], "I5": ["IO80", "IO16", "LFS-IND"], "S1": ["IO240"], "H2": ["FIES", "REF-H2"],
          "H3": ["FIES", "FIES-LFS"], "A2": ["FIES"], "V6": ["REF-V6"], "X1": ["MACRO-M"], "ML1": ["FIES"],
          "S3": ["IO240", "MACRO-Q"], "S5": ["IO16", "IO80"], "S6": ["FIES", "FIES-LFS", "IO16"], "ML2": ["FIES"], "PC1": ["FIES"],
          # 24 Oct 2026 (0.3.13.dev3): the own SAM v0.6-v0.7b tests rebuild the SAM files (FIES and FIES-LFS aggregates;
          # from v0.6e the electricity fuel-mix inputs); the typhoon draw is calibrated on the PAGASA-based table
          "S7": ["FIES", "FIES-LFS", "IO240", "SAM-TESTS"], "S10": ["FIES", "FIES-LFS", "IO240", "ELEC-FUEL", "SAM-TESTS"],
          "S11": ["FIES", "FIES-LFS", "IO240", "ELEC-FUEL", "SAM-TESTS"], "SD1": ["PAGASA"],
          # 25 Oct 2026 (0.3.13.dev4): S12 runs the own SAM v0.9's test (v0.9 is built from v0.7, which has the fuel-mix correction)
          "S12": ["FIES", "FIES-LFS", "IO240", "ELEC-FUEL", "SAM-TESTS"]}


def _missing_inputs(code):
    """'' if every input the check needs is here, else what is missing and where to get it (public version)."""
    out = []
    for key in _NEEDS.get(code, []):
        files, what = _UNDISTRIBUTED[key]
        if not all(Path(f()).exists() for f in files):
            out.append(what)
    return "; ".join(out)


def check(code, title):
    def deco(fn):
        def run():
            missing = _missing_inputs(code)
            if missing:
                results.append((code, title, None, f"NOT RUN: needs {missing}"))
                print(f"[NOT RUN] {code} {title}: needs {missing}")
                return
            try:
                ok, detail = fn()
            except Exception as e:                            # a crash is a failure
                ok, detail = False, f"ERROR: {e!r}\n{traceback.format_exc(limit=2)}"
            results.append((code, title, ok, detail))                     # ok: True, False, or None = NOT RUN
            print(f"[{_label(ok)}] {code} {title}: {detail.splitlines()[0] if detail else ''}")
        return run
    return deco


@check("D1", "data checksums")
def d1():
    inv = (ROOT / "data" / "DATA_INVENTORY.md").read_text(encoding="utf-8")
    rows = re.findall(r"\|\s*`([^`]+)`\s*\|[^|]*\|[^|]*\|\s*`([0-9a-f]{64})`\s*\|", inv)
    bad = [p for p, h in rows if file_checksum(ROOT / "data" / "raw" / p) != h]
    return (len(rows) > 0 and not bad), f"{len(rows)} files checked; mismatches: {bad or 'none'}"


@check("D2", "SAM balance")
def d2():
    out = []
    for p in (paths.SAM_2018, paths.SAM_2023):
        r = SAM.load(p).check(verbose=False)
        out.append((p.name, r["max_row_col_gap"], r["balanced"]))
    # the 2018 SAM is published in whole billions, so it balances only to within rounding (about 5)
    ok = out[1][2] and out[0][1] < 6
    return ok, "; ".join(f"{n}: max gap {g:.3g}" for n, g, _ in out)


@check("D3", "an edited SAM is refused, not balanced away")
def d3():
    # 0.3.3 (rigging audit finding 2): a copy of the 2023 SAM with one cell raised by ₱1 bn must be refused by
    # SAM.load_for_model (it is not declared as rounded); the 2018 SAM (published in rounded figures) is still balanced
    import shutil
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="infinity_gem_d3_"))
    try:
        p = tmp / paths.SAM_2023.name
        shutil.copy2(paths.SAM_2023, p)
        import csv
        with open(p, encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.reader(fh))
        cells = rows[1]
        j = next(k for k in range(2, len(cells)) if cells[k].strip() and float(cells[k]) > 10)
        cells[j] = repr(float(cells[j]) + 1.0)
        with open(p, "w", encoding="utf-8-sig", newline="") as fh:
            csv.writer(fh).writerows(rows)
        try:
            SAM.load_for_model(p)
            refused, msg = False, "the edited SAM was accepted"
        except ValueError as e:
            refused, msg = True, str(e).split(". If")[0]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    s18 = SAM.load_for_model(paths.SAM_2018)
    ok18 = s18.check(tol=1e-6, verbose=False)["balanced"]
    return refused and ok18, f"edited 2023 SAM (+₱1 bn in one cell) refused: {refused} ({msg}); 2018 SAM still balanced: {ok18}"


@check("M1", "SAM multipliers reproduce September 2026 results")
def m1():
    from infinity_gem.multiplier import SAMMultiplier
    import pandas as pd
    vals = {}
    for yr, p in ((2018, paths.SAM_2018), (2023, paths.SAM_2023)):
        pop = pd.read_csv(p.parent / f"003_IFPRI_SAM_PHL_{yr}_POP.csv", encoding="utf-8-sig", skiprows=1 if yr == 2023 else 0)
        pop.columns = ["name", "code", "num", "shr"][: len(pop.columns)]
        ps = {}
        for _, r in pop.iterrows():
            c = str(r["code"]).lower()
            for a, full in (("r", "rur"), ("u", "urb")):
                for q in range(1, 6):
                    if c in (f"h_{full}{q}", f"hhd-{a}{q}"):
                        ps[f"hhd-{a}{q}"] = float(str(r["num"]).replace(",", ""))
        q12 = ["hhd-r1", "hhd-u1", "hhd-r2", "hhd-u2"]
        mult = SAMMultiplier(SAM.load(p))
        vals[yr] = (mult.household_income_multiplier({"hhd-r1": .5, "hhd-r2": .3, "hhd-u1": .2}),
                    mult.household_income_multiplier({h: ps[h] / sum(ps[k] for k in q12) for h in q12}))
    exp = {2018: (2.170, 2.162), 2023: (2.200, 2.197)}      # the September 2026 run log (published values)
    ok = all(abs(vals[y][i] - exp[y][i]) < 0.0005 for y in exp for i in (0, 1))
    return ok, "; ".join(f"{y}: 50/30/20 {vals[y][0]:.3f} (exp. {exp[y][0]:.3f}), bottom 40% {vals[y][1]:.3f} (exp. {exp[y][1]:.3f})" for y in exp)


def _models():
    from infinity_gem.cge import CGE
    return {"long run (investment closure)": CGE.from_sam(),
            "savings closure": CGE.from_sam(closure="savings"),
            "short run (Keynesian, fixed capital)": CGE.from_sam(closure="keynesian", unemployed=("flab-n", "flab-p"), capital="fixed")}


MODELS = {}


def _need_models():
    """The three models C1 builds. 0.3.3 (found by the rigging audit's tamper test, 10 Oct 2026): if C1 could not build
    them, C3-C5 used to loop over nothing and report PASS; now they fail with the reason."""
    if len(MODELS) != 3:
        raise RuntimeError("the models were not built (check C1 failed), so this check could not test anything")
    return MODELS


@check("C1", "CGE benchmark residuals")
def c1():
    MODELS.update(_models())
    out = []
    for k, m in _need_models().items():
        R, _ = m.evaluate(m.x0(), m.make_shocks())
        out.append((k, float(np.abs(R).max())))
    return all(r < 1e-7 for _, r in out), "; ".join(f"{k}: {r:.1e}" for k, r in out)


@check("C2", "CGE reproduces the SAM")
def c2():
    m = MODELS["long run (investment closure)"]
    s = m.solve()
    gap = float((m.rebuild_sam(s) - m.sam.table).abs().values.max())
    return gap < 1e-5, f"max cell gap {gap:.2e} (₱ bn)"


@check("C3", "homogeneity")
def c3():
    out = []
    for k, m in _need_models().items():
        spec = {"exr": 2.0} if m.closure == "keynesian" else {"cpi": 2.0}
        s = m.solve(spec)
        dq = float(np.abs(s["QA"] / m.QA0 - 1).max())
        dp = float(np.abs(s["PQ"][m.iQ] / 2 - 1).max())
        out.append((k, dq, dp))
    return all(a < 1e-7 and b < 1e-7 for _, a, b in out), "; ".join(f"{k}: dQ {a:.1e}, dP {b:.1e}" for k, a, b in out)


SHOCK = {"pwm_scale": {"cchem": 1.3}, "remit_scale": 0.8, "qinv_scale": {"ccons": 0.8}}


@check("C4", "Walras' law")
def c4():
    out = []
    for k, m in _need_models().items():
        s = m.solve(SHOCK)
        out.append((k, s.ok, abs(s["WALRAS"]) / m.qinv.sum()))
    return all(o and w < 1e-9 for _, o, w in out), "; ".join(f"{k}: solved={o}, slack/investment {w:.1e}" for k, o, w in out)


@check("C5", "GDP identity")
def c5():
    out = []
    for k, m in _need_models().items():
        g = m.gdp(m.solve(SHOCK))
        out.append((k, abs(g["nominal_expenditure"] - g["nominal_income"])))
    return all(x < 1e-6 for _, x in out), "; ".join(f"{k}: gap {x:.1e}" for k, x in out)


@check("C6", "direction of effects")
def c6():
    msgs, ok = [], True
    m = MODELS["long run (investment closure)"]
    b = m.solve()
    s = m.solve({"pwm_scale": {"cchem": 1.2}})
    d1, d2 = m.gdp(s)["real"] / m.gdp(b)["real"] - 1, s["QH"].sum() / b["QH"].sum() - 1
    ok &= d1 < 0 and d2 < 0; msgs.append(f"oil +20%: GDP {d1*100:+.2f}%, consumption {d2*100:+.2f}%")
    s = m.solve({"remit_scale": 0.9}); d = s["QH"].sum() / b["QH"].sum() - 1
    ok &= d < 0; msgs.append(f"remittances -10%: consumption {d*100:+.2f}%")
    k = MODELS["short run (Keynesian, fixed capital)"]
    kb, ks = k.solve(), k.solve({"qinv_scale": {"ccons": 0.9}})
    d = k.gdp(ks)["real"] / k.gdp(kb)["real"] - 1
    ok &= d < 0; msgs.append(f"construction investment -10% (short run): GDP {d*100:+.2f}%")
    return ok, "; ".join(msgs)


@check("C7", "CGE multiplier between zero and the SAM bound")
def c7():
    from infinity_gem.multiplier import SAMMultiplier
    k = MODELS["short run (Keynesian, fixed capital)"]
    kb, ks = k.solve(), k.solve({"qinv_scale": {"ccons": 0.9}})
    cut = 0.1 * k.qinv[k.C.index("ccons")]
    cge_mult = (k.gdp(kb)["real"] - k.gdp(ks)["real"]) / cut
    sm = SAMMultiplier(k.sam0)
    dy = sm.shock({"ccons": 1.0})
    va = sum(dy[f] for f in ("flab-n", "flab-p", "flab-s", "flnd", "fcap"))
    return 0 < cge_mult < va, f"CGE short-run GDP multiplier {cge_mult:.2f}; SAM value-added multiplier {va:.2f}"


@check("Y1", "dynamic baseline and zero-shock scenario")
def y1():
    from infinity_gem.dynamic import DynamicCGE
    d = DynamicCGE()
    b = d.baseline()
    target = np.array([d.growth[t] for t in d.years[1:]])
    got = b.table["real_gdp_growth_pct"].values[1:]
    z = d.scenario({})
    gap = float((z.table.real_gdp - b.table.real_gdp).abs().max())
    return bool(np.abs(got - target).max() < 1e-6 and gap < 1e-6), f"max growth miss {np.abs(got-target).max():.1e} pp; zero-shock gap {gap:.1e}"


@check("P1", "microsimulation baseline = PSA official poor")
def p1():
    from infinity_gem.microsim import Microsim, OFFICIAL_POOR_2023
    b = Microsim().baseline()
    return abs(b["poor"] / OFFICIAL_POOR_2023 - 1) < 0.001, f"{b['poor']/1e6:.3f}M poor ({b['rate_pct']:.2f}%) vs PSA 17.54M"


@check("V1", "VAR module: Reference VAR coefficients used by the geopolitics shock (regression guard)")
def v1():
    from infinity_gem import var
    df = var.load_macro()
    fx = var.newey_west(df, "fx", ["gpr", "oil"])["table"].loc["gpr", "coef"]
    fdi = var.newey_west(df, "fdi", ["gpr", "oil"])["table"].loc["gpr", "coef"]
    return abs(fx - 0.0078) < 5e-5 and abs(fdi + 0.0600) < 5e-5, f"b(gpr): fx {fx:+.4f} (expected +0.0078), fdi {fdi:+.4f} (expected -0.0600)"


@check("I1", "I-O model: Leontief inverse = PSA Table B.3 (validation); price and demand regression values")
def i1():
    from infinity_gem.iomodel import IOTable
    import pandas as pd
    io = IOTable()
    li = pd.read_excel(paths.IO_2018.parent / "80-Industry20Matrix202018.xlsx", header=None)
    r0 = next(i for i in range(len(li)) if str(li.iloc[i, 1]).strip() == "Palay")
    gap = float(np.nanmax(np.abs(li.iloc[r0:r0 + 80, 2:82].apply(pd.to_numeric, errors="coerce").values - io.L)))
    ps = io.price_summary({"Coke and refined petroleum products": 0.10})
    va = io.quantity({"Construction": -238.3}, "domestic")["va_bn"]
    ok = gap < 1e-6 and abs(ps["cpi"] * 100 - 0.6832) < 5e-4 and abs(ps["ppi"] * 100 - 0.8051) < 5e-4 and abs(va + 161.5) < 0.05
    return ok, (f"inverse vs PSA Table B.3: max gap {gap:.1e}; petroleum +10%: CPI +{ps['cpi']*100:.4f} pp (regression value 0.6832), "
                f"PPI +{ps['ppi']*100:.4f} pp (0.8051); construction -₱238.3 bn, domestic inverse: GDP {va:,.1f} (regression value -161.5)")


@check("I2", "I-O job-equivalents: regression values (fixed-price upper bound)")
def i2():
    from infinity_gem.iomodel import IOTable
    io = IOTable()
    q = io.quantity({"Construction": -242.93}, "domestic", gdp_other_year=28060)     # an earlier estimate: shock and 2025 GDP it used
    j = io.jobs(q["industries"]["output (%)"])
    c, t = float(j.loc["Construction", "job-equivalents"]), float(j["job-equivalents"].sum())
    ok = abs(c / -254226 - 1) < 0.005 and abs(t / -320934 - 1) < 0.005
    return ok, f"construction {c:,.0f} (reference -254,226), all industries {t:,.0f} (reference -320,934); tolerance 0.5%"


@check("A1", "simulator engines reproduce the scenario scripts")
def a1():
    sys.path.insert(0, str(ROOT))
    from app import engines as E
    s = E.Shocks(construction_bn=-238.3)
    sr = E.run_cge(s, "short run")["summary"]
    sm = E.run_sam(s)["summary"]
    ay = E.run_sam(E.Shocks(transfers_bn=-90.21))["summary"]
    to_sam = lambda x: x / E.PSA_GDP[2025] * E.SAM_GDP_2023
    gdp_ok = abs(E.sam_gdp(E.sam_model(2023).sam) - E.SAM_GDP_2023) < 1e-3
    ok = (gdp_ok and abs(sr["Real GDP (%)"] + 0.279) < 5e-4 and abs(sr["New poor (persons, FIES 2023 base)"] - 497479) < 1
          and abs(to_sam(sm["GDP (value added, ₱ bn)"]) + 350.223) < 0.01 and abs(to_sam(ay["Household income (₱ bn)"]) + 185.06) < 0.01)
    return ok, (f"infrastructure short-run CGE: GDP {sr['Real GDP (%)']:+.3f}% (script -0.279), new poor {sr['New poor (persons, FIES 2023 base)']:,.0f} "
                f"(497,479); SAM: GDP {to_sam(sm['GDP (value added, ₱ bn)']):,.2f} (-350.22, SAM units); Ayuda household income "
                f"{to_sam(ay['Household income (₱ bn)']):,.2f} (-185.06); SAM GDP identity {'ok' if gdp_ok else 'FAILED'}")


@check("R0", "default results equal Infinity GEM 0.2 (the published results)")
def r0():
    import json
    sys.path.insert(0, str(ROOT / "checks"))
    from regression_reference import compute, compare, REF
    ref = json.loads(REF.read_text(encoding="utf-8"))
    got = compute(ROOT)
    # public version: results whose inputs are not distributed (PSA's input-output tables, the FIES microdata) are not
    # computed unless you add those files; they are named here, and every other result is compared exactly as before
    skipped = [k for k in ref if k not in got]
    bad = compare({k: v for k, v in ref.items() if k in got}, got)
    note = f"; not computed on this computer (inputs not distributed): {', '.join(skipped)}" if skipped else ""
    return (not bad and len(got) > 0), (f"{len(ref) - len(skipped)} of {len(ref)} results compared (relative tolerance 1e-9); "
                                        f"differing: {bad or 'none'}{note}")


@check("I3", "I-O identity: primary inputs +10% gives every price +10%")
def i3():
    from infinity_gem.iomodel import IOTable
    io = IOTable()
    dp = io.price_from_primary_inputs(0.10)
    gap = float(np.abs(dp.values - 0.10).max())
    rnd = float(np.abs((io.Z.sum(axis=0) + io.TPI - io.X) / io.X).max())   # PSA's own rounding: inputs + VA vs output
    return gap < 1e-7, f"max deviation from +10% across {io.n} industries: {gap:.1e} (PSA table rounding: {rnd:.1e} of output)"


@check("I4", "I-O identity: one peso of final demand returns one peso")
def i4():
    from infinity_gem.iomodel import IOTable
    io = IOTable()
    tot = io.v @ io.L
    m = ((1 - io.dom_share)[:, None] * io.A).sum(axis=0)          # imported inputs per peso of output
    dom = io.v @ io.Ld + m @ io.Ld
    ok_v = bool(((io.v > 0) & (io.v < 1)).all())
    g1, g2 = float(np.abs(tot - 1).max()), float(np.abs(dom - 1).max())
    return g1 < 1e-7 and g2 < 1e-7 and ok_v, (f"total inverse: value added per peso max gap {g1:.1e}; domestic inverse: "
                                             f"value added + imports max gap {g2:.1e}; value-added shares in (0,1): {ok_v}")


@check("I5", "16-industry I-O table (for LFS microsimulation) reproduces PSA and the identities")
def i5():
    import openpyxl
    from infinity_gem.iomodel import IOTable, load_employment
    io16, io80 = IOTable(paths.IO_2018_16), IOTable()
    ws = openpyxl.load_workbook(paths.DATA_RAW / "io" / "16-Industry20Matrix202018.xlsx", data_only=True, read_only=True).worksheets[0]
    psa = np.array([[float(x) for x in r[2:18]] for r in ws.iter_rows(values_only=True)
                    if r and isinstance(r[0], str) and r[0].strip().isdigit()][:16])
    g_psa = float(np.abs(io16.L - psa).max())                        # PSA Table A.3 (published to 10+ decimals)
    m = ((1 - io16.dom_share)[:, None] * io16.A).sum(axis=0)
    g_tot = float(np.abs(io16.v @ io16.L - 1).max())
    g_dom = float(np.abs(io16.v @ io16.Ld + m @ io16.Ld - 1).max())
    g_gdp = abs(io16.gdp - io80.gdp) / io80.gdp
    emp16, _ = load_employment(16)
    g_emp = abs(float(emp16["employed_thousand"].sum()) - float(load_employment(80)[0]["employed_thousand"].sum()))
    sys.path.insert(0, str(ROOT / "scenarios"))
    from _common import PSA_GDP
    q16 = io16.quantity({"Construction": -238.3}, "domestic", gdp_other_year=PSA_GDP[2025])
    j16 = float(io16.jobs(q16["industries"]["output (%)"])["job-equivalents"].sum())
    ok = g_psa < 1e-6 and g_tot < 1e-7 and g_dom < 1e-7 and g_gdp < 1e-9 and g_emp < 1e-6 and io16.n == 16
    return ok, (f"16 industries; inverse vs PSA Table A.3 max gap {g_psa:.1e}; total inverse: value added per peso gap {g_tot:.1e}; "
                f"domestic: value added + imports gap {g_dom:.1e}; GDP equals the 80-industry table (rel. gap {g_gdp:.1e}); "
                f"LFS employment kept in the 16-industry sum (gap {g_emp:.1e} thousand). Reference, construction -₱238.3 bn, "
                f"domestic: GDP {q16['va_bn']:.1f} bn, job-equivalents {j16:,.0f} (80 industries: -161.5 bn, -315,816)")


@check("C8", "CGE calibrated to the 2018 SAM passes C1-C5")
def c8():
    from infinity_gem.cge import CGE
    out, ok = [], True
    for name, kw in {"long run": {}, "savings": {"closure": "savings"},
                     "short run": {"closure": "keynesian", "unemployed": ("flab-n", "flab-p"), "capital": "fixed"}}.items():
        m = CGE.from_sam(paths.SAM_2018, **kw)
        r1 = float(np.abs(m.evaluate(m.x0(), m.make_shocks())[0]).max())
        b = m.solve()
        r2 = float((m.rebuild_sam(b) - m.sam.table).abs().values.max())
        h = m.solve({"exr": 2.0} if m.closure == "keynesian" else {"cpi": 2.0})
        r3 = float(np.abs(h["QA"] / m.QA0 - 1).max())
        s = m.solve(SHOCK)
        g = m.gdp(s)
        r4, r5 = abs(s["WALRAS"]) / m.qinv.sum(), abs(g["nominal_expenditure"] - g["nominal_income"])
        ok &= s.ok and r1 < 1e-7 and r2 < 1e-5 and r3 < 1e-7 and r4 < 1e-9 and r5 < 1e-6
        out.append(f"{name}: C1 {r1:.0e}, C2 {r2:.0e}, C3 {r3:.0e}, C4 {r4:.0e}, C5 {r5:.0e}")
    return ok, "; ".join(out)


@check("Y2", "hybrid dynamic closure")
def y2():
    from infinity_gem.dynamic import DynamicCGE
    d = DynamicCGE(hybrid=True)
    b = d.baseline()
    z = d.scenario({2025: {}})
    zgap = float((z.table.real_gdp - b.table.real_gdp).abs().max())
    shock = {2025: {"qinv_scale": {"ccons": 0.9}}}
    s = d.scenario(shock)
    g = s.table["employment_gap_low_skill_pct"]
    rho = d.a["gap_persistence"]
    decay = float(np.abs(g.loc[2026:].values - g.loc[2025] * rho ** np.arange(1, len(g.loc[2026:]) + 1)).max())
    lr = DynamicCGE()
    lr.baseline()
    cum_h = d.compare(b, s).loc["cumulative", "gdp_gap_bn"]
    cum_l = lr.compare(lr.base, lr.scenario(shock)).loc["cumulative", "gdp_gap_bn"]
    ok = zgap < 1e-6 and g.loc[2025] < 0 and decay < 1e-6 and cum_h < cum_l < 0
    return ok, (f"zero-shock gap {zgap:.1e}; construction -10% in 2025: low-skill employment gap {g.loc[2025]:.2f}% then "
                f"x{rho} a year (max deviation {decay:.1e}); cumulative GDP gap hybrid {cum_h:,.1f} vs long run {cum_l:,.1f} (₱ bn)")


@check("Y3", "public capital channel")
def y3():
    from infinity_gem.dynamic import DynamicCGE
    shock = {2025: {"qinv_scale": {"ccons": 0.9}}}
    ref = DynamicCGE()
    rb = ref.baseline()
    r = ref.compare(rb, ref.scenario(shock))
    res = {}
    for phi in (0.0, 0.1, 0.2):
        d = DynamicCGE(public_capital={"phi": phi, "kg_gdp": 1.0})      # kg_gdp: test value only
        b = d.baseline()
        res[phi] = d.compare(b, d.scenario(shock))
        if phi == 0.1:
            zgap = float((d.scenario({2025: {}}).table.real_gdp - b.table.real_gdp).abs().max())
    same = float((res[0.0]["gdp_gap_pct"] - r["gdp_gap_pct"]).abs().max())
    x1 = res[0.1].loc[2030, "gdp_gap_pct"] - r.loc[2030, "gdp_gap_pct"]
    x2 = res[0.2].loc[2030, "gdp_gap_pct"] - r.loc[2030, "gdp_gap_pct"]
    ok = same < 1e-9 and zgap < 1e-6 and x1 < 0 and abs(x2 / x1 - 2) < 0.1
    return ok, (f"phi=0 vs no channel: max gap {same:.1e}; zero shock: {zgap:.1e}; extra 2030 GDP gap from the channel: "
                f"phi 0.1 {x1:+.3f} pp, phi 0.2 {x2:+.3f} pp (ratio {x2 / x1:.2f}; kg_gdp test value 1.0)")


@check("V2", "Infinity GEM reproduces IFPRI's standard CGE (condensed Philippine SAM)")
def v2():
    import runpy, contextlib, io as _io
    argv = sys.argv
    try:                                    # compare.py reads sys.argv[1] as its margins option (18 Oct 2026: a stray
        sys.argv = ["compare.py"]           # command-line argument to this suite made V2 fail; V3 already sets it)
        with contextlib.redirect_stdout(_io.StringIO()):
            g = runpy.run_path(str(ROOT / "validation" / "ifpri" / "compare.py"))
    finally:
        sys.argv = argv
    r = g["res"]
    core = r[(r.group == "MACRO") & r["item"].isin(["RGDP", "RCONS"])]
    m_core, share, m_all = float(core.diff_pp.abs().max()), float((r.diff_pp.abs() < 0.1).mean()), float(r.diff_pp.abs().max())
    ok = m_core < 0.01 and share >= 0.95 and m_all < 0.6
    return ok, (f"real GDP and consumption: max gap {m_core:.4f} pp; {share:.1%} of {len(r)} results within 0.1 pp; "
                f"largest gap {m_all:.3f} pp (trade margins)")


@check("V3", "IFPRI-style trade margins option (margins='split') reproduces IFPRI's model more closely")
def v3():
    import runpy, contextlib, io as _io
    from infinity_gem.cge import CGE
    m = CGE.from_sam(margins="split")
    b = m.solve()
    S = m.rebuild_sam(b)
    gap = float((S - m.sam.table.loc[S.index, S.columns]).abs().values.max())
    h = m.solve({"cpi": 2.0})
    hom = float(np.abs(h["QA"] / m.QA0 - 1).max())
    argv = sys.argv
    try:
        sys.argv = ["compare.py", "split"]
        with contextlib.redirect_stdout(_io.StringIO()):
            g = runpy.run_path(str(ROOT / "validation" / "ifpri" / "compare.py"))
    finally:
        sys.argv = argv
    r = g["res"]
    core = r[(r.group == "MACRO") & r["item"].isin(["RGDP", "RCONS"])]
    m_core, share, m_all = float(core.diff_pp.abs().max()), float((r.diff_pp.abs() < 0.1).mean()), float(r.diff_pp.abs().max())
    ok = gap < 1e-6 and hom < 1e-7 and m_core < 0.001 and share >= 0.99 and m_all < 0.15
    return ok, (f"SAM reproduced to {gap:.1e}; homogeneity {hom:.0e}; vs IFPRI: real GDP and consumption max gap "
                f"{m_core:.4f} pp; {share:.1%} of {len(r)} results within 0.1 pp; largest gap {m_all:.3f} pp")


@check("E1", "elasticity sets calibrate and are homogeneous")
def e1():
    from infinity_gem.cge import CGE
    from infinity_gem.elasticities import elasticity_set
    out, ok = [], True
    for name in ("gtap", "ph", "ph_pcgem_cet"):
        el = elasticity_set(name)
        for cl, kw in {"long": {}, "short": {"closure": "keynesian", "unemployed": ("flab-n", "flab-p"), "capital": "fixed"}}.items():
            m = CGE.from_sam(elasticities=el, **kw)
            # 0.3.7: the sets also carry the split SAMs' accounts, so test coverage (every account has a value), not counts
            full = all(set(codes) <= set(el[k]) for k, codes in (("sigma_va", m.A), ("sigma_q", m.C), ("omega_t", m.C)))
            r1 = float(np.abs(m.evaluate(m.x0(), m.make_shocks())[0]).max())
            h = m.solve({"exr": 2.0} if m.closure == "keynesian" else {"cpi": 2.0})
            r3 = float(np.abs(h["QA"] / m.QA0 - 1).max())
            ok &= full and r1 < 1e-7 and r3 < 1e-7
            out.append(f"{name}/{cl}: {r1:.0e}, {r3:.0e}")
    # 0.3.7: the split SAMs (petroleum; petroleum + rice) have a sourced value for every account in the 'gtap' and 'ph' sets
    # (before, their new accounts silently took the generic defaults)
    for sam in (paths.SAM_2023_PETR, paths.SAM_2023_RICE):
        m = CGE.from_sam(sam)
        for name in ("gtap", "ph"):
            el = elasticity_set(name)
            miss = [c for k, codes in (("sigma_va", m.A), ("sigma_q", m.C), ("omega_t", m.C)) for c in codes if c not in el[k]]
            ok &= not miss
            out.append(f"{sam.stem.split('_SAM_')[-1]}/{name}: missing {miss or 'none'}")
    return ok, "benchmark residual, homogeneity: " + "; ".join(out)


@check("Y4", "capital by industry (putty-clay) with the documented baseline")
def y4():
    from infinity_gem.dynamic import DynamicCGE, documented_baseline, DBCC_GROWTH
    d = DynamicCGE(capital_allocation="putty-clay", **documented_baseline())
    b = d.baseline()
    miss = float(np.abs(b.table["real_gdp_growth_pct"].values[1:] - np.array([DBCC_GROWTH[t] for t in d.years[1:]])).max())
    z = d.scenario({2025: {}})
    zgap = float((z.table.real_gdp - b.table.real_gdp).abs().max())
    sh = [d.allocation(b.solutions[t]) for t in d.years]
    shares_ok = all(abs(x.sum() - 1) < 1e-12 and x.min() >= 0 for x in sh)
    g24 = float(b.table.loc[2024, "capital_stock_index"] - 1) * 100
    cv = {}
    for om in (0.0, 1.0, 3.0, 5.0):
        dd = DynamicCGE(capital_allocation="putty-clay", omega=om, **documented_baseline())
        R = dd.baseline().solutions[2030]["W"][dd.kc]
        cv[om] = float(R.std() / R.mean())
    s = d.scenario({2025: {"qinv_scale": {"ccons": 0.9}}})
    ia = d.m.A.index("acons")
    kgap = float(s.capital[2030][ia] / b.capital[2030][ia] - 1) * 100
    mono = cv[0.0] > cv[1.0] > cv[3.0] > cv[5.0]
    ok = miss < 1e-6 and zgap < 1e-6 and shares_ok and 5 <= g24 <= 9 and mono and kgap < 0
    return ok, (f"growth miss {miss:.1e} pp; zero shock {zgap:.1e}; shares ok {shares_ok}; capital growth 2024 {g24:.2f}%; "
                f"rental dispersion 2030 by omega 0/1/3/5: {cv[0.0]:.3f}/{cv[1.0]:.3f}/{cv[3.0]:.3f}/{cv[5.0]:.3f}; construction -10% in 2025: "
                f"construction capital 2030 {kgap:+.2f}% vs baseline")


@check("Y5", "industry baseline reproduces PSA GVA by industry")
def y5():
    from infinity_gem.dynamic import DynamicCGE, documented_baseline, psa_industry_growth, PSA_INDUSTRIES
    tg = psa_industry_growth()
    d = DynamicCGE(capital_allocation="putty-clay", industry_targets=tg, **documented_baseline())
    b = d.baseline()
    m, miss, tfpmax, lev = d.m, 0.0, 0.0, []
    for t in (2024, 2025):
        va, vp = b.solutions[t]["QVA"], b.solutions[t - 1]["QVA"]
        for n, acts in PSA_INDUSTRIES.items():
            ix = [m.A.index(a) for a in acts if a in m.A]
            miss = max(miss, abs((va[ix].sum() / vp[ix].sum() - 1) * 100 - tg[t][n]))
        prev = np.asarray(b.tfp[t - 1], float) if np.ndim(b.tfp[t - 1]) else np.full(len(m.A), float(b.tfp[t - 1]))
        tfpmax = max(tfpmax, float(np.abs(np.asarray(b.tfp[t]) / prev - 1).max()) * 100)
        lev += list(b.demand[t].values())
    gdp = {2024: 5.71, 2025: 4.40}                       # PSA real GDP growth (0052B5BPRA1, constant 2018 prices)
    gmiss = max(abs(b.table.loc[t, "real_gdp_growth_pct"] - g) for t, g in gdp.items())
    z = d.scenario({})
    zgap = float((z.table.real_gdp / b.table.real_gdp - 1).abs().max())
    ok = miss < 1e-6 and gmiss < 0.2 and zgap < 1e-9 and tfpmax < 15 and 0.8 < min(lev) and max(lev) < 1.25
    return ok, (f"industry growth miss {miss:.1e} pp; real GDP vs PSA max gap {gmiss:.3f} pp; zero shock {zgap:.1e}; "
                f"largest TFP change {tfpmax:.1f}%; levers {min(lev):.3f}-{max(lev):.3f}")


@check("L1", "labour growth by skill from PSA")
def l1():
    import pandas as pd
    from infinity_gem import paths
    from infinity_gem.dynamic import DynamicCGE, psa_labour_growth, LABOUR_EDUCATION
    lg = psa_labour_growth()
    lfs = pd.read_csv(paths.DATA_RAW / "lfs" / "PSA_OpenSTAT_LFS_employed_by_highest_grade_2023-2026.csv", comment="#")
    ann = lambda y, k: lfs[(lfs.year == y) & (lfs.month == "Annual") & lfs.highest_grade_completed.isin(LABOUR_EDUCATION[k])].employed_thousands.sum()
    miss = max(abs(lg[y][k] - (ann(y, k) / ann(y - 1, k) - 1)) for y in (2024, 2025) for k in LABOUR_EDUCATION)
    pop = pd.read_csv(paths.DATA_RAW / "population" / "PSA_OpenSTAT_population_projections_2020CPH_2020-2030.csv", comment="#")
    p15 = pop[(pop.sex == "Both Sexes") & ~pop.age_group.isin(["All Ages", "0-4", "5-9", "10-14"])].groupby("year").population_thousands.sum()
    lvl = np.array([ann(2025, k) for k in LABOUR_EDUCATION]) * (1 + np.array(list(lg[2026].values())))
    pmiss = 0.0
    for y in range(2027, 2031):
        new = lvl * (1 + np.array(list(lg[y].values())))
        pmiss = max(pmiss, abs(new.sum() / lvl.sum() - p15[y] / p15[y - 1]))
        lvl = new
    d = DynamicCGE(labour_growth=lg)
    b = d.baseline()
    k = d.m.F.index("flab-s")
    cum = np.prod([1 + lg[y]["flab-s"] for y in range(2024, 2031)])
    smiss = abs(b.solutions[2030]["EMP"][k] / d.m.QFS0[k] - cum)
    ok = miss < 1e-12 and pmiss < 1e-12 and smiss < 1e-8
    return ok, (f"LFS growth miss {miss:.1e}; total vs population 15+ {pmiss:.1e}; model high-skill supply 2030 miss {smiss:.1e}; "
                f"growth 2025 low/medium/high {lg[2025]['flab-n']*100:.2f}/{lg[2025]['flab-p']*100:.2f}/{lg[2025]['flab-s']*100:.2f}%")


@check("H1", "LES household demand calibrates and behaves")
def h1():
    from infinity_gem.cge import CGE
    from infinity_gem.demand import les_briones2023
    les = les_briones2023()
    out, ok = [], True
    for name, kw in (("long", {}), ("short", dict(closure="keynesian", unemployed=("flab-n", "flab-p"), capital="fixed"))):
        m = CGE.from_sam(les=les, **kw)
        b = m.solve()
        S = m.rebuild_sam(b)
        gap = float((S - m.sam.table.loc[S.index, S.columns]).abs().to_numpy().max())
        s = m.solve({"cpi": 1.1}) if name == "long" else None
        hom = float(np.abs(s["QA"] / b["QA"] - 1).max()) if s is not None else 0.0
        engel = float(np.abs(m.les["mb"].sum(axis=0) - 1).max())
        sub_ok = bool((m.les["gamma"] <= m.sam.table.loc[m.C, m.H].values + 1e-9).all())
        fr = m.les["frisch"]
        ok &= b.ok and gap < 1e-6 and hom < 1e-8 and engel < 1e-12 and sub_ok and fr.min() > -3 and fr.max() < -0.5
        out.append(f"{name}: SAM gap {gap:.1e}, homogeneity {hom:.1e}, Engel {engel:.1e}, Frisch {fr.min():.2f} to {fr.max():.2f}")
    cd, le = CGE.from_sam(), CGE.from_sam(les=les)
    i = cd.C.index("cfood")
    d = {}
    for nm, mm in (("CD", cd), ("LES", le)):
        b0, s1 = mm.solve(), mm.solve({"pwm_scale": {"cchem": 1.12}})
        d[nm] = (s1["QH"][i].sum() / b0["QH"][i].sum() - 1) * 100
    ok &= d["LES"] > d["CD"]
    from infinity_gem.demand import les_usda2011, usda_frisch      # benchmark: USDA ERS (Muhammad et al. 2011)
    mu = CGE.from_sam(les=les_usda2011())
    bu = mu.solve()
    Su = mu.rebuild_sam(bu)
    gu = float((Su - mu.sam.table.loc[Su.index, Su.columns]).abs().to_numpy().max())
    fu = usda_frisch()
    ok &= bu.ok and gu < 1e-6 and -3 < fu < -0.5
    from infinity_gem import demand as _demand                     # benchmark: GTAP 10 (2014, CDE)
    if not _demand.GTAP10.exists():                             # public version: GTAP data are licensed, not distributed
        gtap = ("; GTAP 10 benchmark NOT RUN (it needs the GTAP 10 household-demand parameters, which the GTAP licence does "
                "not allow us to distribute; docs/STATUS.md)")
    else:
        mg = CGE.from_sam(les=_demand.les_gtap10())
        bg = mg.solve()
        Sg = mg.rebuild_sam(bg)
        gg = float((Sg - mg.sam.table.loc[Sg.index, Sg.columns]).abs().to_numpy().max())
        ok &= bg.ok and gg < 1e-6
        gtap = (f"; GTAP 10 benchmark: SAM gap {gg:.1e}, Frisch {mg.les['frisch'].min():.2f} to {mg.les['frisch'].max():.2f}")
    return ok, ("; ".join(out) + f"; oil +20%: processed food CD {d['CD']:+.3f}% vs LES {d['LES']:+.3f}%"
                f"; USDA ERS benchmark: SAM gap {gu:.1e}, Frisch {fu:.3f}" + gtap)


@check("S1", "petroleum-split SAM rebuilds, balances and calibrates")
def s1():
    import importlib.util
    from infinity_gem.sam import SAM
    from infinity_gem.cge import CGE
    from infinity_gem.oil import cge_oil_shock
    spec = importlib.util.spec_from_file_location("bsp", ROOT / "tools" / "build_sam_petroleum_split.py")
    bsp = importlib.util.module_from_spec(spec); spec.loader.exec_module(bsp)
    S, summary, _ = bsp.main()
    saved = SAM.load(paths.SAM_2023_PETR)
    rebuild = float((S.table - saved.table.loc[S.table.index, S.table.columns]).abs().to_numpy().max())
    orig = SAM.load(paths.SAM_2023).table
    keep = [c for c in orig.index if c not in ("achem", "cchem")]
    other = float((saved.table.loc[keep, keep] - orig.loc[keep, keep]).abs().to_numpy().max())
    bal = saved.check(tol=1e-6, verbose=False)
    m = CGE.from_sam(paths.SAM_2023_PETR)
    b = m.solve()
    Sm = m.rebuild_sam(b)
    gap = float((Sm - m.sam.table.loc[Sm.index, Sm.columns]).abs().to_numpy().max())
    h = m.solve({"cpi": 1.1})
    hom = float(np.abs(h["QA"] / b["QA"] - 1).max())
    s = m.solve(cge_oil_shock(m, 0.2))
    dp = float(s["PQ"][m.C.index("cpetr")] / b["PQ"][m.C.index("cpetr")] - 1) * 100
    ok = rebuild < 1e-6 and other < 1e-9 and bal["balanced"] and gap < 1e-6 and hom < 1e-8 and s.ok and dp > 5
    return ok, (f"rebuild gap {rebuild:.1e}; other accounts {other:.1e}; balanced {bal['balanced']}; CGE SAM gap {gap:.1e}; "
                f"homogeneity {hom:.1e}; oil +20%: refined petroleum price {dp:+.2f}%; refinery output "
                f"₱{summary['output, refined petroleum (₱ bn)']:.0f} bn")


@check("V4", "home consumption option (home='separate') reproduces the SAM and IFPRI's model with home consumption")
def v4():
    import runpy, contextlib, io as _io
    from infinity_gem.cge import CGE
    m = CGE.from_sam(home="separate")
    b = m.solve()
    S = m.rebuild_sam(b)
    gap = float((S - m.sam0.table.loc[S.index, S.columns]).abs().values.max())   # the SAM as published, home cells kept
    h = m.solve({"cpi": 2.0})
    hom = float(np.abs(h["QA"] / m.QA0 - 1).max())
    g_ = m.gdp(b)
    gid = abs(g_["nominal_expenditure"] - g_["nominal_income"])
    with contextlib.redirect_stdout(_io.StringIO()):
        mod = runpy.run_path(str(ROOT / "validation" / "ifpri_home" / "compare_home.py"), run_name="v4")
    out = []
    ok = gap < 1e-6 and hom < 1e-7 and gid < 1e-6 and abs(float(b["QHA"].sum()) - float(m.HC.sum())) < 1e-6
    for mg, lim in (("composite", (0.01, 0.01, 0.95, 0.6)), ("split", (0.001, 0.002, 0.99, 0.15))):
        r = mod["run"](mg)
        a = r.diff_pp.abs()
        core = float(a[r["item"].isin(["RGDP", "RCONS"])].max())
        home_ = float(a[r["item"] == "RHOME"].max())
        share, mx = float((a < 0.1).mean()), float(a.max())
        ok = ok and core < lim[0] and home_ < lim[1] and share >= lim[2] and mx < lim[3]
        out.append(f"{mg} margins: GDP and consumption {core:.4f} pp, home consumption {home_:.4f} pp, {share:.1%} of {len(r)} within 0.1 pp, largest {mx:.3f} pp")
    return ok, (f"SAM with home cells reproduced to {gap:.1e}; homogeneity {hom:.0e}; GDP identity {gid:.0e}; vs IFPRI (home kept): "
                + "; ".join(out))


@check("V5", "Hosoe cross-check: Infinity GEM reproduces pycge's human-written port of Hosoe's standard CGE")
def v5():
    import runpy, contextlib, io as _io
    with contextlib.redirect_stdout(_io.StringIO()):
        mod = runpy.run_path(str(ROOT / "validation" / "hosoe" / "compare_hosoe.py"), run_name="v5")
    P0, P1, G0, G1, tab, samgap = mod["P0"], mod["P1"], mod["G0"], mod["G1"], mod["tab"], mod["samgap"]
    keys = [k for k in P1 if not k.startswith("pz")]          # pz: unit normalisation differs (README)
    lev = max(max(abs(G0[k] - P0[k]) for k in keys), max(abs(G1[k] - P1[k]) for k in keys))
    pct = float(max(abs(tab.loc[k, "pycge % change"] - tab.loc[k, "Infinity GEM % change"]) for k in P1
                    if np.isfinite(tab.loc[k, "pycge % change"])))
    near = max(max(abs(mod["own"](mm, ss)[k] - P1[k]) for k in keys)
               for lab, (mm, bb, ss, _) in mod["rows"].items() if lab != "CD exact")
    ok = samgap < 1e-9 and lev < 1e-9 and pct < 1e-8 and near < 1e-5
    return ok, (f"{len(P1)} results; SAM reproduced to {samgap:.1e}; largest level gap {lev:.1e}; largest % change gap "
                f"{pct:.1e} pp; sigma_va 0.9999/1.0001 within {near:.1e}; EV {mod['ev_s']:.6f} vs pycge {mod['ev_p']:.6f}")


@check("S2", "named settings: 0.2 published = default; 0.3 recommended passes C2-C5 and Y1")
def s2():
    from infinity_gem import settings as ST
    from infinity_gem.cge import CGE
    from infinity_gem.dynamic import DynamicCGE
    a, b = ST.cge_model("0.2 published").solve(), CGE.from_sam().solve()
    same = all(np.array_equal(np.asarray(a[k]), np.asarray(b[k])) for k in ("QA", "PQ", "EH", "WF"))
    out, ok = [], same
    for name, cl in (("short run", dict(closure="keynesian", unemployed=("flab-n", "flab-p"), capital="fixed")), ("long run", {})):
        m = ST.cge_model("0.3 recommended", **cl)
        bs = m.solve()
        gap = float((m.rebuild_sam(bs) - m.sam.table).abs().values.max())
        hspec = {"cpi": 2.0} if m.closure != "keynesian" else (
            {"exr": 2.0} if m.wage == "real" else {"exr": 2.0, "wbar": {f: 2.0 for f in m.unemployed}})   # 0.3.4: sticky pesos double too
        h = m.solve(hspec)
        hom = float(np.abs(h["QA"] / m.QA0 - 1).max())
        shock = {"pwm_scale": {"cpetr": 1.3}, "remit_scale": 0.8, "qinv_scale": {"ccons": 0.8}}
        s = m.solve(shock)
        wal = abs(s["WALRAS"]) / m.qinv.sum()
        g = m.gdp(s)
        gid = abs(g["nominal_expenditure"] - g["nominal_income"])
        ok = ok and bs.ok and s.ok and gap < 1e-5 and hom < 1e-7 and wal < 1e-9 and gid < 1e-6
        out.append(f"{name}: SAM {gap:.1e}, homogeneity {hom:.1e}, Walras {wal:.1e}, GDP identity {gid:.1e}")
    d = DynamicCGE(**ST.dynamic_kwargs("0.3 recommended"))
    base = d.baseline()
    miss = float(np.abs(base.table["real_gdp_growth_pct"].values[1:] - np.array([d.growth[t] for t in d.years[1:]])).max())
    zgap = float((d.scenario({}).table.real_gdp - base.table.real_gdp).abs().max())
    ok = ok and miss < 1e-6 and zgap < 1e-6
    return ok, (f"0.2 setting = default model: {same}; 0.3 " + "; ".join(out)
                + f"; dynamic 0.3: growth miss {miss:.1e} pp, zero-shock gap {zgap:.1e}")


@check("H2", "household detail: deciles, families and persons, Social-method check")
def h2():
    import pandas as pd
    from infinity_gem.household import HouseholdDetail
    from infinity_gem.microsim import Microsim
    from infinity_gem.cge import CGE
    hd = HouseholdDetail()
    pv0 = hd._counts(hd.f["PCI"])
    base_ok = round(pv0["Poor families"]) == 2_992_013 and round(pv0["Poor persons"]) == 17_538_864
    ref = ROOT / "validation" / "household_detail"
    g = pd.read_csv(ref / "reference_task2_group_effects_central.csv", index_col=0)
    hers = pd.read_csv(ref / "reference_task2_deciles_central_recomputed.csv", index_col=0)
    mine = hd.deciles(g)
    mine.columns = [c.replace("₱", "P") for c in mine.columns]
    dec_gap = float((mine[hers.columns] - hers).abs().max().max())
    m = CGE.from_sam(closure="keynesian", unemployed=("flab-n", "flab-p"), capital="fixed")
    b = m.solve()
    s = m.solve({"qinv_scale": {"ccons": 0.8}})
    ge = hd.group_effects(m, b, s)
    pov_gap = abs(float(hd.poverty(ge).loc["Poor persons", "Change"]) - Microsim().from_cge(m, b, s)["new_poor"])
    ns = abs(hd.deciles(ge, net_seller=True).loc["All families", "Total loss: total (₱ million)"]
             - hd.deciles(ge).loc["All families", "Total loss: total (₱ million)"])
    r = hd.price_only(0.0154, 0.0164)
    p = r["poverty"]
    soc = [round(p["New poor families"]), round(p["New poor persons"]), round(p["New food-poor families"]), round(p["New food-poor persons"])]
    want = [156_329, 835_400, 53_395, 319_894]
    soc_ok = all(abs(x - y) <= 2 for x, y in zip(soc, want))
    monthly = hd.price_only(0.0154)["monthly_loss_b30_per_person_def"]
    nat = r["deciles"].loc["All families", "Loss: total (₱ million)"] / 1e3
    ok = base_ok and dec_gap < 1e-6 and pov_gap < 0.01 and ns < 1e-6 and soc_ok and abs(monthly - 225.11) < 0.01 and abs(nat - 155.5) < 0.05
    return ok, (f"baseline {pv0['Poor families']:,.0f} families / {pv0['Poor persons']:,.0f} persons; deciles vs the reference table {dec_gap:.1e}; "
                f"new poor vs microsim {pov_gap:.1e}; net-seller national change {ns:.1e}; Social method oil +1.54: "
                f"{soc[0]:,} / {soc[1]:,} poor, {soc[2]:,} / {soc[3]:,} food-poor, ₱{monthly:.2f} a month, ₱{nat:.1f} bn")


@check("H3", "LFS link: PSA FIES-LFS 2023 members, earnings by industry")
def h3():
    import pandas as pd
    from infinity_gem.household import HouseholdDetail, NEC, ENTREPRENEURIAL
    hd = HouseholdDetail()
    if not hd.lfs_available():
        return None, ("NOT RUN on this computer: PSA's FIES-LFS 2023 member file is licensed to the person who downloaded it "
                      f"and is not here ({paths.FIES_LFS_MEMBERS.name}).")
    m = hd.members()
    E = hd.earnings_by_industry()           # raises if any member fails to match a FIES household
    f = hd.f
    lab = f["WAGES"].clip(lower=0) + f[list(ENTREPRENEURIAL) + NEC].clip(lower=0).sum(axis=1)
    alloc = float((E.sum(axis=1) - lab).abs().max())
    emp = m[m["emp"]]
    unmapped = int((emp["ind"] < 0).sum())
    lfs = pd.read_csv(paths.DATA_RAW / "lfs" / "PSA_OpenSTAT_LFS_employed_by_highest_grade_2023-2026.csv", comment="#")
    psa = float(lfs[(lfs.year == 2024) & (lfs.month == "January") & (lfs.highest_grade_completed == "Total")].employed_thousands.iloc[0])
    tot = float(emp["w"].sum()) / 1e3
    g = pd.DataFrame({"inflation_pct": 0.0, "income_pct": 0.0, "real_factor": 1.0}, index=sorted(f["grp"].unique()))
    g.attrs["industry_pct"] = {"Construction": -10.0, "Manufacturing": 5.0}
    grp_gap = float((hd._lfs_adjustment(g) * f["RFACT"]).groupby(f["grp"]).sum().abs().max())
    zero = float(hd.earnings_only({}).get("earnings_change").abs().max())
    ok = alloc < 1e-6 and unmapped == 0 and abs(tot / psa - 1) < 0.02 and grp_gap < 1e-3 and zero == 0.0
    return ok, (f"{len(m):,} members of {m[['W_REGN','W_PROV','SEQ_NO']].drop_duplicates().shape[0]:,} households, all matched; "
                f"employed {tot:,.0f} thousand vs PSA January 2024 {psa:,.0f} ({(tot/psa-1)*100:+.1f}%); employed without an "
                f"industry: {unmapped}; earnings allocated vs FIES wages + entrepreneurial {alloc:.1e}; within-group "
                f"redistribution keeps group totals ({grp_gap:.1e}); zero shock gives zero")


@check("A2", "Simulator: every CGE lever and closure; levers by year in the dynamic model")
def a2():
    sys.path[:0] = [str(ROOT), str(ROOT / "scenarios")]
    from app import engines as E
    import numpy as np_
    out, ok = [], True
    for label, (key, kind) in E.LEVERS.items():
        m = E.cge_model("short run")
        code = "ALL" if kind in ("all",) or "+all" in kind else E._lever_items(m, kind)[0]
        spec, pr = E.apply_levers(m, {}, [[label, code, 1.0]])
        z, _ = E.apply_levers(m, {}, [[label, code, 0.0]])
        ok = ok and not pr and key in spec and not z
    for cl in E.CLOSURES:
        r = E.run_cge(E.Shocks(levers=[["Real investment demand (%)", "ccons", -5.0], ["Tariff rate (%)", "ALL", -10.0]]), cl)
        ok = ok and r["ok"] and abs(r["walras"]) < 1e-6 and not [n for n in r["notes"] if "skipped" in n]
        out.append(f"{cl.split(':')[0]} {r['summary']['Real GDP (%)']:+.3f}%" if r["ok"] else f"{cl} FAILED")
    _, pr = E.apply_levers(E.cge_model("short run"), {}, [["Productivity, TFP (%)", "crice", 1.0]])
    ok = ok and len(pr) == 1                                   # a commodity is refused for an industry lever
    a = E.run_dynamic({2025: -238.3}, hybrid=False)["summary"]["Cumulative GDP vs baseline, 2024-2030 (₱ bn)"]
    b = E.run_dynamic({2025: -238.3}, hybrid=False, levers_by_year={2026: [["Productivity, TFP (%)", "ALL", 0.0]]})["summary"]["Cumulative GDP vs baseline, 2024-2030 (₱ bn)"]
    c = E.run_dynamic({}, hybrid=False, levers_by_year={2025: [["Productivity, TFP (%)", "ALL", -1.0]]})
    ok = ok and abs(a - b) < 1e-9 and c["ok"] and c["summary"]["Cumulative GDP vs baseline, 2024-2030 (₱ bn)"] < 0
    return ok, (f"{len(E.LEVERS)} levers map to the engine; {len(E.CLOSURES)} closures solve ({'; '.join(out)}); bad rows refused; "
                f"dynamic: zero lever leaves the freeze at ₱{a:,.1f} bn; TFP −1% in 2025 ₱{c['summary']['Cumulative GDP vs baseline, 2024-2030 (₱ bn)']:,.1f} bn")


@check("W1", "Saving when the outputs folder cannot be written: the person's own folder")
def w1():
    import os
    import shutil
    import subprocess
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="infinity_gem_w1_"))
    shared, mine = tmp / "shared" / "outputs", tmp / "mine"
    (shared / "simulator").mkdir(parents=True)
    keep = paths.OUTPUTS, paths.MY_RUNS
    paths.OUTPUTS, paths.MY_RUNS = shared, mine

    def lock(on):                                          # a real permission, as a file-sharing service "Can view" gives
        if os.name == "nt":
            who = os.environ.get("USERNAME", "")
            # create files/folders, write data and attributes; NOT "W", whose SYNCHRONIZE right would block reading too
            args = ["/deny", f"{who}:(OI)(CI)(WD,AD,WEA,WA)"] if on else ["/remove:d", who]
            subprocess.run(["icacls", str(shared), *args, "/T", "/Q"], capture_output=True)
        else:
            for d in (shared, shared / "simulator"):
                os.chmod(d, 0o555 if on else 0o755)
    try:
        a = paths.output_dir("simulator") == shared / "simulator" and paths.output_dir() == shared
        lock(True)
        locked = not paths.can_write(shared)
        b = paths.output_dir("simulator") == mine / "simulator" and (mine / "simulator").is_dir()
        c = paths.output_dirs("simulator") == [shared / "simulator", mine / "simulator"]
        lock(False)
        left = [p.name for p in tmp.rglob("~infinity_gem_write_test_*")]     # the write test leaves nothing behind
    finally:
        lock(False)
        paths.OUTPUTS, paths.MY_RUNS = keep
        shutil.rmtree(tmp, ignore_errors=True)
    ok = a and locked and b and c and not left
    return ok, (f"writable: saves in outputs ({a}); read-only folder detected ({locked}); then saves in the own folder ({b}); "
                f"reads both ({c}); test files left: {left or 'none'}")


@check("V6", "Structural VAR module: regression guard on an existing VAR (points and bootstrap bands)")
def v6():
    import runpy, contextlib, io as _io
    with contextlib.redirect_stdout(_io.StringIO()):
        mod = runpy.run_path(str(ROOT / "validation" / "var_task1" / "reproduce_task1_var.py"), run_name="v6")
    r = mod["run"]()
    worst = max(r["gaps"].values())
    ok = r["rows"] == r["matched"] == 130 and r["gaps"]["Effect"] < 1e-8 and worst < 1e-6 and r["stable"]
    return ok, (f"{r['matched']} of {r['rows']} results matched; largest gap: responses {r['gaps']['Effect']:.1e}, "
                f"bootstrap bands {worst:.1e}; {r['n_obs']} months; stable VAR")


@check("V7", "Structural VAR module: equals statsmodels; block exogeneity, decomposition, counterfactual, signs, BVAR exact")
def v7():
    import pandas as pd
    from statsmodels.tsa.api import VAR
    from infinity_gem import svar
    rng = np.random.default_rng(7)
    A1 = np.array([[0.5, 0, 0], [0.2, 0.4, 0.1], [0.1, -0.2, 0.3]])
    A2 = np.array([[0.2, 0, 0], [0, 0.1, 0], [0.05, 0, 0.1]])
    P = np.array([[1.0, 0, 0], [0.5, 0.8, 0], [0.3, 0.2, 0.6]])
    Y = np.zeros((3000, 3))
    for t in range(2, len(Y)):
        Y[t] = 0.1 + A1 @ Y[t - 1] + A2 @ Y[t - 2] + P @ rng.standard_normal(3)
    df = pd.DataFrame(Y, columns=["a", "b", "c"])
    m, r = svar.fit(df, 2, sigma_dof="ols"), VAR(df).fit(2)
    g_sm = max(np.abs(np.hstack(r.coefs) - m.A).max(), np.abs(r.sigma_u.values - m.Sigma).max(),
               np.abs(r.irf(10).orth_irfs - svar.irf(m, svar.cholesky(m), 10)).max())
    mb = svar.fit(df, 2, exog_block=["a"])
    B = svar.cholesky(mb)
    g_blk = float(np.abs(svar.irf(mb, B, 24)[:, 0, 1:]).max())
    hd = svar.historical_decomposition(mb, B)
    g_hd = float(np.abs(hd["baseline"] + hd["contribution"].sum(axis=2) - Y[2:]).max())
    g_cf = float(np.abs(svar.counterfactual_irf(mb, B, 1, "c", 12)[:, 2]).max())
    acc = svar.sign_restrictions(mb, 1, {"b": 1, "c": 1}, horizons=(0, 1), draws=100)
    sign_ok = len(acc) == 100 and all((svar.irf(mb, Bs, 1)[:, [1, 2], 1] > 0).all() for Bs in acc)
    g_bv = float(np.abs(svar.bvar_minnesota(df, 2, lam=1e4).model().A - svar.fit(df, 2).A).max())
    ok = g_sm < 1e-12 and g_blk == 0 and g_hd < 1e-10 and g_cf < 1e-12 and sign_ok and g_bv < 1e-8
    return ok, (f"vs statsmodels {g_sm:.0e}; blocked responses {g_blk:.0e}; decomposition {g_hd:.0e}; held variable {g_cf:.0e}; "
                f"sign draws ok {sign_ok}; loose-prior BVAR vs OLS {g_bv:.0e}")


@check("M2", "VAR-to-CGE link (infinity_gem.macrolink): zero shock = base; units and closures")
def m2():
    from infinity_gem.cge import CGE
    from infinity_gem import macrolink as ML
    m = CGE.from_sam(closure="savings")
    b = m.solve()
    zero = float(np.abs(m.solve(ML.cge_shocks(m))["QA"] - b["QA"]).max())
    sp = ML.cge_shocks(m, fdi_usd_m=-1000, php_per_usd=58.0, gdp_bn=28009.93)
    want = 1 - 1000 * 58.0 / 1000 / 28009.93 * ML.sam_gdp(m) / m.fsav            # share of GDP rule
    s = m.solve(sp)
    k = CGE.from_sam(closure="keynesian", unemployed=("flab-n", "flab-p"), capital="fixed")
    try:
        ML.cge_shocks(k, fdi_usd_m=-1000, php_per_usd=58.0, gdp_bn=28009.93, fdi_channel="foreign_savings")
        refused = False
    except ValueError:
        refused = True
    ok = zero == 0 and abs(sp["fsav_scale"] - want) < 1e-12 and s.ok and s["QINV"].sum() < b["QINV"].sum() and refused
    return ok, (f"zero shock gap {zero:.0e}; FDI -US$1 bn -> foreign savings x{sp['fsav_scale']:.5f}, real investment "
                f"{(s['QINV'].sum() / b['QINV'].sum() - 1) * 100:+.3f}% (savings closure); foreign-savings channel refused in "
                f"the keynesian closure: {refused}")


@check("W2", "wage option: sticky peso wages in the short run")
def w2():
    from infinity_gem.cge import CGE
    SR = dict(closure="keynesian", unemployed=("flab-n", "flab-p"), capital="fixed")
    cut = {"trg_h_add": {"hhd-r1": -5.0, "hhd-r2": -5.0, "hhd-u1": -5.0, "hhd-u2": -5.0}}     # an Ayuda-type transfer cut
    # 1. outside the Keynesian closure the CPI is the numeraire, so 'nominal' must equal 'real' exactly
    lr_r, lr_n = CGE.from_sam(), CGE.from_sam(wage="nominal")
    same = float(np.abs(lr_r.solve(SHOCK)["QA"] - lr_n.solve(SHOCK)["QA"]).max())
    # 2. short run, nominal: benchmark, homogeneity (exchange rate AND peso wage x2), direction of a demand cut
    m = CGE.from_sam(wage="nominal", **SR)
    R, _ = m.evaluate(m.x0(), m.make_shocks())
    hom = m.solve({"exr": 2.0, "wbar": {f: 2.0 for f in SR["unemployed"]}})
    dq = float(np.abs(hom["QA"] / m.QA0 - 1).max()); dp = float(np.abs(hom["PQ"][m.iQ] / 2 - 1).max())
    b, s = m.solve(), m.solve(cut)
    k = m.F.index("flab-n"); emp = (s["EMP"][k] / b["EMP"][k] - 1) * 100
    try:
        CGE.from_sam(wage="sticky"); refused = False
    except ValueError:
        refused = True
    ok = same < 1e-9 and float(np.abs(R).max()) < 1e-7 and hom.ok and dq < 1e-7 and dp < 1e-7 and s.ok and emp < 0 and refused
    return ok, (f"long run nominal = real: {same:.1e}; short-run nominal: benchmark {float(np.abs(R).max()):.1e}, homogeneity "
                f"dQ {dq:.1e} dP {dp:.1e}; transfer cut -> low-skill jobs {emp:+.3f}% (must fall); bad option refused: {refused}")


@check("X1", "stochastic dynamic CGE (Stage 1): baseline, fixed path, seed, posterior, calibration")
def x1():
    from infinity_gem.dynamic import DynamicCGE
    from infinity_gem import stochastic as SC
    from infinity_gem import macrolink as ML
    d = SC.load_task1_monthly()
    st = SC.StochasticCGE(DynamicCGE(), d, php_per_usd=float(d["fx"].dropna().iloc[-12:].mean()))
    # (a) zero variance: every draw is the deterministic baseline
    za = float(st.run(n=2, zero_variance=True).draws.abs().max().max())
    # (b) a fixed path through the stochastic machinery = the deterministic scenario built directly
    y = st.years[0]
    via = st.run_path({y: dict(oil_pct=20.0, remit_pct=-5.0, fdi_usd_m=-500.0)})
    direct = st.dyn.compare(st.dyn.base, st.dyn.scenario({y: ML.cge_shocks(
        st.dyn.m, oil_pct=20.0, remit_pct=-5.0, fdi_usd_m=-500.0, php_per_usd=st.php, gdp_bn=st.gdp,
        fdi_channel="investment", investment_passthrough=st.theta)}))
    zb = max(abs(via[f"GDP gap % {t}"] - direct.loc[t, "gdp_gap_pct"]) for t in st.years)
    # (c) same seed, same draws
    r1, r2 = st.run(n=2, seed=7), st.run(n=2, seed=7)
    zc = float((r1.draws - r2.draws).abs().max().max())
    # (d) the posterior draws' covariance averages to the posterior mean (200 draws, no CGE runs)
    k = len(SC.VARIABLES)
    sig_bar = np.mean([S for _, S in st.bvar.draw(200, seed=11)], axis=0)
    sig_post = st.bvar.S / (st.bvar.dof - k - 1)
    zd = float(np.abs(np.diag(sig_bar) / np.diag(sig_post) - 1).max())
    # (e) calibration: the simulated one-year-ahead spread of oil and remittances vs 2016-2025 history (within 0.5x-2x)
    a = d.groupby(d.index.year).agg({"oil": "mean", "remit": "mean"}).loc[2015:2025].pct_change().std() * 100
    rng = np.random.default_rng(3); o, r = [], []
    for B, S in st.bvar.draw(300, seed=3):
        if not st.bvar.model(B, S).stable():
            continue
        ch = SC.yearly_changes(SC._simulate(B, S, st.Y_last, st.H, rng), st.mean_path, st.start, st.years)[y]
        o.append(ch["oil_pct"]); r.append(ch["remit_pct"])
    ro, rr = np.std(o) / a["oil"], np.std(r) / a["remit"]
    ok = za == 0.0 and zb < 1e-9 and zc == 0.0 and zd < 0.15 and 0.5 < ro < 2 and 0.5 < rr < 2
    return ok, (f"zero variance = baseline: {za:.1e}; fixed path = direct scenario: {zb:.1e}; same seed: {zc:.1e}; "
                f"posterior covariance (200 draws) within {zd:.1%}; {y} spread vs 2016-2025 history: oil {np.std(o):.1f}% vs "
                f"{a['oil']:.1f}%, remittances {np.std(r):.1f}% vs {a['remit']:.1f}%")


@check("ML1", "macro-micro link file: FIES categories, family inflation, export (0.3.5)")
def ml1():
    import json
    import tempfile
    import pandas as pd
    from infinity_gem.cge import CGE
    from infinity_gem.microlink import MicroLink, CATEGORIES
    from infinity_gem.microsim import Microsim
    d = json.loads((ROOT / "scenarios" / "specs" / "five_shocks_2026_central.json").read_text(encoding="utf-8"))
    m = CGE.from_sam(**{k: (tuple(v) if isinstance(v, list) else v) for k, v in d["closure"].items()})
    b = m.solve()
    s = m.solve(d["spec"])
    ml = MicroLink(m)
    cover = abs(ml.W.values.sum() / ml.hh_cons.sum() - 1)                      # all household consumption is attributed
    # homogeneity: every consumer price +10% -> every category and every family +10%
    fake = {"PQ": b["PQ"] * 1.1}
    cat10 = float((ml.category_prices(m, b, fake) - 10).abs().max())
    link = ml.link_variables(m, b, s, scenario="ML1")
    pi = ml.family_inflation(link)
    link10 = dict(link)
    link10["fies_categories"] = link["fies_categories"].assign(price_change_pct=10.0)
    fam10 = float((ml.family_inflation(link10) - 10).abs().max())
    # group method = Infinity GEM's published new poor; the reconciled national basket = the SAM's household CPI (spending-weighted)
    pov = float(ml.hd.poverty(link["_g"]).loc["Poor persons", "Change"])
    ms = Microsim().from_cge(m, b, s)["new_poor"]
    sam_cpi = float(ml.hh_cons.values @ ((s["PQ"] / b["PQ"] - 1) * 100) / ml.hh_cons.sum())
    fam_cpi = float(np.average(pi, weights=(ml.spend.values * ml.lam.reindex(CATEGORIES).values).sum(axis=1) * ml.hd.f["RFACT"]))   # reconciled spending
    # export: CSV values = the tables
    with tempfile.TemporaryDirectory() as tmp:
        x = ml.write(link, Path(tmp) / "ml1.xlsx")
        back = pd.read_csv(Path(tmp) / "ml1" / "fies_categories.csv")
        rt = float((back["price_change_pct"].values - link["fies_categories"]["price_change_pct"].values).__abs__().max())
        ok_files = x.exists() and all((Path(tmp) / "ml1" / f"{k}.csv").exists() for k in
                                       ("fies_categories", "commodities", "industries", "household_groups", "factors", "net_seller", "concordance", "expected_results"))
    ok = (cover < 1e-9 and cat10 < 1e-9 and fam10 < 1e-9 and abs(pov - 1_995_889) < 1 and abs(pov - ms) < 0.01
          and abs(fam_cpi - sam_cpi) < 0.02 and rt < 1e-9 and ok_files)
    return ok, (f"household consumption attributed {1 - cover:.12f}; all prices +10% -> categories {cat10:.1e}, families {fam10:.1e}; "
                f"September 2026 five shocks: new poor {pov:,.0f} (microsim {ms:,.0f}); reconciled family CPI {fam_cpi:.4f} vs SAM household "
                f"CPI {sam_cpi:.4f} pp; CSV round trip {rt:.1e}; all 8 tables written")


@check("LP1", "local projections (Jorda 2005): recover a known impulse response; equal OLS (0.3.5)")
def lp1():
    import pandas as pd
    import statsmodels.api as sm
    from infinity_gem.svar import local_projection
    rng = np.random.default_rng(20261015)
    n, rho = 3000, 0.7
    e = rng.standard_normal(n)
    y = np.zeros(n)
    for t in range(1, n):
        y[t] = rho * y[t - 1] + e[t]
    lp = local_projection(pd.Series(y), pd.Series(e), H=6, lags=2)
    gap = float((lp["beta"] - rho ** lp.index.values).abs().max())
    cover = int(((lp["low90"] <= rho ** lp.index.values) & (rho ** lp.index.values <= lp["high90"])).sum())
    # h = 2 by hand with statsmodels: the same coefficient
    Y = pd.Series(y); E_ = pd.Series(e)
    X = pd.DataFrame({"shock": E_, "y_l1": Y.shift(1), "s_l1": E_.shift(1), "y_l2": Y.shift(2), "s_l2": E_.shift(2)})
    z = pd.concat([Y.shift(-2).rename("lhs"), X], axis=1).dropna()
    b2 = sm.OLS(z["lhs"], sm.add_constant(z.drop(columns="lhs"))).fit().params["shock"]
    same = abs(b2 - lp.loc[2, "beta"])
    ok = gap < 0.05 and cover >= 5 and same < 1e-12
    return ok, f"AR(1) rho 0.7, 3,000 draws: max gap to rho^h {gap:.3f}; true value inside the 90% band at {cover} of 7 horizons; h=2 vs statsmodels OLS {same:.1e}"


@check("SH1", "Shapley decomposition: additivity, symmetry, null shock, linear case (0.3.5)")
def sh1():
    from infinity_gem.decompose import shapley
    w = {"a": 1.0, "b": -2.0, "c": 0.5}
    lin = shapley(lambda S: sum(w[k] for k in S), list(w))                     # linear: contribution = own effect
    lin_gap = max(abs(lin[k] - w[k]) for k in w)
    f = lambda S: (len(S & {"a", "b"}) == 2) * 3.0 + ("c" in S) * 1.0           # a and b only matter together; d never
    phi = shapley(f, ["a", "b", "c", "d"])
    add = abs(phi.sum() - phi.attrs["total"])
    sym = abs(phi["a"] - phi["b"]) + abs(phi["a"] - 1.5)
    null = abs(phi["d"])
    ok = lin_gap < 1e-12 and add < 1e-12 and sym < 1e-12 and null < 1e-12 and phi.attrs["evaluations"] == 16
    return ok, (f"linear case gap {lin_gap:.1e}; sum = total {add:.1e}; symmetric pair split 1.5 / 1.5 ({sym:.1e}); null shock {null:.1e}; "
                f"{phi.attrs['evaluations']} evaluations for 4 shocks")


@check("CR1", "public-investment efficiency by year and leakage (0.3.6)")
def cr1():
    # (1) every e_t = e, no leakage: identical to the 0.3 public-capital channel; (2) a lower e_t in one year opens a
    # public-capital gap of exactly (e_t - e) * s * baseline construction the next year; (3) leakage moves L off
    # construction and onto household transfers with the disbursement unchanged: no public-capital gap, demand changes
    from infinity_gem.dynamic import DynamicCGE
    pc = {"phi": 0.1, "kg_gdp": 1.0}                                   # test values only
    s, shock = 0.4, {2025: {"qinv_scale": {"ccons": 0.9}}}             # s: test value only
    ref = DynamicCGE(hybrid=True, public_capital=pc)
    rb = ref.baseline()
    r0 = ref.scenario(shock).table
    yrs = ref.years
    d = DynamicCGE(hybrid=True, public_capital=dict(pc, e_path={t: 0.77 for t in yrs}, ig_public_share=s))
    d.base = rb
    same = float((d.scenario(shock).table[["real_gdp", "public_capital_gap_pct"]] - r0[["real_gdp", "public_capital_gap_pct"]]).abs().max().max())
    ic = ref.m.C.index("ccons")
    igb24 = float(rb.solutions[2024]["QINV"][ic])
    d2 = DynamicCGE(hybrid=True, public_capital=dict(pc, e_path={2024: 0.5}, ig_public_share=s))
    d2.base = rb
    t2 = d2.scenario({}).table
    want = (0.5 - 0.77) * s * igb24 / (pc["kg_gdp"] * float(rb.table.loc[2025, "real_gdp"])) * 100
    eff = abs(float(t2.loc[2025, "public_capital_gap_pct"]) - want) / abs(want)
    d3 = DynamicCGE(hybrid=True, public_capital=dict(pc, leakage={2024: 0.2}, leak_to={"hhd-u5": 1.0}, ig_public_share=s))
    d3.base = rb
    p3 = d3.scenario({2024: {}})
    L = 0.2 * s * igb24
    moved = abs((igb24 - float(p3.solutions[2024]["QINV"][ic])) - L) / L
    kgap = float(p3.table["public_capital_gap_pct"].abs().max())
    dgdp = float(p3.table.loc[2024, "real_gdp"] / rb.table.loc[2024, "real_gdp"] - 1) * 100     # signed
    # (4) 'saved' and 'abroad' destinations (0.3.6): construction falls by exactly L, both solve, demand falls
    dest = {}
    for where in ("saved", "abroad"):
        dd = DynamicCGE(hybrid=True, public_capital=dict(pc, leakage={2024: 0.2}, leak_to={where: 1.0}, ig_public_share=s))
        dd.base = rb
        pp = dd.scenario({2024: {}})
        dest[where] = (abs((igb24 - float(pp.solutions[2024]["QINV"][ic])) - L) / L,
                       float(pp.table.loc[2024, "real_gdp"] / rb.table.loc[2024, "real_gdp"] - 1) * 100)
    # (5) waste_lost: no shock changes nothing; best-performer efficiency in 2024 adds exactly kappa (1 - e) s IGc to the
    # general stock in 2025; leakage at e_t = e leaves the general stock as without leakage (the 23% is lost either way)
    wl = dict(pc, ig_public_share=s, waste_lost=True)
    dw = DynamicCGE(hybrid=True, public_capital=wl)
    dw.base = rb
    zero_w = float((dw.scenario({2025: {}}).table.real_gdp - rb.table.real_gdp).abs().max())
    k_on = DynamicCGE(hybrid=True, public_capital=dict(wl, e_path={2024: 1.0}))
    k_on.base = rb
    k_off = DynamicCGE(hybrid=True, public_capital=dict(pc, ig_public_share=s, e_path={2024: 1.0}))
    k_off.base = rb
    dK = (float(k_on.scenario({}).table.loc[2025, "capital_stock_index"]) - float(k_off.scenario({}).table.loc[2025, "capital_stock_index"])) * ref.K0
    wantK = ref.kappa * (1 - 0.77) * s * igb24
    k_err = abs(dK - wantK) / wantK
    lw = DynamicCGE(hybrid=True, public_capital=dict(wl, leakage={2024: 0.2}, leak_to={"saved": 1.0}))
    lw.base = rb
    k_leak = float((lw.scenario({2024: {}}).table.capital_stock_index - dw.scenario({2024: {}}).table.capital_stock_index).abs().max())
    # (6) absorptive capacity (DIG overruns): a 10% construction rise in 2025 adds e * dIG / (1 + phi_A dIG / KG) of public
    # capital, exactly; a cut is unaffected
    da = DynamicCGE(hybrid=True, public_capital=dict(pc, absorptive=5.0))
    da.base = rb
    pa = da.scenario({2025: {"qinv_scale": {"ccons": 1.1}}})
    dIG25 = float(pa.solutions[2025]["QINV"][ic] - rb.solutions[2025]["QINV"][ic])
    KG25 = pc["kg_gdp"] * float(rb.table.loc[2025, "real_gdp"])
    wantA = 0.77 * dIG25 / (1 + 5.0 * dIG25 / KG25) / (pc["kg_gdp"] * float(rb.table.loc[2026, "real_gdp"])) * 100
    a_err = abs(float(pa.table.loc[2026, "public_capital_gap_pct"]) - wantA) / wantA
    cut_same = float((da.scenario(shock).table.real_gdp - ref.scenario(shock).table.real_gdp).abs().max())
    ok = (same == 0.0 and eff < 1e-9 and moved < 1e-8 and kgap < 1e-12 and dgdp < -1e-4
          and all(m_ < 1e-8 and g_ < -1e-4 for m_, g_ in dest.values()) and zero_w < 1e-6 and k_err < 1e-9 and k_leak < 1e-12
          and a_err < 1e-9 and cut_same < 1e-9)
    return ok, (f"all e_t = e: max difference {same:.1e}; e 0.5 in 2024: gap {float(t2.loc[2025, 'public_capital_gap_pct']):.4f}% "
                f"(formula {want:.4f}%, rel. error {eff:.1e}); leakage 20% in 2024: construction down by L to {moved:.1e}, "
                f"public-capital gap {kgap:.1e}, real GDP 2024 {dgdp:+.4f}% (to a top household group), "
                f"{dest['saved'][1]:+.4f}% (saved), {dest['abroad'][1]:+.4f}% (abroad); waste_lost: zero shock {zero_w:.1e}, "
                f"e 1.0 adds kappa(1-e)s IGc to capital (rel. error {k_err:.1e}), leakage leaves capital unchanged ({k_leak:.1e}); "
                f"absorptive 5: rise adds the DIG amount (rel. error {a_err:.1e}), cut unaffected ({cut_same:.1e}); "
                f"s 0.4 and kg_gdp 1.0 test values")


@check("S3", "rice-split SAM rebuilds, balances, carries PSA 2023 imports; fixed land and drought (0.3.7)")
def s3():
    import importlib.util
    from infinity_gem.sam import SAM
    from infinity_gem.settings import cge_model, short_run_closure
    spec = importlib.util.spec_from_file_location("bsr", ROOT / "tools" / "build_sam_rice_split.py")
    bsr = importlib.util.module_from_spec(spec); spec.loader.exec_module(bsr)
    S, summary, _ = bsr.main("psa2023")
    saved = SAM.load(paths.SAM_2023_RICE)
    rebuild = float((S.table - saved.table.loc[S.table.index, S.table.columns]).abs().to_numpy().max())
    bal = saved.check(tol=1e-6, verbose=False)["balanced"]
    psa = bsr.psa_milled_imports_2023()["php_bn"]
    imp_ok = abs(summary["imports, milled rice and corn (₱ bn)"] - psa) < 1e-9 and         abs(summary["import duty, milled rice and corn (₱ bn)"] - bsr.RICE_DUTY_2023) < 1e-9 and         abs(summary["imports, maize (₱ bn)"] - bsr.psa_maize_imports_2023()) < 1e-9
    m = cge_model("0.3 recommended", rice=True, sam_variant="ifpri", **short_run_closure(), land="fixed")   # 0.3.10: the IFPRI rice-split file
    b = m.solve()
    mm = cge_model("0.3 recommended", rice=True, sam_variant="ifpri", **short_run_closure())
    bm = mm.solve()
    same = float(np.abs(b["QA"] - bm["QA"]).max())                     # fixed and mobile land: same benchmark
    try:
        mm.solve({"lscale": {"arice": 0.9}}); guard = False
    except ValueError:
        guard = True
    s = m.solve({"lscale": {"arice": 0.8}})
    i, c = m.A.index("arice"), m.C.index("cmric")
    dq, dm = float(s["QA"][i] / b["QA"][i] - 1) * 100, float(s["QM"][c] / b["QM"][c] - 1) * 100
    ok = rebuild < 1e-6 and bal and imp_ok and b.ok and same < 1e-8 and guard and s.ok and dq < 0 and dm > 0
    return ok, (f"rebuild gap {rebuild:.1e}; balanced {bal}; imports = PSA 2023 ₱{psa:.2f} bn, duty = BOC ₱{bsr.RICE_DUTY_2023} bn, "
                f"maize imports placed: {imp_ok}; fixed vs mobile land benchmark {same:.1e}; land shock refused with mobile land: "
                f"{guard}; rice land -20%: rice output {dq:+.2f}%, milled-rice imports {dm:+.2f}%")


@check("Y6", "employment capped at the labour supply in short-run years (0.3.7)")
def y6():
    from infinity_gem.dynamic import DynamicCGE
    from infinity_gem.settings import dynamic_kwargs
    d = DynamicCGE(**dynamic_kwargs("0.3 recommended"))
    b = d.baseline()
    z = d.scenario({2026: {}})
    zgap = float((z.table.real_gdp - b.table.real_gdp).abs().max())
    big = {2026: {"qinv_scale": {"ccons": 1.3}, "trg_h_add": {"hhd-r1": 60.0, "hhd-u1": 60.0}}}
    s = d.scenario(big)
    F = d.m.F
    supply = d.m.QFS0 * np.array([1.0 if not f.startswith("flab") else 1.0 for f in F])
    Lidx = (1 + d.a["labour_growth"]) ** d.years.index(2026) if d.L_path is None else None
    sup = np.array([d.m.QFS0[k] * (d.L_path[2026].get(f, 1.0) if d.L_path else Lidx) for k, f in enumerate(F)])
    emp = s.solutions[2026]["EMP"]
    over = max(float(emp[k] / sup[k] - 1) for k, f in enumerate(F) if f in d.a["short_run_unemployed"])
    capped = s.table.loc[2026, "employment_capped"]
    d.a["employment_cap"] = False
    s0 = d.scenario(big)
    emp0 = s0.solutions[2026]["EMP"]
    over0 = max(float(emp0[k] / sup[k] - 1) for k, f in enumerate(F) if f in d.a["short_run_unemployed"])
    d.a["employment_cap"] = True
    ok = zgap < 1e-6 and over < 1e-8 and bool(capped) and over0 > 1e-4
    return ok, (f"zero shock gap {zgap:.1e}; big demand in 2026: employment above supply {over * 100:+.2e}% with the cap "
                f"(capped: {capped}), {over0 * 100:+.2f}% without it")


@check("PK1", "public construction counted once: public capital only, not the general stock (0.3.7)")
def pk1():
    from infinity_gem.dynamic import DynamicCGE
    shock = {2025: {"qinv_scale": {"ccons": 0.9}}}
    out = {}
    for name, pc in (("old", {"phi": 0.1, "kg_gdp": 1.0}), ("old, key True", {"phi": 0.1, "kg_gdp": 1.0, "general_stock": True}),
                     ("once", {"phi": 0.1, "kg_gdp": 1.0, "general_stock": False}),
                     ("once, phi 0", {"phi": 0.0, "kg_gdp": 1.0, "general_stock": False})):
        d = DynamicCGE(public_capital=pc)                  # kg_gdp: test value only
        b = d.baseline()
        s = d.scenario(shock)
        out[name] = (b, s)
    gap = lambda k, y: float(out[k][1].table.loc[y, "real_gdp"] / out[k][0].table.loc[y, "real_gdp"] - 1) * 100
    kdev = float((out["once"][1].table.capital_stock_index - out["once"][0].table.capital_stock_index).loc[2026:].abs().max())
    same = float((out["old"][1].table.real_gdp - out["old, key True"][1].table.real_gdp).abs().max())
    g_old, g_once, g0 = gap("old", 2030), gap("once", 2030), gap("once, phi 0", 2030)
    ok = kdev < 1e-9 and same < 1e-12 and g_old < g_once < 0 and abs(g0) < 1e-6
    return ok, (f"general stock off its baseline after a 10% construction cut: {kdev:.1e}; key left out = True: {same:.1e}; "
                f"2030 GDP gap: double channel {g_old:+.3f}%, public capital only {g_once:+.3f}%, phi 0 {g0:+.1e}%")


@check("SR1", "short-run closure limited to the years given (0.3.7)")
def sr1():
    from infinity_gem.dynamic import DynamicCGE
    from infinity_gem.settings import dynamic_kwargs
    shock = {2026: {"qinv_scale": {"ccons": 0.95}}, 2028: {"qinv_scale": {"ccons": 0.95}}}
    d = DynamicCGE(**dynamic_kwargs("0.3 recommended"))
    d.baseline()
    old = d.scenario(shock).table.closure
    d.a["short_run_years"] = (2025, 2026, 2027)
    lim = d.scenario(shock).table.closure
    d.a["short_run_years"] = None
    again = d.scenario(shock).table.closure
    ok = (old[2026] == "short run" and old[2028] == "short run" and lim[2026] == "short run" and lim[2028] == "long run"
          and (again == old).all())
    return ok, (f"shock years 2026 and 2028: default -> {old[2026]}, {old[2028]}; short_run_years 2025-2027 -> "
                f"{lim[2026]}, {lim[2028]}; None again -> same as default: {(again == old).all()}")


@check("WC1", "short-run wage curve (0.3.7)")
def wc1():
    from infinity_gem.dynamic import DynamicCGE
    from infinity_gem.settings import dynamic_kwargs
    shock = {2026: {"qinv_scale": {"ccons": 0.8}}}
    d = DynamicCGE(**dynamic_kwargs("0.3 recommended"))
    b = d.baseline()
    F = d.m.F
    lab = [k for k, f in enumerate(F) if f.startswith("flab")]
    def run(beta):
        d.a["wage_curve"] = beta
        s = d.scenario(shock)
        z = d.scenario({2026: {}})
        e = max(float(s.solutions[2026]["EMP"][k] / b.solutions[2026]["EMP"][k] - 1) for k in lab)
        emin = min(float(s.solutions[2026]["EMP"][k] / b.solutions[2026]["EMP"][k] - 1) for k in lab)
        w = min(float(s.solutions[2026]["WF"][k] / s.solutions[2026]["CPI"] / (b.solutions[2026]["WF"][k] / b.solutions[2026]["CPI"])) - 1 for k in lab)
        zg = float((z.table.real_gdp - b.table.real_gdp).abs().max())
        # the fixed point holds: wage anchor (real or in pesos, as the model's wage rule) = baseline x (EMP/EMP_baseline) ** beta
        ix = (lambda sol: float(sol["CPI"])) if d.ms.wage == "real" else (lambda sol: 1.0)
        S2, B2 = s.solutions[2026], b.solutions[2026]
        fp = 0.0 if not beta else max(abs(float(S2["WF"][k]) / ix(S2) / (float(B2["WF"][k]) / ix(B2))
                                          - min(1.0, float(S2["EMP"][k] / B2["EMP"][k])) ** beta)
                                      for k in lab if F[k] in d.a["short_run_unemployed"])
        return emin, w, zg, fp, s
    e0, w0, z0, _, s0 = run(None)
    e1, w1, z1, fp, _ = run(2.4)
    d.a["wage_curve"] = None
    again = d.scenario(shock)
    same = float((again.table.real_gdp - s0.table.real_gdp).abs().max())
    ok = e0 < e1 < 0 and w1 < w0 + 1e-12 and z1 < 1e-6 and fp < 1e-8 and same < 1e-12
    return ok, (f"20% construction cut in 2026: largest job loss {e0 * 100:.2f}% at fixed wages, {e1 * 100:.2f}% with beta 2.4 "
                f"(real wage {w1 * 100:+.2f}%); zero shock gap {z1:.1e}; fixed point {fp:.1e}; None again = old: {same:.1e}")


@check("EX1", "peso shock in short-run years (0.3.7)")
def ex1():
    from infinity_gem.dynamic import DynamicCGE
    from infinity_gem.settings import dynamic_kwargs
    d = DynamicCGE(**dynamic_kwargs("0.3 recommended"))
    b = d.baseline()
    z = d.scenario({2026: {}})
    one = d.scenario({2026: {"exr_scale": 1.0}})
    s = d.scenario({2026: {"exr_scale": 1.02}})
    same = float((one.table.real_gdp - z.table.real_gdp).abs().max())
    r = float(s.solutions[2026]["EXR"] / b.solutions[2026]["EXR"])
    cpi = float(s.solutions[2026]["CPI"] / z.solutions[2026]["CPI"]) - 1
    gdp = float(s.table.real_gdp[2026] / z.table.real_gdp[2026]) - 1
    kw = dynamic_kwargs("0.3 recommended")
    kw["short_run_years"] = (2026,)
    d2 = DynamicCGE(**kw)
    d2.baseline()
    try:
        d2.scenario({2027: {"exr_scale": 1.02}})
        refused = False
    except ValueError:
        refused = True
    ok = same < 1e-12 and abs(r - 1.02) < 1e-10 and cpi > 0 and refused
    return ok, (f"exr_scale 1.0 = no shock: {same:.1e}; 1.02 in 2026: peso {r:.6f} x baseline, consumer prices {cpi * 100:+.2f}%, "
                f"real GDP {gdp * 100:+.3f}%; refused in a long-run year: {refused}")


@check("VD1", "VAR decomposition from a chosen date (0.3.7)")
def vd1():
    import pandas as pd
    from infinity_gem import svar
    rng = np.random.default_rng(7)
    T, k = 240, 3
    A1 = np.array([[0.5, 0.0, 0.0], [0.2, 0.4, 0.1], [0.1, -0.2, 0.3]])
    Y = np.zeros((T, k))
    for t in range(1, T):
        Y[t] = 0.1 + A1 @ Y[t - 1] + rng.standard_normal(k) * [1.0, 0.5, 0.8]
    m = svar.fit(pd.DataFrame(Y, columns=["w", "x", "y"]), 2, exog_block=["w"])
    B0 = svar.cholesky(m)
    s = 200
    r = svar.decomposition_since(m, B0, s, D_after=np.ones((6, 1)))
    exact = float(np.abs(r["forecast"] + r["contribution"].sum(axis=2) - r["actual"])[:T - s].max())
    hd = svar.historical_decomposition(m, B0)
    r0 = svar.decomposition_since(m, B0, m.p)
    same = max(float(np.abs(r0["forecast"] - hd["baseline"]).max()), float(np.abs(r0["contribution"] - hd["contribution"]).max()))
    # after the data: no new shocks, so each shock's part follows the model's own dynamics
    c = r["contribution"]
    carry = float(np.abs(c[T - s] - sum(m.lag(L) @ c[T - s - L] for L in range(1, m.p + 1))).max())
    ok = exact < 1e-10 and same < 1e-10 and carry < 1e-12
    return ok, (f"actual = forecast + parts: {exact:.1e}; from the start = historical decomposition: {same:.1e}; "
                f"after the data, parts follow the lags: {carry:.1e}")


@check("IC1", "investment closure and the peso in short-run years (0.3.8)")
def ic1():
    from infinity_gem.dynamic import DynamicCGE
    from infinity_gem.settings import cge_kwargs, dynamic_kwargs
    from infinity_gem.cge import CGE
    shock = {2026: {"qinv_scale": {"ccons": 0.8}}}
    d0 = DynamicCGE(**dynamic_kwargs("0.3 recommended"))
    b0 = d0.baseline()
    s0 = d0.scenario(shock)
    dsv = DynamicCGE(**dynamic_kwargs("0.3 recommended"), investment_closure="savings")
    bsv = dsv.baseline()
    zsv = float((dsv.scenario({2026: {}}).table.real_gdp / bsv.table.real_gdp - 1).abs().max())
    ssv = dsv.scenario(shock)
    inv30 = float(ssv.table.real_investment[2030] / bsv.table.real_investment[2030] - 1)
    g30_0 = float(s0.table.real_gdp[2030] / b0.table.real_gdp[2030] - 1)
    g30_sv = float(ssv.table.real_gdp[2030] / bsv.table.real_gdp[2030] - 1)
    dfx = DynamicCGE(**dynamic_kwargs("0.3 recommended"), sr_fx="flexible")
    bfx = dfx.baseline()
    zfx = float((dfx.scenario({2026: {}}).table.real_gdp / bfx.table.real_gdp - 1).abs().max())
    sfx = dfx.scenario(shock)
    fs = abs(float(sfx.solutions[2026]["FSAV"]) / float(bfx.solutions[2026]["FSAV"]) - 1)
    peso = float(sfx.solutions[2026]["EXR"] / bfx.solutions[2026]["EXR"] - 1)
    dold = DynamicCGE(**dynamic_kwargs("0.3 recommended"), investment_closure="baseline", sr_fx="fixed")
    dold.baseline()
    same = float((dold.scenario(shock).table.real_gdp - s0.table.real_gdp).abs().max())
    kw = cge_kwargs("0.3 recommended")
    path = kw.pop("path")
    kw["wage"] = "real"
    try:
        CGE.from_sam(path, **kw, closure="keynesian", unemployed=("flab-n",), capital="fixed", fx="flexible")
        refused1 = False
    except ValueError:
        refused1 = True
    try:
        dfx.scenario({2026: {"exr_scale": 1.02}})
        refused2 = False
    except ValueError:
        refused2 = True
    ok = (zsv < 1e-9 and zfx < 1e-9 and inv30 < 0 and g30_sv < g30_0 and fs < 1e-9 and same < 1e-12 and refused1 and refused2)
    return ok, (f"zero shock: savings-driven {zsv:.1e}, flexible peso {zfx:.1e}; 20% construction cut in 2026: 2030 investment "
                f"{inv30 * 100:+.2f}% (savings-driven), 2030 GDP {g30_sv * 100:+.3f}% vs {g30_0 * 100:+.3f}% (baseline investment); "
                f"flexible peso: foreign savings {fs:.1e} off baseline, peso {peso * 100:+.2f}%; options left out = old: {same:.1e}; "
                f"refused: CPI-indexed wages {refused1}, peso shock {refused2}")


@check("PS1", "prices rigid downward in short-run years (0.3.8)")
def ps1():
    from infinity_gem.cge import CGE
    from infinity_gem.dynamic import PSA_INDUSTRIES, DynamicCGE
    from infinity_gem.settings import cge_kwargs, dynamic_kwargs
    kw = cge_kwargs("0.3 recommended")
    path = kw.pop("path")
    flexible = set(PSA_INDUSTRIES["Agriculture, forestry, and fishing"] + PSA_INDUSTRIES["Mining and quarrying"])
    base = dict(closure="keynesian", unemployed=("flab-n", "flab-p", "flab-s"), capital="fixed", **kw)
    mf = CGE.from_sam(path, **base)
    ms = CGE.from_sam(path, **base, pricing="sticky", sticky_acts=[a for a in mf.A if a not in flexible])
    bench = ms.solve()
    cut, imp = {"qinv_scale": {"ccons": 0.9}}, {"pwm_scale": {"cchem": 1.3}}
    f_cut, f_imp = mf.solve(cut), mf.solve(imp)
    z_cut = ms.solve({**cut, "stickiness": 0.0})
    s_cut, s_imp = ms.solve({**cut, "stickiness": 0.7}), ms.solve({**imp, "stickiness": 0.7})
    same0 = max(abs(float(z_cut["CPI"]) - float(f_cut["CPI"])), abs(ms.gdp(z_cut)["real"] - mf.gdp(f_cut)["real"]))
    fall_f, fall_s = 1 - float(f_cut["CPI"]), 1 - float(s_cut["CPI"])
    rise_f, rise_s = float(f_imp["CPI"]) - 1, float(s_imp["CPI"]) - 1
    walras = max(abs(float(s_cut["WALRAS"])), abs(float(s_imp["WALRAS"]))) / float(ms.qinv.sum())
    d = DynamicCGE(**dynamic_kwargs("0.3 recommended"), sr_pricing="sticky", sr_stickiness=0.7)
    b = d.baseline()
    zd = float((d.scenario({2026: {}}).table.real_gdp / b.table.real_gdp - 1).abs().max())
    ok = (bench.ok and bench.residual_max < 1e-9 and same0 < 1e-9 and s_cut.ok and s_imp.ok and 0 < fall_s < fall_f
          and abs(rise_s / rise_f - 1) < 0.01 and walras < 1e-6 and zd < 1e-9)
    return ok, (f"benchmark residual {bench.residual_max:.1e}; stickiness 0 = flexible: {same0:.1e}; 10% construction cut: consumer "
                f"prices -{fall_f * 100:.2f}% flexible, -{fall_s * 100:.2f}% at stickiness 0.7; 30% import-price rise (chemicals and "
                f"fuels): +{rise_f * 100:.2f}% vs +{rise_s * 100:.2f}%; Walras/investment {walras:.1e}; dynamic zero shock {zd:.1e}")


@check("S4", "updated SAM, 2024 and 2025 (0.3.8)")
def s4():
    import importlib.util
    from infinity_gem.sam import SAM
    from infinity_gem.settings import cge_kwargs, cge_model
    spec = importlib.util.spec_from_file_location("update_sam", ROOT / "tools" / "update_sam.py")
    us = importlib.util.module_from_spec(spec); spec.loader.exec_module(us)
    out = []
    ok = True
    for y in (2024, 2025):
        S, diag, ctl, _, _ = us.build(y)
        f = SAM.load(paths.sam_updated(y))
        same = float(np.abs(f.table.values - S.table.loc[f.codes, f.codes].values).max())
        gap = float(np.abs(ctl["achieved"] - ctl["target"]).max())
        m = cge_model("0.3 recommended", rice=True, sam_year=y)
        b = m.solve()
        ok = ok and same < 1e-6 and diag["max row-column gap"] < 1e-6 and gap < 1e-6 and b.ok and b.residual_max < 1e-8
        out.append(f"{y}: file = rebuild {same:.1e}, balance {diag['max row-column gap']:.1e}, controls {gap:.1e}, "
                   f"benchmark residual {b.residual_max:.1e}")
    default = cge_kwargs("0.3 recommended", rice=True, sam_variant="ifpri")["path"] == paths.SAM_2023_RICE   # 0.3.10: IFPRI named
    return ok and default, "; ".join(out) + f"; sam_year left out (IFPRI) = 2023 SAM: {default}"


@check("S5", "PSA-consistent 2023 SAM, taxes on products counted once (0.3.9)")
def s5():
    import importlib.util
    from infinity_gem.sam import SAM
    from infinity_gem.settings import cge_kwargs, cge_model
    spec = importlib.util.spec_from_file_location("build_sam_psa_consistent", ROOT / "tools" / "build_sam_psa_consistent.py")
    bp = importlib.util.module_from_spec(spec); spec.loader.exec_module(bp)
    S, s0, diag, ctl, tc, lab, psa = bp.build()
    f = SAM.load(paths.SAM_2023_RICE_PSA)
    same = float(np.abs(f.table.values - S.table.loc[f.codes, f.codes].values).max())
    e0, e1 = bp.expenditure(s0.table, s0), bp.expenditure(f.table, f)
    hfce = abs(e1["household consumption"] - psa["hfce"])
    A = s0.accounts("a")
    lab_same = float(np.abs(f.table.loc[list(bp.LABOUR), A].values - s0.table.loc[list(bp.LABOUR), A].values).max())
    kept = max(abs(e1[k] - e0[k]) for k in ("taxes on products", "government consumption", "fixed investment", "stock change",
                                              "exports", "imports"))
    cut = abs((e0["value added"] - e1["value added"]) - (e0["household consumption"] - e1["household consumption"]))
    gap = float(np.abs(ctl["achieved"] - ctl["target"]).max())
    m = cge_model("0.3 recommended", rice=True, sam_variant="psa")
    b = m.solve()
    rep = float((m.rebuild_sam(b) - m.sam.table).abs().values.max())
    default = cge_kwargs("0.3 recommended", rice=True, sam_variant="ifpri")["path"] == paths.SAM_2023_RICE   # 0.3.10: IFPRI named
    #: the 2024 and 2025 SAMs rebased on this SAM rebuild exactly, balance, meet their controls and calibrate
    spec2 = importlib.util.spec_from_file_location("update_sam", ROOT / "tools" / "update_sam.py")
    us = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(us)
    rebased = []
    for y in (2024, 2025):
        Sy, dy, cy, _, _ = us.build(y, base="psa")
        fy = SAM.load(paths.sam_updated(y, base="psa"))
        sy = float(np.abs(fy.table.values - Sy.table.loc[fy.codes, fy.codes].values).max())
        gy = float(np.abs(cy["achieved"] - cy["target"]).max())
        by = cge_model("0.3 recommended", rice=True, sam_variant="psa", sam_year=y).solve()
        ok_y = sy < 1e-6 and dy["max row-column gap"] < 1e-6 and gy < 1e-6 and by.ok and by.residual_max < 1e-8
        rebased.append((y, ok_y, sy, gy, by.residual_max))
    ok = (same < 1e-6 and diag["max row-column gap"] < 1e-6 and hfce < 1e-6 and lab_same == 0 and kept < 1e-6 and cut < 1e-6
          and gap < 1e-6 and b.ok and b.residual_max < 1e-8 and rep < 1e-5 and default and all(r[1] for r in rebased))
    return ok, (f"file = rebuild {same:.1e}; balance {diag['max row-column gap']:.1e}; HFCE - PSA {hfce:.1e}; labour income "
                f"unchanged {lab_same:.0e}; kept items {kept:.1e}; value-added cut = consumption cut {cut:.1e}; controls {gap:.1e}; "
                f"benchmark residual {b.residual_max:.1e}; SAM reproduced {rep:.1e}; sam_variant left out = IFPRI SAM: {default}; "
                + "; ".join(f"{y} rebased: rebuild {sy:.0e}, controls {gy:.0e}, benchmark {ry:.0e}" for y, _, sy, gy, ry in rebased))


@check("S6", "Infinity GEM's own 2023 SAM, latest version (0.3; 0.3.9)")
def s6():
    import importlib.util
    from infinity_gem.sam import SAM
    from infinity_gem.settings import cge_kwargs, cge_model, short_run_closure
    from infinity_gem.dynamic import PSA_INDUSTRIES
    spec = importlib.util.spec_from_file_location("build_own_sam_2023", ROOT / "tools" / "build_own_sam_2023.py")
    bs = importlib.util.module_from_spec(spec); spec.loader.exec_module(bs)
    S, s78, diag, ctl, ind, fg, psa, extra = bs.build()
    f = SAM.load(paths.SAM_2023_OWN)
    t = f.table
    same = float(np.abs(t.values - S.table.loc[f.codes, f.codes].values).max())
    e = bs.P.expenditure(t, f)
    targets = {"household consumption": psa["hfce"], "government consumption": psa["gfce"], "fixed investment": psa["gfcf"],
               "stock change": psa["gcf"] - psa["gfcf"], "exports": psa["exports"], "imports": psa["imports"], "GDP (expenditure)": psa["gdp"]}
    macro = max(abs(e[k] - v) for k, v in targets.items())
    L, NL = list(bs.P.LABOUR), list(bs.P.NONLAB)
    va = max(abs(float(t.loc[L + NL, [a for a in acts if a in t.columns]].values.sum()) - ind.loc[k, "value added at basic prices"])
             for k, acts in PSA_INDUSTRIES.items())
    lab = max(abs(float(t.loc[L, [a for a in acts if a in t.columns]].values.sum()) - ind.loc[k, "labour income"])
              for k, acts in PSA_INDUSTRIES.items())
    H, C, A = f.accounts("hhd"), f.accounts("c"), f.accounts("a")
    cons = t.loc[C, H].sum() + t.loc[A, H].sum()
    purpose = float((bs.by_purpose(t, f) - bs.hfce_by_purpose_2023() * psa["hfce"] / bs.hfce_by_purpose_2023().sum()).abs().max())  # v0.3
    grp = max(float((cons / cons.sum() - fg["TOTEX"] / fg["TOTEX"].sum()).abs().max()),
              float((t.loc[H, L].sum(axis=1) / t.loc[H, L].values.sum() - fg["WAGES"] / fg["WAGES"].sum()).abs().max()),
              float((t.loc[H, "row"] / t.loc[H, "row"].sum() - fg["CASH_ABROAD"] / fg["CASH_ABROAD"].sum()).abs().max()))
    m = cge_model("0.3 recommended", rice=True, sam_variant="own")
    b = m.solve()
    rep = float((m.rebuild_sam(b) - m.sam.table).abs().values.max())
    m2 = cge_model("0.3 recommended", rice=True, sam_variant="own", **short_run_closure("0.3 recommended"), land="fixed")
    b2 = m2.solve()
    s2 = m2.solve({"qinv_scale": {"ccons": 0.9}})
    dg = (m2.gdp(s2)["real"] / m2.gdp(b2)["real"] - 1) * 100
    # 0.3.10 (18 Oct 2026): Infinity GEM's own SAM is the default for rice=True runs; "ifpri" still gives IFPRI's
    default = (cge_kwargs("0.3 recommended", rice=True)["path"] == paths.SAM_2023_OWN
               and cge_kwargs("0.3 recommended", rice=True, sam_variant="ifpri")["path"] == paths.SAM_2023_RICE)
    ok = (same < 1e-6 and diag["max row-column gap"] < 1e-6 and macro < 1e-6 and va < 1e-6 and lab < 1e-6 and grp < 1e-9 and purpose < 1e-6
          and b.ok and b.residual_max < 1e-8 and rep < 1e-5 and s2.ok and -3 < dg < 0 and default)
    return ok, (f"file = rebuild {same:.1e}; balance {diag['max row-column gap']:.1e}; PSA expenditure items and GDP {macro:.1e}; "
                f"industry value added {va:.1e}, labour {lab:.1e}; FIES group shares {grp:.1e}; consumption by purpose {purpose:.1e}; benchmark residual "
                f"{b.residual_max:.1e}; SAM reproduced {rep:.1e}; short run, 10% construction cut: real GDP {dg:.3f}%; "
                f"sam_variant left out = Infinity GEM's own SAM ({paths.SAM_2023_OWN.stem.split('_own_')[-1]}), 'ifpri' = IFPRI SAM: {default}")


@check("ML2", "MicroLink concordance: chemicals out of UTILITIES and TRANSPORT on split SAMs (default since 18 Oct 2026)")
def ml2():
    from infinity_gem import microlink
    from infinity_gem.cge import CGE
    from infinity_gem.microlink import MicroLink
    from infinity_gem.settings import cge_model
    m = cge_model("0.3 recommended", rice=True)                  # refined petroleum split from chemicals
    b = m.solve()
    base, fix = MicroLink(m, fuel_split_map=False), MicroLink(m)   # default since 18 Oct 2026: the fuel-split map
    old_kept = base.cmap is microlink.CATEGORY_MAP                 # the old map, for the 2026 scenario numbers of 17 Oct 2026
    default_fixed = fix.cmap is not microlink.CATEGORY_MAP
    chem_out = float(fix.W.loc[["UTILITIES", "TRANSPORT"], "cchem"].abs().max())
    chem_before = float(base.W.loc[["UTILITIES", "TRANSPORT"], "cchem"].sum())
    cover = abs(fix.W.values.sum() / fix.hh_cons.sum() - 1)
    cat10 = float((fix.category_prices(m, b, {"PQ": b["PQ"] * 1.1}) - 10).abs().max())
    link = fix.link_variables(m, b, b)                            # as ML1: a real link, then every category +10%
    link["fies_categories"] = link["fies_categories"].assign(price_change_pct=10.0)
    fam10 = float((fix.family_inflation(link) - 10).abs().max())
    u = CGE.from_sam(paths.SAM_2023)                              # IFPRI's SAM as published: fuel inside chemicals
    nosplit = float((MicroLink(u).W - MicroLink(u, fuel_split_map=False).W).abs().values.max())
    ok = old_kept and default_fixed and chem_out == 0 and chem_before > 0 and cover < 1e-9 and cat10 < 1e-9 and fam10 < 1e-9 and nosplit == 0
    return ok, (f"default = fuel-split map: {default_fixed}; old map kept (fuel_split_map=False): {old_kept}; chemicals in UTILITIES and TRANSPORT ₱{chem_before:,.1f} bn -> {chem_out:.1f}; "
                f"household consumption attributed {1 - cover:.12f}; all prices +10% -> categories {cat10:.1e}, families {fam10:.1e}; "
                f"SAM without petroleum split: weights change {nosplit:.1e}")


@check("PC1", "consumer prices on PSA's CPI weights (reporting; 0.3.10)")
def pc1():
    from infinity_gem import psa_cpi
    from infinity_gem.microlink import MicroLink
    from infinity_gem.settings import cge_model
    m = cge_model("0.3 recommended", rice=True)                  # the petroleum-split SAM the PSA map needs
    b = m.solve()
    ml = MicroLink(m)
    link = ml.link_variables(m, b, b)                            # no shock: every PSA group price change is zero
    zero = max(abs(v) for v in psa_cpi.change(link).values())
    link["fies_categories"] = link["fies_categories"].assign(price_change_pct=10.0)
    link["commodities"] = link["commodities"].assign(consumer_price_pq_pct=10.0)
    ten = max(abs(v - 10.0) for v in psa_cpi.change(link).values())
    sums = [float(psa_cpi.weights(n).sum()) for n in psa_cpi.FILES]
    ok = all(abs(s - 100) < 1e-6 for s in sums) and zero < 1e-9 and ten < 1e-9
    return ok, (f"mapped PSA weights sum to {sums[0]:.6f} (all households) and {sums[1]:.6f} (bottom 30%); "
                f"no shock -> {zero:.1e}; every price +10% -> error {ten:.1e}")


@check("X3", "DSGE research code (0.3.11): solver, open economy, pass-through, Kalman")
def x3():
    import subprocess
    d = ROOT / "research" / "dsge"
    out = []
    for t in ("test_milestone1.py", "test_milestone2.py", "test_milestone3.py", "test_milestone5.py", "test_milestone6.py", "test_milestone8.py",
              "test_milestone10.py",                      # 19 Oct 2026, about 8:35 AM: rule-of-thumb price setters (soe_rot.py)
              "test_milestone11.py",                      # 19 Oct 2026, about 9:30 AM: hand-to-mouth, adaptive expectations (soe_htm.py)
              "test_milestone15.py",                      # 19 Oct 2026, about 2:30 PM: oil as an imported good and input (soe_oil.py)
              "test_milestone18.py",                      # 19 Oct 2026, about 11:20 PM: missing data (COVID quarters), long sample
              "test_milestone19.py",                      # 20 Oct 2026, about 01:45: domestic cost-push shock (soe_htmu.py)
              "test_milestone21.py",                      # 20 Oct 2026, about 9:20 AM: oil supply vs world oil demand (soe_oilw.py)
              "test_milestone22.py",                      # 21 Oct 2026, about 1:25 AM: flexible energy-intensive prices in the CPI (soe_oilf.py)
              "test_milestone23.py",                      # 21 Oct 2026, about 1:40 AM: capital and investment adjustment costs (soe_htmk.py)
              "test_milestone23c.py",                     # 21 Oct 2026, about 11:30 PM: investment data as an observable (obs=inv)
              "test_milestone24.py",                      # 22 Oct 2026, about 5:05 PM: the investment-specific shock (soe_htmki.py)
              "test_milestone25.py",                      # 22-23 Oct 2026, night: a flexible-price share of the CPI (soe_htmkf.py)
              "test_smc.py"):                             # 21 Oct 2026, about 1:05 AM: the sequential Monte Carlo sampler (smc.py)
        r = subprocess.run([sys.executable, "-I", str(d / t)], capture_output=True, text=True, cwd=str(d), timeout=600)
        last = [l for l in r.stdout.splitlines() if l.strip()][-1] if r.stdout.strip() else "no output"
        out.append((t, r.returncode == 0, last))
    sys.path.insert(0, str(d))
    try:
        import estimate as E
        from scipy import linalg, stats
        th = np.array([2.0, 0.70, 0.55, 1.6, 0.30, 0.75, 0.80, 0.85, 0.45, 0.30, 0.30, 0.60, 0.50, 0.40])
        Z = E.simulate(th, 10, seed=3)
        Pm, Rm, Q, H = E.state_space(th)
        Sig = linalg.solve_discrete_lyapunov(Pm, Rm @ Q @ Rm.T)
        T_, m_ = Z.shape
        C = np.zeros((T_ * m_, T_ * m_))
        for s_ in range(T_):
            for u in range(T_):
                blk = H @ np.linalg.matrix_power(Pm, abs(s_ - u)) @ Sig @ H.T
                C[s_ * m_:(s_ + 1) * m_, u * m_:(u + 1) * m_] = blk if s_ >= u else blk.T
        C += np.eye(T_ * m_) * 1e-4
        kf, bf = E.kalman_loglik(Pm, Rm, Q, H, Z), stats.multivariate_normal(np.zeros(T_ * m_), C).logpdf(Z.ravel())
    finally:
        sys.path.remove(str(d))
    ok = all(o for _, o, _ in out) and abs(kf - bf) < 1e-6 * abs(bf)
    return ok, "; ".join(f"{t[:-3]} {last}" for t, _, last in out) + f"; Kalman {kf:.6f} = exact {bf:.6f}"


@check("HD1", "paid labour hoarding (0.3.11): off = unchanged; on = accounts close; tamper caught")
def hd1():
    from infinity_gem.cge import CGE
    kw = dict(closure="keynesian", unemployed=("flab-n", "flab-p"), capital="fixed")
    m0, mh = CGE.from_sam(**kw), CGE.from_sam(**kw, hoarding=0.8)
    b0 = m0.solve()
    spec = {"qinv_scale": {"ccons": 0.8}}
    s0, s_off, sh = m0.solve(spec), mh.solve(spec), mh.solve(dict(spec, hoard_ref=b0["QF"]))
    same = max(float(np.abs(np.asarray(s0[k]) - np.asarray(s_off[k])).max()) for k in ("QA", "EMP", "YH", "PQ"))
    S = mh.rebuild_sam(sh)                                     # rebuild_sam does not record the Keynesian closure's foreign
    tot = float(S.values.sum())                                # saving change (s-i and row; also without hoarding): left out
    keep = [c for c in S.index if c not in ("s-i", "row")]
    gap = lambda X: float(np.abs((X.sum(axis=1) - X.sum(axis=0)).loc[keep]).max()) / tot
    imb = gap(S)
    net = lambda s: float(np.asarray(s["YF"]).sum() - (s["W"] * s["QF"]).sum())   # factor income less value added
    idn = abs(net(sh) - net(s0))                               # = the same (foreign factor income): hoarded wages net out
    HB = sh["W"] * sh["QFH"]
    T_ = S.copy()
    T_.loc["fcap", mh.A] = T_.loc["fcap", mh.A].values + HB.sum(axis=0)      # tamper: hoarded wages not taken from capital
    imb_t = gap(T_)
    a = mh.A.index("acons")
    lab = [k for k, f in enumerate(mh.F) if f.startswith("flab")]
    e0 = float(s0["QF"][lab, a].sum() / b0["QF"][lab, a].sum() - 1)
    eh = float((sh["QF"] + sh["QFH"])[lab, a].sum() / b0["QF"][lab, a].sum() - 1)
    ok = (s0.ok and s_off.ok and sh.ok and same < 1e-10 and imb < 1e-9 and idn < 1e-8 and abs(sh["WALRAS"]) / mh.qinv.sum() < 1e-9 and HB.sum() > 0
          and abs(eh) < abs(e0) and imb_t > 1e-6)
    return ok, (f"no reference: largest change {same:.1e}; h 0.8, construction investment -20%: SAM imbalance {imb:.1e} (all but s-i, row), "
                f"factor-income identity {idn:.1e}, Walras {abs(sh['WALRAS']) / mh.qinv.sum():.1e}, hoarded wages {HB.sum():.2f} bn; construction jobs {e0:+.2%} -> {eh:+.2%}; "
                f"tampered SAM imbalance {imb_t:.1e} (caught)")


@check("EN1", "value added-energy bundle (0.3.11): benchmark, homogeneity, substitution, Leontief limit; tamper caught")
def en1():
    from infinity_gem import settings
    mk = lambda **kw: settings.cge_model("0.3 recommended", rice=True, **kw)
    m0 = mk()
    E = [c for c in ("cpetr", "celec") if c in m0.C]
    mE = mk(energy_nest={"energy": E, "sigma_ve": 0.5, "sigma_e": 1.5})
    mL = mk(energy_nest={"energy": E, "sigma_ve": 0.01, "sigma_e": 0.01})
    b0, bE, bL = m0.solve(), mE.solve(), mL.solve()
    S0, SE = m0.rebuild_sam(b0), mE.rebuild_sam(bE)
    rep0 = float(np.max(np.abs(S0.values - m0.sam.table.loc[S0.index, S0.columns].values)))
    rep = float(np.max(np.abs(SE.values - mE.sam.table.loc[SE.index, SE.columns].values)))
    h = mE.solve({"cpi": 2.0})
    hom = float(np.max(np.abs(np.asarray(h["QA"]) / np.asarray(bE["QA"]) - 1)))
    shock = {"pwm_scale": {E[0]: 1.3}}
    ei = [m0.C.index(c) for c in E]
    use = lambda s, b: float(s["QINT"][ei].sum() / s["QA"].sum() / (b["QINT"][ei].sum() / b["QA"].sum()) - 1)
    s0, sE, sL = m0.solve(shock), mE.solve(shock), mL.solve(shock)
    u0, uE, uL = use(s0, b0), use(sE, bE), use(sL, bL)
    S = mE.rebuild_sam(sE)
    keep = [c for c in S.index if c not in ("s-i", "row")]
    gap = lambda X: float(np.abs((X.sum(axis=1) - X.sum(axis=0)).loc[keep]).max()) / float(X.values.sum())
    T_ = S.copy()                                              # tamper: energy inputs back at Leontief quantities
    en = mE.en["E"]
    T_.loc[[mE.C[i] for i in en], mE.A] = mE.ica[en] * np.asarray(sE["QA"])[None, :] * np.asarray(sE["PQ"])[en][:, None]
    imb, imb_t = gap(S), gap(T_)
    # 19 Oct 2026, about 11:05 PM: a short-run bundle (0.1/0.5) centred on the shocked point of the 0.5/1.5 model reproduces
    # that model's bundle choices there (energy_shares_at); centred on the benchmark it returns the SAM's shares; tamper:
    # the SAM's shares at the shocked point miss it
    mS = mk(energy_nest={"energy": E, "sigma_ve": 0.1, "sigma_e": 0.5})
    ref = mE._energy_nest(sE["PQ"], sE["PVA"], sE["QA"])
    cen = lambda sh: max(float(np.max(np.abs(x - y))) for x, y in zip(ref, mS._energy_nest(sE["PQ"], sE["PVA"], sE["QA"], sh)))
    rc, rc_t = cen(mS.energy_shares_at(sE["PQ"], sE["PVA"], sE["QA"], mE)), cen(None)
    shb = mS.energy_shares_at(np.ones(len(mS.C)), np.ones(len(mS.A)) / mS.tfp, mS.QA0, mS)
    rb = max(float(np.max(np.abs(shb[k] - mS.en[k]))) for k in ("dva", "den", "de"))
    ok = (b0.ok and bE.ok and bL.ok and s0.ok and sE.ok and sL.ok and rep <= max(10 * rep0, 1e-6) and hom < 1e-9 and uE < -0.01
          and abs(uL - u0) < 0.005 and imb < 1e-9 and imb_t > 1e-6 and rc < 1e-9 and rb < 1e-12 and rc_t > 1e-6)
    return ok, (f"benchmark SAM gap {rep:.1e} (without the bundle {rep0:.1e}); homogeneity {hom:.1e}; {E[0]} world price +30%: energy per unit "
                f"of output {u0:+.2%} (Leontief), {uE:+.2%} (0.5/1.5), {uL:+.2%} (0.01/0.01); rebuilt SAM imbalance {imb:.1e}; "
                f"tampered {imb_t:.1e} (caught); short-run bundle centred on the shocked point {rc:.1e} (SAM's shares {rc_t:.1e}, caught), "
                f"on the benchmark {rb:.1e}")


@check("EN2", "value added-energy bundle in the dynamic hybrid (0.3.11): short-run years with lower elasticities "
              "reproduce the baseline when nothing is shocked")
def en2():
    from infinity_gem.dynamic import DynamicCGE
    from infinity_gem.settings import dynamic_kwargs
    E = ["cpetr", "celec"]
    kw = dynamic_kwargs("0.3 recommended", public_capital="low", rice=True, land="fixed")
    kw.update(energy_nest={"energy": E, "sigma_ve": 0.8, "sigma_e": 0.5}, sr_energy_nest={"energy": E, "sigma_ve": 0.1, "sigma_e": 0.5},
              short_run_years=(2025, 2026, 2027))
    d = DynamicCGE(**kw)
    base = d.baseline()
    p = d.scenario({2025: {}, 2026: {}})
    g = float(np.max(np.abs(p.table.real_gdp / base.table.real_gdp - 1)))
    sr = [int(y) for y in p.table.index if p.table.loc[y, "closure"] == "short run"]
    ok = g < 1e-9 and sr == [2025, 2026]
    return ok, f"short-run years {sr} (bundle 0.1/0.5, long run 0.8/0.5): largest real GDP gap against the baseline {g:.1e}"


@check("ST1", "sectoral price stickiness (0.3.11): a dict of equal shares = the single share; BSP WPS 2020-02 durations; "
              "fuel flexible; the dynamic model takes the dict")
def st1():
    from infinity_gem import stickiness as STK
    from infinity_gem.cge import CGE
    from infinity_gem.dynamic import DynamicCGE, PSA_INDUSTRIES
    from infinity_gem.settings import cge_kwargs, dynamic_kwargs
    kw = cge_kwargs("0.3 recommended", rice=True)
    path = kw.pop("path")
    flexible = set(PSA_INDUSTRIES["Agriculture, forestry, and fishing"] + PSA_INDUSTRIES["Mining and quarrying"])
    base = dict(closure="keynesian", unemployed=("flab-n", "flab-p", "flab-s"), capital="fixed", **kw)
    acts = [a for a in CGE.from_sam(path, **base).A if a not in flexible]
    ms = CGE.from_sam(path, **base, pricing="sticky", sticky_acts=acts)
    cut = {"qinv_scale": {"ccons": 0.9}}
    s1, s2 = ms.solve({**cut, "stickiness": 0.7}), ms.solve({**cut, "stickiness": {a: 0.7 for a in acts}})
    same = max(float(np.max(np.abs(s1.x - s2.x))), abs(float(s1["CPI"]) - float(s2["CPI"])))
    sec = STK.sectoral(acts)
    s3 = ms.solve({**cut, "stickiness": sec})
    s0 = ms.solve({**cut, "stickiness": 0.6})
    va = {a: float(v) for a, v in zip(ms.A, ms.iva * ms.QA0)}
    wmean = sum(sec[a] * va[a] for a in acts) / sum(va[a] for a in acts)
    rule = STK.share_not_passed(STK.DECREASE_MONTHS["All items"])
    order = sec.get("afood", 0) < sec.get("aeduc", 1) and sec.get("apetr", 1) == 0.0
    differs = abs(float(s3["CPI"]) - float(s0["CPI"])) > 1e-6
    d = DynamicCGE(**dynamic_kwargs("0.3 recommended", rice=True), sr_pricing="sticky", sr_stickiness=STK.sectoral(acts))
    b = d.baseline()
    zd = float((d.scenario({2026: {}}).table.real_gdp / b.table.real_gdp - 1).abs().max())
    ok = (s1.ok and s2.ok and s3.ok and s0.ok and same < 1e-12 and abs(rule - 0.5823) < 1e-3 and 0.5 < wmean < 0.7 and order
          and differs and zd < 1e-9)
    return ok, (f"dict of 0.7 = 0.7: {same:.1e}; all items D 10.0 -> {rule:.3f}; sectoral (value-added weighted) {wmean:.3f}, food "
                f"{sec.get('afood', float('nan')):.2f}, education {sec.get('aeduc', float('nan')):.2f}, fuel {sec.get('apetr', float('nan')):.2f}; "
                f"10% construction cut: consumer prices {float(s3['CPI']) - 1:+.3%} sectoral vs {float(s0['CPI']) - 1:+.3%} at 0.6; "
                f"dynamic zero shock with the dict {zd:.1e}")


@check("IR1", "interest-rate closure (0.3.11): benchmark r = 0; eps = 0 = 'savings', theta = 0 = 'investment'; "
              "a construction cut lowers r and crowds in other investment; dynamic zero shock")
def ir1():
    from infinity_gem.cge import CGE
    from infinity_gem.dynamic import DynamicCGE
    from infinity_gem.settings import cge_kwargs, dynamic_kwargs
    kw = cge_kwargs("0.3 recommended", rice=True)
    path = kw.pop("path")
    cut = {"qinv_scale": {"ccons": 0.9}}
    real = lambda s: np.concatenate([np.atleast_1d(np.asarray(s[k], float)).ravel() for k in ("QA", "QH", "QINV", "QG", "QE", "QM", "CPI", "EXR")])
    mi, ms = CGE.from_sam(path, closure="investment", **kw), CGE.from_sam(path, closure="savings", **kw)
    mr = CGE.from_sam(path, closure="interest", interest={"theta": 2.0, "eps": 0.3}, **kw)
    b_i, b_r = mi.solve({}), mr.solve({})
    bench = max(abs(float(b_r["RINT"])), float(np.max(np.abs(real(b_r) - real(b_i)))))
    s_s, s_0 = ms.solve(cut), CGE.from_sam(path, closure="interest", interest={"theta": 2.0, "eps": 0.0}, **kw).solve(cut)
    lim_s = max(float(np.max(np.abs(real(s_0) - real(s_s)))), abs(float(s_0["RINT"]) + 100 * np.log(float(s_s["IADJ"])) / 2.0))
    s_i, s_t = mi.solve(cut), CGE.from_sam(path, closure="interest", interest={"theta": 0.0, "eps": 0.3}, **kw).solve(cut)
    lim_i = max(float(np.max(np.abs(real(s_t) - real(s_i)))), abs(float(s_t["RINT"]) - 100 * float(s_i["MPSADJ"]) / 0.3))
    s_r = mr.solve(cut)
    oth = [j for j, c in enumerate(mr.C) if c != "ccons"]
    crowd = float(s_r["QINV"][oth].sum() / b_r["QINV"][oth].sum() - 1)
    d = DynamicCGE(**dynamic_kwargs("0.3 recommended", rice=True), closure="interest", interest={"theta": 2.0, "eps": 0.3})
    b = d.baseline()
    zd = float((d.scenario({2026: {}}).table.real_gdp / b.table.real_gdp - 1).abs().max())
    ok = (all(x.ok for x in (b_i, b_r, s_s, s_0, s_i, s_t, s_r)) and bench < 1e-8 and lim_s < 1e-8 and lim_i < 1e-8
          and float(s_r["RINT"]) < 0 and crowd > 0 and zd < 1e-9)
    return ok, (f"benchmark {bench:.1e}; eps = 0 vs 'savings' {lim_s:.1e}; theta = 0 vs 'investment' {lim_i:.1e}; 10% construction "
                f"cut (theta 2, eps 0.3): r {float(s_r['RINT']):+.2f} pp, other investment {crowd:+.2%}; dynamic zero shock {zd:.1e}")


@check("VN1", "within-year capital vintages (0.3.12): benchmark; e = 0 = fixed capital; e = 100 = mobile; "
              "capital conserved; a new-capital pool is hired under complementarity; dynamic baseline bounded and zero shock reproduced")
def vn1():
    from infinity_gem.cge import CGE
    from infinity_gem.dynamic import DynamicCGE
    from infinity_gem.settings import cge_kwargs, dynamic_kwargs
    kw = cge_kwargs("0.3 recommended", rice=True)
    path = kw.pop("path")
    cut = {"qinv_scale": {"ccons": 0.8}}
    qa = lambda s: np.asarray(s["QA"], float)
    mv = CGE.from_sam(path, capital="vintage", vintage={"e": 0.7}, **kw)
    kc, ia = mv.kcap, mv.iK
    b = mv.solve({})
    bench = max(float(b.residual_max), float(np.max(np.abs(b["W"][kc, ia] - 1.0))), float(np.max(np.abs(b["NK"]))))
    s = mv.solve(cut)
    cons = abs(float(s["QF"][kc].sum() / b["QF"][kc].sum()) - 1.0)                         # the stock is fully employed, unchanged
    sf = CGE.from_sam(path, capital="fixed", **kw).solve(cut)
    s0 = CGE.from_sam(path, capital="vintage", vintage={"e": 0.0}, **kw).solve(cut)
    lim_f = float(np.max(np.abs(qa(s0) / qa(sf) - 1)))
    sm = CGE.from_sam(path, capital="mobile", **kw).solve(cut)
    s9 = CGE.from_sam(path, capital="vintage", vintage={"e": 100.0}, **kw).solve(cut)
    lim_m = float(np.max(np.abs(qa(s9) / qa(sm) - 1)))
    sn = mv.solve({"knew": 0.05})                                                            # 5% new capital on offer
    grow = float(sn["QF"][kc].sum() / b["QF"][kc].sum()) - 1.05
    comp = float(np.max(np.abs(sn["NK"] / mv.QF0[kc, ia] * (sn["RN"] - sn["W"][kc, ia]))))     # NK (RN - W) = 0, W <= RN
    comp = max(comp, float(np.max(sn["W"][kc, ia] - sn["RN"])), -float(np.min(sn["NK"])))
    dk = dynamic_kwargs("0.3 recommended", rice=True)
    dk["capital_allocation"] = "vintage"
    d = DynamicCGE(**dk)
    bl = d.baseline()
    disp = max(float(np.max(x["W"][d.kc, d.m.iK]) / np.min(x["W"][d.kc, d.m.iK])) for x in bl.solutions.values())
    zd = float((d.scenario({2026: {}}).table.real_gdp / bl.table.real_gdp - 1).abs().max())
    ok = (all(x.ok for x in (b, s, sf, s0, sm, s9, sn)) and bench < 1e-8 and cons < 1e-9 and lim_f < 1e-5 and lim_m < 2e-3
          and abs(grow) < 1e-6 and comp < 1e-8 and disp < 5.0 and zd < 1e-9)
    return ok, (f"benchmark {bench:.1e}; stock conserved {cons:.1e}; e = 0 vs fixed {lim_f:.1e}; e = 100 vs mobile {lim_m:.1e}; "
                f"new capital 5%: stock {grow + 0.05:+.3%}, complementarity {comp:.1e}; baseline rental dispersion (max/min) {disp:.2f}; "
                f"zero shock {zd:.1e}")


@check("MP1", "a BSP policy rule inside the dynamic model (0.3.12): zero shock leaves the rate at zero and the path on "
              "the baseline; a held rate path reproduces the same investment scales applied by hand; the monetary= setting routes "
              "scenario() to the rule; on a construction cut the rule lowers the rate and cushions the loss; the fixed point converges")
def mp1():
    from infinity_gem.dynamic import DynamicCGE
    from infinity_gem.settings import dynamic_kwargs
    rule = {"rho": 0.7, "phi_pi": 1.5, "phi_x": 0.5, "phi_e": 0.0}        # coefficients for the test only (PAMPh-like smoothing)
    kw = dynamic_kwargs("0.3 recommended", rice=True)
    kw["short_run_years"] = (2026,)                                         # the rule then acts in 2026 (short run) and 2027-2030 (long run)
    d = DynamicCGE(**kw)
    b = d.baseline()
    cut = {2026: {"qinv_scale": {"ccons": 0.9}}}
    s0 = d.scenario(cut)
    z = d.monetary_scenario({2026: {}}, rule=rule, theta=2.0)
    zr = float(z.monetary["policy_rate_gap_pp"].abs().max())
    zd = float((z.table.real_gdp / b.table.real_gdp - 1).abs().max())
    path = {2026: {"i": 1.0, "pi_e": 0.0}, 2027: {"i": 0.5, "pi_e": 0.0}}
    p = d.monetary_scenario(cut, rule=rule, theta=2.0, path=path)
    inv = [c for i, c in enumerate(d.m.C) if d.m.qinv[i] > 0]
    s26, s27 = float(np.exp(-2.0 * 1.0 / 100)), float(np.exp(-2.0 * 0.5 / 100))
    hand = d.scenario({2026: {"qinv_scale": {**{c: s26 for c in inv}, "ccons": 0.9 * s26}}, 2027: {"qinv_scale": {c: s27 for c in inv}}})
    lim_h = max(float((p.table.real_gdp / hand.table.real_gdp - 1).abs().max()), float((p.table.cpi / hand.table.cpi - 1).abs().max()))
    d.a["monetary"] = {"path": path, "theta": 2.0}                          # the setting: scenario() must give the same path
    lim_r = float((d.scenario(cut).table.real_gdp / p.table.real_gdp - 1).abs().max())
    d.a["monetary"] = None
    r = d.monetary_scenario(cut, rule=rule, theta=2.0)
    g0 = float(s0.table.real_gdp[2026] / b.table.real_gdp[2026] - 1) * 100
    g1 = float(r.table.real_gdp[2026] / b.table.real_gdp[2026] - 1) * 100
    pi26, i26 = float(r.monetary.loc[2026, "inflation_gap_pp"]), float(r.monetary.loc[2026, "policy_rate_gap_pp"])
    conv = bool(r.monetary.attrs["converged"]) and r.monetary.attrs["iterations"] <= 15
    ok = zr < 1e-9 and zd < 1e-9 and lim_h < 1e-10 and lim_r < 1e-10 and pi26 < 0 and i26 < 0 and g1 > g0 and conv
    return ok, (f"zero shock: rate {zr:.1e}, GDP {zd:.1e}; held path vs hand {lim_h:.1e}; setting routes scenario() {lim_r:.1e}; "
                f"10% construction cut: inflation gap {pi26:+.2f} pp, rate {i26:+.2f} pp, GDP gap 2026 {g0:+.3f}% without the rule, "
                f"{g1:+.3f}% with it; {r.monetary.attrs['iterations']} iterations, converged {conv}")


def _io_price_markup(m, dpwm, given, mu=None):
    """MK1, test 3: the input-output price model (check I1's formula, dp_r = (I - A_rr')^-1 A_Kr' dp_K), written on the CGE's own
    benchmark coefficients, first order, and sharing no code with cge.py's evaluate(): the home price of each markup commodity
    from (1 - ta) dPDS = (1 + mu) x (its inputs' price changes weighted by ica), wages, the peso and export prices held; the other
    home prices given (the set K: the flexible-price activities, as the CGE has them); imports at world prices (dpwm); Armington
    shares, sales taxes and trade margins as in the SAM. mu = 0 gives the plain cost-push model (value added fixed per unit).
    Returns (dPDS, dPQ)."""
    nC = len(m.C)
    mu = m.mu0 if mu is None else mu
    mkc = m.mkC & m.hasD
    act = {int(m.mk_com[a]): int(a) for a in np.where(m.isMK)[0]}
    mix, onlyM, onlyD = m.hasM & m.hasD, m.hasM & ~m.hasD, m.hasD & ~m.hasM
    icq = m.icq if m.margins == "composite" else np.zeros(nC)    # split margins sit in the import and home prices
    n = 2 * nC + 1

    def T(u):
        dPDS = np.where(mkc, u[:nC], given)
        dPQ, dPT = u[nC:2 * nC], u[-1]
        new = np.zeros(n)
        for c, a in act.items():
            new[c] = (1 + mu[a]) / (1 - m.ta[a]) * float(m.ica[:, a] @ dPQ)
        dPDD, dPM = dPDS + m.icx * dPT, (1 + m.tm) * dpwm + m.icx * dPT
        dPARM = np.zeros(nC)
        dPARM[mix] = (m.QM0[mix] * dPM[mix] + m.QD0[mix] * dPDD[mix]) / m.QQ0[mix]
        dPARM[onlyM], dPARM[onlyD] = m.k_m[onlyM] * dPM[onlyM], m.k_d[onlyD] * dPDD[onlyD]
        new[nC:2 * nC] = np.where(m.hasQ, (1 + m.tq) * (dPARM + icq * dPT), 0.0)
        new[-1] = float(m.sm @ dPQ)
        return new

    b0 = T(np.zeros(n))
    M = np.column_stack([T(e) - b0 for e in np.eye(n)])
    u = np.linalg.solve(np.eye(n) - M, b0)
    return np.where(mkc, u[:nC], given), u[nC:2 * nC]


@check("MK1", "markup pricing in short-run years (0.3.13): zero shock = benchmark and baseline; homogeneity; "
              "cost push = the input-output price model; accounts close; tamper caught")
def mk1():
    from infinity_gem import stickiness as STK
    from infinity_gem.cge import CGE, MARKET_PRICE_ACTS
    from infinity_gem.dynamic import DynamicCGE, PSA_INDUSTRIES
    from infinity_gem.oil import cge_oil_shock
    from infinity_gem.settings import cge_kwargs, dynamic_kwargs, short_run_closure
    kw = cge_kwargs("0.3 recommended", rice=True)                  # Infinity GEM's own SAM (the default), the 2026 scenarios' short-run closure
    path = kw.pop("path")
    base = dict(**short_run_closure("0.3 recommended"), land="fixed", **kw)
    mf, mm = CGE.from_sam(path, **base), CGE.from_sam(path, **base, pricing="markup")
    acts = [a for i, a in enumerate(mm.A) if mm.isMK[i]]
    farm = tuple(PSA_INDUSTRIES["Agriculture, forestry, and fishing"]) == MARKET_PRICE_ACTS and "amach" not in acts
    # (1) zero shock: the benchmark and the SAM; the dynamic hybrid with markup and sectoral stickiness (option (c)) = its baseline
    res0 = float(np.abs(mm.evaluate(mm.x0(), mm.make_shocks())[0]).max())
    b = mm.solve()
    rep = float((mm.rebuild_sam(b) - mm.sam.table).abs().values.max())
    d = DynamicCGE(**dynamic_kwargs("0.3 recommended", rice=True), sr_pricing="markup", sr_stickiness=STK.sectoral(acts))
    bl = d.baseline()
    z = d.scenario({2026: {}})
    zd = max(float((z.table.real_gdp / bl.table.real_gdp - 1).abs().max()), float((z.table.cpi / bl.table.cpi - 1).abs().max()))
    # (2) homogeneity after a shock (world oil +30%, stickiness 0.6, markup charged on half of a cost change): every nominal
    # anchor +10% (the peso, the fixed peso wages, the stickiness and margin anchor) gives every price +10%, quantities unchanged
    oil = dict(cge_oil_shock(mm, 0.30), stickiness=0.6, mk_pass=0.5)
    s1 = mm.solve(oil)
    s2 = mm.solve({**oil, "exr": 1.1, "wbar": {f: 1.1 for f in mm.unemployed},
                   "pa_anchor": {a: 1.1 * (1 - mm.ta[i]) for i, a in enumerate(mm.A)}})
    hq = max(float(np.max(np.abs(np.asarray(s2[k]) / np.asarray(s1[k]) - 1))) for k in ("QA", "QE", "QM", "QH"))
    hp = max(float(np.max(np.abs(np.asarray(s2[k])[i_] / np.asarray(s1[k])[i_] / 1.1 - 1)))    # prices that exist (a commodity
             for k, i_ in (("PQ", mm.iQ), ("PDS", mm.iD), ("AVC", mm.iMK)))                       # without home sales has no PDS)
    hp = max(hp, float(np.max(np.abs(s2["W"][mm.kcap, mm.iK] / s1["W"][mm.kcap, mm.iK] / 1.1 - 1))))
    # (3) cost push: the markup prices' response to the world price of refined petroleum (central difference) = the I-O price
    # model's, given the flexible prices; for the default set and for every activity that can take a markup (home sales, no land);
    # with mk_pass 0 (margin per unit fixed in pesos) = the plain I-O price model (I1's formula on the SAM's coefficients, mu = 0)
    eps, j = 1e-3, mm.C.index("cpetr")
    kl = mm.F.index("flnd")
    every = [a for i, a in enumerate(mm.A) if mm.hasD[int(np.argmax(mm.theta[i]))] and mm.QF0[kl, i] == 0]
    me = CGE.from_sam(path, **base, pricing="markup", markup_acts=every)
    gap_io, cpi = 0.0, {}
    for m_, lam in ((mm, 1.0), (me, 1.0), (mm, 0.0)):
        dpwm = np.zeros(len(m_.C)); dpwm[j] = 1.0
        up = m_.solve({"pwm_scale": {"cpetr": 1 + eps}, "mk_pass": lam})
        dn = m_.solve({"pwm_scale": {"cpetr": 1 - eps}, "mk_pass": lam})
        dc = (np.asarray(up["PDS"]) - np.asarray(dn["PDS"])) / (2 * eps)
        dio, dq = _io_price_markup(m_, dpwm, np.where(m_.mkC, 0.0, dc), mu=lam * m_.mu0)
        k_ = m_.mkC & m_.hasD
        gap_io = max(gap_io, float(np.max(np.abs(dio[k_] - dc[k_]))))
        if m_ is mm:
            cpi["markup" if lam == 1.0 else "plain"] = 0.1 * float(m_.cwts @ dq) * 100
            dmax = float(np.max(np.abs(dc[k_]))) if lam == 1.0 else dmax
    # demand moves the markup prices only through the flexible ones: a construction-investment change, same comparison
    up, dn = mm.solve({"qinv_scale": {"ccons": 1 + eps}}), mm.solve({"qinv_scale": {"ccons": 1 - eps}})
    dc = (np.asarray(up["PDS"]) - np.asarray(dn["PDS"])) / (2 * eps)
    dio, _ = _io_price_markup(mm, np.zeros(len(mm.C)), np.where(mm.mkC, 0.0, dc))
    k_ = mm.mkC & mm.hasD
    gap_dem = float(np.max(np.abs(dio[k_] - dc[k_])))
    # accounts close after the oil shock (Walras, GDP identity, rebuilt SAM); tamper: markup activities' capital paid its
    # benchmark rent (1 per unit installed) instead of the residual
    s = mm.solve(cge_oil_shock(mm, 0.30))
    walras = abs(float(s["WALRAS"])) / float(mm.qinv.sum())
    gid = abs(mm.gdp(s)["nominal_expenditure"] - mm.gdp(s)["nominal_income"])
    S = mm.rebuild_sam(s)
    keep = [c for c in S.index if c not in ("s-i", "row")]          # rebuild_sam leaves the Keynesian closure's foreign saving out
    gap = lambda X: float(np.abs((X.sum(axis=1) - X.sum(axis=0)).loc[keep]).max()) / float(X.values.sum())
    T_ = S.copy()
    T_.loc["fcap", acts] = mm.QF0[mm.kcap][mm.isMK]
    imb, imb_t = gap(S), gap(T_)
    # direction (design note §3): a 10% construction cut lowers consumer prices less and GDP more than with flexible prices
    cut = {"qinv_scale": {"ccons": 0.9}}
    fc, mc = mf.solve(cut), mm.solve(cut)
    bf = mf.solve()
    dirn = (1 - float(mc["CPI"])) < (1 - float(fc["CPI"])) and mm.gdp(mc)["real"] / mm.gdp(b)["real"] < mf.gdp(fc)["real"] / mf.gdp(bf)["real"]
    # guards: a pure exporter or a land user refused as a markup activity; the markup keys refused without pricing='markup'
    refused = 0
    for bad in (dict(pricing="markup", markup_acts=["amach"]), dict(pricing="markup", markup_acts=["arice"])):
        try:
            CGE.from_sam(path, **base, **bad)
        except ValueError:
            refused += 1
    try:
        mf.solve({"markup": 0.2})
    except ValueError:
        refused += 1
    ok = (farm and res0 < 1e-7 and rep < 1e-5 and zd < 1e-9 and s1.ok and s2.ok and hq < 1e-9 and hp < 1e-9 and gap_io < 1e-6
          and gap_dem < 1e-6 and dmax > 0.01 and s.ok and walras < 1e-9 and gid < 1e-6 and imb < 1e-9 and imb_t > 1e-6 and dirn
          and refused == 3 and fc.ok and mc.ok)
    return ok, (f"{len(acts)} markup activities (farms flexible: {farm}; amach, a pure exporter, flexible); benchmark residual {res0:.1e}, "
                f"SAM reproduced {rep:.1e}; dynamic zero shock with sectoral stickiness {zd:.1e}; homogeneity after oil +30%: "
                f"quantities {hq:.1e}, prices {hp:.1e}; cost push = I-O price model (markup, and mk_pass 0 = plain I-O): largest gap "
                f"{gap_io:.1e} (largest response {dmax:.3f}); demand moves markup prices only through flexible prices: {gap_dem:.1e}; "
                f"CPI per 10% on imported refined petroleum {cpi['markup']:.3f}% (mk_pass 0: {cpi['plain']:.3f}%); oil +30%: Walras "
                f"{walras:.1e}, GDP identity "
                f"{gid:.1e}, rebuilt SAM {imb:.1e}, tampered (rent not the residual) {imb_t:.1e} (caught); 10% construction cut: prices "
                f"{float(mc['CPI']) - 1:+.2%} vs {float(fc['CPI']) - 1:+.2%} flexible, GDP {mm.gdp(mc)['real'] / mm.gdp(b)['real'] - 1:+.2%} "
                f"vs {mf.gdp(fc)['real'] / mf.gdp(bf)['real'] - 1:+.2%}; refused {refused}/3 (option off: check R0)")


@check("CS1", "short-run consumption rule (0.3.13): lam 1 = the rule off; zero shock = baseline; the rule holds (also with "
              "the employment cap binding); homogeneity; tamper caught; guards")
def cs1():
    from infinity_gem.dynamic import DynamicCGE
    from infinity_gem.oil import cge_oil_shock
    from infinity_gem.settings import dynamic_kwargs
    kw = dynamic_kwargs("0.3 recommended", rice=True, land="fixed")       # Infinity GEM's own SAM v0.5 (the default), the 2026 scenarios' engine:
    kw.update(wage_curve=10.5, hoarding=0.85, short_run_years=(2026,))    # wage curve at about its central beta, hoarding 0.85
    d = DynamicCGE(**kw)
    b = d.baseline()
    t, lam, beta = 2026, 0.62, 10.5
    shock = {t: {**cge_oil_shock(d.m, 0.30), "qinv_scale": {"ccons": 0.85}}}   # world oil +30%, construction investment -15%
    F, m = d.m.F, d.m
    keys = ("QA", "QH", "QE", "QM", "QINV", "EMP", "PQ", "WF", "EH", "DY", "YH")
    qkeys = ("QA", "QH", "QE", "QM", "QINV", "QG", "EMP")
    lab = [k for k, f in enumerate(F) if f.startswith("flab")]
    rd = lambda a_, b_: float(np.max(np.abs(np.asarray(a_, float) - np.asarray(b_, float))
                                     / np.maximum(np.abs(np.asarray(b_, float)), 1e-9)))
    prices = lambda s_: [np.asarray(s_["PQ"], float)[d.ms.iQ], np.asarray(s_["PDS"], float)[d.ms.iD], np.asarray(s_["WF"], float)[lab],
                         np.asarray(s_["W"], float)[d.ms.kcap, d.ms.iK], np.asarray(s_["EH"], float), np.asarray(s_["DY"], float),
                         np.asarray(s_["YH"], float), np.array([float(s_["CPI"]), float(s_["EXR"])])]
    hom = lambda p_, q_: (max(rd(p_.solutions[t][k], q_.solutions[t][k]) for k in qkeys),          # quantities unchanged,
                          max(rd(x_ / 1.1, y_) for x_, y_ in zip(prices(p_.solutions[t]), prices(q_.solutions[t]))),   # prices +10%,
                          abs(float(p_.solutions[t]["MPSADJ"]) - float(q_.solutions[t]["MPSADJ"])),  # the same saving rates,
                          max(rd(p_.solutions[y][k], q_.solutions[y][k]) for y in d.years if y > t for k in keys))   # later years

    def run(lam_, sh=shock):
        d.a["sr_consumption"] = None if lam_ is None else {"htm": lam_}
        return d.scenario(sh)

    def rule_gap(s_, ref=b.solutions[t]):        # the rule, written here independently of dynamic.py: total household spending =
        mb = np.clip(np.asarray(d.ms.mps, float) * (1 + float(ref["MPSADJ"])), -1.0, 1.0)   # lam (1 - baseline saving rates) DY
        target = (lam * float(((1 - mb) * np.asarray(s_["DY"], float)).sum())               # + (1 - lam) baseline spending x CPI /
                  + (1 - lam) * float(np.sum(ref["EH"])) * float(s_["CPI"]) / float(ref["CPI"]))   # baseline CPI
        return abs(float(np.sum(s_["EH"])) - target) / target

    bs = b.solutions[t]
    p_off, p_1, p_c = run(None), run(1.0), run(lam)
    z = run(lam, {t: {}})
    # (1) nesting: lam 1 = the engine without the rule, every year; (2) zero shock = the baseline
    nest = max(rd(p_1.solutions[y][k], p_off.solutions[y][k]) for y in d.years for k in keys)
    zd = max(float((z.table.real_gdp / b.table.real_gdp - 1).abs().max()), float((z.table.cpi / b.table.cpi - 1).abs().max()))
    # (3) the rule holds in the solution; the wage curve's fixed point holds jointly (anchor in pesos or real, as the wage rule);
    # households smooth: consumption falls less than without the rule, and the saving-rate adjustment falls
    s = p_c.solutions[t]
    gap = rule_gap(s)
    ix = (lambda sol: float(sol["CPI"])) if d.ms.wage == "real" else (lambda sol: 1.0)
    capped_c = str(p_c.table.loc[t, "employment_capped"]).split(",")
    fp = max(abs(float(s["WF"][k]) / ix(s) / (float(bs["WF"][k]) / ix(bs)) - min(1.0, float(s["EMP"][k] / bs["EMP"][k])) ** beta)
             for k in lab if F[k] in d.ms.unemployed and F[k] not in capped_c)
    c_off = float(np.sum(p_off.solutions[t]["QH"]) / np.sum(bs["QH"]) - 1)
    c_on = float(np.sum(s["QH"]) / np.sum(bs["QH"]) - 1)
    dmps = float(s["MPSADJ"]) - float(bs["MPSADJ"])
    dirn = c_off < c_on < 0 and dmps < 0
    # (3b) the employment cap binding (a large demand shock, as Y6): the rule re-solved after the change of regime still holds
    p_big = run(lam, {t: {"qinv_scale": {"ccons": 1.3}, "trg_h_add": {"hhd-r1": 60.0, "hhd-u1": 60.0}}})
    capped = str(p_big.table.loc[t, "employment_capped"])
    gap_cap = rule_gap(p_big.solutions[t])
    # (4) homogeneity: the baseline year solved at a consumer price level 10% higher (every price +10%, quantities the same, as
    # check C3) carries every nominal anchor of the short-run year +10%: the peso, the peso wage anchors and the wage curve's,
    # world prices in pesos, and the rule's baseline spending and price reference. (4a) all of them; (4b) the same with the rule's
    # reference held at the original baseline's, whose REAL spending is the same: nothing real may change in either
    x11 = bs.x.copy()
    for k_ in ("PDS", "PQ", "WF", "RK", "RL", "RN", "EXR"):                # the long-run model's price unknowns
        x11[m.slices[k_]] *= 1.1
    b11 = m.solve({**bs.shocks, "cpi": 1.1}, x_start=x11)
    ref_c, tgt_c = d._sr_consumption_ref, d._sr_consumption_target
    held = lambda t_, model: (dict(ref_c(t_, model), EH=np.asarray(bs["EH"], float), CPI=float(bs["CPI"])) if t_ == t
                              else ref_c(t_, model))
    no_cpi = lambda s_, ref: (ref["lam"] * (1.0 - ref["mps"]) * np.asarray(s_["DY"], float)   # TAMPER: the CPI term dropped (the
                              + (1.0 - ref["lam"]) * ref["EH"])                                 # rule holds nominal spending)
    try:
        d.base.solutions[t] = b11
        p_h = run(lam)
        d._sr_consumption_ref = held
        p_r = run(lam)
        # (5) tamper: the rule without its CPI term, on the original baseline and on the scaled one with the reference held
        d._sr_consumption_target = no_cpi
        p_tr = run(lam)
        d.base.solutions[t] = bs
        p_t = run(lam)
    finally:
        d.base.solutions[t] = bs
        d.__dict__.pop("_sr_consumption_ref", None)
        d.__dict__.pop("_sr_consumption_target", None)
    h_a, h_b = hom(p_h, p_c), hom(p_r, p_c)
    gap_t = rule_gap(p_t.solutions[t])
    hq_t = hom(p_tr, p_t)[0]
    # (6) guards: lam outside [0, 1] or not a number, a wrong key, no hybrid closure (at construction and when set afterwards),
    # and a scenario saving-rate shock in a short-run year are refused
    refused = 0
    for bad in ({"htm": 1.2}, {"htm": -0.1}, {"htm": float("nan")}, {"htm": True}, {"lam": lam}, lam):
        try:
            DynamicCGE(**dict(kw, sr_consumption=bad))
        except ValueError:
            refused += 1
    try:
        DynamicCGE(**dict(kw, hybrid=False, sr_consumption={"htm": lam}))
    except ValueError:
        refused += 1
    try:
        run(lam, {t: {**shock[t], "mpsadj": 0.1}})
    except ValueError:
        refused += 1
    d.a["hybrid"] = False
    try:
        run(lam)
    except ValueError:
        refused += 1
    finally:
        d.a["hybrid"], d.a["sr_consumption"] = True, None
    ok = (nest < 1e-9 and zd < 1e-9 and gap < 1e-8 and fp < 1e-8 and dirn and bool(capped) and gap_cap < 1e-8 and b11.ok
          and max(h_a) < 1e-9 and max(h_b) < 1e-9 and gap_t > 1e-6 and hq_t > 1e-6 and refused == 9)
    return ok, (f"2026 oil +30%, construction -15% (Infinity GEM SAM, beta {beta}, hoarding 0.85): lam 1 vs off {nest:.1e} (all years); zero "
                f"shock {zd:.1e}; lam {lam}: rule gap {gap:.1e}, wage-curve fixed point {fp:.1e}, consumption {c_on:+.2%} vs {c_off:+.2%} "
                f"without the rule, saving-rate adjustment {dmps:+.3f}; cap binding ({capped}): rule gap {gap_cap:.1e}; homogeneity "
                f"(anchors +10%): quantities {h_a[0]:.1e}, prices {h_a[1]:.1e}, MPSADJ {h_a[2]:.1e}, later years {h_a[3]:.1e}; with the "
                f"rule's real reference held: {max(h_b):.1e}; tamper (CPI term dropped): rule gap {gap_t:.1e}, homogeneity with the "
                f"real reference {hq_t:.1e} (caught); refused {refused}/9")


@check("ER1", "incomplete pass-through of the peso to import prices (0.3.13, P2(b)): phi 1 = the option off; zero shock = "
              "baseline; the import-price equation and the current account; accounts close; homogeneity; tamper caught; guards")
def er1():
    from infinity_gem.cge import CGE
    from infinity_gem.dynamic import DynamicCGE, ERPT_FULL
    from infinity_gem.oil import cge_oil_shock
    from infinity_gem.settings import cge_kwargs, dynamic_kwargs, short_run_closure
    phi = 0.3
    rd = lambda a_, b_: float(np.max(np.abs(np.asarray(a_, float) - np.asarray(b_, float))
                                     / np.maximum(np.abs(np.asarray(b_, float)), 1e-9)))

    def pm_rule(m, s_, e_, ref):                 # the import-price equation, written here independently of cge.py: the suppliers'
        sh = m.make_shocks(s_.shocks)            # US$ price and the peso price (with IFPRI-style margins on top, as 'split')
        home = m.pwm * sh["pwm_scale"] * (float(s_["EXR"]) / ref) ** (e_ - 1.0)
        return home, home * float(s_["EXR"]) * (1 + m.tm * sh["tm_scale"]) + m.icx * float(s_["PTRC"]), sh

    # (A) the static short-run model: Infinity GEM's own SAM, the 2026 scenarios' short-run closure, flexible prices and markup pricing; a 5%
    # depreciation with world oil +30%, phi 0.3 on every import but oil and crude
    kw = cge_kwargs("0.3 recommended", rice=True)
    path = kw.pop("path")
    base = dict(**short_run_closure("0.3 recommended"), land="fixed", **kw)
    out, ok = [], True
    for pricing in ("flex", "markup"):
        m = CGE.from_sam(path, **base, pricing=pricing)
        non = {c: phi for c in m.C if c not in ERPT_FULL}
        e_ = np.array([non.get(c, 1.0) for c in m.C])
        sh0 = {**cge_oil_shock(m, 0.30), "exr": 1.05}
        b, s_off, s_1, s_p = m.solve(), m.solve(sh0), m.solve({**sh0, "erpt": 1.0}), m.solve({**sh0, "erpt": non})
        nest = max(rd(s_1[k], s_off[k]) for k in ("QA", "QH", "QE", "QM", "PQ", "PM", "EH", "WF"))
        home, pm, sh = pm_rule(m, s_p, e_, 1.0)
        pm_gap = float(np.max(np.abs(np.asarray(s_p["PM"], float)[m.hasM] / pm[m.hasM] - 1)))
        v = s_p.v
        fcu = float((home * np.asarray(v["QM"], float)).sum() + (m.pwm * sh["pwm_scale"] * m.rex).sum() + m.frow_out.sum()
                    + m.erow_out + m.hrow_out.sum() + m.grow_out + sh["grow_out_add"])
        ca = abs(fcu - float(v["fcu_out"])) / float(m.QM0.sum())
        walras = abs(float(v["WALRAS"])) / float(m.qinv.sum())
        gid = abs(m.gdp(s_p)["nominal_expenditure"] - m.gdp(s_p)["nominal_income"])
        S = m.rebuild_sam(s_p)
        keep = [c for c in S.index if c not in ("s-i", "row")]          # rebuild_sam leaves the Keynesian closure's foreign saving out
        imb = float(np.abs((S.sum(axis=1) - S.sum(axis=0)).loc[keep]).max()) / float(S.values.sum())
        # homogeneity: the peso, its reference, the peso wage anchors (and the markup anchor) +10%
        sp2 = {**sh0, "erpt": non, "exr": 1.05 * 1.1, "exr_ref": 1.1, "wbar": {f: 1.1 for f in m.unemployed}}
        if pricing == "markup":
            sp2["pa_anchor"] = {a: 1.1 * (1 - m.ta[i]) for i, a in enumerate(m.A)}
        s2 = m.solve(sp2)
        hq = max(rd(s2[k], s_p[k]) for k in ("QA", "QE", "QM", "QH"))
        hp = max(rd(np.asarray(s2[k], float)[i_] / 1.1, np.asarray(s_p[k], float)[i_])
                 for k, i_ in (("PQ", m.iQ), ("PDS", m.iD), ("PM", m.hasM)))
        # direction: consumer prices rise less than with full pass-through; phi 0: non-oil import prices (before margins) unchanged
        s_0 = m.solve({**sh0, "erpt": {c: 0.0 for c in non}})
        home0 = np.asarray(s_0["pwm_home"], float) * float(s_0["EXR"])
        i_non = np.array([c in non for c in m.C]) & m.hasM
        flat = float(np.max(np.abs(home0[i_non] / (m.pwm * m.make_shocks(s_0.shocks)["pwm_scale"])[i_non] - 1)))
        cpi_off, cpi_p = float(s_off["CPI"]) / float(b["CPI"]) - 1, float(s_p["CPI"]) / float(b["CPI"]) - 1
        dirn = 0 < cpi_p < cpi_off
        good = (all(x.ok for x in (b, s_off, s_1, s_p, s2, s_0)) and nest < 1e-9 and pm_gap < 1e-12 and ca < 1e-12 and walras < 1e-9
                and gid < 1e-6 and imb < 1e-9 and hq < 1e-9 and hp < 1e-9 and dirn and flat < 1e-12)
        ok &= good
        out.append(f"static {pricing}: phi 1 vs off {nest:.1e}; PM rule {pm_gap:.1e}; current account {ca:.1e}; Walras {walras:.1e}, "
                   f"GDP identity {gid:.1e}, SAM {imb:.1e}; homogeneity q {hq:.1e} p {hp:.1e}; CPI {cpi_p:+.2%} vs {cpi_off:+.2%} at "
                   f"full pass-through; phi 0: non-oil import prices {flat:.1e}")
    refused = 0
    for bad in ({"erpt": 1.2}, {"erpt": -0.1}, {"erpt": float("nan")}, {"erpt": True}, {"erpt": {"cxxx": 0.5}}, {"exr_ref": 0.0},
                {"exr_ref": True}):
        try:
            m.solve(bad)
        except ValueError:
            refused += 1
    for model in (CGE.from_sam(path, **kw), CGE.from_sam(path, **dict(base, fx="flexible"))):   # the peso is the model's there
        try:
            model.solve({"erpt": 0.5})
        except ValueError:
            refused += 1
    # (B) the dynamic hybrid: Infinity GEM's own SAM, the 2026 scenarios' engine (wage curve 10.5, hoarding 0.85), 2026 short run; world oil +30%,
    # construction investment -15% and the peso 2% weaker in 2026
    kwd = dynamic_kwargs("0.3 recommended", rice=True, land="fixed")
    kwd.update(wage_curve=10.5, hoarding=0.85, short_run_years=(2026,))
    d = DynamicCGE(**kwd)
    bl = d.baseline()
    t = 2026
    shock = {t: {**cge_oil_shock(d.m, 0.30), "qinv_scale": {"ccons": 0.85}, "exr_scale": 1.02}}
    keys = ("QA", "QH", "QE", "QM", "QINV", "EMP", "PQ", "WF", "EH", "DY", "YH")
    qkeys = ("QA", "QH", "QE", "QM", "QINV", "QG", "EMP")
    lab = [k for k, f in enumerate(d.m.F) if f.startswith("flab")]
    prices = lambda s_: [np.asarray(s_["PQ"], float)[d.ms.iQ], np.asarray(s_["PDS"], float)[d.ms.iD], np.asarray(s_["WF"], float)[lab],
                         np.asarray(s_["PM"], float)[d.ms.hasM], np.asarray(s_["EH"], float), np.array([float(s_["CPI"]), float(s_["EXR"])])]
    hom = lambda p_, q_: (max(rd(p_.solutions[t][k], q_.solutions[t][k]) for k in qkeys),
                          max(rd(x_ / 1.1, y_) for x_, y_ in zip(prices(p_.solutions[t]), prices(q_.solutions[t]))),
                          max(rd(p_.solutions[y][k], q_.solutions[y][k]) for y in d.years if y > t for k in keys))

    def run(e, sh=shock):
        d.a["sr_erpt"] = e
        return d.scenario(sh)

    bs = bl.solutions[t]
    try:
        p_off, p_1, p_c = run(None), run(1.0), run(phi)
        z = run(phi, {t: {}})
        nest_d = max(rd(p_1.solutions[y][k], p_off.solutions[y][k]) for y in d.years for k in keys)
        zd = max(float((z.table.real_gdp / bl.table.real_gdp - 1).abs().max()), float((z.table.cpi / bl.table.cpi - 1).abs().max()))
        s = p_c.solutions[t]
        e_d = np.array([0.3 if c not in ERPT_FULL else 1.0 for c in d.ms.C])
        _, pm_d, _ = pm_rule(d.ms, s, e_d, float(bs["EXR"]))
        pm_gap_d = float(np.max(np.abs(np.asarray(s["PM"], float)[d.ms.hasM] / pm_d[d.ms.hasM] - 1)))
        cpi_dir = float(s["CPI"]) < float(p_off.solutions[t]["CPI"])
        # homogeneity, as check CS1: the baseline year solved at a consumer price level 10% higher carries every nominal anchor
        # of the short-run year +10% (the peso and the suppliers' reference peso, the peso wage anchors and the wage curve's)
        x11 = bs.x.copy()
        for k_ in ("PDS", "PQ", "WF", "RK", "RL", "RN", "EXR"):
            x11[d.m.slices[k_]] *= 1.1
        b11 = d.m.solve({**bs.shocks, "cpi": 1.1}, x_start=x11)
        d.base.solutions[t] = b11
        p_h = run(phi)
        # tamper: the suppliers anchored to the benchmark peso instead of the year's (the reference dropped from the rule)
        for mdl in d._ms_cache.values():
            mdl._ptm = lambda pwm, EXR, sh_: pwm * EXR ** (sh_["erpt"] - 1.0)
        p_t = run(phi)
    finally:
        d.base.solutions[t] = bs
        for mdl in d._ms_cache.values():
            mdl.__dict__.pop("_ptm", None)
        d.a["sr_erpt"] = None
    h_d, h_t = hom(p_h, p_c), hom(p_t, p_c)
    # guards: phi outside [0, 1] or not a number, an unknown commodity, no hybrid closure, a flexible peso, a scenario's own key,
    # and the option set after construction without the hybrid closure
    for bad in ({"sr_erpt": 1.5}, {"sr_erpt": True}, {"sr_erpt": float("nan")}, {"sr_erpt": {"cxxx": 0.3}},
                {"sr_erpt": phi, "hybrid": False}, {"sr_erpt": phi, "sr_fx": "flexible"}):
        try:
            DynamicCGE(**dict(kwd, **bad))
        except ValueError:
            refused += 1
    try:
        run(phi, {t: {**shock[t], "erpt": {"cfood": 0.2}}})
    except ValueError:
        refused += 1
    d.a["hybrid"] = False
    try:
        run(phi)
    except ValueError:
        refused += 1
    finally:
        d.a["hybrid"], d.a["sr_erpt"] = True, None
    ok &= (nest_d < 1e-9 and zd < 1e-9 and pm_gap_d < 1e-12 and cpi_dir and b11.ok and max(h_d) < 1e-9 and h_t[0] > 1e-6
           and refused == 17)
    out.append(f"dynamic (Infinity GEM SAM, beta 10.5, hoarding 0.85; 2026 oil +30%, construction -15%, peso +2%): phi 1 vs off {nest_d:.1e} "
               f"(all years); zero shock {zd:.1e}; PM rule {pm_gap_d:.1e}; CPI 2026 {float(s['CPI']) / float(bs['CPI']) - 1:+.2%} vs "
               f"{float(p_off.solutions[t]['CPI']) / float(bs['CPI']) - 1:+.2%} at full pass-through; homogeneity: quantities "
               f"{h_d[0]:.1e}, prices {h_d[1]:.1e}, later years {h_d[2]:.1e}; tamper (reference dropped): quantities {h_t[0]:.1e} "
               f"(caught); refused {refused}/17")
    return ok, "; ".join(out)


@check("MG1", "a markup pass-through that depends on the output gap (0.3.13, P6): slope 0 = the option off; the rule at its gap "
              "= the constant pass-through; the price rule recomputed; accounts close; homogeneity; zero shock = baseline with every "
              "new option on; tamper caught; guards")
def mg1():
    from infinity_gem import stickiness as STK
    from infinity_gem.cge import CGE
    from infinity_gem.dynamic import DynamicCGE
    from infinity_gem.oil import cge_oil_shock
    from infinity_gem.settings import cge_kwargs, dynamic_kwargs, short_run_closure
    s_ = 0.1                                      # test value: the pass-through changes by 0.1 per percent of output gap
    rd = lambda a_, b_: float(np.max(np.abs(np.asarray(a_, float) - np.asarray(b_, float))
                                     / np.maximum(np.abs(np.asarray(b_, float)), 1e-9)))

    def rule_gap(m, sol, s, yref, lam0=None):      # the home price rule, written here independently of cge.py: unit variable cost
        sh = m.make_shocks(sol.shocks)            # rebuilt from wages, the installed technology and composite prices; the gap
        coef = m.mk_coef0 if sh["mk_coef"] is None else np.asarray(sh["mk_coef"], float)   # from gdp()'s real GDP
        tfp = m.tfp * sh["tfp_scale"]
        W, PQ = np.asarray(sol["W"], float), np.asarray(sol["PQ"], float)
        avc = (W[m.mk_lab] * coef[m.mk_lab]).sum(axis=0) / tfp + m.ica.T @ PQ
        g = 100.0 * (m.gdp(sol)["real"] / yref - 1.0)
        mu, A = sh["markup"], sh["pa_anchor"]
        lam_e = (sh["mk_pass"] if lam0 is None else lam0) + s * g
        cm = avc + mu * (A / (1 + mu) + lam_e * (avc - A / (1 + mu)))
        z = (A - cm) / A
        fz = np.where(z <= 0, 0.0, np.where(z < 1e-4, z * z / 2e-4, z - 0.5e-4))
        price = cm + np.where(m.isST, np.asarray(sh["stickiness"], float) * A * fz, 0.0)
        urd = np.asarray(sol["PDS"], float)[m.mk_com] * (1 - m.ta)
        return float(np.max(np.abs(urd[m.isMK] / price[m.isMK] - 1))), g

    # (A) static: Infinity GEM's own SAM, the 2026 scenarios' short-run closure, markup pricing with mk_pass 0; world oil +30%
    kw = cge_kwargs("0.3 recommended", rice=True)
    path = kw.pop("path")
    base = dict(**short_run_closure("0.3 recommended"), land="fixed", **kw)
    m = CGE.from_sam(path, **base, pricing="markup")
    b = m.solve()
    ref0 = abs(m.real_gdp0 / m.gdp(b)["real"] - 1)
    oil = {**cge_oil_shock(m, 0.30), "mk_pass": 0.0}
    s0, s00, s1 = m.solve(oil), m.solve({**oil, "mk_gap": 0.0}), m.solve({**oil, "mk_gap": s_})
    nest = max(rd(s00[k], s0[k]) for k in ("QA", "QH", "QE", "QM", "PQ", "PDS", "EH", "WF"))
    res0 = float(np.abs(m.evaluate(m.x0(), m.make_shocks({"mk_gap": s_}))[0]).max())
    gap1, g1 = rule_gap(m, s1, s_, m.real_gdp0)
    s_c = m.solve({**oil, "mk_pass": s_ * g1})                       # the constant pass-through at the solved gap: same solution
    fixed = max(rd(s_c[k], s1[k]) for k in ("QA", "QH", "QE", "QM", "PQ", "PDS", "EH", "WF"))
    walras = abs(float(s1["WALRAS"])) / float(m.qinv.sum())
    gid = abs(m.gdp(s1)["nominal_expenditure"] - m.gdp(s1)["nominal_income"])
    S = m.rebuild_sam(s1)
    keep = [c for c in S.index if c not in ("s-i", "row")]
    imb = float(np.abs((S.sum(axis=1) - S.sum(axis=0)).loc[keep]).max()) / float(S.values.sum())
    s2 = m.solve({**oil, "mk_gap": s_, "exr": 1.1, "wbar": {f: 1.1 for f in m.unemployed},
                  "pa_anchor": {a: 1.1 * (1 - m.ta[i]) for i, a in enumerate(m.A)}})
    hq = max(rd(s2[k], s1[k]) for k in ("QA", "QE", "QM", "QH"))
    hp = max(rd(np.asarray(s2[k], float)[i_] / 1.1, np.asarray(s1[k], float)[i_]) for k, i_ in (("PQ", m.iQ), ("PDS", m.iD)))
    gb = m.gdp(b)["real"]
    dirn = float(s1["CPI"]) < float(s0["CPI"]) and m.gdp(s1)["real"] > m.gdp(s0)["real"] and g1 < 0
    refused = 0
    for bad in ({"mk_gap": float("nan")}, {"mk_gap": True}, {"mk_gdp": -1.0}, {"mk_gdp": True}):
        try:
            m.solve(bad)
        except ValueError:
            refused += 1
    try:
        CGE.from_sam(path, **base).solve({"mk_gap": s_})
    except ValueError:
        refused += 1
    ok = (all(x.ok for x in (b, s0, s00, s1, s_c, s2)) and ref0 < 1e-12 and nest == 0.0 and res0 < 1e-7 and gap1 < 1e-9
          and fixed < 1e-8 and walras < 1e-9 and gid < 1e-6 and imb < 1e-9 and hq < 1e-9 and hp < 1e-9 and dirn)
    out = [f"static (oil +30%, mk_pass 0, slope {s_}): reference GDP = benchmark {ref0:.1e}; slope 0 vs off {nest:.1e}; zero shock "
           f"{res0:.1e}; price rule {gap1:.1e} (gap {g1:+.2f}%); = constant pass-through at that gap {fixed:.1e}; CPI "
           f"{float(s1['CPI']) - 1:+.2%} vs {float(s0['CPI']) - 1:+.2%} at slope 0, GDP {m.gdp(s1)['real'] / gb - 1:+.2%} vs "
           f"{m.gdp(s0)['real'] / gb - 1:+.2%}; Walras {walras:.1e}, GDP identity {gid:.1e}, SAM {imb:.1e}; homogeneity q {hq:.1e} "
           f"p {hp:.1e}"]
    # (B) dynamic: option (c) with the 2026 scenarios' engine (Infinity GEM's own SAM, wage curve 10.5, hoarding 0.85), 2026 short run; world oil +30%,
    # construction investment -15%, the peso 2% weaker
    kwd = dynamic_kwargs("0.3 recommended", rice=True, land="fixed")
    kwd.update(wage_curve=10.5, hoarding=0.85, short_run_years=(2026,), sr_pricing="markup", sr_markup_pass=0.0)
    d = DynamicCGE(**kwd)
    d.a["sr_stickiness"] = STK.sectoral([a for i, a in enumerate(d.ms.A) if d.ms.isMK[i]])
    bl = d.baseline()
    t = 2026
    shock = {t: {**cge_oil_shock(d.m, 0.30), "qinv_scale": {"ccons": 0.85}, "exr_scale": 1.02}}
    keys = ("QA", "QH", "QE", "QM", "QINV", "EMP", "PQ", "WF", "EH", "DY", "YH")
    qkeys = ("QA", "QH", "QE", "QM", "QINV", "QG", "EMP")
    lab = [k for k, f in enumerate(d.m.F) if f.startswith("flab")]
    prices = lambda x_: [np.asarray(x_["PQ"], float)[d.ms.iQ], np.asarray(x_["PDS"], float)[d.ms.iD], np.asarray(x_["WF"], float)[lab],
                         np.asarray(x_["EH"], float), np.array([float(x_["CPI"]), float(x_["EXR"])])]
    hom = lambda p_, q_: (max(rd(p_.solutions[t][k], q_.solutions[t][k]) for k in qkeys),
                          max(rd(x_ / 1.1, y_) for x_, y_ in zip(prices(p_.solutions[t]), prices(q_.solutions[t]))),
                          max(rd(p_.solutions[y][k], q_.solutions[y][k]) for y in d.years if y > t for k in keys))

    def run(s, allon=False, sh=shock):
        d.a["sr_markup_gap"] = s
        d.a["sr_consumption"], d.a["sr_erpt"] = ({"htm": 0.62}, 0.3) if allon else (None, None)
        return d.scenario(sh)

    bs = bl.solutions[t]
    try:
        p_off, p_s, p_a = run(0.0), run(s_), run(s_, True)
        z = run(s_, True, {t: {}})
        zd = max(float((z.table.real_gdp / bl.table.real_gdp - 1).abs().max()), float((z.table.cpi / bl.table.cpi - 1).abs().max()))
        gap_d, g_d = rule_gap(d.ms, p_s.solutions[t], s_, float(bl.table.loc[t, "real_gdp"]))
        gap_a, _ = rule_gap(d.ms, p_a.solutions[t], s_, float(bl.table.loc[t, "real_gdp"]))
        cpi_dir = float(p_s.solutions[t]["CPI"]) < float(p_off.solutions[t]["CPI"]) and g_d < 0
        x11 = bs.x.copy()
        for k_ in ("PDS", "PQ", "WF", "RK", "RL", "RN", "EXR"):
            x11[d.m.slices[k_]] *= 1.1
        b11 = d.m.solve({**bs.shocks, "cpi": 1.1}, x_start=x11)
        d.base.solutions[t] = b11
        p_h = run(s_, True)
        d.base.solutions[t] = bs
        # tamper: the output gap measured against the benchmark's real GDP instead of the year's baseline (a zero shock cannot show
        # it, the margin being the reference margin whatever the gap when costs are at the reference: the price rule does)
        for mdl in d._ms_cache.values():
            mdl._output_gap = lambda Y, sh_, mdl=mdl: 100.0 * (Y / mdl.real_gdp0 - 1.0)
        zt = run(s_)
        zt_d, _ = rule_gap(d.ms, zt.solutions[t], s_, float(bl.table.loc[t, "real_gdp"]))
    finally:
        d.base.solutions[t] = bs
        for mdl in d._ms_cache.values():
            mdl.__dict__.pop("_output_gap", None)
        d.a["sr_markup_gap"], d.a["sr_consumption"], d.a["sr_erpt"] = 0.0, None, None
    h_a = hom(p_h, p_a)
    for bad in ({"sr_markup_gap": float("nan")}, {"sr_markup_gap": True}, {"sr_markup_gap": s_, "sr_pricing": "flex"},
                {"sr_markup_gap": s_, "hybrid": False}):
        try:
            DynamicCGE(**dict(kwd, **bad))
        except ValueError:
            refused += 1
    d.a["sr_pricing"] = "flex"                    # set after construction: refused before the path
    try:
        run(s_)
    except ValueError:
        refused += 1
    finally:
        d.a["sr_pricing"], d.a["sr_markup_gap"] = "markup", 0.0
    ok &= (zd < 1e-9 and gap_d < 1e-9 and gap_a < 1e-9 and cpi_dir and b11.ok and max(h_a) < 1e-9 and zt_d > 1e-6 and refused == 10)
    out.append(f"dynamic, option (c) (2026 oil +30%, construction -15%, peso +2%): zero shock with every new option on (consumption "
               f"rule 0.62, pass-through 0.3, slope {s_}) {zd:.1e}; price rule {gap_d:.1e} (gap {g_d:+.2f}%), with every option on "
               f"{gap_a:.1e}; CPI 2026 {float(p_s.solutions[t]['CPI']) / float(bs['CPI']) - 1:+.2%} vs "
               f"{float(p_off.solutions[t]['CPI']) / float(bs['CPI']) - 1:+.2%} at slope 0; homogeneity (every option on): quantities "
               f"{h_a[0]:.1e}, prices {h_a[1]:.1e}, later years {h_a[2]:.1e}; tamper (gap against the benchmark's GDP): price rule "
               f"{zt_d:.1e} (caught); refused {refused}/10")
    return ok, "; ".join(out)


@check("LG1", "no-shock 2026 labour path option (0.3.9)")
def lg1():
    import pandas as pd
    from infinity_gem.dynamic import psa_labour_growth, documented_baseline
    a, b = psa_labour_growth(), psa_labour_growth(y2026="trend")
    same_default = documented_baseline()["labour_growth"] == a and all(a[y] == b[y] or y == 2026 or y > 2026 for y in a)
    pop = pd.read_csv(paths.DATA_RAW / "population" / "PSA_OpenSTAT_population_projections_2020CPH_2020-2030.csv", comment="#")
    p15 = pop[(pop["sex"] == "Both Sexes") & ~pop["age_group"].isin(["All Ages", "0-4", "5-9", "10-14"])].groupby("year")["population_thousands"].sum()
    lfs = pd.read_csv(paths.DATA_RAW / "lfs" / "PSA_OpenSTAT_LFS_employed_by_highest_grade_2023-2026.csv", comment="#")
    from infinity_gem.dynamic import LABOUR_EDUCATION
    lev = np.array([lfs[(lfs["year"] == 2025) & (lfs["month"] == "Annual") & lfs["highest_grade_completed"].isin(v)]["employed_thousands"].sum()
                    for v in LABOUR_EDUCATION.values()])
    tot = float((lev * (1 + np.array(list(b[2026].values())))).sum() / lev.sum())
    rule = float(p15[2026] / p15[2025])
    ok = same_default and abs(tot - rule) < 1e-12 and a[2026] != b[2026]
    return ok, f"default unchanged: {same_default}; trend 2026 total employment growth {tot - 1:.4%} = population 15+ {rule - 1:.4%}"


@check("E2", "sensitivity elasticity sets: 'ph' with one value changed; calibrate on the rice-split SAM (0.3.9)")
def e2():
    from infinity_gem.cge import CGE
    from infinity_gem.elasticities import elasticity_set, SENSITIVITY_SETS
    base = elasticity_set("ph")
    out, ok = [], True
    for name, (code, value, _) in SENSITIVITY_SETS.items():
        el = elasticity_set(name)
        diff = [k for k in base["sigma_q"] if base["sigma_q"][k] != el["sigma_q"][k]]
        same_rest = el["sigma_va"] == base["sigma_va"] and el["omega_t"] == base["omega_t"]
        m = CGE.from_sam(paths.SAM_2023_RICE, elasticities=el)
        r = float(np.abs(m.evaluate(m.x0(), m.make_shocks())[0]).max())
        ok &= diff == [code] and el["sigma_q"][code] == value and same_rest and r < 1e-7
        out.append(f"{name}: only {diff} changed ({base['sigma_q'][code]} -> {value}); benchmark residual {r:.0e}")
    return ok, "; ".join(out)


@check("X2", "forward-looking CGE (the forward-looking CGE; research code): solver benchmarks, SAM, no shock, static block = cge.py")
def x2():
    import pandas as pd
    sys.path.insert(0, str(ROOT / "research" / "intertemporal"))
    import benchmark_solver as BS
    import pf_cge9 as P
    from infinity_gem.cge import CGE
    out, ok = [], True
    # (a) the stacked solver against benchmarks that share no code with it
    e_bm, _ = BS.brock_mirman()
    e1, _, _ = BS.blanchard_kahn(0.02)
    e2, _, _ = BS.blanchard_kahn(0.01)
    ok &= e_bm < 1e-10 and e2 < 1e-4 and 3.0 < e1 / e2 < 5.0
    out.append(f"Brock-Mirman closed form {e_bm:.1e}; Blanchard-Kahn second order (ratio {e1 / e2:.2f})")
    # (b) steady state at 2023 values = the SAM, and (c) no shock stays put, in three configurations
    from infinity_gem.settings import PUBLIC_CAPITAL          # the sourced pair, not typed in here
    for kw in (dict(), dict(calib="pwt", households="groups"), dict(calib="pwt", households="groups", public_capital=PUBLIC_CAPITAL["low"])):
        m = P.CGE9(**kw)
        y, _ = m.steady()
        v = m.split(y[:, None])
        dev = max(np.abs(v["pd"] - 1).max(), np.abs(v["X"][:, 0] / m.X0 - 1).max(), abs(v["C"][0] / m.C0 - 1))
        Y, *_ = m.run(m.path(60), y_start=y)
        drift = float(np.abs(Y - y[:, None]).max() / np.abs(y).max())
        ok &= dev < 1e-8 and drift < 1e-10
        out.append(f"{kw or 'defaults'}: SAM {dev:.0e}, no-shock drift {drift:.0e}")
    # (d) within-year block = Infinity GEM's static CGE (closure 'investment', capital 'fixed'), ten groups, data calibration
    t = pd.read_csv(P.SAM_CSV, index_col=0)
    g = CGE(SAM(t, {}, "condensed 2023 SAM"), closure="investment", capital="fixed")
    m = P.CGE9(calib="pwt", households="groups")
    ic = P.SECT.index("chem")
    worst = 0.0
    for spec, setx in (({"pwm_scale": {"cchem": 1.2}}, (9 + ic, 1.2)), ({"remit_scale": 0.9}, (30, 0.9))):
        sol = g.solve(spec)
        x = m.x0.copy(); x[setx[0]] = setx[1]
        vv, s, _ = m.static_equilibrium(x)
        cpi_pf = float(m.shc @ (s["pq"][:, 0] / m.pq0))
        gaps = [np.abs(sol.v["QA"] / g.QA0 - vv["X"][:, 0] / m.X0).max(),
                np.abs(sol.v["PQ"] / sol.v["CPI"] - s["pq"][:, 0] / m.pq0 / cpi_pf).max(),
                np.abs(sol.v["EH"] / g.EH0 / sol.v["CPI"] - s["EH"][:, 0] / m.EH0 / cpi_pf).max()]
        worst = max(worst, float(max(gaps)) * 100)
    ok &= worst < 1e-6
    out.append(f"static block = cge.py (oil +20%, remittances -10%): largest gap {worst:.1e} pp")
    # (e) Build 2 (18 Oct 2026): the Keynesian year = cge.py closure 'keynesian' (all three labour types unemployed at fixed
    # peso wages, capital fixed, exchange rate fixed), employment included; and a tamper (shock on one side only) is caught
    gk = CGE(SAM(t, {}, "condensed 2023 SAM"), closure="keynesian", unemployed=tuple(P.LAB), capital="fixed", wage="nominal")
    bk = gk.solve()
    solk = gk.solve({"remit_scale": 0.9})
    x = m.x0.copy(); x[30] = 0.9
    vk, sk, _ = m.static_keynesian(x)
    emp_c = np.array([solk.v["EMP"][gk.F.index(f)] / bk.v["EMP"][gk.F.index(f)] for f in P.LAB])
    gk_gap = float(max(np.abs(emp_c - sk["employment"]).max(), np.abs(solk.v["QA"] / gk.QA0 - vk["X"][:, 0] / m.X0).max())) * 100
    _, st, _ = m.static_keynesian(m.x0.copy())
    tamper = float(np.abs(emp_c - st["employment"]).max()) * 100
    ok &= gk_gap < 1e-6 and tamper > 0.1
    out.append(f"Keynesian year = cge.py (remittances -10%): employment and output gap {gk_gap:.1e} pp; tamper caught ({tamper:.2f} pp)")
    # (f) Build 1 (foreign-saving bridge): 2023 borrows exactly the SAM's temporary excess of foreign saving; the debt stays bounded
    X, Y, y0, info = m.bridge_baseline(120)
    bb = m.split(Y)["b"]
    ok &= abs(bb[0] + info["temporary"]) < 1e-6 * m.GDP0 and bb.min() > -0.5 * m.GDP0
    out.append(f"foreign-saving bridge: 2023 borrowing = excess (gap {bb[0] + info['temporary']:.1e}); lowest assets {bb.min() / m.GDP0 * 100:.1f}% of GDP")
    return ok, "; ".join(out)


@check("SL1", "slack at the start of short-run years (0.3.13): the LFS natural rate and slack recomputed; slack 0 = the "
              "option off; zero shock = baseline; the cap at the labour force less the natural rate; homogeneity; tamper caught; guards")
def sl1():
    import pandas as pd
    from infinity_gem import dynamic as D
    from infinity_gem.dynamic import DynamicCGE
    from infinity_gem.settings import dynamic_kwargs
    out, ok = [], True
    # (1) the natural rate, recomputed independently: the same penalised least squares written as one stacked least-squares problem
    # (numpy lstsq; the engine solves its normal equations, with quarter 1's effect eliminated, here quarter 4's), from the file read here
    raw = pd.read_csv(paths.DATA_RAW / "lfs" / "PSA_OpenSTAT_0021B3FKEI2_LFS_key_employment_rates_2005-2026.csv", comment="#",
                      na_values=".")
    qm = {"January": 1, "April": 2, "July": 3, "October": 4}
    r = raw[raw["Month"].isin(list(qm))].dropna(subset=["Unemployment Rate Both sexes"]).copy()
    r["q"] = r["Month"].map(qm)
    r["t"] = r["Year"] + (r["q"] - 1) / 4
    r = r.sort_values("t")
    s25 = r[r["Year"] <= 2025]
    T, lam = len(s25), 1600.0
    y, tq, qq = s25["Unemployment Rate Both sexes"].to_numpy(float), s25["t"].to_numpy(), s25["q"].to_numpy(int)
    keep = ~((tq >= 2020.25) & (tq <= 2021.75))
    G = np.zeros((T, 3))                                   # quarter effects g1, g2, g3; g4 = -(g1 + g2 + g3)
    for i, k in enumerate(qq):
        G[i] = -1.0 if k == 4 else np.eye(3)[k - 1]
    Xd = np.hstack([np.eye(T), G])[keep]
    Xs = np.zeros((T - 2, T + 3))
    for i in range(T - 2):
        Xs[i, i:i + 3] = np.sqrt(lam) * np.array([1.0, -2.0, 1.0])
    z = np.linalg.lstsq(np.vstack([Xd, Xs]), np.concatenate([y[keep], np.zeros(T - 2)]), rcond=None)[0]
    un_c, g = float(z[T - 1]) / 100, {1: z[T], 2: z[T + 1], 3: z[T + 2], 4: -(z[T] + z[T + 1] + z[T + 2])}
    est = D.lfs_natural_rate()
    nr_gap = max(abs(un_c - est["rate"]), max(abs(g[k] - est["seasonal"][k]) for k in g) / 100,
                 float(np.max(np.abs(z[:T] - est["trend"].to_numpy()))) / 100)
    t19 = float(z[list(tq).index(2019.75)])
    reg = abs(est["rate"] * 100 - 4.5104) < 5e-4            # regression value on the file of 14 Oct 2026 (check D1 guards the file)
    # (2) the baseline's unemployment and the slack by year: 2023-2025 the year's four rounds, 2026 the rounds on file less their quarter
    # effects, later years held; s = max(0, (1 - u_n) / (1 - u_t) - 1)
    ub = {yy: float(r[r["Year"] == yy]["Unemployment Rate Both sexes"].mean()) / 100 for yy in (2023, 2024, 2025)}
    r26 = r[r["Year"] == 2026]
    ub[2026] = float((r26["Unemployment Rate Both sexes"] - r26["q"].map(g)).mean()) / 100
    for yy in range(2027, 2031):
        ub[yy] = ub[2026]
    sl_c = {yy: max(0.0, (1 - un_c) / (1 - u) - 1) for yy, u in ub.items()}
    sl = D.lfs_labour_slack()
    sl_gap = max(abs(sl[yy] - sl_c[yy]) for yy in sl_c)
    trend26 = D.lfs_labour_slack(y2026="trend")
    ok &= nr_gap < 1e-9 and reg and sl_gap < 1e-9 and 5.0 <= t19 <= 5.25 and sl[2024] == 0.0 and trend26[2026] == trend26[2025]
    out.append(f"natural rate {est['rate']:.4%} (recomputed: gap {nr_gap:.1e}; 2019Q4 trend {t19:.2f}%, BSP DP 2024-11 NAIRU 5.02-5.19%); "
               f"slack 2025 {sl[2025]:.3%}, 2026 {sl[2026]:.3%} (recomputed: gap {sl_gap:.1e}; 2024 {sl[2024]:.1%}: tighter than the "
               f"natural rate)")
    # (3) the dynamic hybrid: Infinity GEM's own SAM v0.5, the 2026 scenarios' engine (wage curve 10.5, hoarding 0.85), 2026 short run
    kw = dynamic_kwargs("0.3 recommended", rice=True, land="fixed")
    kw.update(wage_curve=10.5, hoarding=0.85, short_run_years=(2026,))
    d = DynamicCGE(**kw)
    b = d.baseline()
    t, s = 2026, float(sl[2026])
    F = d.m.F
    lab = [k for k, f in enumerate(F) if f.startswith("flab")]
    keys = ("QA", "QH", "QE", "QM", "QINV", "EMP", "PQ", "WF", "EH", "DY", "YH")
    rd = lambda a_, b_: float(np.max(np.abs(np.asarray(a_, float) - np.asarray(b_, float))
                                     / np.maximum(np.abs(np.asarray(b_, float)), 1e-9)))
    boom = {t: {"qinv_scale": {"ccons": 1.3}, "trg_h_add": {"hhd-r1": 60.0, "hhd-u1": 60.0}}}
    slump = {t: {"qinv_scale": {"ccons": 0.85}}}
    peso = {t: {"exr_scale": 1.01}}

    def run(sl_, sh):
        d.a["sr_labour_slack"] = sl_
        return d.scenario(sh)

    try:
        p_off, p_0, p_s = run(None, boom), run(0.0, boom), run(s, boom)
        q_off, q_0 = run(None, slump), run({t: 0.0}, slump)
        z_s = run(s, {t: {}})
        e_off, e_s = run(None, peso), run(sl, peso)
        nest = max(max(rd(x_.solutions[yy][k], y_.solutions[yy][k]) for yy in d.years for k in keys)
                   for x_, y_ in ((p_0, p_off), (q_0, q_off)))
        zd = max(float((z_s.table.real_gdp / b.table.real_gdp - 1).abs().max()), float((z_s.table.cpi / b.table.cpi - 1).abs().max()))
        cap_s = str(p_s.table.loc[t, "employment_capped"]).split(",")
        sup = {k: float(b.solutions[t]["EMP"][k]) * (1 + s) for k in lab}          # the cap: the baseline's employment x (1 + s)
        at_cap = max(abs(float(p_s.solutions[t]["EMP"][k]) / sup[k] - 1) for k in lab if F[k] in cap_s)
        above = max(float(p_s.solutions[t]["EMP"][k]) / sup[k] - 1 for k in lab)
        rise = min(float(p_s.solutions[t]["EMP"][k] / p_off.solutions[t]["EMP"][k]) - 1 for k in lab if F[k] in cap_s)
        cpi = lambda p_: float(p_.solutions[t]["CPI"]) / float(b.solutions[t]["CPI"]) - 1
        gdp = lambda p_: float(p_.table.real_gdp[t] / b.table.real_gdp[t]) - 1
        dirn = cpi(e_s) < cpi(e_off) and gdp(e_s) > gdp(e_off)
        # homogeneity, as CS1: the baseline year solved at a consumer price level 10% higher carries every nominal anchor +10%
        bs = b.solutions[t]
        x11 = bs.x.copy()
        for k_ in ("PDS", "PQ", "WF", "RK", "RL", "RN", "EXR"):
            x11[d.m.slices[k_]] *= 1.1
        b11 = d.m.solve({**bs.shocks, "cpi": 1.1}, x_start=x11)
        d.base.solutions[t] = b11
        p_h = run(s, boom)
        d.base.solutions[t] = bs
        hq = max(rd(p_h.solutions[t][k], p_s.solutions[t][k]) for k in ("QA", "QH", "QE", "QM", "QINV", "EMP"))
        hp = max(rd(np.asarray(p_h.solutions[t][k], float)[i_] / 1.1, np.asarray(p_s.solutions[t][k], float)[i_])
                 for k, i_ in (("PQ", d.ms.iQ), ("PDS", d.ms.iD), ("WF", lab)))
        # tamper: an engine that ignores the option (the cap left at the baseline's employment)
        d._sr_slack = lambda t_: 0.0
        p_t = run(s, boom)
        at_cap_t = max(abs(float(p_t.solutions[t]["EMP"][k]) / sup[k] - 1) for k in lab if F[k] in cap_s)
    finally:
        d.base.solutions[t] = b.solutions[t]
        d.__dict__.pop("_sr_slack", None)
        d.a["sr_labour_slack"] = None
    # guards: a negative share, 0.25 or more, NaN, a bool, a year that is not an integer, a negative share by year, no hybrid closure,
    # no employment cap (at construction), and the option set afterwards with the cap off
    refused = 0
    for bad in ({"sr_labour_slack": -0.01}, {"sr_labour_slack": 0.3}, {"sr_labour_slack": float("nan")}, {"sr_labour_slack": True},
                {"sr_labour_slack": {"2026": 0.01}}, {"sr_labour_slack": {2026: -0.01}}, {"sr_labour_slack": s, "hybrid": False},
                {"sr_labour_slack": s, "employment_cap": False}):
        try:
            DynamicCGE(**dict(kw, **bad))
        except ValueError:
            refused += 1
    d.a.update(employment_cap=False, sr_labour_slack=s)
    try:
        d.scenario(slump)
    except ValueError:
        refused += 1
    finally:
        d.a.update(employment_cap=True, sr_labour_slack=None)
    ok &= (nest == 0.0 and zd < 1e-9 and at_cap < 1e-8 and above < 1e-8 and rise > 0.5 * s and dirn and b11.ok and hq < 1e-9
           and hp < 1e-9 and at_cap_t > 0.5 * s and refused == 9)
    out.append(f"dynamic (Infinity GEM SAM, beta 10.5, hoarding 0.85; 2026 slack {s:.3%}): slack 0 vs off {nest:.1e} (boom and slump, all years); "
               f"zero shock {zd:.1e}; boom: capped ({','.join(cap_s)}) at the baseline's employment x (1 + s) to {at_cap:.1e}, none above "
               f"({above:+.1e}), {rise:+.3%} more jobs than with the cap at the baseline's employment; peso 1% weaker: CPI {cpi(e_s):+.3%} vs "
               f"{cpi(e_off):+.3%}, GDP {gdp(e_s):+.3%} vs {gdp(e_off):+.3%}; homogeneity: quantities {hq:.1e}, prices {hp:.1e}; tamper "
               f"(slack ignored): cap missed by {at_cap_t:.2%} (caught); refused {refused}/9")
    return ok, "; ".join(out)


@check("EC1", "an employment cap that settles (0.3.13): below the cap = the model without it, at the cap = the market-"
              "clearing model; complementarity; homogeneity; smooth = switching cap in the dynamic model; the BSP rule settles under "
              "option (c); tamper caught; guards")
def ec1():
    from infinity_gem import stickiness as STK
    from infinity_gem.cge import CGE
    from infinity_gem.dynamic import DynamicCGE
    from infinity_gem.monetary import rule as bsp_rule
    from infinity_gem.oil import cge_oil_shock
    from infinity_gem.settings import cge_kwargs, dynamic_kwargs, short_run_closure
    rd = lambda a_, b_: float(np.max(np.abs(np.asarray(a_, float) - np.asarray(b_, float))
                                     / np.maximum(np.abs(np.asarray(b_, float)), 1e-9)))
    qk, pk = ("QA", "QH", "QE", "QM", "QINV", "EMP", "QD"), ("PQ", "PDS", "WF", "PA", "EH", "DY")
    out, ok = [], True
    # (A) the static short-run model: Infinity GEM's own SAM v0.5, the 2026 scenarios' short-run closure (all skills on fixed wages), fixed land
    kw = cge_kwargs("0.3 recommended", rice=True)
    path = kw.pop("path")
    base = dict(**short_run_closure("0.3 recommended"), land="fixed", **kw)
    slump, boom = {"qinv_scale": {"ccons": 0.9}}, {"qinv_scale": {"ccons": 1.3}, "trg_h_add": {"hhd-r1": 60.0, "hhd-u1": 60.0}}
    for h in (0.0, 0.85):
        m0 = CGE.from_sam(path, **base, hoarding=h)
        mc = CGE.from_sam(path, **base, hoarding=h, labour_cap=True)
        ku = mc.iU
        ref = {"hoard_ref": np.asarray(m0.QF0, float)} if h else {}
        bc = mc.solve(ref or None)
        bench = max(float(bc.residual_max), float(np.max(np.abs(bc["LPREM"]))))
        s0, sc = m0.solve({**slump, **ref}), mc.solve({**slump, **ref})
        below = max(rd(sc[k], s0[k]) for k in qk + pk)
        sb = mc.solve({**boom, **ref})
        capped = [mc.F[k] for k in ku if float(sb["LPREM"][k]) > 1e-8]
        prod = np.asarray(sb["QF"], float).sum(axis=1)
        at_cap = max(abs(prod[k] / mc.QFS0[k] - 1) for k in ku if mc.F[k] in capped)
        a_ = (mc.QFS0[ku] - prod[ku]) / mc.QFS0[ku]
        comp = max(float(np.max(-a_)), float(np.max(-np.asarray(sb["LPREM"], float)[ku])),
                   float(np.max(np.abs(a_ * np.asarray(sb["LPREM"], float)[ku]))))
        mr = CGE.from_sam(path, **dict(base, unemployed=tuple(f for f in mc.unemployed if f not in capped)), hoarding=h)
        sr = mr.solve({**boom, **ref})
        regime = max(rd(sb[k], sr[k]) for k in qk + ("PQ", "PDS", "WF", "PA"))
        walras = abs(float(sb["WALRAS"])) / float(mc.qinv.sum())
        gid = abs(mc.gdp(sb)["nominal_expenditure"] - mc.gdp(sb)["nominal_income"])
        s2 = mc.solve({**boom, **ref, "exr": 1.1, "wbar": {f: 1.1 for f in mc.unemployed}})      # every nominal anchor +10%
        hq = max(rd(s2[k], sb[k]) for k in qk)
        hp = max(max(rd(np.asarray(s2[k], float)[i_] / 1.1, np.asarray(sb[k], float)[i_]) for k, i_ in (("PQ", mc.iQ), ("PDS", mc.iD))),
                 rd(np.asarray(s2["WF"], float)[ku] / 1.1, np.asarray(sb["WF"], float)[ku]), rd(s2["LPREM"][ku], sb["LPREM"][ku]))
        tol_r = 1e-9 if h == 0 else 2e-4                    # with hoarding: its C1 smoothing of min(desired, slack), at most eps / 2
        good = (all(x.ok for x in (bc, s0, sc, sb, sr, s2)) and bench < 1e-8 and below < 1e-9 and len(capped) == len(ku)
                and at_cap < 1e-9 and comp < 1e-12 and regime < tol_r and walras < 1e-9 and gid < 1e-6 and hq < 1e-9 and hp < 1e-9)
        ok &= good
        out.append(f"static, hoarding {h:g}: benchmark {bench:.1e}; slump vs no cap {below:.1e}; boom: capped {','.join(capped)} at supply "
                   f"{at_cap:.1e}, premia {', '.join(f'{float(sb['LPREM'][k]):.1%}' for k in ku)}, complementarity {comp:.1e}, vs the "
                   f"market-clearing model {regime:.1e}; Walras {walras:.1e}, GDP identity {gid:.1e}; homogeneity q {hq:.1e} p {hp:.1e}")
    refused = 0
    for bad in (dict(kw, closure="investment"), dict(base, unemployed=()), dict(base, fx="flexible")):   # not the Keynesian closure;
        try:                                                                   # no fixed-wage type; a flexible peso
            CGE.from_sam(path, **bad, labour_cap=True)
        except ValueError:
            refused += 1
    # (B) the dynamic hybrid: Infinity GEM's own SAM, the 2026 scenarios' engine (wage curve 10.5, hoarding 0.85), 2026 short run
    kwd = dynamic_kwargs("0.3 recommended", rice=True, land="fixed")
    kwd.update(wage_curve=10.5, hoarding=0.85, short_run_years=(2026,))
    d = DynamicCGE(**kwd)
    b = d.baseline()
    t = 2026
    keys = ("QA", "QH", "QE", "QM", "QINV", "EMP", "PQ", "WF", "EH", "DY", "YH")
    shocks = {"slump": {t: {**cge_oil_shock(d.m, 0.30), "qinv_scale": {"ccons": 0.85}}},
              "boom": {t: {"qinv_scale": {"ccons": 1.3}, "trg_h_add": {"hhd-r1": 60.0, "hhd-u1": 60.0}}}}

    def run(cap, sh, lam=None):
        d.a["employment_cap"], d.a["sr_consumption"] = cap, (None if lam is None else {"htm": lam})
        return d.scenario(sh)

    gaps, capped_b = {}, ""
    try:
        z = run("smooth", {t: {}})
        zd = max(float((z.table.real_gdp / b.table.real_gdp - 1).abs().max()), float((z.table.cpi / b.table.cpi - 1).abs().max()))
        for lam in (None, 0.62):
            for nm, sh in shocks.items():
                p_r, p_s = run(True, sh, lam), run("smooth", sh, lam)
                gaps[(nm, lam)] = max(rd(p_s.solutions[yy][k], p_r.solutions[yy][k]) for yy in d.years for k in keys)
                if nm == "boom":
                    capped_b = str(p_s.table.loc[t, "employment_capped"])
                    if lam is not None:                  # the rule still holds with the cap binding (as CS1 computes it)
                        s_, ref_ = p_s.solutions[t], b.solutions[t]
                        mb = np.clip(np.asarray(d.ms.mps, float) * (1 + float(ref_["MPSADJ"])), -1.0, 1.0)
                        tgt = (lam * float(((1 - mb) * np.asarray(s_["DY"], float)).sum())
                               + (1 - lam) * float(np.sum(ref_["EH"])) * float(s_["CPI"]) / float(ref_["CPI"]))
                        rule_gap = abs(float(np.sum(s_["EH"])) - tgt) / tgt
                        p_boom = p_s
        # homogeneity with the cap binding (the boom, the consumption rule on), as CS1: the baseline year at a 10% higher price level
        bs = b.solutions[t]
        x11 = bs.x.copy()
        for k_ in ("PDS", "PQ", "WF", "RK", "RL", "RN", "EXR"):
            x11[d.m.slices[k_]] *= 1.1
        b11 = d.m.solve({**bs.shocks, "cpi": 1.1}, x_start=x11)
        d.base.solutions[t] = b11
        p_h = run("smooth", shocks["boom"], 0.62)
        d.base.solutions[t] = bs
        lab = [k for k, f in enumerate(d.m.F) if f.startswith("flab")]
        hq = max(rd(p_h.solutions[t][k], p_boom.solutions[t][k]) for k in ("QA", "QH", "QE", "QM", "QINV", "EMP"))
        hp = max(max(rd(np.asarray(p_h.solutions[t][k], float)[i_] / 1.1, np.asarray(p_boom.solutions[t][k], float)[i_])
                     for k, i_ in (("PQ", d.ms.iQ), ("PDS", d.ms.iD), ("WF", lab))),
                 rd(p_h.solutions[t]["LPREM"][lab], p_boom.solutions[t]["LPREM"][lab]))
        # tamper: the cap left at the benchmark's labour supply (the labour supply path of the year dropped from the short-run spec)
        orig_spec = d._short_run_spec

        def tampered(spec, t_, K, ms=None):
            sp = orig_spec(spec, t_, K, ms)
            sp["qfs_scale"] = {f: (1.0 if f.startswith("flab") else v) for f, v in sp["qfs_scale"].items()}
            return sp
        d._short_run_spec = tampered
        try:
            z_t = run("smooth", {t: {}})
            zt = float((z_t.table.real_gdp / b.table.real_gdp - 1).abs().max())
        except RuntimeError:                                 # a tampered model that no longer solves counts as caught
            zt = float("inf")
    finally:
        d.base.solutions[t] = b.solutions[t]
        d.__dict__.pop("_short_run_spec", None)
        d.a["employment_cap"], d.a["sr_consumption"] = True, None
    tol_d = 2e-4                                             # hoarding 0.85: its smoothing at the cap (static test above: exact without)
    for bad in ({"employment_cap": "soft"}, {"employment_cap": "smooth", "hybrid": False},
                {"employment_cap": "smooth", "sr_fx": "flexible"}):
        try:
            DynamicCGE(**dict(kwd, **bad))
        except ValueError:
            refused += 1
    d.a["employment_cap"] = "soft"
    try:
        d.scenario(shocks["slump"])
    except ValueError:
        refused += 1
    finally:
        d.a["employment_cap"] = True
    ok &= (zd < 1e-9 and gaps[("slump", None)] < 1e-8 and gaps[("slump", 0.62)] < 1e-8 and gaps[("boom", None)] < tol_d
           and gaps[("boom", 0.62)] < tol_d and bool(capped_b) and rule_gap < 1e-8 and b11.ok and hq < 1e-9 and hp < 1e-9
           and zt > 1e-4 and refused == 7)
    out.append(f"dynamic (Infinity GEM SAM, beta 10.5, hoarding 0.85): zero shock {zd:.1e}; smooth vs switching cap: slump {gaps[('slump', None)]:.1e} "
               f"({gaps[('slump', 0.62)]:.1e} with the consumption rule), boom ({capped_b}) {gaps[('boom', None)]:.1e} "
               f"({gaps[('boom', 0.62)]:.1e}); the rule at the cap {rule_gap:.1e}; homogeneity q {hq:.1e} p {hp:.1e}; tamper (cap at the "
               f"benchmark's supply): zero shock off by {zt:.2%} (caught); refused {refused}/7")
    # (C) the BSP rule inside the path under option (c) (markup prices with stickiness by sector, mk_pass 0, the consumption rule
    # lam 0.7, wage curve 2.4): the 2026 oil and construction shock, PAMPh's rule, theta 1.5; it must converge with the smooth cap
    kwc = dict(kwd, wage_curve=2.4, sr_pricing="markup", sr_markup_pass=0.0, sr_consumption={"htm": 0.7}, employment_cap="smooth",
               sr_labour_slack=0.00891)
    dc = DynamicCGE(**kwc)
    dc.a["sr_stickiness"] = STK.sectoral([a for i, a in enumerate(dc.ms.A) if dc.ms.isMK[i]])
    dc.baseline()
    rl = bsp_rule("pamph")
    pm = dc.monetary_scenario(shocks["slump"], rule=rl, theta=1.5)
    mo = pm.monetary
    conv, i26 = bool(mo.attrs["converged"]), float(mo.loc[t, "policy_rate_gap_pp"])
    # the fixed point, recomputed here: the rule's rate from the path's own gaps (quarterly partial adjustment within each year),
    # adaptive expectations (last year's inflation gap), and the investment scale the path was run with, exp(-theta r / 100), within
    # 0.05 pp of real rate (theta x 0.05 / 100 of the scale): the rule's tolerance on the rate, 0.01 pp, plus the change of expected
    # inflation between the last two iterations (the last path ran with the expectations of the one before)
    i_end, fp_rate, fp_pie, fp_scale, prev_pi = 0.0, 0.0, 0.0, 0.0, None
    for yy in mo.index:
        tg = (float(rl["phi_pi"]) * float(mo.loc[yy, "inflation_gap_pp"]) + float(rl["phi_x"]) * float(mo.loc[yy, "output_gap_pct"])
              + float(rl.get("phi_e", 0.0)) * float(mo.loc[yy, "depreciation_gap_pp"]))
        rho = float(rl["rho"])
        i_avg = tg + (i_end - tg) * rho * (1 - rho ** 4) / (4 * (1 - rho))
        i_end = tg + (i_end - tg) * rho ** 4
        pie = 0.0 if prev_pi is None else prev_pi
        prev_pi = float(mo.loc[yy, "inflation_gap_pp"])
        fp_rate = max(fp_rate, abs(i_avg - float(mo.loc[yy, "policy_rate_gap_pp"])))
        fp_pie = max(fp_pie, abs(pie - float(mo.loc[yy, "expected_inflation_gap_pp"])))
        fp_scale = max(fp_scale, abs(float(mo.loc[yy, "investment_scale"]) - float(np.exp(-1.5 * (i_avg - pie) / 100))))
    ok &= conv and fp_rate < 1e-9 and fp_pie < 1e-9 and fp_scale < 1.5 * 0.05 / 100
    out.append(f"option (c) with the consumption rule and the BSP rule (PAMPh, theta 1.5; world oil +30% and construction -15% in 2026): "
               f"converged {conv} in {mo.attrs['iterations']} iterations; policy-rate gap 2026 {i26:+.2f} pp (inflation gap "
               f"{float(mo.loc[t, 'inflation_gap_pp']):+.2f} pp, output gap {float(mo.loc[t, 'output_gap_pct']):+.2f}%), investment scale "
               f"{float(mo.loc[t, 'investment_scale']):.4f}; the rule recomputed on the path's own gaps: rate {fp_rate:.1e}, expectations "
               f"{fp_pie:.1e}, the investment scale applied {fp_scale:.1e} (tolerance {1.5 * 0.05 / 100:.1e})")
    return ok, "; ".join(out)


@check("OP1", "a within-year share of the world oil price reaching domestic prices (0.3.13): omega 1 = the option "
              "off; zero shock = baseline; the import-price equation, the government's absorption, the current account; accounts close; "
              "homogeneity; tamper caught; guards")
def op1():
    from infinity_gem.cge import CGE
    from infinity_gem.dynamic import DynamicCGE, OIL_PASS
    from infinity_gem.oil import cge_oil_shock
    from infinity_gem.settings import cge_kwargs, dynamic_kwargs, short_run_closure
    om = 0.6                                      # test value (the calibrated share: scenarios/row83_oil_passthrough.py)
    rd = lambda a_, b_: float(np.max(np.abs(np.asarray(a_, float) - np.asarray(b_, float))
                                     / np.maximum(np.abs(np.asarray(b_, float)), 1e-9)))

    def pm_rule(m, s_, o_, ref):                  # the import-price equation, written here independently of cge.py: the world price in
        sh = m.make_shocks(s_.shocks)             # pesos, the domestic price before the tariff (R x (W / R) ** omega; omega 1 elsewhere),
        W = m.pwm * sh["pwm_scale"] * float(s_["EXR"])    # the import price with the tariff and the margin ('split' margins)
        dom = np.where(o_ != 1.0, ref * (W / ref) ** o_, W)
        return W, dom, dom * (1 + m.tm * sh["tm_scale"]) + m.icx * float(s_["PTRC"]), sh

    def border(m, s_, W, dom, sh):                 # the government's absorption, the import tax and the current account, recomputed
        QM, v = np.asarray(s_["QM"], float), s_.v
        sub = (W - dom) * QM
        scale = float(m.QM0.sum())
        g_sub = float(np.max(np.abs(np.asarray(v.get("OILSUB", np.zeros_like(QM)), float) - sub))) / scale
        g_mtax = float(np.max(np.abs(np.asarray(v["MTAX"], float) - (m.tm * sh["tm_scale"] * dom * QM - sub)))) / scale
        fcu = float((m.pwm * sh["pwm_scale"] * (QM + m.rex)).sum() + m.frow_out.sum() + m.erow_out + m.hrow_out.sum() + m.grow_out
                    + sh["grow_out_add"])
        return g_sub, g_mtax, abs(fcu - float(v["fcu_out"])) / scale, float(sub.sum())

    # (A) the static short-run model: Infinity GEM's own SAM, the 2026 scenarios' short-run closure, flexible prices and markup pricing; world oil
    # +30% and the peso 5% weaker; omega 0.6 on oil and crude
    kw = cge_kwargs("0.3 recommended", rice=True)
    path = kw.pop("path")
    base = dict(**short_run_closure("0.3 recommended"), land="fixed", **kw)
    out, ok = [], True
    qk, pk = ("QA", "QH", "QE", "QM", "QD", "QINV", "EMP"), ("PQ", "PDS", "PM", "WF", "EH", "MTAX", "GSAV")
    for pricing in ("flex", "markup"):
        m = CGE.from_sam(path, **base, pricing=pricing)
        oil = {c: om for c in OIL_PASS}
        o_ = np.array([oil.get(c, 1.0) for c in m.C])
        sh0 = {**cge_oil_shock(m, 0.30), "exr": 1.05}
        b, s_off, s_1, s_p = (m.solve(), m.solve(sh0), m.solve({**sh0, "oil_pass": {c: 1.0 for c in OIL_PASS}}),
                              m.solve({**sh0, "oil_pass": oil}))
        nest = max(rd(s_1[k], s_off[k]) for k in qk + pk)
        z0 = m.solve({"oil_pass": oil})          # no world price change: the reference price, the benchmark
        zres = max(rd(z0[k], b[k]) for k in qk + pk)
        W, dom, pm, sh = pm_rule(m, s_p, o_, 1.0)
        pm_gap = float(np.max(np.abs(np.asarray(s_p["PM"], float)[m.hasM] / pm[m.hasM] - 1)))
        g_sub, g_mtax, ca, sub = border(m, s_p, W, dom, sh)
        walras = abs(float(s_p["WALRAS"])) / float(m.qinv.sum())
        gid = abs(m.gdp(s_p)["nominal_expenditure"] - m.gdp(s_p)["nominal_income"])
        S = m.rebuild_sam(s_p)
        keep = [c for c in S.index if c not in ("s-i", "row")]           # rebuild_sam leaves the Keynesian closure's foreign saving out
        imb = float(np.abs((S.sum(axis=1) - S.sum(axis=0)).loc[keep]).max()) / float(S.values.sum())
        i = m.C.index("cpetr")
        fuel_off, fuel_p = float(s_off["PQ"][i] / b["PQ"][i] - 1), float(s_p["PQ"][i] / b["PQ"][i] - 1)
        dirn = 0 < fuel_p < fuel_off and float(s_p["GSAV"]) < float(s_off["GSAV"]) and sub > 0
        s_0 = m.solve({**sh0, "oil_pass": {c: 0.0 for c in OIL_PASS}})  # omega 0: the domestic price stays at the reference (1)
        lst = o_ != 1.0
        held = float(np.max(np.abs(np.asarray(s_0["PM_dom"], float)[lst] - 1.0)))
        # homogeneity: every nominal anchor +10% (the peso, the reference world price in pesos, the peso wage anchors; the markup anchor)
        sp2 = {**sh0, "oil_pass": oil, "exr": 1.05 * 1.1, "oil_ref": 1.1, "wbar": {f: 1.1 for f in m.unemployed}}
        if pricing == "markup":
            sp2["pa_anchor"] = {a: 1.1 * (1 - m.ta[j]) for j, a in enumerate(m.A)}
        s2 = m.solve(sp2)
        hq = max(rd(s2[k], s_p[k]) for k in qk)
        hp = max(max(rd(np.asarray(s2[k], float)[i_] / 1.1, np.asarray(s_p[k], float)[i_])
                     for k, i_ in (("PQ", m.iQ), ("PDS", m.iD), ("PM", m.hasM))), rd(np.asarray(s2["OILSUB"], float)[lst] / 1.1,
                                                                                 np.asarray(s_p["OILSUB"], float)[lst]))
        good = (all(x.ok for x in (b, s_off, s_1, s_p, z0, s_0, s2)) and nest == 0.0 and zres < 1e-9 and pm_gap < 1e-12
                and g_sub < 1e-12 and g_mtax < 1e-12 and ca < 1e-12 and walras < 1e-9 and gid < 1e-6 and imb < 1e-9 and dirn
                and held < 1e-12 and hq < 1e-9 and hp < 1e-9)
        ok &= good
        out.append(f"static {pricing}: omega 1 vs off {nest:.1e}; zero shock {zres:.1e}; PM rule {pm_gap:.1e}; absorption {g_sub:.1e}, "
                   f"import tax {g_mtax:.1e}, current account {ca:.1e}; Walras {walras:.1e}, GDP identity {gid:.1e}, SAM {imb:.1e}; fuel "
                   f"{fuel_p:+.2%} vs {fuel_off:+.2%} in full, the government absorbs {sub:.1f} bn; omega 0 holds the price {held:.1e}; "
                   f"homogeneity q {hq:.1e} p {hp:.1e}")
    refused = 0
    for bad in ({"oil_pass": 1.2}, {"oil_pass": -0.1}, {"oil_pass": float("nan")}, {"oil_pass": True}, {"oil_pass": {"cxxx": 0.5}},
                {"oil_ref": 0.0}, {"oil_ref": True}, {"oil_pass": {"cfood": 0.5}, "erpt": {"cfood": 0.5}}):
        try:
            m.solve(bad)
        except ValueError:
            refused += 1
    try:                                          # the long-run closure: world prices pass through in full there
        CGE.from_sam(path, **kw).solve({"oil_pass": 0.5})
    except ValueError:
        refused += 1
    # (B) the dynamic hybrid: Infinity GEM's own SAM, the 2026 scenarios' engine (wage curve 10.5, hoarding 0.85), 2026 short run; world oil +30%,
    # construction investment -15% and the peso 2% weaker in 2026
    kwd = dynamic_kwargs("0.3 recommended", rice=True, land="fixed")
    kwd.update(wage_curve=10.5, hoarding=0.85, short_run_years=(2026,))
    d = DynamicCGE(**kwd)
    bl = d.baseline()
    t = 2026
    shock = {t: {**cge_oil_shock(d.m, 0.30), "qinv_scale": {"ccons": 0.85}, "exr_scale": 1.02}}
    keys = ("QA", "QH", "QE", "QM", "QINV", "EMP", "PQ", "WF", "EH", "DY", "YH")
    qkeys = ("QA", "QH", "QE", "QM", "QINV", "QG", "EMP")
    lab = [k for k, f in enumerate(d.m.F) if f.startswith("flab")]
    prices = lambda s_: [np.asarray(s_["PQ"], float)[d.ms.iQ], np.asarray(s_["PDS"], float)[d.ms.iD], np.asarray(s_["WF"], float)[lab],
                         np.asarray(s_["PM"], float)[d.ms.hasM], np.asarray(s_["EH"], float), np.array([float(s_["CPI"]), float(s_["EXR"])])]
    hom = lambda p_, q_: (max(rd(p_.solutions[t][k], q_.solutions[t][k]) for k in qkeys),
                          max(rd(x_ / 1.1, y_) for x_, y_ in zip(prices(p_.solutions[t]), prices(q_.solutions[t]))),
                          max(rd(p_.solutions[y][k], q_.solutions[y][k]) for y in d.years if y > t for k in keys))

    def run(o, sh=shock, erpt=None):
        d.a["sr_oil_pass"], d.a["sr_erpt"] = o, erpt
        return d.scenario(sh)

    bs = bl.solutions[t]
    orig_spec = d._short_run_spec
    try:
        p_off, p_1, p_c = run(None), run(1.0), run(om)
        z = run(om, {t: {}}, erpt=0.3)            # zero shock with the peso's partial pass-through (non-oil imports) on as well
        nest_d = max(rd(p_1.solutions[y][k], p_off.solutions[y][k]) for y in d.years for k in keys)
        zd = max(float((z.table.real_gdp / bl.table.real_gdp - 1).abs().max()), float((z.table.cpi / bl.table.cpi - 1).abs().max()))
        s = p_c.solutions[t]
        o_d = np.array([om if c in OIL_PASS else 1.0 for c in d.ms.C])
        ref_d = np.asarray(bs["pwm"], float) * float(bs["EXR"])         # the baseline year's world price in pesos
        W, dom, pm_d, sh = pm_rule(d.ms, s, o_d, ref_d)
        pm_gap_d = float(np.max(np.abs(np.asarray(s["PM"], float)[d.ms.hasM] / pm_d[d.ms.hasM] - 1)))
        g_sub_d, g_mtax_d, ca_d, sub_d = border(d.ms, s, W, dom, sh)
        i = d.ms.C.index("cpetr")
        fuel_dir = float(s["PQ"][i]) < float(p_off.solutions[t]["PQ"][i]) and float(s["GSAV"]) < float(p_off.solutions[t]["GSAV"])
        # homogeneity, as check ER1: the baseline year solved at a consumer price level 10% higher carries every nominal anchor of the
        # short-run year +10% (the peso and with it the reference world price in pesos, the peso wage anchors and the wage curve's)
        x11 = bs.x.copy()
        for k_ in ("PDS", "PQ", "WF", "RK", "RL", "RN", "EXR"):
            x11[d.m.slices[k_]] *= 1.1
        b11 = d.m.solve({**bs.shocks, "cpi": 1.1}, x_start=x11)
        d.base.solutions[t] = b11
        p_h = run(om)
        # tamper: the reference held at the benchmark's world price in pesos (1), not the baseline year's

        def tampered(spec, t_, K, ms=None):
            sp = orig_spec(spec, t_, K, ms)
            if "oil_ref" in sp:
                sp["oil_ref"] = {c: 1.0 for c in sp["oil_ref"]}
            return sp
        d._short_run_spec = tampered
        p_t = run(om)
    finally:
        d.base.solutions[t] = bs
        d.__dict__.pop("_short_run_spec", None)
        d.a["sr_oil_pass"], d.a["sr_erpt"] = None, None
    h_d, h_t = hom(p_h, p_c), hom(p_t, p_c)
    # guards: omega outside [0, 1] or not a number, an unknown commodity, no hybrid closure, a commodity that also carries an sr_erpt
    # share (a one-share sr_erpt covers every commodity but oil and crude), a scenario's own key, and the option set afterwards without
    # the hybrid closure
    for bad in ({"sr_oil_pass": 1.5}, {"sr_oil_pass": True}, {"sr_oil_pass": float("nan")}, {"sr_oil_pass": {"cxxx": 0.3}},
                {"sr_oil_pass": om, "hybrid": False}, {"sr_oil_pass": om, "sr_erpt": {"cpetr": 0.5}},
                {"sr_oil_pass": {"cfood": 0.5}, "sr_erpt": 0.3}):
        try:
            DynamicCGE(**dict(kwd, **bad))
        except ValueError:
            refused += 1
    try:
        run(om, {t: {**shock[t], "oil_pass": {"cpetr": 0.2}}})
    except ValueError:
        refused += 1
    d.a["hybrid"] = False
    try:
        run(om)
    except ValueError:
        refused += 1
    finally:
        d.a["hybrid"], d.a["sr_oil_pass"], d.a["sr_erpt"] = True, None, None
    ok &= (nest_d == 0.0 and zd < 1e-9 and pm_gap_d < 1e-12 and g_sub_d < 1e-12 and g_mtax_d < 1e-12 and ca_d < 1e-12 and fuel_dir
           and b11.ok and max(h_d) < 1e-9 and h_t[0] > 1e-6 and refused == 18)
    out.append(f"dynamic (Infinity GEM SAM, beta 10.5, hoarding 0.85; 2026 oil +30%, construction -15%, peso +2%): omega 1 vs off {nest_d:.1e} "
               f"(all years); zero shock (with sr_erpt 0.3) {zd:.1e}; PM rule against the baseline year's world price in pesos "
               f"{pm_gap_d:.1e}; absorption {g_sub_d:.1e}, import tax {g_mtax_d:.1e}, current account {ca_d:.1e}; fuel 2026 "
               f"{float(s['PQ'][i]) / float(bs['PQ'][i]) - 1:+.2%} vs {float(p_off.solutions[t]['PQ'][i]) / float(bs['PQ'][i]) - 1:+.2%} in full, "
               f"the government absorbs {sub_d:.1f} bn; homogeneity: quantities {h_d[0]:.1e}, prices {h_d[1]:.1e}, later years "
               f"{h_d[2]:.1e}; tamper (reference at the benchmark's world price): quantities {h_t[0]:.1e} (caught); refused {refused}/18")
    return ok, "; ".join(out)


@check("S7", "Infinity GEM's own 2023 SAM v0.6 (research, opt-in): rebuild, PSA sector accounts, FIES shares, CGE reproduces it; v0.5 still default")
def s7():
    import os
    import subprocess                                      # 0.3.13 (23 Oct 2026): the standalone test, as check X3 runs its tests
    r = subprocess.run([sys.executable, str(ROOT / "checks" / "test_own_sam_v06.py")], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(ROOT), timeout=1800, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    lines = [l for l in r.stdout.splitlines() if l.strip()]
    return r.returncode == 0, (lines[-1] if lines else "no output")


@check("S10", "Infinity GEM's own 2023 SAM v0.7 (research, opt-in): coal split from mining; rebuilds, v0.5e back, coal account, CGE, other SAMs unchanged")
def s10():
    import os
    import subprocess                                      # 0.3.13 (24 Oct 2026): the standalone test, in S7's pattern
    r = subprocess.run([sys.executable, str(ROOT / "checks" / "test_own_sam_v07.py")], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(ROOT), timeout=1800, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    lines = [l for l in r.stdout.splitlines() if l.strip()]
    return r.returncode == 0, (lines[-1] if lines else "no output")


@check("S11", "Infinity GEM's own 2023 SAM v0.7b (research, opt-in): v0.7 without the coal double count; rebuilds, targets, controls, CGE")
def s11():
    import os
    import subprocess                                      # 0.3.13 (24 Oct 2026): the standalone test, in S10's pattern
    r = subprocess.run([sys.executable, str(ROOT / "checks" / "test_own_sam_v07b.py")], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(ROOT), timeout=1800, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    lines = [l for l in r.stdout.splitlines() if l.strip()]
    return r.returncode == 0, (lines[-1] if lines else "no output")


@check("S12", "Infinity GEM's own 2023 SAM v0.9 (research, opt-in): customs-anchored coal and fuel account; rebuilds, customs targets, CGE")
def s12():
    import os
    import subprocess                                      # 0.3.13 (24 Oct 2026): the standalone test, in S11's pattern
    r = subprocess.run([sys.executable, str(ROOT / "checks" / "test_own_sam_v09.py")], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(ROOT), timeout=1800, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    lines = [l for l in r.stdout.splitlines() if l.strip()]
    return r.returncode == 0, (lines[-1] if lines else "no output")


@check("SD1", "stochastic outlook: opt-in typhoon draw: off by default, calibration, mapping, refusals")
def sd1():
    import subprocess                                      # 0.3.13 (23 Oct 2026): the standalone test, as check X3 runs its tests
    p = subprocess.run([sys.executable, str(ROOT / "validation" / "stochastic_disasters" / "test_disaster_draw.py")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
    res = [l for l in p.stdout.splitlines() if l.startswith(("[PASS]", "[FAIL]"))]
    ok = p.returncode == 0 and len(res) == 9 and all(l.startswith("[PASS]") for l in res)
    return ok, f"{sum(l.startswith('[PASS]') for l in res)} of 9 pass; " + "; ".join(l[:70] for l in res if l.startswith("[FAIL]"))


EXTRA = [i3, i4, c8, y2, y3, v2, v3, e1, y4, y5, l1, h1, s1, v4, i5, v5, s2, h2, h3, a2, w1, v6, v7, m2, d3, w2, x1, ml1, lp1, sh1, cr1, s3, y6, pk1, sr1, wc1, ex1, vd1, ic1, ps1, s4, lg1, e2, x2, s5, s6, ml2, pc1, hd1, x3, en1, en2, st1, ir1, vn1, mp1, mk1, cs1, er1, mg1, sl1, ec1, s7, sd1, op1, s10, s11, s12]    # checks added in 0.3 (S12: 0.3.13, 24 Oct 2026, Infinity GEM SAM v0.9, customs-anchored coal and fuel account; S11: 0.3.13, 24 Oct 2026, Infinity GEM SAM v0.7b, v0.7 without the coal double count; S10: 0.3.13, 24 Oct 2026, Infinity GEM SAM v0.7, coal split from mining; OP1: 0.3.13, 23 Oct 2026, a within-year share of the world oil price reaching domestic prices; EC1: 0.3.13, 23 Oct 2026, an employment cap that settles; SL1: 0.3.13, 23 Oct 2026, slack at the start of short-run years; S7, SD1: 0.3.13, 23 Oct 2026; MG1: 0.3.13, P6, a markup pass-through that depends on the output gap; ER1: 0.3.13, P2(b), incomplete pass-through of the peso to import prices; CS1: 0.3.13, the short-run consumption rule; MK1: 0.3.13; MP1: 0.3.12; VN1: 0.3.12; IR1: 0.3.11; ST1: 0.3.11, sectoral stickiness; EN1, EN2: 0.3.11; HD1, X3: 0.3.11; S5, S6, ML2: 0.3.9; E2, X2: 0.3.9; LG1: 0.3.9; IC1, PS1, S4: 0.3.8; S3, Y6, PK1, SR1, WC1, EX1, VD1: 0.3.7; CR1: 0.3.6; ML1, LP1, SH1: 0.3.5; V4, I5, V5, S2, H2, H3: 0.3.1; W1: 0.3.2; D3: 0.3.3; W2: 0.3.4)


if __name__ == "__main__":
    for fn in (d1, d2, m1, c1, c2, c3, c4, c5, c6, c7, y1, p1, v1, i1, i2, a1, r0, *EXTRA):
        fn()
    run = [r for r in results if r[2] is not None]
    not_run = [r[0] for r in results if r[2] is None]
    n_ok = sum(1 for r in run if r[2])
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    nr = f" ({len(not_run)} not run on this computer: {', '.join(not_run)})" if not_run else ""
    lines = [f"# Infinity GEM validation report, {stamp}", "", f"**{n_ok} of {len(run)} checks passed**{nr}.", "",
             "| Check | Title | Result | Detail |", "|---|---|---|---|"]
    for code, title, ok, detail in results:
        lines.append(f"| {code} | {title} | {'**FAIL**' if ok is False else _label(ok)} | {detail.splitlines()[0] if detail else ''} |")
    out = paths.output_dir() / f"validation_report_{dt.datetime.now():%Y%m%d_%H%M}.md"   # 0.3.2: own folder if read-only; 0.3.7: time added so a second run the same day does not overwrite the first
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n{n_ok}/{len(run)} passed{nr}. Report: {out}")
    sys.exit(0 if n_ok == len(run) else 1)
