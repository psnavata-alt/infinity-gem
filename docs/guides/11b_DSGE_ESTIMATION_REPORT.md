# 11b The New Keynesian DSGE: estimation report (DRAFT, 21 Oct 2026, about 1:55 AM; updated 24 Oct 2026, about 9:45 PM)

**Status: a draft for Infinity GEM's own review; research code; NOT FOR CITATION.** **Updated 24 Oct 2026:**
- section 8 is new (milestones 24-26: the investment-specific shock, the price-block fix by sticky wages, its convergence, and the oil supply shock on it);
- **25 Oct 2026, about 1:30 AM: the milestone 26 figures in §8b-8c VERIFIED** (a review note, not included): the sticky-wage model converged, the link's theta 1.5 stays, nothing for the 2026 scenarios;
- sections 5 and 7 carry dated notes;
- sections 1-6 are otherwise the 21 Oct text, and their candidate (`soe_htmu`) is no longer the best-specified model (section 8). Companion to guide 11 (what the model is for, the link to the CGE); this report is about the estimation itself: data, priors, samplers, what is identified, what is not, and what the checks of 21 Oct found. Sections marked *pending* are filled in when the overnight runs finish (`research/dsge/README.md`, 21 Oct section, has the running log). Every number names its file in `outputs/` of the development copy (not included).

## 1. What is estimated

