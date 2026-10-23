# 11 The New Keynesian DSGE (Stage 3, and the money block): a guide

**Version 2, 20 Oct 2026**. Version 1 (19 Oct, about 11:35 AM, the 2002-2019 model) is not included.

**Not for citation:** research code in `research/dsge/`, not used by any published Infinity GEM result. The milestone-by-milestone record of the development, with every number and file, is not included; `research/dsge/README.md` lists the code. This chapter says what the model is for, how it is built and estimated, what it shows, how it connects to the CGE, and its limits.

Work on the DSGE started on 19 Oct 2026.

**What changed since version 1:**
1. **New candidate model.**
   - `soe_htmu.py` adds a domestic cost-push shock (food and fuel supply shocks).
   - It is estimated on 2002-2026, with the COVID quarters skipped and GDP seasonally adjusted.
   - Three chains have converged.
2. **"100 bp" is now quoted on a defined path,** the policy rate held 1 point higher for a year. A shock to the model's rule brings further tightening with it, so it is not the same experiment.
3. **Oil:** supply shocks are separated from world-demand-driven oil prices (milestone 21).
4. **Investment's response to interest rates** is pinned down only loosely by Philippine data: the capital DSGE with sticky wages (milestone 25) gives 1.43 (90% band 0.72-2.23). Since 23 Oct 2026 the CGE link uses 1.5, with 0.7 low and 2 high (it used a matched 2 before).

## 1. What it is for

Infinity GEM's CGE answers "who gains and who loses, by industry and household". But it has no money, no interest rate and no expectations of inflation.

A DSGE (dynamic stochastic general equilibrium model) is the standard tool central banks use for exactly that: how a change in the BSP's policy rate, or a shock to world prices or the peso, moves output, inflation and the exchange rate over the following quarters. The project's design uses the two together:
- the **DSGE** (quarterly, a few aggregates) says how much output, inflation, interest rates and the peso move;
- the **CGE** (yearly, 40 industries, 10 household groups) takes those moves and says which industries and households are hit, and how many people fall into poverty.

## 2. The model in plain words (`soe_htmu.py`)

A small open economy, built up in steps that are each tested (milestones 1-19):
- **Households.**
  - About 60% of them are *hand-to-mouth*: they spend their current income, because they have no savings or credit to smooth with.
  - The rest plan ahead. They have habits (consumption changes gradually) and partly *adaptive expectations*: about 70% of their expectation is last quarter's value.
- **Firms** set prices in pesos and change them only now and then.
  - Domestic prices are very sticky (the Phillips curve is flat).
  - Import prices change about every two to three quarters.
  - A few price setters copy last quarter's trend.
- **Cost-push shocks** (new in version 2): food and fuel supply shocks can raise domestic inflation directly.
  - Without them the model could explain Philippine inflation only through implausibly large swings in productivity.
  - That was the warning sign in version 1.
- **The rest of the world** sets world output, world inflation and the world interest rate. The peso links them, with a risk premium that can move on its own.
- **The BSP** sets its policy rate by a rule:
  - it raises the rate when inflation or output rise (inflation coefficient about 1.3), and responds a little to the peso;
  - it moves very gradually (smoothing 0.95);
  - a policy surprise is followed by further moves in the same direction, as in the data.

## 3. Estimation: data, method and the one judgment call

- **Data** (`ph_data.py`, files on disk):
  - quarterly real GDP growth and CPI inflation (PSA);
  - the BSP policy rate and the peso-dollar rate (BIS);
  - 2002Q1-2026Q2.
- **Two data treatments:**
  - The COVID quarters (2020-2021) are left out: the Kalman filter skips them.
  - GDP is seasonally adjusted (STL), because PSA's unadjusted series keeps a drifting seasonal pattern that the usual quarter means do not remove.
- **Method:** Bayesian estimation (Kalman filter likelihood, priors, random-walk Metropolis), as central banks do (An and Schorfheide 2007; Herbst and Schorfheide 2015). Three chains have converged (largest R-hat 1.012).
- **The judgment call: how strongly does BSP policy move inflation?**
  - On the data alone the model says implausibly strongly: inflation would fall about 8 points per point of tightening. Yet that fits the data only about 3 log points better than the evidence-based version. The data barely pin transmission down.
  - So the project collected the independent evidence (milestone 12):
    - the BSP's PAMPh (WPS 2020-12);
    - the BSP's 2009 DSGE (WPS 2009-01);
    - the BSP's 2021 VAR note (RN 2021-02);
    - Infinity GEM's own local projections.
  - These put the fall in inflation at about 0.2-0.5 points per point of first-year tightening.
  - The model adds that as a *system prior* on transmission strength (Andrle and Benes 2013), with a looser one on output.
  - **The output result is not imposed:** without the output prior, output responds the same (−0.33 against −0.31 per point).

