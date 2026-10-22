# Validating the CGE's labour-market assumptions (14 Oct 2026)

**By:** an AI coding assistant. **Status:** development version only. Nothing published changes: R0 passes, and the development version passed 43 of 43 checks, including the new W2.

## The question

In the short run (the central closure behind the September 2026 figures), Infinity GEM lets **low- and medium-skill employment follow demand at a fixed wage**, while high-skill workers stay fully employed. Two things needed checking:

1. **Is there enough slack** for employment to follow demand?
2. **What is held fixed:** the *real* wage, indexed to the CPI within the year (the model so far), or the *peso* wage (sticky pay)?

A third, open since 8 Oct: under the "0.3 recommended" settings, cutting Ayuda or remittances **raised** low-skill employment slightly, which is an implausible sign.

## 1. Slack: yes (PSA Labor Force Survey, OpenSTAT 0021B3FKEI2)

| | 2019 | 2020 | 2023 | 2024 | 2025 | 2026, Jan–Aug |
|---|---|---|---|---|---|---|
| Unemployment rate | 5.1% | 10.3% | 4.4% | 3.8% | 4.2% | 4.7–6.0% |
| Underemployment rate | 13.8% | 16.2% | 12.3% | 11.9% | 11.9% | 11.8–15.2% |

About one worker in eight wants more hours, and unemployment rose in 2026. Treating low- and medium-skill employment as demand-determined in a one-year horizon is supported.

## 2. Wages: sticky in pesos (OpenSTAT 0161B3FADB2, average daily basic pay of wage and salary workers)

- In **2020**, unemployment doubled (5.1% to 10.3%), yet average daily pay **rose 3.6%** in pesos (₱485.58 to ₱503.28); the median industry rose 1.3%.
- Some industry averages fell (50 of 210 industry-years, 2017–2025), but an average also changes with *who* keeps a job. When low-paid workers are laid off, the average rises. So this is weak evidence either way.
- **Minimum wages are set in nominal pesos** by the Regional Tripartite Wages and Productivity Boards (RA 6727, 1989) and adjusted by wage orders, typically about once a year.

**Conclusion: within a year, Philippine wages behave as fixed in pesos, not indexed to prices.**

## 3. The 0.3 sign puzzle, explained

`1_signflip_by_upgrade.py`, `2_signflip_by_elasticity_and_activity.py`.

- Turning the four 0.3 upgrades on one at a time shows that **only the Philippine elasticity set flips the sign**, and within it **only the labour–capital substitution elasticities (sigma_va, GTAP-based)**. The trade elasticities, the petroleum split, LES demand and the split margins do not.
- **The mechanism.** The model ties the short-run wage to the CPI one-for-one (`cge.py`: wage = wbar × CPI), while the exchange rate is fixed. A demand cut lowers the CPI (−0.37% for the Ayuda cut), so peso wages fall 0.37% *within the year*, relative to world prices. Export-oriented services then substitute labour for their fixed capital, and their GTAP elasticities are high. The extra jobs appear mainly in **business services** (+0.07% of low-skill employment) and outweigh the losses in rice, fisheries and food processing.
- **It is an artefact of the indexed-wage assumption.** With sticky peso wages the sign is negative under both settings (below).

## 4. The new option and what it changes

**New in 0.3.4:** `CGE(..., wage="nominal")` fixes the peso wage of the unemployed labour types; the default `wage="real"` keeps the previous behaviour. The option is off by default. Check W2 tests it: it changes nothing outside the short run; benchmark residual 3.8e-09; doubling the exchange rate and the peso wage doubles prices and leaves quantities unchanged; a transfer cut lowers low-skill jobs; a mistyped option is refused.

Short run, `3_wage_closure_sensitivity.py` (CSV: `wage_closure_sensitivity.csv`):