- **The candidate model `soe_htmu.py`** (milestone 19): a small open economy with Calvo price setters and rule-of-thumb resetters (Gali-Gertler) for home goods and imports, external habits, a country risk premium, hand-to-mouth households (a share lam_h consuming current real income), partly adaptive expectations (a share kappa of last quarter's value in the optimisers' expectations), a domestic cost-push shock, and a Lubik-Schorfheide policy rule on headline CPI inflation, output and the depreciation rate with interest-rate smoothing. Six shocks: policy, productivity, world output, world inflation, risk premium, cost-push. 24 parameters estimated; calibrated: the discount factor, the import share, the trade elasticities (`soe_med.py`).
- **The oil models** (`soe_oilw.py`, milestone 21; and `soe_oilf.py`, milestone 22, built 21 Oct): oil as an imported consumption good (CPI weight 0.037) and a production input (cost share 0.030, Infinity GEM's own SAM), a world real oil price with a supply part and a world-demand part (chi_o on world output, identified by G3 GDP growth as a sixth observable); soe_oilf adds flexible-price energy-intensive services (passenger transport and electricity, 9.1% of the CPI, fuel cost share 0.19) through which oil reaches the CPI outside the Calvo sector.
- **Data** (`ph_data.py`): quarterly real GDP growth (PSA, STL seasonal adjustment), CPI inflation (PSA), the BSP policy rate and the peso-dollar rate (BIS), Dubai crude (World Bank) and G3 GDP growth (FRED) for the oil models; 2002Q1-2026Q2 with the COVID quarters 2020-2021 treated as missing (the Kalman filter skips them); all series demeaned, growth and inflation de-seasonalised with quarter means. 98 quarters, 90 observed.
- **Priors:** the usual DSGE families (beta for shares and persistences, gamma for elasticities and rule coefficients, inverse gamma for shock sizes), means and ranges in `estimate_rot.py` and `estimate_med.py`; the Calvo parameter beta(0.7, 0.1) on [0.05, 0.97].
- **The system prior** (Andrle and Benes 2013): a prior on what the model does rather than on a parameter: the fall in CPI inflation per point of first-year cumulative tightening ~ N(−0.35, 0.10), from the BSP's PAMPh (−0.22), the BSP's 2009 DSGE (about −0.45) and the project's local projections (−0.50), and a looser one on output growth ~ N(−0.20, 0.15). Without it the data put the transmission at about 8 points of inflation per point of tightening with a likelihood only 3 log points better: the data barely identify transmission, and the evidence must. The 21 Oct check (section 4) found a flaw in the prior's form and a repair (`prior=ratio2`).

## 2. How it is estimated

- **Likelihood:** the Kalman filter on the first-order (Klein) solution, missing quarters skipped (`estimate.py`); the model solved by QZ at every evaluation (`klein.py`). One evaluation takes about 50 ms on a laptop (100 ms under load).
- **Posterior mode** by Nelder-Mead from the prior means and from a second start; **random-walk Metropolis** with the proposal covariance tuned to an acceptance rate of 20-40% (`estimate_rot.py`); 20,000 draws, 25% burn-in; further chains from over-dispersed starts (`seed=K start=pooled`); split R-hat and effective sample size by `rhat.py`.
- **The candidate's convergence:** three further chains, largest split R-hat 1.012 (`outputs/dsge_rhat_20261020_0303.md`); the oil model with the Calvo parameter calibrated at 0.85, three chains, 1.103 (`_2157.md`); at 0.73, four chains, 1.133 (`_2156.md`; three parameters at 1.12-1.13).
- **A second sampler (21 Oct):** sequential Monte Carlo (`smc.py`; Herbst and Schorfheide 2014: particles from the prior, adaptive tempering, resampling, blocked random-walk mutation; a marginal-data-density estimate as a by-product), tested on an exact Gaussian case (`test_smc.py`).

## 3. The candidate's posterior (the mode the chains found)

Pooled Metropolis chains of 20 Oct (82,500 draws; `outputs/dsge_ph_htmu_estimation_20261020_0231_w1_ratio_long_stl.md` and the seeds; `outputs/dsge_robustness_candidate_20261021_0122.md`):

| Parameter | Posterior mean (5-95%) | Reading |
|---|---|---|
| Calvo, home goods (theta) | 0.954 (0.94-0.97) | prices reset about every five years on average: a very flat Phillips curve (slope 0.002); at the prior's bound; the 0.99-bound check gives 0.952 |
| Calvo, imports (theta_F) | 0.61 (0.48-0.72) | import prices pass through in about two to three quarters |
| Rule-of-thumb share, home goods (omega_H) | 0.22 (0.05-0.45) | some backward-looking inflation |
| Habits (hab) | 0.76 (0.67-0.84) | |
| Hand-to-mouth share (lam_h) | 0.61 (0.37-0.80) | most households consume current income |
| Adaptive weight in expectations (kappa) | 0.71 (0.56-0.84) | |
| Rule: inflation, output, depreciation; smoothing | 1.34 (1.06-1.71); 0.32 (0.19-0.48); 0.13 (0.04-0.23); 0.95 (0.93-0.96) | the BSP responds to inflation more than one for one, smooths heavily |
| Transmission at the mean | CPI −0.35, GDP growth −0.30 per pp of first-year cumulative tightening | the system prior's centre |
| Log likelihood at the mean | −315.7 | |

**What is and is not identified.** The policy rule's coefficients and smoothing, the import Calvo, habits and the shock sizes are identified by the data (posterior bands well inside the priors). The home-goods Calvo is pushed to its bound by the data (a flat Phillips curve), which is why the cost-push shock (milestone 19) and, for the oil questions, a calibrated Calvo from the BSP's micro price data (0.73-0.85, milestone 21b) are used. The transmission strength is set by the system prior (section 1); the output response is not imposed (without its prior: −0.33 against −0.31). Investment's response to interest rates is not in the model (`soe_htmk.py`, section 6) and is not identified by Philippine data in the CGE link either (guide 11 §5).

## 4. The 21 Oct checks

### 4a. The SMC against the chains: a bimodal posterior and its cause

The SMC on the candidate (1,000 particles, 18 stages, 109,000 evaluations; `outputs/dsge_smc_20261021_0106_htmu_w1_ratio_long_stl_n1000.md`) settled at theta 0.805 (0.77-0.84), kappa 0.41, rho_i 0.91, lam_h 0.42, with the same transmission (CPI −0.35, growth −0.31). The log posterior is higher in the chains' region by about 11 log points on average (`outputs/dsge_chain_logpost_20261021_0112.md`, `_0113.md`): the parameter prior penalises theta 0.95 by about 11 log points and the likelihood favours it by 22. Along the straight line between the two means the system-prior penalty rises to −115,000 log points at the midpoint, because the first-year cumulative rate response, the denominator of the transmission ratio, passes through zero there. The SMC's region is an artefact of the ratio's scale-freedom: at its mean a policy shock scaled to a 0.80 pp impact has a rate path of 0.8, 8.7, 17, 24, 27, 29 pp over six quarters (cumulative 62 times the impact; the particles' median 87) and a CPI trough of −17 pp, and the ratio is satisfied because numerator and denominator are both absurd. The chains' mode has a sensible path (cumulative 4.9 times the impact; PAMPh's own 1.35).