## 4. What it shows

Converged estimates (20 Oct 2026, 3:03 AM; three chains; `outputs/dsge_rhat_20261020_0303.md`, `outputs/dsge_posterior_strength_20261020_0304.md`):

| | Posterior mean |
|---|---|
| Hand-to-mouth share of households | 0.60 (5-95%: 0.36-0.79) |
| Weight on last quarter in expectations | 0.71 |
| BSP's response to inflation | 1.34 |
| BSP's interest-rate smoothing; persistence of policy surprises | 0.95; 0.51 |
| Inflation fall per pp of first-year tightening | median 0.37 (0.24-0.50); 91% of draws inside the evidence band |
| Output (GDP growth) fall per pp | median 0.30 (0.22-0.41); PAMPh about 0.19 |

**Two ways to say "100 bp"** (milestone 19c; `outputs/dsge_rate_path_review_20261020_0905.md`): 2026 output, medians with 5-95% in brackets.

| Rate path | PAMPh (BSP) | QPM calibrated to PAMPh | the project's DSGE |
|---|---|---|---|
| A policy surprise of 1 point, then each model's own rule | −0.22% | −0.24% | −1.05% (−1.44 to −0.75) |
| PAMPh's own rate path (1 point, back to zero in three quarters) | −0.22% | −0.22% | −0.40% (−0.56 to −0.29) |
| **1 point held for a year, then back** | | −0.43% | **−0.86% (−1.19 to −0.63)** |

Reading:
- After a surprise, the project's model keeps raising the rate for two quarters: about 1.2 points on average in 2026 and 0.7 in 2027, as the BSP's rate does in the data. PAMPh's rate falls back at once (0.3 point on average in 2026). That difference explains most of the gap.
- On the same rate path, the project's model gives about twice PAMPh's output effect.
- **Quote "1 point held for a year", which is the same experiment in every model.**

## 5. The link to the CGE

`scenarios/qpm_cge_link.py` takes the DSGE's (or the QPM's) yearly output gap, real interest rate and real exchange rate into the CGE:
1. **The interest-rate channel the CGE lacks.** Real investment demand falls by θ% per point of real interest rate. θ is set so the CGE's 2026 GDP effect equals the macro model's.
2. **The peso** moves with the macro model's real exchange rate.
3. **Labour hoarding** is on, as in the 2026 scenarios of 20 Oct 2026.

**The policy rate 1 point higher for a year** (`path=hold4`; `outputs/qpm_cge_link_20261020_0914_*_pathhold4.md`):

| | 2026 GDP | 2026 new poor | 2027 new poor |
|---|---|---|---|
| QPM calibrated to PAMPh | −0.43% | about 0.35 million | about 0 |
| the project's DSGE | −0.85% | about 0.71 million | about 0 |

So a year of 1-point-tighter policy costs roughly **0.4-0.9% of 2026 GDP and 0.35-0.7 million new poor**, depending on whose transmission is right. The night's figure (+0.86 M for "100 bp") includes the rule's follow-up tightening.

**θ, investment's sensitivity to the real interest rate** (milestone 20b, `outputs/dsge_investment_response_20261020_0924.md`):
- Philippine data on 2002-2026 do not identify it.
- After a measured tightening, CPI falls but GDP and investment rise (the "output puzzle": the BSP tends to tighten on news of strong demand).
- Until market-based policy surprises are available, θ comes from the matching above: 1.9 (PAMPh's transmission) to 3.3 (the project's DSGE); about 2 was the central value until 23 Oct 2026. **Since then the central value is 1.5, with 0.7 low and 2 high:** the capital DSGE with sticky wages, estimated with PSA's investment data (milestone 25, the best fit of every version), puts year-1 θ at 1.43, 90% band 0.72-2.23 (`research/dsge/README.md`, 23 Oct).

**An interest rate in the CGE itself** (opt-in: `closure="interest"`): in long-run years a real interest rate can now clear savings and investment, as in the World Bank's MANAGE model (check IR1). The first research run on the 2026 scenarios' case is in `outputs/interest_closure_check_*`.