| Shock | Setting | Wages | GDP % | Low-skill jobs % | New poor |
|---|---|---|---|---|---|
| Freeze −₱238.3 bn | 0.2 published | indexed (published) | −0.279 | −1.80 | 497,479 |
| | 0.2 published | **sticky** | −0.345 | −2.70 | 490,047 |
| | 0.3 recommended | indexed | −0.231 | −1.91 | 446,278 |
| | 0.3 recommended | **sticky** | −0.306 | −2.82 | 477,793 |
| World oil +20% | 0.2 | indexed | −0.215 | −1.14 | 600,661 |
| | 0.2 | **sticky** | −0.156 | −0.33 | 619,934 |
| | 0.3 | indexed | −0.260 | −1.39 | 690,236 |
| | 0.3 | **sticky** | −0.228 | −1.01 | 676,524 |
| Ayuda −₱90.21 bn | 0.2 | indexed | −0.054 | −0.08 | 1,534,348 |
| | 0.2 | **sticky** | −0.074 | −0.35 | 1,530,316 |
| | 0.3 | indexed | −0.031 | **+0.04** | 1,517,135 |
| | 0.3 | **sticky** | −0.061 | −0.31 | 1,525,422 |
| Remittances −10% | 0.2 | indexed | −0.072 | −0.05 | 168,809 |
| | 0.2 | **sticky** | −0.105 | −0.51 | 157,121 |
| | 0.3 | indexed | −0.042 | **+0.08** | 145,887 |
| | 0.3 | **sticky** | −0.090 | −0.50 | 164,333 |
| Four shocks together | 0.2 | indexed | −0.859 | −3.74 | 1,764,199 |
| | 0.2 | **sticky** | −0.797 | −2.90 | 1,782,283 |
| | 0.3 | indexed | −0.923 | −4.67 | 2,038,687 |
| | 0.3 | **sticky** | −0.914 | −4.56 | 2,031,730 |

**Reading it:**
- **The combined (four-shock) result is robust:** GDP moves by at most 0.06 pp and new poor by at most 1%. Oil, which raises prices, and the freeze, which lowers them, move real wages in opposite directions and largely cancel.
- **Single-shock job figures are sensitive.** The freeze costs *more* jobs with sticky wages, because falling prices raise real wages; oil costs *fewer*, because rising prices erode real wages. Poverty counts barely move, because the household income changes are similar.

## 5. Recommendations

1. **Keep the short-run closure** (low- and medium-skill unemployment), now with evidence behind it (§1).
2. **Add `wage="nominal"` to "0.3 recommended"** before 0.3 is used for citation. It matches Philippine wage setting (§2) and removes the sign puzzle (§3). It would not change the published 0.2 results.
3. **For the published figures**, attach a range to single-shock job numbers. Freeze, low-skill employment: −1.8% (published) to −2.7% (sticky wages). Oil +20%: −1.1% to −0.3%. The combined-shock figures need no change.

## 6. Follow-ups done on 16 Oct 2026