**Repair (`prior=ratio2`, built 21 Oct):** the same prior plus a loose prior on the path's scale, the first-year cumulative per pp of impact ~ N(3, 2) (PAMPh 1.35; a pure AR(1) at the estimated smoothing 0.95 about 3.7; the chains' mode 4.9). It penalises the artefact region by about 440 log points and leaves the chains' mode untouched (penalty 0.7 against 0.2). The singular ridge between the prior's bulk and theta 0.95 remains (the transmission is genuinely extreme there), so an SMC started from the parameter prior cannot be the independent check for this model; a bridging SMC started from a wide cloud around the chains' posterior can. **The candidate re-estimated with `ratio2` (one chain, 3:05 AM; `outputs/dsge_robustness_candidate_20261021_0307.md`) has the same posterior as with `ratio`** (Calvo 0.951, kappa 0.70, hand-to-mouth 0.62, rule 1.39 / 0.37 / 0.13, smoothing 0.95; transmission −0.36 / −0.31; log likelihood −315.7): the repair changes nothing where the chains are and only closes the artefact region. **Seeds 2 and 3 (21 Oct, morning): R-hat at most 1.079 (phi_x), ESS 231-464 (`outputs/dsge_rhat_20261021_0843.md`); the pooled posterior (`outputs/dsge_robustness_candidate_20261021_0843.md`): Calvo 0.952 (0.94-0.97), kappa 0.70, hand-to-mouth 0.62, rule 1.35 / 0.33 / 0.13, smoothing 0.95, the same as `ratio` to the second decimal.** **The bridging SMC (`smc.py start=chains`, 21 Oct morning; generalised tempering from a cloud around the chains, Cai et al. 2021; `outputs/dsge_smc_20261021_0859_htmu_w1_ratio_long_stl_n1000_chains.md`) agrees with the four chains: Calvo 0.954 against 0.954, transmission -0.37 / -0.32 against -0.35 / -0.30, the largest gap between posterior means 1.16 SMC s.d. (rho_v), bands of similar width.** So the chains' mode is confirmed from inside its basin, and the prior-started SMC's other mode is the artefact described above. The same check under `ratio2` (three chains; `outputs/dsge_smc_20261021_0906_htmu_w1_ratio2_long_stl_n1000_chains.md`): Calvo 0.957 against 0.952, transmission -0.34 / -0.31 against -0.36 / -0.31, largest gap 1.35 s.d. (kappa). The oil models re-estimated under `ratio2` (21 Oct, 10:15-10:18 AM; Calvo fixed at 0.73 and 0.85; `outputs/dsge_ph_oilw_estimation_20261021_1015_*thfix0.73.md`, `_1017_*thfix0.85.md`) reproduce their `ratio` posteriors inside the 90% bands (transmission -0.47 / -0.08 and -0.47 / -0.14 against -0.46 / -0.06 and -0.46 / -0.13; rule 1.39 against 1.55 and 1.44). **The repair changes no result anywhere.**

### 4b. The oil models under the SMC

The oil model with the Calvo parameter calibrated at 0.85 (`outputs/dsge_smc_20261021_0150_oilw_w1_ratio_long_stl_thfix0.85_n1000.md`) also has two modes: the chains' (adaptive expectations, kappa 0.71; sigma 0.37; import Calvo 0.96; hand-to-mouth share 0.82) and the SMC's (kappa 0.03; sigma 1.44; 0.71; 0.48), with the same policy-rule coefficients; between them the system prior forms a ridge of about 230 log points (the transmission ratio reaches −2.2 there), not a singularity. The chains' mode fits the data better by 37 log points and sits far in the priors' tails; its posterior density is higher by about 25 log points at the means, and a Laplace approximation of each basin's mass puts the chains' mode about 22 log points ahead (`outputs/dsge_chain_logpost_20261021_0156.md`, `_0157.md`; the SMC's own evidence estimate, −871, covers only its basin). **So the BSP-response numbers of guide 11 §5b stand**; at the secondary mode the BSP's response to the 2026-sized oil shock would cost 1.12% of output in year 1 instead of 0.24% (`outputs/dsge_oil_policy_20261021_0159_oilw_long_stl_thfix0.85_smc.md`), which is the size of the model uncertainty a reader should keep in mind. The 0.73 case (the BSP micro-data Calvo; `outputs/dsge_smc_20261021_0237_oilw_w1_ratio_long_stl_thfix0.73_n1000.md`) shows the same pattern: the SMC's mode has model-consistent expectations (kappa 0.02 against the chains' 0.77), sigma 1.27 against 0.37, import Calvo 0.79 against 0.96; the chains fit better by 41 log points and their basin carries about 30 log points more mass (Laplace −852 against −883). Both oil posteriors are therefore bimodal with a dominant mode, which is the one the 20 Oct numbers use.

### 4c. Robustness across specifications

