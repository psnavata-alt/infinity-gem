# Infinity GEM rigging audit: run of 21 October 2026, 08:33

Folder audited: `<repository root>`  
**Version 0.3.11** (20 October 2026; this development copy i  
Script: `docs/verification/rigging_audit/rigging_audit.py` (what each part does: the script's first lines).

## Summary

| part | what | result |
|---|---|---|
| A | Result numbers written into model code | 109 expected numbers searched among 309 numbers written in the model code: 57 matches, 0 unexplained |
| B | Error handlers | 23 handlers; carry on silently: 6; return a fixed value: 2 |
| C | Plugs, slack and clamps | 18 shocked solutions: largest Walras slack 3.8e-12 of investment; solutions with a binding clamp, a negative quantity or no convergence: 0 |
| D | Test strength | 254 tolerances, 43 of 0.001 or more (each explained); checks that can PASS without testing: 0 |
| E | Solver convergence | 30 places solve the model; without a look at the convergence flag: 0 |
| F | Numbers typed into report text | 230 numbers written inside report or screen text in `app/` and `scenarios/` (each to be read: input, source or label?) |
| G | Fitting and randomness | 7 optimiser/root-finder calls, 9 random draws |
| H | Tamper tests | 7 of 7 deliberate breaks caught; control copy passes: True |

## A. Result numbers written into model code

109 numbers the checks expect (including the 21 frozen R0 results, every element) were searched for among the 309 numbers with 3 or more significant digits written in `infinity_gem/`, `app/` and `scenarios/` (also inside text, and as %, thousands or millions). A match is fine only if the number is an INPUT (declared in the script with its source).

| file | line | text | expected | status |
|---|---|---|---|---|
| infinity_gem/demand.py | 95 | 20.0 | check x1 (checks/run_all_checks.py:1129) | declared input: a round test shock size (world oil price +20%) in the Simulator's presets, the settings comparison and check X1's fixed path; in infinity_gem/demand.py the search bound (-20) of the Frisch fit (added 14 Oct 2026) |
| infinity_gem/psa_cpi.py | 65 | 100.0 | check vn1 (checks/run_all_checks.py:1944) | declared input: a round test input: check VN1's release elasticity e = 100 (large enough for the vintage model to reproduce mobile capital; 0.3.12, 20 Oct 2026); in model and scenario code 100.0 is the percent scale (x / 100.0, 100.0 * x) (added 20 Oct 2026, evening) |
| infinity_gem/stickiness.py | 27 | 10.0 | check h3 (checks/run_all_checks.py:956) | declared input: a round default shock size (10%) in input boxes and test shocks |
| infinity_gem/stochastic.py | 181 | 58.0 | check m2 (checks/run_all_checks.py:1079) | declared input: an assumed exchange rate (₱58 per US$) for converting US$ amounts: check M2's test input and the default of infinity_gem/stochastic.py (scenario scripts pass the observed rate) (added 14 Oct 2026) |
| infinity_gem/stochastic.py | 181 | 28009.93 | check m2 (checks/run_all_checks.py:1079) | declared input: PSA nominal GDP 2025, ₱ bn (PSA National Accounts; used to scale shocks) |
| app/simulator.py | 61 | 238.3 | check a1 (checks/run_all_checks.py:470) | declared input: construction investment cut, ₱ bn (September 2026 infrastructure scenario input; DBM/September 2026) |
| app/simulator.py | 62 | 90.21 | check a1 (checks/run_all_checks.py:473) | declared input: Ayuda cut, ₱ bn (September 2026 scenario input) |
| app/simulator.py | 63 | 20.0 | check x1 (checks/run_all_checks.py:1129) | declared input: a round test shock size (world oil price +20%) in the Simulator's presets, the settings comparison and check X1's fixed path; in infinity_gem/demand.py the search bound (-20) of the Frisch fit (added 14 Oct 2026) |
| app/simulator.py | 295 | 10.0 | check h3 (checks/run_all_checks.py:956) | declared input: a round default shock size (10%) in input boxes and test shocks |
| app/simulator.py | 297 | 10.0 | check h3 (checks/run_all_checks.py:956) | declared input: a round default shock size (10%) in input boxes and test shocks |
| app/simulator.py | 300 | 10.0 | check h3 (checks/run_all_checks.py:956) | declared input: a round default shock size (10%) in input boxes and test shocks |
| app/simulator.py | 61 | 238.3 | check a1 (checks/run_all_checks.py:470) | declared input: construction investment cut, ₱ bn (September 2026 infrastructure scenario input; DBM/September 2026) |
| app/simulator.py | 62 | 90.21 | check a1 (checks/run_all_checks.py:473) | declared input: Ayuda cut, ₱ bn (September 2026 scenario input) |
| app/simulator.py | 64 | 10.0 | check h3 (checks/run_all_checks.py:956) | declared input: a round default shock size (10%) in input boxes and test shocks |
| app/simulator.py | 619 | 238.3 | check a1 (checks/run_all_checks.py:470) | declared input: construction investment cut, ₱ bn (September 2026 infrastructure scenario input; DBM/September 2026) |
| app/simulator.py | 620 | 238.3 | check a1 (checks/run_all_checks.py:470) | declared input: construction investment cut, ₱ bn (September 2026 infrastructure scenario input; DBM/September 2026) |
| app/simulator.py | 622 | 238.3 | check a1 (checks/run_all_checks.py:470) | declared input: construction investment cut, ₱ bn (September 2026 infrastructure scenario input; DBM/September 2026) |
| app/simulator.py | 839 | 10.0 | check h3 (checks/run_all_checks.py:956) | declared input: a round default shock size (10%) in input boxes and test shocks |
| app/simulator.py | 842 | 100.0 | check vn1 (checks/run_all_checks.py:1944) | declared input: a round test input: check VN1's release elasticity e = 100 (large enough for the vintage model to reproduce mobile capital; 0.3.12, 20 Oct 2026); in model and scenario code 100.0 is the percent scale (x / 100.0, 100.0 * x) (added 20 Oct 2026, evening) |
| app/simulator.py | 599 | 10.0 | check h3 (checks/run_all_checks.py:956) | declared input: a round default shock size (10%) in input boxes and test shocks |
| app/simulator.py | 839 | 100.0 | check vn1 (checks/run_all_checks.py:1944) | declared input: a round test input: check VN1's release elasticity e = 100 (large enough for the vintage model to reproduce mobile capital; 0.3.12, 20 Oct 2026); in model and scenario code 100.0 is the percent scale (x / 100.0, 100.0 * x) (added 20 Oct 2026, evening) |
| scenarios/_common.py | 35 | 28009.93 | check m2 (checks/run_all_checks.py:1079) | declared input: PSA nominal GDP 2025, ₱ bn (PSA National Accounts; used to scale shocks) |
| scenarios/ayuda_cut.py | 20 | 90.21 | check a1 (checks/run_all_checks.py:473) | declared input: Ayuda cut, ₱ bn (September 2026 scenario input) |
| scenarios/ayuda_cut.py | 22 | 90.21 | check a1 (checks/run_all_checks.py:473) | declared input: Ayuda cut, ₱ bn (September 2026 scenario input) |
| scenarios/combined_2025_2030.py | 58 | 238.3 | check a1 (checks/run_all_checks.py:470) | declared input: construction investment cut, ₱ bn (September 2026 infrastructure scenario input; DBM/September 2026) |
| scenarios/combined_2025_2030.py | 58 | 90.21 | check a1 (checks/run_all_checks.py:473) | declared input: Ayuda cut, ₱ bn (September 2026 scenario input) |
| scenarios/combined_revised.py | 87 | 90.21 | check a1 (checks/run_all_checks.py:473) | declared input: Ayuda cut, ₱ bn (September 2026 scenario input) |
| scenarios/corruption_efficiency_leakage.py | 58 | 238.3 | check a1 (checks/run_all_checks.py:470) | declared input: construction investment cut, ₱ bn (September 2026 infrastructure scenario input; DBM/September 2026) |
| scenarios/demand_sensitivity.py | 36 | 238.3 | check a1 (checks/run_all_checks.py:470) | declared input: construction investment cut, ₱ bn (September 2026 infrastructure scenario input; DBM/September 2026) |
| scenarios/demand_sensitivity.py | 36 | 238.3 | check a1 (checks/run_all_checks.py:470) | declared input: construction investment cut, ₱ bn (September 2026 infrastructure scenario input; DBM/September 2026) |
| scenarios/elasticity_sensitivity.py | 31 | 238.3 | check a1 (checks/run_all_checks.py:470) | declared input: construction investment cut, ₱ bn (September 2026 infrastructure scenario input; DBM/September 2026) |
| scenarios/elasticity_sensitivity.py | 31 | 238.3 | check a1 (checks/run_all_checks.py:470) | declared input: construction investment cut, ₱ bn (September 2026 infrastructure scenario input; DBM/September 2026) |
| a development script (not in this repository) | 42 | 238.3 | check a1 (checks/run_all_checks.py:470) | declared input: construction investment cut, ₱ bn (September 2026 infrastructure scenario input; DBM/September 2026) |
| a development script (not in this repository) | 53 | 0.0600 | check v1 (checks/run_all_checks.py:437) | reviewed: a coefficient of an earlier VAR estimate used as an INPUT; check V1 re-estimates it from the data with infinity_gem/var.py |
| scenarios/home_consumption_sensitivity.py | 28 | 238.3 | check a1 (checks/run_all_checks.py:470) | declared input: construction investment cut, ₱ bn (September 2026 infrastructure scenario input; DBM/September 2026) |
| scenarios/home_consumption_sensitivity.py | 28 | 238.3 | check a1 (checks/run_all_checks.py:470) | declared input: construction investment cut, ₱ bn (September 2026 infrastructure scenario input; DBM/September 2026) |
| scenarios/infrastructure_catchup.py | 33 | 238.3 | check a1 (checks/run_all_checks.py:470) | declared input: construction investment cut, ₱ bn (September 2026 infrastructure scenario input; DBM/September 2026) |
| scenarios/infrastructure_freeze.py | 29 | 238.3 | check a1 (checks/run_all_checks.py:470) | declared input: construction investment cut, ₱ bn (September 2026 infrastructure scenario input; DBM/September 2026) |
| scenarios/infrastructure_freeze.py | 32 | 238.3 | check a1 (checks/run_all_checks.py:470) | declared input: construction investment cut, ₱ bn (September 2026 infrastructure scenario input; DBM/September 2026) |
| scenarios/infrastructure_full_dynamic.py | 71 | 238.3 | check a1 (checks/run_all_checks.py:470) | declared input: construction investment cut, ₱ bn (September 2026 infrastructure scenario input; DBM/September 2026) |
| scenarios/infrastructure_full_dynamic.py | 25 | 238.3 | check a1 (checks/run_all_checks.py:470) | declared input: construction investment cut, ₱ bn (September 2026 infrastructure scenario input; DBM/September 2026) |
| scenarios/infrastructure_public_capital.py | 33 | 238.3 | check a1 (checks/run_all_checks.py:470) | declared input: construction investment cut, ₱ bn (September 2026 infrastructure scenario input; DBM/September 2026) |
| scenarios/labour_hoarding_alternatives.py | 57 | 100.0 | check vn1 (checks/run_all_checks.py:1944) | declared input: a round test input: check VN1's release elasticity e = 100 (large enough for the vintage model to reproduce mobile capital; 0.3.12, 20 Oct 2026); in model and scenario code 100.0 is the percent scale (x / 100.0, 100.0 * x) (added 20 Oct 2026, evening) |
| scenarios/public_works_multiplier_sticky_construction.py | 38 | 28_009.93 | check m2 (checks/run_all_checks.py:1079) | declared input: PSA nominal GDP 2025, ₱ bn (PSA National Accounts; used to scale shocks) |
| scenarios/qpm_cge_link.py | 141 | 100.0 | check vn1 (checks/run_all_checks.py:1944) | declared input: a round test input: check VN1's release elasticity e = 100 (large enough for the vintage model to reproduce mobile capital; 0.3.12, 20 Oct 2026); in model and scenario code 100.0 is the percent scale (x / 100.0, 100.0 * x) (added 20 Oct 2026, evening) |
| scenarios/qpm_cge_link.py | 71 | 100.0 | check vn1 (checks/run_all_checks.py:1944) | declared input: a round test input: check VN1's release elasticity e = 100 (large enough for the vintage model to reproduce mobile capital; 0.3.12, 20 Oct 2026); in model and scenario code 100.0 is the percent scale (x / 100.0, 100.0 * x) (added 20 Oct 2026, evening) |
| scenarios/qpm_cge_link.py | 105 | 100.0 | check vn1 (checks/run_all_checks.py:1944) | declared input: a round test input: check VN1's release elasticity e = 100 (large enough for the vintage model to reproduce mobile capital; 0.3.12, 20 Oct 2026); in model and scenario code 100.0 is the percent scale (x / 100.0, 100.0 * x) (added 20 Oct 2026, evening) |
| scenarios/qpm_cge_link.py | 68 | 100.0 | check vn1 (checks/run_all_checks.py:1944) | declared input: a round test input: check VN1's release elasticity e = 100 (large enough for the vintage model to reproduce mobile capital; 0.3.12, 20 Oct 2026); in model and scenario code 100.0 is the percent scale (x / 100.0, 100.0 * x) (added 20 Oct 2026, evening) |
| scenarios/qpm_cge_link.py | 103 | 100.0 | check vn1 (checks/run_all_checks.py:1944) | declared input: a round test input: check VN1's release elasticity e = 100 (large enough for the vintage model to reproduce mobile capital; 0.3.12, 20 Oct 2026); in model and scenario code 100.0 is the percent scale (x / 100.0, 100.0 * x) (added 20 Oct 2026, evening) |
| scenarios/settings_comparison.py | 21 | 238.3 | check a1 (checks/run_all_checks.py:470) | declared input: construction investment cut, ₱ bn (September 2026 infrastructure scenario input; DBM/September 2026) |
| scenarios/settings_comparison.py | 23 | 90.21 | check a1 (checks/run_all_checks.py:473) | declared input: Ayuda cut, ₱ bn (September 2026 scenario input) |
| scenarios/settings_comparison.py | 22 | 20.0 | check x1 (checks/run_all_checks.py:1129) | declared input: a round test shock size (world oil price +20%) in the Simulator's presets, the settings comparison and check X1's fixed path; in infinity_gem/demand.py the search bound (-20) of the Frisch fit (added 14 Oct 2026) |
| scenarios/settings_comparison.py | 21 | 238.3 | check a1 (checks/run_all_checks.py:470) | declared input: construction investment cut, ₱ bn (September 2026 infrastructure scenario input; DBM/September 2026) |
| scenarios/settings_comparison.py | 23 | 90.21 | check a1 (checks/run_all_checks.py:473) | declared input: Ayuda cut, ₱ bn (September 2026 scenario input) |
| scenarios/settings_comparison.py | 24 | 10.0 | check h3 (checks/run_all_checks.py:956) | declared input: a round default shock size (10%) in input boxes and test shocks |
| scenarios/settings_comparison.py | 43 | 238.3 | check a1 (checks/run_all_checks.py:470) | declared input: construction investment cut, ₱ bn (September 2026 infrastructure scenario input; DBM/September 2026) |
| scenarios/settings_comparison.py | 43 | 238.3 | check a1 (checks/run_all_checks.py:470) | declared input: construction investment cut, ₱ bn (September 2026 infrastructure scenario input; DBM/September 2026) |

## B. Error handlers

Every `except` in the model code and what it does when something goes wrong.

| file | line | function | catches | does |
|---|---|---|---|---|
| infinity_gem/dynamic.py | 363 | _robust_root | _SolveFailed | CARRIES ON SILENTLY (pass/continue) |
| infinity_gem/dynamic.py | 1111 | monetary_scenario | RuntimeError | re-raises or raises a clearer error |
| infinity_gem/dynamic.py | 797 | _run | _SolveFailed | other: tf = _robust_root(gap, tfps[prev_t], xtol=1e-10) |
| infinity_gem/household.py | 86 | psic_to_psa16 | ValueError | RETURNS A FIXED VALUE (-1) |
| infinity_gem/macrolink.py | 94 | consistency | (KeyError, TypeError) | CARRIES ON SILENTLY (pass/continue) |
| infinity_gem/monetary.py | 80 | <module> | (FileNotFoundError, ValueError) | other: print(n, '->', e) |
| infinity_gem/paths.py | 80 | can_write | OSError | returns None/False |
| infinity_gem/paths.py | 102 | <module> | OSError | CARRIES ON SILENTLY (pass/continue) |
| infinity_gem/var.py | 115 | irf_table | Exception | CARRIES ON SILENTLY (pass/continue) |
| app/engines.py | 495 | run_dynamic | RuntimeError | reports a failure (ok=False) |
| app/engines.py | 21 | <module> | warnings | warnings switched off |
| app/simulator.py | 33 | _brand | Exception | returns None/False |
| scenarios/_common.py | 117 | save | OSError | CARRIES ON SILENTLY (pass/continue) |
| scenarios/_common.py | 13 | <module> | warnings | warnings switched off |
| scenarios/combined_revised.py | 270 | measures | ValueError | CARRIES ON SILENTLY (pass/continue) |
| a development script (not in this repository) | 20 | <module> | warnings | warnings switched off |
| scenarios/interest_closure_check.py | 27 | rint | (KeyError, TypeError) | other: return np.nan |
| scenarios/lhs_2026_ranges.py | 159 | main | Exception | other: res = {k: np.nan for k in KEYS} \| {'error': repr(e)[:200]} |
| scenarios/monetary_check.py | 207 | main | RuntimeError | other: failed[lab] = str(e).splitlines()[0][:200] |
| scenarios/monetary_check.py | 229 | main | RuntimeError | other: failed[lab] = str(e).splitlines()[0][:200] |
| scenarios/qpm_cge_link.py | 182 | g | RuntimeError | RETURNS A FIXED VALUE (-1000.0) |
| scenarios/stochastic_outlook.py | 95 | <module> | Exception | other: rep.p(f'(Fan chart not drawn: {e!r})') |
| scenarios/stochastic_outlook.py | 15 | <module> | warnings | warnings switched off |

## C. Plugs, slack terms and clamps

**Names in `infinity_gem/` that suggest a plug** (each is explained in the written report):

| file | line | name |
|---|---|---|
| infinity_gem/cge.py | 75 | residual_max |
| infinity_gem/cge.py | 501 | WALRAS |
| infinity_gem/cge.py | 609 | slack |
| infinity_gem/dynamic.py | 409 | missing |
| infinity_gem/dynamic.py | 460 | residual_max |
| infinity_gem/household.py | 221 | _lfs_adjustment |
| infinity_gem/iomodel.py | 188 | missing |
| infinity_gem/macrolink.py | 50 | residual_max |
| infinity_gem/microlink.py | 257 | _lfs_adjustment |
| infinity_gem/psa_cpi.py | 56 | missing |
| infinity_gem/sam.py | 203 | balance |

**Shocked solutions.** The only slack variable is WALRAS (savings minus investment); it must be zero. `_pos()` keeps prices above 1e-12 and `np.clip` keeps saving rates within -1..1: a clamp that binds would mean the solution is not a real equilibrium.

| closure | shock | solved | residual | walras | gdp_gap | min_price | clamp_price | clamp_mps | negative_qty | real_gdp_pct |
|---|---|---|---|---|---|---|---|---|---|---|
| long run | construction -10% | True | 3.8e-14 | 3.5e-12 | 1.1e-11 | 9.9e-01 | False | False | False | +0.076 |
| long run | world chemical/petroleum prices +30% | True | 5.5e-15 | 3.4e-12 | 3.6e-12 | 9.5e-01 | False | False | False | -0.622 |
| long run | remittances -20% | True | 1.5e-15 | 3.4e-12 | 3.6e-12 | 9.6e-01 | False | False | False | -0.060 |
| long run | tariffs abolished | True | 9.0e-16 | 3.7e-12 | 3.6e-12 | 4.8e-01 | False | False | False | +2.797 |
| long run | mixed (check C4) | True | 5.3e-15 | 3.4e-12 | 3.6e-12 | 9.4e-01 | False | False | False | -0.541 |
| long run | capital stock +5%, productivity +2% | True | 4.9e-15 | 3.7e-12 | 3.6e-12 | 9.9e-01 | False | False | False | +5.324 |
| savings | construction -10% | True | 1.1e-15 | 3.5e-12 | 0.0e+00 | 9.9e-01 | False | False | False | +0.040 |
| savings | world chemical/petroleum prices +30% | True | 3.4e-15 | 3.4e-12 | 0.0e+00 | 9.5e-01 | False | False | False | -0.612 |
| savings | remittances -20% | True | 1.2e-15 | 3.4e-12 | 7.3e-12 | 9.7e-01 | False | False | False | -0.054 |
| savings | tariffs abolished | True | 2.1e-15 | 3.8e-12 | 3.6e-12 | 4.8e-01 | False | False | False | +2.973 |
| savings | mixed (check C4) | True | 6.1e-14 | 3.3e-12 | 6.9e-11 | 9.4e-01 | False | False | False | -0.580 |
| savings | capital stock +5%, productivity +2% | True | 8.8e-15 | 3.6e-12 | 0.0e+00 | 9.9e-01 | False | False | False | +5.280 |
| short run | construction -10% | True | 9.7e-14 | 3.4e-12 | 7.3e-11 | 7.5e-01 | False | False | False | -0.483 |
| short run | world chemical/petroleum prices +30% | True | 1.7e-14 | 3.5e-12 | 2.2e-11 | 8.6e-01 | False | False | False | -0.550 |
| short run | remittances -20% | True | 3.0e-15 | 3.4e-12 | 3.6e-12 | 9.7e-01 | False | False | False | -0.147 |
| short run | tariffs abolished | True | 8.7e-13 | 3.0e-12 | 4.1e-10 | 4.4e-01 | False | False | False | +3.176 |
| short run | mixed (check C4) | True | 7.2e-14 | 3.2e-12 | 1.8e-10 | 5.5e-01 | False | False | False | -1.755 |
| short run | capital stock +5%, productivity +2% | True | 8.0e-15 | 3.5e-12 | 7.3e-12 | 9.5e-01 | False | False | False | +1.946 |

**Data treatments that could act as plugs:**

- Re-exports (exports above domestic output, treated as imports re-exported at fixed quantities): ₱345.1 bn, goods ['cmach'].
- Balancing of the 2018 SAM (published in whole billions): largest cell change ₱1.94 bn; total change ₱57.2 bn (the SAM's total is ₱148,751 bn). The 2023 SAM is used as published.
- FIES households dropped for missing values: 0; households in no SAM group (would get no change): 0.

## D. Test strength

**Checks that return PASS without testing** (a skipped test must not count as passed):

_none_

**Tolerances of 0.001 or more** (smaller ones are listed below):

| check | line | tolerance | test |
|---|---|---|---|
| D2 | 255 | 6.0 | out[0][1] |
| P1 | 428 | 0.001 | abs(b['poor'] / OFFICIAL_POOR_2023 - 1) |
| I1 | 450 | 0.05 | abs(va + 161.5) |
| I2 | 462 | 0.005 | abs(c / -254226 - 1) |
| I2 | 462 | 0.005 | abs(t / -320934 - 1) |
| A1 | 475 | 0.001 | abs(E.sam_gdp(E.sam_model(2023).sam) - E.SAM_GDP_2023) |
| A1 | 476 | 1.0 | abs(sr['New poor (persons, FIES 2023 base)'] - 497479) |
| A1 | 477 | 0.01 | abs(to_sam(sm['GDP (value added, ₱ bn)']) + 350.223) |
| A1 | 477 | 0.01 | abs(to_sam(ay['Household income (₱ bn)']) + 185.06) |
| I4 | 510 | 1.0 | io.v |
| Y3 | 600 | 0.1 | abs(x2 / x1 - 2) |
| V2 | 618 | 0.01 | m_core |
| V2 | 618 | 0.6 | m_all |
| V2 | 617 | 0.1 | r.diff_pp.abs() |
| V3 | 643 | 0.001 | m_core |
| V3 | 643 | 0.15 | m_all |
| V3 | 642 | 0.1 | r.diff_pp.abs() |
| Y4 | 696 | 9.0 | 5 <= g24 <= 9 |
| Y5 | 721 | 0.2 | gmiss |
| Y5 | 721 | 15.0 | tfpmax |
| Y5 | 721 | 1.25 | max(lev) |
| V4 | 846 | 0.1 | a |
| H2 | 931 | 0.01 | pov_gap |
| H2 | 931 | 0.01 | abs(monthly - 225.11) |
| H2 | 931 | 0.05 | abs(nat - 155.5) |
| H2 | 928 | 2.0 | abs(x - y) |
| H3 | 959 | 0.02 | abs(tot / psa - 1) |
| H3 | 959 | 0.001 | grp_gap |
| X1 | 1151 | 0.15 | zd |
| X1 | 1151 | 2.0 | 0.5 < ro < 2 |
| X1 | 1151 | 2.0 | 0.5 < rr < 2 |
| ML1 | 1191 | 1.0 | abs(pov - 1995889) |
| ML1 | 1191 | 0.01 | abs(pov - ms) |
| ML1 | 1192 | 0.02 | abs(fam_cpi - sam_cpi) |
| LP1 | 1218 | 0.05 | gap |
| PS1 | 1566 | 0.01 | abs(rise_s / rise_f - 1) |
| EN1 | 1834 | 0.005 | abs(uL - u0) |
| ST1 | 1886 | 0.001 | abs(rule - 0.5823) |
| ST1 | 1886 | 0.7 | 0.5 < wmean < 0.7 |
| VN1 | 1956 | 0.002 | lim_m |
| VN1 | 1957 | 5.0 | disp |
| MP1 | 1992 | 15.0 | r.monetary.attrs['iterations'] |
| X2 | 2046 | 5.0 | 3.0 < e1 / e2 < 5.0 |

<details><summary>All tolerances</summary>

| check | line | tolerance | test |
|---|---|---|---|
| D2 | 255 | 6.0 | out[0][1] |
| M1 | 309 | 0.0005 | abs(vals[y][i] - exp[y][i]) |
| C1 | 338 | 1e-07 | r |
| C2 | 346 | 1e-05 | gap |
| C3 | 358 | 1e-07 | a |
| C3 | 358 | 1e-07 | b |
| C4 | 370 | 1e-09 | w |
| C5 | 379 | 1e-06 | x |
| C6 | 391 | 0.0 | d |
| C6 | 395 | 0.0 | d |
| C6 | 389 | 0.0 | d1 |
| C6 | 389 | 0.0 | d2 |
| Y1 | 421 | 1e-06 | np.abs(got - target).max() |
| Y1 | 421 | 1e-06 | gap |
| P1 | 428 | 0.001 | abs(b['poor'] / OFFICIAL_POOR_2023 - 1) |
| V1 | 437 | 5e-05 | abs(fx - 0.0078) |
| V1 | 437 | 5e-05 | abs(fdi + 0.06) |
| I1 | 450 | 1e-06 | gap |
| I1 | 450 | 0.0005 | abs(ps['cpi'] * 100 - 0.6832) |
| I1 | 450 | 0.0005 | abs(ps['ppi'] * 100 - 0.8051) |
| I1 | 450 | 0.05 | abs(va + 161.5) |
| I2 | 462 | 0.005 | abs(c / -254226 - 1) |
| I2 | 462 | 0.005 | abs(t / -320934 - 1) |
| A1 | 475 | 0.001 | abs(E.sam_gdp(E.sam_model(2023).sam) - E.SAM_GDP_2023) |
| A1 | 476 | 0.0005 | abs(sr['Real GDP (%)'] + 0.279) |
| A1 | 476 | 1.0 | abs(sr['New poor (persons, FIES 2023 base)'] - 497479) |
| A1 | 477 | 0.01 | abs(to_sam(sm['GDP (value added, ₱ bn)']) + 350.223) |
| A1 | 477 | 0.01 | abs(to_sam(ay['Household income (₱ bn)']) + 185.06) |
| I3 | 500 | 1e-07 | gap |
| I4 | 512 | 1e-07 | g1 |
| I4 | 512 | 1e-07 | g2 |
| I4 | 510 | 1.0 | io.v |
| I5 | 535 | 1e-06 | g_psa |
| I5 | 535 | 1e-07 | g_tot |
| I5 | 535 | 1e-07 | g_dom |
| I5 | 535 | 1e-09 | g_gdp |
| I5 | 535 | 1e-06 | g_emp |
| C8 | 557 | 1e-07 | r1 |
| C8 | 557 | 1e-05 | r2 |
| C8 | 557 | 1e-07 | r3 |
| C8 | 557 | 1e-09 | r4 |
| C8 | 557 | 1e-06 | r5 |
| Y2 | 578 | 1e-06 | zgap |
| Y2 | 578 | 0.0 | g.loc[2025] |
| Y2 | 578 | 1e-06 | decay |
| Y2 | 578 | 0.0 | cum_h < cum_l < 0 |
| Y3 | 600 | 1e-09 | same |
| Y3 | 600 | 1e-06 | zgap |
| Y3 | 600 | 0.0 | x1 |
| Y3 | 600 | 0.1 | abs(x2 / x1 - 2) |
| V2 | 618 | 0.01 | m_core |
| V2 | 618 | 0.6 | m_all |
| V2 | 617 | 0.1 | r.diff_pp.abs() |
| V3 | 643 | 1e-06 | gap |
| V3 | 643 | 1e-07 | hom |
| V3 | 643 | 0.001 | m_core |
| V3 | 643 | 0.15 | m_all |
| V3 | 642 | 0.1 | r.diff_pp.abs() |
| E1 | 662 | 1e-07 | r1 |
| E1 | 662 | 1e-07 | r3 |
| Y4 | 696 | 1e-06 | miss |
| Y4 | 696 | 1e-06 | zgap |
| Y4 | 696 | 9.0 | 5 <= g24 <= 9 |
| Y4 | 696 | 0.0 | kgap |
| Y4 | 685 | 1e-12 | abs(x.sum() - 1) |
| Y5 | 721 | 1e-06 | miss |
| Y5 | 721 | 0.2 | gmiss |
| Y5 | 721 | 1e-09 | zgap |
| Y5 | 721 | 15.0 | tfpmax |
| Y5 | 721 | 1.25 | max(lev) |
| L1 | 748 | 1e-12 | miss |
| L1 | 748 | 1e-12 | pmiss |
| L1 | 748 | 1e-08 | smiss |
| H1 | 784 | 1e-06 | gu |
| H1 | 790 | 1e-06 | gg |
| H1 | 769 | 1e-06 | gap |
| H1 | 769 | 1e-08 | hom |
| H1 | 769 | 1e-12 | engel |
| S1 | 819 | 1e-06 | rebuild |
| S1 | 819 | 1e-09 | other |
| S1 | 819 | 1e-06 | gap |
| S1 | 819 | 1e-08 | hom |
| V4 | 840 | 1e-06 | gap |
| V4 | 840 | 1e-07 | hom |
| V4 | 840 | 1e-06 | gid |
| V4 | 840 | 1e-06 | abs(float(b['QHA'].sum()) - float(m.HC.sum())) |
| V4 | 846 | 0.1 | a |
| V5 | 865 | 1e-09 | samgap |
| V5 | 865 | 1e-09 | lev |
| V5 | 865 | 1e-08 | pct |
| V5 | 865 | 1e-05 | near |
| S2 | 897 | 1e-06 | miss |
| S2 | 897 | 1e-06 | zgap |
| S2 | 891 | 1e-05 | gap |
| S2 | 891 | 1e-07 | hom |
| S2 | 891 | 1e-09 | wal |
| S2 | 891 | 1e-06 | gid |
| H2 | 931 | 1e-06 | dec_gap |
| H2 | 931 | 0.01 | pov_gap |
| H2 | 931 | 1e-06 | ns |
| H2 | 931 | 0.01 | abs(monthly - 225.11) |
| H2 | 931 | 0.05 | abs(nat - 155.5) |
| H2 | 928 | 2.0 | abs(x - y) |
| H3 | 959 | 1e-06 | alloc |
| H3 | 959 | 0.02 | abs(tot / psa - 1) |
| H3 | 959 | 0.001 | grp_gap |
| H3 | 951 | 0.0 | emp['ind'] |
| A2 | 987 | 1e-09 | abs(a - b) |
| A2 | 987 | 0.0 | c['summary']['Cumulative GDP vs baseline, 2024-2030 (₱ bn)'] |
| A2 | 980 | 1e-06 | abs(r['walras']) |
| V6 | 1037 | 1e-08 | r['gaps']['Effect'] |
| V6 | 1037 | 1e-06 | worst |
| V7 | 1067 | 1e-12 | g_sm |
| V7 | 1067 | 1e-10 | g_hd |
| V7 | 1067 | 1e-12 | g_cf |
| V7 | 1067 | 1e-08 | g_bv |
| M2 | 1088 | 1e-12 | abs(sp['fsav_scale'] - want) |
| W2 | 1113 | 1e-09 | same |
| W2 | 1113 | 1e-07 | float(np.abs(R).max()) |
| W2 | 1113 | 1e-07 | dq |
| W2 | 1113 | 1e-07 | dp |
| W2 | 1113 | 0.0 | emp |
| X1 | 1151 | 1e-09 | zb |
| X1 | 1151 | 0.15 | zd |
| X1 | 1151 | 2.0 | 0.5 < ro < 2 |
| X1 | 1151 | 2.0 | 0.5 < rr < 2 |
| ML1 | 1191 | 1e-09 | cover |
| ML1 | 1191 | 1e-09 | cat10 |
| ML1 | 1191 | 1e-09 | fam10 |
| ML1 | 1191 | 1.0 | abs(pov - 1995889) |
| ML1 | 1191 | 0.01 | abs(pov - ms) |
| ML1 | 1192 | 0.02 | abs(fam_cpi - sam_cpi) |
| ML1 | 1192 | 1e-09 | rt |
| LP1 | 1218 | 0.05 | gap |
| LP1 | 1218 | 1e-12 | same |
| SH1 | 1233 | 1e-12 | lin_gap |
| SH1 | 1233 | 1e-12 | add |
| SH1 | 1233 | 1e-12 | sym |
| SH1 | 1233 | 1e-12 | null |
| CR1 | 1301 | 1e-09 | eff |
| CR1 | 1301 | 1e-08 | moved |
| CR1 | 1301 | 1e-12 | kgap |
| CR1 | 1302 | 1e-06 | zero_w |
| CR1 | 1302 | 1e-09 | k_err |
| CR1 | 1302 | 1e-12 | k_leak |
| CR1 | 1303 | 1e-09 | a_err |
| CR1 | 1303 | 1e-09 | cut_same |
| CR1 | 1302 | 1e-08 | m_ |
| S3 | 1325 | 1e-09 | abs(summary['imports, milled rice and corn (₱ bn)'] - psa) |
| S3 | 1325 | 1e-09 | abs(summary['import duty, milled rice and corn (₱ bn)'] - bsr.RICE_DUTY_2023) |
| S3 | 1325 | 1e-09 | abs(summary['imports, maize (₱ bn)'] - bsr.psa_maize_imports_2023()) |
| S3 | 1338 | 1e-06 | rebuild |
| S3 | 1338 | 1e-08 | same |
| S3 | 1338 | 0.0 | dq |
| Y6 | 1366 | 1e-06 | zgap |
| Y6 | 1366 | 1e-08 | over |
| PK1 | 1387 | 1e-09 | kdev |
| PK1 | 1387 | 1e-12 | same |
| PK1 | 1387 | 0.0 | g_old < g_once < 0 |
| PK1 | 1387 | 1e-06 | abs(g0) |
| WC1 | 1439 | 0.0 | e0 < e1 < 0 |
| WC1 | 1439 | 1e-06 | z1 |
| WC1 | 1439 | 1e-08 | fp |
| WC1 | 1439 | 1e-12 | same |
| EX1 | 1466 | 1e-12 | same |
| EX1 | 1466 | 1e-10 | abs(r - 1.02) |
| VD1 | 1492 | 1e-10 | exact |
| VD1 | 1492 | 1e-10 | same |
| VD1 | 1492 | 1e-12 | carry |
| IC1 | 1535 | 1e-09 | zsv |
| IC1 | 1535 | 1e-09 | zfx |
| IC1 | 1535 | 0.0 | inv30 |
| IC1 | 1535 | 1e-09 | fs |
| IC1 | 1535 | 1e-12 | same |
| PS1 | 1565 | 1e-09 | bench.residual_max |
| PS1 | 1565 | 1e-09 | same0 |
| PS1 | 1566 | 0.01 | abs(rise_s / rise_f - 1) |
| PS1 | 1566 | 1e-06 | walras |
| PS1 | 1566 | 1e-09 | zd |
| S4 | 1588 | 1e-06 | same |
| S4 | 1588 | 1e-06 | diag['max row-column gap'] |
| S4 | 1588 | 1e-06 | gap |
| S4 | 1588 | 1e-08 | b.residual_max |
| S5 | 1629 | 1e-06 | same |
| S5 | 1629 | 1e-06 | diag['max row-column gap'] |
| S5 | 1629 | 1e-06 | hfce |
| S5 | 1629 | 1e-06 | kept |
| S5 | 1629 | 1e-06 | cut |
| S5 | 1630 | 1e-06 | gap |
| S5 | 1630 | 1e-08 | b.residual_max |
| S5 | 1630 | 1e-05 | rep |
| S5 | 1627 | 1e-06 | sy |
| S5 | 1627 | 1e-06 | dy['max row-column gap'] |
| S5 | 1627 | 1e-06 | gy |
| S5 | 1627 | 1e-08 | by.residual_max |
| S6 | 1674 | 1e-06 | same |
| S6 | 1674 | 1e-06 | diag['max row-column gap'] |
| S6 | 1674 | 1e-06 | macro |
| S6 | 1674 | 1e-06 | va |
| S6 | 1674 | 1e-06 | lab |
| S6 | 1674 | 1e-09 | grp |
| S6 | 1674 | 1e-06 | purpose |
| S6 | 1675 | 1e-08 | b.residual_max |
| S6 | 1675 | 1e-05 | rep |
| S6 | 1675 | 0.0 | -3 < dg < 0 |
| ML2 | 1702 | 1e-09 | cover |
| ML2 | 1702 | 1e-09 | cat10 |
| ML2 | 1702 | 1e-09 | fam10 |
| PC1 | 1722 | 1e-09 | zero |
| PC1 | 1722 | 1e-09 | ten |
| PC1 | 1722 | 1e-06 | abs(s - 100) |
| HD1 | 1791 | 1e-10 | same |
| HD1 | 1791 | 1e-09 | imb |
| HD1 | 1791 | 1e-08 | idn |
| HD1 | 1791 | 1e-09 | abs(sh['WALRAS']) / mh.qinv.sum() |
| EN1 | 1833 | 1e-09 | hom |
| EN1 | 1834 | 0.005 | abs(uL - u0) |
| EN1 | 1834 | 1e-09 | imb |
| EN1 | 1834 | 1e-09 | rc |
| EN1 | 1834 | 1e-12 | rb |
| EN2 | 1855 | 1e-09 | g |
| ST1 | 1886 | 1e-12 | same |
| ST1 | 1886 | 0.001 | abs(rule - 0.5823) |
| ST1 | 1886 | 0.7 | 0.5 < wmean < 0.7 |
| ST1 | 1887 | 1e-09 | zd |
| IR1 | 1918 | 1e-08 | bench |
| IR1 | 1918 | 1e-08 | lim_s |
| IR1 | 1918 | 1e-08 | lim_i |
| IR1 | 1919 | 0.0 | float(s_r['RINT']) |
| IR1 | 1919 | 1e-09 | zd |
| VN1 | 1956 | 1e-08 | bench |
| VN1 | 1956 | 1e-09 | cons |
| VN1 | 1956 | 1e-05 | lim_f |
| VN1 | 1956 | 0.002 | lim_m |
| VN1 | 1957 | 1e-06 | abs(grow) |
| VN1 | 1957 | 1e-08 | comp |
| VN1 | 1957 | 5.0 | disp |
| VN1 | 1957 | 1e-09 | zd |
| MP1 | 1992 | 15.0 | r.monetary.attrs['iterations'] |
| MP1 | 1993 | 1e-09 | zr |
| MP1 | 1993 | 1e-09 | zd |
| MP1 | 1993 | 1e-10 | lim_h |
| MP1 | 1993 | 1e-10 | lim_r |
| MP1 | 1993 | 0.0 | pi26 |
| MP1 | 1993 | 0.0 | i26 |
| LG1 | 2013 | 1e-12 | abs(tot - rule) |
| E2 | 2029 | 1e-07 | r |
| X2 | 2074 | 1e-06 | worst |
| X2 | 2046 | 1e-10 | e_bm |
| X2 | 2046 | 0.0001 | e2 |
| X2 | 2046 | 5.0 | 3.0 < e1 / e2 < 5.0 |
| X2 | 2087 | 1e-06 | gk_gap |
| X2 | 2057 | 1e-08 | dev |
| X2 | 2057 | 1e-10 | drift |

</details>

## E. Solver convergence

Each function or script that calls `.solve()` and whether it looks at the result's convergence flag (`ok`) or residual. The dynamic model's `baseline()`/`scenario()` stop with an error by themselves if a year does not solve.

| file | line | function | solves | checks_flag |
|---|---|---|---|---|
| infinity_gem/dynamic.py | 458 | __init__ | 1 | True |
| infinity_gem/dynamic.py | 647 | _cap_employment | 1 | True |
| infinity_gem/dynamic.py | 821 | _run | 7 | True |
| infinity_gem/dynamic.py | 558 | resid | 1 | True |
| infinity_gem/dynamic.py | 600 | resid | 1 | True |
| infinity_gem/dynamic.py | 791 | gap | 1 | True |
| infinity_gem/dynamic.py | 803 | gap | 1 | True |
| infinity_gem/macrolink.py | 48 | sam_gdp | 1 | True |
| app/engines.py | 233 | run_cge | 2 | True |
| scenarios/ayuda_cut.py | 37 | <script body> | 2 | True |
| scenarios/benchmark_cororaton_2018sam.py | 23 | <script body> | 2 | True |
| scenarios/combined_2025_2030.py | 102 | static_land_cuts | 1 | True |
| scenarios/combined_revised.py | 146 | land_cuts | 1 | True |
| scenarios/demand_sensitivity.py | 31 | <script body> | 2 | True |
| scenarios/elasticity_sensitivity.py | 28 | <script body> | 2 | True |
| scenarios/fertilizer_2026_measured.py | 34 | main | 2 | True |
| a development script (not in this repository) | 122 | <script body> | 2 | True |
| scenarios/home_consumption_sensitivity.py | 25 | <script body> | 2 | True |
| scenarios/infrastructure_catchup.py | 49 | <script body> | 2 | True |
| scenarios/infrastructure_freeze.py | 48 | <script body> | 2 | True |
| scenarios/micro_link_export.py | 31 | run | 2 | True |
| scenarios/oil_2026_measured.py | 39 | main | 2 | True |
| scenarios/oil_passthrough_by_sam.py | 80 | run | 2 | True |
| scenarios/oil_petroleum_split.py | 31 | <script body> | 5 | True |
| scenarios/oil_price_shock.py | 28 | <script body> | 2 | True |
| scenarios/sam_psa_sensitivity.py | 72 | run | 1 | True |
| scenarios/sam_year_sensitivity.py | 34 | main | 1 | True |
| scenarios/own_sam_cpi_decomposition.py | 44 | run | 1 | True |
| scenarios/own_sam_wage_curve_diagnostic.py | 59 | run | 1 | True |
| scenarios/shapley_five_shocks.py | 32 | main | 2 | True |

## F. Numbers typed into report text

Numbers written inside text in `app/` and `scenarios/` (computed numbers enter text through `{...}` and do not appear here). Each should be an input, a source or a label, not a result.

| file | line | number | context |
|---|---|---|---|
| app/engines.py | 46 | 1.1 | der '0.3 recommended' (PSA data: about ₱1.1 of GDP per peso of public cons |
| app/engines.py | 516 | 1.5% | om 2026, depreciation 5%, labour growth 1.5% (infinity_gem/dynamic.py). No pub |
| app/engines.py | 523 | 0.083 | low end (phi 0.083, public capital 0.397 x GDP). |
| app/engines.py | 523 | 0.397 | low end (phi 0.083, public capital 0.397 x GDP). |
| app/engines.py | 524 | 0.122 | high end (phi 0.122, public capital 0.296 x GDP). |
| app/engines.py | 524 | 0.296 | high end (phi 0.122, public capital 0.296 x GDP). |
| app/simulator.py | 61 | 238.3 bn | Infrastructure freeze, H2 2025 (−₱238.3 bn construction; DBM |
| app/simulator.py | 62 | 90.21 bn | yuda cut, FY 2027 NEP vs FY 2026 GAA (−₱90.21 bn to the bottom 40%; DBM D.3) |
| app/simulator.py | 377 | 0.8 | Defaults (0.8, 2.0, 2.0) are common in the  |
| app/simulator.py | 377 | 2.0 | Defaults (0.8, 2.0, 2.0) are common in the literature |
| app/simulator.py | 537 | −1.8% | truction freeze costs low-skill jobs of −1.8% with CPI-indexed pay and −2.7 |
| app/simulator.py | 537 | −2.7% |  jobs of −1.8% with CPI-indexed pay and −2.7% with pay fixed in pesos; a 20 |
| app/simulator.py | 537 | −1.1% | ay fixed in pesos; a 20% oil-price rise −1.1% and −0.3% (validation/labour_ |
| app/simulator.py | 537 | −0.3% | n pesos; a 20% oil-price rise −1.1% and −0.3% (validation/labour_closures/R |
| app/simulator.py | 354 | 0.6 | modity's import price times this share. 0.6 is an assumption, to be replac |
| app/simulator.py | 619 | 238.3 bn | Preset: freeze in 2025 (−₱238.3 bn) |
| app/simulator.py | 621 | 208.7 bn | et: freeze in 2025, catch-up in 2027 (+₱208.7 bn) |
| app/simulator.py | 653 | 0.5 | 0.5: half the gap is left after o |
| app/simulator.py | 825 | 1.9 | ffect**, and its size is an assumption (1.9-3.3% of real investment per p |
| app/simulator.py | 825 | 3.3% | t**, and its size is an assumption (1.9-3.3% of real investment per point  |
| app/simulator.py | 724 | 0.4% | 00 bp held for a year costs 2026 output 0.4% (PAMPh-type model) to 0.9% (S |
| app/simulator.py | 724 | 0.9% |  2026 output 0.4% (PAMPh-type model) to 0.9% (the project's DSGE). |
| app/simulator.py | 735 | 0.85 |  moves with the real rate gap, hoarding 0.85, Infinity GEM's own SAM): |
| app/simulator.py | 776 | 0.55 | s; columns are the investment response (0.55, 2, 3.3) and the channel (bot |
| app/simulator.py | 776 | 3.3 | s are the investment response (0.55, 2, 3.3) and the channel (both, inves |
| app/simulator.py | 662 | 0.083 | φ 0.083, public capital 0.397 × GDP |
| app/simulator.py | 662 | 0.397 | φ 0.083, public capital 0.397 × GDP |
| app/simulator.py | 662 | 0.122 | φ 0.122, public capital 0.296 × GDP |
| app/simulator.py | 662 | 0.296 | φ 0.122, public capital 0.296 × GDP |
| scenarios/ayuda_cut.py | 22 | 90.21 bn | Scenario: FY 2027 Ayuda cut (₱90.21 bn) |
| scenarios/bsp_oil_response_netting.py | 63 | 0.55 | 0.55,2,3.3 |
| scenarios/bsp_oil_response_netting.py | 63 | 3.3 | 0.55,2,3.3 |
| scenarios/calibrate_wage_curve.py | 101 | 3.9% | e unemployment rate the beta implies at 3.9% unemployment (Blanchflower an |
| scenarios/calibrate_wage_curve.py | 101 | -0.1 | nt (Blanchflower and Oswald 1994: about -0.1 internationally). |
| scenarios/calibrate_wage_curve.py | 105 | 3.9% | e unemployment rate the beta implies at 3.9% unemployment (Blanchflower an |
| scenarios/calibrate_wage_curve.py | 105 | -0.1 | nt (Blanchflower and Oswald 1994: about -0.1 internationally). |
| scenarios/combined_2025_2030.py | 117 | 1.0 | n path (public investment at efficiency 1.0 in 2023-2025, none of the shoc |
| scenarios/combined_2025_2030.py | 270 | 2.0 | evel from 2027; the 2027 dry-season ONI 2.0; typhoon damage documented to |
| scenarios/combined_2025_2030.py | 270 | 0.77 | e allows for a normal year); efficiency 0.77 and no leakage (the efficiency and leakage channel gives  |
| scenarios/combined_revised.py | 103 | 4.4 | 4.4 (PSA actual) |
| scenarios/combined_revised.py | 103 | 3.5 | 3.5-4.5 (DBCC 193rd, Jul 2026); H |
| scenarios/combined_revised.py | 103 | 4.5 | 3.5-4.5 (DBCC 193rd, Jul 2026); H1 act |
| scenarios/combined_revised.py | 103 | 2.6 | 5-4.5 (DBCC 193rd, Jul 2026); H1 actual 2.6 |
| scenarios/combined_revised.py | 103 | 5.0 | 5.0-6.0 (DBCC 193rd) |
| scenarios/combined_revised.py | 103 | 6.0 | 5.0-6.0 (DBCC 193rd) |
| scenarios/combined_revised.py | 106 | ₱19,070 | ₱19,070 bn, end-June 2026 (BTr, as us |
| scenarios/combined_revised.py | 277 | 30.5 | 7 implied by the DBCC 193rd statement: ₱30.5 and ₱33.2 trillion); results a |
| scenarios/combined_revised.py | 277 | 33.2 | by the DBCC 193rd statement: ₱30.5 and ₱33.2 trillion); results are in 2025 |
| scenarios/combined_revised.py | 384 | 5.5 | seline growth: DBCC December 2025 path (5.5 / 6.0 / 6.5%) |
| scenarios/combined_revised.py | 384 | 6.0 |  growth: DBCC December 2025 path (5.5 / 6.0 / 6.5%) |
| scenarios/combined_revised.py | 384 | 6.5% | h: DBCC December 2025 path (5.5 / 6.0 / 6.5%) |
| scenarios/combined_revised.py | 397 | 1.5 | om the IRI plume of 21 Sept 2026; range 1.5-2.5). |
| scenarios/combined_revised.py | 397 | 2.5 | he IRI plume of 21 Sept 2026; range 1.5-2.5). |
| scenarios/combined_revised.py | 411 | 2.0 | Inflation 2026: pre-shock official 2.0-4.0% (midpoint  |
| scenarios/combined_revised.py | 411 | 4.0% | Inflation 2026: pre-shock official 2.0-4.0% (midpoint  |
| scenarios/combined_revised.py | 411 | 5.4% | %, against actual January-September 5.4% (PSA) and the July 2026 offic |
| scenarios/combined_revised.py | 411 | 6.0 | r 5.4% (PSA) and the July 2026 official 6.0-7.0%. The model has no money, |
| scenarios/combined_revised.py | 411 | 7.0% | 4% (PSA) and the July 2026 official 6.0-7.0%. The model has no money, exch |
| scenarios/combined_revised.py | 411 | 5.3% |  the rise in prices. Jobs: unemployment 5.3% in August 2026 against 3.9% a |
| scenarios/combined_revised.py | 411 | 3.9% | nemployment 5.3% in August 2026 against 3.9% a year earlier (PSA LFS). |
| scenarios/combined_revised.py | 447 | 2.3% | lic works lower 2026 consumer prices by 2.3%, against about 0.3-0.8 points |
| scenarios/combined_revised.py | 447 | 0.8 | sumer prices by 2.3%, against about 0.3-0.8 points below forecast in the d |
| scenarios/combined_revised.py | 456 | 0.77 | nstruction that becomes usable capital (0.77, IMF PIMA) and the output ela |
| scenarios/combined_revised.py | 456 | 0.083 | he output elasticity of public capital (0.083 low, 0.122 high; Bom and Ligth |
| scenarios/combined_revised.py | 456 | 0.122 | lasticity of public capital (0.083 low, 0.122 high; Bom and Ligthart 2014). |
| scenarios/combined_revised.py | 458 | 0.71 | s the upper bound. The Okun elasticity (0.71, all quarters 2006-2026) is i |
| scenarios/combined_revised.py | 458 | 0.15 | he 2020-21 quarters: without them it is 0.15 (sensitivity row, beta  |
| scenarios/combined_revised.py | 458 | 0.5 | s left each later year (gap_persistence 0.5: no source yet). |
| scenarios/combined_revised.py | 464 | 66.6% | as 4Ps does (PIDS DP 2024-27, Table 13: 66.6% in the bottom 30%); A's lower |
| scenarios/combined_revised.py | 400 | 1.5 | om the IRI plume of 21 Sept 2026; range 1.5-2.5). |
| scenarios/combined_revised.py | 400 | 2.5 | he IRI plume of 21 Sept 2026; range 1.5-2.5). |
| scenarios/combined_revised.py | 412 | 5.4% | %, against actual January-September 5.4% (PSA) and the July 2026 offic |
| scenarios/combined_revised.py | 412 | 6.0 | r 5.4% (PSA) and the July 2026 official 6.0-7.0%. The model has no money, |
| scenarios/combined_revised.py | 412 | 7.0% | 4% (PSA) and the July 2026 official 6.0-7.0%. The model has no money, exch |
| scenarios/combined_revised.py | 412 | 5.3% |  the rise in prices. Jobs: unemployment 5.3% in August 2026 against 3.9% a |
| scenarios/combined_revised.py | 412 | 3.9% | nemployment 5.3% in August 2026 against 3.9% a year earlier (PSA LFS). |
| scenarios/combined_revised.py | 461 | 0.71 | s the upper bound. The Okun elasticity (0.71, all quarters 2006-2026) is i |
| scenarios/combined_revised.py | 461 | 0.15 | he 2020-21 quarters: without them it is 0.15 (sensitivity row, beta  |
| scenarios/combined_revised.py | 463 | 0.5 | s left each later year (gap_persistence 0.5: no source yet). |
| scenarios/combined_revised.py | 356 | 1.5 | El Nino: ONI 1.5 |
| scenarios/combined_revised.py | 356 | 2.5 | El Nino: ONI 2.5 |
| scenarios/corruption_efficiency_leakage.py | 53 | 0.77 | 0.77 (IMF PIMA 2019) |
| scenarios/corruption_efficiency_leakage.py | 53 | 0.60 | 0.60 (IMF GIMF Philippines 2015) |
| scenarios/corruption_efficiency_leakage.py | 71 | 0.77 | Inputs: efficiency 0.77 (IMF PIMA) or 0.60 (IMF GIMF f |
| scenarios/corruption_efficiency_leakage.py | 71 | 0.60 | Inputs: efficiency 0.77 (IMF PIMA) or 0.60 (IMF GIMF for the Philippines) |
| scenarios/corruption_efficiency_leakage.py | 71 | 1.0 |  0.60 (IMF GIMF for the Philippines) vs 1.0 for the best performers; gover |
| scenarios/corruption_efficiency_leakage.py | 83 | 0.25 | ffie et al. 2012, pp. 21-22) sets it at 0.25 from World Bank project return |
| scenarios/corruption_efficiency_leakage.py | 83 | 0.21 |  On recorded capital the 'low' setting (0.21) is inside that range and the |
| scenarios/corruption_efficiency_leakage.py | 83 | 0.41 | side that range and the 'high' setting (0.41) above it; on usable capital  |
| scenarios/corruption_efficiency_leakage.py | 203 | 0.5 |  0.3 range (section 0); gap persistence 0.5; DIG's overrun parameter is a |
| scenarios/corruption_efficiency_leakage.py | 78 | 0.77 | implied return on usable capital, e 0.77 |
| scenarios/corruption_efficiency_leakage.py | 79 | 0.60 | implied return on usable capital, e 0.60 |
| scenarios/corruption_efficiency_leakage.py | 170 | 208.7 bn | catch-up ₱208.7 bn |
| scenarios/corruption_efficiency_leakage.py | 171 | 1.0 | reform from 2027 (e 1.0), no catch-up |
| scenarios/corruption_efficiency_leakage.py | 172 | 208.7 bn | catch-up ₱208.7 bn + reform from 2027 |
| scenarios/d3_labour_path_sensitivity.py | 20 | -1.22% |  Central (observed 2026 path): 2026 GDP -1.22%, 2027 -0.97%, 2030 -0.69%, lo |
| scenarios/d3_labour_path_sensitivity.py | 20 | -0.97% | erved 2026 path): 2026 GDP -1.22%, 2027 -0.97%, 2030 -0.69%, loss ₱1,654 bn, |
| scenarios/d3_labour_path_sensitivity.py | 20 | -0.69% | th): 2026 GDP -1.22%, 2027 -0.97%, 2030 -0.69%, loss ₱1,654 bn, new poor 3.1 |
| scenarios/d3_labour_path_sensitivity.py | 20 | ₱1,654 |  -1.22%, 2027 -0.97%, 2030 -0.69%, loss ₱1,654 bn, new poor 3.14 / 1.76 M.   |
| scenarios/d3_labour_path_sensitivity.py | 20 | 3.14 | , 2030 -0.69%, loss ₱1,654 bn, new poor 3.14 / 1.76 M.   |
| scenarios/d3_labour_path_sensitivity.py | 20 | 1.76 | -0.69%, loss ₱1,654 bn, new poor 3.14 / 1.76 M.   |
| scenarios/demand_sensitivity.py | 36 | 238.3 bn | Infrastructure freeze -₱238.3 bn |
| scenarios/elasticity_sensitivity.py | 31 | 238.3 bn | Infrastructure freeze -₱238.3 bn |
| scenarios/energy_nest_oil_check.py | 35 | 0.35 |  2028-2030 at the old/new capital blend 0.35 |
| scenarios/energy_nest_oil_check.py | 49 | 0.1 | apital-skilled labour-energy bundle old 0.1 / new 0.8; energy carriers 0.5 |
| scenarios/energy_nest_oil_check.py | 49 | 0.8 | lled labour-energy bundle old 0.1 / new 0.8; energy carriers 0.5): 2028-2 |
| scenarios/energy_nest_oil_check.py | 49 | 0.5 | ndle old 0.1 / new 0.8; energy carriers 0.5): 2028-2030  |
| scenarios/energy_nest_oil_check.py | 49 | 0.85 | energy_shares_at). Infinity GEM's own SAM; hoarding 0.85; wage-curve beta  |
| scenarios/energy_nest_oil_check.py | 51 | 0.85 | energy_shares_at). Infinity GEM's own SAM; hoarding 0.85; wage-curve beta  |
| scenarios/energy_nest_oil_paths.py | 76 | 0.85 | . Infinity GEM's own SAM; hoarding 0.85; wage-curve beta  |
| scenarios/energy_nest_oil_paths.py | 77 | 0.85 | . Infinity GEM's own SAM; hoarding 0.85; wage-curve beta  |
| scenarios/engine_sensitivities.py | 52 | 0.6 | D2, high: stickiness 0.6 (beta recalibrated) |
| scenarios/engine_sensitivities.py | 184 | 12.7% | t alone strengthens the model's peso by 12.7% (check IC1), while the actual |
| scenarios/engine_sensitivities.py | 184 | 2.0% |  (check IC1), while the actual peso was 2.0% weaker than forecast in Janua |
| scenarios/engine_sensitivities.py | 188 | 0.6 | oes (Peltzman 2000). Stickiness 0.3 and 0.6: the share of a cost change n |
| scenarios/engine_sensitivities.py | 188 | 0.65% | lic works alone lowering 2026 prices by 0.65%) is out of reach: at stickine |
| scenarios/engine_sensitivities.py | 188 | 0.95 | y 0.65%) is out of reach: at stickiness 0.95 they still fall 1.16%, from fl |
| scenarios/engine_sensitivities.py | 188 | 1.16% | ach: at stickiness 0.95 they still fall 1.16%, from flexible farm and food  |
| scenarios/engine_sensitivities.py | 194 | 0.29 | 9 2019; `infinity_gem/stickiness.py`): food 0.29, utilities and rents 0.56, tr |
| scenarios/engine_sensitivities.py | 194 | 0.56 | ss.py`): food 0.29, utilities and rents 0.56, transport 0.71, restaurants  |
| scenarios/engine_sensitivities.py | 194 | 0.71 | 29, utilities and rents 0.56, transport 0.71, restaurants and financial se |
| scenarios/engine_sensitivities.py | 194 | 0.87 | .71, restaurants and financial services 0.87, education 0.89; refined petr |
| scenarios/engine_sensitivities.py | 194 | 0.89 |  and financial services 0.87, education 0.89; refined petroleum flexible;  |
| scenarios/engine_sensitivities.py | 194 | 0.62 |  the simple mean (value-added weighted: 0.62). |
| scenarios/engine_sensitivities.py | 198 | 2.0% | Data checks: the peso was 2.0% weaker than forecast in Janua |
| scenarios/engine_sensitivities.py | 198 | 2.5% | han forecast in January-September 2026 (2.5% for the year; Note C); the VA |
| scenarios/engine_sensitivities.py | 198 | 0.65 |  shocks lowered 2026 inflation by about 0.65 points (the model's public wor |
| scenarios/engine_sensitivities.py | 202 | 3.9% | e unemployment rate the beta implies at 3.9% unemployment (Blanchflower an |
| scenarios/engine_sensitivities.py | 202 | -0.1 | nt (Blanchflower and Oswald 1994: about -0.1). |
| scenarios/example_catchup_2027.py | 13 | 208.7 bn | Example: DPWH catch-up spending of ₱208.7 bn in 2027 |
| scenarios/example_catchup_2027.py | 23 | 208.7 bn | PWH 2025 carry-over still unobligated, ₱208.7 bn. |
| scenarios/fertilizer_2026_measured.py | 59 | 0.1% | 8 I-O, sector 110), % (activities above 0.1%) |
| a development script (not in this repository) | 247 | 0.002 | , p=0.002) applied to the realised 2026 |
| a development script (not in this repository) | 258 | 41.8 bn | he same shares as an earlier ₱41.8 bn hazard-damage split. Modelled |
| a development script (not in this repository) | 317 | 17.71 | 's change in government savings to the ₱17.71 tn NG debt baseline used in th |
| a development script (not in this repository) | 260 | 41.8 bn | he same shares as an earlier ₱41.8 bn hazard-damage split. Modelled |
| scenarios/gap_persistence_sensitivity.py | 51 | 0.5 | ong-run year set to 0 (closes at once), 0.5 (central; no source) and 1 (ne |
| scenarios/hoarding_grid.py | 60 | -0.31 | industry slope, jobs on output (data -0.31) |
| scenarios/hoarding_grid.py | 73 | 1.0 | Jan-Aug); public-works multiplier about 1.0-1.1 (PSA local projections);  |
| scenarios/hoarding_grid.py | 73 | 1.1 | Aug); public-works multiplier about 1.0-1.1 (PSA local projections); labou |
| scenarios/hoarding_grid.py | 73 | +9.0% | ncome and wages close to trend (LFS pay +9.0% in 2026 after +7.3% in 2025); |
| scenarios/hoarding_grid.py | 73 | +7.3% | e to trend (LFS pay +9.0% in 2026 after +7.3% in 2025); H1 2026 growth 2.6% |
| scenarios/hoarding_grid.py | 73 | 2.6% | 26 after +7.3% in 2025); H1 2026 growth 2.6% against the pre-shock 5.5%. S |
| scenarios/hoarding_grid.py | 73 | 5.5% |  2026 growth 2.6% against the pre-shock 5.5%. Script `scenarios/hoarding_g |
| scenarios/home_consumption_sensitivity.py | 28 | 238.3 bn | Infrastructure freeze -₱238.3 bn |
| scenarios/industry_baseline.py | 62 | 208.7 bn | Catch-up (+₱208.7 bn in 2027) on each baseline |
| scenarios/infrastructure_catchup.py | 107 | 1.5% | h, depreciation (5%) and labour growth (1.5%) are placeholder assumptions  |
| scenarios/infrastructure_freeze.py | 32 | 238.3 bn |  bn (= ₱238.3 bn / 2025 GDP); 2026 ₱ |
| scenarios/infrastructure_freeze.py | 32 | 202.2 bn |  bn (= ₱202.2 bn / H1 2025 GDP, assumed to app |
| scenarios/infrastructure_full_dynamic.py | 71 | 238.3 bn | e of GDP as in the 2023 SAM). Shocks: -₱238.3 bn construction investment in 20 |
| scenarios/infrastructure_full_dynamic.py | 71 | 208.7 bn | 3 bn construction investment in 2025; +₱208.7 bn in 2027. |
| scenarios/infrastructure_public_capital.py | 31 | 0.083 | short-run elasticity 0.083 |
| scenarios/infrastructure_public_capital.py | 31 | 0.122 | long-run elasticity 0.122 |
| scenarios/infrastructure_public_capital.py | 84 | 3.52% | ntrol are missing, which decays slowly (3.52% a year). A lower KG/GDP makes |
| scenarios/infrastructure_public_capital.py | 84 | 0.5 |  Assumptions to review: gap persistence 0.5; the elasticitie |
| scenarios/infrastructure_public_capital.py | 84 | 0.77 | ticities are mostly OECD estimates; e = 0.77 rests on perceived quality. |
| scenarios/interest_closure_check.py | 38 | 3.3 | interest closure, theta 3.3, eps 0.3 |
| scenarios/interest_closure_check.py | 56 | 0.85 | anged (Keynesian). Infinity GEM's own SAM; hoarding 0.85; wage-curve beta  |
| scenarios/interest_closure_check.py | 56 | 1.9 | cks. theta from the DSGE-CGE link (matched values 1.9-3.3); eps 0.3 an assumption.  |
| scenarios/interest_closure_check.py | 56 | 3.3 |  theta from the DSGE-CGE link (matched values 1.9-3.3); eps 0.3 an assumption. Scri |
| scenarios/interest_closure_check.py | 58 | 1.9 | cks. theta from the DSGE-CGE link (matched values 1.9-3.3); eps 0.3 an assumption.  |
| scenarios/interest_closure_check.py | 58 | 3.3 |  theta from the DSGE-CGE link (matched values 1.9-3.3); eps 0.3 an assumption. Scri |
| scenarios/measure_c_sensitivity.py | 72 | 208.7 bn | y.py`. The central 2026 run with C (₱208.7 bn of DPWH's lapsing 2025 money) |
| scenarios/measure_c_sensitivity.py | 72 | 0.77 | vestment that becomes usable capital at 0.77 (IMF PIMA, central) or 0.6 (IM |
| scenarios/measure_c_sensitivity.py | 72 | 0.6 |  capital at 0.77 (IMF PIMA, central) or 0.6 (IMF DIG base, Buffie et al. 2 |
| scenarios/measure_c_sensitivity.py | 45 | 0.77 | efficiency 0.77 (central) |
| scenarios/measure_c_sensitivity.py | 45 | 0.6 | efficiency 0.6 (IMF DIG base) |
| scenarios/monetary_check.py | 59 | 0.6 | D2, high: stickiness 0.6 (beta recalibrated) |
| scenarios/monetary_check.py | 164 | 0.85 | 0.85 |
| scenarios/monetary_check.py | 170 | 0.01 | 0.01 |
| scenarios/monetary_check.py | 188 | 0.1 | -energy bundle, MANAGE-WB elasticities (0.1 short run, 0.8 later; 0.5 betw |
| scenarios/monetary_check.py | 188 | 0.8 |  MANAGE-WB elasticities (0.1 short run, 0.8 later; 0.5 between carriers) |
| scenarios/monetary_check.py | 188 | 0.5 | elasticities (0.1 short run, 0.8 later; 0.5 between carriers) |
| scenarios/monetary_check.py | 167 | 0.55 | oil0.85:0.55,oil0.85:3.3,oil0.85:2:foresig |
| scenarios/monetary_check.py | 167 | 3.3 | oil0.85:0.55,oil0.85:3.3,oil0.85:2:foresight |
| scenarios/oil_passthrough_by_sam.py | 50 | 01.1 | 01.1.6 |
| scenarios/oil_passthrough_by_sam.py | 51 | 01.1 | 01.1.9 |
| scenarios/oil_passthrough_by_sam.py | 52 | 01.2 | 01.2.5 |
| scenarios/oil_passthrough_by_sam.py | 53 | 01.2 | 01.2.9 |
| scenarios/oil_passthrough_by_sam.py | 54 | 02.1 | 02.1 |
| scenarios/oil_passthrough_by_sam.py | 54 | 02.3 | 02.3 |
| scenarios/oil_passthrough_by_sam.py | 54 | 02.4 | 02.4 |
| scenarios/oil_passthrough_by_sam.py | 56 | 04.1 | 04.1 |
| scenarios/oil_passthrough_by_sam.py | 56 | 04.3 | 04.3 |
| scenarios/oil_passthrough_by_sam.py | 56 | 04.4 | 04.4 |
| scenarios/oil_passthrough_by_sam.py | 56 | 04.5 | 04.5.3 |
| scenarios/oil_passthrough_by_sam.py | 57 | 04.5 | 04.5.4 |
| scenarios/oil_passthrough_by_sam.py | 59 | 07.1 | 07.1 |
| scenarios/oil_passthrough_by_sam.py | 59 | 07.2 | 07.2.4 |
| scenarios/oil_passthrough_by_sam.py | 60 | 07.3 | 07.3 |
| scenarios/oil_passthrough_by_sam.py | 60 | 07.4 | 07.4 |
| scenarios/oil_passthrough_by_sam.py | 61 | 11.1 | 11.1 |
| scenarios/oil_passthrough_by_sam.py | 61 | 11.2 | 11.2 |
| scenarios/oil_petroleum_split.py | 33 | 0.6 | A combined SAM, share 0.6 (published) |
| scenarios/oil_petroleum_split.py | 52 | 0.6 | assumed 0.6 |
| a development script (not in this repository) | 27 | 7.1405 | central check (beta 7.1405, 17 Oct 2026) |
| a development script (not in this repository) | 27 | 0.600 | hours target 0.600 (beta 8.893) |
| a development script (not in this repository) | 27 | 8.893 | hours target 0.600 (beta 8.893) |
| scenarios/okun_hours_sensitivity.py | 34 | 0.713 | central (persons, all quarters, e 0.713; 17 Oct 2026) |
| scenarios/okun_hours_sensitivity.py | 54 | 3.14 | _split_map=True (the scenarios of 17 Oct 2026 used False: 3.14 M). 'Implied pay elasticity' a |
| scenarios/public_works_multiplier_sticky_construction.py | 33 | 1.0 | construction rigid downward, stickiness 1.0 (beta  |
| scenarios/public_works_multiplier_sticky_construction.py | 34 | 0.6 | construction rigid downward, stickiness 0.6 (beta  |
| scenarios/public_works_multiplier_sticky_construction.py | 35 | 0.6 | all non-farm prices rigid downward, 0.6 (D2 high; beta  |
| scenarios/public_works_multiplier_sticky_construction.py | 61 | 1.0 | % of GDP). PSA data: about 1.0-1.1 (`outputs/freeze_multipli |
| scenarios/public_works_multiplier_sticky_construction.py | 61 | 1.1 | % of GDP). PSA data: about 1.0-1.1 (`outputs/freeze_multiplier_bu |
| scenarios/public_works_multiplier_sticky_construction.py | 63 | 1.0 | % of GDP). PSA data: about 1.0-1.1 (`outputs/freeze_multipli |
| scenarios/public_works_multiplier_sticky_construction.py | 63 | 1.1 | % of GDP). PSA data: about 1.0-1.1 (`outputs/freeze_multiplier_bu |
| scenarios/sam_psa_sensitivity.py | 163 | 0.6 | cCGE(sr_pricing='sticky', sr_stickiness=0.6), the high setting of review D2; the wage |
| scenarios/sam_psa_sensitivity.py | 163 | -1.9% |  is Infinity GEM's own SAM's 2026 price fall (about -1.9% with flexible prices) a flexi |
| scenarios/own_sam_cpi_decomposition.py | 81 | 7.14 | s own calibrated wage-curve beta (IFPRI 7.14, own SAM v0.3 10.77, v0.4 9.72). |
| scenarios/own_sam_cpi_decomposition.py | 81 | 10.77 |  wage-curve beta (IFPRI 7.14, own SAM v0.3 10.77, v0.4 9.72). Contribution = C |
| scenarios/own_sam_cpi_decomposition.py | 81 | 9.72 | beta (IFPRI 7.14, own SAM v0.3 10.77, v0.4 9.72). Contribution = CPI weight x |
| scenarios/own_sam_cpi_decomposition.py | 27 | 0.4 | 0.4 |
| scenarios/own_sam_v04_test.py | 19 | 0.4 | 0.4 |
| scenarios/own_sam_wage_curve_diagnostic.py | 98 | 7.14 | the values shown (0 = fixed peso wages; 7.14 = IFPRI's calibration; 10.77 = |
| scenarios/own_sam_wage_curve_diagnostic.py | 98 | 10.77 | peso wages; 7.14 = IFPRI's calibration; 10.77 = own SAM v0.3's). |
| scenarios/own_sam_wage_curve_diagnostic.py | 102 | 7.14 |  Employment by PSA industry, 2026, beta 7.14 (% against the no-shock path) |
| scenarios/settings_comparison.py | 21 | 238.3 bn | Infrastructure freeze (−₱238.3 bn) |
| scenarios/settings_comparison.py | 23 | 90.21 bn | Ayuda cut (−₱90.21 bn, bottom 40%) |
| scenarios/settings_comparison.py | 53 | 0.083 | id closure and public capital (low: phi 0.083, KG 0.397 x GDP; high: phi 0. |
| scenarios/settings_comparison.py | 53 | 0.397 |  and public capital (low: phi 0.083, KG 0.397 x GDP; high: phi 0.122, KG 0.2 |
| scenarios/settings_comparison.py | 53 | 0.122 | w: phi 0.083, KG 0.397 x GDP; high: phi 0.122, KG 0.296 x GDP). Home consum |
| scenarios/settings_comparison.py | 53 | 0.296 | 83, KG 0.397 x GDP; high: phi 0.122, KG 0.296 x GDP). Home consumption |
| a development script (not in this repository) | 60 | 0.85 | Oct2026.md`; PSA's data support h about 0.85, range 0.75-0.95; since 19 Oc |
| a development script (not in this repository) | 60 | 0.75 |  PSA's data support h about 0.85, range 0.75-0.95; since 19 Oct 8:40 AM ho |
| a development script (not in this repository) | 60 | 0.95 | s data support h about 0.85, range 0.75-0.95; since 19 Oct 8:40 AM hoardin |
| scenarios/vintage_check.py | 21 | 0.7 | vintages, release 0.7 after 2027 only (installed cap |
| scenarios/vintage_check.py | 25 | 0.7 | vintages, release 0.7 in every year (upper bound on  |
| scenarios/vintage_check.py | 48 | 0.7 | ase elasticity of installed capital e = 0.7 (MANAGE-WB's invElas, bridge-f |
| scenarios/vintage_check.py | 48 | 0.85 | s in the baseline. Infinity GEM's own SAM; hoarding 0.85; wage-curve beta  |

## G. Fitting and randomness

| file | line | function | call | kind |
|---|---|---|---|---|
| infinity_gem/cge.py | 894 | solve | root | fit/solve |
| infinity_gem/cge.py | 896 | solve | root | fit/solve |
| infinity_gem/demand.py | 95 | fit_frisch | minimize_scalar | fit/solve |
| infinity_gem/dynamic.py | 568 | _calibrate_industries | root | fit/solve |
| infinity_gem/dynamic.py | 607 | _wage_curve | root | fit/solve |
| infinity_gem/dynamic.py | 367 | _robust_root | brentq | fit/solve |
| infinity_gem/dynamic.py | 796 | _run | brentq | fit/solve |
| infinity_gem/stochastic.py | 235 | run | np.random.default_rng | random |
| infinity_gem/stochastic.py | 236 | run | np.random.default_rng | random |
| infinity_gem/stochastic.py | 214 | _B | oil_random_walk | random |
| infinity_gem/svar.py | 135 | sign_restrictions | np.random.default_rng | random |
| infinity_gem/svar.py | 239 | bootstrap_irf | np.random.default_rng | random |
| infinity_gem/svar.py | 310 | draw | np.random.default_rng | random |
| infinity_gem/var.py | 103 | irf_table | np.random.default_rng | random |
| scenarios/lhs_2026_ranges.py | 62 | draws | qmc.LatinHypercube(d=len(PARAMS), seed=SEED).random | random |
| scenarios/poverty_sampling_error.py | 53 | bootstrap | np.random.default_rng | random |

## H. Tamper tests

A copy of the model (in a temporary folder, deleted afterwards) is broken on purpose and checks D1, D2, C1, C3, C4, C5, A1, R0 are run on it. Each break must make at least one check FAIL.

| tamper | why | edit | expected | result |
|---|---|---|---|---|
| Control: unbroken copy |  | none |  | all PASS (as it should) |
| Tariff revenue left out of government income | an accounting error: money disappears from the accounts | infinity_gem/cge.py: `+ MTAX.sum() + STAX.sum() + ATAX.sum()` -> `+ STAX.sum() + ATAX.sum()` | C1 | caught by C1, C4 |
| A leak that shows only after a shock (import bill at pre-shock world prices) | an error invisible in the base year: the base-year SAM is still reproduced | infinity_gem/cge.py: `fcu_out = (pwm * (QM + self.rex)).sum()` -> `fcu_out = (self.pwm * (QM + self.rex)).sum()` | C4 | caught by C4, R0 |
| A hidden plug: 0.1% extra demand in every factor market | a plug term, like the archived R scripts' Missing_Demand_0 | infinity_gem/cge.py: `- self.QFS0[k] * sh["qfs_scale"][k]) / self.QFS0[k])` -> `- self.QFS0[k] * sh["qfs_scale"][k]) / self.QFS0[k] + 0.001)` | C1 | caught by C1, C3, R0 |
| Solver stopped early but reports success | a result used without convergence | infinity_gem/cge.py: `ok = bool(np.abs(R).max() < 1e-7)` -> `ok = True` | C3, C4 | caught by C3, C4, C5, A1, R0 |
| Headline result rigged: Simulator's real GDP effect scaled by 0.9 | a hard-coded adjustment to an answer | app/engines.py: `"Real GDP (%)": pct(gs["real"], gb["real"]),` -> `"Real GDP (%)": pct(gs["real"], gb["real"]) * 0.9,` | A1, R0 | caught by A1, R0 |
| A parameter quietly changed: Armington elasticity 2.0 -> 2.2 | a parameter changed to move results; the model is still internally consistent | infinity_gem/cge.py: `"sigma_q": 2.0,` -> `"sigma_q": 2.2,` | R0 | caught by A1, R0 |
| One number in the data changed (2023 SAM, one cell +₱1 bn) | the data edited to move results | row 'amaiz', column cmaiz: 200.91810465 -> 201.91810465 | D1, D2 | caught by D1, D2, C1, C3, C4, C5, A1, R0 |

<details><summary>Control: unbroken copy: every check</summary>

| check | result | detail |
|---|---|---|
| D1 | PASS | 81 files checked; mismatches: none |
| D2 | PASS | 002_IFPRI_SAM_PHL_2018_SAM.csv: max gap 5; 002_IFPRI_SAM_PHL_2023_SAM.csv: max gap 4e-08 |
| C1 | PASS | long run (investment closure): 3.8e-09; savings closure: 3.8e-09; short run (Keynesian, fixed capital): 3.8e-09 |
| C3 | PASS | long run (investment closure): dQ 7.6e-10, dP 3.9e-09; savings closure: dQ 7.8e-10, dP 3.9e-09; short run (Keynesian, fixed capital): dQ 5.1e-10, dP 3.9e-09 |
| C4 | PASS | long run (investment closure): solved=True, slack/investment 3.4e-12; savings closure: solved=True, slack/investment 3.3e-12; short run (Keynesian, fixed capita |
| C5 | PASS | long run (investment closure): gap 3.6e-12; savings closure: gap 6.9e-11; short run (Keynesian, fixed capital): gap 1.8e-10 |
| A1 | PASS | infrastructure short-run CGE: GDP -0.279% (script -0.279), new poor 497,479 (497,479); SAM: GDP -350.22 (-350.22, SAM units); Ayuda household income -185.06 (-1 |
| R0 | PASS | 21 results compared (relative tolerance 1e-9); differing: none |

</details>

<details><summary>Tariff revenue left out of government income: every check</summary>

| check | result | detail |
|---|---|---|
| D1 | PASS | 81 files checked; mismatches: none |
| D2 | PASS | 002_IFPRI_SAM_PHL_2018_SAM.csv: max gap 5; 002_IFPRI_SAM_PHL_2023_SAM.csv: max gap 4e-08 |
| C1 | FAIL | long run (investment closure): 2.2e-01; savings closure: 2.2e-01; short run (Keynesian, fixed capital): 2.2e-01 |
| C3 | PASS | long run (investment closure): dQ 7.6e-10, dP 3.9e-09; savings closure: dQ 7.8e-10, dP 3.9e-09; short run (Keynesian, fixed capital): dQ 5.1e-10, dP 3.9e-09 |
| C4 | FAIL | long run (investment closure): solved=True, slack/investment 2.1e-01; savings closure: solved=True, slack/investment 2.1e-01; short run (Keynesian, fixed capita |
| C5 | PASS | long run (investment closure): gap 1.8e-11; savings closure: gap 3.3e-11; short run (Keynesian, fixed capital): gap 1.2e-10 |
| A1 | PASS | infrastructure short-run CGE: GDP -0.279% (script -0.279), new poor 497,479 (497,479); SAM: GDP -350.22 (-350.22, SAM units); Ayuda household income -185.06 (-1 |
| R0 | PASS | 21 results compared (relative tolerance 1e-9); differing: none |

</details>

<details><summary>A leak that shows only after a shock (import bill at pre-shock world prices): every check</summary>

| check | result | detail |
|---|---|---|
| D1 | PASS | 81 files checked; mismatches: none |
| D2 | PASS | 002_IFPRI_SAM_PHL_2018_SAM.csv: max gap 5; 002_IFPRI_SAM_PHL_2023_SAM.csv: max gap 4e-08 |
| C1 | PASS | long run (investment closure): 3.8e-09; savings closure: 3.8e-09; short run (Keynesian, fixed capital): 3.8e-09 |
| C3 | PASS | long run (investment closure): dQ 7.6e-10, dP 3.9e-09; savings closure: dQ 7.8e-10, dP 3.9e-09; short run (Keynesian, fixed capital): dQ 5.1e-10, dP 3.9e-09 |
| C4 | FAIL | long run (investment closure): solved=True, slack/investment 8.1e-02; savings closure: solved=True, slack/investment 7.9e-02; short run (Keynesian, fixed capita |
| C5 | PASS | long run (investment closure): gap 6.5e-11; savings closure: gap 6.5e-11; short run (Keynesian, fixed capital): gap 1.3e-10 |
| A1 | PASS | infrastructure short-run CGE: GDP -0.279% (script -0.279), new poor 497,479 (497,479); SAM: GDP -350.22 (-350.22, SAM units); Ayuda household income -185.06 (-1 |
| R0 | FAIL | 21 results compared (relative tolerance 1e-9); differing: ['cge_lr_real_gdp_pct', 'cge_lr_eh', 'cge_sav_real_gdp_pct', 'cge_sav_eh'] |

</details>

<details><summary>A hidden plug: 0.1% extra demand in every factor market: every check</summary>

| check | result | detail |
|---|---|---|
| D1 | PASS | 81 files checked; mismatches: none |
| D2 | PASS | 002_IFPRI_SAM_PHL_2018_SAM.csv: max gap 5; 002_IFPRI_SAM_PHL_2023_SAM.csv: max gap 4e-08 |
| C1 | FAIL | long run (investment closure): 1.0e-03; savings closure: 1.0e-03; short run (Keynesian, fixed capital): 1.0e-03 |
| C3 | FAIL | long run (investment closure): dQ 1.7e-03, dP 7.7e-05; savings closure: dQ 3.3e-03, dP 5.7e-05; short run (Keynesian, fixed capital): dQ 1.4e-03, dP 6.3e-04 |
| C4 | PASS | long run (investment closure): solved=True, slack/investment 3.4e-12; savings closure: solved=True, slack/investment 3.3e-12; short run (Keynesian, fixed capita |
| C5 | PASS | long run (investment closure): gap 3.6e-12; savings closure: gap 7.3e-11; short run (Keynesian, fixed capital): gap 1.8e-10 |
| A1 | PASS | infrastructure short-run CGE: GDP -0.279% (script -0.279), new poor 497,479 (497,479); SAM: GDP -350.22 (-350.22, SAM units); Ayuda household income -185.06 (-1 |
| R0 | FAIL | 21 results compared (relative tolerance 1e-9); differing: ['cge_lr_real_gdp_pct', 'cge_lr_emp', 'cge_lr_eh', 'cge_sav_real_gdp_pct', 'cge_sav_emp', 'cge_sav_eh' |

</details>

<details><summary>Solver stopped early but reports success: every check</summary>

| check | result | detail |
|---|---|---|
| D1 | PASS | 81 files checked; mismatches: none |
| D2 | PASS | 002_IFPRI_SAM_PHL_2018_SAM.csv: max gap 5; 002_IFPRI_SAM_PHL_2023_SAM.csv: max gap 4e-08 |
| C1 | PASS | long run (investment closure): 3.8e-09; savings closure: 3.8e-09; short run (Keynesian, fixed capital): 3.8e-09 |
| C3 | FAIL | long run (investment closure): dQ 9.8e-06, dP 2.2e-07; savings closure: dQ 1.0e-05, dP 2.3e-07; short run (Keynesian, fixed capital): dQ 9.6e-01, dP 2.2e-01 |
| C4 | FAIL | long run (investment closure): solved=True, slack/investment 1.2e-02; savings closure: solved=True, slack/investment 1.3e-02; short run (Keynesian, fixed capita |
| C5 | FAIL | long run (investment closure): gap 5.0e+01; savings closure: gap 5.8e+01; short run (Keynesian, fixed capital): gap 2.2e+02 |
| A1 | FAIL | infrastructure short-run CGE: GDP -0.260% (script -0.279), new poor 519,373 (497,479); SAM: GDP -350.22 (-350.22, SAM units); Ayuda household income -185.06 (-1 |
| R0 | FAIL | 21 results compared (relative tolerance 1e-9); differing: ['cge_lr_real_gdp_pct', 'cge_lr_cpi', 'cge_lr_emp', 'cge_lr_eh', 'cge_sav_real_gdp_pct', 'cge_sav_cpi' |

</details>

<details><summary>Headline result rigged: Simulator's real GDP effect scaled by 0.9: every check</summary>

| check | result | detail |
|---|---|---|
| D1 | PASS | 81 files checked; mismatches: none |
| D2 | PASS | 002_IFPRI_SAM_PHL_2018_SAM.csv: max gap 5; 002_IFPRI_SAM_PHL_2023_SAM.csv: max gap 4e-08 |
| C1 | PASS | long run (investment closure): 3.8e-09; savings closure: 3.8e-09; short run (Keynesian, fixed capital): 3.8e-09 |
| C3 | PASS | long run (investment closure): dQ 7.6e-10, dP 3.9e-09; savings closure: dQ 7.8e-10, dP 3.9e-09; short run (Keynesian, fixed capital): dQ 5.1e-10, dP 3.9e-09 |
| C4 | PASS | long run (investment closure): solved=True, slack/investment 3.4e-12; savings closure: solved=True, slack/investment 3.3e-12; short run (Keynesian, fixed capita |
| C5 | PASS | long run (investment closure): gap 3.6e-12; savings closure: gap 6.9e-11; short run (Keynesian, fixed capital): gap 1.8e-10 |
| A1 | FAIL | infrastructure short-run CGE: GDP -0.251% (script -0.279), new poor 497,479 (497,479); SAM: GDP -350.22 (-350.22, SAM units); Ayuda household income -185.06 (-1 |
| R0 | FAIL | 21 results compared (relative tolerance 1e-9); differing: ['sim_sr_gdp_pct'] |

</details>

<details><summary>A parameter quietly changed: Armington elasticity 2.0 -> 2.2: every check</summary>

| check | result | detail |
|---|---|---|
| D1 | PASS | 81 files checked; mismatches: none |
| D2 | PASS | 002_IFPRI_SAM_PHL_2018_SAM.csv: max gap 5; 002_IFPRI_SAM_PHL_2023_SAM.csv: max gap 4e-08 |
| C1 | PASS | long run (investment closure): 3.8e-09; savings closure: 3.8e-09; short run (Keynesian, fixed capital): 3.8e-09 |
| C3 | PASS | long run (investment closure): dQ 8.2e-10, dP 3.9e-09; savings closure: dQ 8.4e-10, dP 3.9e-09; short run (Keynesian, fixed capital): dQ 5.4e-10, dP 3.9e-09 |
| C4 | PASS | long run (investment closure): solved=True, slack/investment 3.4e-12; savings closure: solved=True, slack/investment 3.3e-12; short run (Keynesian, fixed capita |
| C5 | PASS | long run (investment closure): gap 7.3e-12; savings closure: gap 8.4e-11; short run (Keynesian, fixed capital): gap 1.2e-10 |
| A1 | FAIL | infrastructure short-run CGE: GDP -0.282% (script -0.279), new poor 497,479 (497,479); SAM: GDP -350.22 (-350.22, SAM units); Ayuda household income -185.06 (-1 |
| R0 | FAIL | 21 results compared (relative tolerance 1e-9); differing: ['cge_lr_real_gdp_pct', 'cge_lr_eh', 'cge_sav_real_gdp_pct', 'cge_sav_eh', 'cge_sr_real_gdp_pct', 'cge |

</details>

<details><summary>One number in the data changed (2023 SAM, one cell +₱1 bn): every check</summary>

| check | result | detail |
|---|---|---|
| D1 | FAIL | 81 files checked; mismatches: ['sam/002_IFPRI_SAM_PHL_2023_SAM.csv'] |
| D2 | FAIL | 002_IFPRI_SAM_PHL_2018_SAM.csv: max gap 5; 002_IFPRI_SAM_PHL_2023_SAM.csv: max gap 1 |
| C1 | FAIL | ERROR: ValueError('The SAM 002_IFPRI_SAM_PHL_2023_SAM.csv does not balance: largest row-column gap 1 (account cmaiz). If it is published in rounded figures, loa |
| C3 | FAIL | ERROR: RuntimeError('the models were not built (check C1 failed), so this check could not test anything') |
| C4 | FAIL | ERROR: RuntimeError('the models were not built (check C1 failed), so this check could not test anything') |
| C5 | FAIL | ERROR: RuntimeError('the models were not built (check C1 failed), so this check could not test anything') |
| A1 | FAIL | ERROR: ValueError('The SAM 002_IFPRI_SAM_PHL_2023_SAM.csv does not balance: largest row-column gap 1 (account cmaiz). If it is published in rounded figures, loa |
| R0 | FAIL | ERROR: ValueError('The SAM 002_IFPRI_SAM_PHL_2023_SAM.csv does not balance: largest row-column gap 1 (account cmaiz). If it is published in rounded figures, loa |

</details>