**What other Philippine CGE studies assume about the labour market.** All were opened; page numbers are PDF pages, and the files are in `Infinity GEM/a reference copy (not distributed) and a reference copy (not distributed).

| Study | Labour closure | Page |
|---|---|---|
| Cororaton (2000), PCGEM, PIDS DP 2000-33 | "a full employment model" (neoclassical, price clearing) | p. 2 |
| Briones (2015), Philippine Regional General Equilibrium Model, *Philippine Review of Economics* 52(1) | Factor markets clear in each region (full employment) | p. 16 (eqs. 45-46) |
| Briones et al. (2023), food affordability to 2030, PIDS DP 2023-23 | Agricultural and industry-service labour each clear at a market wage (full employment) | p. 24 |
| Corong and Horridge (2012), PHILGEM, CoPS G-227 | ORANI-style closure. Short run: wages indexed to the CPI, employment adjusts (variant: average nominal wage fixed). Long run: aggregate employment fixed, the wage adjusts | p. 59 |
| World Bank (2025), MANAGE-WB, PRWP 11258 | Market-clearing wages, optionally with an upward-sloping labour supply and segmented labour markets | p. 9 |
| Cororaton (2026), DLSU-AKI Policy Brief 2026-04-066 (oil) | Not stated in the paper | — |

**Reading:**
- **Most Philippine CGE work assumes full employment.**
- **PHILGEM's short-run closure is the exception.** It is close to Infinity GEM's earlier rule (real wage fixed, employment adjusts).
- **Infinity GEM 0.3.7 sits between the two.** Its short-run rule is a wage curve whose slope is set from Okun's law on PSA data (check WC1; `outputs/okun_20261016.md`, `outputs/wage_curve_calibration_20261016.md`).
- **Full employment would show no job losses in 2026.** PSA's LFS shows unemployment up from 3.9% (Aug 2025) to 5.3% (Aug 2026).

**The disaster job sign.**
- **How it was run:** `5_disaster_job_sign.py` (output in `out_5_disaster_job_sign.txt` and `disaster_job_sign.csv`), on the static short-run CGE with the 0.3 recommended settings. The shock is the same as on 14 Oct: ₱47.44 bn of capital destroyed.

| Wage rule | Damage only: low-skill jobs | Damage + rebuilding |
|---|---|---|
| Indexed to the CPI | +0.07% | +0.47% |
| Fixed in pesos | +0.38% | +0.98% |

- **Not the wage rule.** Jobs rise under both rules, and more with peso-fixed wages (prices rise, so real pay falls).
- **The cause is how damage enters.** The damage lowers capital stocks (`kscale`) while labour is idle at a fixed wage. Firms then put labour in place of the lost capital, at the CES substitution elasticity. In a real disaster, destroyed farms, roads and buildings cannot be replaced by more hands within the year, so the I-O sign (−49.3k) is closer for the first year.
- **Recommendation** (an engine change, so not made):
  - For a future disaster shock, enter the damage as a productivity loss in the affected industries (as El Niño enters, `tfp_scale`), or with low capital-labour substitution in the damaged sectors.
  - Add rebuilding spending only from the year it is budgeted.
  - Check the result against the empirical literature on typhoons and household incomes in the Philippines before use (not opened today).
- **No published number is affected.** Typhoons are not in the combined run, because 2025 and 2026 were not above a normal year (`outputs/typhoons_normal_year_20261016.md`).

## 7. The Okun target's evidence (18 Oct 2026, about 12:15-12:45 PM)

**The question.** The wage curve's slope is set so that the model's 2026 labour input falls by e times its own output effect. e = 0.713 is the elasticity of the employment-to-population ratio to real GDP, on quarterly PSA data for 2006-2026 (`preshock/okun.py`). It is identified by the 2020-2021 quarters: without them it is 0.154 (not significant), and in 2006-2019 it is −0.23. The 2026 scenarios of 17 Oct 2026 say so. The question is whether the target has evidence outside COVID.

**Philippine literature (opened and read; PDFs: reference copies, not distributed):**
- **Felipe and Estrada (2018), ADB Economics WP 542** (saved 18 Oct), annual 1957-2017:
  - unemployment barely responds to growth: −0.086 per point of growth (static, significant at 10%), long-run ARDL −0.12, most other specifications not significant (Tables 1-2);
  - total underemployment RISES with growth (+0.28 static, +0.75 long-run gap ARDL; Table 3). The authors trace this to the survey: people already working 40+ hours may declare themselves underemployed;
  - visible underemployment (under 40 hours), 1987-2017: −0.113 static (10%), otherwise not significant (Table 4);
  - they cite Paqueo et al. (2014): an employment elasticity to output of 0.60 for 1956-2010. That is a long-run growth elasticity, not a cyclical one.
- **Corpus, Epetia and Debuque-Gonzales (2025), BSP DP 2025-17**, regional panel 2018Q1-2023Q3:
  - wage growth responds to unemployment only during COVID (−1.05 pp per standard deviation of regional unemployment, significant) and not before or after;
  - the response is asymmetric (rising unemployment only) and strongest for men and the less educated.
- **Reading:** outside COVID, Philippine labour markets adjust neither through open unemployment nor through pay. The adjustment runs through hours, underemployment and informal earnings, as the 2026 scenarios already note.

**New estimates: hours and the informal margin** (`preshock/okun_hours.py`, `outputs/okun_hours_20261018_*.md`). Data: PSA OpenSTAT 0191B3FHRS1 (mean hours worked), 0171B3FVIS1 (visibly underemployed), 0011B3FKEI1 (levels) and 0131B3FEMP5 (class of worker), downloaded 18 Oct by `data/raw/lfs/download_lfs_hours_data.py`. Same method as `okun.py`; its persons row reproduces `okun.py` exactly.

| Margin (year-on-year, on ln real GDP) | 2006-2019 | 2006-2026 without 2020-21 | 2006-2024 without 2020-21 | All quarters |
|---|---|---|---|---|
| Persons (employment-to-population) | −0.23 (0.14) | 0.15 (0.27) | −0.01 (0.25) | 0.71 (0.11) |
| **Total hours per person 15+** | 0.23 (0.20) | **0.60 (0.30)** | 0.61 (0.33) | 1.31 (0.15) |
| Mean hours of the employed | **0.46 (0.17)** | **0.45 (0.20)** | **0.63 (0.19)** | 0.60 (0.06) |
| Visible underemployment rate, pp | **−0.16 (0.07)** | **−0.20 (0.07)** | **−0.22 (0.08)** | −0.27 (0.03) |
| Informal share of employment, pp | −0.19 (0.13) | −0.04 (0.15) | −0.17 (0.14) | −0.15 (0.03) |

Newey-West standard errors in brackets; bold = significant at 5%.

**What this means for the target:**
- **The model's labour input is persons × hours**, so its data counterpart is total hours, not persons. On hours the no-COVID elasticity is 0.60 (s.e. 0.30), close to the 0.71 now used. The persons-only 0.15 understates the response of labour input.
- **The intensive margin is the robust one:** mean hours respond with 0.45-0.63 in every sample, 2006-2019 included. Visible underemployment moves the same way.
- **Before 2020 the hours elasticity is 0.23** (not significant), because persons moved against GDP in 2006-2019. That gives a lower bound.
- **Recommendation (technical):** restate the target as "total hours, 2006-2026 without COVID: 0.60 (range 0.23 to 0.94)". This keeps the central calibration close to where it is and removes the COVID dependence. Effect on the 2026 scenarios: see the model rows below.

**The pay side.** At e = 0.71 the calibrated curve implies a pay elasticity to the unemployment rate of −0.29 (Blanchflower-Oswald: about −0.1), and BSP DP 2025-17 finds pay unresponsive outside COVID. The wage curve therefore stands in for more than literal pay cuts: labour hoarding and informal earnings that fall with hours. Report it that way; the sensitivity table already shows the "fixed real wages" and "whole observed fall" rows as bounds.

**Not used: an AI search summary (18 Oct).** Its general point (COVID drives the coefficient; the informal sector absorbs) matches the papers. Its numbers do not:
- "ADB … 0.15 and 0.28": not in WP 542. There 0.28 is the coefficient for total underemployment, and it is positive;
- "0.70-0.90+ with COVID": no source given; our own 0.71 is a different measure;
- "SSRN / Reserds 'Okun paradox'": not located; not opened.

**Model rows** (`scenarios/okun_hours_sensitivity.py`, `outputs/okun_hours_sensitivity_20261018_1241.md`; the combined shocks, public capital low, MicroLink's default fuel-split map):

| Wage-curve target | beta | Implied pay elasticity | GDP 2026 | Employment gap 2026 | New poor 2026 | New poor 2027 |
|---|---|---|---|---|---|---|
| Persons, all quarters, 0.713 (the central 2026 setting of 17 Oct 2026) | 7.14 | −0.29 | −1.22% | −1.18 pp | 3.16 M | 1.76 M |
| **Total hours, 2006-2026 without COVID, 0.600** | 8.89 | −0.36 | −1.18% | −0.97 pp | **3.13 M** | 1.75 M |
| Total hours, 2006-2019, 0.233 (lower bound, not significant) | 26.47 | −1.07 | −1.05% | −0.35 pp | 3.07 M | 1.72 M |

**Effect on the 2026 scenarios:** none that matters. On the hours target the 2026 poverty result moves by about 1% against the 17 Oct 2026 target (same map), and GDP falls 1.18% against 1.22%. The central numbers stand, on a non-COVID basis.

## Still open (as of 14 Oct; the three items below are now done, see section 6)

- **What other Philippine CGE studies assume** (Cororaton; PIDS; the World Bank's MANAGE). Not opened today, so nothing is claimed about them here.
- An Okun's-law estimate from the LFS and the national accounts, as a second check on how employment responds.
- The disaster job sign (CGE +22.6k vs I-O −49.3k note). This is a separate question about how capital destruction enters (`kscale`). It is likely affected by the wage rule too: test it with `wage="nominal"`.

## Files

| File | What |
|---|---|
| `1_signflip_by_upgrade.py` → `out_1_…`, `signflip_table.csv` | The four 0.3 upgrades, one at a time (reads the released 0.3.3) |
| `2_signflip_by_elasticity_and_activity.py` → `out_2_…` | sigma_va vs trade elasticities; job change by activity (reads the released version) |
| `3_wage_closure_sensitivity.py` → `out_3_…`, `wage_closure_sensitivity.csv` | §4 table (needs the `wage=` option) |
| `4_lfs_evidence.py` → `out_4_…` | §1–2 evidence from `data/raw/lfs/` (two new PSA tables, in `data/DATA_INVENTORY.md`) |