`outputs/dsge_robustness_candidate_20261021_0122.md`: with the system prior, theta sits at 0.95 in every Metropolis specification (ratio; ratio on CPI only, which changes nothing, so the output-strength prior is not binding; the Calvo bound at 0.99; raw instead of STL-adjusted GDP, which gives the same structure at a far lower likelihood, −392 against −316, the seasonal pattern falling on the productivity shock); without it (w = 0) theta is 0.885 and the transmission per pp is −8.45 / −3.38, the singular region again; the sample to 2023Q4 gives the same posterior as the full sample (section 4d), and so does the short sample 2002-2019 (`sample=short gdp=stl`, 72 quarters, no COVID gap: theta 0.951, hand-to-mouth 0.64, kappa 0.69, rule 1.33 / 0.34 / 0.12, smoothing 0.95; transmission −0.34 / −0.29; `outputs/dsge_robustness_candidate_20261021_0248.md`). **So the candidate's parameters are the same whether the sample ends in 2019, 2023 or 2026, and the same under the repaired prior (`ratio2`, section 4a); what the sample choice changes is the likelihood's level, not its shape.**

### 4d. Pseudo-out-of-sample forecasts

The candidate re-estimated on data to 2023Q4 (`outputs/dsge_ph_htmu_estimation_20261021_0234_w1_ratio_long_stl_to2023Q4.md`) has the same posterior as on the full sample (Calvo 0.951, kappa 0.67, hand-to-mouth 0.60, rule 1.36 / 0.34 / 0.14, smoothing 0.95; transmission −0.35 / −0.31): the 2024-2026 quarters, the oil shock included, do not move the estimates. Its forecasts of 2024Q1-2026Q2 (`outputs/dsge_forecast_check_20261021_0236_htmu_w1_ratio_long_stl_to2023Q4.md`; units: demeaned quarterly rates; benchmarks: the unconditional mean and an AR(1) per series fitted to 2023Q4; a ratio below one means the model won):

| Series | Multi-step from the cut-off, RMSE ratio to the mean / to the AR(1), horizons 1-4; 5-10 | One-step-ahead through the period, ratio to the mean / to the AR(1) |
|---|---|---|
| GDP growth | 1.08 / 1.09; **0.81 / 0.81** | **0.95 / 0.94** |
| CPI inflation | 1.09 / 0.95; 1.04 / 1.04 | **0.79 / 0.93** |
| Policy rate | **0.39** / 3.20; 3.46 / 1.65 | **0.22 / 0.81** |
| Peso depreciation | 1.06 / 1.06; 1.05 / 1.05 | 1.00 / 0.93 |

Reading. From the end of 2023 the model foresaw below-average growth through 2026 (predictive-mean sum −2.2 against −3.9 actual, in demeaned quarterly points) and wins against the naive benchmarks at 5-10 quarters for GDP; it could not foresee the 2026 inflation surge (an oil shock after the cut-off) and kept the policy rate high while the BSP cut through 2024-2025, which is why an AR(1) beats it on the rate at short horizons. Once the quarters are observed one by one, the model's dynamics track all four series better than both benchmarks (the one-step-ahead column), the policy rate especially (the rule with smoothing), inflation by a fifth. The 90% bands at the posterior mean covered 100% of the GDP, rate and peso outcomes and 80% of inflation's. Caveat: the STL seasonal adjustment of GDP uses all quarters on file.

### 4e. The rule against the BSP's 2026 decisions

(`rule_check_2026.py`, 20 Oct; `outputs/dsge_rule_check_2026_20261020_2141_long_stl_thfix0.85.md`.) With the oil model's estimated rule, the smoothed 2026 states (headline inflation gap +3.4 and +8.9 pp a year in Q1 and Q2; output gap −0.75 and −1.14%) prescribe 4.90% and 5.08% against the BSP's 4.33% and 4.58%: policy shocks of about one usual size; by Q3 (4.92%) the BSP had reached the rule's level, a quarter late. The rule's own response to the 2026-sized oil shock (+0.6 to +0.8 point in year 1) is the size of the BSP's actual moves (4.25% in March to 5.00% in August). Timing caveat (the BIS series dates each 2026 move a month later than the BSP deck's chart data).

## 5. What the estimates are good for now, and what they are not

- **Good for:** the transmission used in the CGE link (a year of one-point-tighter policy: 0.4-0.9% of 2026 GDP, 0.35-0.7 million new poor; guide 11 §5), the BSP's estimated reaction to the 2026 oil shock (guide 11 §5b; indicative), and the "same rule, two readings" diagnosis of the money block (a review note (not included)): these rest on the transmission strength, which the system prior pins and which is the same in both posterior regions.
- **Not for:** any reported number; the Calvo parameter itself (at a bound, bimodal under the ratio prior); investment's interest sensitivity (not in the model until milestone 23 is estimated); the oil supply shock's sign with theta estimated (milestone 22, pending).
- **Update (24 Oct 2026):**
  - The Calvo parameter comes off its bound with sticky wages: 0.76-0.79, converged (section 8b).
  - Investment's interest sensitivity is estimated: year-1 theta about 1.3-1.4 (0.6-2.2). The CGE link uses 1.5 (since 23 Oct 2026).
  - The oil supply shock's sign with the Calvo estimated is answered: still expansionary in year 1, now because of sticky nominal wages (section 8c).
  - None of this is for the 2026 scenarios.