## 5b. Oil and the BSP's response

The oil models (`soe_oil.py`, `soe_oilu.py`, `soe_oilw.py`) treat oil:
- as part of what households buy (3.7% of the CPI: LPG, kerosene and vehicle fuels, PSA 2018 weights);
- as an input to production (3% of costs, Infinity GEM's own SAM);
- with world prices passed through at once;
- with little substitution in the short run.

They are estimated with Dubai crude as an extra data series.

**Why milestone 21 was needed.**
- With the cost-push shock added (soe_oilu), an oil-price rise *raised* Philippine output. Over 2002-2026, oil-price rises mostly came with world booms that also lifted Philippine growth: a single oil shock mixes oil supply with world demand (Kilian 2009).
- `soe_oilw.py` separates the two: the oil price = a supply part + a part that moves with world output. World output is now observed: the average real GDP growth of the United States, the euro area and Japan (FRED).
- The 2026 disruption is then a pure supply shock.

**What milestone 21 found** (20 Oct 2026; `research/dsge/README.md`):
1. **World demand is identified.** A 1% world-output boom raises the real oil price about 7% (90%: 3-11%). The model converged on three chains.
2. **As estimated, an oil supply shock still raises Philippine output** (+0.6% in the first year). The cause is the flat domestic Phillips curve: domestic prices change about every five years in the estimate, so fuel costs barely reach prices, home goods become relatively cheaper, and demand switches to them. The world-demand mix-up was not the main cause.
3. **With price stickiness from the BSP's micro price data,** the oil supply shock is contractionary as expected. The micro data (WPS 2020-02) show prices changing about every 10 months, a quarterly Calvo of 0.73. For a shock the size of 2026's (+36% in logs):
   - **the BSP's estimated response** (+0.7 point on the policy rate in the first year) lowers headline inflation from about +3.8 to +2.7 points and core from +2.6 to +1.6;
   - **it costs about 0.16% of output in the first year and 0.18% in the second.**
4. **Through the CGE,** that response adds about **0.15-0.45 million poor in 2026, about 0.3 million at the central θ** (0.34 M with the Calvo parameter at 0.73, 0.28 M at 0.85; 23 Oct 2026). The answer depends almost entirely on how strongly investment responds to interest rates (Calvo 0.73): +0.17 M at θ 0.7, **+0.34 M at θ 1.5**, +0.45 M at θ 2 (`outputs/qpm_cge_link_20261023_0859_*_thfix0.73.md`; before 23 Oct the range was θ 0.55-3.3: +0.13 M at 0.55, +0.74 M at 3.3). In exchange, inflation is about a point lower.

**Status: indicative only.**
- The micro-calibrated model fits the data about 16 log points worse than the estimated one.
- Import-price stickiness and the intertemporal elasticity sit at their bounds.
- It rests on one chain.

So no DSGE oil number is ready for use yet. The 19 Oct figures (0.02-0.08% of output, about 46,000 poor) came from a model without the cost-push shock and are superseded.

**Next:** more chains of the micro-calibrated model; a middle case (Calvo 0.85); or let fuel costs pass through outside the Calvo block (a flexible-price, energy-intensive sector).

**Model uncertainty behind §5b's numbers (21 Oct 2026):** the oil model's posterior has a second mode (expectations fully model-consistent instead of mostly adaptive) that the chains never visit; it carries far less posterior mass (section 5e; about 22 log points less), so the numbers above stand, but at that mode the BSP's response to the 2026-sized oil shock would cost 1.12% of output in year 1 instead of 0.24% (`oil_policy.py ... src=smc`; `outputs/dsge_oil_policy_20261021_0159_oilw_long_stl_thfix0.85_smc.md`). Quote §5b's ranges with that in mind.

## 5c. Two checks made before any monetary number is cited (20 Oct 2026, evening)

**1. The poverty figures already net the price benefit.** The question (20 Oct 2026, evening) was whether the "+0.1 to +0.75 million poor" from the BSP's oil response count only the output cost. They do not: the poor are counted from each FIES family's own basket inflation and its group's nominal income change (`infinity_gem.microlink.MicroLink.poverty`), so the lower prices the tightening brings are netted against the income it costs. `scenarios/bsp_oil_response_netting.py` separates the parts (`outputs/bsp_oil_response_netting_20261020_2213_*thfix0.73.md`, four chains pooled, and `_2204_*thfix0.85.md`, three chains pooled). At θ 2 (the central value until 23 Oct 2026, now the high case), 2026:

| | Calvo 0.73 | Calvo 0.85 |
|---|---|---|
| incomes and prices (the published count) | +0.45 M | +0.38 M |
| incomes only (prices held at the baseline) | +1.17 M | +1.05 M |
| prices only (nominal incomes held) | −0.68 M | −0.63 M |
| consumer prices 2026 | −1.27% | −1.18% |

**At the central θ 1.5 (23 Oct 2026; `outputs/bsp_oil_response_netting_20261023_0903_*thfix0.73.md`, `_0910_*thfix0.85.md`):** the published count is +0.34 M (Calvo 0.73) and +0.28 M (Calvo 0.85); incomes only +0.96 M and +0.88 M; prices only −0.59 M and −0.56 M. At θ 0.7, the low case: +0.17 M and +0.15 M. The gross income loss alone would add about three times the published count; the lower prices alone take out about 60% of it. The peso channel (the DSGE's stronger peso) carries almost all of the price fall in 2027 but little of the poverty effect; the investment channel carries the poverty effect. The three counts do not add exactly because families cross the line one at a time. What is not in either model: any second-round benefit of better-anchored expectations.

**2. The estimated rule against the BSP's actual 2026 decisions** (`research/dsge/rule_check_2026.py`; `outputs/dsge_rule_check_2026_20261020_2140_*thfix0.73.md`, `_2141_*thfix0.85.md`). The Kalman smoother reads the 2002-2026 data through the model and gives, quarter by quarter, the rate the rule prescribes and the policy "shock" the rule does not explain:
- in the first half of 2026 the BSP's rate (4.33% and 4.58%, quarterly averages) sat about half a point below the rule's prescription (4.9-5.1%): policy shocks of −1.0 to −1.2 times their usual size, inside the sample's range (95th percentile 1.5; the largest, 2007Q3, −4.3);
- by the third quarter (4.92%) the BSP had raised the rate to about the level the rule prescribed in the second quarter: the same response, about a quarter later;
- the rule's own response to the 2026-sized oil shock (+0.6 to +0.8 point in the first year) is the size of the BSP's 2026 increases (4.25% in March to 5.0% in August).

So the rule is consistent with the BSP's 2026 behaviour in size and direction, with a lag of about a quarter. Both checks are recorded; the monetary figures remain research, not for citation, for the reasons in section 6.

## 5d. The rule inside the dynamic model (built 20 Oct 2026, evening)

**What it is.** `DynamicCGE.monetary_scenario()`, or the setting `DynamicCGE(monetary={...})`, closes the loop the CGE link of section 5 leaves open: the CGE's own gaps of each year (output; inflation in the short-run years, where the peso is the numeraire; the peso's depreciation) feed a policy rule within the year, the rule's rate less expected inflation scales real investment demand by exp(−θ r/100), and the whole path is solved as a fixed point (a damped step, then a safeguarded secant step; tolerance 0.01 pp; four to seven iterations on the 2026 scenarios' case). Coefficients by name from `infinity_gem.monetary.rule`: "pamph" (the QPM's PAMPh match: smoothing 0.72, inflation 2.05, output 0.10), "dsge" (the candidate soe_htmu: 0.95, 1.34, 1.27 pp a year per % of output gap, depreciation 0.13), "oil0.85" and "oil0.73" (the oil model: 0.95, 1.40-1.52, 1.20-1.50, 0.14-0.16); nothing typed in. Suite check MP1. The design note's §6 records the four departures from the design (the rule acts within the year; the quarterly rule is integrated exactly over the year; expectations are an option, "adaptive" by default; the peso moves only by an imposed scale) and why.

**What it gives on the four 2026 shocks** (`scenarios/monetary_check.py`; `outputs/monetary_check_20261023_0928_own.md`, 23 Oct 2026; Infinity GEM's own SAM, hoarding 0.85, **θ 1.5**, adaptive expectations):

| | no rule (the 2026 scenarios) | oil0.85 rule | oil0.73 rule | dsge rule | PAMPh-type rule |
|---|---|---|---|---|---|
| policy-rate gap 2026 / 2027 (pp) | 0 / 0 | −1.04 / −1.34 | −0.90 / −1.11 | −0.86 / −1.10 | −1.44 / −0.11 |
| GDP 2026 / 2027 / 2030 (%) | −2.91 / −1.82 / −0.67 | −2.87 / −1.66 / −0.36 | −2.90 / −1.70 / −0.41 | −2.90 / −1.70 / −0.41 | −2.80 / −1.93 / −0.63 |
| new poor 2026 / 2027 (M) | 3.41 / 1.79 | 3.39 / 1.61 | 3.42 / 1.64 | 3.43 / 1.64 | 3.36 / 1.95 |
| 2025-2030 loss (₱ bn) | 2,618 | 2,301 | 2,369 | 2,374 | 2,548 |

With the oil0.85 rule, θ 0.7 / 2 give a loss of ₱2,466 / ₱2,201 bn. θ 2 reproduces the 20 Oct run exactly (`outputs/monetary_check_20261020_2303_own.md`, then the central case; there θ 0.55 / 3.3 gave ₱2,498 / ₱1,961 bn). "foresight" expectations: not solved at θ 1.5 either (in 2026 the employment cap did not settle; recorded, not used).

**Reading.** In the CGE's own reading, the combined 2026 shocks are a demand slump with a LOWER price level in 2026 (consumer prices −1.05% in the 2026 scenarios' run: under the wage curve the public-works cut outweighs oil) and a large negative output gap, so a rule that reads the CGE's gaps cuts: 2026 barely changes, 2027-2030 are cushioned as investment recovers. A PAMPh-type rule, with little weight on output, cuts in 2026 and tightens in 2027, when the CGE's prices recover (inflation gap +0.6 to +1.2 pp), and makes 2027 worse. This is the opposite sign to the oil-only link of section 5b (+0.1 to +0.75 million poor from the BSP's tightening), and the difference is not an error: the DSGE sees the oil shock alone, with observed inflation dominating; the CGE sees all four shocks with the public-works cut dominating and its 2026 price level falling, against the 5.4% inflation actually observed in January-September 2026. So the closed loop's answer is governed by the CGE's short-run price response, which understates 2026 inflation (the sticky-price sensitivity is the related sensitivity). Until that is resolved, the oil-only link is the better guide to what the BSP's actual 2026 response cost, and neither number is for citation.

## 5e. Checks of the estimation and two model extensions (21 Oct 2026, overnight)

**A second sampler.** `research/dsge/smc.py` estimates the same posteriors by sequential Monte Carlo (Herbst and Schorfheide 2014): particles drawn from the prior, the likelihood switched on gradually, resampling and random-walk moves at each stage. It needs no mode search and no earlier chain, so agreement with the Metropolis chains is evidence that both found the posterior. **On the candidate they do not agree:** the SMC settles at a Calvo parameter of 0.80 (prices fixed about five quarters) where the chains sit at 0.95 (about five years), with the same transmission strength. The reason is a flaw in the system prior, not in either sampler: the prior on transmission strength divides the model's inflation response by the first year's cumulative policy-rate response, and between the two regions that denominator passes through zero, so the prior's penalty forms a wall that neither sampler crosses (`research/dsge/README.md`, 21 Oct). The posterior is therefore bimodal; the chains' mode has the higher density. Until the prior is restated in a form that cannot be singular, every parameter table in this guide should be read as "the mode the chains found", while the transmission numbers and the CGE links, which the prior pins, are the same in both modes.

**Robustness and a forecast check.** `research/dsge/robustness_candidate.py` puts the candidate's posterior across specifications in one table (`outputs/dsge_robustness_candidate_*`): the system prior on CPI strength alone changes nothing; the data alone put the Calvo parameter at 0.89 with an explosive transmission ratio (the same singularity); raw instead of STL-adjusted GDP gives the same structure at a far lower likelihood. `research/dsge/forecast_check.py` estimates the model to 2023Q4 (`estimate_rot.py ... end=2023Q4`; `ph_data.py adjust_end=`) and compares its forecasts for 2024Q1-2026Q2 with what happened, against the unconditional mean and an AR(1) (results in `outputs/dsge_forecast_check_*` once the 2023Q4 chain has run).

**Two extensions (model and tests only).** `soe_oilf.py` (milestone 22) lets oil reach the CPI through flexible-price, energy-intensive services (passenger transport and electricity, 9.1% of the basket, fuel cost share 0.19 from Infinity GEM's own SAM) instead of only through the Calvo sector: the question is whether an oil supply shock is contractionary with the Calvo parameter estimated rather than calibrated (section 5b); its estimation was started overnight. `soe_htmk.py` (milestone 23) adds capital, investment with Smets-Wouters adjustment costs, Tobin's q and variable utilisation to the candidate, so that a tightening lowers investment inside the model (2.9% against consumption 0.5% at the posterior mean) and the CGE link no longer has to borrow an investment response; its estimation is for the morning.

## 6. Limits (read before using any number)

- **Research, not for citation.** Nothing here has been reviewed outside the project. The system prior is a documented judgment.
- **Transmission is weakly identified by the data** (section 3). The evidence band anchors it, so results move with that evidence.
- **Small model:**
  - five or six observed series and six or seven kinds of shocks;
  - the domestic Phillips curve is flat (very sticky domestic prices), a common result in estimated models (the micro-macro gap in price durations);
  - the policy rate is treated as stationary around its average.
- **No investment in the DSGE.** The interest-rate channel to investment comes from the CGE link's θ, which Philippine data cannot pin down (section 5).
- **The link is top-down:** the DSGE drives the CGE, not the other way round. Over two years this is the standard macro-micro approach (Bourguignon, Robilliard and Robinson 2005).

## 7. Files

**The Simulator page "Money and the BSP (research)"** (`app/simulator.py`, added 20 Oct 2026) shows the newest saved results of this guide's §4-§5b in plain words: the 100 bp rate paths by model, the 100 bp held for a year through the CGE, the BSP's response to the 2026 oil shock and its CGE link by θ. It solves nothing; rerun the scripts below to refresh it. Every table on it names its file and carries the research warning.

`research/dsge/` (see its README):
- **The models:**
  - `soe_htmu.py` (candidate) and its predecessors `soe_htm.py`, `soe_rot.py`, `soe_med.py`, `soe_lcp.py`, `soe_nk.py`, solved by `klein.py`;
  - oil: `soe_oil.py`, `soe_oilu.py`, `soe_oilw.py`.
- **Estimation and diagnostics:**
  - `estimate_rot.py` (e.g. `model=htmu prior=ratio sample=long gdp=stl`);
  - `rhat.py`, `chain_logpost.py`, `posterior_strength.py`;
  - `transmission_benchmarks.py` (evidence), `rate_path_review.py` (milestone 19c), `investment_lp.py` and `investment_response.py` (θ), `oil_policy.py`.
- **The QPM block:** `qpm.py` and `pamph_targets.py`.
- **The two checks of section 5c (20 Oct 2026, evening):** `rule_check_2026.py` (the rule against the BSP's 2026 decisions) and `scenarios/bsp_oil_response_netting.py` (the price benefit and the income loss separated).
- **The rule inside the dynamic model (section 5d):** `infinity_gem/dynamic.py` (`DynamicCGE.monetary_scenario`, `monetary_gaps`, `annual_rule`; the `monetary=` setting), `infinity_gem/monetary.py` (`rule("pamph" | "dsge" | "oil0.73" | "oil0.85")`, coefficients read from the QPM's match or the saved chains), `scenarios/monetary_check.py` (the 2026 shocks with the rule; 21 Oct: `sticky=`, `energy=`, `observed=` variants); suite check MP1. **Why it cuts, and what the data say:** a review note (not included) (21 Oct 2026): the CGE's 2026 inflation gap is negative where the data's is +1.6 points; sticky prices and the energy bundle halve the gap but keep its sign; the closed loop stays research-only.
- **Section 5e (21 Oct 2026):** `research/dsge/smc.py` and `test_smc.py` (the SMC sampler); `chain_logpost.py` (which region holds the density); `robustness_candidate.py`; `forecast_check.py` (with `estimate_rot.py end=` and `ph_data.py adjust_end=`); `soe_oilf.py` and `test_milestone22.py`; `soe_htmk.py` and `test_milestone23.py`; a reference copy (not distributed) (the BSP's model papers in a reference library, one line each).
- **Tests:** `test_milestone*.py`. Suite check X3 runs milestones 1-3, 5, 6, 8, 10, 11, 15, 18, 19 and 21 and the Kalman test.
- **Outputs:** `outputs/dsge_*`, `outputs/qpm_cge_link_*`, `outputs/bsp_oil_response_netting_*`, `outputs/monetary_check_*`.

## References

- Adolfson, M., S. Laseen, J. Linde and M. Villani (2007). "Bayesian Estimation of an Open Economy DSGE Model with Incomplete Pass-Through." *Journal of International Economics* 72(2).
- Andrle, M., and J. Benes (2013). "System Priors: Formulating Priors about DSGE Models' Properties." IMF Working Paper 13/257.
- An, S., and F. Schorfheide (2007). "Bayesian Analysis of DSGE Models." *Econometric Reviews* 26(2-4).
- Bilbiie, F. O. (2008). "Limited Asset Markets Participation, Monetary Policy and (Inverted) Aggregate Demand Logic." *Journal of Economic Theory* 140(1).
- Bourguignon, F., A.-S. Robilliard and S. Robinson (2005). "Representative versus Real Households in the Macroeconomic Modeling of Inequality." In *Frontiers in Applied General Equilibrium Modeling*. Cambridge University Press.
- BSP (2009). "Macroeconomic Model for Policy Analysis and Insight (a DSGE Model for the BSP)." BSP Working Paper Series No. 2009-01.
- BSP (2020). Alarcon, S. J., P. R. Alhambra, R. Amodia and D. Bautista. "Policy Analysis Model for the Philippines." BSP Working Paper Series No. 2020-12.
- Cleveland, R. B., W. S. Cleveland, J. E. McRae and I. Terpenning (1990). "STL: A Seasonal-Trend Decomposition Procedure Based on Loess." *Journal of Official Statistics* 6(1).
- Durbin, J., and S. J. Koopman (2012). *Time Series Analysis by State Space Methods*, 2nd ed. Oxford University Press.
- Federal Reserve Bank of New York (2026). *DSGE.jl: The New York Fed DSGE Model (Version 1002)*, code and model documentation (`DSGE_Model_Documentation_1002.pdf`). https://github.com/FRBNY-DSGE/DSGE.jl (accessed 20 October 2026; saved in a reference copy (not distributed), with a source note on what it is used for: a methods and software reference for conditional rate paths, sequential Monte Carlo estimation and a cross-check of the project's likelihood and sampler; not a model to adopt).
- Gali, J., and M. Gertler (1999). "Inflation Dynamics: A Structural Econometric Analysis." *Journal of Monetary Economics* 44(2).
- Gali, J., J. D. Lopez-Salido and J. Valles (2007). "Understanding the Effects of Government Spending on Consumption." *Journal of the European Economic Association* 5(1).
- Gali, J., and T. Monacelli (2005). "Monetary Policy and Exchange Rate Volatility in a Small Open Economy." *Review of Economic Studies* 72(3).
- Herbst, E., and F. Schorfheide (2015). *Bayesian Estimation of DSGE Models*. Princeton University Press.
- Jorda, O. (2005). "Estimation and Inference of Impulse Responses by Local Projections." *American Economic Review* 95(1).
- Kilian, L. (2009). "Not All Oil Price Shocks Are Alike: Disentangling Demand and Supply Shocks in the Crude Oil Market." *American Economic Review* 99(3).
- Klein, P. (2000). "Using the Generalized Schur Form to Solve a Multivariate Linear Rational Expectations Model." *Journal of Economic Dynamics and Control* 24(10).
- Leeper, E. M., and T. Zha (2003). "Modest Policy Interventions." *Journal of Monetary Economics* 50(8).
- Lomibao, N. F. G. (2021). "Heterogeneity in Responses of Inflation to Monetary Policy in the Philippines." BSP Research Note No. 2021-02.
- Lubik, T., and F. Schorfheide (2007). "Do Central Banks Respond to Exchange Rate Movements? A Structural Investigation." *Journal of Monetary Economics* 54(4).
- Monacelli, T. (2005). "Monetary Policy in a Low Pass-Through Environment." *Journal of Money, Credit and Banking* 37(6).
- Rauch, H. E., F. Tung and C. T. Striebel (1965). "Maximum Likelihood Estimates of Linear Dynamic Systems." *AIAA Journal* 3(8).
- Smets, F., and R. Wouters (2007). "Shocks and Frictions in US Business Cycles: A Bayesian DSGE Approach." *American Economic Review* 97(3).
- van der Mensbrugghe, D., et al. MANAGE-WB model documentation, World Bank Policy Research Working Paper 11258 (as saved in `external/`; check the exact title before citing).
