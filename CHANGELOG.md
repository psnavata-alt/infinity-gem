# Changelog

The public repository continues the version numbers of the code base it was built from, so the version notes in the code ("added in 0.3.7") stay meaningful. Every upgrade after 0.2 is opt-in: with default settings the model reproduces the 0.2 results exactly (check R0).

## 0.3.13.dev1 (23 October 2026)

- **A short-run consumption rule** (opt-in; check CS1): `DynamicCGE(sr_consumption={"htm": lam})`, with lam between 0 and 1. In the hybrid closure's short-run years, the share lam of household spending follows disposable income at the baseline saving rates (hand-to-mouth households) and the rest keeps its baseline real value (households that smooth their consumption). The rule is met by the year's saving-rate adjustment, one factor for every household, solved together with the wage curve and re-solved whenever the employment cap changes regime. With the option off (the default) or lam = 1 the results are unchanged. `scenarios/consumption_rule_2026.py` applies it to the central 2026 case.
- **Research DSGE, milestone 25:** the capital model with a flexible-price energy share of the CPI (`research/dsge/soe_htmkf.py`; its test `test_milestone25.py` runs in check X3), and the same model with sticky (Calvo) wages (`soe_htmkw.py`; its test `test_milestone25b.py` is run by hand). `estimate_rot.py` takes `model=htmkf` and `model=htmkw`; `htmk_theta.py` takes `model=htmkf` and a `pattern=` option that scores saved sampler output.
- The validation suite has 75 checks. With default settings the model still reproduces version 0.2 exactly (check R0).

## 0.3.13.dev0 (22 October 2026): first public build

The development copy, published for outside review under the name Infinity GEM (by Paolo Navata; it extends pystdcge, https://github.com/psnavata-alt/pystdcge); new since 0.3.12: markup pricing in short-run years (opt-in; check MK1). Compared with the code it was built from: the package is renamed `infinity_gem`; data that may not be redistributed are left out (`docs/STATUS.md`), and the checks that need them report NOT RUN; PSA's 2018 input-output and supply-use tables are included, so the input-output checks run; the 2026 oil-shock sizes are measured from public monthly series (World Bank Pink Sheet, EIA STEO) instead of a compiled weekly tracker; comments and report text are worded neutrally (no people, organizational units, working documents or planning lists), with the code unchanged.

## Earlier versions (not published under this name)

- **0.3.12 (21 Oct 2026):** within-year capital vintages (`capital="vintage"`, check VN1); a central-bank policy rule inside the dynamic model (`DynamicCGE.monetary_scenario`, check MP1); research DSGE milestones (a sequential Monte Carlo sampler, capital and investment adjustment costs).
- **0.3.11 (20 Oct 2026):** paid labour hoarding in the short run (HD1); a value added-energy bundle with fuel substitution (EN1, EN2); sectoral price stickiness from the duration of price decreases by CPI group (ST1); an interest-rate closure that clears savings and investment (IR1); research DSGE code with Bayesian estimation (X3).
- **0.3.10 (19 Oct 2026):** a 2023 SAM built from PSA sources (national accounts, input-output table, FIES and FIES-LFS aggregates, BESF taxes) as the default for rice-split runs; consumer prices on PSA's CPI weights (PC1).
- **0.3.9 (18 Oct 2026):** a PSA-consistent variant of IFPRI's 2023 SAM with taxes on products counted once (S5); the first versions of the own 2023 SAM (S6); a corrected FIES concordance for the macro-micro link (ML2); the forward-looking CGE research code (X2); own Armington estimates as sensitivity sets (E2).
- **0.3.8 (17 Oct 2026):** savings-driven investment in long-run years and a floating peso in short-run years (IC1); prices rigid downward in the short run (PS1); 2024 and 2025 SAMs updated to PSA totals by cross-entropy (S4).
- **0.3.7 (16 Oct 2026):** rice and corn split from processed food (S3); an employment cap in short-run years (Y6); public construction counted once (PK1); limited short-run years (SR1); a short-run wage curve (WC1); peso shocks (EX1); VAR decompositions from a date (VD1).
- **0.3.6 (15 Oct 2026):** public-investment efficiency by year and leakage (CR1); all skill levels can lose work in the short run.
- **0.3.5 (15 Oct 2026):** the macro-micro link file (ML1); local projections (LP1); Shapley decompositions (SH1).
- **0.3.4 (14 Oct 2026):** sticky peso wages in the short run (W2); the stochastic dynamic CGE, Stage 1 (X1).
- **0.3.3 (10 Oct 2026):** fixes from an audit for "rigging" (results typed in, plugs, hidden failures, weak tests): an edited SAM is refused (D3); structural VARs (V6, V7) and the VAR-to-CGE link (M2).
- **0.3.2 (9 Oct 2026):** saving results when the outputs folder cannot be written (W1).
- **0.3.1 (8 Oct 2026):** home consumption as own produce, validated against IFPRI's model (V4); Hosoe options validated against pycge (V5); named settings (S2); the 16-industry input-output table (I5); household detail (H2, H3).
- **0.3.0 (8 Oct 2026):** validation against IFPRI's own GAMS model (V2) and IFPRI-style trade margins (V3); the 2018 SAM (C8); LES household demand (H1); sourced elasticity sets (E1); refined petroleum split from chemicals (S1); hybrid dynamic closure (Y2); public capital (Y3); capital by industry and a documented baseline (Y4); industry baselines (Y5); labour growth by skill (L1).
- **0.2 (1 Oct 2026):** data checksums (D1); the frozen regression reference (R0); documentation of every equation.
- **0.1 (26 Sep 2026):** SAM tools and multipliers; input-output models; the static standard CGE model in three closures; the recursive-dynamic model; poverty microsimulation; Newey-West regressions, VARs and local projections.