## 6. Extensions built on 21 Oct (soe_oilf estimated on three chains; soe_htmk's first chain)

- **`soe_oilf.py`** (milestone 22): oil pass-through through flexible-price transport and electricity. Estimated (one chain, 3:19 AM; `outputs/dsge_ph_oilf_estimation_20261021_0319_w1_ratio_long_stl.md`): the Calvo parameter stays at 0.94 (0.89-0.97); after a 36% oil shock headline inflation is +2.4 pp in year 1 (soe_oilw at Calvo 0.85: +2.0) and consumption −1.25%, but output still rises 0.54% in year 1 (`outputs/dsge_oil_policy_20261021_0319_oilf_long_stl.md`): the supply shock is expansionary with theta estimated whatever the pass-through channel, because the home-goods Phillips curve is flat; the contractionary case needs the Calvo parameter calibrated from the BSP's micro price data (0.73-0.85, guide 11 §5b). The BSP's response costs 0.45% of output in year 1 and 0.89% in year 2 here. Seeds 2 and 3 (21 Oct, morning): R-hat at most 1.104 (theta), the rest below 1.1, ESS 102-327 (`outputs/dsge_rhat_20261021_0821.md`); on the pooled chains the BSP's response costs 0.47% / 0.93% of output and the supply shock still raises year-1 output 0.56% (`outputs/dsge_oil_policy_20261021_0822_oilf_long_stl.md`): the answer stands.
- **`soe_htmk.py`** (milestone 23): capital, Smets-Wouters investment adjustment costs, Tobin's q, variable utilisation; determinate at the Philippine calibration only with utilisation and forward-looking expected inflation in Tobin's q; `estimate_rot.py model=htmk` wired (phi_i normal(4, 1.5), psi_u beta(0.5, 0.15)); a tightening cuts investment 2.9% against consumption 0.5% at the candidate's posterior mean. **First estimation (21 Oct, 9:05 AM; one chain, `outputs/dsge_ph_htmk_estimation_20261021_0905_w1_ratio2_long_stl.md`):** phi_i 7.1 (5.2-9.0), identified away from its prior; psi_u 0.29; Calvo 0.92 (0.83-0.96). ~~But transmission is unpinned across the draws (CPI strength 5-95% -8.7 to +10.2, median -0.43; `outputs/dsge_posterior_strength_20261021_0907.md`): the estimated rule reverses strongly, the first-year cumulative rate path crosses zero inside the posterior, and the ratio prior does not bind. Not usable for the CGE link as estimated; needs a prior on the rate path itself (research/dsge/README.md, 21 Oct morning).~~ **CORRECTION (21 Oct 2026, about 11:05 PM): the spread below came from a bug, not from the model.** `posterior_strength.py` solved each draw without the calibrated parameters (`ER.FIXED`: capital share 0.5, investment share 0.24, depreciation 0.025); soe_htmk's defaults are a capital share and an investment share of 0, so the 9:07 AM run solved the model WITHOUT capital at parameters estimated WITH capital. Fixed and rerun on all three chains (`outputs/dsge_posterior_strength_20261021_2309.md`, 900 draws): **CPI strength -0.38 (5-95%: -0.56 to -0.22), 81% of draws inside the evidence band; GDP strength -0.41 (-0.53 to -0.30); the first-year cumulative rate path 3.6-5.0 times the impact, never near zero: transmission IS pinned and soe_htmk is usable for the CGE link.** The report's strength at the posterior MEAN (-0.86, then -0.73 on the pooled chains) is a point where the averaged parameters make the rate reverse; at the parameters' median it is -0.34 (scratch check, 11:15 PM). Models with no calibrated parameters (htm, htmu) were not affected; `oil_policy.py`, `rule_check_2026.py` and `forecast_check.py` already passed `FIXED`. **New, 11:11 PM (`htmk_theta.py`, `outputs/dsge_htmk_theta_20261021_2311.md`): the investment semi-elasticity theta implied by soe_htmk is 0.83 in year 1 (5-95%: 0.11 to 1.46; two years 0.86), below the link's range 1.9-3.3 for 99% of draws;** the data's local projections (`outputs/dsge_investment_lp_20261020_0242.md`) give 0.17 in year 1 and 2.3 in year 2 (about 0.77 over two years), wide bands. Neither saw investment data in the DSGE's estimation: `estimate_rot.py obs=inv` (milestone 23c, tests `test_milestone23c.py` 3/3) adds PSA real investment growth as a fifth observable with a measurement error; its first chain started 11:15 PM. Research only; Three chains (10:08 AM; `outputs/dsge_rhat_20261021_1008.md`): R-hat at most 1.271 (sd_a), the rest below 1.1, phi_i 7.0-7.1 on every chain: the identification is robust, the model stays indicative.

- **With PSA investment data (milestone 23c, `obs=inv`; three chains, 11:15 PM-12:01 AM; `outputs/dsge_ph_htmk_estimation_20261021_2336_w1_ratio2_long_stl_inv.md`, `_2357_*_inv_seed2.md`, `20261022_0001_*_inv_seed3`; R-hat `outputs/dsge_rhat_20261022_*.md`):** phi_i 7.7-7.9 on every chain (R-hat 1.02), investment measurement error 4.9% a quarter (R-hat 1.02; about GFCF's whole volatility, so the data inform the model through comovement, not quarter-to-quarter swings). **The Calvo parameter has NOT converged** (R-hat 2.45: 0.951, 0.909, 0.951 by chain; the second chain sits in a lower region, as in the bimodality found on 21 Oct overnight), so the posterior is indicative. **But the quantity that matters for the CGE link agrees on every chain: theta in year 1 = 0.62 / 0.56 / 0.58 (5-95% about 0.0 to 1.1), CPI strength -0.34 / -0.44 / -0.33** (scratch per-chain check, 12:03 AM; pooled: `outputs/dsge_htmk_theta_20261021_2340_inv.md` on chain 1, 0.61). Without investment data theta was 0.83; with them about 0.6; the data's local projections give about 0.77 over two years; the CGE link has used 1.9-3.3 (central 2). **Reading:** the evidence now points to the link's LOW case (0.55, milestone 14): at that value the BSP's oil response cost about +0.12 million poor through the CGE (20 Oct, research), against +0.38 million at 2. Before any use: more chains for the Calvo parameter (or theta fixed at 0.95 for this check), and a decision on whether the link's central theta moves (a research setting).
- **22 Oct 2026: the posterior is multimodal; a heavy SMC favours the high-response region** (`research/dsge/README.md`, 22 Oct). With 3,000 particles and 20 tempering stages, 95% of the mass sits in the region with lower investment adjustment costs and large productivity shocks, where the year-1 investment theta is 2.30 (1.33-3.45), in line with the CGE link's central 2; the remaining 5% has theta about 0.6. Light runs had disagreed on the weights (98% and 17% for this region); two heavy runs agree with the first (95%; and, with the Calvo bound raised to 0.99, essentially all the mass, theta 2.44, 1.62-3.53). The favoured region needs the Calvo parameter at its bound and productivity shocks of s.d. 4.2% a quarter, which suggests a missing investment-specific shock. The link's central theta (2) stands, with 0.55 the low case.

## 7. Files

`research/dsge/` (24 Oct 2026: also `soe_htmki.py`, `soe_htmkf.py`, `soe_htmkw.py`, `soe_htmkwo.py`, `htmk_theta.py`, `oil_policy_htmkwo.py`, `test_milestone24.py`-`test_milestone26.py`, `milestone25_scratch/`, `milestone26_scratch/`; `estimate_rot.py` adds `obs=inv`, `start=cloud:<file>`, `model=htmki|htmkf|htmkw|htmkwo`; `scenarios/bsp_oil_response_netting_htmkwo.py`): `estimate_rot.py` (`prior=pamph|ratio|ratio_cpi|ratio2`, `sample=`, `gdp=`, `end=`, `theta_fix=`, `theta_hi=`, `world=`, `init=`, `seed= start=`), `rhat.py`, `chain_logpost.py`, `smc.py`, `robustness_candidate.py`, `forecast_check.py`, `rule_check_2026.py`, `oil_policy.py`, `posterior_strength.py`, `transmission_benchmarks.py`, `pamph_targets.py`; the models `soe_*.py` and their `test_milestone*.py`; `README.md` (the dated log). Outputs: `outputs/dsge_ph_<model>_estimation_*`, `_draws_*.npy`, `dsge_rhat_*`, `dsge_smc_*`, `dsge_chain_logpost_*`, `dsge_robustness_candidate_*`, `dsge_forecast_check_*`.

## 8. Milestones 24-26 (22-24 Oct 2026; added 24 Oct 2026)

All with PSA investment growth as a fifth observable (`obs=inv`, measurement error me_inv) and the `ratio2` system prior. Heavy SMC = 3,000 particles, 5 mutation steps, ESS target 0.8. The full logs are in `research/dsge/README.md` (22 Oct, milestone 25, milestone 26) and in `outputs/dsge_price_block_fix_22Oct2026_results.md` and `outputs/dsge_milestone26_results_24Oct2026.md`.

### 8a. Milestone 24: an investment-specific shock (22 Oct)

`soe_htmki.py` is soe_htmk plus a marginal-efficiency-of-investment shock (Smets and Wouters 2007). Heavy bridging SMC: `outputs/dsge_smc_20261022_1704_htmki_w1_ratio2_long_stl_inv_n3000_seed11_chains.md`.
- It removes soe_htmk's implausible productivity shocks: sd_a 0.68 against 4-5.
- It removes the investment block's bimodality.
- It improves the mean log posterior by about 16 points.
- **Year-1 investment theta 1.39 (0.74-2.11).**
- But the domestic Calvo stays at its bound (0.956), and the CPI transmission is weak (-0.22).

### 8b. Milestone 25: the price block, and the sticky-wage model (22-23 Oct night; convergence 24 Oct)

**Diagnosis.** With flexible wages the real wage equals the marginal rate of substitution every quarter, so real marginal cost has an s.d. of about 7% a quarter against CPI inflation's 0.74. The likelihood therefore needs some device to keep marginal cost out of the CPI, and it takes whichever is open:
- a flat domestic Phillips curve (Calvo at its bound: year-1 theta 1.4);
- rigid import prices (theta about 2.0; 10 log points worse when the domestic Calvo is fixed at 0.73);
- very elastic capital utilisation (psi_u 0.1; theta 0.8).

Fixing the Calvo at 0.73 or 0.85 (runs A1, A2) and adding a flexible-price energy share (`soe_htmkf.py`, run B1) moves the problem but does not solve it.

**The fix: Calvo wages** (`soe_htmkw.py`; Erceg, Henderson and Levin 2000; theta_w beta(0.75, 0.10); eps_w 4.5). Run W1 (heavy bridging SMC, 23 Oct; `outputs/dsge_smc_20261023_0503_htmkw_w1_ratio2_long_stl_inv_n3000_seed15_chains.md`):
- domestic Calvo **0.786 (0.628-0.907)**, with the BSP's micro-data 0.73 inside;
- import Calvo 0.65 and utilisation 0.57: no block at a bound;
- wage Calvo 0.93;
- **log MDD -622.95, about 8 points above every flexible-wage version** (-631.3 to -641.4);
- year-1 investment theta 1.43 (0.72-2.23).

On this basis the CGE link's theta moved from 2 to 1.5, with 0.7 low and 2 high (23 Oct 2026).

**Convergence (new, 24 Oct 2026).** Three Metropolis chains (seeds 41-43, 40,000 draws each, overdispersed starts around W1's particles via `estimate_rot.py start=cloud:<file>`):

| Quantity | split R-hat | ESS | pooled posterior (5-95%) |
|---|---|---|---|
| every parameter | at most **1.042** (sd_ystar) | 152-432 | |
| Calvo, home goods | 1.010 | 238 | 0.76 (0.58-0.89) |
| Calvo, wages | 1.005 | 258 | 0.94 (0.91-0.97) |
| year-1 investment theta | 1.003 | 346 (thinned) | **1.28 (0.61-2.05)** |
| CPI / GDP transmission strength | 1.006 / 1.008 | 374 / 451 (thinned) | -0.26 / -0.38 |

Files: `outputs/dsge_rhat_20261024_1854.md`, `outputs/dsge_htmkw_theta_20261024_2136_inv.md`, `outputs/dsge_ph_htmkw_estimation_20261024_185*_seed4*.md`. The posterior has converged and agrees with W1. The year-1 theta (1.28) is slightly below W1's 1.43, and the link's 1.5 sits near the 65th percentile.

Not yet done:
- a second SMC (another seed or a prior start), so W1's log MDD rests on one run;
- a check that no other region holds mass (the chains started in W1's region).

### 8c. Milestone 26: the oil supply shock on the sticky-wage model (24 Oct 2026)

**Model and estimation.** `soe_htmkwo.py` is soe_htmkw plus the oil block of soe_oilf: oil in the CPI (0.037) and in production (0.030), the flexible services' fuel share (0.19), oil supply separate from world oil demand. It has 33 parameters and 7 observables; `test_milestone26.py` 5/5. Heavy bridging SMC (22 stages, 9,535 s on 3 workers): `outputs/dsge_smc_20261024_2133_htmkwo_w1_ratio2_long_stl_inv_n3000_seed26_chains.md`.
- Calvo **0.864 (0.79-0.93)**: estimated, off its bound;
- wage Calvo 0.94;
- sigma 0.43; chi_o 6.6;
- sd_a 5.9 (a misspecification flag);
- log MDD -1114.71 (seven observables, so not comparable with W1's -622.95).

**The 2026-sized oil supply shock (36%, log).** `outputs/dsge_oil_policy_20261024_2134_htmkwo_long_stl_inv.md`:

| | Estimated rule | Rate held for a year | BSP's cost (rule minus held) |
|---|---|---|---|
| Output, year 1 | **+0.39%** (draws +0.13 to +0.67; 99.6% positive) | +1.08% | **-0.69%** (-0.92 to -0.50) |
| Output, year 2 | -0.11% | | -1.21% (-1.73 to -0.78) |
| Headline inflation, year 1 | +2.37 pp | +2.94 pp | -0.57 pp |

**So the oil supply shock still raises year-1 output with the Calvo parameter estimated, but no longer because of a flat Phillips curve.** One parameter changed at a time at the posterior mean (scratch `research/dsge/milestone26_scratch/oil_sign_decomposition.py`):
- with flexible wages, year-1 output is -0.03%;
- with theta_w 0.75, it is -0.36%;
- with Calvo 0.73 and flexible wages, -0.46%;
- with Calvo 0.73 and sticky wages, still +0.27%.

Very sticky nominal wages without indexation let the oil-driven CPI rise cut the real wage (-2.3% in year 1), which lowers marginal cost and raises hiring. That is the opposite of the real-wage rigidity behind contractionary oil shocks (Blanchard and Gali 2007). Philippine wage boards respond to inflation, so wage indexation (Smets-Wouters) is the next variant to test (not done yet).

**Through the CGE link** (θ 0.7 / 1.5 / 2; Infinity GEM's own SAM, hoarding 0.85; `scenarios/bsp_oil_response_netting_htmkwo.py`; `outputs/bsp_oil_response_netting_20261024_2138_own_oil36_htmkwo_long_stl_inv.md`). The DSGE inputs for 2026 are a real-rate gap of 1.33 pp and a real exchange rate of -0.44%. The BSP's response adds this many new poor in 2026:

| | θ 0.7 | θ 1.5 | θ 2 |
|---|---|---|---|
| Net of the price benefit | **0.11 M** | **0.21 M** | **0.28 M** |
| Incomes only (gross) | 0.42 M | 0.67 M | 0.82 M |
| Prices only | -0.33 M | -0.45 M | -0.52 M |

In 2027 the net figures are 0.06 / 0.09 / 0.11 M. The 23 Oct figures, on soe_oilw with the Calvo fixed at 0.73, were 0.17 / 0.34 / 0.45 M. Indicative only: one bridging SMC, a misspecification flag, and an oil sign that depends on the missing wage indexation.

## References

- An, S., and F. Schorfheide (2007). "Bayesian Analysis of DSGE Models." Econometric Reviews 26(2-4): 113-172.
- Andrle, M., and J. Benes (2013). "System Priors: Formulating Priors about DSGE Models' Properties." IMF Working Paper 13/257.
- Blanchard, O. J., and J. Gali (2007). "The Macroeconomic Effects of Oil Price Shocks: Why Are the 2000s So Different from the 1970s?" NBER Working Paper 13368.
- Cai, M., M. Del Negro, E. Herbst, E. Matlin, R. Sarfati, and F. Schorfheide (2021). "Online Estimation of DSGE Models." Econometrics Journal 24(1): C33-C58.
- Christiano, L. J., M. Eichenbaum, and C. L. Evans (2005). "Nominal Rigidities and the Dynamic Effects of a Shock to Monetary Policy." Journal of Political Economy 113(1): 1-45.
- Erceg, C. J., D. W. Henderson, and A. T. Levin (2000). "Optimal Monetary Policy with Staggered Wage and Price Contracts." Journal of Monetary Economics 46(2): 281-313.
- Herbst, E., and F. Schorfheide (2014). "Sequential Monte Carlo Sampling for DSGE Models." Journal of Applied Econometrics 29(7): 1073-1098.
- Herbst, E., and F. Schorfheide (2016). Bayesian Estimation of DSGE Models. Princeton University Press.
- Klein, P. (2000). "Using the Generalized Schur Form to Solve a Multivariate Linear Rational Expectations Model." Journal of Economic Dynamics and Control 24(10): 1405-1423.
- Smets, F., and R. Wouters (2007). "Shocks and Frictions in US Business Cycles: A Bayesian DSGE Approach." American Economic Review 97(3): 586-606.
- The BSP papers of section 1's evidence: a reference copy (not distributed).
